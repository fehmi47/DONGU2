from datetime import date
from decimal import Decimal
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.user import User
from app.models.category import Category
from app.models.product import Product
from app.models.recipe import Recipe
from app.models.recipe_ingredient import RecipeIngredient
from app.models.consumption_log import ConsumptionLog
from app.models.notification import Notification

from app.schemas.product import ProductCreate, ProductUpdate
from app.schemas.consumption import ConsumptionCreate

from app.services.category_service import seed_categories, get_categories, DEFAULT_CATEGORIES
from app.services.product_service import (
    create_product,
    get_user_products,
    get_product_by_id,
    update_product,
    delete_product,
    consume_product,
    InsufficientQuantityError,
    ProductNotFoundError,
)


@pytest.fixture(scope="function")
def db_session():
    """Creates a fresh in-memory SQLite database with PRAGMA foreign_keys=ON for each test."""
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False}
    )

    @event.listens_for(test_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def sample_user(db_session):
    user = User(username="ipek", email="ipek@dongu.org", password_hash="hashed_secret_123")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def second_user(db_session):
    user = User(username="ahmet", email="ahmet@dongu.org", password_hash="hashed_secret_456")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def seeded_categories(db_session):
    return seed_categories(db_session)


# ------------------ TESTLER ------------------

def test_category_seeding_and_idempotency(db_session):
    """Test category seeding creates 11 categories and running again does not duplicate."""
    cats = seed_categories(db_session)
    assert len(cats) == 11
    assert [c.name for c in cats] == DEFAULT_CATEGORIES

    # Idempotency check: run seed again
    cats_second_run = seed_categories(db_session)
    assert len(cats_second_run) == 11
    assert db_session.query(Category).count() == 11


def test_sqlite_foreign_key_enforcement(db_session):
    """Foreign key enforcement: Inserting product with nonexistent user or category must fail."""
    invalid_product = Product(
        user_id=999,  # Nonexistent
        category_id=999,  # Nonexistent
        name="Elma",
        quantity=Decimal("5.00"),
        unit="adet",
        date_type="STT",
        storage_location="fridge",
        status="active"
    )
    db_session.add(invalid_product)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_user_unique_constraints(db_session, sample_user):
    """Username and email must be unique."""
    # Duplicate username
    dup_user = User(username="ipek", email="other@dongu.org", password_hash="hash")
    db_session.add(dup_user)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # Duplicate email
    dup_email = User(username="unique_user", email="ipek@dongu.org", password_hash="hash")
    db_session.add(dup_email)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_product_create_and_validation(db_session, sample_user, seeded_categories):
    """Test product creation with valid STT date."""
    category = seeded_categories[0]  # Sebzeler

    product_in = ProductCreate(
        category_id=category.id,
        name="Domates",
        quantity=Decimal("2.50"),
        unit="kg",
        expiry_date=date(2026, 11, 15),
        date_type="STT",
        storage_location="fridge"
    )
    product = create_product(db_session, sample_user.id, product_in)

    assert product.id is not None
    assert product.name == "Domates"
    assert product.quantity == Decimal("2.50")
    assert product.status == "active"
    assert product.user_id == sample_user.id
    assert product.category_id == category.id


def test_product_stt_requires_expiry_date():
    """Pydantic validation: STT or TETT without expiry date must raise validation error."""
    with pytest.raises(ValueError, match="STT seçildiğinde son tarih"):
        ProductCreate(
            category_id=1,
            name="Süt",
            quantity=Decimal("1.00"),
            unit="litre",
            expiry_date=None,
            date_type="STT",
            storage_location="fridge"
        )


def test_product_none_date_type_allows_null_expiry(db_session, sample_user, seeded_categories):
    """When date_type is NONE, expiry_date can be None."""
    category = seeded_categories[6]  # Yağ, Sos ve Baharat
    product_in = ProductCreate(
        category_id=category.id,
        name="Tuz",
        quantity=Decimal("1.00"),
        unit="kg",
        expiry_date=None,
        date_type="NONE",
        storage_location="pantry"
    )
    product = create_product(db_session, sample_user.id, product_in)
    assert product.expiry_date is None
    assert product.date_type == "NONE"


def test_user_data_isolation(db_session, sample_user, second_user, seeded_categories):
    """A user must only see their own products."""
    cat = seeded_categories[0]

    # Create product for user 1
    create_product(db_session, sample_user.id, ProductCreate(
        category_id=cat.id,
        name="Kullanıcı 1 Elması",
        quantity=Decimal("3.00"),
        unit="adet",
        expiry_date=date(2026, 11, 20),
        date_type="STT",
        storage_location="fridge"
    ))

    # Create product for user 2
    create_product(db_session, second_user.id, ProductCreate(
        category_id=cat.id,
        name="Kullanıcı 2 Armutu",
        quantity=Decimal("4.00"),
        unit="adet",
        expiry_date=date(2026, 11, 21),
        date_type="STT",
        storage_location="fridge"
    ))

    user1_products = get_user_products(db_session, sample_user.id)
    user2_products = get_user_products(db_session, second_user.id)

    assert len(user1_products) == 1
    assert user1_products[0].name == "Kullanıcı 1 Elması"

    assert len(user2_products) == 1
    assert user2_products[0].name == "Kullanıcı 2 Armutu"


def test_category_filtering(db_session, sample_user, seeded_categories):
    """Test filtering products by category."""
    veg_cat = seeded_categories[0]    # Sebzeler
    fruit_cat = seeded_categories[1]  # Meyveler

    create_product(db_session, sample_user.id, ProductCreate(
        category_id=veg_cat.id,
        name="Havuç",
        quantity=Decimal("1.00"),
        unit="kg",
        expiry_date=date(2026, 11, 10),
        date_type="STT",
        storage_location="fridge"
    ))
    create_product(db_session, sample_user.id, ProductCreate(
        category_id=fruit_cat.id,
        name="Muz",
        quantity=Decimal("6.00"),
        unit="adet",
        expiry_date=date(2026, 11, 5),
        date_type="STT",
        storage_location="pantry"
    ))

    veg_products = get_user_products(db_session, sample_user.id, category_id=veg_cat.id)
    fruit_products = get_user_products(db_session, sample_user.id, category_id=fruit_cat.id)

    assert len(veg_products) == 1
    assert veg_products[0].name == "Havuç"

    assert len(fruit_products) == 1
    assert fruit_products[0].name == "Muz"


def test_consumption_transaction_partial_and_full(db_session, sample_user, seeded_categories):
    """
    Test consumption transaction:
    1. Partial consumption reduces quantity and creates ConsumptionLog.
    2. Full consumption sets status to 'consumed' and quantity to 0.
    """
    cat = seeded_categories[2]  # Süt ve Süt Ürünleri
    product = create_product(db_session, sample_user.id, ProductCreate(
        category_id=cat.id,
        name="Yoğurt",
        quantity=Decimal("1000.00"),
        unit="gram",
        expiry_date=date(2026, 11, 12),
        date_type="STT",
        storage_location="fridge"
    ))

    # 1. Partial consumption (400g)
    consumption_1 = ConsumptionCreate(
        product_id=product.id,
        quantity_used=Decimal("400.00"),
        unit="gram",
        action_type="consumed"
    )
    updated_prod, log_1 = consume_product(db_session, sample_user.id, consumption_1)

    assert updated_prod.quantity == Decimal("600.00")
    assert updated_prod.status == "active"
    assert log_1.quantity_used == Decimal("400.00")
    assert log_1.action_type == "consumed"

    # 2. Complete consumption (remaining 600g)
    consumption_2 = ConsumptionCreate(
        product_id=product.id,
        quantity_used=Decimal("600.00"),
        unit="gram",
        action_type="consumed"
    )
    final_prod, log_2 = consume_product(db_session, sample_user.id, consumption_2)

    assert final_prod.quantity == Decimal("0.00")
    assert final_prod.status == "consumed"
    assert log_2.quantity_used == Decimal("600.00")

    # Verify logs count
    logs = db_session.query(ConsumptionLog).filter(ConsumptionLog.product_id == product.id).all()
    assert len(logs) == 2


def test_consumption_insufficient_quantity_rejection(db_session, sample_user, seeded_categories):
    """
    If requested consumption quantity > available quantity,
    transaction must rollback and raise InsufficientQuantityError.
    """
    cat = seeded_categories[0]
    product = create_product(db_session, sample_user.id, ProductCreate(
        category_id=cat.id,
        name="Ispanak",
        quantity=Decimal("500.00"),
        unit="gram",
        expiry_date=date(2026, 11, 4),
        date_type="STT",
        storage_location="fridge"
    ))

    excessive_consumption = ConsumptionCreate(
        product_id=product.id,
        quantity_used=Decimal("600.00"),  # More than 500
        unit="gram",
        action_type="consumed"
    )

    with pytest.raises(InsufficientQuantityError):
        consume_product(db_session, sample_user.id, excessive_consumption)

    # Verify product quantity was NOT changed
    db_session.refresh(product)
    assert product.quantity == Decimal("500.00")
    assert product.status == "active"
    # No logs should be recorded
    assert db_session.query(ConsumptionLog).count() == 0


def test_consumption_logs_preserved_when_product_deleted(db_session, sample_user, seeded_categories):
    """
    Requirement: Tüketim geçmişi silinmemeli.
    When product is deleted, historical consumption logs must persist with product_id=None.
    """
    cat = seeded_categories[0]
    product = create_product(db_session, sample_user.id, ProductCreate(
        category_id=cat.id,
        name="Maydanoz",
        quantity=Decimal("100.00"),
        unit="gram",
        expiry_date=date(2026, 11, 2),
        date_type="STT",
        storage_location="fridge"
    ))

    # Consume some
    consume_product(db_session, sample_user.id, ConsumptionCreate(
        product_id=product.id,
        quantity_used=Decimal("50.00"),
        unit="gram",
        action_type="consumed"
    ))

    log = db_session.query(ConsumptionLog).filter(ConsumptionLog.product_id == product.id).first()
    assert log is not None
    assert log.quantity_used == Decimal("50.00")

    # Hard delete product
    delete_product(db_session, sample_user.id, product.id, soft=False)

    # Verify log is preserved, with product_id set to NULL
    db_session.refresh(log)
    assert log.product_id is None
    assert log.quantity_used == Decimal("50.00")
    assert db_session.query(ConsumptionLog).count() == 1


def test_recipe_and_recipe_ingredients_relationship(db_session):
    """Test Recipe and RecipeIngredient cascade and relationship."""
    recipe = Recipe(
        name="Sebzeli Menemen",
        description="Domates, biber ve yumurtayla pratik lezzet.",
        instructions="Biberleri kavur, domatesleri ekle, suyunu çekince yumurtaları kır.",
        preparation_time=5,
        cooking_time=10,
        servings=2,
        difficulty="Kolay"
    )
    db_session.add(recipe)
    db_session.commit()
    db_session.refresh(recipe)

    ing1 = RecipeIngredient(
        recipe_id=recipe.id,
        ingredient_name="Domates",
        quantity=Decimal("3.00"),
        unit="adet",
        is_optional=False
    )
    ing2 = RecipeIngredient(
        recipe_id=recipe.id,
        ingredient_name="Yumurta",
        quantity=Decimal("2.00"),
        unit="adet",
        is_optional=False
    )
    db_session.add_all([ing1, ing2])
    db_session.commit()

    db_session.refresh(recipe)
    assert len(recipe.ingredients) == 2
    assert recipe.ingredients[0].ingredient_name in ("Domates", "Yumurta")
