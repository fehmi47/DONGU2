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
    İsteği yapan kullanıcıyı tespit eden FastAPI bağımlılık fonksiyonu.
    
    Çalışma Mantığı:
    - İstek başlığında (Header) 'X-User-Id' gönderilmişse, veritabanından ilgili kullanıcıyı sorgular.
      Kullanıcı bulunamazsa 404 Not Found hatası fırlatır.
    - Eğer 'X-User-Id' gönderilmemişse (örneğin Swagger üzerinden doğrudan test yapılıyorsa),
      sistemdeki 'demo_user' kullanıcısını döner veya otomatik oluşturur.
    - Böylece hem testlerde ve API çağrılarında kullanıcı izolasyonu tam sağlanır, hem de Swagger
      üzerinden kolayca deneme yapılabilir.
    """
    if x_user_id is not None:
        user = db.query(User).filter(User.id == x_user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{x_user_id} ID'li kullanıcı bulunamadı."
            )
        return user

    # Başlık gönderilmediğinde varsayılan demo kullanıcıyı temin etme
    default_user = db.query(User).filter(User.username == "demo_user").first()
    if not default_user:
        default_user = User(
            username="demo_user",
            email="demo@dongu.org",
            password_hash="demo_hashed_password"
        )
        db.add(default_user)
        db.commit()
        db.refresh(default_user)

    return default_user
