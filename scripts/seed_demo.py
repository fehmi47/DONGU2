"""
DÖNGÜ - Demo Verileri Tohumlama Scripti (scripts/seed_demo.py)

1. Kullanıcı 1'in aktif ürünlerine tarihine 2 gün kalmış "Ispanak" (500 g, buzdolabı, STT) ekler.
2. Kullanıcı 1 için son 30 güne yayılmış 14 adet gerçekçi tüketim kaydı ekler.
Tekrar çalıştırıldığında kayıtları çoğaltmaz (idempotent).
"""

import sys
import os
from datetime import datetime, timedelta, date
from decimal import Decimal

# Proje backend dizinini Python path'e ekle
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.database import SessionLocal
from app.models.product import Product
from app.models.consumption_log import ConsumptionLog
from app.models.recipe import Recipe
from app.models.category import Category


def seed_demo_ispanak(db, user_id: int = 1):
    """
    Demo senaryosu için Kullanıcı 1'e tarihine 2 gün kalmış aktif Ispanak ekler.
    İdempotenttir; ürün zaten aktifse mükerrer oluşturmaz.
    """
    existing_ispanak = (
        db.query(Product)
        .filter(
            Product.user_id == user_id,
            Product.name == "Ispanak",
            Product.status == "active",
        )
        .first()
    )

    cat_sebze = db.query(Category).filter(Category.name.like("%Sebze%")).first()
    category_id = cat_sebze.id if cat_sebze else 1
    target_expiry = date.today() + timedelta(days=2)

    if not existing_ispanak:
        new_ispanak = Product(
            user_id=user_id,
            category_id=category_id,
            name="Ispanak",
            quantity=Decimal("500.0"),
            unit="gram",
            storage_location="fridge",
            status="active",
            date_type="STT",
            expiry_date=target_expiry,
        )
        db.add(new_ispanak)
        db.commit()
        print(f"[seed_demo] Kullanıcı {user_id} için 2 gün kalmış aktif 'Ispanak' (500 gram, buzdolabı) eklendi.")
    else:
        # Tarihini ve miktarını demo senaryosuna göre güncelle
        existing_ispanak.expiry_date = target_expiry
        existing_ispanak.quantity = Decimal("500.0")
        existing_ispanak.storage_location = "fridge"
        existing_ispanak.unit = "gram"
        db.commit()
        print(f"[seed_demo] Kullanıcı {user_id} için aktif 'Ispanak' zaten mevcut (tarih ve miktar doğrulandı).")


def seed_demo_consumption():
    db = SessionLocal()
    try:
        user_id = 1

        # 1. Aktif Ispanak ürününü ekle / doğrula
        seed_demo_ispanak(db, user_id=user_id)

        # 2. Tüketim geçmişi idempotency kontrolü
        existing_logs_count = (
            db.query(ConsumptionLog)
            .join(Product, ConsumptionLog.product_id == Product.id)
            .filter(Product.user_id == user_id)
            .count()
        )
        if existing_logs_count >= 10:
            print(f"[seed_demo] Kullanıcı {user_id} için zaten {existing_logs_count} adet tüketim kaydı mevcut. Tüketim logları atlandı.")
            return

        now = datetime.utcnow()

        # Mevcut tarifleri al
        menemen = db.query(Recipe).filter(Recipe.name.like("%Menemen%")).first()
        mercimek_corbasi = db.query(Recipe).filter(Recipe.name.like("%Mercimek Çorbası%")).first()
        sebzeli_makarna = db.query(Recipe).filter(Recipe.name.like("%Sebzeli Makarna%")).first()

        menemen_id = menemen.id if menemen else None
        mercimek_id = mercimek_corbasi.id if mercimek_corbasi else None
        makarna_id = sebzeli_makarna.id if sebzeli_makarna else None

        # Tüketim geçmişi için ürün tanımları
        demo_products_data = [
            {"name": "Amasya Elması", "category_id": 1, "unit": "kg", "storage": "pantry"},
            {"name": "Günlük Tam Yağlı Süt", "category_id": 3, "unit": "litre", "storage": "fridge"},
            {"name": "Köy Yumurtası", "category_id": 4, "unit": "adet", "storage": "fridge"},
            {"name": "Tavuk Bonfile", "category_id": 2, "unit": "gram", "storage": "fridge"},
            {"name": "Burgu Makarna", "category_id": 6, "unit": "gram", "storage": "pantry"},
            {"name": "Kırmızı Mercimek", "category_id": 6, "unit": "kg", "storage": "pantry"},
            {"name": "Kuru Soğan", "category_id": 1, "unit": "kg", "storage": "pantry"},
            {"name": "Havuç", "category_id": 1, "unit": "kg", "storage": "fridge"},
            {"name": "Sızma Zeytinyağı", "category_id": 5, "unit": "mililitre", "storage": "pantry"},
            {"name": "Beyaz Peynir", "category_id": 3, "unit": "gram", "storage": "fridge"},
        ]

        # Ürünleri oluştur veya mevcutları eşle
        product_map = {}
        for pdata in demo_products_data:
            prod = (
                db.query(Product)
                .filter(Product.user_id == user_id, Product.name == pdata["name"])
                .first()
            )
            if not prod:
                prod = Product(
                    user_id=user_id,
                    category_id=pdata["category_id"],
                    name=pdata["name"],
                    quantity=Decimal("0.0"),
                    unit=pdata["unit"],
                    storage_location=pdata["storage"],
                    status="consumed",
                    date_type="NONE",
                )
                db.add(prod)
                db.flush()
            product_map[pdata["name"]] = prod

        # 14 adet son 30 güne dağıtılmış gerçekçi tüketim kaydı
        consumption_schedule = [
            (28, "Kuru Soğan", Decimal("0.30"), "kg", "consumed", None),
            (26, "Amasya Elması", Decimal("0.50"), "kg", "consumed", None),
            (24, "Burgu Makarna", Decimal("400.00"), "gram", "recipe_used", makarna_id),
            (22, "Günlük Tam Yağlı Süt", Decimal("0.50"), "litre", "consumed", None),
            (20, "Tavuk Bonfile", Decimal("600.00"), "gram", "consumed", None),
            (18, "Havuç", Decimal("0.35"), "kg", "consumed", None),
            (16, "Köy Yumurtası", Decimal("3.00"), "adet", "recipe_used", menemen_id),
            (14, "Kırmızı Mercimek", Decimal("0.25"), "kg", "recipe_used", mercimek_id),
            (12, "Beyaz Peynir", Decimal("200.00"), "gram", "consumed", None),
            (10, "Sızma Zeytinyağı", Decimal("150.00"), "mililitre", "recipe_used", menemen_id),
            (8, "Amasya Elması", Decimal("0.40"), "kg", "consumed", None),
            (5, "Burgu Makarna", Decimal("300.00"), "gram", "consumed", None),
            (3, "Köy Yumurtası", Decimal("2.00"), "adet", "consumed", None),
            (1, "Günlük Tam Yağlı Süt", Decimal("1.00"), "litre", "consumed", None),
        ]

        added_count = 0
        for days_ago, prod_name, qty, unit, action, r_id in consumption_schedule:
            prod = product_map.get(prod_name)
            if not prod:
                continue

            rec_time = now - timedelta(days=days_ago, hours=2, minutes=15)
            log = ConsumptionLog(
                product_id=prod.id,
                recipe_id=r_id,
                quantity_used=qty,
                unit=unit,
                action_type=action,
                recorded_at=rec_time,
            )
            db.add(log)
            added_count += 1

        db.commit()
        print(f"[seed_demo] Başarılı! Kullanıcı {user_id} için {added_count} adet tüketim kaydı oluşturuldu.")

    except Exception as e:
        db.rollback()
        print(f"[seed_demo] Hata oluştu: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_demo_consumption()
