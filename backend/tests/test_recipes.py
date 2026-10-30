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
from app.models.recipe import Recipe
from app.services.category_service import seed_categories
from app.data.seed_recipes import seed_recipes


@pytest.fixture(scope="function")
def test_engine():
    """Tüm testler için StaticPool in-memory SQLite motoru."""
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
    """Testler için veritabanı oturumu; kategori ve tarif başlangıç verilerini yükler."""
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
    user = User(username="burak", email="burak@dongu.org", password_hash="hash123")
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)
    return user


@pytest.fixture
def user2(test_db_session):
    user = User(username="deniz", email="deniz@dongu.org", password_hash="hash456")
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)
    return user


# ==============================================================================
# 1. TARİF YÖNETİMİ CRUD TESTLERİ
# ==============================================================================

def test_list_and_search_recipes(client):
    """Tüm tarifleri listeleme ve arama kontrolü."""
    # 20 başlangıç tarifi listelenmeli
    res = client.get("/api/recipes")
    assert res.status_code == 200
    recipes = res.json()
    assert len(recipes) >= 20

    # Arama testi (Menemen)
    res_search = client.get("/api/recipes?search=menemen")
    assert res_search.status_code == 200
    search_results = res_search.json()
    assert len(search_results) >= 1
    assert any(r["name"] == "Menemen" for r in search_results)


def test_get_recipe_detail_and_404(client):
    """Mevcut tarif detayı ve 404 kontrolü."""
    res_list = client.get("/api/recipes")
    first_id = res_list.json()[0]["id"]

    res_get = client.get(f"/api/recipes/{first_id}")
    assert res_get.status_code == 200
    assert "ingredients" in res_get.json()
    assert len(res_get.json()["ingredients"]) > 0

    # Olmayan tarif
    res_not_found = client.get("/api/recipes/99999")
    assert res_not_found.status_code == 404


def test_create_update_delete_recipe(client):
    """Yeni tarif oluşturma, güncelleme ve silme yaşam döngüsü testi."""
    payload = {
        "name": "Özel Test Çorbası",
        "description": "Otomasyon testi için özel tarif",
        "instructions": "1. Suyu kaynat.\n2. Malzemeleri ekle.",
        "preparation_time": 5,
        "cooking_time": 15,
        "servings": 2,
        "difficulty": "Kolay",
        "ingredients": [
            {"ingredient_name": "Su", "quantity": 1.0, "unit": "litre", "is_optional": False},
            {"ingredient_name": "Tuz", "quantity": 1.0, "unit": "kaşık", "is_optional": True}
        ]
    }
    # 1. Oluştur (POST)
    res_create = client.post("/api/recipes", json=payload)
    assert res_create.status_code == 201
    created_id = res_create.json()["id"]
    assert res_create.json()["name"] == "Özel Test Çorbası"
    assert len(res_create.json()["ingredients"]) == 2

    # 2. Malzemeleri getir (GET /{id}/ingredients)
    res_ing = client.get(f"/api/recipes/{created_id}/ingredients")
    assert res_ing.status_code == 200
    assert len(res_ing.json()) == 2

    # 3. Güncelle (PUT)
    res_update = client.put(f"/api/recipes/{created_id}", json={
        "name": "Güncellenmiş Test Çorbası",
        "servings": 4
    })
    assert res_update.status_code == 200
    assert res_update.json()["name"] == "Güncellenmiş Test Çorbası"
    assert res_update.json()["servings"] == 4

    # 4. Sil (DELETE)
    res_delete = client.delete(f"/api/recipes/{created_id}")
    assert res_delete.status_code == 200

    # 5. Silindiğini doğrula (GET -> 404)
    res_verify = client.get(f"/api/recipes/{created_id}")
    assert res_verify.status_code == 404


# ==============================================================================
# 2. AKILLI TARİF EŞLEŞTİRME VE ÖNERİ TESTLERİ
# ==============================================================================

def test_recipe_recommendations_with_pantry(client, user1):
    """
    Kullanıcının kilerinde Domates, Biber ve Yumurta olduğunda
    Menemen tarifinin en üstte önerilmesi ve can_prepare=True olması testi.
    """
    headers = {"X-User-Id": str(user1.id)}
    today = date.today()

    # Kullanıcı 1 kilerine Menemen malzemelerini ekler (Domates'in STT'sine 1 gün kalmış - critical!)
    client.post("/api/products", json={
        "category_id": 1,
        "name": "Salkım Domates",
        "quantity": 3.0,
        "unit": "adet",
        "expiry_date": str(today + timedelta(days=1)),
        "date_type": "STT"
    }, headers=headers)

    client.post("/api/products", json={
        "category_id": 1,
        "name": "Köy Biberi",
        "quantity": 2.0,
        "unit": "adet",
        "expiry_date": str(today + timedelta(days=4)),
        "date_type": "STT"
    }, headers=headers)

    client.post("/api/products", json={
        "category_id": 4,
        "name": "Yumurta",
        "quantity": 4.0,
        "unit": "adet",
        "expiry_date": str(today + timedelta(days=8)),
        "date_type": "STT"
    }, headers=headers)

    # Tarif önerilerini çek
    res = client.get("/api/recipes/recommendations", headers=headers)
    assert res.status_code == 200
    recommendations = res.json()
    assert len(recommendations) > 0

    # En üst sıradaki tarif Menemen olmalıdır!
    top_recipe = recommendations[0]
    assert top_recipe["name"] == "Menemen"
    assert top_recipe["can_prepare"] is True
    assert top_recipe["priority_score"] > 0
    assert top_recipe["total_time"] == top_recipe["preparation_time"] + top_recipe["cooking_time"]

    # Eşleşen malzemeler kontrolü
    matched_names = [m["ingredient_name"] for m in top_recipe["matched_ingredients"]]
    assert "Domates" in matched_names
    assert "Biber" in matched_names
    assert "Yumurta" in matched_names


def test_stt_expired_products_excluded_from_recommendations(client, user1):
    """
    KRİTİK GIDA GÜVENLİĞİ TESTİ:
    STT tarihi geçmiş bir ürün (örneğin bozuk tavuk veya yumurta)
    asla tarif eşleştirmesine ve önerilerine dahil edilmemelidir!
    """
    headers = {"X-User-Id": str(user1.id)}
    today = date.today()

    # STT tarihi 2 gün önce geçmiş kıyma
    client.post("/api/products", json={
        "category_id": 4,
        "name": "Kıyma",
        "quantity": 300.0,
        "unit": "gram",
        "expiry_date": str(today - timedelta(days=2)),
        "date_type": "STT"
    }, headers=headers)

    # Taze yumurta
    client.post("/api/products", json={
        "category_id": 4,
        "name": "Yumurta",
        "quantity": 2.0,
        "unit": "adet",
        "expiry_date": str(today + timedelta(days=5)),
        "date_type": "STT"
    }, headers=headers)

    res = client.get("/api/recipes/recommendations", headers=headers)
    assert res.status_code == 200
    recommendations = res.json()

    # 'Kıymalı Yumurta' tarifini bul
    kiymali_yumurta = next((r for r in recommendations if r["name"] == "Kıymalı Yumurta"), None)
    assert kiymali_yumurta is not None

    # Tarihi geçmiş kıyma ASLA eşleşenlerde yer almamalı, eksik malzemelerde olmalıdır!
    matched_ing_names = [m["ingredient_name"] for m in kiymali_yumurta["matched_ingredients"]]
    assert "Kıyma" not in matched_ing_names
    assert "Yumurta" in matched_ing_names

    # Kıyma eksik sayıldığı için can_prepare False olmalıdır
    assert kiymali_yumurta["can_prepare"] is False


def test_user_isolation_in_recommendations(client, user1, user2):
    """
    Kullanıcı izolasyonu: Kullanıcı 1'in kilerindeki ürünler
    Kullanıcı 2'nin tarif önerilerini asla etkilememelidir.
    """
    headers_u1 = {"X-User-Id": str(user1.id)}
    headers_u2 = {"X-User-Id": str(user2.id)}
    today = date.today()

    # Kullanıcı 1 kilerine Menemen malzemeleri ekler
    client.post("/api/products", json={
        "category_id": 1,
        "name": "Domates",
        "quantity": 3.0,
        "unit": "adet",
        "expiry_date": str(today + timedelta(days=2)),
        "date_type": "STT"
    }, headers=headers_u1)

    # Kullanıcı 2'nin kileri tamamen boştur
    res_u2 = client.get("/api/recipes/recommendations", headers=headers_u2)
    assert res_u2.status_code == 200
    u2_recommendations = res_u2.json()

    # Kullanıcı 2 için hiçbir tarif hazır (can_prepare=True) olamaz
    for rec in u2_recommendations:
        assert rec["can_prepare"] is False
        assert len(rec["matched_ingredients"]) == 0
        assert rec["priority_score"] == 0.0
