from datetime import date, datetime
from decimal import Decimal
from typing import Optional, Literal
from pydantic import BaseModel, Field, ConfigDict, model_validator
from app.schemas.category import CategoryResponse


DateTypeLiteral = Literal["STT", "TETT", "NONE"]
StorageLocationLiteral = Literal["fridge", "freezer", "pantry"]
ProductStatusLiteral = Literal["active", "consumed", "discarded"]


class ProductBase(BaseModel):
    category_id: int
    name: str = Field(..., min_length=1, max_length=100)
    quantity: Decimal = Field(..., ge=0, decimal_places=2)
    unit: str = Field(..., min_length=1, max_length=20)
    expiry_date: Optional[date] = None
    date_type: DateTypeLiteral = "STT"
    storage_location: StorageLocationLiteral = "fridge"


class ProductCreate(ProductBase):
    @model_validator(mode="after")
    def validate_expiry_and_date_type(self):
        if self.date_type in ("STT", "TETT") and not self.expiry_date:
            raise ValueError(f"{self.date_type} seçildiğinde son tarih (expiry_date) girilmesi zorunludur.")
        return self


class ProductUpdate(BaseModel):
    category_id: Optional[int] = None
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    quantity: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    unit: Optional[str] = Field(None, min_length=1, max_length=20)
    expiry_date: Optional[date] = None
    date_type: Optional[DateTypeLiteral] = None
    storage_location: Optional[StorageLocationLiteral] = None
    status: Optional[ProductStatusLiteral] = None

    @model_validator(mode="after")
    def validate_date_type_and_expiry(self):
        if self.date_type in ("STT", "TETT") and self.expiry_date is None:
            # Only validate if date_type was explicitly updated
            pass
        return self


class ProductResponse(ProductBase):
    id: int
    user_id: int
    status: ProductStatusLiteral
    created_at: datetime
    updated_at: datetime
    category: Optional[CategoryResponse] = None

    model_config = ConfigDict(from_attributes=True)
