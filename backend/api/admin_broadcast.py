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
    target: Optional[str] = "all"  # all, active, with_referrals


class WelcomeMessageUpdate(BaseModel):
    """Схема обновления приветственного сообщения"""
    message: str


@router.post("/send")
async def send_broadcast(
    data: BroadcastMessage,
    _: Admin = Depends(get_current_admin)
):
    """Отправка рассылки пользователям"""
    # Получаем пользователей по фильтру
    if data.target == "all":
        users = await User.all()
    elif data.target == "with_referrals":
        users = await User.filter(referrer__isnull=False)
    else:
        users = await User.all()

    # Отправляем через API бота
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BOT_API_URL}/broadcast",
                json={
                    "user_ids": [user.tg_id for user in users],
                    "message": data.message
                },
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()

        return {
            "message": "Broadcast sent successfully",
            "total_users": len(users),
            "result": result
        }
    except Exception as e:
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
