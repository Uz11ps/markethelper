from aiogram import Router, F
from aiogram.types import Message
from bot.keyboards.main_menu import main_menu_kb
from bot.services.api_client import APIClient
from bot.utils import get_full_name

router = Router()
api = APIClient()


@router.message(F.text == "/update_keyboard")
@router.message(F.text == "🔄 Обновить меню")
async def update_keyboard(message: Message):
    """Принудительное обновление клавиатуры"""
    tg = message.from_user
    
    try:
        profile = await api.get_profile(tg.id, username=tg.username, full_name=get_full_name(tg))
        active_until = profile.get("active_until") if profile else None
        has_active = active_until is not None
    except Exception:
        has_active = False
    
    await message.answer(
        "✅ <b>Клавиатура обновлена!</b>\n\n"
        "Теперь вы видите все доступные кнопки, включая '💰 Пополнить'.",
        reply_markup=main_menu_kb(has_active_sub=has_active)
    )

