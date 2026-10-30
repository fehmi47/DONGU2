from datetime import date
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session

from app.models.product import Product
from app.schemas.product import ProductPriorityResponse, PriorityLevelLiteral


class PriorityEvaluationResult:
    """
    Ürün öncelik hesaplama sonucunu temsil eden dahili veri taşıyıcı sınıf.
    """
    def __init__(
        self,
        priority_level: PriorityLevelLiteral,
        days_remaining: Optional[int],
        priority_message: str,
        can_be_recommended: bool,
        sort_rank: int,
    ):
        self.priority_level = priority_level
        self.days_remaining = days_remaining
        self.priority_message = priority_message
        self.can_be_recommended = can_be_recommended
        self.sort_rank = sort_rank


def evaluate_product_priority(
    product: Product,
    reference_date: Optional[date] = None
) -> PriorityEvaluationResult:
    """
    Bir gıda ürününün tüketim önceliğini ve gıda güvenliği durumunu hesaplar.
    
    Önemli Kurallar:
    1. STT (Son Tüketim Tarihi):
       - Kesin mikrobiyolojik gıda güvenliği sınırıdır.
       - Tarih geçmişse: 'expired_stt' seviyesine alınır ve 'can_be_recommended = False' yapılır.
         Kesinlikle tarif önerilerine ve tüketime yönlendirilmez.
       - 0 - 2 gün: 'critical' (acil değerlendirilmeli).
       - 3 - 5 gün: 'high' (yüksek öncelikli).
       - 6 - 10 gün: 'medium' (orta öncelikli).
       - 10+ gün: 'low' (düşük öncelikli).
       
    2. TETT (Tavsiye Edilen Tüketim Tarihi):
       - Kalite ve tazelik göstergesidir; otomatik bozulma tarihi değildir.
       - Tarih geçmişse: 'high' seviyesinde değerlendirilir, 'can_be_recommended = True' bırakılır.
         Kullanıcıya duyusal kontrol (koku, görünüm, tat) yapması hatırlatılır.
       - 0 - 2 gün: 'critical'.
       - 3 - 5 gün: 'high'.
       - 6 - 10 gün: 'medium'.
       - 10+ gün: 'low'.
       
    3. NONE (Tarihsiz Ürünler):
       - Tarih hesabı yapılmaz; 'no_date' atanır ve 'days_remaining = None' döner.
    """
    ref_date = reference_date or date.today()

    # Tarihsiz ürün durumu
    if product.date_type == "NONE" or product.expiry_date is None:
        return PriorityEvaluationResult(
            priority_level="no_date",
            days_remaining=None,
            priority_message="Tarih bilgisi bulunmuyor. Ürünün fiziksel durumunu kontrol ederek dilediğiniz zaman tüketebilirsiniz.",
            can_be_recommended=True,
            sort_rank=5,  # Düşük öncelikli listeleme
        )

    # Kalan gün hesabı (tutarlı ve parametrik)
    days_remaining = (product.expiry_date - ref_date).days

    # STT (Son Tüketim Tarihi) Mantığı
    if product.date_type == "STT":
        if days_remaining < 0:
            return PriorityEvaluationResult(
                priority_level="expired_stt",
                days_remaining=days_remaining,
                priority_message=f"Son tüketim tarihi {abs(days_remaining)} gün önce geçti. Gıda güvenliği riski nedeniyle tüketilmesi veya tariflerde kullanılması önerilmez.",
                can_be_recommended=False,
                sort_rank=6,  # En sonda gösterilir; kullanıcının israf etmeden/ayırması için
            )
        elif days_remaining <= 2:
            msg = "Son tüketim tarihi bugün!" if days_remaining == 0 else f"Son tüketim tarihine {days_remaining} gün kaldı! Gıda güvenliği açısından acilen tüketilmelidir."
            return PriorityEvaluationResult(
                priority_level="critical",
                days_remaining=days_remaining,
                priority_message=msg,
                can_be_recommended=True,
                sort_rank=1,
            )
        elif days_remaining <= 5:
            return PriorityEvaluationResult(
                priority_level="high",
                days_remaining=days_remaining,
                priority_message=f"Son tüketim tarihine {days_remaining} gün kaldı. Yakın zamanda değerlendirilmesi tavsiye edilir.",
                can_be_recommended=True,
                sort_rank=2,
            )
        elif days_remaining <= 10:
            return PriorityEvaluationResult(
                priority_level="medium",
                days_remaining=days_remaining,
                priority_message=f"Son tüketim tarihine {days_remaining} gün var. Haftalık tüketim planınıza dahil edebilirsiniz.",
                can_be_recommended=True,
                sort_rank=3,
            )
        else:
            return PriorityEvaluationResult(
                priority_level="low",
                days_remaining=days_remaining,
                priority_message=f"Son tüketim tarihine {days_remaining} gün var. Güvenle muhafaza edilebilir.",
                can_be_recommended=True,
                sort_rank=4,
            )

    # TETT (Tavsiye Edilen Tüketim Tarihi) Mantığı
    else:  # TETT
        if days_remaining < 0:
            return PriorityEvaluationResult(
                priority_level="high",
                days_remaining=days_remaining,
                priority_message=f"Tavsiye edilen tüketim tarihi {abs(days_remaining)} gün önce geçmiş. Ürün otomatik olarak bozuk sayılmaz; ambalaj ve duyusal kontroller (koku, görünüş) yaparak güvenliyse öncelikle değerlendirin.",
                can_be_recommended=True,
                sort_rank=2,
            )
        elif days_remaining <= 2:
            msg = "Tavsiye edilen tüketim tarihi bugün doluyor!" if days_remaining == 0 else f"Tavsiye edilen tüketim tarihine {days_remaining} gün kaldı. Kalite ve besin değerini kaybetmeden öncelikli değerlendirin."
            return PriorityEvaluationResult(
                priority_level="critical",
                days_remaining=days_remaining,
                priority_message=msg,
                can_be_recommended=True,
                sort_rank=1,
            )
        elif days_remaining <= 5:
            return PriorityEvaluationResult(
                priority_level="high",
                days_remaining=days_remaining,
                priority_message=f"Tavsiye edilen tüketim tarihine {days_remaining} gün kaldı. Kısa süre içinde tüketilmesi önerilir.",
                can_be_recommended=True,
                sort_rank=2,
            )
        elif days_remaining <= 10:
            return PriorityEvaluationResult(
                priority_level="medium",
                days_remaining=days_remaining,
                priority_message=f"Tavsiye edilen tüketim tarihine {days_remaining} gün var.",
                can_be_recommended=True,
                sort_rank=3,
            )
        else:
            return PriorityEvaluationResult(
                priority_level="low",
                days_remaining=days_remaining,
                priority_message=f"Tavsiye edilen tüketim tarihine {days_remaining} gün var. Kalitesini korumaktadır.",
                can_be_recommended=True,
                sort_rank=4,
            )


def build_priority_response(
    product: Product,
    evaluation: PriorityEvaluationResult
) -> ProductPriorityResponse:
    """
    SQLAlchemy Product modeli ile öncelik değerlendirmesini birleştirerek
    ProductPriorityResponse Pydantic nesnesine dönüştürür.
    """
    return ProductPriorityResponse(
        id=product.id,
        user_id=product.user_id,
        category_id=product.category_id,
        name=product.name,
        quantity=product.quantity,
        unit=product.unit,
        expiry_date=product.expiry_date,
        date_type=product.date_type,
        storage_location=product.storage_location,
        status=product.status,
        created_at=product.created_at,
        updated_at=product.updated_at,
        category=product.category,
        priority_level=evaluation.priority_level,
        days_remaining=evaluation.days_remaining,
        priority_message=evaluation.priority_message,
        can_be_recommended=evaluation.can_be_recommended,
    )


def get_user_products_with_priority(
    db: Session,
    user_id: int,
    reference_date: Optional[date] = None
) -> List[ProductPriorityResponse]:
    """
    Kullanıcının tüm aktif ürünlerini çeker, her birinin öncelik seviyesini hesaplar
    ve aciliyet sırasına (sort_rank ve days_remaining) göre sıralayarak döner.
    """
    products = db.query(Product).filter(
        Product.user_id == user_id,
        Product.status == "active"
    ).all()

    evaluated_items = []
    for product in products:
        evaluation = evaluate_product_priority(product, reference_date=reference_date)
        response_item = build_priority_response(product, evaluation)
        # Sıralama anahtarı: (sort_rank, days_remaining if not None else 9999)
        sort_days = evaluation.days_remaining if evaluation.days_remaining is not None else 9999
        evaluated_items.append((evaluation.sort_rank, sort_days, response_item))

    # Aciliyet derecesine göre sırala
    evaluated_items.sort(key=lambda x: (x[0], x[1]))
    return [item[2] for item in evaluated_items]


def get_user_expiring_products(
    db: Session,
    user_id: int,
    days: int = 3,
    reference_date: Optional[date] = None
) -> List[ProductPriorityResponse]:
    """
    Kullanıcının aktif ürünleri arasında, belirtilen gün eşiği (`days`) içerisinde
    tarihi yaklaşan ürünleri filtreler ve öncelik bilgisiyle döner.
    """
    ref_date = reference_date or date.today()

    # Sadece tarihi olan ve aktif ürünler
    products = db.query(Product).filter(
        Product.user_id == user_id,
        Product.status == "active",
        Product.expiry_date.isnot(None)
    ).all()

    expiring_items = []
    for product in products:
        evaluation = evaluate_product_priority(product, reference_date=ref_date)
        # Kalan gün 0 ile eşik değer arasındaysa (veya TETT geçmişse)
        if evaluation.days_remaining is not None and 0 <= evaluation.days_remaining <= days:
            response_item = build_priority_response(product, evaluation)
            expiring_items.append((evaluation.sort_rank, evaluation.days_remaining, response_item))

    expiring_items.sort(key=lambda x: (x[0], x[1]))
    return [item[2] for item in expiring_items]


def get_single_product_priority(
    db: Session,
    user_id: int,
    product_id: int,
    reference_date: Optional[date] = None
) -> Optional[ProductPriorityResponse]:
    """
    Belirli bir ürünün kullanıcıya ait olduğunu doğrulayarak öncelik detayını döner.
    Ürün yoksa veya başka kullanıcıya aitse None döner.
    """
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.user_id == user_id
    ).first()

    if not product:
        return None

    evaluation = evaluate_product_priority(product, reference_date=reference_date)
    return build_priority_response(product, evaluation)
