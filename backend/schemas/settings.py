from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class SettingsUpdate(BaseModel):
    ai_prompt: Optional[str] = None
    prompt_generator_prompt: Optional[str] = None
    referral_bonus: Optional[int] = None
    image_generation_cost: Optional[int] = None
    gpt_request_cost: Optional[int] = None


class SettingsResponse(BaseModel):
    ai_prompt: str
    referral_bonus: int
    prompt_generator_prompt: str
    image_generation_cost: int
    gpt_request_cost: int


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
