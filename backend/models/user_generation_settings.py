from tortoise import fields
from tortoise.models import Model


class UserGenerationSettings(Model):
    """
    Настройки генерации для пользователя
    """
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField("models.User", related_name="generation_settings", unique=True)
    
    # Выбранная модель для генерации (ключ из настроек админа)
    selected_model_key = fields.CharField(255, null=True)
    
    # Кастомный промпт пользователя (если null, используется системный)
    custom_prompt = fields.TextField(null=True)
    
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "user_generation_settings"

