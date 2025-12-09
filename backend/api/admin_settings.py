from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, Dict

from backend.models.settings import Settings
from backend.models.admin import Admin
from backend.api.admin import get_current_admin

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
    product_analysis_prompt = await Settings.filter(key="product_analysis_prompt").first()

    return {
        "default_prompt": default_prompt.value if default_prompt else "",
        "product_analysis_prompt": product_analysis_prompt.value if product_analysis_prompt else ""
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
            value=data.template,
            description="Default prompt template for image generation"
        )

    return {"message": "Default prompt template updated successfully"}


@router.put("/prompts/analysis")
async def update_analysis_prompt(
    data: PromptTemplateUpdate,
    _: Admin = Depends(get_current_admin)
):
    """Обновление промпта для анализа продукта"""
    setting = await Settings.filter(key="product_analysis_prompt").first()

    if setting:
        setting.value = data.template
        await setting.save()
    else:
        await Settings.create(
            key="product_analysis_prompt",
            value=data.template,
            description="Prompt template for product analysis"
        )

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
            value=data.message,
            description="Welcome message for new users"
        )

    return {"message": "Welcome message updated successfully"}


@router.get("/all")
async def get_all_settings(_: Admin = Depends(get_current_admin)):
    """Получение всех настроек"""
    try:
        print("[GET_ALL_SETTINGS] Запрос всех настроек")
        settings = await Settings.all()
        print(f"[GET_ALL_SETTINGS] Найдено настроек: {len(settings)}")

        result = {}
        for setting in settings:
            try:
                result[setting.key] = {
                    "value": setting.value or "",
                    "description": getattr(setting, 'description', None) or ""
                }
            except Exception as e:
                print(f"[GET_ALL_SETTINGS] Ошибка при обработке настройки {setting.key}: {e}")
                result[setting.key] = {
                    "value": str(setting.value) if setting.value else "",
                    "description": ""
                }

        print(f"[GET_ALL_SETTINGS] Возвращено настроек: {len(result)}")
        return result
    except Exception as e:
        print(f"[GET_ALL_SETTINGS] Ошибка: {e}")
        import traceback
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
        if data.description:
            setting.description = data.description
        await setting.save()
        message = "Setting updated successfully"
    else:
        await Settings.create(
            key=data.key,
            value=data.value,
            description=data.description
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
