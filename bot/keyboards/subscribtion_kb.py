from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def tariffs_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Индивидуальный", callback_data="tariff:INDIVIDUAL")],
        [InlineKeyboardButton(text="Складчина", callback_data="tariff:GROUP")],
    ])


def durations_kb(tariff_code: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="1 месяц", callback_data=f"duration:{tariff_code}:1")],
        [InlineKeyboardButton(text="3 месяца", callback_data=f"duration:{tariff_code}:3")],
        [InlineKeyboardButton(text="6 месяцев", callback_data=f"duration:{tariff_code}:6")],
    ])
