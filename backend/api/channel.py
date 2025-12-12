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


@router.get("/has-pending-request/{tg_id}")
async def has_pending_channel_bonus_request(tg_id: int):
    """Проверить, есть ли pending запрос на бонус за подписку на канал для пользователя"""
    user = await User.get_or_none(tg_id=tg_id)
    if not user:
        return {"has_pending": False}
    
    # Проверяем наличие pending запроса
    pending_request = await ChannelBonusRequest.filter(
        user=user,
        status="pending"
    ).first()
    
    return {"has_pending": pending_request is not None}


@router.post("/mark-message-shown/{tg_id}")
async def mark_channel_subscription_message_shown(tg_id: int):
    """Отметить, что сообщение о подписке на канал было показано пользователю"""
    user = await User.get_or_none(tg_id=tg_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.channel_subscription_message_shown = True
    await user.save(update_fields=['channel_subscription_message_shown'])
    
    return {"message": "Message marked as shown"}


@router.get("/prompt-generator")
async def get_prompt_generator_public():
    """Получение промпта генератора изображений (публичный endpoint для бота)"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        prompt = await SettingsService.get_prompt_generator_prompt()
        logger.info(f"[get_prompt_generator_public] Загружен промпт из БД (длина: {len(prompt)} символов, первые 200 символов: {prompt[:200]}...)")
        
        if not prompt or not prompt.strip():
            logger.warning("[get_prompt_generator_public] Промпт пустой или отсутствует в БД!")
            # Возвращаем дефолтный промпт, если в БД пусто
            prompt = SettingsService.DEFAULT_PROMPT_GENERATOR_PROMPT
            logger.warning("[get_prompt_generator_public] Используется дефолтный промпт из кода")
        
        return {
            "prompt_generator_prompt": prompt
        }
    except Exception as e:
        logger.error(f"[get_prompt_generator_public] Ошибка при загрузке промпта: {e}", exc_info=True)
        # В случае ошибки возвращаем дефолтный промпт
        prompt = SettingsService.DEFAULT_PROMPT_GENERATOR_PROMPT
        logger.warning("[get_prompt_generator_public] Используется дефолтный промпт из кода из-за ошибки")
        return {
            "prompt_generator_prompt": prompt
        }


@router.post("/check-subscription/{tg_id}")
async def check_channel_subscription(tg_id: int):
    """
    Проверка подписки пользователя на канал и создание запроса на бонус.
    Вызывается из бота после проверки подписки через Telegram API.
    """
    try:
        logger.info(f"[check_channel_subscription] Начало обработки для tg_id={tg_id}")
        
        user = await User.get_or_none(tg_id=tg_id)
        if not user:
            logger.error(f"[check_channel_subscription] Пользователь не найден: tg_id={tg_id}")
            raise HTTPException(status_code=404, detail="User not found")
        
        logger.info(f"[check_channel_subscription] Пользователь найден: id={user.id}, tg_id={user.tg_id}")
        
        # Если бонус уже был начислен, ничего не делаем
        if user.channel_bonus_given:
            logger.info(f"[check_channel_subscription] Бонус уже был начислен для пользователя {tg_id}")
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
            logger.info(f"[check_channel_subscription] Уже есть pending запрос для пользователя {tg_id}")
            return {
                "subscribed": True,
                "request_already_exists": True,
                "message": "Запрос на бонус за подписку уже отправлен и ожидает одобрения"
            }
        
        # Получаем размер бонуса из настроек
        try:
            bonus_amount = await SettingsService.get_channel_bonus()
            logger.info(f"[check_channel_subscription] Размер бонуса из настроек: {bonus_amount}")
        except Exception as e:
            logger.error(f"[check_channel_subscription] Ошибка при получении размера бонуса: {e}")
            import traceback
            traceback.print_exc()
            bonus_amount = 50  # Дефолтное значение
        
        # Создаем запрос на бонус (требует одобрения админа)
        try:
            logger.info(f"[check_channel_subscription] Создание запроса на бонус: user_id={user.id}, bonus_amount={bonus_amount}")
            bonus_request = await ChannelBonusRequest.create(
                user=user,
                bonus_amount=bonus_amount,
                status="pending"
            )
            logger.info(f"[check_channel_subscription] Запрос на бонус успешно создан: id={bonus_request.id}")
        except Exception as e:
            logger.error(f"[check_channel_subscription] Ошибка при создании запроса на бонус: {e}")
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Ошибка при создании запроса на бонус: {str(e)}")
        
        logger.info(f"[check_channel_subscription] Успешно создан запрос на бонус для пользователя {tg_id}: {bonus_amount} токенов")
        
        return {
            "subscribed": True,
            "request_created": True,
            "bonus_amount": bonus_amount,
            "message": f"✅ Запрос на {bonus_amount} токенов за подписку на канал отправлен администратору. Бонус будет начислен после одобрения."
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[check_channel_subscription] Неожиданная ошибка: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")

