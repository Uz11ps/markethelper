from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from bot.services.api_client import APIClient
from bot.utils import get_full_name
import logging

router = Router()
api = APIClient()
logger = logging.getLogger(__name__)

def format_topup_label(tokens: int, price: float) -> str:
    """Форматирует метку для варианта пополнения"""
    discount = ""
    if tokens >= 1000:
        discount = " (скидка 30%)"
    elif tokens >= 500:
        discount = " (скидка 20%)"
    elif tokens >= 250:
        discount = " (скидка 10%)"
    return f"{tokens} токенов - {price:.0f}₽{discount}"


def topup_amounts_kb(options: list):
    """Создает клавиатуру с вариантами пополнения"""
    buttons = []
    for option in options:
        tokens = option.get("tokens", 0)
        price = option.get("price", 0)
        label = format_topup_label(tokens, price)
        buttons.append([
            InlineKeyboardButton(
                text=label,
                callback_data=f"topup:{tokens}:{price}"
            )
        ])
    buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data="topup:cancel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(F.text == "💰 Пополнить")
async def show_topup_menu(message: Message):
    """Показать меню пополнения баланса"""
    tg = message.from_user
    
    try:
        profile = await api.get_profile(tg.id, username=tg.username, full_name=get_full_name(tg))
        balance = profile.get("bonus_balance", 0) if profile else 0
    except Exception as e:
        logger.error(f"Ошибка получения профиля: {e}")
        balance = 0
    
    # Получаем настройки пополнения из базы данных
    try:
        topup_settings = await api.get_topup_settings()
        topup_options = topup_settings.get("topup_options", [])
        token_price = topup_settings.get("token_price", 1.0)
    except Exception as e:
        logger.error(f"Ошибка получения настроек пополнения: {e}")
        # Используем значения по умолчанию
        topup_options = [
            {"tokens": 100, "price": 100},
            {"tokens": 250, "price": 225},
            {"tokens": 500, "price": 400},
            {"tokens": 1000, "price": 700},
        ]
        token_price = 1.0
    
    text = (
        "💰 <b>Пополнение баланса</b>\n\n"
        f"💼 Ваш текущий баланс: <b>{balance} токенов</b>\n"
        f"💵 Стоимость 1 токена: <b>{token_price:.2f}₽</b>\n\n"
        "Выберите сумму для пополнения:"
    )
    
    await message.answer(text, reply_markup=topup_amounts_kb(topup_options))


@router.callback_query(F.data.startswith("topup:"))
async def handle_topup_choice(callback: CallbackQuery):
    """Обработка выбора суммы пополнения"""
    await callback.answer()
    
    if callback.data == "topup:cancel":
        await callback.message.edit_text("❌ Пополнение отменено")
        return
    
    try:
        _, tokens_str, price_str = callback.data.split(":")
        tokens = int(tokens_str)
        price = float(price_str)
    except ValueError:
        await callback.message.edit_text("❌ Ошибка: неверный формат данных")
        return
    
    tg = callback.from_user
    
    try:
        # Создаем заявку на пополнение через API
        result = await api.create_token_purchase_request(
            tg_id=tg.id,
            amount=tokens,
            cost=price
        )
        
        await callback.message.edit_text(
            f"✅ <b>Заявка на пополнение создана!</b>\n\n"
            f"💰 Сумма: <b>{tokens} токенов</b>\n"
            f"💵 Стоимость: <b>{price}₽</b>\n\n"
            f"📋 Номер заявки: <b>#{result.get('id', 'N/A')}</b>\n\n"
            "⏳ Ожидайте подтверждения администратора. "
            "После подтверждения оплаты токены будут начислены на ваш баланс."
        )
    except Exception as e:
        logger.error(f"Ошибка создания заявки на пополнение: {e}")
        await callback.message.edit_text(
            f"❌ Ошибка при создании заявки: {str(e)}\n\n"
            "Попробуйте позже или обратитесь к администратору."
        )

