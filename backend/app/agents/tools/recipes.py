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
        "Kullanıcının mutfağındaki malzemelerle yapabileceği yemek tariflerini akıllı eşleştirme puanına göre listeler. "
        "Bozulmak üzere olan ürünleri kullanan ve eldeki malzemelerle hemen pişirilebilecek tarifleri öne çıkarır. "
        "İsteğe bağlı olarak belirli bir malzemeye göre (örn: 'domates', 'yoğurt', 'ıspanak') filtreleme yapabilir. "
        "Aranan malzemenin kullanıcının mutfağında olup olmadığını 'kullanicida_var' alanı ile belirtir."
    ),
    parameters={
        "type": "object",
        "properties": {
            "ingredient": {
                "type": "string",
                "description": "Opsiyonel filtre. Belirli bir malzemeyi içeren tarifleri bulmak için malzeme adı (örn: 'domates', 'ıspanak', 'incir').",
            }
        },
        "required": [],
    },
)
def search_recipes(
    db: Session,
    user_id: int,
    ingredient: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Kullanıcının kilerindeki malzemelere göre eşleşen tarifleri getirir.
    
    Kurallar:
    - En fazla 5 tarif döndürülür.
    - 'ingredient' parametresi verildiğinde kullanıcının aktif kilerinde bu malzemenin
      olup olmadığı kontrol edilir ve 'kullanicida_var': True/False alanı eklenir.
    - 'eksik_malzemeler' listesi kesinlikle yalnızca kilerde bulunmayan veya yetersiz olan malzemeleri içerir.
    """
    recommendations = match_user_products_with_recipes(db=db, user_id=user_id)

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
