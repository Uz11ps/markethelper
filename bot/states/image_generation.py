from aiogram.fsm.state import State, StatesGroup


class ImageGenerationStates(StatesGroup):
    """Состояния для генерации изображений товара"""
    choosing_aspect_ratio = State()  # Выбор формата изображения
    waiting_for_product_photos = State()  # Ожидание фото товара (1-5)
    waiting_for_reference_photos = State()  # Ожидание фото референсов (1-5)
    waiting_for_card_text = State()  # Ожидание текста для карточки
    choosing_prompt_mode = State()  # Выбор режима промпта (авто или ручной)
    waiting_for_custom_prompt = State()  # Ожидание ввода кастомного промпта
    generating = State()  # Процесс генерации
    waiting_for_refinement = State()  # Ожидание описания правок для изображения
