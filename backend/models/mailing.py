from tortoise import fields
from tortoise.models import Model

class Mailing(Model):
    id = fields.IntField(pk=True)
    created_by = fields.ForeignKeyField("models.User", related_name="mailings")

    audience_id = fields.IntField()   # FK -> audiences
    content = fields.TextField()

    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "mailings"
