from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List
from sqlalchemy.orm import Session

from app.models.product import Product
from app.models.category import Category
from app.models.consumption_log import ConsumptionLog


def seed_demo_products(db: Session, user_id: int = 1) -> List[Product]:
    """
    Demo kullanıcısı için zengin ve gerçekçi örnek mutfak ürünleri ekler.
    Tarihi yaklaşan, orta vadeli ve tarihsiz ürünler barındırır.
    Zaten ürün eklenmişse tekrar eklemez (idempotent).
    """
    existing_count = db.query(Product).filter(Product.user_id == user_id).count()
    if existing_count > 0:
        return db.query(Product).filter(Product.user_id == user_id).all()

    today = date.today()

    # Kategori adından ID bulucu
    cat_map = {c.name: c.id for c in db.query(Category).all()}
    sebze_id = cat_map.get("Sebzeler", 1)
    sut_id = cat_map.get("Süt ve Süt Ürünleri", 3)
    et_yumurta_id = cat_map.get("Et, Tavuk ve Yumurta", 4)
    bakliyat_id = cat_map.get("Bakliyat", 6)
    yag_sos_id = cat_map.get("Yağ, Sos ve Baharat", 7)

    sample_products = [
        # 1. Acil (1 gün kalmış) Domates -> Menemen önerisini tetikler
        Product(
            user_id=user_id,
            category_id=sebze_id,
            name="Salkım Domates",
            quantity=Decimal("3.00"),
            unit="adet",
            expiry_date=today + timedelta(days=1),
            date_type="STT",
            storage_location="fridge",
            status="active"
        ),
        # 2. Acil (2 gün kalmış) Yoğurt
        Product(
            user_id=user_id,
            category_id=sut_id,
            name="Süzme Yoğurt",
            quantity=Decimal("500.00"),
            unit="gram",
            expiry_date=today + timedelta(days=2),
            date_type="STT",
            storage_location="fridge",
            status="active"
        ),
        # 3. Yüksek Öncelikli (3 gün kalmış) Yeşil Köy Biberi
        Product(
            user_id=user_id,
            category_id=sebze_id,
            name="Yeşil Köy Biberi",
            quantity=Decimal("4.00"),
            unit="adet",
            expiry_date=today + timedelta(days=3),
            date_type="STT",
            storage_location="fridge",
            status="active"
        ),
        # 4. Orta Öncelikli (7 gün kalmış) Yumurta
        Product(
            user_id=user_id,
            category_id=et_yumurta_id,
            name="Organik Yumurta",
            quantity=Decimal("6.00"),
            unit="adet",
            expiry_date=today + timedelta(days=7),
            date_type="STT",
            storage_location="fridge",
            status="active"
        ),
        # 5. TETT geçmiş Bakliyat (Duyusal kontrol uyarısı ile)
        Product(
            user_id=user_id,
            category_id=bakliyat_id,
            name="Kırmızı Mercimek",
            quantity=Decimal("1.00"),
            unit="kg",
            expiry_date=today - timedelta(days=4),
            date_type="TETT",
            storage_location="pantry",
            status="active"
        ),
        # 6. Tarihsiz Kaya Tuzu
        Product(
            user_id=user_id,
            category_id=yag_sos_id,
            name="Öğütülmüş Kaya Tuzu",
            quantity=Decimal("1.00"),
            unit="kg",
            expiry_date=None,
            date_type="NONE",
            storage_location="pantry",
            status="active"
        ),
    ]

    db.add_all(sample_products)
    db.commit()

    # Tüketim ve çevresel kazanım kayıtlarını da otomatik ekle
    seed_demo_consumptions(db, user_id=user_id)

    return sample_products


def seed_demo_consumptions(db: Session, user_id: int = 1) -> List[ConsumptionLog]:
    """
    Demo kullanıcısı için zengin tüketim geçmişi ve çevresel etki verileri ekler.
    Tasarım hedefleri:
    - Toplam kurtarılan gıda: 5.45 kg
    - Haftalık kurtarılan gıda: 1.90 kg
    - Tamamlanan tarif: 3 adet (Fırında Karışık Sebze, Menemen, Kırmızı Mercimek Çorbası)
    - Önlenen CO2 salınımı: 13.62 kg
    - Kurtarılan su: 4905.0 L
    - Haftalık trend zirve günü: Perşembe (1.0 kg)
    """
    existing_count = (
        db.query(ConsumptionLog)
        .join(Product, ConsumptionLog.product_id == Product.id)
        .filter(Product.user_id == user_id)
        .count()
    )
    if existing_count > 0:
        return (
            db.query(ConsumptionLog)
            .join(Product, ConsumptionLog.product_id == Product.id)
            .filter(Product.user_id == user_id)
            .all()
        )

    cat_map = {c.name: c.id for c in db.query(Category).all()}
    sebze_id = cat_map.get("Sebzeler", 1)
    sut_id = cat_map.get("Süt ve Süt Ürünleri", 3)
    tahil_id = cat_map.get("Tahıl ve Unlu Mamuller", 5)
    bakliyat_id = cat_map.get("Bakliyat", 6)

    # Geçmişte tüketilip bitirilmiş ürün kayıtları
    consumed_prods = [
        Product(user_id=user_id, category_id=sebze_id, name="Köy Biberi ve Patlıcan", quantity=Decimal("0.00"), unit="kg", status="consumed", storage_location="fridge"),
        Product(user_id=user_id, category_id=sut_id, name="Süzme Yoğurt", quantity=Decimal("0.00"), unit="kg", status="consumed", storage_location="fridge"),
        Product(user_id=user_id, category_id=sebze_id, name="Çeri Domates", quantity=Decimal("0.00"), unit="kg", status="consumed", storage_location="fridge"),
        Product(user_id=user_id, category_id=sebze_id, name="Tarla Domatesi", quantity=Decimal("0.00"), unit="kg", status="consumed", storage_location="fridge"),
        Product(user_id=user_id, category_id=sebze_id, name="Yeşil Sivri Biber", quantity=Decimal("0.00"), unit="kg", status="consumed", storage_location="fridge"),
        Product(user_id=user_id, category_id=sebze_id, name="Havuç", quantity=Decimal("0.00"), unit="kg", status="consumed", storage_location="fridge"),
        Product(user_id=user_id, category_id=bakliyat_id, name="Kırmızı Mercimek", quantity=Decimal("0.00"), unit="kg", status="consumed", storage_location="pantry"),
        Product(user_id=user_id, category_id=tahil_id, name="Tam Buğday Ekmeği", quantity=Decimal("0.00"), unit="kg", status="consumed", storage_location="pantry"),
    ]
    db.add_all(consumed_prods)
    db.commit()

    now = datetime.utcnow()
    # Son 6 günün günlerini haritala
    days_back = {}
    for i in range(1, 7):
        d = now - timedelta(days=i)
        days_back[d.weekday()] = d

    # Perşembe (3): 1.0 kg (Zirve kurtarma günü)
    # Çarşamba (2): 0.2 kg
    # Salı (1): 0.1 kg
    # Pazartesi (0): 0.3 kg
    # Pazar (6): 0.2 kg
    # Cumartesi (5): 0.1 kg
    # Toplam son 7 gün: 1.90 kg
    thursday_date = days_back.get(3, now - timedelta(days=1))
    wednesday_date = days_back.get(2, now - timedelta(days=2))
    tuesday_date = days_back.get(1, now - timedelta(days=3))
    monday_date = days_back.get(0, now - timedelta(days=4))
    sunday_date = days_back.get(6, now - timedelta(days=5))
    saturday_date = days_back.get(5, now - timedelta(days=6))

    sample_logs = [
        ConsumptionLog(product_id=consumed_prods[0].id, recipe_id=18, quantity_used=Decimal("1.00"), unit="kg", action_type="recipe_used", recorded_at=thursday_date),
        ConsumptionLog(product_id=consumed_prods[1].id, recipe_id=None, quantity_used=Decimal("0.20"), unit="kg", action_type="consumed", recorded_at=wednesday_date),
        ConsumptionLog(product_id=consumed_prods[2].id, recipe_id=None, quantity_used=Decimal("0.10"), unit="kg", action_type="consumed", recorded_at=tuesday_date),
        ConsumptionLog(product_id=consumed_prods[3].id, recipe_id=1, quantity_used=Decimal("0.30"), unit="kg", action_type="recipe_used", recorded_at=monday_date),
        ConsumptionLog(product_id=consumed_prods[4].id, recipe_id=None, quantity_used=Decimal("0.20"), unit="kg", action_type="consumed", recorded_at=sunday_date),
        ConsumptionLog(product_id=consumed_prods[5].id, recipe_id=None, quantity_used=Decimal("0.10"), unit="kg", action_type="consumed", recorded_at=saturday_date),
        ConsumptionLog(product_id=consumed_prods[6].id, recipe_id=4, quantity_used=Decimal("1.55"), unit="kg", action_type="recipe_used", recorded_at=now - timedelta(days=12)),
        ConsumptionLog(product_id=consumed_prods[7].id, recipe_id=None, quantity_used=Decimal("2.00"), unit="kg", action_type="consumed", recorded_at=now - timedelta(days=16)),
    ]

    db.add_all(sample_logs)
    db.commit()
    return sample_logs
