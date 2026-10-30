from decimal import Decimal
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.product import Product
from app.models.category import Category
from app.models.consumption_log import ConsumptionLog
from app.schemas.product import ProductCreate, ProductUpdate
from app.schemas.consumption import ConsumptionCreate


class InsufficientQuantityError(ValueError):
    """Kullanıcının tüketmek istediği miktar eldeki mevcut ürün miktarından fazla olduğunda fırlatılır."""
    pass


class ProductNotFoundError(ValueError):
    """İstenen ürün veritabanında bulunamadığında veya sorgulayan kullanıcıya ait olmadığında fırlatılır."""
    pass


class CategoryNotFoundError(ValueError):
    """Belirtilen kategori ID'si veritabanında bulunamadığında fırlatılır."""
    pass


def create_product(db: Session, user_id: int, product_in: ProductCreate) -> Product:
    """
    Belirtilen kullanıcı için mutfağa yeni bir gıda ürünü kaydeder.
    
    Kontroller:
    - Kategori ID'sinin geçerli bir kategoriye ait olduğunu doğrular.
    - Ürünü 'active' (kullanımda) statüsü ile veritabanına ekler.
    """
    category = db.query(Category).filter(Category.id == product_in.category_id).first()
    if not category:
        raise CategoryNotFoundError(f"{product_in.category_id} ID'li kategori bulunamadı.")

    product = Product(
        user_id=user_id,
        category_id=product_in.category_id,
        name=product_in.name.strip(),
        quantity=product_in.quantity,
        unit=product_in.unit.strip(),
        expiry_date=product_in.expiry_date,
        date_type=product_in.date_type,
        storage_location=product_in.storage_location,
        status="active",
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def get_user_products(
    db: Session,
    user_id: int,
    category_id: Optional[int] = None,
    status: Optional[str] = "active",
    storage_location: Optional[str] = None,
    search: Optional[str] = None
) -> List[Product]:
    """
    Kullanıcının envanterindeki gıdaları filtreler ve listeler.
    
    Güvenlik ve İzolasyon:
    - Sadece ilgili `user_id`'ye ait ürünleri getirir; kullanıcılar birbirinin ürünlerini göremez.
    - Kategori, ürün durumu (aktif, tüketildi, atıldı), saklama yeri ve isim araması (search) filtrelerini uygular.
    - Filtreler birlikte ve dinamik olarak çalışır.
    - Son tüketim tarihi en yakın olan ürünleri öncelikli değerlendirme amacıyla en üstte listeler.
    """
    query = db.query(Product).filter(Product.user_id == user_id)

    if category_id is not None:
        query = query.filter(Product.category_id == category_id)

    if status is not None:
        query = query.filter(Product.status == status)

    if storage_location is not None:
        query = query.filter(Product.storage_location == storage_location)

    if search is not None and search.strip():
        # Büyük/küçük harf duyarsız arama
        search_pattern = f"%{search.strip()}%"
        query = query.filter(Product.name.ilike(search_pattern))

    return query.order_by(Product.expiry_date.asc().nullslast(), Product.created_at.desc()).all()


def get_product_by_id(db: Session, user_id: int, product_id: int) -> Optional[Product]:
    """
    Belirli bir ürünü ID'sine göre getirir.
    Ürünün kesinlikle bu kullanıcıya ait olup olmadığını doğrular (veri izolasyonu).
    """
    return db.query(Product).filter(
        Product.id == product_id,
        Product.user_id == user_id
    ).first()


def update_product(
    db: Session,
    user_id: int,
    product_id: int,
    product_in: ProductUpdate
) -> Optional[Product]:
    """
    Kullanıcının mevcut bir ürünündeki bilgileri (miktar, saklama yeri, son tarih vb.) günceller.
    
    Kontroller:
    - Ürünün kullanıcıya ait olup olmadığını doğrular.
    - Kategori ID'si güncelleniyorsa, yeni kategorinin varlığını kontrol eder.
    - Sadece kullanıcının gönderdiği (None olmayan) alanlar güncellenir.
    """
    product = get_product_by_id(db, user_id, product_id)
    if not product:
        return None

    update_data = product_in.model_dump(exclude_unset=True)

    if "category_id" in update_data and update_data["category_id"] is not None:
        category = db.query(Category).filter(Category.id == update_data["category_id"]).first()
        if not category:
            raise CategoryNotFoundError(f"{update_data['category_id']} ID'li kategori bulunamadı.")

    for field, value in update_data.items():
        setattr(product, field, value)

    db.commit()
    db.refresh(product)
    return product


def delete_product(
    db: Session,
    user_id: int,
    product_id: int,
    soft: bool = False
) -> bool:
    """
    Ürünü kilerden kaldırır.
    
    Tüketim Geçmişini Koruma İlkesi:
    - soft=True ise: Ürün durumunu 'discarded' (atıldı) yapar, veritabanından silmez.
    - soft=False ise: Ürün tablodan silinir ancak 'consumption_logs' tablosundaki eski tüketim
      kayıtları silinmez; yabancı anahtar (product_id) SET NULL yapılarak geçmiş istatistik korunur.
    """
    product = get_product_by_id(db, user_id, product_id)
    if not product:
        return False

    if soft:
        product.status = "discarded"
        db.commit()
    else:
        db.delete(product)
        db.commit()

    return True


def consume_product(
    db: Session,
    user_id: int,
    consumption_in: ConsumptionCreate
) -> tuple[Product, ConsumptionLog]:
    """
    Gıda tüketimini veya tarif kullanımını tek bir güvenli işlem (transaction) altında kaydeder.
    
    İş Akışı ve Kurallar:
    1. Ürünün kullanıcıya ait olduğunu doğrular.
    2. Tüketilmek istenen miktarın pozitif olduğunu ve eldeki miktarı aşmadığını doğrular.
    3. Ürünün mevcut miktarından tüketilen miktarı düşer.
    4. Kalan miktar sıfırlandığında ürünün durumunu otomatik olarak 'consumed' yapar.
    5. Tüketim günlüğüne (consumption_logs) denetim kaydını ekler.
    6. İşlemleri tek transaction içinde kaydeder (commit); hata anında tüm değişiklikleri geri alır (rollback).
    """
    product = get_product_by_id(db, user_id, consumption_in.product_id)
    if not product:
        raise ProductNotFoundError("Ürün bulunamadı veya bu kullanıcıya ait değil.")

    quantity_used_input = Decimal(str(consumption_in.quantity_used))

    if quantity_used_input <= 0:
        raise ValueError("Tüketim miktarı sıfırdan büyük olmalıdır.")

    # Mutfak ölçü birimi dönüşümü (ör: kaşık -> kg, gram -> kg, adet -> gr)
    from app.services.unit_converter import convert_unit
    deduction_in_stock_unit = convert_unit(
        quantity=quantity_used_input,
        from_unit=consumption_in.unit,
        to_unit=product.unit,
        item_name=product.name,
    )

    TOLERANCE = Decimal("0.005")
    if product.quantity < deduction_in_stock_unit:
        if (deduction_in_stock_unit - product.quantity) > TOLERANCE:
            raise InsufficientQuantityError(
                f"Yetersiz ürün miktarı! Mevcut: {product.quantity} {product.unit}, "
                f"İstenen: {deduction_in_stock_unit.quantize(Decimal('0.01'))} {product.unit} "
                f"({consumption_in.quantity_used} {consumption_in.unit})"
            )

    try:
        # Miktar düşümü
        new_quantity = product.quantity - deduction_in_stock_unit
        if new_quantity <= TOLERANCE:
            product.quantity = Decimal("0.00")
            product.status = "consumed"
        else:
            product.quantity = new_quantity.quantize(Decimal("0.01"))

        # Tüketim günlüğü kaydı oluştur
        log = ConsumptionLog(
            product_id=product.id,
            recipe_id=consumption_in.recipe_id,
            quantity_used=deduction_in_stock_unit.quantize(Decimal("0.01")),
            unit=product.unit,
            action_type=consumption_in.action_type,
        )
        db.add(log)
        db.commit()
        db.refresh(product)
        db.refresh(log)
        return product, log

    except Exception:
        db.rollback()
        raise
