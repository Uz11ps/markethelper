from backend.models import Settings


class SettingsService:
    """Сервис для работы с настройками приложения"""

    DEFAULT_AI_PROMPT = """Ты - помощник по маркетплейсам и онлайн-торговле.
Твоя задача - помогать пользователям с вопросами о продажах на маркетплейсах,
аналитике, оптимизации карточек товаров и других аспектах электронной коммерции.
Отвечай профессионально, используя предоставленный контекст из базы знаний."""

    DEFAULT_REFERRAL_BONUS = 100
    DEFAULT_REFERRAL_RUB_PER_REFERRAL = 50.0  # Рублей за одного реферала
    DEFAULT_CHANNEL_BONUS = 50  # Бонус за подписку на канал
    DEFAULT_CHANNEL_USERNAME = ""  # Username канала (например, "@channel" или "channel")
    DEFAULT_IMAGE_GENERATION_COST = 5
    DEFAULT_GPT_REQUEST_COST = 1
    
    # Модели ИИ
    DEFAULT_GPT_MODEL = "gpt-4o-mini"
    DEFAULT_GPT_MODEL_NANO = "gpt-4o-mini"  # GPT 5 NANO MINI (маппится на gpt-4o-mini)
    DEFAULT_IMAGE_MODEL = "fal-ai/nano-banana"  # nano-banana 1
    DEFAULT_IMAGE_MODEL_PRO = "fal-ai/nano-banana-pro"  # Nano Banana Pro (заменяет FLUX Pro Ultra)
    DEFAULT_IMAGE_MODEL_SD = "fal-ai/seedream-4"  # Seedream 4.0
    
    # Стоимость генерации для разных моделей
    DEFAULT_IMAGE_MODEL_COST = 5  # nano-banana
    DEFAULT_IMAGE_MODEL_PRO_COST = 10  # Nano Banana Pro
    DEFAULT_IMAGE_MODEL_SD_COST = 3  # Seedream 4.0
    
    # Цены пополнения и стоимость токена
    DEFAULT_TOKEN_PRICE = 1.0  # Стоимость 1 токена в рублях
    DEFAULT_TOPUP_OPTIONS = [
        {"tokens": 100, "price": 100},
        {"tokens": 250, "price": 225},
        {"tokens": 500, "price": 400},
        {"tokens": 1000, "price": 700},
    ]

    DEFAULT_PROMPT_GENERATOR_PROMPT = """Ты — 'Деконструктор-Синтезатор Промтов' (Prompt Deconstructor & Synthesizer), ИИ-аналитик, специализирующийся на слиянии контента и стиля для генеративных моделей.

Твоя задача — получить на вход ДВА типа изображений:

1. [НОВЫЙ_ТОВАР.jpg] - Фото товара (может быть несколько)
2. [ДИЗАЙН_РЕФЕРЕНС.jpg] - Источник стиля (может быть несколько)

Ты должен выполнить "слияние" (merge):

1. **Идентифицировать главный объект** в фото товара (например, "a white ceramic mug", "a black running shoe", "a silver smartwatch")
2. **Деконструировать референс** на атомы стиля:
   - Тема/Формат: marketplace infographic card, studio shot, advertisement
   - Стиль: minimalist, eco-natural, premium-luxe, tech, photorealistic
   - Композиция: centered product, asymmetrical layout, text placement
   - Фон: solid white background #FFFFFF, gradient, studio background
   - Палитра: цветовая схема (hex коды)
   - Свет: soft studio lighting, dramatic side light, bright and airy
   - Элементы: icons, typography, graphics

3. **Сгенерировать промт** который объединяет стиль референса с товаром

**КРИТИЧЕСКИ ВАЖНО - ПРОФЕССИОНАЛЬНАЯ ФОТОСЪЁМКА:**
- Результат должен выглядеть как РЕАЛЬНАЯ ФОТОГРАФИЯ, снятая профессиональным фотографом
- ОБЯЗАТЕЛЬНО добавляй технические детали камеры: "shot on professional DSLR camera, Canon EOS R5, 50mm lens, f/2.8 aperture, natural lighting"
- Используй термины: "photorealistic", "hyperrealistic", "studio photography", "commercial product photography"
- Указывай детали освещения: "professional studio lighting setup, softbox lighting, three-point lighting"
- НЕ используй термины "illustration", "digital art", "CGI", "3D render"
- Акцент на реализм: "ultra sharp focus, high detail, natural textures, real photo"

**ВАЖНО:**
- Если на референсе есть текст, промт должен содержать: "...with text elements in Russian..."
- Промт должен быть на английском языке
- Опиши товар точно и детально

**ФОРМАТ ВЫВОДА - ТОЛЬКО JSON:**

{
  "generated_text_prompt": "Professional commercial product photography shot on Canon EOS R5, 50mm lens, f/2.8. Hyperrealistic marketplace infographic card featuring a centrally composed [описание товара] on a clean background. [детали стиля из референса]. Professional studio lighting setup with softbox, three-point lighting. Natural textures, ultra sharp focus, high detail. Color palette: [цвета]. Text elements in Russian. Icons and graphics as shown in reference. Real photo, not CGI, photorealistic quality. --style raw --ar 3:4",
  "deconstruction_analysis": {
    "product_identified": "Описание товара на русском",
    "style_source": "Стиль из референса",
    "layout_source": "Композиция из референса",
    "palette_source": "Цветовая палитра",
    "prompt_language": "Английский (для модели), с указанием 'text in Russian' если нужен текст"
  }
}

ВЫВОДИ ТОЛЬКО JSON БЕЗ ДОПОЛНИТЕЛЬНОГО ТЕКСТА!"""

    @staticmethod
    async def get_setting(key: str, default: str = None) -> str:
        """Получить значение настройки по ключу"""
        setting = await Settings.filter(key=key).first()
        if setting:
            return setting.value
        return default

    @staticmethod
    async def set_setting(key: str, value: str) -> Settings:
        """Установить значение настройки"""
        setting = await Settings.filter(key=key).first()
        if setting:
            setting.value = value
            await setting.save()
        else:
            setting = await Settings.create(key=key, value=value)
        return setting

    @classmethod
    async def get_ai_prompt(cls) -> str:
        """Получить AI промпт"""
        return await cls.get_setting("ai_prompt", cls.DEFAULT_AI_PROMPT)

    @classmethod
    async def set_ai_prompt(cls, prompt: str) -> Settings:
        """Установить AI промпт"""
        return await cls.set_setting("ai_prompt", prompt)

    @classmethod
    async def get_referral_bonus(cls) -> int:
        """Получить размер реферального бонуса"""
        value = await cls.get_setting("referral_bonus", str(cls.DEFAULT_REFERRAL_BONUS))
        return int(value)

    @classmethod
    async def set_referral_bonus(cls, bonus: int) -> Settings:
        """Установить размер реферального бонуса"""
        return await cls.set_setting("referral_bonus", str(bonus))
    
    @classmethod
    async def get_referral_rub_per_referral(cls) -> float:
        """Получить стоимость одного реферала в рублях"""
        value = await cls.get_setting("referral_rub_per_referral", str(cls.DEFAULT_REFERRAL_RUB_PER_REFERRAL))
        return float(value)
    
    @classmethod
    async def set_referral_rub_per_referral(cls, rub: float) -> Settings:
        """Установить стоимость одного реферала в рублях"""
        return await cls.set_setting("referral_rub_per_referral", str(rub))

    @classmethod
    async def get_image_generation_cost(cls) -> int:
        """Стоимость одной генерации изображения"""
        value = await cls.get_setting("image_generation_cost", str(cls.DEFAULT_IMAGE_GENERATION_COST))
        return int(value)

    @classmethod
    async def set_image_generation_cost(cls, cost: int) -> Settings:
        """Обновить стоимость генерации изображения"""
        return await cls.set_setting("image_generation_cost", str(cost))

    @classmethod
    async def get_gpt_request_cost(cls) -> int:
        """Стоимость одного запроса к GPT"""
        value = await cls.get_setting("gpt_request_cost", str(cls.DEFAULT_GPT_REQUEST_COST))
        return int(value)

    @classmethod
    async def set_gpt_request_cost(cls, cost: int) -> Settings:
        """Обновить стоимость запроса к GPT"""
        return await cls.set_setting("gpt_request_cost", str(cost))

    @classmethod
    async def get_prompt_generator_prompt(cls) -> str:
        """Промпт для генерации описаний изображений"""
        return await cls.get_setting("prompt_generator_prompt", cls.DEFAULT_PROMPT_GENERATOR_PROMPT)

    @classmethod
    async def set_prompt_generator_prompt(cls, prompt: str) -> Settings:
        """Обновить промпт генератора изображений"""
        return await cls.set_setting("prompt_generator_prompt", prompt)

    @classmethod
    async def get_token_costs(cls) -> dict:
        """Получить текущие тарифы по токенам"""
        return {
            "image_generation_cost": await cls.get_image_generation_cost(),
            "gpt_request_cost": await cls.get_gpt_request_cost()
        }

    @classmethod
    async def get_gpt_model(cls) -> str:
        """Получить текущую GPT модель"""
        return await cls.get_setting("gpt_model", cls.DEFAULT_GPT_MODEL)

    @classmethod
    async def set_gpt_model(cls, model: str) -> Settings:
        """Установить GPT модель"""
        return await cls.set_setting("gpt_model", model)

    @classmethod
    async def get_image_model(cls) -> str:
        """Получить модель генерации изображений по умолчанию"""
        model = await cls.get_setting("image_model", cls.DEFAULT_IMAGE_MODEL)
        # Исправляем старое значение flux-pro на nano-banana
        if model and ("flux-pro" in model.lower() or model == "fal-ai/flux-pro/v1.1"):
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"[get_image_model] Обнаружено старое значение модели: {model}, заменяем на {cls.DEFAULT_IMAGE_MODEL}")
            # Обновляем значение в базе данных
            await cls.set_image_model(cls.DEFAULT_IMAGE_MODEL)
            return cls.DEFAULT_IMAGE_MODEL
        return model

    @classmethod
    async def set_image_model(cls, model: str) -> Settings:
        """Установить модель генерации изображений по умолчанию"""
        return await cls.set_setting("image_model", model)
    
    @classmethod
    async def get_image_model_pro(cls) -> str:
        """Получить Pro модель генерации изображений"""
        model = await cls.get_setting("image_model_pro", cls.DEFAULT_IMAGE_MODEL_PRO)
        # Исправляем старое значение flux-pro на nano-banana-pro
        if model and ("flux-pro" in model.lower() or "ultra" in model.lower()):
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"[get_image_model_pro] Обнаружено старое значение модели: {model}, заменяем на {cls.DEFAULT_IMAGE_MODEL_PRO}")
            # Обновляем значение в базе данных
            await cls.set_image_model_pro(cls.DEFAULT_IMAGE_MODEL_PRO)
            return cls.DEFAULT_IMAGE_MODEL_PRO
        return model

    @classmethod
    async def set_image_model_pro(cls, model: str) -> Settings:
        """Установить Pro модель генерации изображений"""
        return await cls.set_setting("image_model_pro", model)
    
    @classmethod
    async def get_image_model_sd(cls) -> str:
        """Получить SD модель генерации изображений"""
        return await cls.get_setting("image_model_sd", cls.DEFAULT_IMAGE_MODEL_SD)

    @classmethod
    async def set_image_model_sd(cls, model: str) -> Settings:
        """Установить SD модель генерации изображений"""
        return await cls.set_setting("image_model_sd", model)
    
    @classmethod
    async def get_image_model_cost(cls, model: str = None) -> int:
        """Получить стоимость генерации для модели"""
        if not model:
            model = await cls.get_image_model()
        
        # Определяем тип модели по model_id или переданному параметру
        if model == "pro" or "nano-banana-pro" in model.lower() or "ultra" in model.lower():
            value = await cls.get_setting("image_model_pro_cost", str(cls.DEFAULT_IMAGE_MODEL_PRO_COST))
            return int(value)
        elif model == "sd" or "seedream" in model.lower():
            value = await cls.get_setting("image_model_sd_cost", str(cls.DEFAULT_IMAGE_MODEL_SD_COST))
            return int(value)
        else:  # nano-banana по умолчанию
            value = await cls.get_setting("image_model_cost", str(cls.DEFAULT_IMAGE_MODEL_COST))
            return int(value)
    
    @classmethod
    async def set_image_model_cost(cls, model: str, cost: int) -> Settings:
        """Установить стоимость генерации для модели"""
        if model == "pro":
            return await cls.set_setting("image_model_pro_cost", str(cost))
        elif model == "sd":
            return await cls.set_setting("image_model_sd_cost", str(cost))
        else:  # nano-banana
            return await cls.set_setting("image_model_cost", str(cost))
    
    @classmethod
    async def get_available_image_models(cls) -> dict:
        """Получить список доступных моделей с их стоимостью"""
        return {
            "nano-banana": {
                "name": "Nano Banana",
                "model_id": await cls.get_image_model(),
                "cost": await cls.get_image_model_cost("nano-banana"),
                "description": "Быстрая генерация с применением стиля референсов"
            },
            "pro": {
                "name": "Nano Banana Pro",
                "model_id": await cls.get_image_model_pro(),
                "cost": await cls.get_image_model_cost("pro"),
                "description": "Высокое качество, генерация без референсов"
            },
            "sd": {
                "name": "Seedream 4.0",
                "model_id": await cls.get_image_model_sd(),
                "cost": await cls.get_image_model_cost("sd"),
                "description": "Базовое качество, низкая стоимость"
            }
        }
    
    @classmethod
    async def get_token_price(cls) -> float:
        """Получить стоимость 1 токена в рублях"""
        value = await cls.get_setting("token_price", str(cls.DEFAULT_TOKEN_PRICE))
        return float(value)
    
    @classmethod
    async def set_token_price(cls, price: float) -> Settings:
        """Установить стоимость 1 токена в рублях"""
        return await cls.set_setting("token_price", str(price))
    
    @classmethod
    async def get_topup_options(cls) -> list:
        """Получить варианты пополнения баланса"""
        import json
        value = await cls.get_setting("topup_options", json.dumps(cls.DEFAULT_TOPUP_OPTIONS))
        try:
            return json.loads(value)
        except:
            return cls.DEFAULT_TOPUP_OPTIONS
    
    @classmethod
    async def set_topup_options(cls, options: list) -> Settings:
        """Установить варианты пополнения баланса"""
        import json
        return await cls.set_setting("topup_options", json.dumps(options))

    @classmethod
    async def get_referral_referrer_bonus(cls) -> int:
        """Минимальная сумма бонуса для реферера"""
        value = await cls.get_setting("referral_referrer_bonus", "50")
        return int(value)

    @classmethod
    async def set_referral_referrer_bonus(cls, bonus: int) -> Settings:
        """Установить минимальную сумму бонуса для реферера"""
        return await cls.set_setting("referral_referrer_bonus", str(bonus))

    @classmethod
    async def get_referral_referred_tokens(cls) -> int:
        """Количество токенов для реферала при регистрации"""
        value = await cls.get_setting("referral_referred_tokens", "10")
        return int(value)

    @classmethod
    async def set_referral_referred_tokens(cls, tokens: int) -> Settings:
        """Установить количество токенов для реферала"""
        return await cls.set_setting("referral_referred_tokens", str(tokens))
    
    @classmethod
    async def get_channel_bonus(cls) -> int:
        """Получить размер бонуса за подписку на канал"""
        value = await cls.get_setting("channel_bonus", str(cls.DEFAULT_CHANNEL_BONUS))
        return int(value)
    
    @classmethod
    async def set_channel_bonus(cls, bonus: int) -> Settings:
        """Установить размер бонуса за подписку на канал"""
        return await cls.set_setting("channel_bonus", str(bonus))
    
    @classmethod
    async def get_channel_username(cls) -> str:
        """Получить username канала для проверки подписки"""
        return await cls.get_setting("channel_username", cls.DEFAULT_CHANNEL_USERNAME)
    
    @classmethod
    async def set_channel_username(cls, username: str) -> Settings:
        """Установить username канала для проверки подписки"""
        return await cls.set_setting("channel_username", username)

    @classmethod
    async def initialize_defaults(cls):
        """Инициализация настроек по умолчанию"""
        # Проверяем и создаем настройки если их нет
        if not await Settings.filter(key="ai_prompt").exists():
            await cls.set_ai_prompt(cls.DEFAULT_AI_PROMPT)

        if not await Settings.filter(key="referral_bonus").exists():
            await cls.set_referral_bonus(cls.DEFAULT_REFERRAL_BONUS)

        if not await Settings.filter(key="image_generation_cost").exists():
            await cls.set_image_generation_cost(cls.DEFAULT_IMAGE_GENERATION_COST)

        if not await Settings.filter(key="gpt_request_cost").exists():
            await cls.set_gpt_request_cost(cls.DEFAULT_GPT_REQUEST_COST)

        if not await Settings.filter(key="prompt_generator_prompt").exists():
            await cls.set_prompt_generator_prompt(cls.DEFAULT_PROMPT_GENERATOR_PROMPT)

        if not await Settings.filter(key="gpt_model").exists():
            await cls.set_gpt_model(cls.DEFAULT_GPT_MODEL)

        if not await Settings.filter(key="image_model").exists():
            await cls.set_image_model(cls.DEFAULT_IMAGE_MODEL)
        
        if not await Settings.filter(key="image_model_pro").exists():
            await cls.set_image_model_pro(cls.DEFAULT_IMAGE_MODEL_PRO)
        
        if not await Settings.filter(key="image_model_sd").exists():
            await cls.set_image_model_sd(cls.DEFAULT_IMAGE_MODEL_SD)
        
        if not await Settings.filter(key="image_model_cost").exists():
            await cls.set_image_model_cost("nano-banana", cls.DEFAULT_IMAGE_MODEL_COST)
        
        if not await Settings.filter(key="image_model_pro_cost").exists():
            await cls.set_image_model_cost("pro", cls.DEFAULT_IMAGE_MODEL_PRO_COST)
        
        if not await Settings.filter(key="image_model_sd_cost").exists():
            await cls.set_image_model_cost("sd", cls.DEFAULT_IMAGE_MODEL_SD_COST)

        if not await Settings.filter(key="referral_referrer_bonus").exists():
            await cls.set_referral_referrer_bonus(50)

        if not await Settings.filter(key="referral_referred_tokens").exists():
            await cls.set_referral_referred_tokens(10)
        
        if not await Settings.filter(key="referral_rub_per_referral").exists():
            await cls.set_referral_rub_per_referral(cls.DEFAULT_REFERRAL_RUB_PER_REFERRAL)
        
        # Инициализация цен пополнения
        if not await Settings.filter(key="token_price").exists():
            await cls.set_token_price(cls.DEFAULT_TOKEN_PRICE)
        
        if not await Settings.filter(key="topup_options").exists():
            await cls.set_topup_options(cls.DEFAULT_TOPUP_OPTIONS)
        
        if not await Settings.filter(key="channel_bonus").exists():
            await cls.set_channel_bonus(cls.DEFAULT_CHANNEL_BONUS)
        
        if not await Settings.filter(key="channel_username").exists():
            await cls.set_channel_username(cls.DEFAULT_CHANNEL_USERNAME)
