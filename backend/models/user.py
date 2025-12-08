from tortoise import fields
from tortoise.models import Model


class User(Model):
    """
    Основная таблица пользователей
    """
    id = fields.IntField(pk=True)
    tg_id = fields.BigIntField(unique=True, index=True)
    username = fields.CharField(255, null=True)
    full_name = fields.CharField(255, null=True)

    bonus_balance = fields.IntField(default=0)
    token_balance = fields.IntField(default=0)  # Внутренняя валюта - токены
    
    is_banned = fields.BooleanField(default=False)  # Черный список

    referrer = fields.ForeignKeyField(
        "models.User",
        null=True,
        related_name="referrals"
    )

    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "users"


class Referral(Model):
    """
    Реферальные связи
    """
    id = fields.IntField(pk=True)
    referrer = fields.ForeignKeyField("models.User", related_name="invited")
    referred = fields.ForeignKeyField("models.User", related_name="was_invited")

    activated = fields.BooleanField(default=False)
    reward_given = fields.BooleanField(default=False)

    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "referrals"
