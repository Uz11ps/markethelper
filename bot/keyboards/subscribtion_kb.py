from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Optional


def subscription_type_kb():
    """Клавиатура выбора типа подписки"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📦 Складчина", callback_data="sub_type:group")],
        [InlineKeyboardButton(text="👤 Индивидуальный доступ", callback_data="sub_type:individual")],
    ])


def tariffs_kb():
    """Клавиатура выбора тарифа (для совместимости со старым кодом)"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Индивидуальный", callback_data="tariff:INDIVIDUAL")],
        [InlineKeyboardButton(text="Складчина", callback_data="tariff:GROUP")],
    ])


def durations_kb(tariff_code: str, subscription_type: str = "group"):
    """Клавиатура выбора длительности подписки"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="1 месяц", callback_data=f"duration:{tariff_code}:{subscription_type}:1")],
        [InlineKeyboardButton(text="3 месяца", callback_data=f"duration:{tariff_code}:{subscription_type}:3")],
        [InlineKeyboardButton(text="6 месяцев", callback_data=f"duration:{tariff_code}:{subscription_type}:6")],
    ])


def groups_kb(groups: List[dict], tariff_code: str, months: int):
    """Клавиатура выбора группы файлов для складчины"""
    buttons = []
    for group in groups:
        buttons.append([InlineKeyboardButton(
            text=f"📁 {group['name']}",
            callback_data=f"group:{group['id']}:{tariff_code}:{months}"
        )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def email_request_kb(tariff_code: str, months: int):
    """Клавиатура для запроса email или пропуска шага"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📧 Указать email", callback_data=f"email_input:{tariff_code}:{months}")],
        [InlineKeyboardButton(text="⏭ Пропустить", callback_data=f"email_skip:{tariff_code}:{months}")],
    ])
