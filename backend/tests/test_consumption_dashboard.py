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
from app.models.recipe import Recipe
from app.services.category_service import seed_categories
from app.data.seed_recipes import seed_recipes


@pytest.fixture(scope="function")
def test_engine():
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
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()
    seed_categories(session)
    seed_recipes(session)
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(test_engine, test_db_session):
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
    user = User(username="ali", email="ali@dongu.org", password_hash="hash123")
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)
    return user


@pytest.fixture
def user2(test_db_session):
    user = User(username="zeynep", email="zeynep@dongu.org", password_hash="hash456")
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)
    return user


# ==============================================================================
# 1. TÜKETİM VE GIDA KURTARMA TESTLERİ
# ==============================================================================

def test_record_consumption_success(client, user1):
    """
    Tüketim kaydı oluşturulduğunda ürün miktarı düşmeli ve
    consumption_logs kaydı oluşmalıdır.
    """
    headers = {"X-User-Id": str(user1.id)}
    today = date.today()

    # 1. Ürün ekle (1000 gram domates)
    res_add = client.post("/api/products", json={
        "category_id": 1,
        "name": "Domates",
        "quantity": 1000.0,
        "unit": "gram",
        "expiry_date": str(today + timedelta(days=3)),
        "date_type": "STT"
    }, headers=headers)
    prod_id = res_add.json()["id"]

    # 2. 300 gramını tüket
    res_consume = client.post("/api/consumption", json={
        "product_id": prod_id,
        "quantity_used": 300.0,
        "unit": "gram",
        "action_type": "consumed"
    }, headers=headers)

    assert res_consume.status_code == 201
    data = res_consume.json()
    assert float(data["quantity_used"]) == 300.0
    assert data["product_name"] == "Domates"

    # 3. Ürünün kalan miktarını kontrol et (700 gram kalmalı)
    res_prod = client.get(f"/api/products/{prod_id}", headers=headers)
    assert float(res_prod.json()["quantity"]) == 700.0
    assert res_prod.json()["status"] == "active"


def test_consumption_exceeding_quantity_rejected(client, user1):
    """Mevcut stoktan fazla miktar tüketilmeye çalışıldığında 400 dönmelidir."""
    headers = {"X-User-Id": str(user1.id)}
    today = date.today()

    res_add = client.post("/api/products", json={
        "category_id": 3,
        "name": "Kaşar Peyniri",
        "quantity": 200.0,
        "unit": "gram",
        "expiry_date": str(today + timedelta(days=5)),
        "date_type": "STT"
    }, headers=headers)
    prod_id = res_add.json()["id"]

    # 250 gram tüketmeye çalış (elde 200 gram var)
    res_consume = client.post("/api/consumption", json={
        "product_id": prod_id,
        "quantity_used": 250.0,
        "unit": "gram",
        "action_type": "consumed"
    }, headers=headers)

    assert res_consume.status_code == 400
    assert "Yetersiz ürün miktarı" in res_consume.json()["detail"]


def test_consumption_summary_and_impact(client, user1):
    """
    Tüketim özeti ve etki paneli hesaplaması:
    Toplam kg, haftalık miktar, tamamlanan tarif ve çevresel kazanç hesaplanmalı.
    """
    headers = {"X-User-Id": str(user1.id)}
    today = date.today()

    res_add = client.post("/api/products", json={
        "category_id": 1,
        "name": "Patates",
        "quantity": 2.0,
        "unit": "kg",
        "expiry_date": str(today + timedelta(days=10)),
        "date_type": "STT"
    }, headers=headers)
    prod_id = res_add.json()["id"]

    # 1 kg tüket (1. tarifle ilişkili)
    client.post("/api/consumption", json={
        "product_id": prod_id,
        "quantity_used": 1.0,
        "unit": "kg",
        "action_type": "recipe_used",
        "recipe_id": 3  # Patates Yemeği
    }, headers=headers)

    # Özet getir
    res_summary = client.get("/api/consumption/summary", headers=headers)
    assert res_summary.status_code == 200
    summary = res_summary.json()

    assert float(summary["total_evaluated_kg"]) == 1.0
    assert summary["completed_recipes_count"] == 1
    assert summary["environmental_impact"]["is_estimate"] is True
    assert summary["environmental_impact"]["estimated_co2_saved_kg"] > 0
    assert summary["environmental_impact"]["estimated_water_saved_liters"] > 0


# ==============================================================================
# 2. DASHBOARD VE BİLDİRİM TESTLERİ
# ==============================================================================

def test_dashboard_summary_endpoint(client, user1):
    """GET /api/dashboard/summary özet verileri doğru dönmelidir."""
    headers = {"X-User-Id": str(user1.id)}
    today = date.today()

    # Kritik ürün ekle (1 gün kalmış)
    client.post("/api/products", json={
        "category_id": 1,
        "name": "Ispanak",
        "quantity": 500.0,
        "unit": "gram",
        "expiry_date": str(today + timedelta(days=1)),
        "date_type": "STT"
    }, headers=headers)

    res_dash = client.get("/api/dashboard/summary", headers=headers)
    assert res_dash.status_code == 200
    data = res_dash.json()

    assert data["active_products_count"] == 1
    assert data["critical_priority_count"] == 1
    assert data["expiring_stt_count"] == 1
    assert "weekly_stats" in data
    assert len(data["weekly_stats"]) == 7


def test_notifications_workflow(client, user1):
    """
    Bildirim listeleme, acil ürünler için otomatik bildirim üretme,
    tek bildirim okundu yapma ve tümünü okundu işaretleme testi.
    """
    headers = {"X-User-Id": str(user1.id)}
    today = date.today()

    # Acil ürün ekle (STT bugün doluyor)
    client.post("/api/products", json={
        "category_id": 4,
        "name": "Tavuk But",
        "quantity": 1.0,
        "unit": "kg",
        "expiry_date": str(today),
        "date_type": "STT"
    }, headers=headers)

    # Bildirimleri listele (otomatik bildirim tetiklenmeli)
    res_notif = client.get("/api/notifications", headers=headers)
    assert res_notif.status_code == 200
    notifs = res_notif.json()
    assert len(notifs) >= 1
    assert "Acil Tüketilmeli" in notifs[0]["title"]
    notif_id = notifs[0]["id"]

    # Tek bildirimi okundu yap
    res_read = client.patch(f"/api/notifications/{notif_id}/read", headers=headers)
    assert res_read.status_code == 200
    assert res_read.json()["is_read"] is True

    # Tümünü okundu yap
    res_all = client.patch("/api/notifications/read-all", headers=headers)
    assert res_all.status_code == 200


# ==============================================================================
# 3. FRONTEND ROTALARI TESTİ
# ==============================================================================

def test_frontend_routes_served(client):
    """Arayüz HTML sayfalarının başarıyla 200 döndüğünü doğrula."""
    res_home = client.get("/")
    assert res_home.status_code == 200
    assert "DÖNGÜ" in res_home.text

    res_pantry = client.get("/pantry")
    assert res_pantry.status_code == 200

    res_impact = client.get("/impact")
    assert res_impact.status_code == 200
