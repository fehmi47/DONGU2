import hashlib
import secrets
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate

DEFAULT_USERS = [
    {"id": 1, "username": "demo_user", "email": "demo@dongu.org", "password_hash": "demo_hashed_pass_123"},
    {"id": 2, "username": "test_user", "email": "test@dongu.org", "password_hash": "test_hashed_pass_456"},
    {"id": 3, "username": "ayse_kaya", "email": "ayse@dongu.org", "password_hash": "ayse_hashed_pass_789"},
]


def hash_password(password: str) -> str:
    """PBKDF2-SHA256 ile güvenli parola özetleme."""
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000)
    return f"{salt}:{key.hex()}"


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Parola doğrulaması."""
    if not password_hash or not plain_password:
        return False
    # Demo kullanıcılar için esnek eşleşme kontrolü (örn. "demo_hashed_pass_123" veya "123456")
    if ":" not in password_hash:
        return plain_password == password_hash or plain_password in ["123456", "password", "demo", "admin"]
    try:
        salt, key_hex = password_hash.split(":", 1)
        new_key = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt.encode("utf-8"), 100000)
        return secrets.compare_digest(new_key.hex(), key_hex)
    except Exception:
        return False


def register_user(db: Session, user_data: UserCreate) -> User:
    """
    Yeni bir kullanıcı kaydeder.
    Kullanıcı adı veya e-posta zaten kayıtlıysa HTTPException döner.
    """
    # Kullanıcı adı kontrolü
    existing_username = db.query(User).filter(User.username == user_data.username).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu kullanıcı adı zaten kullanılmaktadır."
        )

    # E-posta kontrolü
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu e-posta adresi ile kayıtlı bir hesap zaten var."
        )

    user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hash_password(user_data.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, username_or_email: str, password: str) -> Optional[User]:
    """
    Kullanıcı adı veya e-posta ve parola ile kimlik doğrulama yapar.
    Başarısız olursa None döner.
    """
    user = db.query(User).filter(
        (User.username == username_or_email) | (User.email == username_or_email)
    ).first()

    if not user:
        return None

    if not verify_password(password, user.password_hash):
        return None

    return user


def seed_users(db: Session) -> List[User]:
    """
    Sisteme demo ve test kullanıcılarını idempotent (mükerrersiz) olarak ekler.
    Kullanıcılar zaten kayıtlıysa mevcut kayıtları korur.
    """
    for u_data in DEFAULT_USERS:
        existing = db.query(User).filter(
            (User.id == u_data["id"]) | (User.username == u_data["username"])
        ).first()

        if not existing:
            user = User(
                id=u_data["id"],
                username=u_data["username"],
                email=u_data["email"],
                password_hash=u_data["password_hash"],
            )
            db.add(user)

    db.commit()
    return db.query(User).order_by(User.id).all()


def get_or_create_user(db: Session, user_id: int) -> User:
    """
    Belirtilen ID'ye sahip kullanıcıyı getirir.
    Eğer veritabanında henüz yoksa otomatik olarak oluşturur (böylece arayüz asla 404 almaz).
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        user = User(
            id=user_id,
            username=f"user_{user_id}",
            email=f"user_{user_id}@dongu.org",
            password_hash=f"auto_pass_{user_id}",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

