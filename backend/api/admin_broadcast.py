from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional

from backend.models.user import User
from backend.models.admin import Admin
from backend.api.admin import get_current_admin
import httpx
import os

router = APIRouter(prefix="/admin/broadcast", tags=["Admin Broadcast"])

BOT_API_URL = os.getenv("BOT_API_URL", "http://bot:8001")


class BroadcastMessage(BaseModel):
    """Схема сообщения для рассылки"""
    message: str
    target: Optional[str] = "all"  # all, active, inactive, with_referrals
    audience: Optional[str] = None  # Для совместимости со старым API


class WelcomeMessageUpdate(BaseModel):
    """Схема обновления приветственного сообщения"""
    message: str


@router.post("/send")
@router.post("/")  # Для совместимости со старым API
async def send_broadcast(
    data: BroadcastMessage,
    _: Admin = Depends(get_current_admin)
):
    """Отправка рассылки пользователям"""
    from backend.models.subscription import Subscription
    from datetime import datetime
    
    # Поддержка старого формата с audience
    target = data.target or data.audience or "all"
    
    print(f"[BROADCAST] Получен запрос на рассылку: target={target}, message_length={len(data.message)}")
    
    # Получаем пользователей по фильтру
    if target == "all":
        users = await User.all()
        print(f"[BROADCAST] Все пользователи: {len(users)}")
    elif target == "active":
        # Пользователи с активными подписками
        from backend.models import Status
        active_status = await Status.get_or_none(type="subscription", code="ACTIVE")
        if not active_status:
            users = []
            print("[BROADCAST] Статус ACTIVE не найден")
        else:
            active_subs = await Subscription.filter(
                status_id=active_status.id,
                end_date__gte=datetime.utcnow()
            ).prefetch_related("user")
            user_ids = {sub.user_id for sub in active_subs}
            users = await User.filter(id__in=list(user_ids))
            print(f"[BROADCAST] Активные пользователи: {len(users)}")
    elif target == "inactive":
        # Все пользователи минус активные
        from backend.models import Status
        all_users = await User.all()
        active_status = await Status.get_or_none(type="subscription", code="ACTIVE")
        if active_status:
            active_subs = await Subscription.filter(
                status_id=active_status.id,
                end_date__gte=datetime.utcnow()
            ).prefetch_related("user")
            active_user_ids = {sub.user_id for sub in active_subs}
            users = [u for u in all_users if u.id not in active_user_ids]
        else:
            users = list(all_users)
        print(f"[BROADCAST] Неактивные пользователи: {len(users)}")
    elif target == "with_referrals":
        users = await User.filter(referrer__isnull=False)
        print(f"[BROADCAST] Пользователи с рефералами: {len(users)}")
    else:
        users = await User.all()
        print(f"[BROADCAST] Неизвестный target, используем всех: {len(users)}")

    if not users:
        print("[BROADCAST] Нет пользователей для рассылки")
        return {
            "message": "Broadcast sent successfully",
            "total_users": 0,
            "sent_count": 0,
            "result": {"ok": True, "success_count": 0, "failed_count": 0}
        }

    # Отправляем через API бота
    try:
        user_ids = [user.tg_id for user in users]
        print(f"[BROADCAST] Отправка на {len(user_ids)} пользователей через {BOT_API_URL}/broadcast")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BOT_API_URL}/broadcast",
                json={
                    "user_ids": user_ids,
                    "message": data.message
                },
                timeout=60.0
            )
            response.raise_for_status()
            result = response.json()
            print(f"[BROADCAST] Результат: {result}")

        sent_count = result.get("success_count", len(user_ids))
        
        return {
            "message": "Broadcast sent successfully",
            "total_users": len(users),
            "sent_count": sent_count,
            "failed_count": result.get("failed_count", 0),
            "result": result
        }
    except httpx.HTTPError as e:
        print(f"[BROADCAST] HTTP ошибка: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send broadcast: {str(e)}"
        )
    except Exception as e:
        print(f"[BROADCAST] Общая ошибка: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send broadcast: {str(e)}"
        )


@router.get("/stats")
async def get_broadcast_stats(_: Admin = Depends(get_current_admin)):
    """Получение статистики для рассылки"""
    total_users = await User.all().count()
    users_with_referrals = await User.filter(referrer__isnull=False).count()

    return {
        "total_users": total_users,
        "users_with_referrals": users_with_referrals,
        "users_without_referrals": total_users - users_with_referrals
    }
