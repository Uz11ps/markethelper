from tortoise import fields
from tortoise.models import Model

class AccessFile(Model):
    id = fields.IntField(pk=True)
    group = fields.ForeignKeyField("models.AccessGroup", related_name="files")

    path = fields.CharField(255)
    login = fields.CharField(255, null=True)
    password = fields.CharField(255, null=True)

    last_updated = fields.DatetimeField(auto_now=True)
    locked_until = fields.DatetimeField(null=True)

    class Meta:
        table = "access_files"
