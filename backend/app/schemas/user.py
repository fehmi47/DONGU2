from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr = Field(..., max_length=100)


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=100)


class UserResponse(UserBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserLogin(BaseModel):
    username_or_email: str = Field(..., min_length=3, description="Kullanıcı adı veya e-posta adresi")
    password: str = Field(..., min_length=1, description="Parola")


class AuthResponse(BaseModel):
    user: UserResponse
    message: str = "Giriş başarılı"

