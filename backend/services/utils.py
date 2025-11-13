import httpx
from backend.models import Status
import os
import requests
from http.cookiejar import MozillaCookieJar
from requests.cookies import create_cookie
from backend.models import AccessFile
from datetime import datetime, timedelta
from fastapi import HTTPException

BOT_URL = "http://bot:8001/notify"  # адрес API бота в docker-compose

async def notify_user(tg_id: int, message: str, has_active_sub: bool = False):
    """
    Отправка уведомления боту
    """
    async with httpx.AsyncClient() as client:
        try:
            await client.post(
                BOT_URL,
                json={
                    "tg_id": tg_id,
                    "message": message,
                    "has_active_sub": has_active_sub
                }
            )
        except Exception as e:
            print(f"⚠ Ошибка при отправке уведомления: {e}")


async def get_status(type: str, code: str):
    """
    Получение или создание статуса
    """
    status = await Status.get_or_none(type=type, code=code)
    if not status:
        status = await Status.create(type=type, code=code, name=code.capitalize())
    return status
