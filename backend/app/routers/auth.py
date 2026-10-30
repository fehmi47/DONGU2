from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, UserLogin, AuthResponse
from app.services.user_service import register_user, authenticate_user, DEFAULT_USERS
from app.routers.deps import get_current_user

router = APIRouter(prefix="/api/auth", tags=["Kimlik Doğrulama"])


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED, summary="Yeni Kullanıcı Kaydı")
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Sisteme yeni bir kullanıcı kaydeder.
    Kullanıcı adı ve e-posta benzersiz olmalıdır.
    """
    user = register_user(db, user_data)
    return AuthResponse(
        user=UserResponse.model_validate(user),
        message="Hesabınız başarıyla oluşturuldu! Hoş geldiniz."
    )


@router.post("/login", response_model=AuthResponse, summary="Kullanıcı Girişi")
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Kullanıcı adı / e-posta ve parola ile giriş yapar.
    Başarılı girişte kullanıcı bilgilerini döner.
    """
    user = authenticate_user(db, credentials.username_or_email, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kullanıcı adı, e-posta veya parola hatalı."
        )

    return AuthResponse(
        user=UserResponse.model_validate(user),
        message=f"Hoş geldiniz, {user.username}!"
    )


@router.get("/me", response_model=UserResponse, summary="Aktif Oturum Bilgisi")
def get_me(current_user: User = Depends(get_current_user)):
    """
    İsteği gönderen aktif kullanıcının bilgilerini döner.
    """
    return current_user


@router.get("/demo-users", summary="Hızlı Giriş İçin Demo Kullanıcılar")
def get_demo_users():
    """
    Arayüzde tek tıkla test girişi yapabilmek için tanımlı demo kullanıcı listesini döner.
    """
    return [
        {"id": u["id"], "username": u["username"], "email": u["email"]}
        for u in DEFAULT_USERS
    ]
