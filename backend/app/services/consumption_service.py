from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.consumption_log import ConsumptionLog
from app.models.product import Product
from app.models.recipe import Recipe
from app.models.category import Category
from app.schemas.consumption import (
    ConsumptionCreate,
    ConsumptionResponse,
    CategoryConsumptionSummary,
    EnvironmentalImpactSummary,
    ConsumptionSummaryResponse,
)
from app.services.product_service import consume_product


def convert_to_kg(quantity: Decimal, unit: str) -> Decimal:
    """
    Farklı gıda birimlerini toplam istatistik ve çevresel analiz için
    yaklaşık kilogram (kg) cinsine dönüştürür.
    """
    u = unit.strip().lower()
    qty = Decimal(str(quantity))

    if u in ("kg", "kilogram"):
        return qty
    elif u in ("gram", "g"):
        return qty / Decimal("1000")
    elif u in ("litre", "l"):
        return qty  # Sıvı gıdalarda 1L ~ 1kg kabul edilir
    elif u in ("ml", "mililitre"):
        return qty / Decimal("1000")
    elif u in ("adet", "tane"):
        # Ortalama bir meyve/sebze/yumurta yaklaşık 150 gramdır
        return qty * Decimal("0.15")
    elif u in ("kaşık", "yemek kaşığı"):
        return qty * Decimal("0.015")
    elif u in ("paket", "kutu"):
        return qty * Decimal("0.40")
    elif u in ("demet",):
        return qty * Decimal("0.10")
    else:
        # Bilinmeyen birimlerde varsayılan tolerans
        return qty * Decimal("0.10")


def record_consumption(
    db: Session,
    user_id: int,
    consumption_in: ConsumptionCreate
) -> ConsumptionResponse:
    """
    Kullanıcının gıda tüketimini tek bir transaction içinde kaydeder,
    kilerdeki ürün miktarını düşer ve oluşturulan günlüğü döner.
    """
    product, log = consume_product(db, user_id=user_id, consumption_in=consumption_in)

    recipe_name = None
    if log.recipe_id:
        recipe = db.query(Recipe).filter(Recipe.id == log.recipe_id).first()
        if recipe:
            recipe_name = recipe.name

    return ConsumptionResponse(
        id=log.id,
        product_id=log.product_id,
        recipe_id=log.recipe_id,
        quantity_used=log.quantity_used,
        unit=log.unit,
        action_type=log.action_type,
        recorded_at=log.recorded_at,
        product_name=product.name if product else None,
        recipe_name=recipe_name,
    )


def get_user_consumptions(
    db: Session,
    user_id: int,
    limit: int = 50,
    offset: int = 0
) -> List[ConsumptionResponse]:
    """
    Kullanıcıya ait tüketim geçmişini en yeniden eskiye doğru listeler.
    Ürün adı ve varsa tarif adı ile zenginleştirilir.
    """
    # Kullanıcının ürünlerine ait tüketim loglarını çek
    logs = (
        db.query(ConsumptionLog)
        .join(Product, ConsumptionLog.product_id == Product.id)
        .filter(Product.user_id == user_id)
        .order_by(desc(ConsumptionLog.recorded_at))
        .offset(offset)
        .limit(limit)
        .all()
    )

    results = []
    for log in logs:
        prod_name = log.product.name if log.product else "Silinmiş Ürün"
        rec_name = log.recipe.name if log.recipe else None
        results.append(
            ConsumptionResponse(
                id=log.id,
                product_id=log.product_id,
                recipe_id=log.recipe_id,
                quantity_used=log.quantity_used,
                unit=log.unit,
                action_type=log.action_type,
                recorded_at=log.recorded_at,
                product_name=prod_name,
                recipe_name=rec_name,
            )
        )
    return results


def get_consumption_by_id(
    db: Session,
    user_id: int,
    log_id: int
) -> Optional[ConsumptionResponse]:
    """
    Belirli bir tüketim kaydının detayını döner. Kullanıcı izolasyonunu denetler.
    """
    log = (
        db.query(ConsumptionLog)
        .join(Product, ConsumptionLog.product_id == Product.id)
        .filter(ConsumptionLog.id == log_id, Product.user_id == user_id)
        .first()
    )
    if not log:
        return None

    prod_name = log.product.name if log.product else None
    rec_name = log.recipe.name if log.recipe else None
    return ConsumptionResponse(
        id=log.id,
        product_id=log.product_id,
        recipe_id=log.recipe_id,
        quantity_used=log.quantity_used,
        unit=log.unit,
        action_type=log.action_type,
        recorded_at=log.recorded_at,
        product_name=prod_name,
        recipe_name=rec_name,
    )


def calculate_consumption_summary(
    db: Session,
    user_id: int
) -> ConsumptionSummaryResponse:
    """
    Kullanıcının değerlendirdiği gıdaların etki analizini hesaplar:
    - Yalnızca 'consumed' veya 'recipe_used' olan gerçek kurtarılmış kayıtları hesaplar.
    - 'discarded' (israf edilen) kayıtları değerlendirilen gıdaya dahil etmez!
    - Kategori bazlı dağılımı ve haftalık/aylık trendleri çıkarır.
    - Tahmini CO2 ve su tasarrufunu hesaplar.
    """
    now = datetime.utcnow()
    seven_days_ago = now - timedelta(days=7)
    thirty_days_ago = now - timedelta(days=30)

    # Kullanıcının tüm tüketim kayıtları
    logs = (
        db.query(ConsumptionLog)
        .join(Product, ConsumptionLog.product_id == Product.id)
        .filter(Product.user_id == user_id)
        .all()
    )

    total_evaluated_kg = Decimal("0.0")
    weekly_evaluated_kg = Decimal("0.0")
    monthly_evaluated_kg = Decimal("0.0")
    completed_recipes = set()
    category_totals: Dict[int, Dict[str, Any]] = {}

    for log in logs:
        # Sadece fiilen tüketilen ve değerlendirilen gıdalar (atılanlar değerlendirilmiş sayılmaz!)
        if log.action_type in ("consumed", "recipe_used"):
            kg_amount = convert_to_kg(log.quantity_used, log.unit)
            total_evaluated_kg += kg_amount

            if log.recorded_at >= seven_days_ago:
                weekly_evaluated_kg += kg_amount

            if log.recorded_at >= thirty_days_ago:
                monthly_evaluated_kg += kg_amount

            if log.recipe_id:
                completed_recipes.add(log.recipe_id)

            # Kategori bazlı biriktirme
            if log.product and log.product.category_id:
                cat_id = log.product.category_id
                cat_name = log.product.category.name if log.product.category else "Diğer"
                if cat_id not in category_totals:
                    category_totals[cat_id] = {
                        "category_id": cat_id,
                        "category_name": cat_name,
                        "total_kg": Decimal("0.0"),
                        "count": 0,
                    }
                category_totals[cat_id]["total_kg"] += kg_amount
                category_totals[cat_id]["count"] += 1

    # Kategori döküm listesi
    category_breakdown = [
        CategoryConsumptionSummary(
            category_id=v["category_id"],
            category_name=v["category_name"],
            total_quantity_kg=round(v["total_kg"], 2),
            log_count=v["count"],
        )
        for v in category_totals.values()
    ]
    category_breakdown.sort(key=lambda x: x.total_quantity_kg, reverse=True)

    # Çevresel fayda analizi (1 kg gıda israfı ortalama 2.5 kg CO2 ve 900 litre su tasarrufu sağlar)
    total_kg_float = float(total_evaluated_kg)
    estimated_co2 = round(total_kg_float * 2.5, 2)
    estimated_water = round(total_kg_float * 900.0, 1)

    return ConsumptionSummaryResponse(
        total_evaluated_kg=round(total_evaluated_kg, 2),
        weekly_evaluated_kg=round(weekly_evaluated_kg, 2),
        monthly_evaluated_kg=round(monthly_evaluated_kg, 2),
        completed_recipes_count=len(completed_recipes),
        total_logs_count=len(logs),
        category_breakdown=category_breakdown,
        environmental_impact=EnvironmentalImpactSummary(
            estimated_co2_saved_kg=estimated_co2,
            estimated_water_saved_liters=estimated_water,
            is_estimate=True,
        ),
    )
