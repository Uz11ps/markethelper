from tortoise import fields
from tortoise.models import Model


class PendingBonus(Model):
    """
    Ожидающие подтверждения реферальные бонусы
    """
    id = fields.IntField(pk=True)
    referral = fields.ForeignKeyField("models.Referral", related_name="pending_bonuses")
    referrer = fields.ForeignKeyField("models.User", related_name="pending_bonuses")
    referred = fields.ForeignKeyField("models.User", related_name="pending_bonuses_for")
    
    bonus_amount = fields.IntField()  # Размер бонуса
    status = fields.CharField(max_length=20, default="pending")  # pending, approved, rejected
    
    # Связь с заявкой, при одобрении которой был создан этот бонус
    request = fields.ForeignKeyField("models.Request", null=True, related_name="pending_bonuses")
    
    created_at = fields.DatetimeField(auto_now_add=True)
    approved_at = fields.DatetimeField(null=True)
    approved_by = fields.ForeignKeyField("models.Admin", null=True, related_name="approved_bonuses")

    class Meta:
        table = "pending_bonuses"

