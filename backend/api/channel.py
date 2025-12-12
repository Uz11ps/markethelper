from fastapi import APIRouter, HTTPException
from backend.models.user import User
from backend.models.channel_bonus import ChannelBonusRequest
from backend.services.settings_service import SettingsService
import logging

router = APIRouter(prefix="/channel", tags=["Channel"])

logger = logging.getLogger(__name__)


@router.get("/settings")
async def get_channel_settings_public():
    """Получение настроек канала (публичный endpoint для бота)"""
    return {
        "channel_bonus": await SettingsService.get_channel_bonus(),
        "channel_username": await SettingsService.get_channel_username(),
        "channel_id": await SettingsService.get_channel_id() or -1002089983609  # Дефолтный ID канала @lifefreelancer
    }


@router.post("/check-subscription/{tg_id}")
async def check_channel_subscription(tg_id: int):
    """
    Проверка подписки пользователя на канал и создание запроса на бонус.
    Вызывается из бота после проверки подписки через Telegram API.
    """
    user = await User.get_or_none(tg_id=tg_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Если бонус уже был начислен, ничего не делаем
    if user.channel_bonus_given:
        return {
            "subscribed": True,
            "bonus_already_given": True,
            "message": "Бонус за подписку уже был начислен ранее"
        }
    
    # Проверяем, есть ли уже pending запрос
    existing_request = await ChannelBonusRequest.filter(
        user=user,
        status="pending"
    ).first()
    
    if existing_request:
        return {
            "subscribed": True,
            "request_already_exists": True,
            "message": "Запрос на бонус за подписку уже отправлен и ожидает одобрения"
        }
    
    # Получаем размер бонуса из настроек
    bonus_amount = await SettingsService.get_channel_bonus()
    
    # Создаем запрос на бонус (требует одобрения админа)
    await ChannelBonusRequest.create(
        user=user,
        bonus_amount=bonus_amount,
        status="pending"
    )
    
    logger.info(f"Создан запрос на бонус за подписку на канал для пользователя {tg_id}: {bonus_amount} токенов")
    
    return {
        "subscribed": True,
        "request_created": True,
        "bonus_amount": bonus_amount,
        "message": f"✅ Запрос на {bonus_amount} токенов за подписку на канал отправлен администратору. Бонус будет начислен после одобрения."
    }

