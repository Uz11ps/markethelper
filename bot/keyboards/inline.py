from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def generation_keyboard():
    """Клавиатура для начала генерации"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎨 Генерировать карточку", callback_data="generate_image")]
    ])
    return keyboard


def skip_keyboard(callback_data: str):
    """Клавиатура с кнопками 'Готово' и 'Назад'"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Готово", callback_data=callback_data)],
        [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_menu")]
    ])
    return keyboard


def result_keyboard(image_url: str = None):
    """Клавиатура после генерации изображения"""
    # Telegram ограничивает callback_data до 64 байт, поэтому не передаем URL напрямую
    # URL будет браться из state в обработчике
    buttons = [
        [InlineKeyboardButton(text="📥 Получить файлом", callback_data="download_image")],
        [InlineKeyboardButton(text="✏️ Редактировать промпт", callback_data="edit_prompt")],
        [InlineKeyboardButton(text="🔄 Внести правки в изображение", callback_data="refine_image")],
        [InlineKeyboardButton(text="🎨 Создать новое изображение", callback_data="generate_image")],
        [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def prompt_edit_keyboard():
    """Клавиатура для выбора способа создания промпта"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤖 Сгенерировать автоматически", callback_data="use_auto_prompt")],
        [InlineKeyboardButton(text="✏️ Написать свой промпт", callback_data="edit_prompt")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")]
    ])
    return keyboard


def prompt_preview_keyboard():
    """Клавиатура для предварительного просмотра промпта"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Использовать промпт", callback_data="confirm_auto_prompt")],
        [InlineKeyboardButton(text="✏️ Редактировать промпт", callback_data="edit_auto_prompt")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")]
    ])
    return keyboard


def custom_prompt_preview_keyboard():
    """Клавиатура подтверждения кастомного промпта"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Запустить генерацию", callback_data="confirm_custom_prompt")],
        [InlineKeyboardButton(text="✏️ Изменить промпт", callback_data="reenter_custom_prompt")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")]
    ])
    return keyboard


def aspect_ratio_keyboard():
    """Клавиатура выбора формата изображения для Озон"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📦 Стандартный товар (3:4)", callback_data="aspect_3_4")],
        [InlineKeyboardButton(text="👕 Одежда/Аксессуары (2:3)", callback_data="aspect_2_3")],
        [InlineKeyboardButton(text="◼️ Квадрат (1:1)", callback_data="aspect_1_1")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")]
    ])
    return keyboard


def skip_text_keyboard():
    """Клавиатура для пропуска текста на карточке"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏭ Пропустить (без текста)", callback_data="skip_card_text")],
        [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_menu")]
    ])
    return keyboard


def model_selection_keyboard(models: dict, selected_model_key: str = None):
    """Клавиатура выбора модели генерации"""
    buttons = []
    for model_key, model_info in models.items():
        name = model_info.get("name", model_key)
        cost = model_info.get("cost", 0)
        description = model_info.get("description", "")
        checkmark = "✅" if model_key == selected_model_key else "⚪"
        buttons.append([
            InlineKeyboardButton(
                text=f"{checkmark} {name} ({cost} токенов)",
                callback_data=f"select_model:{model_key}"
            )
        ])
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
