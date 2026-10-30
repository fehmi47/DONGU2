from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Literal
from pydantic import BaseModel, Field, ConfigDict

ActionTypeLiteral = Literal["consumed", "discarded", "recipe_used"]


class ConsumptionCreate(BaseModel):
    """
    Yeni tüketim veya değerlendirme kaydı oluşturma isteği.
    """
    product_id: int = Field(..., description="Tüketilen ürün ID'si")
    quantity_used: Decimal = Field(..., gt=0, decimal_places=2, description="Tüketilen miktar (sıfırdan büyük olmalıdır)")
    unit: str = Field(..., min_length=1, max_length=20, description="Miktar birimi")
    action_type: ActionTypeLiteral = Field("consumed", description="İşlem türü: consumed (doğrudan tüketildi), recipe_used (tarif için kullanıldı), discarded (atıldı/israf)")
    recipe_id: Optional[int] = Field(None, description="Eğer bir tarif kapsamında kullanıldıysa tarif ID'si")


class ConsumptionResponse(BaseModel):
    """
    İstemciye dönülecek tüketim günlüğü detayı.
    """
    id: int
    product_id: Optional[int] = None
    recipe_id: Optional[int] = None
    quantity_used: Decimal
    unit: str
    action_type: str
    recorded_at: datetime
    product_name: Optional[str] = Field(None, description="Ürün adı")
    recipe_name: Optional[str] = Field(None, description="Kullanılan tarif adı")

    model_config = ConfigDict(from_attributes=True)


class CategoryConsumptionSummary(BaseModel):
    """Kategori bazında kurtarılan/tüketilen gıda özeti."""
    category_id: int
    category_name: str
    total_quantity_kg: Decimal = Field(..., description="Kilogram cinsinden toplam miktar")
    log_count: int = Field(..., description="Kayıt sayısı")


class EnvironmentalImpactSummary(BaseModel):
    """
    Tahmini çevresel kazanım göstergeleri.
    Tüketilen gıdanın israf edilmemesi sayesinde önlenen çevresel yük.
    """
    estimated_co2_saved_kg: float = Field(..., description="Tahmini önlenen CO2 salınımı (kg)")
    estimated_water_saved_liters: float = Field(..., description="Tahmini kurtarılan su miktarı (litre)")
    is_estimate: bool = Field(True, description="Değerlerin tahmini olduğunu belirten bayrak")
    disclaimer: str = Field(
        "Çevresel kazanımlar, kurtarılan gıda miktarları baz alınarak küresel gıda yaşam döngüsü ortalamalarına göre hesaplanan tahmini değerlerdir.",
        description="Açıklama ve yasal uyarı"
    )


class ConsumptionSummaryResponse(BaseModel):
    """
    Kullanıcının gıda değerlendirme ve etki paneli özeti.
    Yalnızca doğrulanmış gerçek tüketim kayıtlarını yansıtır.
    """
    total_evaluated_kg: Decimal = Field(..., description="Toplam değerlendirilen gıda miktarı (kg)")
    weekly_evaluated_kg: Decimal = Field(..., description="Son 7 günde değerlendirilen miktar (kg)")
    monthly_evaluated_kg: Decimal = Field(..., description="Son 30 günde değerlendirilen miktar (kg)")
    completed_recipes_count: int = Field(..., description="Tamamlanan tarif sayısı (ilişkili tarif kayıtları)")
    total_logs_count: int = Field(..., description="Toplam tüketim işlemi sayısı")
    category_breakdown: List[CategoryConsumptionSummary] = Field(default=[], description="Kategori bazlı dağılım")
    environmental_impact: EnvironmentalImpactSummary = Field(..., description="Tahmini çevresel fayda analizi")
