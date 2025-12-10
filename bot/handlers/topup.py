from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from bot.services.api_client import APIClient
from bot.utils import get_full_name
import logging

router = Router()
api = APIClient()
logger = logging.getLogger(__name__)

# Варианты пополнения (токены: стоимость в рублях)
TOPUP_OPTIONS = [
    {"tokens": 100, "price": 100, "label": "100 токенов - 100₽"},
    {"tokens": 250, "price": 225, "label": "250 токенов - 225₽ (скидка 10%)"},
    {"tokens": 500, "price": 400, "label": "500 токенов - 400₽ (скидка 20%)"},
    {"tokens": 1000, "price": 700, "label": "1000 токенов - 700₽ (скидка 30%)"},
]


def topup_amounts_kb():
    """Клавиатура выбора суммы пополнения"""
    buttons = []
    for option in TOPUP_OPTIONS:
        buttons.append([
            InlineKeyboardButton(
                text=option["label"],
                callback_data=f"topup:{option['tokens']}:{option['price']}"
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
    
    text = (
        "💰 <b>Пополнение баланса</b>\n\n"
        f"💼 Ваш текущий баланс: <b>{balance} токенов</b>\n\n"
        "Выберите сумму пополнения:\n\n"
    )
    
    for option in TOPUP_OPTIONS:
        text += f"• {option['label']}\n"
    
    text += "\nПосле выбора суммы с вами свяжется администратор для подтверждения оплаты."
    
    await message.answer(text, reply_markup=topup_amounts_kb())


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

