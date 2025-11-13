from tortoise import fields
from tortoise.models import Model

class AIRequest(Model):
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField("models.User", related_name="ai_requests")

    question = fields.TextField()
    answer = fields.TextField()
    rating_id = fields.IntField(null=True)  # FK -> ratings

    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "ai_requests"
