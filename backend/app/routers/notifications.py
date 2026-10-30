from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.notification import NotificationResponse
from app.services.notification_service import (
    get_user_notifications,
    get_notification_by_id,
    mark_notification_as_read,
    mark_all_notifications_as_read,
)
from app.routers.deps import get_current_user

router = APIRouter(prefix="/api/notifications", tags=["Bildirimler"])


@router.get(
    "",
    response_model=List[NotificationResponse],
    summary="Bildirimleri listele",
    description="Kullanıcıya ait bildirimleri listeler. Öncelikli ve tarihi yaklaşan gıdalar için otomatik denetim yapar."
)
def list_notifications(
    unread_only: bool = Query(False, description="Yalnızca okunmamış bildirimleri filtrele"),
    limit: int = Query(50, ge=1, le=100, description="Kayıt limiti"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Kullanıcının bildirimlerini döner.
    """
    return get_user_notifications(db, user_id=current_user.id, unread_only=unread_only, limit=limit)


@router.patch(
    "/read-all",
    summary="Tüm bildirimleri okundu olarak işaretle",
    description="Kullanıcının tüm okunmamış bildirimlerini okundu durumuna getirir."
)
def read_all_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Tüm bildirimleri okundu yapar.
    """
    count = mark_all_notifications_as_read(db, user_id=current_user.id)
    return {"detail": f"{count} adet bildirim okundu olarak işaretlendi."}


@router.get(
    "/{id}",
    response_model=NotificationResponse,
    summary="Tek bildirim detayını getir",
    description="Belirtilen bildirimin detayını getirir."
)
def get_notification(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Bildirim detayını getirir.
    """
    notif = get_notification_by_id(db, user_id=current_user.id, notification_id=id)
    if not notif:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{id} ID'li bildirim bulunamadı."
        )
    return notif


@router.patch(
    "/{id}/read",
    response_model=NotificationResponse,
    summary="Bildirimi okundu olarak işaretle",
    description="Belirtilen bildirimi okundu durumuna günceller."
)
def read_notification(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Tek bir bildirimi okundu yapar.
    """
    notif = mark_notification_as_read(db, user_id=current_user.id, notification_id=id)
    if not notif:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{id} ID'li bildirim bulunamadı."
        )
    return notif
