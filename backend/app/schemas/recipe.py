from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class RecipeIngredientBase(BaseModel):
    """
    Tarif malzemesi için temel veri alanları.
    """
    ingredient_name: str = Field(..., min_length=1, max_length=100, description="Malzeme adı")
    quantity: Decimal = Field(..., gt=0, decimal_places=2, description="Gereken miktar")
    unit: str = Field(..., min_length=1, max_length=20, description="Miktar birimi")
    is_optional: bool = Field(False, description="Malzemenin opsiyonel olup olmadığı")


class RecipeIngredientCreate(RecipeIngredientBase):
    """Tarif oluştururken gönderilen malzeme şeması."""
    pass


class RecipeIngredientResponse(RecipeIngredientBase):
    """İstemciye dönülecek malzeme yanıt şeması."""
    id: int
    recipe_id: int

    model_config = ConfigDict(from_attributes=True)


class RecipeBase(BaseModel):
    """
    Yemek tarifi temel bilgileri.
    """
    name: str = Field(..., min_length=2, max_length=150, description="Tarif adı")
    description: str = Field(..., description="Tarif açıklaması ve püf noktaları")
    instructions: str = Field(..., description="Hazırlanış ve pişirme adımları")
    preparation_time: int = Field(..., ge=0, description="Hazırlık süresi (dakika)")
    cooking_time: int = Field(..., ge=0, description="Pişirme süresi (dakika)")
    servings: int = Field(..., gt=0, description="Kaç kişilik olduğu")
    difficulty: str = Field(..., min_length=1, max_length=20, description="Zorluk seviyesi (Kolay, Orta, Zor)")
    image_url: Optional[str] = Field(None, description="Tarif görseli URL adresi")


class RecipeCreate(RecipeBase):
    """Yeni tarif oluşturma şeması (malzemelerle birlikte gönderilebilir)."""
    ingredients: List[RecipeIngredientCreate] = []


class RecipeUpdate(BaseModel):
    """Tarif güncelleme şeması."""
    name: Optional[str] = Field(None, min_length=2, max_length=150)
    description: Optional[str] = None
    instructions: Optional[str] = None
    preparation_time: Optional[int] = Field(None, ge=0)
    cooking_time: Optional[int] = Field(None, ge=0)
    servings: Optional[int] = Field(None, gt=0)
    difficulty: Optional[str] = Field(None, min_length=1, max_length=20)
    image_url: Optional[str] = None
    ingredients: Optional[List[RecipeIngredientCreate]] = None


class RecipeResponse(RecipeBase):
    """İstemciye dönülecek tam tarif yanıt şeması."""
    id: int
    ingredients: List[RecipeIngredientResponse] = []

    model_config = ConfigDict(from_attributes=True)


# ==============================================================================
# AKILLI TARİF EŞLEŞTİRME VE ÖNERİ ŞEMALARI
# ==============================================================================

class MatchedIngredientInfo(BaseModel):
    """
    Kullanıcının kilerinde bulunan ve tarifle eşleşen malzeme bilgisi.
    """
    ingredient_name: str = Field(..., description="Tarifteki malzeme adı")
    required_quantity: Decimal = Field(..., description="Tarifin istediği miktar")
    required_unit: str = Field(..., description="Tarifin istediği birim")
    product_id: int = Field(..., description="Kullanıcının kilerindeki ürün ID'si")
    product_name: str = Field(..., description="Kullanıcının kilerindeki ürün adı")
    available_quantity: Decimal = Field(..., description="Kilerdeki mevcut miktar")
    available_unit: str = Field(..., description="Kilerdeki birim")
    is_sufficient: bool = Field(..., description="Eldeki miktar tarif için yeterli mi?")
    priority_level: str = Field(..., description="Ürünün öncelik seviyesi (critical, high, medium, low, no_date)")


class MissingIngredientInfo(BaseModel):
    """
    Tarifin ihtiyaç duyduğu ancak kullanıcının kilerinde bulunmayan veya yetersiz olan malzeme.
    """
    ingredient_name: str = Field(..., description="Eksik malzeme adı")
    quantity: Decimal = Field(..., description="İhtiyaç duyulan miktar")
    unit: str = Field(..., description="Birim")
    is_optional: bool = Field(False, description="Malzeme opsiyonel mi?")
    reason: str = Field(..., description="Eksiklik nedeni (Örn: 'Kilerde bulunmuyor' veya 'Miktar yetersiz')")


class RecipeRecommendationResponse(RecipeBase):
    """
    Akıllı tarif öneri yanıt şeması.
    Kullanıcının kilerine göre hesaplanmış eşleşme yüzdesi, eksik malzemeler ve öncelik puanını barındırır.
    """
    id: int
    total_time: int = Field(..., description="Toplam süre (hazırlık + pişirme dakika)")
    ingredients: List[RecipeIngredientResponse] = []
    matched_ingredients: List[MatchedIngredientInfo] = []
    missing_ingredients: List[MissingIngredientInfo] = []
    match_percentage: float = Field(..., description="Malzeme eşleşme yüzdesi (0-100)")
    can_prepare: bool = Field(..., description="Mevcut stokla hemen hazırlanabilir mi?")
    priority_score: float = Field(..., description="Öncelikli gıdaları değerlendirme skoru")

    model_config = ConfigDict(from_attributes=True)
