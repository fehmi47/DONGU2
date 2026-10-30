from datetime import date, timedelta
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models.user import User
from app.models.product import Product
from app.services.category_service import seed_categories
from app.services.priority_service import evaluate_product_priority


@pytest.fixture(scope="function")
def test_engine():
    """Tüm bağlantıların aynı in-memory veritabanını paylaşması için StaticPool motoru."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_db_session(test_engine):
    """Testler için veritabanı oturumu ve kategori yüklemesi."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()
    seed_categories(session)
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(test_engine, test_db_session):
    """FastAPI TestClient üretimi."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def user1(test_db_session):
    user = User(username="selin", email="selin@dongu.org", password_hash="pass123")
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)
    return user


@pytest.fixture
def user2(test_db_session):
    user = User(username="kerem", email="kerem@dongu.org", password_hash="pass456")
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)
    return user


# ==============================================================================
# 1. BİRİM TESTLER: AKILLI ÖNCELİK ALGORİTMASI MANTIĞI
# ==============================================================================

def test_evaluate_stt_expired():
    """Tarihi geçmiş STT ürünü: expired_stt olmalı ve can_be_recommended=False dönmelidir."""
    today = date(2026, 11, 1)
    product = Product(
        name="Tavuk Göğsü",
        quantity=Decimal("1.0"),
        unit="kg",
        expiry_date=date(2026, 10, 30),  # 2 gün önce geçmiş
        date_type="STT",
        storage_location="fridge",
        status="active"
    )
    result = evaluate_product_priority(product, reference_date=today)
    assert result.priority_level == "expired_stt"
    assert result.days_remaining == -2
    assert result.can_be_recommended is False
    assert "Gıda güvenliği riski" in result.priority_message


def test_evaluate_stt_critical():
    """Son tüketim tarihine 1 gün kalan STT ürünü critical olmalıdır."""
    today = date(2026, 11, 1)
    product = Product(
        name="Taze Süt",
        quantity=Decimal("1.0"),
        unit="litre",
        expiry_date=date(2026, 11, 2),  # 1 gün kaldı
        date_type="STT",
        storage_location="fridge",
        status="active"
    )
    result = evaluate_product_priority(product, reference_date=today)
    assert result.priority_level == "critical"
    assert result.days_remaining == 1
    assert result.can_be_recommended is True


def test_evaluate_tett_past_still_can_be_recommended():
    """
    TETT tarihi geçmiş ürün: Otomatik bozuk sayılmaz.
    priority_level='high' ve can_be_recommended=True olmalı, kullanıcıya duyusal kontrol uyarısı verilmelidir.
    """
    today = date(2026, 11, 1)
    product = Product(
        name="Kuru Fasulye",
        quantity=Decimal("1.0"),
        unit="kg",
        expiry_date=date(2026, 10, 25),  # TETT 7 gün önce dolmuş
        date_type="TETT",
        storage_location="pantry",
        status="active"
    )
    result = evaluate_product_priority(product, reference_date=today)
    assert result.priority_level == "high"
    assert result.days_remaining == -7
    assert result.can_be_recommended is True
    assert "duyusal kontroller" in result.priority_message


def test_evaluate_none_date_type():
    """Tarihsiz ürünlerde (NONE) no_date dönmeli ve gün hesabı yapılmamalıdır (None)."""
    product = Product(
        name="Sofra Tuzu",
        quantity=Decimal("1.0"),
        unit="kg",
        expiry_date=None,
        date_type="NONE",
        storage_location="pantry",
        status="active"
    )
    result = evaluate_product_priority(product)
    assert result.priority_level == "no_date"
    assert result.days_remaining is None
    assert result.can_be_recommended is True


# ==============================================================================
# 2. ENTEGRASYON TESTLERİ: ÖNCELİK ENDPOINT'LERİ
# ==============================================================================

def test_get_products_priority_endpoint(client, user1):
    """
    GET /api/products/priority endpoint'i ürünleri doğru sıralamalıdır:
    Critical ürünler en başta, expired_stt ürünler en sonda yer almalıdır.
    """
    headers = {"X-User-Id": str(user1.id)}
    today = date.today()

    # 1. expired_stt (3 gün önce geçmiş STT)
    client.post("/api/products", json={
        "category_id": 4,
        "name": "Kıyma",
        "quantity": 500.0,
        "unit": "gram",
        "expiry_date": str(today - timedelta(days=3)),
        "date_type": "STT"
    }, headers=headers)

    # 2. critical (1 gün kalmış STT)
    client.post("/api/products", json={
        "category_id": 3,
        "name": "Krema",
        "quantity": 200.0,
        "unit": "ml",
        "expiry_date": str(today + timedelta(days=1)),
        "date_type": "STT"
    }, headers=headers)

    # 3. low (20 gün kalmış STT)
    client.post("/api/products", json={
        "category_id": 1,
        "name": "Patates",
        "quantity": 3.0,
        "unit": "kg",
        "expiry_date": str(today + timedelta(days=20)),
        "date_type": "STT"
    }, headers=headers)

    # 4. no_date (Tarihsiz tuz)
    client.post("/api/products", json={
        "category_id": 7,
        "name": "Karabiber",
        "quantity": 50.0,
        "unit": "gram",
        "expiry_date": None,
        "date_type": "NONE"
    }, headers=headers)

    response = client.get("/api/products/priority", headers=headers)
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 4

    # En baştaki ürün critical olmalı (Krema)
    assert items[0]["name"] == "Krema"
    assert items[0]["priority_level"] == "critical"
    assert items[0]["can_be_recommended"] is True

    # Tarihi geçmiş kıyma expired_stt olmalı ve önerilemez olmalı
    expired_item = next(it for it in items if it["name"] == "Kıyma")
    assert expired_item["priority_level"] == "expired_stt"
    assert expired_item["can_be_recommended"] is False


def test_get_expiring_products_endpoint(client, user1):
    """
    GET /api/products/expiring?days=3 endpoint'i yalnızca 3 gün içinde
    süresi dolacak ürünleri getirmelidir.
    """
    headers = {"X-User-Id": str(user1.id)}
    today = date.today()

    # 2 gün kalan ürün (dahil olmalı)
    client.post("/api/products", json={
        "category_id": 1,
        "name": "Taze Yeşillik",
        "quantity": 1.0,
        "unit": "demet",
        "expiry_date": str(today + timedelta(days=2)),
        "date_type": "STT"
    }, headers=headers)

    # 10 gün kalan ürün (dahil OLMAMALI)
    client.post("/api/products", json={
        "category_id": 2,
        "name": "Karpuz",
        "quantity": 1.0,
        "unit": "adet",
        "expiry_date": str(today + timedelta(days=10)),
        "date_type": "STT"
    }, headers=headers)

    response = client.get("/api/products/expiring?days=3", headers=headers)
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 1
    assert items[0]["name"] == "Taze Yeşillik"
    assert items[0]["days_remaining"] == 2


def test_get_single_product_priority_and_isolation(client, user1, user2):
    """
    GET /api/products/priority/{id} tek ürün önceliğini getirmeli ve
    başka kullanıcının ürünü için 404 dönmelidir.
    """
    headers_u1 = {"X-User-Id": str(user1.id)}
    headers_u2 = {"X-User-Id": str(user2.id)}
    today = date.today()

    res_add = client.post("/api/products", json={
        "category_id": 1,
        "name": "Mantar",
        "quantity": 300.0,
        "unit": "gram",
        "expiry_date": str(today + timedelta(days=4)),
        "date_type": "STT"
    }, headers=headers_u1)
    prod_id = res_add.json()["id"]

    # Kullanıcı 1 kendi ürününün önceliğini sorgular
    res_priority = client.get(f"/api/products/priority/{prod_id}", headers=headers_u1)
    assert res_priority.status_code == 200
    data = res_priority.json()
    assert data["name"] == "Mantar"
    assert data["priority_level"] == "high"
    assert data["days_remaining"] == 4
    assert data["can_be_recommended"] is True

    # Kullanıcı 2 Kullanıcı 1'in ürününün önceliğini sorgulayamaz -> 404
    res_u2 = client.get(f"/api/products/priority/{prod_id}", headers=headers_u2)
    assert res_u2.status_code == 404
