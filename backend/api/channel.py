from fastapi import APIRouter, HTTPException
from backend.models.user import User
from backend.services.settings_service import SettingsService
import logging

router = APIRouter(prefix="/channel", tags=["Channel"])

logger = logging.getLogger(__name__)


@router.post("/check-subscription/{tg_id}")
async def check_channel_subscription(tg_id: int):
    """
    Проверка подписки пользователя на канал и начисление бонуса при необходимости.
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
    
    # Получаем размер бонуса из настроек
    bonus_amount = await SettingsService.get_channel_bonus()
    
    # Начисляем бонус
    user.bonus_balance += bonus_amount
    user.channel_bonus_given = True
    await user.save()
    
    logger.info(f"Начислен бонус за подписку на канал пользователю {tg_id}: +{bonus_amount} токенов")
    
    return {
        "subscribed": True,
        "bonus_given": True,
        "bonus_amount": bonus_amount,
        "new_balance": user.bonus_balance,
        "message": f"🎉 Вам начислено {bonus_amount} токенов за подписку на канал!"
    }

