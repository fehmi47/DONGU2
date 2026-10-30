import sys
import os

# Backend kök dizinini sys.path'e ekleme
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import init_db, SessionLocal
from app.services.category_service import seed_categories
from app.data.seed_recipes import seed_recipes


def main():
    print("DÖNGÜ veritabanı başlatılıyor...")
    init_db()
    print("Veritabanı tabloları hazırlandı.")

    db = SessionLocal()
    try:
        categories = seed_categories(db)
        print(f"Kategoriler başarıyla yüklendi! Toplam kategori: {len(categories)}")

        recipes = seed_recipes(db)
        print(f"Tarifler başarıyla yüklendi! Toplam tarif: {len(recipes)}")
        for r in recipes[:5]:
            print(f" - [{r.id}] {r.name} ({len(r.ingredients)} malzeme)")
        if len(recipes) > 5:
            print(f" ... ve {len(recipes) - 5} tarif daha.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
