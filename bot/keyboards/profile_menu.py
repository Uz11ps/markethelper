from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def profile_menu_kb(has_active_sub: bool = False, has_file_access: bool = False):
    """
    Клавиатура профиля пользователя
    
    Args:
        has_active_sub: Есть ли активная подписка
        has_file_access: Есть ли доступ к файлам (для складчины, не для индивидуального доступа)
    """
    buttons = [
        [InlineKeyboardButton(text="🤖 ChatGPT", callback_data="profile:chatgpt"),
         InlineKeyboardButton(text="🎨 Генерация", callback_data="profile:generate")],
    ]
    
    # Кнопка файлов показывается только если есть активная подписка И доступ к файлам (складчина)
    if has_active_sub and has_file_access:
        buttons.append([InlineKeyboardButton(text="🔑 Куки аккаунта", callback_data="profile:get_file")])
    
    buttons.extend([
        [InlineKeyboardButton(text="💳 Продлить подписку", callback_data="profile:renew")],
        [InlineKeyboardButton(text="🎁 Реферальная ссылка", callback_data="profile:referral")],
        [InlineKeyboardButton(text="📞 Связь с оператором", callback_data="profile:support")],
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)
