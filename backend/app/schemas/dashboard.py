from decimal import Decimal
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from app.schemas.consumption import ConsumptionResponse, CategoryConsumptionSummary, EnvironmentalImpactSummary


class WeeklyStatItem(BaseModel):
    """Günlük tüketim/kurtarma istatistik kalemi."""
    date_str: str = Field(..., description="Tarih etiketi (Örn: 28 Eki)")
    day_name: str = Field(..., description="Gün adı (Örn: Pazartesi)")
    amount_kg: float = Field(..., description="O gün değerlendirilen gıda (kg)")


class DashboardSummaryResponse(BaseModel):
    """
    Ana kontrol paneli için konsolide metrik ve durum özeti.
    """
    active_products_count: int = Field(..., description="Mutfaktaki aktif ürün sayısı")
    expiring_stt_count: int = Field(..., description="STT tarihi yaklaşan (0-3 gün) ürün sayısı")
    expiring_tett_count: int = Field(..., description="TETT tarihi yaklaşan ürün sayısı")
    critical_priority_count: int = Field(..., description="Acil tüketilmesi gereken ürün sayısı")
    high_priority_count: int = Field(..., description="Yüksek öncelikli ürün sayısı")
    
    total_evaluated_kg: Decimal = Field(..., description="Toplam değerlendirilen gıda (kg)")
    weekly_evaluated_kg: Decimal = Field(..., description="Bu hafta değerlendirilen gıda (kg)")
    completed_recipes_count: int = Field(..., description="Tamamlanan tarif sayısı")
    unread_notifications_count: int = Field(..., description="Okunmamış bildirim sayısı")
    
    weekly_stats: List[WeeklyStatItem] = Field(default=[], description="Son 7 günün tüketim trendi")
    category_distribution: List[CategoryConsumptionSummary] = Field(default=[], description="Kategori bazlı değerlendirme dağılımı")
    recent_consumptions: List[ConsumptionResponse] = Field(default=[], description="Son yapılan tüketim hareketleri")
    environmental_impact: EnvironmentalImpactSummary = Field(..., description="Tahmini çevresel kazanımlar")
