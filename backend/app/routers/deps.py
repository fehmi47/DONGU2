from typing import Optional
from fastapi import Depends, Header
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.services.user_service import get_or_create_user


def get_current_user(
    db: Session = Depends(get_db),
    x_user_id: Optional[int] = Header(
        None,
        alias="X-User-Id",
        description="İşlemi gerçekleştiren kullanıcının ID'si (Kullanıcılar arası veri izolasyonu için)"
    )
) -> User:
    """
    İsteği yapan kullanıcıyı tespit eden bağımlılık fonksiyonu.
    
    Çalışma Mantığı:
    - Başlıkta 'X-User-Id' gönderilmişse (örneğin 1, 2 veya 3), ilgili kullanıcıyı getirir.
      Eğer veritabanında henüz oluşturulmamışsa otomatik olarak oluşturur (asla 404 vermez).
    - Eğer 'X-User-Id' gönderilmemişse, varsayılan olarak ID: 1 (demo_user) kullanıcısını döner.
    """
    target_id = x_user_id if x_user_id is not None else 1
    return get_or_create_user(db, user_id=target_id)
