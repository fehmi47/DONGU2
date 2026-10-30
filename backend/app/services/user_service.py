from typing import List
from sqlalchemy.orm import Session
from app.models.user import User

DEFAULT_USERS = [
    {"id": 1, "username": "demo_user", "email": "demo@dongu.org", "password_hash": "demo_hashed_pass_123"},
    {"id": 2, "username": "test_user", "email": "test@dongu.org", "password_hash": "test_hashed_pass_456"},
    {"id": 3, "username": "ayse_kaya", "email": "ayse@dongu.org", "password_hash": "ayse_hashed_pass_789"},
]


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
