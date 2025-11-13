from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AccessGroupBase(BaseModel):
    name: str


class AccessGroupCreate(AccessGroupBase):
    pass


class AccessGroupOut(AccessGroupBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class SubscriptionBase(BaseModel):
    user_id: int
    tariff_id: int
    status_id: int
    group_id: Optional[int]
    start_date: Optional[datetime]
    end_date: datetime


class SubscriptionCreate(SubscriptionBase):
    pass


class SubscriptionOut(SubscriptionBase):
    id: int

    class Config:
        from_attributes = True
