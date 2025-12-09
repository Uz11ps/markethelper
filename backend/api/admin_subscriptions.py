from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from datetime import datetime, timedelta

from backend.models.subscription import Subscription
from backend.models.admin import Admin
from backend.api.admin import get_current_admin

router = APIRouter(prefix="/admin/subscriptions", tags=["Admin Subscriptions"])


class SubscriptionExtend(BaseModel):
    days: int


@router.post("/{subscription_id}/extend")
async def extend_subscription(
    subscription_id: int,
    data: SubscriptionExtend,
    admin: Admin = Depends(get_current_admin)
):
    """Продлить подписку на указанное количество дней"""
    print(f"[EXTEND_SUBSCRIPTION] Продление подписки {subscription_id} на {data.days} дней")
    
    subscription = await Subscription.filter(id=subscription_id).prefetch_related("user").first()

    if not subscription:
        print(f"[EXTEND_SUBSCRIPTION] Подписка {subscription_id} не найдена")
        raise HTTPException(status_code=404, detail="Подписка не найдена")

    # Получаем статус ACTIVE
    from backend.models import Status
    active_status = await Status.get_or_none(type="subscription", code="ACTIVE")
    if not active_status:
        active_status = await Status.create(type="subscription", code="ACTIVE", name="Активна")

    # Если подписка уже истекла, продлеваем от текущей даты
    now = datetime.utcnow()
    if subscription.end_date and subscription.end_date < now:
        subscription.end_date = now + timedelta(days=data.days)
        print(f"[EXTEND_SUBSCRIPTION] Подписка истекла, продлеваем от текущей даты до {subscription.end_date}")
    else:
        # Иначе продлеваем от текущей даты окончания или от текущей даты
        end_date = subscription.end_date if subscription.end_date else now
        subscription.end_date = end_date + timedelta(days=data.days)
        print(f"[EXTEND_SUBSCRIPTION] Продлеваем от {end_date} до {subscription.end_date}")

    subscription.status = active_status
    await subscription.save()

    return {
        "status": "success",
        "message": f"Подписка продлена на {data.days} дней",
        "new_end_date": subscription.end_date.isoformat(),
        "subscription_id": subscription_id
    }


@router.delete("/{subscription_id}")
async def revoke_subscription(
    subscription_id: int,
    admin: Admin = Depends(get_current_admin)
):
    """Отозвать подписку (установить статус EXPIRED и дату окончания на текущую)"""
    print(f"[REVOKE_SUBSCRIPTION] Отзыв подписки {subscription_id}")
    
    subscription = await Subscription.filter(id=subscription_id).first()
    
    if not subscription:
        raise HTTPException(status_code=404, detail="Подписка не найдена")

    # Получаем статус EXPIRED
    from backend.models import Status
    expired_status = await Status.get_or_none(type="subscription", code="EXPIRED")
    if not expired_status:
        expired_status = await Status.create(type="subscription", code="EXPIRED", name="Истекла")

    subscription.status = expired_status
    subscription.end_date = datetime.utcnow()
    await subscription.save()

    return {
        "status": "success",
        "message": "Подписка отозвана",
        "subscription_id": subscription_id
    }

