from datetime import datetime, timedelta, date
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.notification import Notification
from app.models.product import Product
from app.schemas.notification import NotificationResponse
from app.services.priority_service import evaluate_product_priority


def check_and_generate_notifications(db: Session, user_id: int) -> int:
    """
    Kullanıcının kilerindeki ürünleri denetler ve acil olanlar için bildirim üretir.
    
    Mükerrer Bildirim Engelleme:
    - Son 24 saat içinde aynı ürün ve bildirim türü için zaten bir bildirim varsa
      tekrar yeni bildirim oluşturmaz (sayfa yenilemelerinde kirliliği önler).
    """
    products = db.query(Product).filter(
        Product.user_id == user_id,
        Product.status == "active"
    ).all()

    now = datetime.utcnow()
    one_day_ago = now - timedelta(hours=24)
    new_notifications_count = 0

    for prod in products:
        eval_res = evaluate_product_priority(prod)

        # Yalnızca critical, high veya expired_stt durumlarında bildirim oluştur
        if eval_res.priority_level in ("critical", "high", "expired_stt"):
            notif_type = f"alert_{eval_res.priority_level}"

            # Mükerrerlik kontrolü: Son 24 saat içinde bu ürün için bildirim var mı?
            recent_exists = (
                db.query(Notification)
                .filter(
                    Notification.user_id == user_id,
                    Notification.product_id == prod.id,
                    Notification.notification_type == notif_type,
                    Notification.created_at >= one_day_ago,
                )
                .first()
            )

            if not recent_exists:
                if eval_res.priority_level == "expired_stt":
                    title = f"⚠️ Son Tüketim Tarihi Geçti: {prod.name}"
                elif eval_res.priority_level == "critical":
                    title = f"🚨 Acil Tüketilmeli: {prod.name}"
                else:
                    title = f"⏰ Tarihi Yaklaşıyor: {prod.name}"

                notification = Notification(
                    user_id=user_id,
                    product_id=prod.id,
                    title=title,
                    message=eval_res.priority_message,
                    notification_type=notif_type,
                    is_read=False,
                    created_at=now,
                )
                db.add(notification)
                new_notifications_count += 1

    if new_notifications_count > 0:
        db.commit()

    return new_notifications_count


def get_user_notifications(
    db: Session,
    user_id: int,
    unread_only: bool = False,
    limit: int = 50
) -> List[Notification]:
    """
    Kullanıcının bildirimlerini listeler.
    Otomatik olarak yeni durumları da denetler.
    """
    check_and_generate_notifications(db, user_id)

    query = db.query(Notification).filter(Notification.user_id == user_id)
    if unread_only:
        query = query.filter(Notification.is_read == False)  # noqa: E712

    return query.order_by(desc(Notification.created_at)).limit(limit).all()


def get_notification_by_id(
    db: Session,
    user_id: int,
    notification_id: int
) -> Optional[Notification]:
    """
    Tek bir bildirimi getirir (kullanıcı izolasyonlu).
    """
    return db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == user_id
    ).first()


def mark_notification_as_read(
    db: Session,
    user_id: int,
    notification_id: int
) -> Optional[Notification]:
    """
    Bildirimi okundu olarak işaretler.
    """
    notif = get_notification_by_id(db, user_id=user_id, notification_id=notification_id)
    if not notif:
        return None

    notif.is_read = True
    db.commit()
    db.refresh(notif)
    return notif


def mark_all_notifications_as_read(db: Session, user_id: int) -> int:
    """
    Kullanıcının tüm okunmamış bildirimlerini okundu durumuna getirir.
    Etkilenen kayıt sayısını döner.
    """
    updated_count = (
        db.query(Notification)
        .filter(Notification.user_id == user_id, Notification.is_read == False)  # noqa: E712
        .update({Notification.is_read: True})
    )
    db.commit()
    return updated_count
