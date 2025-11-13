from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def chatgpt_kb():

    kb = [
        [KeyboardButton(text="🚪 Выйти")]
    ]

    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)