"""
DÖNGÜ AI Asistanı - Pydantic Şemaları

Sohbet istek ve yanıt modellerini tanımlar.
"""

from typing import List
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Kullanıcının asistana yönelttiği soru veya talimat.",
        json_schema_extra={"example": "Bugün hangi ürünlerimi tüketmeliyim?"},
    )


class ChatResponse(BaseModel):
    answer: str = Field(
        ...,
        description="Asistanın ürettiği Türkçe doğal dil yanıtı.",
    )
    tools: List[str] = Field(
        default_factory=list,
        description="Bu yanıtı üretirken kullanılan backend araçlarının adları.",
        json_schema_extra={"example": ["get_priority_products"]},
    )
