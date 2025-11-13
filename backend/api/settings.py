from fastapi import APIRouter, HTTPException
from backend.schemas.settings import (
    SettingsUpdate, SettingsResponse,
    BroadcastCreate, BroadcastResponse,
    SubscriptionExtend, SubscriptionUpdate
)
from backend.services.settings_service import SettingsService
from backend.models import BroadcastMessage, User, Subscription
from datetime import datetime, timedelta
import httpx
import os

router = APIRouter(prefix="/admin", tags=["Admin - Settings"])


@router.get("/settings", response_model=SettingsResponse)
async def get_settings():
    """Получить текущие настройки"""
    ai_prompt = await SettingsService.get_ai_prompt()
    referral_bonus = await SettingsService.get_referral_bonus()

    return SettingsResponse(
        ai_prompt=ai_prompt,
        referral_bonus=referral_bonus
    )


@router.put("/settings")
async def update_settings(data: SettingsUpdate):
    """Обновить настройки"""
    if data.ai_prompt is not None:
        await SettingsService.set_ai_prompt(data.ai_prompt)

    if data.referral_bonus is not None:
        await SettingsService.set_referral_bonus(data.referral_bonus)

    return {"status": "success", "message": "Настройки обновлены"}


@router.post("/broadcast", response_model=BroadcastResponse)
async def create_broadcast(data: BroadcastCreate):
    """
    Создать рассылку
    audience: 'active' - пользователи с активной подпиской
              'inactive' - пользователи без активной подписки
              'all' - все пользователи
    """
    # Получаем список пользователей в зависимости от аудитории
    if data.audience == "active":
        # Пользователи с активными подписками
        subscriptions = await Subscription.filter(
            status="ACTIVE",
            end_date__gte=datetime.now()
        ).prefetch_related("user")
        users = [sub.user for sub in subscriptions]
        # Убираем дубликаты
        unique_users = {user.tg_id: user for user in users}.values()
    elif data.audience == "inactive":
        # Все пользователи
        all_users = await User.all()
        # Пользователи с активными подписками
        active_subscriptions = await Subscription.filter(
            status="ACTIVE",
            end_date__gte=datetime.now()
        ).prefetch_related("user")
        active_user_ids = {sub.user.tg_id for sub in active_subscriptions}
        # Неактивные = все - активные
        unique_users = [user for user in all_users if user.tg_id not in active_user_ids]
    else:  # all
        unique_users = await User.all()

    # Создаем запись о рассылке
    broadcast = await BroadcastMessage.create(
        message=data.message,
        audience=data.audience,
        sent_count=0
    )

    # Отправляем сообщения через бот
    sent_count = 0
    bot_url = os.getenv("BACKEND_URL", "http://bot:8001").replace("backend:8000", "bot:8001")

    async with httpx.AsyncClient() as client:
        for user in unique_users:
            try:
                await client.post(
                    f"{bot_url}/broadcast",
                    json={
                        "tg_id": user.tg_id,
                        "message": data.message
                    },
                    timeout=5.0
                )
                sent_count += 1
            except Exception as e:
                print(f"Failed to send message to {user.tg_id}: {e}")

    # Обновляем количество отправленных
    broadcast.sent_count = sent_count
    await broadcast.save()

    return BroadcastResponse(
        id=broadcast.id,
        message=broadcast.message,
        audience=broadcast.audience,
        sent_count=broadcast.sent_count,
        created_at=broadcast.created_at
    )


@router.get("/broadcast/history")
async def get_broadcast_history():
    """Получить историю рассылок"""
    broadcasts = await BroadcastMessage.all().order_by("-created_at").limit(50)
    return [
        BroadcastResponse(
            id=b.id,
            message=b.message,
            audience=b.audience,
            sent_count=b.sent_count,
            created_at=b.created_at
        )
        for b in broadcasts
    ]


@router.post("/subscriptions/{subscription_id}/extend")
async def extend_subscription(subscription_id: int, data: SubscriptionExtend):
    """Продлить подписку на указанное количество дней"""
    subscription = await Subscription.filter(id=subscription_id).first()

    if not subscription:
        raise HTTPException(status_code=404, detail="Подписка не найдена")

    # Если подписка уже истекла, продлеваем от текущей даты
    if subscription.end_date < datetime.now():
        subscription.end_date = datetime.now() + timedelta(days=data.days)
    else:
        # Иначе продлеваем от текущей даты окончания
        subscription.end_date = subscription.end_date + timedelta(days=data.days)

    subscription.status = "ACTIVE"
    await subscription.save()

    return {
        "status": "success",
        "message": f"Подписка продлена на {data.days} дней",
        "new_end_date": subscription.end_date.isoformat()
    }


@router.delete("/subscriptions/{subscription_id}")
async def revoke_subscription(subscription_id: int):
    """Отозвать подписку (установить статус INACTIVE и дату окончания на текущую)"""
    subscription = await Subscription.filter(id=subscription_id).first()

    if not subscription:
        raise HTTPException(status_code=404, detail="Подписка не найдена")

    subscription.status = "INACTIVE"
    subscription.end_date = datetime.now()
    await subscription.save()

    return {
        "status": "success",
        "message": "Подписка отозвана"
    }


@router.patch("/subscriptions/{subscription_id}")
async def update_subscription(subscription_id: int, data: SubscriptionUpdate):
    """Обновить подписку"""
    subscription = await Subscription.filter(id=subscription_id).first()

    if not subscription:
        raise HTTPException(status_code=404, detail="Подписка не найдена")

    if data.status is not None:
        subscription.status = data.status

    if data.end_date is not None:
        subscription.end_date = data.end_date

    await subscription.save()

    return {
        "status": "success",
        "message": "Подписка обновлена"
    }
