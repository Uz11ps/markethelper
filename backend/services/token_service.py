from fastapi import HTTPException
from backend.models import User
from backend.services.settings_service import SettingsService


class TokenService:
    """Сервис для списания токенов за различные действия"""

    ACTION_IMAGE_GENERATION = "image_generation"
    ACTION_GPT = "ai_chat"

    ACTION_LABELS = {
        ACTION_IMAGE_GENERATION: "генерацию изображения",
        ACTION_GPT: "запрос к GPT"
    }

    @classmethod
    async def get_cost_for_action(cls, action: str) -> int:
        if action == cls.ACTION_IMAGE_GENERATION:
            return await SettingsService.get_image_generation_cost()
        if action == cls.ACTION_GPT:
            return await SettingsService.get_gpt_request_cost()
        raise HTTPException(status_code=400, detail="Неизвестный тип действия для списания токенов")

    @classmethod
    async def charge(cls, tg_id: int, action: str) -> dict:
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            logger.info(f"[TokenService.charge] Списание токенов для tg_id={tg_id}, action={action}")
            
            user = await User.get_or_none(tg_id=tg_id)
            if not user:
                logger.error(f"[TokenService.charge] Пользователь не найден: tg_id={tg_id}")
                raise HTTPException(status_code=404, detail="Пользователь не найден")

            logger.debug(f"[TokenService.charge] Пользователь найден: id={user.id}, balance={user.bonus_balance}")
            
            cost = await cls.get_cost_for_action(action)
            logger.debug(f"[TokenService.charge] Стоимость действия: {cost}")

            if cost < 0:
                logger.error(f"[TokenService.charge] Отрицательная стоимость: {cost}")
                raise HTTPException(status_code=400, detail="Стоимость действия не может быть отрицательной")

            if cost == 0:
                logger.info(f"[TokenService.charge] Стоимость равна 0, списание не требуется")
                return {
                    "action": action,
                    "cost": 0,
                    "balance": user.bonus_balance,
                    "label": cls.ACTION_LABELS.get(action, action)
                }

            if user.bonus_balance < cost:
                logger.warning(f"[TokenService.charge] Недостаточно токенов: balance={user.bonus_balance}, cost={cost}")
                raise HTTPException(status_code=402, detail="Недостаточно токенов")

            old_balance = user.bonus_balance
            user.bonus_balance -= cost
            await user.save()
            
            logger.info(f"[TokenService.charge] Токены списаны: balance {old_balance} -> {user.bonus_balance}, cost={cost}")

            return {
                "action": action,
                "cost": cost,
                "balance": user.bonus_balance,
                "label": cls.ACTION_LABELS.get(action, action)
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[TokenService.charge] Неожиданная ошибка при списании токенов: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Ошибка при списании токенов: {str(e)}")

    @classmethod
    async def get_pricing(cls) -> dict:
        return await SettingsService.get_token_costs()
