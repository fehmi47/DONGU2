"""
DÖNGÜ AI Asistanı - Pydantic Şemaları

Sohbet istek ve yanıt modellerini tanımlar.
Backend stateless mimariyi korur; konuşma bağlamı (history) frontend tarafından iletilir.
"""

from typing import List, Literal
from pydantic import BaseModel, Field


class ChatTurn(BaseModel):
    """
    Sohbet geçmişindeki tek bir konuşma turunu (kullanıcı veya asistan mesajı) temsil eder.
    Güvenlik: Yalnızca 'user' ve 'assistant' rollerine izin verilir; 'system' veya 'tool' rolleri reddedilir.
    """
    role: Literal["user", "assistant"] = Field(
        ...,
        description="Mesajı gönderen taraf. Güvenlik gereği yalnızca 'user' veya 'assistant' olabilir.",
    )
    content: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        description="Mesaj içeriği (maksimum 4000 karakter).",
    )


class ChatRequest(BaseModel):
    """
    Kullanıcının asistana gönderdiği soru ve opsiyonel konuşma bağlamı isteği.
    """
    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Kullanıcının asistana yönelttiği yeni soru veya talimat.",
        json_schema_extra={"example": "Bugün hangi ürünlerimi tüketmeliyim?"},
    )
    history: List[ChatTurn] = Field(
        default_factory=list,
        max_length=10,
        description="Son 10 sohbet mesajı geçmişi. Boş bırakılabilir (geriye dönük uyumlu).",
    )


class ChatResponse(BaseModel):
    """
    Asistanın kullanıcıya döndürdüğü yanıt modeli.
    """
    answer: str = Field(
        ...,
        description="Asistanın ürettiği Türkçe doğal dil yanıtı.",
    )
    tools: List[str] = Field(
        default_factory=list,
        description="Bu yanıtı üretirken kullanılan backend araçlarının adları.",
        json_schema_extra={"example": ["get_priority_products"]},
    )
