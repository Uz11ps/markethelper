from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def profile_menu_kb(has_active_sub: bool = False, is_group_subscription: bool = False):
    """
    Клавиатура профиля пользователя
    
    Args:
        has_active_sub: Есть ли активная подписка
        is_group_subscription: Является ли подписка тарифом "Складчина" (GROUP)
    """
    buttons = [
        [InlineKeyboardButton(text="🤖 ChatGPT", callback_data="profile:chatgpt"),
         InlineKeyboardButton(text="🎨 Генерация", callback_data="profile:generate")],
    ]
    
    # Кнопка "Куки аккаунта" показывается только для тарифа "Складчина"
    if has_active_sub and is_group_subscription:
        buttons.append([InlineKeyboardButton(text="🔑 Куки аккаунта", callback_data="profile:get_file")])
    
    buttons.extend([
        [InlineKeyboardButton(text="💰 Пополнить баланс", callback_data="profile:topup")],
        [InlineKeyboardButton(text="💳 Продлить подписку", callback_data="profile:renew")],
        [InlineKeyboardButton(text="🎁 Реферальная ссылка", callback_data="profile:referral")],
        [InlineKeyboardButton(text="📞 Связь с оператором", callback_data="profile:support")],
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)
