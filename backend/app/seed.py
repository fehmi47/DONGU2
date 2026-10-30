import sys
import os

# Backend kök dizinini sys.path'e ekleme
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import init_db, SessionLocal
from app.services.category_service import seed_categories
from app.services.user_service import seed_users
from app.data.seed_recipes import seed_recipes
from app.data.seed_sample_products import seed_demo_products, seed_demo_consumptions


def main():
    print("DÖNGÜ veritabanı başlatılıyor...")
    init_db()
    print("Veritabanı tabloları hazırlandı.")

    db = SessionLocal()
    try:
        # 1. Kullanıcıları yükle
        users = seed_users(db)
        print(f"Kullanıcılar yüklendi! Toplam kullanıcı: {len(users)}")
        for u in users:
            print(f" - [{u.id}] {u.username} ({u.email})")

        # 2. Kategorileri yükle
        categories = seed_categories(db)
        print(f"Kategoriler yüklendi! Toplam kategori: {len(categories)}")

        # 3. Tarifleri yükle
        recipes = seed_recipes(db)
        print(f"Tarifler yüklendi! Toplam tarif: {len(recipes)}")

        # 4. Demo kullanıcısı için örnek ürünleri yükle
        sample_prods = seed_demo_products(db, user_id=1)
        print(f"Demo kullanıcısı için {len(sample_prods)} örnek ürün yüklendi.")

        # 5. Demo kullanıcısı için tüketim ve çevresel kazanım kayıtlarını yükle
        sample_logs = seed_demo_consumptions(db, user_id=1)
        print(f"Demo kullanıcısı için {len(sample_logs)} tüketim kaydı yüklendi.")

        print("\nTUM BASLANGIC VERILERI BASARIYLA HAZIRLANDI!")
    finally:
        db.close()


if __name__ == "__main__":
    main()
