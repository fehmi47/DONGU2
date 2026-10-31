from datetime import date
from decimal import Decimal
from typing import List, Optional, Tuple, Dict
from sqlalchemy.orm import Session

from app.models.recipe import Recipe
from app.models.recipe_ingredient import RecipeIngredient
from app.models.product import Product
from app.schemas.recipe import (
    RecipeRecommendationResponse,
    RecipeIngredientResponse,
    MatchedIngredientInfo,
    MissingIngredientInfo,
)
from app.services.priority_service import evaluate_product_priority

# Birim dönüşüm katsayıları tablosu
UNIT_CONVERSIONS: Dict[str, Tuple[str, Decimal]] = {
    "g": ("weight", Decimal("1")),
    "gram": ("weight", Decimal("1")),
    "kg": ("weight", Decimal("1000")),
    "kilogram": ("weight", Decimal("1000")),

    "ml": ("volume", Decimal("1")),
    "mililitre": ("volume", Decimal("1")),
    "l": ("volume", Decimal("1000")),
    "litre": ("volume", Decimal("1000")),

    "adet": ("count", Decimal("1")),
    "tane": ("count", Decimal("1")),
    "paket": ("packet", Decimal("1")),
    "demet": ("bunch", Decimal("1")),
    "kaşık": ("spoon", Decimal("1")),
}

# Öncelik seviyelerine göre tarif sıralama bonus puanları
PRIORITY_BONUS: Dict[str, float] = {
    "critical": 35.0,  # 0-2 gün kalmış ürünler tarifi en üste taşır
    "high": 20.0,      # 3-5 gün kalmış veya TETT geçmiş ürünler
    "medium": 10.0,    # 6-10 gün
    "low": 4.0,        # 10+ gün
    "no_date": 2.0,    # Tarihsiz kiler ürünleri
}


# Sıfatlar, niteleyiciler ve eşleşmede tek başına esas alınmaması gereken kelimeler
FOOD_MODIFIERS = {
    "taze", "kuru", "kur", "organik", "doğal", "dogal", "yerli", "çiftlik", "ciftlik", "köy", "koy",
    "tatlı", "tatli", "tatl", "acı", "aci", "ekşi", "eksi", "tuzlu", "acılı", "acili", "toz", "tane",
    "süzme", "suzme", "yarım", "yarim", "tam", "yağlı", "yagli", "yağsız", "yagsiz", "az",
    "beyaz", "kırmızı", "kirmizi", "kırmız", "kirmiz", "yeşil", "yesil", "sarı", "sari", "siyah",
    "iri", "ince", "dilim", "dilimli", "kıyılmış", "kiyilmis", "rendelenmiş", "rendelenmis",
    "haşlanmış", "haslanmis", "fırın", "firin", "fırınlanmış", "firinlanmis", "bayat",
    "salkım", "salkim", "çeri", "ceri", "tarla", "çengelköy", "cengelkoy", "amasya", "koçbaşı", "kocbasi",
    "pilavlık", "pilavlik", "köftelik", "koftelik", "çorbalık", "corbalik",
    "burgu", "fiyonk", "spagetti", "sızma", "sizma", "riviera", "çiğ", "cig", "kavrulmuş", "kavrulmus",
    "gezen"
}


def normalize_turkish_text(text: str) -> str:
    """
    Türkçe karakterleri güvenli şekilde küçük harfe dönüştürür (İ->i, I->ı)
    ve noktalama işaretlerini temizler.
    """
    tr_map = str.maketrans("İIŞĞÜÖÇ", "iışğüöç")
    cleaned = text.translate(tr_map).lower()
    return "".join(c for c in cleaned if c.isalnum() or c.isspace()).strip()


def stem_food_word(w: str) -> str:
    """
    Türkçe gıda isimlerindeki tamlanan ve iyelik eklerini (-i, -ı, -u, -ü, -si, -sı vb.)
    ve ünsüz yumuşamalarını (ğ->k, c->ç, d->t, b->p) güvenle köke indirger.
    """
    if w in FOOD_MODIFIERS:
        return w

    KNOWN_ROOTS = {
        "kayısı", "kayisi", "biber", "fasulye", "domates", "patates", "soğan", "sogan",
        "havuç", "havuc", "pirinç", "pirinc", "mercimek", "nohut", "bulgur", "makarna",
        "yoğurt", "yogurt", "peynir", "tavuk", "yumurta", "ekmek", "balık", "balik",
        "zeytinyağı", "zeytinyagi", "tereyağı", "tereyagi", "salça", "salca", "nane", "tuz",
        "elma", "armut", "portakal", "limon", "kabak", "patlıcan", "patlican", "ıspanak", "ispanak"
    }
    if w in KNOWN_ROOTS:
        return w

    if w.endswith(("si", "sı", "su", "sü")) and len(w) > 4:
        return w[:-2]
    elif w.endswith(("i", "ı", "u", "ü")) and len(w) > 3:
        stem = w[:-1]
        if stem.endswith(("yağ", "yag")):
            return stem
        elif stem.endswith(("ğ", "g")):
            return stem[:-1] + "k"
        elif stem.endswith("c"):
            return stem[:-1] + "ç"
        elif stem.endswith("d"):
            return stem[:-1] + "t"
        elif stem.endswith("b"):
            return stem[:-1] + "p"
        return stem
    return w


def is_name_match(product_name: str, ingredient_name: str) -> bool:
    """
    Kilerdeki ürün adı ile tarifteki malzeme adının uyuşup uyuşmadığını kontrol eder.
    Sıfatların (taze, kuru, organik vb.) alakasız ürünleri hatalı eşleştirmesini engeller.
    
    Örnekler:
    - 'Salkım Domates' <-> 'Domates' -> Eşleşir (True)
    - 'Tam Buğday Ekmeği' <-> 'Ekmek' -> Eşleşir (True)
    - 'Köy Yoğurdu' <-> 'Yoğurt' -> Eşleşir (True)
    - 'Taze Kaşar Peyniri' <-> 'Taze Fasulye' -> Eşleşmez (False)
    - 'Kuru Kayısı' <-> 'Kuru Fasulye' -> Eşleşmez (False)
    """
    p_norm = normalize_turkish_text(product_name)
    i_norm = normalize_turkish_text(ingredient_name)

    if p_norm == i_norm:
        return True

    p_words = [stem_food_word(w) for w in p_norm.split()]
    i_words = [stem_food_word(w) for w in i_norm.split()]

    p_stemmed_str = " ".join(p_words)
    i_stemmed_str = " ".join(i_words)

    # 1. Tam öbek alt dize eşleşmesi
    if i_stemmed_str in p_stemmed_str:
        if any(w not in FOOD_MODIFIERS for w in i_words):
            return True

    if p_stemmed_str in i_stemmed_str:
        if any(w not in FOOD_MODIFIERS for w in p_words):
            return True

    # 2. Ana gıda kelimelerinin (modifiye edici olmayan) kesişimi
    p_core = {w for w in p_words if w not in FOOD_MODIFIERS and len(w) >= 3}
    i_core = {w for w in i_words if w not in FOOD_MODIFIERS and len(w) >= 3}

    common_core = p_core & i_core
    if common_core:
        return True

    return False


def check_quantity_sufficiency(
    prod_qty: Decimal,
    prod_unit: str,
    req_qty: Decimal,
    req_unit: str,
    ingredient_name: str = "",
) -> bool:
    """
    Kilerdeki ürün miktarının tarifte istenen miktarı karşılayıp karşılamadığını
    akıllı birim dönüşümlerini (kaşık, bardak, adet, kg, gr vb.) dikkate alarak hesaplar.
    """
    p_unit_clean = prod_unit.strip().lower()
    r_unit_clean = req_unit.strip().lower()

    # Birebir aynı birim
    if p_unit_clean == r_unit_clean:
        return prod_qty >= req_qty

    from app.services.unit_converter import convert_unit
    try:
        needed_in_prod_unit = convert_unit(
            quantity=req_qty,
            from_unit=req_unit,
            to_unit=prod_unit,
            item_name=ingredient_name,
        )
        TOLERANCE = Decimal("0.005")
        return (Decimal(str(prod_qty)) + TOLERANCE) >= needed_in_prod_unit
    except Exception:
        return Decimal(str(prod_qty)) > 0


def match_user_products_with_recipes(
    db: Session,
    user_id: int,
    reference_date: Optional[date] = None
) -> List[RecipeRecommendationResponse]:
    """
    Kullanıcının aktif gıda stoklarını tüm yemek tarifleriyle eşleştirir ve
    en uygun tarif önerilerini aciliyet puanına göre sıralayarak döner.
    
    Gıda Güvenliği ve Öncelik Kuralları:
    1. STT Tarihi Geçmiş Ürünler:
       - 'evaluate_product_priority' sonucunda 'can_be_recommended == False' olan ürünler
         kesinlikle eşleştirmeye ve tariflere dahil edilmez!
    2. TETT Tarihi Geçmiş Ürünler:
       - Gıda güvenliği kurallarına uygun olarak 'high' öncelik bonusuyla değerlendirilir.
    3. Öncelik Sıralaması:
       - Kilerdeki acil tüketilmesi gereken ('critical', 'high') ürünleri kullanan tarifler
         ve eksiksiz hazırlanabilen ('can_prepare == True') tarifler en üstte listelenir.
    """
    ref_date = reference_date or date.today()

    # 1. Kullanıcının aktif ürünlerini çek ve gıda güvenliği değerlendirmesinden geçir
    user_products = db.query(Product).filter(
        Product.user_id == user_id,
        Product.status == "active"
    ).all()

    # Yalnızca güvenle tüketilebilecek ürünleri al (STT geçmişler filtrelenir!)
    eligible_products = []
    for prod in user_products:
        eval_res = evaluate_product_priority(prod, reference_date=ref_date)
        if eval_res.can_be_recommended:
            eligible_products.append({
                "product": prod,
                "priority_level": eval_res.priority_level,
                "priority_bonus": PRIORITY_BONUS.get(eval_res.priority_level, 0.0),
            })

    # 2. Tüm tarifleri çek
    all_recipes = db.query(Recipe).all()
    recommendations: List[RecipeRecommendationResponse] = []

    for recipe in all_recipes:
        matched_items: List[MatchedIngredientInfo] = []
        missing_items: List[MissingIngredientInfo] = []
        recipe_priority_score: float = 0.0
        used_product_ids = set()

        total_ingredients_count = len(recipe.ingredients)
        all_required_sufficient = True

        for ing in recipe.ingredients:
            # Bu tarif malzemesi için kullanıcının elindeki en uygun ürünü bul
            matched_prod_info = None

            for ep in eligible_products:
                prod = ep["product"]
                if prod.id not in used_product_ids and is_name_match(prod.name, ing.ingredient_name):
                    matched_prod_info = ep
                    break

            if matched_prod_info:
                prod = matched_prod_info["product"]
                used_product_ids.add(prod.id)

                is_sufficient = check_quantity_sufficiency(
                    prod_qty=prod.quantity,
                    prod_unit=prod.unit,
                    req_qty=ing.quantity,
                    req_unit=ing.unit,
                    ingredient_name=ing.ingredient_name,
                )

                if not is_sufficient and not ing.is_optional:
                    all_required_sufficient = False

                matched_items.append(MatchedIngredientInfo(
                    ingredient_name=ing.ingredient_name,
                    required_quantity=ing.quantity,
                    required_unit=ing.unit,
                    product_id=prod.id,
                    product_name=prod.name,
                    available_quantity=prod.quantity,
                    available_unit=prod.unit,
                    is_sufficient=is_sufficient,
                    priority_level=matched_prod_info["priority_level"],
                ))

                # Öncelikli ürün kullanım puanı ekle
                recipe_priority_score += matched_prod_info["priority_bonus"]

            else:
                # Malzeme kilerde hiç yok
                if not ing.is_optional:
                    all_required_sufficient = False

                missing_items.append(MissingIngredientInfo(
                    ingredient_name=ing.ingredient_name,
                    quantity=ing.quantity,
                    unit=ing.unit,
                    is_optional=ing.is_optional,
                    reason="Kilerde bulunmuyor",
                ))

        # Yüzde hesaplama
        if total_ingredients_count > 0:
            match_percentage = round((len(matched_items) / total_ingredients_count) * 100, 1)
        else:
            match_percentage = 0.0

        can_prepare = (all_required_sufficient and len(matched_items) > 0)
        total_time = recipe.preparation_time + recipe.cooking_time

        # Pydantic yanıt modelini oluştur
        ingredient_responses = [
            RecipeIngredientResponse.model_validate(ri) for ri in recipe.ingredients
        ]

        rec = RecipeRecommendationResponse(
            id=recipe.id,
            name=recipe.name,
            description=recipe.description,
            instructions=recipe.instructions,
            preparation_time=recipe.preparation_time,
            cooking_time=recipe.cooking_time,
            total_time=total_time,
            servings=recipe.servings,
            difficulty=recipe.difficulty,
            image_url=recipe.image_url,
            ingredients=ingredient_responses,
            matched_ingredients=matched_items,
            missing_ingredients=missing_items,
            match_percentage=match_percentage,
            can_prepare=can_prepare,
            priority_score=round(recipe_priority_score, 1),
        )

        recommendations.append(rec)

    # 3. Akıllı Sıralama Algoritması:
    # Formül: (Hemen Pişirilebilir mi? * 100) + (Eşleşme Yüzdesi * 1.5) + (Öncelik Puanı * 2.0)
    # Bu formül sayesinde:
    # 1. Eldeki acil gıdalarla HEMEN pişirilebilecek tarifler zirveye yerleşir.
    # 2. Öncelikli (bozulmak üzere olan) gıdaları en çok kullanan tarifler avantaj kazanır.
    def calculate_sort_weight(item: RecipeRecommendationResponse) -> float:
        can_prep_weight = 100.0 if item.can_prepare else 0.0
        return can_prep_weight + (item.match_percentage * 1.5) + (item.priority_score * 2.0)

    recommendations.sort(key=calculate_sort_weight, reverse=True)
    return recommendations
