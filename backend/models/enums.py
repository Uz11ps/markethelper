from tortoise import fields
from tortoise.models import Model


class Tariff(Model):
    """
    Тарифы подписки (например: Индивидуал, Складчина).
    """
    id = fields.IntField(pk=True)
    code = fields.CharField(50, unique=True)
    name = fields.CharField(100)

    class Meta:
        table = "tariffs"


class Status(Model):
    """
    Универсальная таблица для всех статусов.
    Например:
      type = "subscription", code = "ACTIVE", name = "Активна"
      type = "subscription", code = "EXPIRED", name = "Истекла"
      type = "request", code = "PENDING", name = "В ожидании"
    """
    id = fields.IntField(pk=True)
    type = fields.CharField(50, index=True)   
    code = fields.CharField(50)               
    name = fields.CharField(100)

    class Meta:
        table = "statuses"
        unique_together = (("type", "code"),)


class Duration(Model):
    """
    Длительности подписок (в месяцах).
    """
    id = fields.IntField(pk=True)
    months = fields.IntField(unique=True) 

    class Meta:
        table = "durations"


class Audience(Model):
    """
    Типы аудиторий для рассылки.
    """
    id = fields.IntField(pk=True)
    code = fields.CharField(50, unique=True) 
    name = fields.CharField(100)

    class Meta:
        table = "audiences"
