import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models.user import User  # noqa: F401
from app.services.user_service import seed_users

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)



@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    seed_users(db)
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_auth_demo_users(client):
    response = client.get("/api/auth/demo-users")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 3
    assert any(u["username"] == "demo_user" for u in data)


def test_auth_register_success(client):
    payload = {
        "username": "yeni_kullanici",
        "email": "yeni@dongu.org",
        "password": "guvenli_parola_123"
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["user"]["username"] == "yeni_kullanici"
    assert data["user"]["email"] == "yeni@dongu.org"
    assert "id" in data["user"]


def test_auth_register_duplicate_username(client):
    payload = {
        "username": "demo_user",
        "email": "farkli@dongu.org",
        "password": "password123"
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 400
    assert "zaten kullanılmaktadır" in response.json()["detail"]


def test_auth_login_success(client):
    # Kayıtlı demo kullanıcı ile giriş
    payload = {
        "username_or_email": "demo_user",
        "password": "demo_hashed_pass_123"
    }
    response = client.post("/api/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["username"] == "demo_user"
    assert "Giriş başarılı" in data["message"] or "Hoş geldiniz" in data["message"]


def test_auth_login_with_email(client):
    # E-posta ile giriş
    payload = {
        "username_or_email": "demo@dongu.org",
        "password": "demo_hashed_pass_123"
    }
    response = client.post("/api/auth/login", json=payload)
    assert response.status_code == 200
    assert response.json()["user"]["username"] == "demo_user"


def test_auth_login_wrong_password(client):
    payload = {
        "username_or_email": "demo_user",
        "password": "yanlis_parola"
    }
    response = client.post("/api/auth/login", json=payload)
    assert response.status_code == 401
    assert "hatalı" in response.json()["detail"]


def test_unauthorized_without_user_id(client):
    """X-User-Id gnderilmediinde veya geersiz olduunda 401 dner (artk varsaylan 1 atanmaz)."""
    res_no_header = client.get("/api/auth/me")
    assert res_no_header.status_code == 401
    assert "Oturum" in res_no_header.json()["detail"]

    res_invalid = client.get("/api/auth/me", headers={"X-User-Id": "999999"})
    assert res_invalid.status_code == 401
    assert "oturum" in res_invalid.json()["detail"]
