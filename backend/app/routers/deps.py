from typing import Optional
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User


def get_current_user(
    db: Session = Depends(get_db),
    x_user_id: Optional[int] = Header(
        None,
        alias="X-User-Id",
        description="İşlemi gerçekleştiren kullanıcının ID'si (Kullanıcılar arası veri izolasyonu için)"
    )
) -> User:
    """
    İsteği yapan kullanıcıyı X-User-Id başlığı üzerinden doğrular.
    Başlık gönderilmemişse veya kullanıcı bulunamazsa 401 Unauthorized fırlatır.
    Varsayılan kullanıcı ID'si (1) KULLANILMAZ; herkes kendi ID'si ile işlem yapar.
    """
    if x_user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Oturum açmanız gerekiyor. Lütfen giriş yapın."
        )

    user = db.query(User).filter(User.id == x_user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Geçersiz kullanıcı oturumu. Lütfen tekrar giriş yapın."
        )
    return user
