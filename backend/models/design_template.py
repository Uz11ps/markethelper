from tortoise import fields
from tortoise.models import Model


class DesignTemplate(Model):
    """
    Пресеты инфографик, которые подбираются по типу и тематике товара.
    """

    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=150)
    type = fields.CharField(max_length=50, index=True)
    theme_tags = fields.CharField(max_length=250, default="")
    prompt = fields.TextField()
    sections = fields.JSONField(null=True)
    negative_prompt = fields.TextField(null=True)
    preview_url = fields.CharField(max_length=300, null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "design_templates"

    def tag_list(self) -> list[str]:
        """
        Возвращает список тегов по разделителю запятая/пробел.
        """
        raw = (self.theme_tags or "").strip()
        if not raw:
            return []
        parts = [part.strip() for part in raw.replace(";", ",").split(",")]
        return [part for part in parts if part]
