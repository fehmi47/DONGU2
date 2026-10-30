"""
DÖNGÜ AI Asistanı - Tarif Arama ve Akıllı Eşleştirme Aracı

Kullanıcının mutfağındaki aktif ürünlerle yemek tariflerini eşleştirir.
Salt-okunur (read-only) çalışır; veritabanında kesinlikle değişiklik yapmaz.
"""

from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.models.product import Product
from app.agents.registry import register
from app.services.recipe_matcher import match_user_products_with_recipes


def turkish_lower(text: str) -> str:
    """
    Türkçe karakter kurallarına uygun olarak metni küçük harfe dönüştürür.
    Python'ın standart .lower() metodunun 'I' -> 'i' yapma hatasını önlemek için
    önce 'I' -> 'ı' ve 'İ' -> 'i' dönüşümü uygular, ardından lower() çağırır.

    Örnekler:
        turkish_lower("Ispanak") == "ıspanak"
        turkish_lower("İncir") == "incir"
    """
    if not text:
        return ""
    return text.replace("I", "ı").replace("İ", "i").lower()


def turkish_match(query: str, target: str) -> bool:
    """
    Kullanıcının veya LLM'in girdiği arama terimi ile hedef metni (tarif/malzeme/ürün adı)
    Türkçe karakter kurallarına (I/ı, İ/i) ve klavye esnekliğine göre eşleştirir.
    Hem 'Ispanak', hem 'ıspanak' hem de İngilizce klavye 'ispanak' girişlerini yakalar.
    """
    if not query or not target:
        return False
    q_l = turkish_lower(query.strip())
    t_l = turkish_lower(target.strip())

    if q_l in t_l:
        return True

    # i <-> ı esnek eşleşmesi (kullanıcı veya LLM i/ı karıştırırsa)
    return q_l.replace("i", "ı") in t_l.replace("i", "ı")


@register(
    name="search_recipes",
    description=(
        # 1) İki çalışma modu var: LLM hangisini ne zaman kullanacağını buradan öğrenir
        "Veritabanındaki tarifleri kullanıcının mutfağıyla eşleştirir. İki modu vardır: "
        "(A) AÇIK UÇLU mod: 'ne pişirebilirim', 'domatesle ne yapabilirim' gibi sorularda dish_name VERME; "
        "en fazla 5 tarif döner, bozulmak üzere olan ürünleri kullananlar üsttedir. "
        "(B) BELİRLİ YEMEK modu: kullanıcı belirli bir yemek isterse ('menemen yapalım', "
        "'domatesli biber salatası tarifi') dish_name ver; sadece o yemeği arar. "
        # 2) Dönen alanların anlamı
        "Her tarifte: ad, eşleşme oranı, süre, 'eldeki_malzemeler' (kullanıcıda olanlar), "
        "'eksik_malzemeler' (kullanıcıda OLMAYANLAR) ve 'kaynak': 'veritabani' bulunur. "
        "Bir malzeme ya eldeki ya da eksik listesindedir, ikisinde birden olamaz. "
        # 3) Özel alanların davranışı: alanı söylemek yetmez, ne yapılacağını da söyle
        "'kullanicida_var' false ise cevabına o malzemenin mutfakta olmadığını söyleyerek başla. "
        "'veritabaninda_var' false ise araçtan gelen 'talimat' alanına BİREBİR uy. "
        # 4) Etiket kuralı: veriye bağlı, LLM'in yorumuna değil
        "'kaynak': 'veritabani' olan tariflere ASLA '💡 Asistan önerisi' etiketi koyma. "
        # 5) Ne yapmaz
        "Bu araç yeni tarif üretmez ve stokta değişiklik yapmaz."
    ),
    parameters={
        "type": "object",
        "properties": {
            "ingredient": {
                "type": "string",
                # Sadece açık uçlu modda kullanılır
                "description": (
                    "Opsiyonel, sadece AÇIK UÇLU modda. TEK bir malzemenin yalın, ek almamış hali, küçük harfle "
                    "('domateslerle' değil 'domates', 'ıspanağım' değil 'ıspanak'). "
                    "Kullanıcı birden fazla malzeme sayarsa en acil olanı gönder ya da filtresiz çağır."
                ),
            },
            "dish_name": {
                "type": "string",
                "description": (
                    "Opsiyonel, sadece BELİRLİ YEMEK modunda. Kullanıcının istediği yemeğin yalın adı, küçük harfle "
                    "('menemeni' değil 'menemen'). Açık uçlu sorularda bu parametreyi KULLANMA."
                ),
            },
        },
        "required": [],
    },
)
def search_recipes(
    db: Session,
    user_id: int,
    ingredient: Optional[str] = None,
    dish_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Kullanıcının kilerindeki malzemelere göre eşleşen tarifleri getirir.
    
    Kurallar:
    - dish_name verildiğinde:
      - Veritabanındaki tarif adlarında turkish_lower ile arama yapılır.
      - BULUNURSA: Yalnızca o tarif 'kaynak': 'veritabani' bilgisiyle dönülür.
      - BULUNMAZSA: Başka hiçbir tarif dönülmez, 'veritabaninda_var': False ve asistan tarif üretme talimatı dönülür.
    - dish_name verilmediğinde (açık uçlu mod):
      - En fazla 5 tarif döndürülür, her birine 'kaynak': 'veritabani' eklenir.
      - 'ingredient' parametresi verildiğinde kullanıcının aktif kilerinde bu malzemenin
        olup olmadığı kontrol edilir ve 'kullanicida_var': True/False alanı eklenir.
      - 'eksik_malzemeler' listesi kesinlikle yalnızca kilerde bulunmayan veya yetersiz olan malzemeleri içerir.
    """
    recommendations = match_user_products_with_recipes(db=db, user_id=user_id)

    # 1. BELİRLİ YEMEK MODU (dish_name verildiğinde)
    if dish_name and dish_name.strip():
        cleaned_dish = dish_name.strip()
        dish_lower = turkish_lower(cleaned_dish)

        # Veritabanındaki tarif adlarında turkish_lower ile ara:
        # tam eşleşme veya tarif adı dish_name'i içeriyorsa / dish_name tarif adını içeriyorsa
        matched_rec = None
        for rec in recommendations:
            rec_lower = turkish_lower(rec.name)
            if rec_lower == dish_lower:
                matched_rec = rec
                break
        if not matched_rec:
            for rec in recommendations:
                rec_lower = turkish_lower(rec.name)
                if rec_lower in dish_lower or dish_lower in rec_lower:
                    matched_rec = rec
                    break

        if matched_rec:
            kilerdeki_malzemeler = [
                m.ingredient_name for m in matched_rec.matched_ingredients if m.is_sufficient
            ]
            yetersiz_malzemeler = [
                f"{m.ingredient_name} (yetersiz miktar)"
                for m in matched_rec.matched_ingredients
                if not m.is_sufficient and not getattr(m, "is_optional", False)
            ]
            hic_olmayanlar = [
                m.ingredient_name for m in matched_rec.missing_ingredients if not m.is_optional
            ]
            eksik_malzemeler = hic_olmayanlar + yetersiz_malzemeler
            opsiyonel_eksikler = [
                m.ingredient_name for m in matched_rec.missing_ingredients if m.is_optional
            ]

            return {
                "istenen_yemek": cleaned_dish,
                "veritabaninda_var": True,
                "tarif": {
                    "id": matched_rec.id,
                    "tarif_adi": matched_rec.name,
                    "eslesme_yuzdesi": float(matched_rec.match_percentage),
                    "pisirilebilir_mi": bool(matched_rec.can_prepare),
                    "toplam_sure_dakika": int(matched_rec.total_time),
                    "oncelik_puani": float(matched_rec.priority_score),
                    "kilerdeki_malzemeler": kilerdeki_malzemeler,
                    "eksik_malzemeler": eksik_malzemeler,
                    "opsiyonel_eksikler": opsiyonel_eksikler,
                    "kaynak": "veritabani",
                },
            }
        else:
            return {
                "istenen_yemek": cleaned_dish,
                "veritabaninda_var": False,
                "talimat": (
                    "Bu yemek veritabanında yok. Başka tarif önerme. "
                    "Kullanıcının istediği yemeğin tarifini ASİSTAN TARİFİ formatında "
                    "sen oluştur ve başına '💡 Asistan önerisi' etiketi koy."
                ),
            }

    kullanicida_var: Optional[bool] = None

    if ingredient and ingredient.strip():
        # Kullanıcının aktif ve tüketilebilir ürünlerinde bu malzemenin olup olmadığını kontrol et
        user_active_products = (
            db.query(Product)
            .filter(
                Product.user_id == user_id,
                Product.status == "active",
            )
            .all()
        )
        kullanicida_var = any(
            turkish_match(ingredient, p.name) for p in user_active_products
        )

        # Tarifleri filtrele (hem tarif adına hem tarif malzemelerine bak)
        filtered = []
        for rec in recommendations:
            has_ingredient = turkish_match(ingredient, rec.name) or any(
                turkish_match(ingredient, ing.ingredient_name) for ing in rec.ingredients
            )
            if has_ingredient:
                filtered.append(rec)
        recommendations = filtered

    # En fazla 5 tarif al
    top_recipes = recommendations[:5]

    tarif_listesi: List[Dict[str, Any]] = []
    for rec in top_recipes:
        # Kilerde tam ve yeterli olanlar
        kilerdeki_malzemeler = [
            m.ingredient_name for m in rec.matched_ingredients if m.is_sufficient
        ]
        # Kilerde olan ama miktarı yetersiz kalanlar
        yetersiz_malzemeler = [
            f"{m.ingredient_name} (yetersiz miktar)"
            for m in rec.matched_ingredients
            if not m.is_sufficient and not getattr(m, "is_optional", False)
        ]
        # Kilerde hiç bulunmayan zorunlu malzemeler
        hic_olmayanlar = [
            m.ingredient_name for m in rec.missing_ingredients if not m.is_optional
        ]

        # Eksik malzemeler listesi: Kilerde hiç olmayanlar + miktarı yetersiz olanlar
        eksik_malzemeler = hic_olmayanlar + yetersiz_malzemeler

        # Opsiyonel eksikler
        opsiyonel_eksikler = [
            m.ingredient_name for m in rec.missing_ingredients if m.is_optional
        ]

        tarif_listesi.append({
            "id": rec.id,
            "tarif_adi": rec.name,
            "eslesme_yuzdesi": float(rec.match_percentage),
            "pisirilebilir_mi": bool(rec.can_prepare),
            "toplam_sure_dakika": int(rec.total_time),
            "oncelik_puani": float(rec.priority_score),
            "kilerdeki_malzemeler": kilerdeki_malzemeler,
            "eksik_malzemeler": eksik_malzemeler,
            "opsiyonel_eksikler": opsiyonel_eksikler,
            "kaynak": "veritabani",
        })

    bilgi_notu = None
    if ingredient and kullanicida_var is False:
        bilgi_notu = (
            f"Kullanıcının mutfağında '{ingredient}' bulunmamaktadır. "
            "Listelenen tarifler genel katalogdan getirilmiştir. "
            "Kullanıcıya bu malzemenin mutfağında olmadığını açıkça söyle."
        )

    return {
        "kullanicida_var": kullanicida_var,
        "filtrelenen_malzeme": ingredient.strip() if ingredient else None,
        "tarifler": tarif_listesi,
        "toplam_bulunan_tarif": len(recommendations),
        "bilgi_notu": bilgi_notu,
    }
