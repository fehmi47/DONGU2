from datetime import date, datetime
from decimal import Decimal
from typing import Optional, Literal
from pydantic import BaseModel, Field, ConfigDict, model_validator, field_validator
from app.schemas.category import CategoryResponse

DateTypeLiteral = Literal["STT", "TETT", "NONE"]
StorageLocationLiteral = Literal["fridge", "freezer", "pantry"]
ProductStatusLiteral = Literal["active", "consumed", "discarded"]
PriorityLevelLiteral = Literal["critical", "high", "medium", "low", "expired_stt", "no_date"]

# Sistemde kabul edilen standart gıda birimleri
VALID_UNITS = {
    "gram", "g", "kilogram", "kg", "mililitre", "ml", "litre", "l",
    "adet", "paket", "porsiyon", "kutu", "dilim", "bardak", "kaşık", "demet", "kavanoz"
}


class ProductBase(BaseModel):
    """
    Ürün için temel veri alanları ve ortak doğrulama kuralları.
    """
    category_id: int = Field(..., description="Ürünün ait olduğu kategori ID'si")
    name: str = Field(..., min_length=1, max_length=100, description="Ürün adı")
    quantity: Decimal = Field(..., gt=0, decimal_places=2, description="Ürün miktarı (sıfırdan büyük olmalıdır)")
    unit: str = Field(..., min_length=1, max_length=20, description="Ürün birimi (ör: kg, gram, adet, litre)")
    expiry_date: Optional[date] = Field(None, description="Son tüketim veya tavsiye edilen tüketim tarihi")
    date_type: DateTypeLiteral = Field("STT", description="Tarih türü: STT (Son Tüketim Tarihi), TETT veya NONE")
    storage_location: StorageLocationLiteral = Field("fridge", description="Saklama yeri: fridge (buzdolabı), freezer (dondurucu), pantry (kiler)")

    @field_validator("name")
    @classmethod
    def validate_name_not_empty(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Ürün adı sadece boşluklardan oluşamaz.")
        return stripped

    @field_validator("unit")
    @classmethod
    def validate_unit(cls, v: str) -> str:
        cleaned = v.strip().lower()
        if cleaned not in VALID_UNITS:
            raise ValueError(
                f"Geçersiz birim: '{v}'. Kabul edilen birimler: {', '.join(sorted(VALID_UNITS))}"
            )
        return cleaned


class ProductCreate(ProductBase):
    """
    Yeni ürün oluşturma isteği şeması.
    STT ve TETT seçildiğinde son tarih girilmesini zorunlu kılar.
    """
    @model_validator(mode="after")
    def validate_expiry_and_date_type(self):
        if self.date_type in ("STT", "TETT") and not self.expiry_date:
            raise ValueError(f"{self.date_type} seçildiğinde son tarih (expiry_date) girilmesi zorunludur.")
        return self


class ProductUpdate(BaseModel):
    """
    Mevcut ürün güncelleme şeması.
    Tüm alanlar opsiyoneldir; sadece güncellenmek istenen alanlar gönderilir.
    """
    category_id: Optional[int] = Field(None, description="Yeni kategori ID'si")
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Yeni ürün adı")
    quantity: Optional[Decimal] = Field(None, gt=0, decimal_places=2, description="Yeni miktar (sıfırdan büyük olmalı)")
    unit: Optional[str] = Field(None, min_length=1, max_length=20, description="Yeni birim")
    expiry_date: Optional[date] = Field(None, description="Yeni son tarih")
    date_type: Optional[DateTypeLiteral] = Field(None, description="Yeni tarih türü")
    storage_location: Optional[StorageLocationLiteral] = Field(None, description="Yeni saklama alanı")
    status: Optional[ProductStatusLiteral] = Field(None, description="Yeni ürün durumu")

    @field_validator("name")
    @classmethod
    def validate_name_not_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            stripped = v.strip()
            if not stripped:
                raise ValueError("Ürün adı sadece boşluklardan oluşamaz.")
            return stripped
        return v

    @field_validator("unit")
    @classmethod
    def validate_unit(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            cleaned = v.strip().lower()
            if cleaned not in VALID_UNITS:
                raise ValueError(
                    f"Geçersiz birim: '{v}'. Kabul edilen birimler: {', '.join(sorted(VALID_UNITS))}"
                )
            return cleaned
        return v

    @model_validator(mode="after")
    def validate_date_type_and_expiry(self):
        # Eğer tarih türü STT veya TETT olarak güncelleniyorsa ve expiry_date açıkça None yapılmışsa hata ver
        if self.date_type in ("STT", "TETT") and self.expiry_date is None:
            pass
        return self


class ProductResponse(BaseModel):
    """
    İstemciye dönülecek ürün yanıt şeması.
    İlişkili kategori bilgilerini ve veritabanı ID'sini içerir.
    """
    id: int
    user_id: int
    category_id: int
    name: str
    quantity: Decimal
    unit: str
    expiry_date: Optional[date] = None
    date_type: DateTypeLiteral
    storage_location: StorageLocationLiteral
    status: ProductStatusLiteral
    created_at: datetime
    updated_at: datetime
    category: Optional[CategoryResponse] = None

    model_config = ConfigDict(from_attributes=True)


class ProductPriorityResponse(ProductResponse):
    """
    Akıllı öncelik bilgileriyle zenginleştirilmiş ürün yanıt şeması.
    
    Ek Alanlar:
    - priority_level: Ürünün öncelik kategorisi ('critical', 'high', 'medium', 'low', 'expired_stt', 'no_date')
    - days_remaining: Son tarihe kalan gün sayısı (tarihsiz ürünlerde None, geçmişte negatif)
    - priority_message: Kullanıcıya yönelik gıda güvenliği ve tüketim yönlendirme mesajı
    - can_be_recommended: Ürünün tariflerde veya tüketimde önerilip önerilemeyeceği (STT geçmişse False)
    """
    priority_level: PriorityLevelLiteral = Field(..., description="Öncelik seviyesi")
    days_remaining: Optional[int] = Field(None, description="Kalan gün sayısı")
    priority_message: str = Field(..., description="Gıda güvenliği ve yönlendirme açıklaması")
    can_be_recommended: bool = Field(..., description="Tarif önerilerine uygun mu?")

