from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


class AdminCreate(BaseModel):
    """Схема создания администратора"""
    username: str
    password: str
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    is_super_admin: bool = False


class AdminLogin(BaseModel):
    """Схема для входа"""
    username: str
    password: str


class AdminResponse(BaseModel):
    """Схема ответа с данными администратора"""
    id: int
    username: str
    full_name: Optional[str]
    email: Optional[str]
    is_active: bool
    is_super_admin: bool
    created_at: datetime
    last_login: Optional[datetime]

    class Config:
        from_attributes = True


class AdminUpdate(BaseModel):
    """Схема обновления администратора"""
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None


class Token(BaseModel):
    """JWT токен"""
    access_token: str
    token_type: str = "bearer"
