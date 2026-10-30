from decimal import Decimal
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.product import Product
from app.models.consumption_log import ConsumptionLog
from app.schemas.product import ProductCreate, ProductUpdate
from app.schemas.consumption import ConsumptionCreate


class InsufficientQuantityError(ValueError):
    """Raised when the consumed quantity exceeds the available product quantity."""
    pass


class ProductNotFoundError(ValueError):
    """Raised when a product is not found or does not belong to the user."""
    pass


def create_product(db: Session, user_id: int, product_in: ProductCreate) -> Product:
    """Creates a new product record for the specified user."""
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
    storage_location: Optional[str] = None
) -> List[Product]:
    """
    Returns products strictly isolated to the specified user.
    Supports filtering by category, status, and storage location.
    """
    query = db.query(Product).filter(Product.user_id == user_id)

    if category_id is not None:
        query = query.filter(Product.category_id == category_id)

    if status is not None:
        query = query.filter(Product.status == status)

    if storage_location is not None:
        query = query.filter(Product.storage_location == storage_location)

    return query.order_by(Product.expiry_date.asc().nullslast(), Product.created_at.desc()).all()


def get_product_by_id(db: Session, user_id: int, product_id: int) -> Optional[Product]:
    """Returns a specific product, ensuring it belongs to the given user."""
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
    """Updates an existing product for the specified user."""
    product = get_product_by_id(db, user_id, product_id)
    if not product:
        return None

    update_data = product_in.model_dump(exclude_unset=True)
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
    Deletes a product while preserving historical consumption logs.
    - If soft=True, updates status to 'discarded'.
    - If soft=False, deletes the product; foreign keys on consumption_logs set product_id to NULL.
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
    Records consumption in a single atomic transaction:
    1. Verifies user ownership of product.
    2. Validates available quantity >= requested quantity.
    3. Decreases product quantity.
    4. If remaining quantity == 0, updates product status to 'consumed'.
    5. Inserts consumption log.
    6. Commits transaction or rolls back on any error.
    """
    # Verify product ownership
    product = get_product_by_id(db, user_id, consumption_in.product_id)
    if not product:
        raise ProductNotFoundError("Ürün bulunamadı veya bu kullanıcıya ait değil.")

    quantity_used = Decimal(str(consumption_in.quantity_used))

    if quantity_used <= 0:
        raise ValueError("Tüketim miktarı sıfırdan büyük olmalıdır.")

    if product.quantity < quantity_used:
        raise InsufficientQuantityError(
            f"Yetersiz ürün miktarı! Mevcut: {product.quantity} {product.unit}, İstenen: {quantity_used} {product.unit}"
        )

    try:
        # Atomic deduction
        new_quantity = product.quantity - quantity_used
        product.quantity = new_quantity

        if new_quantity == 0:
            product.status = "consumed"

        # Create audit log
        log = ConsumptionLog(
            product_id=product.id,
            recipe_id=consumption_in.recipe_id,
            quantity_used=quantity_used,
            unit=consumption_in.unit,
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
