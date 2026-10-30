from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class IngredientDeductionInput(BaseModel):
    """
    Yapay zekâlı Şef Ajan'dan veya tarif onayından gelen tek bir malzeme düşüm talebi.
    """
    name: str = Field(..., min_length=1, description="Malzeme adı (örn: domates, yumurta, soğan)")
    quantity: Decimal = Field(..., gt=0, description="Düşülecek miktar")
    unit: str = Field(..., min_length=1, description="Birim (adet, gr, kg, l, ml)")
    product_id: Optional[int] = Field(None, description="Opsiyonel olarak doğrudan hedeflenen ürün ID'si")

    model_config = ConfigDict(from_attributes=True)


class RecipeDeductionRequest(BaseModel):
    """
    Şef Ajan tarif onayıyla toplu stok düşüm istek şeması.
    """
    recipe_id: Optional[int] = Field(None, description="Tarif ID'si")
    recipe_name: Optional[str] = Field(None, description="Tarif başlığı")
    ingredients: List[IngredientDeductionInput] = Field(..., min_length=1, description="Düşülecek malzeme listesi")


class DeductionResultItem(BaseModel):
    """
    Başarıyla düşülen her bir ürünün stok değişim detayları.
    """
    product_id: int
    product_name: str
    requested_quantity: Decimal
    requested_unit: str
    deducted_quantity: Decimal
    stock_unit: str
    previous_stock: Decimal
    remaining_stock: Decimal
    status: str

    model_config = ConfigDict(from_attributes=True)


class RecipeDeductionResponse(BaseModel):
    """
    Akıllı stok düşüm işlemi sonucu dönen özet yanıt şeması.
    """
    success: bool = True
    message: str
    deductions: List[DeductionResultItem]
    consumed_products: List[str] = Field(default_factory=list, description="Miktarı 0'a ulaşıp CONSUMED statüsüne geçen ürünler")
