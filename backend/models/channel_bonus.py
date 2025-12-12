from tortoise import fields
from tortoise.models import Model


class ChannelBonusRequest(Model):
    """
    Запросы на бонус за подписку на канал (требуют одобрения админа)
    """
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField("models.User", related_name="channel_bonus_requests")
    
    bonus_amount = fields.IntField()  # Размер бонуса
    status = fields.CharField(max_length=20, default="pending")  # pending, approved, rejected
    
    created_at = fields.DatetimeField(auto_now_add=True)
    approved_at = fields.DatetimeField(null=True)
    approved_by = fields.ForeignKeyField("models.Admin", null=True, related_name="approved_channel_bonuses")

    class Meta:
        table = "channel_bonus_requests"

