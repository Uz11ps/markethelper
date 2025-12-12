from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, Dict

from backend.models.settings import Settings
from backend.models.admin import Admin
from backend.api.admin import get_current_admin
from backend.services.settings_service import SettingsService

router = APIRouter(prefix="/admin/settings", tags=["Admin Settings"])


class PromptTemplateUpdate(BaseModel):
    """Схема обновления шаблона промпта"""
    template: str


class WelcomeMessageUpdate(BaseModel):
    """Схема обновления приветственного сообщения"""
    message: str


class SettingsUpdate(BaseModel):
    """Схема обновления настроек"""
    key: str
    value: str
    description: Optional[str] = None


@router.get("/prompts")
async def get_prompt_settings(_: Admin = Depends(get_current_admin)):
    """Получение настроек промптов"""
    default_prompt = await Settings.filter(key="default_prompt_template").first()
    # Используем правильный ключ prompt_generator_prompt вместо product_analysis_prompt
    prompt_generator_prompt = await SettingsService.get_prompt_generator_prompt()

    return {
        "default_prompt": default_prompt.value if default_prompt else "",
        "product_analysis_prompt": prompt_generator_prompt  # Возвращаем для совместимости с фронтендом
    }


@router.put("/prompts/default")
async def update_default_prompt(
    data: PromptTemplateUpdate,
    _: Admin = Depends(get_current_admin)
):
    """Обновление шаблона промпта по умолчанию"""
    setting = await Settings.filter(key="default_prompt_template").first()

    if setting:
        setting.value = data.template
        await setting.save()
    else:
        await Settings.create(
            key="default_prompt_template",
            value=data.template
        )

    return {"message": "Default prompt template updated successfully"}


@router.put("/prompts/analysis")
async def update_analysis_prompt(
    data: PromptTemplateUpdate,
    _: Admin = Depends(get_current_admin)
):
    """Обновление промпта для анализа продукта (генератора изображений)"""
    # Используем правильный ключ prompt_generator_prompt через SettingsService
    await SettingsService.set_prompt_generator_prompt(data.template)
    
    # Также обновляем старый ключ для совместимости (если он существует)
    old_setting = await Settings.filter(key="product_analysis_prompt").first()
    if old_setting:
        old_setting.value = data.template
        await old_setting.save()

    return {"message": "Analysis prompt template updated successfully"}


@router.get("/welcome")
async def get_welcome_message(_: Admin = Depends(get_current_admin)):
    """Получение приветственного сообщения"""
    welcome = await Settings.filter(key="welcome_message").first()

    return {
        "message": welcome.value if welcome else "Добро пожаловать!"
    }


@router.put("/welcome")
async def update_welcome_message(
    data: WelcomeMessageUpdate,
    _: Admin = Depends(get_current_admin)
):
    """Обновление приветственного сообщения"""
    setting = await Settings.filter(key="welcome_message").first()

    if setting:
        setting.value = data.message
        await setting.save()
    else:
        await Settings.create(
            key="welcome_message",
            value=data.message
        )

    return {"message": "Welcome message updated successfully"}


@router.get("/all")
async def get_all_settings(_: Admin = Depends(get_current_admin)):
    """Получение всех настроек"""
    try:
        import logging
        logger = logging.getLogger(__name__)
        logger.info("[GET_ALL_SETTINGS] Запрос всех настроек")
        
        settings = await Settings.all()
        logger.info(f"[GET_ALL_SETTINGS] Найдено настроек: {len(settings)}")

        result = {}
        for setting in settings:
            try:
                # Модель Settings не имеет поля description, используем только value
                key = getattr(setting, 'key', 'unknown')
                value = getattr(setting, 'value', '')
                
                result[key] = {
                    "value": value if value else "",
                    "description": ""  # Поле description отсутствует в модели
                }
            except Exception as e:
                logger.error(f"[GET_ALL_SETTINGS] Ошибка при обработке настройки: {e}", exc_info=True)
                # Пропускаем проблемную настройку, но продолжаем обработку остальных
                continue

        logger.info(f"[GET_ALL_SETTINGS] Возвращено настроек: {len(result)}")
        return result
    except Exception as e:
        import logging
        import traceback
        logger = logging.getLogger(__name__)
        logger.error(f"[GET_ALL_SETTINGS] Критическая ошибка: {e}", exc_info=True)
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при получении настроек: {str(e)}"
        )


@router.post("/")
async def create_or_update_setting(
    data: SettingsUpdate,
    _: Admin = Depends(get_current_admin)
):
    """Создание или обновление настройки"""
    setting = await Settings.filter(key=data.key).first()

    if setting:
        setting.value = data.value
        await setting.save()
        message = "Setting updated successfully"
    else:
        await Settings.create(
            key=data.key,
            value=data.value
        )
        message = "Setting created successfully"

    return {"message": message}


@router.delete("/{key}")
async def delete_setting(
    key: str,
    _: Admin = Depends(get_current_admin)
):
    """Удаление настройки"""
    setting = await Settings.filter(key=key).first()

    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Setting not found"
        )

    await setting.delete()
    return {"message": "Setting deleted successfully"}


class ModelUpdate(BaseModel):
    """Схема обновления модели"""
    model_id: str


class ModelCostUpdate(BaseModel):
    """Схема обновления стоимости модели"""
    cost: int


@router.get("/models")
async def get_image_models(_: Admin = Depends(get_current_admin)):
    """Получение списка доступных моделей генерации изображений"""
    models = await SettingsService.get_available_image_models()
    return models


@router.put("/models/{model_type}")
async def update_image_model(
    model_type: str,
    data: ModelUpdate,
    _: Admin = Depends(get_current_admin)
):
    """Обновление модели генерации изображений"""
    if model_type == "nano-banana":
        await SettingsService.set_image_model(data.model_id)
    elif model_type == "pro":
        await SettingsService.set_image_model_pro(data.model_id)
    elif model_type == "sd":
        await SettingsService.set_image_model_sd(data.model_id)
    else:
        raise HTTPException(status_code=400, detail="Неизвестный тип модели")
    
    return {"message": f"Модель {model_type} обновлена"}


@router.put("/models/{model_type}/cost")
async def update_image_model_cost(
    model_type: str,
    data: ModelCostUpdate,
    _: Admin = Depends(get_current_admin)
):
    """Обновление стоимости генерации для модели"""
    await SettingsService.set_image_model_cost(model_type, data.cost)
    return {"message": f"Стоимость модели {model_type} обновлена"}


class ChannelBonusUpdate(BaseModel):
    """Схема обновления бонуса за подписку на канал"""
    bonus: int


class ChannelUsernameUpdate(BaseModel):
    """Схема обновления username канала"""
    username: str


@router.get("/channel")
async def get_channel_settings(_: Admin = Depends(get_current_admin)):
    """Получение настроек канала"""
    return {
        "channel_bonus": await SettingsService.get_channel_bonus(),
        "channel_username": await SettingsService.get_channel_username(),
        "channel_id": await SettingsService.get_channel_id() or -1002089983609  # Дефолтный ID канала @lifefreelancer
    }


@router.put("/channel/bonus")
async def update_channel_bonus(
    data: ChannelBonusUpdate,
    _: Admin = Depends(get_current_admin)
):
    """Обновление размера бонуса за подписку на канал"""
    await SettingsService.set_channel_bonus(data.bonus)
    return {"message": f"Бонус за подписку на канал обновлен: {data.bonus} токенов"}


@router.put("/channel/username")
async def update_channel_username(
    data: ChannelUsernameUpdate,
    _: Admin = Depends(get_current_admin)
):
    """Обновление username канала"""
    await SettingsService.set_channel_username(data.username)
    return {"message": f"Username канала обновлен: {data.username}"}


class TokenPriceUpdate(BaseModel):
    """Схема обновления стоимости токена"""
    price: float


class TopupOptionsUpdate(BaseModel):
    """Схема обновления вариантов пополнения"""
    options: list  # [{"tokens": 100, "price": 100}, ...]


@router.get("/topup")
async def get_topup_settings(_: Admin = Depends(get_current_admin)):
    """Получение настроек пополнения баланса"""
    return {
        "token_price": await SettingsService.get_token_price(),
        "topup_options": await SettingsService.get_topup_options()
    }


@router.put("/topup/price")
async def update_token_price(
    data: TokenPriceUpdate,
    _: Admin = Depends(get_current_admin)
):
    """Обновление стоимости 1 токена"""
    await SettingsService.set_token_price(data.price)
    return {"message": f"Стоимость токена обновлена: {data.price}₽"}


@router.put("/topup/options")
async def update_topup_options(
    data: TopupOptionsUpdate,
    _: Admin = Depends(get_current_admin)
):
    """Обновление вариантов пополнения"""
    await SettingsService.set_topup_options(data.options)
    return {"message": "Варианты пополнения обновлены"}
