from tortoise import fields
from tortoise.models import Model

class AccessGroup(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(50, unique=True)  # "SF-1"
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "access_groups"


class Subscription(Model):
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField("models.User", related_name="subscriptions")
    tariff_id = fields.IntField()   # FK -> tariffs
    status_id = fields.IntField()   # FK -> subscription_statuses
    group = fields.ForeignKeyField("models.AccessGroup", null=True, related_name="subscriptions")

    start_date = fields.DatetimeField(auto_now_add=True)
    end_date = fields.DatetimeField()

    class Meta:
        table = "subscriptions"
