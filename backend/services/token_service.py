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
        user = await User.get_or_none(tg_id=tg_id)
        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")

        cost = await cls.get_cost_for_action(action)

        if cost < 0:
            raise HTTPException(status_code=400, detail="Стоимость действия не может быть отрицательной")

        if cost == 0:
            return {
                "action": action,
                "cost": 0,
                "balance": user.bonus_balance,
                "label": cls.ACTION_LABELS.get(action, action)
            }

        if user.bonus_balance < cost:
            raise HTTPException(status_code=402, detail="Недостаточно токенов")

        user.bonus_balance -= cost
        await user.save()

        return {
            "action": action,
            "cost": cost,
            "balance": user.bonus_balance,
            "label": cls.ACTION_LABELS.get(action, action)
        }

    @classmethod
    async def get_pricing(cls) -> dict:
        return await SettingsService.get_token_costs()
