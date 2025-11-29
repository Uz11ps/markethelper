from typing import List

from fastapi import APIRouter, HTTPException, Query

from backend.schemas import (
    DesignPromptRequest,
    DesignPromptResponse,
    DesignTemplateCreate,
    DesignTemplateOut,
)
from backend.services import design_service
from backend.services import prompt_service
from backend.services.prompt_service import PromptGenerationError

router = APIRouter(prefix="/designs", tags=["Design templates"])


@router.get("/search", response_model=List[DesignTemplateOut])
async def search_designs(
    template_type: str = Query(..., alias="type", description="Тип шаблона: cover или second_slide"),
    query: str | None = Query(default=None, description="Текстовый запрос по тематике"),
    limit: int = Query(default=3, ge=1, le=10),
):
    templates = await design_service.search_templates(template_type=template_type, query=query, limit=limit)
    return [DesignTemplateOut.model_validate(template) for template in templates]


@router.post("/", response_model=DesignTemplateOut, status_code=201)
async def create_design(payload: DesignTemplateCreate):
    try:
        template = await design_service.create_template(**payload.model_dump())
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return DesignTemplateOut.model_validate(template)


@router.post("/generate", response_model=DesignPromptResponse)
async def generate_design_prompt(payload: DesignPromptRequest):
    try:
        if payload.mode == "infographic":
            result = await prompt_service.generate_for_infographic(
                reference_image_base64=payload.reference_image_base64,
                template_type=payload.template_type,
                product_keywords=payload.product_keywords,
            )
        elif payload.mode == "custom":
            result = await prompt_service.generate_for_custom(
                payload.prompt or "",
                negative_prompt=payload.negative_prompt,
            )
        else:  # competitor
            product_name = payload.product_name or "nano banana"
            result = await prompt_service.generate_for_competitor(
                reference_image_base64=payload.reference_image_base64 or "",
                template_type=payload.template_type,
                product_keywords=payload.product_keywords,
                product_name=product_name,
            )
    except PromptGenerationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    template = result.template or result.stored_template
    response = DesignPromptResponse(
        prompt=result.prompt,
        negative_prompt=result.negative_prompt,
        template_id=template.id if template else None,
        template_name=template.name if template else None,
        template_type=template.type if template else payload.template_type,
        preview_url=result.preview_url or (template.preview_url if template else None),
        warnings=result.warnings or [],
        stored_template_id=result.stored_template.id if result.stored_template else None,
        concept=result.concept,
        concept_raw=result.concept_raw,
    )
    return response
