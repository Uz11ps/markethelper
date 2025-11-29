from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def generation_result_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔁 Сгенерировать ещё", callback_data="profile:open_generation"),
                InlineKeyboardButton(text="⬅️ Назад в профиль", callback_data="profile:back"),
            ]
        ]
    )


def generation_type_choice_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🏆 Заглавная картинка", callback_data="generation:type:cover"),
            ],
            [
                InlineKeyboardButton(text="🧩 Второй слайд", callback_data="generation:type:second_slide"),
            ],
            [
                InlineKeyboardButton(text="↩️ Загрузить другое фото", callback_data="generation:restart"),
            ],
        ]
    )


def prompt_review_kb(stage_titles: list[tuple[str, str]]) -> InlineKeyboardMarkup:
    buttons: list[list[InlineKeyboardButton]] = []

    for key, title in stage_titles:
        buttons.append([
            InlineKeyboardButton(text=f"✏️ {title}", callback_data=f"generation:edit:{key}")
        ])

    buttons.append([
        InlineKeyboardButton(text="🔄 Сменить тип слайда", callback_data="generation:change_type"),
    ])
    buttons.append([
        InlineKeyboardButton(text="✅ Сформировать инфографику", callback_data="generation:confirm"),
    ])
    buttons.append([
        InlineKeyboardButton(text="↩️ Начать заново", callback_data="generation:restart"),
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)
