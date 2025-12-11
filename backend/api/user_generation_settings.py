from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.models.user import User
from backend.models.user_generation_settings import UserGenerationSettings
from backend.services.settings_service import SettingsService
import logging

router = APIRouter(prefix="/users/{tg_id}/generation-settings", tags=["User Generation Settings"])
logger = logging.getLogger(__name__)


class GenerationSettingsUpdate(BaseModel):
    selected_model_key: str | None = None
    selected_gpt_model: str | None = None
    custom_prompt: str | None = None


@router.get("")
async def get_user_generation_settings(tg_id: int):
    """Получить настройки генерации пользователя"""
    user = await User.get_or_none(tg_id=tg_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    settings = await UserGenerationSettings.get_or_none(user=user)
    
    # Получаем доступные модели из админки
    try:
        image_models = await SettingsService.get_image_models()
    except Exception as e:
        logger.warning(f"Не удалось получить модели из настроек: {e}")
        image_models = {}
    
    # Получаем системный промпт
    try:
        system_prompt = await SettingsService.get_prompt_generator_prompt()
    except Exception as e:
        logger.warning(f"Не удалось получить системный промпт: {e}")
        system_prompt = None
    
    return {
        "selected_model_key": settings.selected_model_key if settings else None,
        "selected_gpt_model": settings.selected_gpt_model if settings else None,
        "custom_prompt": settings.custom_prompt if settings else None,
        "available_models": image_models,
        "system_prompt": system_prompt,
    }


@router.put("")
async def update_user_generation_settings(tg_id: int, data: GenerationSettingsUpdate):
    """Обновить настройки генерации пользователя"""
    user = await User.get_or_none(tg_id=tg_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Проверяем что модель существует
    if data.selected_model_key:
        try:
            image_models = await SettingsService.get_image_models()
            if data.selected_model_key not in image_models:
                raise HTTPException(status_code=400, detail=f"Model {data.selected_model_key} not found")
        except Exception as e:
            logger.warning(f"Ошибка проверки модели: {e}")
            raise HTTPException(status_code=400, detail=f"Invalid model key: {e}")
    
    settings, created = await UserGenerationSettings.get_or_create(
        user=user,
        defaults={
            "selected_model_key": data.selected_model_key,
            "selected_gpt_model": data.selected_gpt_model,
            "custom_prompt": data.custom_prompt,
        }
    )
    
    if not created:
        if data.selected_model_key is not None:
            settings.selected_model_key = data.selected_model_key
        if data.selected_gpt_model is not None:
            settings.selected_gpt_model = data.selected_gpt_model
        if data.custom_prompt is not None:
            settings.custom_prompt = data.custom_prompt
        await settings.save()
    
    return {
        "status": "success",
        "message": "Settings updated",
        "selected_model_key": settings.selected_model_key,
        "selected_gpt_model": settings.selected_gpt_model,
        "custom_prompt": settings.custom_prompt,
    }

