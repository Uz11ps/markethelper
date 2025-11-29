from tortoise import fields
from tortoise.models import Model
from typing import Optional
import json

class ProductDescription(Model):
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField("models.User", related_name="product_descriptions")
    
    title = fields.CharField(max_length=255)
    description = fields.TextField()
    product_images = fields.JSONField(default=list)  # list of base64 strings or URLs
    reference_images = fields.JSONField(default=list)  # list of base64 strings or URLs
    
    generated_concepts = fields.JSONField(default=list)  # 3 концепции из промта
    selected_concept_index = fields.IntField(null=True)  # какая концепция выбрана
    
    editable_prompt_areas = fields.JSONField(default=dict)  # области для редактирования
    final_prompt = fields.TextField(null=True)
    
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    
    class Meta:
        table = "product_descriptions"

class EditablePromptTemplate(Model):
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField("models.User", related_name="prompt_templates")
    
    name = fields.CharField(max_length=255)
    base_prompt = fields.TextField()
    
    # Области для редактирования
    icon_areas = fields.JSONField(default=dict)  # {area_name: default_value}
    color_areas = fields.JSONField(default=dict)  # {area_name: default_value}
    layout_areas = fields.JSONField(default=dict)  # {area_name: default_value}
    
    is_default = fields.BooleanField(default=False)
    
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    
    class Meta:
        table = "editable_prompt_templates"

class InfographicProject(Model):
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField("models.User", related_name="infographic_projects")
    
    project_type = fields.CharField(max_length=50)  # "product" или "reference"
    title = fields.CharField(max_length=255)
    
    product_description = fields.ForeignKeyField(
        "models.ProductDescription", 
        related_name="infographic_projects",
        null=True
    )
    
    # Состояние проекта
    status = fields.CharField(max_length=50, default="draft")  # draft, generated, completed
    
    # Генерированные результаты
    generated_images = fields.JSONField(default=list)  # URLs генерированных изображений
    selected_image_url = fields.CharField(max_length=500, null=True)
    
    # Настройки генерации
    generation_settings = fields.JSONField(default=dict)
    
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    
    class Meta:
        table = "infographic_projects"