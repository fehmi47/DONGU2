from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class NotificationBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=150)
    message: str
    notification_type: str = Field(..., min_length=1, max_length=30)
    product_id: Optional[int] = None


class NotificationCreate(NotificationBase):
    user_id: int


class NotificationResponse(NotificationBase):
    id: int
    user_id: int
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
