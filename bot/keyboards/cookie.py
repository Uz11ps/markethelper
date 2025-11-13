from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def file_actions_kb(file_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Обновить куки", callback_data=f"file:update:{file_id}")],
    ])
