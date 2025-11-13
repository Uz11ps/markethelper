from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class SettingsUpdate(BaseModel):
    ai_prompt: Optional[str] = None
    referral_bonus: Optional[int] = None


class SettingsResponse(BaseModel):
    ai_prompt: str
    referral_bonus: int


class BroadcastCreate(BaseModel):
    message: str
    audience: str  # 'active', 'inactive', 'all'


class BroadcastResponse(BaseModel):
    id: int
    message: str
    audience: str
    sent_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class SubscriptionExtend(BaseModel):
    days: int  # количество дней для продления


class SubscriptionUpdate(BaseModel):
    status: Optional[str] = None
    end_date: Optional[datetime] = None
