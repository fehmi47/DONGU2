from datetime import date, timedelta
from decimal import Decimal
from typing import List
from sqlalchemy.orm import Session

from app.models.product import Product
from app.models.category import Category


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
    return sample_products
