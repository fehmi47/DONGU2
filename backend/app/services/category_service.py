from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.category import Category

# Sistemin varsayılan gıda kategorileri listesi
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
    Sistemin ihtiyaç duyduğu temel gıda kategorilerini veritabanına ekler.
    
    Çalışma Mantığı:
    - Veritabanında kayıtlı mevcut kategorileri kontrol eder.
    - Sadece henüz eklenmemiş olan kategorileri yeni kayıt olarak ekler (idempotent).
    - Mevcut kayıtları ve atanmış ID'leri asla bozmaz; tekrar tekrar çalıştırılabilir.
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
    """
    Sistemde kayıtlı olan tüm gıda kategorilerini ID sırasına göre listeler.
    Ürün ekleme formlarında veya kategori bazlı filtreleme menülerinde kullanılır.
    """
    return db.query(Category).order_by(Category.id).all()


def get_category_by_id(db: Session, category_id: int) -> Optional[Category]:
    """
    Belirtilen ID'ye sahip kategoriyi veritabanından getirir.
    Kategori bulunamazsa None döndürür.
    """
    return db.query(Category).filter(Category.id == category_id).first()

