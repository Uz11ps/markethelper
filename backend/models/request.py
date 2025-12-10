from tortoise import fields
from tortoise.models import Model

class Request(Model):
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField("models.User", related_name="requests")
    
    tariff = fields.ForeignKeyField("models.Tariff", related_name="requests")
    duration = fields.ForeignKeyField("models.Duration", related_name="requests")
    status = fields.ForeignKeyField("models.Status", related_name="requests")
    
    # Тип подписки: "group" (складчина) или "individual" (индивидуальный доступ)
    subscription_type = fields.CharField(max_length=20, default="group")
    # Для складчины - ID группы файлов
    group_id = fields.IntField(null=True)
    # Для индивидуального доступа - email пользователя (если был указан)
    user_email = fields.CharField(255, null=True)

    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "requests"
