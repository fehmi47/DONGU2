from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.category import Category

DEFAULT_CATEGORIES = [
    "Sebzeler",
    "Meyveler",
    "Süt ve Süt Ürünleri",
    "Et, Tavuk ve Yumurta",
    "Tahıl ve Unlu Mamuller",
    "Bakliyat",
    "Yağ, Sos ve Baharat",
    "Dondurulmuş Ürünler",
    "Atıştırmalıklar",
    "İçecekler",
    "Diğer",
]


def seed_categories(db: Session) -> List[Category]:
    """
    Idempotent category seeding.
    Only adds categories that don't already exist.
    Preserves existing records and IDs.
    """
    existing = {c.name for c in db.query(Category).all()}
    added = []

    for name in DEFAULT_CATEGORIES:
        if name not in existing:
            cat = Category(name=name, description=f"{name} kategorisi")
            db.add(cat)
            added.append(cat)

    if added:
        db.commit()
        for cat in added:
            db.refresh(cat)

    return db.query(Category).order_by(Category.id).all()


def get_categories(db: Session) -> List[Category]:
    """Returns all categories ordered by ID."""
    return db.query(Category).order_by(Category.id).all()


def get_category_by_id(db: Session, category_id: int) -> Optional[Category]:
    """Returns category by its primary key ID."""
    return db.query(Category).filter(Category.id == category_id).first()
