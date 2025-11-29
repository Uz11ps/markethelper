from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, model_validator


class DesignTemplateBase(BaseModel):
    name: str = Field(..., max_length=150)
    type: str = Field(..., max_length=50, description="Тип слайда: cover или second_slide")
    theme_tags: Optional[str] = Field(default=None, max_length=250)
    prompt: str
    sections: Optional[list[dict[str, Any]]] = None
    negative_prompt: Optional[str] = None
    preview_url: Optional[str] = Field(default=None, max_length=300)


class DesignTemplateCreate(DesignTemplateBase):
    pass


class DesignTemplateOut(DesignTemplateBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class DesignPromptRequest(BaseModel):
    mode: Literal["infographic", "custom", "competitor"] = Field(..., description="Режим генерации промпта")
    template_type: Optional[str] = Field(default=None, max_length=50)
    product_keywords: Optional[str] = Field(default=None, max_length=250)
    product_name: Optional[str] = Field(default=None, max_length=150)
    reference_image_base64: Optional[str] = Field(default=None, description="Base64 изображение-референс")
    prompt: Optional[str] = Field(default=None, max_length=4000, description="Пользовательский промпт")
    negative_prompt: Optional[str] = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def validate_mode(cls, values: "DesignPromptRequest") -> "DesignPromptRequest":
        mode = values.mode
        if mode in {"infographic", "competitor"} and not values.reference_image_base64:
            raise ValueError("Для выбранного режима требуется изображение.")
        if mode == "custom" and not values.prompt:
            raise ValueError("Для пользовательского режима необходимо передать промпт.")
        return values


class DesignPromptResponse(BaseModel):
    prompt: str = Field(..., max_length=4000)
    negative_prompt: Optional[str] = Field(default=None, max_length=2000)
    template_id: Optional[int] = None
    template_name: Optional[str] = None
    template_type: Optional[str] = None
    preview_url: Optional[str] = None
    warnings: list[str] = Field(default_factory=list)
    stored_template_id: Optional[int] = Field(
        default=None, description="ID шаблона, созданного из клиентского референса"
    )
    concept: Optional[dict[str, Any]] = Field(
        default=None, description="JSON-концепция, собранная из референсов"
    )
    concept_raw: Optional[str] = Field(
        default=None, description="Строковое представление концепции"
    )
