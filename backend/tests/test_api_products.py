from datetime import date
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models.user import User
from app.models.category import Category
from app.services.category_service import seed_categories


@pytest.fixture(scope="function")
def test_engine():
    """
    Her test fonksiyonu için StaticPool kullanan in-memory SQLite motoru oluşturur.
    Tüm bağlantılar ve TestClient istekleri aynı veritabanı belleğini paylaşır.
    """
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
    """
    Testler için veritabanı oturumu sağlar ve başlangıç kategorilerini yükler.
    """
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()
    seed_categories(session)

    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(test_engine, test_db_session):
    """
    FastAPI get_db bağımlılığını test motoruna bağlayan TestClient üretir.
    """
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
    """Test için 1. kullanıcı."""
    user = User(username="ipek", email="ipek@dongu.org", password_hash="pass123")
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)
    return user


@pytest.fixture
def user2(test_db_session):
    """Kullanıcı izolasyonunu test etmek için 2. kullanıcı."""
    user = User(username="mehmet", email="mehmet@dongu.org", password_hash="pass456")
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)
    return user


# ==============================================================================
# 1. ÜRÜN EKLEME (POST /api/products) TESTLERİ
# ==============================================================================

def test_add_product_success(client, user1):
    """Geçerli verilerle ürün ekleme başarılı olmalı (201 Created)."""
    headers = {"X-User-Id": str(user1.id)}
    payload = {
        "category_id": 1,  # Sebzeler
        "name": "Domates",
        "quantity": 2.5,
        "unit": "kg",
        "expiry_date": "2026-11-20",
        "date_type": "STT",
        "storage_location": "fridge"
    }
    response = client.post("/api/products", json=payload, headers=headers)
    assert response.status_code == 201

    data = response.json()
    assert data["name"] == "Domates"
    assert float(data["quantity"]) == 2.5
    assert data["unit"] == "kg"
    assert data["user_id"] == user1.id
    assert data["status"] == "active"
    assert "id" in data


def test_add_product_stt_requires_date(client, user1):
    """STT seçildiğinde tarih girilmezse 422 Unprocessable Entity dönmelidir."""
    headers = {"X-User-Id": str(user1.id)}
    payload = {
        "category_id": 1,
        "name": "Süt",
        "quantity": 1.0,
        "unit": "litre",
        "expiry_date": None,
        "date_type": "STT",
        "storage_location": "fridge"
    }
    response = client.post("/api/products", json=payload, headers=headers)
    assert response.status_code == 422


def test_add_product_none_date_type_allowed(client, user1):
    """NONE seçildiğinde son tarih boş geçilebilmelidir (201 Created)."""
    headers = {"X-User-Id": str(user1.id)}
    payload = {
        "category_id": 7,  # Yağ, Sos ve Baharat
        "name": "Kaya Tuzu",
        "quantity": 1.0,
        "unit": "kg",
        "expiry_date": None,
        "date_type": "NONE",
        "storage_location": "pantry"
    }
    response = client.post("/api/products", json=payload, headers=headers)
    assert response.status_code == 201
    assert response.json()["expiry_date"] is None


def test_add_product_reject_invalid_quantity(client, user1):
    """Miktar sıfır veya negatif olduğunda istek reddedilmelidir (422)."""
    headers = {"X-User-Id": str(user1.id)}
    payload = {
        "category_id": 1,
        "name": "Havuç",
        "quantity": 0,  # Sıfır miktar
        "unit": "kg",
        "expiry_date": "2026-11-15",
        "date_type": "STT"
    }
    response = client.post("/api/products", json=payload, headers=headers)
    assert response.status_code == 422


def test_add_product_reject_nonexistent_category(client, user1):
    """Mevcut olmayan bir kategori ID'si girildiğinde 400 Bad Request dönmelidir."""
    headers = {"X-User-Id": str(user1.id)}
    payload = {
        "category_id": 9999,  # Olmayan kategori
        "name": "Muz",
        "quantity": 1.0,
        "unit": "kg",
        "expiry_date": "2026-11-10",
        "date_type": "STT"
    }
    response = client.post("/api/products", json=payload, headers=headers)
    assert response.status_code == 400
    assert "kategori bulunamadı" in response.json()["detail"]


# ==============================================================================
# 2. ÜRÜN LİSTELEME VE FİLTRELEME (GET /api/products) TESTLERİ
# ==============================================================================

def test_list_and_filter_products(client, user1):
    """
    Ürün listeleme ve kategori, saklama yeri, arama filtrelerinin
    birlikte ve ayrı ayrı doğru çalıştığını doğrular.
    """
    headers = {"X-User-Id": str(user1.id)}

    # Test ürünleri oluşturma
    client.post("/api/products", json={
        "category_id": 1,  # Sebze
        "name": "Kırmızı Elma",
        "quantity": 3.0,
        "unit": "adet",
        "expiry_date": "2026-11-10",
        "date_type": "STT",
        "storage_location": "fridge"
    }, headers=headers)

    client.post("/api/products", json={
        "category_id": 2,  # Meyve
        "name": "Yeşil Elma",
        "quantity": 2.0,
        "unit": "kg",
        "expiry_date": "2026-11-12",
        "date_type": "STT",
        "storage_location": "pantry"
    }, headers=headers)

    client.post("/api/products", json={
        "category_id": 1,  # Sebze
        "name": "Brokoli",
        "quantity": 500.0,
        "unit": "gram",
        "expiry_date": "2026-11-05",
        "date_type": "STT",
        "storage_location": "fridge"
    }, headers=headers)

    # 1. Filtresiz listeleme
    res_all = client.get("/api/products", headers=headers)
    assert res_all.status_code == 200
    assert len(res_all.json()) == 3

    # 2. Kategoriye göre filtreleme (Kategori 1: Sebzeler -> 2 ürün)
    res_cat = client.get("/api/products?category_id=1", headers=headers)
    assert res_cat.status_code == 200
    assert len(res_cat.json()) == 2

    # 3. Saklama yerine göre filtreleme (pantry -> 1 ürün)
    res_loc = client.get("/api/products?storage_location=pantry", headers=headers)
    assert res_loc.status_code == 200
    assert len(res_loc.json()) == 1
    assert res_loc.json()[0]["name"] == "Yeşil Elma"

    # 4. İsim araması (search=elma -> 2 ürün)
    res_search = client.get("/api/products?search=elma", headers=headers)
    assert res_search.status_code == 200
    assert len(res_search.json()) == 2

    # 5. Kombine filtreleme: Kategori 1 + Arama 'elma' -> 1 ürün (Kırmızı Elma)
    res_comb = client.get("/api/products?category_id=1&search=elma", headers=headers)
    assert res_comb.status_code == 200
    assert len(res_comb.json()) == 1
    assert res_comb.json()[0]["name"] == "Kırmızı Elma"


# ==============================================================================
# 3. TEK ÜRÜN GETİRME VE 404 (GET /api/products/{id}) TESTLERİ
# ==============================================================================

def test_get_product_detail_and_404(client, user1):
    """Mevcut ürünü getirme ve var olmayan ürün için 404 dönme kontrolü."""
    headers = {"X-User-Id": str(user1.id)}

    # Ürün ekle
    res_add = client.post("/api/products", json={
        "category_id": 1,
        "name": "Kabak",
        "quantity": 1.0,
        "unit": "kg",
        "expiry_date": "2026-11-08",
        "date_type": "STT"
    }, headers=headers)
    prod_id = res_add.json()["id"]

    # Detayı getir
    res_get = client.get(f"/api/products/{prod_id}", headers=headers)
    assert res_get.status_code == 200
    assert res_get.json()["name"] == "Kabak"

    # Olmayan ürünü iste
    res_not_found = client.get("/api/products/99999", headers=headers)
    assert res_not_found.status_code == 404


# ==============================================================================
# 4. ÜRÜN GÜNCELLEME (PUT /api/products/{id}) TESTLERİ
# ==============================================================================

def test_update_product(client, user1):
    """Ürün miktarını ve saklama alanını güncelleme kontrolü."""
    headers = {"X-User-Id": str(user1.id)}

    # Ürün ekle
    res_add = client.post("/api/products", json={
        "category_id": 1,
        "name": "Patates",
        "quantity": 5.0,
        "unit": "kg",
        "expiry_date": "2026-11-30",
        "date_type": "STT",
        "storage_location": "pantry"
    }, headers=headers)
    prod_id = res_add.json()["id"]

    # Miktar ve saklama yerini güncelle
    res_put = client.put(f"/api/products/{prod_id}", json={
        "quantity": 3.5,
        "storage_location": "fridge"
    }, headers=headers)
    assert res_put.status_code == 200
    updated_data = res_put.json()
    assert float(updated_data["quantity"]) == 3.5
    assert updated_data["storage_location"] == "fridge"
    assert updated_data["name"] == "Patates"  # İsim değişmedi


# ==============================================================================
# 5. ÜRÜN SİLME (DELETE /api/products/{id}) TESTLERİ
# ==============================================================================

def test_delete_product(client, user1):
    """Ürün başarıyla silinmeli ve tekrar istendiğinde 404 dönmelidir."""
    headers = {"X-User-Id": str(user1.id)}

    res_add = client.post("/api/products", json={
        "category_id": 1,
        "name": "Biber",
        "quantity": 500.0,
        "unit": "gram",
        "expiry_date": "2026-11-09",
        "date_type": "STT"
    }, headers=headers)
    prod_id = res_add.json()["id"]

    # Silme isteği
    res_del = client.delete(f"/api/products/{prod_id}", headers=headers)
    assert res_del.status_code == 200
    assert "başarıyla silindi" in res_del.json()["detail"]

    # Tekrar kontrol et: 404 dönmeli
    res_get = client.get(f"/api/products/{prod_id}", headers=headers)
    assert res_get.status_code == 404


# ==============================================================================
# 6. KULLANICILAR ARASI VERİ İZOLASYONU TESTLERİ
# ==============================================================================

def test_user_data_isolation(client, user1, user2):
    """
    Kullanıcı 1'in eklediği ürün:
    - Kullanıcı 2'nin liste endpoint'inde asla görünmemelidir.
    - Kullanıcı 2 direkt ürün ID'si ile erişmek istediğinde 404 almalıdır.
    - Kullanıcı 2 bu ürünü güncelleyemez veya silemez (404).
    """
    headers_user1 = {"X-User-Id": str(user1.id)}
    headers_user2 = {"X-User-Id": str(user2.id)}

    # Kullanıcı 1 ürün ekler
    res_add = client.post("/api/products", json={
        "category_id": 1,
        "name": "Gizli Kullanıcı1 Ürünü",
        "quantity": 1.0,
        "unit": "adet",
        "expiry_date": "2026-11-20",
        "date_type": "STT"
    }, headers=headers_user1)
    prod_id = res_add.json()["id"]

    # Kullanıcı 2 kendi ürünlerini listeler -> Boş liste görmeli
    res_user2_list = client.get("/api/products", headers=headers_user2)
    assert res_user2_list.status_code == 200
    assert len(res_user2_list.json()) == 0

    # Kullanıcı 2 Kullanıcı 1'in ürününü direkt ID ile sorgular -> 404 dönmeli
    res_user2_get = client.get(f"/api/products/{prod_id}", headers=headers_user2)
    assert res_user2_get.status_code == 404

    # Kullanıcı 2 Kullanıcı 1'in ürününü güncellemeye çalışır -> 404 dönmeli
    res_user2_put = client.put(f"/api/products/{prod_id}", json={"quantity": 99.0}, headers=headers_user2)
    assert res_user2_put.status_code == 404

    # Kullanıcı 2 Kullanıcı 1'in ürününü silmeye çalışır -> 404 dönmeli
    res_user2_del = client.delete(f"/api/products/{prod_id}", headers=headers_user2)
    assert res_user2_del.status_code == 404


# ==============================================================================
# 7. KATEGORİ API (GET /api/categories) TESTLERİ
# ==============================================================================

def test_category_endpoints(client):
    """Tüm kategorileri ve tek kategori detayını listeleme testi."""
    # Tüm kategoriler (11 adet başlangıç kategorisi olmalı)
    res_list = client.get("/api/categories")
    assert res_list.status_code == 200
    categories = res_list.json()
    assert len(categories) == 11
    assert categories[0]["name"] == "Sebzeler"

    # Tek kategori detayı
    cat_id = categories[0]["id"]
    res_detail = client.get(f"/api/categories/{cat_id}")
    assert res_detail.status_code == 200
    assert res_detail.json()["id"] == cat_id
    assert res_detail.json()["name"] == "Sebzeler"

    # Olmayan kategori için 404 kontrolü
    res_nonexistent = client.get("/api/categories/99999")
    assert res_nonexistent.status_code == 404
