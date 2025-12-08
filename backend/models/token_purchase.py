from tortoise import fields
from tortoise.models import Model


class TokenPurchaseRequest(Model):
    """
    Заявки на покупку токенов
    """
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField("models.User", related_name="token_purchases")
    amount = fields.IntField()  # Количество токенов
    cost = fields.DecimalField(max_digits=10, decimal_places=2)  # Стоимость в рублях
    status = fields.CharField(50, default="PENDING")  # PENDING, APPROVED, REJECTED
    payment_method = fields.CharField(100, null=True)  # Способ оплаты
    
    created_at = fields.DatetimeField(auto_now_add=True)
    processed_at = fields.DatetimeField(null=True)
    
    class Meta:
        table = "token_purchase_requests"

