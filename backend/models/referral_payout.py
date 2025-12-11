from tortoise import fields
from tortoise.models import Model


class ReferralPayout(Model):
    """
    Заявки на выплату рублей за рефералов
    """
    id = fields.IntField(pk=True)
    referrer = fields.ForeignKeyField("models.User", related_name="referral_payouts")
    
    # Количество рефералов за которые выплата
    referral_count = fields.IntField()
    
    # Сумма выплаты в рублях
    amount_rub = fields.FloatField()
    
    # Статус: PENDING, APPROVED, REJECTED
    status = fields.CharField(max_length=20, default="PENDING")
    
    # Комментарий администратора
    admin_comment = fields.TextField(null=True)
    
    # Администратор который обработал заявку
    processed_by = fields.ForeignKeyField("models.Admin", null=True, related_name="processed_payouts")
    
    created_at = fields.DatetimeField(auto_now_add=True)
    processed_at = fields.DatetimeField(null=True)

    class Meta:
        table = "referral_payouts"

