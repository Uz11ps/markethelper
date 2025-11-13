from datetime import datetime
from pydantic import BaseModel
from typing import Optional

class UserBase(BaseModel):
    tg_id: int
    username: Optional[str] = None
    full_name: Optional[str] = None
    bonus_balance: int = 0
    referrer_id: Optional[int] = None

class UserCreate(BaseModel):
    tg_id: int
    username: str | None = None
    full_name: str | None = None

class UserUpdate(BaseModel):
    username: Optional[str] = None
    full_name: Optional[str] = None
    bonus_balance: Optional[int] = None
    referrer_id: Optional[int] = None


class UserOut(UserBase):
    id: int

    class Config:
        from_attributes = True


# Алиас для админки
UserResponse = UserOut


class ReferralBase(BaseModel):
    referrer_id: int
    referred_id: int
    activated: bool = False
    reward_given: bool = False


class ReferralCreate(ReferralBase):
    pass


class ReferralOut(ReferralBase):
    id: int

    class Config:
        from_attributes = True

class ProfileOut(BaseModel):
    user_id: int
    tg_id: int
    username: Optional[str]
    full_name: Optional[str]

    tariff_code: Optional[str]
    tariff_name: Optional[str]
    active_until: Optional[datetime]

    access_group: Optional[str]       
    access_file_path: Optional[str]  

    bonus_balance: int = 0

    class Config:
        from_attributes = True