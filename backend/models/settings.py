from tortoise import Model, fields


class Settings(Model):
    id = fields.IntField(pk=True)
    key = fields.CharField(max_length=255, unique=True)
    value = fields.TextField()

    class Meta:
        table = "settings"

    def __str__(self):
        return f"{self.key}: {self.value}"


class BroadcastMessage(Model):
    """История рассылок"""
    id = fields.IntField(pk=True)
    message = fields.TextField()
    audience = fields.CharField(max_length=50)  # active, inactive, all
    sent_count = fields.IntField(default=0)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "broadcast_messages"

    def __str__(self):
        return f"Broadcast {self.id}: {self.audience} ({self.sent_count} sent)"
