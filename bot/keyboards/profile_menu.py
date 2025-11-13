from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def profile_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤖 ChatGPT", callback_data="profile:chatgpt"),
         InlineKeyboardButton(text="🎨 Генерация", callback_data="profile:generate")],
        [InlineKeyboardButton(text="🔑 Куки аккаунта", callback_data="profile:get_file")],
        [InlineKeyboardButton(text="💳 Продлить подписку", callback_data="profile:renew")],
        [InlineKeyboardButton(text="🎁 Реферальная ссылка", callback_data="profile:referral")],
        [InlineKeyboardButton(text="📞 Связь с оператором", callback_data="profile:support")],
    ])
