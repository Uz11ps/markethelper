from pydantic import BaseModel
from datetime import datetime


class ReferralOut(BaseModel):
    id: int
    referrer_id: int
    referrer_username: str | None
    referred_id: int
    referred_username: str | None
    activated: bool
    reward_given: bool
    created_at: datetime

    class Config:
        from_attributes = True
