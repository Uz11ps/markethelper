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
    
    # Новые поля
    subscription_type: Optional[str] = "group"
    group_id: Optional[int] = None
    group_name: Optional[str] = None
    user_email: Optional[str] = None

    class Config:
        from_attributes = True

    @classmethod
    async def from_orm(cls, obj: 'Request') -> 'RequestOut':
        tariff = obj.tariff
        duration = obj.duration
        status = obj.status
        user = obj.user
        
        # Получаем название группы, если есть
        group_name = None
        if hasattr(obj, 'group_id') and obj.group_id:
            from backend.models.subscription import AccessGroup
            group = await AccessGroup.get_or_none(id=obj.group_id)
            if group:
                group_name = group.name

        return cls(
            id=obj.id,
            tg_id=user.tg_id,
            username=user.username,
            full_name=user.full_name,
            tariff_code=tariff.code,
            duration_months=duration.months,
            status=status.name,
            created_at=obj.created_at,
            subscription_type=getattr(obj, 'subscription_type', 'group'),
            group_id=getattr(obj, 'group_id', None),
            group_name=group_name,
            user_email=getattr(obj, 'user_email', None),
        )
