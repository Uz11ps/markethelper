from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder


def infographic_type_kb():
    """Клавиатура выбора типа генерации инфографики"""
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="📦 По товару"))
    builder.add(KeyboardButton(text="🎯 По референсу"))
    builder.add(KeyboardButton(text="🔙 Назад"))
    builder.adjust(2, 1)
    return builder.as_markup(resize_keyboard=True)


def upload_images_kb():
    """Клавиатура для загрузки изображений"""
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="✅ Загрузить изображения"))
    builder.add(KeyboardButton(text="🔙 Назад"))
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)


def skip_prompt_kb():
    """Клавиатура с возможностью пропустить ввод промта"""
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="⏭️ Пропустить"))
    builder.add(KeyboardButton(text="🔙 Назад"))
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)


def concepts_inline_kb(concepts_count: int = 3):
    """Inline клавиатура для выбора концепции"""
    builder = InlineKeyboardBuilder()
    
    for i in range(concepts_count):
        builder.add(InlineKeyboardButton(
            text=f"Концепция {i + 1}",
            callback_data=f"concept_{i}"
        ))
    
    builder.adjust(1)
    return builder.as_markup()


def style_edit_kb():
    """Клавиатура для редактирования стиля"""
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(text="🖌️ Иконки", callback_data="edit_icons"))
    builder.add(InlineKeyboardButton(text="🎨 Цвета", callback_data="edit_colors"))
    builder.add(InlineKeyboardButton(text="📐 Композиция", callback_data="edit_layout"))
    builder.add(InlineKeyboardButton(text="✅ Создать инфографику", callback_data="generate_final"))
    
    builder.adjust(3, 1)
    return builder.as_markup()


def icon_style_kb():
    """Клавиатура для выбора стиля иконок"""
    builder = InlineKeyboardBuilder()
    
    styles = [
        ("Контурные", "line"),
        ("Залитые", "solid"),
        ("3D", "3d"),
        ("Скетч", "sketch")
    ]
    
    for name, value in styles:
        builder.add(InlineKeyboardButton(text=name, callback_data=f"icon_style_{value}"))
    
    builder.add(InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_style"))
    builder.adjust(2, 2, 1)
    return builder.as_markup()


def color_palette_kb():
    """Клавиатура для выбора цветовой палитры"""
    builder = InlineKeyboardBuilder()
    
    palettes = [
        ("Монохромная", "monochrome"),
        ("Контрастная", "contrast"),
        ("Пастельная", "pastel"),
        ("Тёмная", "dark"),
        ("Натуральная", "natural")
    ]
    
    for name, value in palettes:
        builder.add(InlineKeyboardButton(text=name, callback_data=f"color_{value}"))
    
    builder.add(InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_style"))
    builder.adjust(2, 2, 1, 1)
    return builder.as_markup()


def background_style_kb():
    """Клавиатура для выбора стиля фона"""
    builder = InlineKeyboardBuilder()
    
    backgrounds = [
        ("Техно-Фокус", "tech"),
        ("Эко-Минимализм", "eco"),
        ("Яркий Брутализм", "bright"),
        ("Премиум/Люкс", "premium"),
        ("Лайфстайл", "lifestyle"),
        ("Инфо-Схема", "info")
    ]
    
    for name, value in backgrounds:
        builder.add(InlineKeyboardButton(text=name, callback_data=f"bg_{value}"))
    
    builder.add(InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_style"))
    builder.adjust(2, 2, 2, 1)
    return builder.as_markup()


def result_actions_kb():
    """Клавиатура с действиями для готовой инфографики"""
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(text="✏️ Редактировать", callback_data="edit_material"))
    builder.add(InlineKeyboardButton(text="🔄 Новая генерация", callback_data="new_generation"))
    builder.add(InlineKeyboardButton(text="📁 Мои проекты", callback_data="my_projects"))
    
    builder.adjust(1)
    return builder.as_markup()


def continue_or_finish_kb():
    """Клавиатура для продолжения или завершения"""
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="▶️ Продолжить"))
    builder.add(KeyboardButton(text="🔙 Назад"))
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)


def main_menu_with_infographic_kb(has_active_sub: bool):
    """Главное меню с добавленной кнопкой инфографики"""
    rows: list[list[KeyboardButton]] = [[KeyboardButton(text="👤 Профиль")]]

    if has_active_sub:
        rows[0].append(KeyboardButton(text="🔑 Доступы"))
        rows.append([KeyboardButton(text="🎨 Создать инфографику")])
    else:
        rows.append([KeyboardButton(text="🔑 Доступы")])

    rows.append([KeyboardButton(text="❓ FAQ")])

    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)