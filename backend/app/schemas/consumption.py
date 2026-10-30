from datetime import datetime
from decimal import Decimal
from typing import Optional, Literal
from pydantic import BaseModel, Field, ConfigDict


ActionTypeLiteral = Literal["consumed", "discarded", "recipe_used"]


class ConsumptionCreate(BaseModel):
    product_id: int
    quantity_used: Decimal = Field(..., gt=0, decimal_places=2, description="Tüketim miktarı sıfırdan büyük olmalıdır.")
    unit: str = Field(..., min_length=1, max_length=20)
    action_type: ActionTypeLiteral = "consumed"
    recipe_id: Optional[int] = None


class ConsumptionResponse(BaseModel):
    id: int
    product_id: Optional[int] = None
    recipe_id: Optional[int] = None
    quantity_used: Decimal
    unit: str
    action_type: str
    recorded_at: datetime

    model_config = ConfigDict(from_attributes=True)
