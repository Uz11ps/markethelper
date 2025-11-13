from backend.models import Settings


class SettingsService:
    """Сервис для работы с настройками приложения"""

    DEFAULT_AI_PROMPT = """Ты - помощник по маркетплейсам и онлайн-торговле.
Твоя задача - помогать пользователям с вопросами о продажах на маркетплейсах,
аналитике, оптимизации карточек товаров и других аспектах электронной коммерции.
Отвечай профессионально, используя предоставленный контекст из базы знаний."""

    DEFAULT_REFERRAL_BONUS = 100

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
    async def initialize_defaults(cls):
        """Инициализация настроек по умолчанию"""
        # Проверяем и создаем настройки если их нет
        if not await Settings.filter(key="ai_prompt").exists():
            await cls.set_ai_prompt(cls.DEFAULT_AI_PROMPT)

        if not await Settings.filter(key="referral_bonus").exists():
            await cls.set_referral_bonus(cls.DEFAULT_REFERRAL_BONUS)
