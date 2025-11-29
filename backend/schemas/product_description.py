from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field

class ProductDescriptionCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    product_images: List[str] = Field(default_factory=list)  # base64 strings or URLs
    reference_images: List[str] = Field(default_factory=list)  # base64 strings or URLs

class ProductDescriptionUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, min_length=1)
    product_images: Optional[List[str]] = None
    reference_images: Optional[List[str]] = None
    selected_concept_index: Optional[int] = None
    final_prompt: Optional[str] = None

class ProductDescriptionResponse(BaseModel):
    id: int
    title: str
    description: str
    product_images: List[str]
    reference_images: List[str]
    generated_concepts: List[Dict[str, Any]]
    selected_concept_index: Optional[int]
    editable_prompt_areas: Dict[str, Any]
    final_prompt: Optional[str]
    created_at: str
    updated_at: str

class GenerateProductDescriptionRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    product_images: List[str] = Field(..., min_items=1)  # base64 strings
    reference_images: Optional[List[str]] = Field(default_factory=list)
    user_prompt: Optional[str] = Field(default="")

class EditablePromptTemplateCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    base_prompt: str = Field(..., min_length=1)
    icon_areas: Dict[str, str] = Field(default_factory=dict)
    color_areas: Dict[str, str] = Field(default_factory=dict)
    layout_areas: Dict[str, str] = Field(default_factory=dict)
    is_default: bool = Field(default=False)

class EditablePromptTemplateUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    base_prompt: Optional[str] = Field(None, min_length=1)
    icon_areas: Optional[Dict[str, str]] = None
    color_areas: Optional[Dict[str, str]] = None
    layout_areas: Optional[Dict[str, str]] = None
    is_default: Optional[bool] = None

class EditablePromptTemplateResponse(BaseModel):
    id: int
    name: str
    base_prompt: str
    icon_areas: Dict[str, str]
    color_areas: Dict[str, str]
    layout_areas: Dict[str, str]
    is_default: bool
    created_at: str
    updated_at: str

class InfographicProjectCreate(BaseModel):
    project_type: Literal["product", "reference"]
    title: str = Field(..., min_length=1, max_length=255)
    product_description_id: Optional[int] = None
    generation_settings: Dict[str, Any] = Field(default_factory=dict)

class InfographicProjectUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    status: Optional[Literal["draft", "generated", "completed"]] = None
    generated_images: Optional[List[str]] = None
    selected_image_url: Optional[str] = None
    generation_settings: Optional[Dict[str, Any]] = None

class InfographicProjectResponse(BaseModel):
    id: int
    project_type: str
    title: str
    status: str
    generated_images: List[str]
    selected_image_url: Optional[str]
    generation_settings: Dict[str, Any]
    created_at: str
    updated_at: str

class EditPromptAreasRequest(BaseModel):
    product_description_id: int
    icon_edits: Dict[str, str] = Field(default_factory=dict)
    color_edits: Dict[str, str] = Field(default_factory=dict)
    layout_edits: Dict[str, str] = Field(default_factory=dict)

class GenerateInfographicRequest(BaseModel):
    project_id: int
    concept_index: Optional[int] = Field(default=0)
    custom_prompt_edits: Optional[Dict[str, Any]] = Field(default_factory=dict)
