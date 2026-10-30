import sys
import os

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import init_db, SessionLocal
from app.services.category_service import seed_categories


def main():
    print("Initializing DÖNGÜ database...")
    init_db()
    print("Database tables initialized.")

    db = SessionLocal()
    try:
        categories = seed_categories(db)
        print(f"Categories successfully seeded! Total categories: {len(categories)}")
        for cat in categories:
            print(f" - [{cat.id}] {cat.name}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
