from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from backend.models.request import Request


class RequestBase(BaseModel):
    user_id: int
    tariff_id: int
    duration_id: int
    status_id: int


class RequestCreate(RequestBase):
    pass


class RequestOut(BaseModel):
    id: int
    tg_id: int
    username: Optional[str]
    full_name: Optional[str]

    tariff_code: str
    duration_months: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

    @classmethod
    def from_orm(cls, obj: 'Request') -> 'RequestOut':
        tariff = obj.tariff
        duration = obj.duration
        status = obj.status
        user = obj.user

        return cls(
            id=obj.id,
            tg_id=user.tg_id,
            username=user.username,
            full_name=user.full_name,
            tariff_code=tariff.code,
            duration_months=duration.months,
            status=status.name,
            created_at=obj.created_at,
        )
