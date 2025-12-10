from aiogram.fsm.state import State, StatesGroup


class ImageGenerationStates(StatesGroup):
    """Состояния для генерации изображений товара"""
    choosing_model = State()  # Выбор модели генерации
    choosing_aspect_ratio = State()  # Выбор формата изображения
    waiting_for_product_photos = State()  # Ожидание фото товара (1-5)
    waiting_for_reference_photos = State()  # Ожидание фото референсов (1-5)
    waiting_for_card_text = State()  # Ожидание текста для карточки
    choosing_prompt_mode = State()  # Выбор режима промпта (авто или ручной)
    previewing_prompt = State()  # Предварительный просмотр автоматически сгенерированного промпта
    editing_auto_prompt = State()  # Редактирование автоматически сгенерированного промпта
    waiting_for_custom_prompt = State()  # Ожидание ввода кастомного промпта
    confirming_custom_prompt = State()  # Подтверждение кастомного промпта перед запуском
    generating = State()  # Процесс генерации
    waiting_for_refinement = State()  # Ожидание описания правок для изображения
