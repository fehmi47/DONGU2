from datetime import datetime, timedelta, date
from decimal import Decimal
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from app.models.product import Product
from app.models.notification import Notification
from app.models.consumption_log import ConsumptionLog
from app.schemas.dashboard import DashboardSummaryResponse, WeeklyStatItem
from app.services.consumption_service import (
    calculate_consumption_summary,
    get_user_consumptions,
    convert_to_kg,
)
from app.services.priority_service import evaluate_product_priority
from app.services.notification_service import check_and_generate_notifications


TURKISH_DAYS = {
    0: "Pazartesi",
    1: "Salı",
    2: "Çarşamba",
    3: "Perşembe",
    4: "Cuma",
    5: "Cumartesi",
    6: "Pazar",
}


def get_dashboard_summary(db: Session, user_id: int) -> DashboardSummaryResponse:
    """
    Kullanıcının ana paneli için tüm özet istatistikleri konsolide eder.
    Tüm veriler tamamen oturum açan kullanıcının kendi kayıtlarından hesaplanır.
    """
    # Bildirimleri güncelle
    check_and_generate_notifications(db, user_id)

    # 1. Aktif ürünler ve öncelik sayıları
    active_products = db.query(Product).filter(
        Product.user_id == user_id,
        Product.status == "active"
    ).all()

    active_count = len(active_products)
    expiring_stt_count = 0
    expiring_tett_count = 0
    critical_count = 0
    high_count = 0

    for p in active_products:
        eval_res = evaluate_product_priority(p)
        if eval_res.priority_level == "critical":
            critical_count += 1
        elif eval_res.priority_level == "high":
            high_count += 1

        if eval_res.days_remaining is not None and 0 <= eval_res.days_remaining <= 3:
            if p.date_type == "STT":
                expiring_stt_count += 1
            elif p.date_type == "TETT":
                expiring_tett_count += 1

    # 2. Tüketim ve etki özeti
    consumption_summary = calculate_consumption_summary(db, user_id=user_id)

    # 3. Son 7 günün günlük tüketim grafiği verisi
    now = datetime.utcnow()
    weekly_stats: List[WeeklyStatItem] = []

    # Günlük harita oluştur
    daily_amounts: Dict[str, Decimal] = {}
    for i in range(6, -1, -1):
        target_day = now - timedelta(days=i)
        key = target_day.strftime("%Y-%m-%d")
        daily_amounts[key] = Decimal("0.0")

    # Kullanıcının loglarını günlere dağıt
    user_logs = (
        db.query(ConsumptionLog)
        .join(Product, ConsumptionLog.product_id == Product.id)
        .filter(
            Product.user_id == user_id,
            ConsumptionLog.action_type.in_(["consumed", "recipe_used"]),
            ConsumptionLog.recorded_at >= (now - timedelta(days=7))
        )
        .all()
    )

    for log in user_logs:
        day_key = log.recorded_at.strftime("%Y-%m-%d")
        if day_key in daily_amounts:
            daily_amounts[day_key] += convert_to_kg(log.quantity_used, log.unit)

    # WeeklyStatItem listesine dönüştür
    for i in range(6, -1, -1):
        target_day = now - timedelta(days=i)
        key = target_day.strftime("%Y-%m-%d")
        amount = daily_amounts[key]
        weekly_stats.append(
            WeeklyStatItem(
                date_str=target_day.strftime("%d.%m"),
                day_name=TURKISH_DAYS[target_day.weekday()],
                amount_kg=float(round(amount, 2)),
            )
        )

    # 4. Okunmamış bildirimler
    unread_notif_count = db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.is_read == False  # noqa: E712
    ).count()

    # 5. Son 5 tüketim işlemi
    recent_consumptions = get_user_consumptions(db, user_id=user_id, limit=5)

    return DashboardSummaryResponse(
        active_products_count=active_count,
        expiring_stt_count=expiring_stt_count,
        expiring_tett_count=expiring_tett_count,
        critical_priority_count=critical_count,
        high_priority_count=high_count,
        total_evaluated_kg=consumption_summary.total_evaluated_kg,
        weekly_evaluated_kg=consumption_summary.weekly_evaluated_kg,
        completed_recipes_count=consumption_summary.completed_recipes_count,
        unread_notifications_count=unread_notif_count,
        weekly_stats=weekly_stats,
        category_distribution=consumption_summary.category_breakdown,
        recent_consumptions=recent_consumptions,
        environmental_impact=consumption_summary.environmental_impact,
    )
