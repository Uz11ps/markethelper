from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def main_menu_kb(has_active_sub: bool):
    # Временно для тестирования - всегда показываем профиль
    kb = [
        [KeyboardButton(text="👤Профиль")],
        [KeyboardButton(text="💰 Пополнить")],
        [KeyboardButton(text="❓FAQ")],
    ]

    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
