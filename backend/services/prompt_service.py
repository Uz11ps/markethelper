import base64
import binascii
import imghdr
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

from backend.models import DesignTemplate
from backend.services import ai_service, design_service

STATIC_DIR = Path("backend/static")
DESIGN_UPLOAD_DIR = STATIC_DIR / "designs"


@dataclass
class PromptGenerationResult:
    prompt: str
    negative_prompt: Optional[str] = None
    template: Optional[DesignTemplate] = None
    warnings: list[str] = field(default_factory=list)
    preview_url: Optional[str] = None
    stored_template: Optional[DesignTemplate] = None
    concept: Optional[dict[str, Any]] = None
    concept_raw: Optional[str] = None


class PromptGenerationError(RuntimeError):
    """Raised when prompt generation fails."""


def _ensure_static_dirs() -> None:
    """
    Makes sure that static folders required for uploads exist.
    """
    if not STATIC_DIR.exists():
        STATIC_DIR.mkdir(parents=True, exist_ok=True)
    if not DESIGN_UPLOAD_DIR.exists():
        DESIGN_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _strip_base64_header(data: str) -> tuple[str, Optional[str]]:
    """
    Removes data URI prefix and returns pure base64 string with detected extension.
    """
    if not data:
        raise PromptGenerationError("Пустые данные изображения.")

    extension = None
    payload = data.strip()

    if payload.startswith("data:"):
        header, _, encoded = payload.partition(",")
        if not encoded:
            raise PromptGenerationError("Некорректный data URI изображения.")
        payload = encoded
        if "image/" in header:
            try:
                extension = header.split("image/")[1].split(";")[0].strip() or None
            except IndexError:
                extension = None

    return payload, extension


def _decode_base64_image(data: str) -> tuple[bytes, str]:
    """
    Преобразует base64 строку в байты изображения и определяет расширение.
    """
    payload, ext_hint = _strip_base64_header(data)
    try:
        binary = base64.b64decode(payload, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise PromptGenerationError("Не удалось декодировать изображение.") from exc

    detected = imghdr.what(None, h=binary)
    extension = detected or ext_hint or "png"
    if extension == "jpeg":
        extension = "jpg"
    return binary, extension


def _save_reference_image(reference_base64: str, prefix: str = "design") -> str:
    """
    Сохраняет изображение на диск и возвращает относительный URL.
    """
    _ensure_static_dirs()
    binary, ext = _decode_base64_image(reference_base64)
    filename = f"{prefix}_{int(time.time())}_{uuid4().hex[:8]}.{ext}"
    path = DESIGN_UPLOAD_DIR / filename
    with path.open("wb") as fh:
        fh.write(binary)
    # FastAPI StaticFiles смонтирован на /static
    return f"/static/designs/{filename}"


async def _fetch_template(template_type: Optional[str], query: Optional[str]) -> Optional[DesignTemplate]:
    """
    Возвращает наиболее подходящий шаблон из базы, если таковой найден.
    """
    if not template_type:
        return None
    try:
        templates = await design_service.search_templates(
            template_type=template_type,
            query=query,
            limit=1,
        )
    except Exception:
        return None
    return templates[0] if templates else None


async def generate_for_infographic(
    *,
    reference_image_base64: Optional[str],
    template_type: Optional[str],
    product_keywords: Optional[str],
    fallback_prompt: Optional[str] = None,
) -> PromptGenerationResult:
    """
    Строит промпт для варианта «Инфографика».
    """
    warnings: list[str] = []

    template = await _fetch_template(template_type, product_keywords)
    template_prompt = template.prompt if template else None
    negative_prompt = template.negative_prompt if template and template.negative_prompt else None

    prompt_parts: list[str] = []
    if template_prompt:
        prompt_parts.append(template_prompt.strip())

    reference_result = None
    if reference_image_base64:
        try:
            reference_result = await ai_service.build_image_prompt_from_reference(
                user_prompt=product_keywords or "",
                reference_images_base64=[reference_image_base64],
            )
        except Exception as exc:
            warnings.append(f"Не удалось проанализировать изображение: {exc}")
    else:
        warnings.append("Референсное изображение не передано.")

    concept_data: Optional[dict[str, Any]] = None
    concept_raw: Optional[str] = None
    if reference_result and reference_result.prompt:
        prompt_parts.append(reference_result.prompt.strip())
        concept_data = reference_result.concept
        concept_raw = reference_result.raw_concept
    elif fallback_prompt:
        prompt_parts.append(fallback_prompt.strip())
    elif not template_prompt:
        subject = product_keywords or "marketplace product"
        prompt_parts.append(
            f"Create a clean marketplace infographic slide for {subject}. "
            "Use balanced composition, concise Russian captions, and ensure the product remains the main focus."
        )

    combined_prompt = "\n\n".join(part for part in prompt_parts if part)
    if not combined_prompt:
        raise PromptGenerationError("Не удалось построить промт для инфографики.")

    return PromptGenerationResult(
        prompt=combined_prompt,
        negative_prompt=negative_prompt,
        template=template,
        warnings=warnings,
        concept=concept_data,
        concept_raw=concept_raw,
    )


async def generate_for_custom(prompt: str, negative_prompt: Optional[str] = None) -> PromptGenerationResult:
    """
    Возвращает пользовательский промпт без изменений.
    """
    if not prompt or len(prompt.strip()) < 5:
        raise PromptGenerationError("Промпт должен содержать минимум 5 символов.")

    return PromptGenerationResult(
        prompt=prompt.strip(),
        negative_prompt=negative_prompt.strip() if negative_prompt else None,
    )


async def generate_for_competitor(
    *,
    reference_image_base64: str,
    template_type: Optional[str],
    product_keywords: Optional[str],
    product_name: str,
) -> PromptGenerationResult:
    """
    Строит промпт на основе карточки конкурента и сохраняет новый шаблон в базу.
    """
    if not reference_image_base64:
        raise PromptGenerationError("Нужно передать изображение конкурента.")

    user_prompt = (
        f"Brand/product: {product_name}. "
        "Create an engaging marketplace slide in Russian language following the style of the reference image. "
        "Highlight key benefits succinctly, keep layout balanced, and ensure the product feels premium."
    )
    if product_keywords:
        user_prompt += f" Keywords to consider: {product_keywords}."

    warnings: list[str] = []
    concept_data: Optional[dict[str, Any]] = None
    concept_raw: Optional[str] = None
    try:
        reference_result = await ai_service.build_image_prompt_from_reference(
            user_prompt=user_prompt,
            reference_images_base64=[reference_image_base64],
        )
        if reference_result:
            prompt_text = reference_result.prompt
            concept_data = reference_result.concept
            concept_raw = reference_result.raw_concept
        else:
            prompt_text = None
    except Exception as exc:
        warnings.append(f"Не удалось проанализировать изображение конкурента: {exc}")
        prompt_text = None
    if not prompt_text:
        warnings.append("Не удалось получить промпт по изображению конкурента, используем базовый вариант.")
        prompt_text = (
            f"Create a high-converting marketplace slide for product {product_name}. "
            "Replicate the layout and energy of the provided reference while adjusting colors and branding "
            "to match the new product. Keep all captions in Russian and emphasize trust-building badges."
        )

    preview_url = _save_reference_image(reference_image_base64, prefix="competitor")

    name_suffix = product_name or "Upload"
    template_name = f"Client reference — {name_suffix}"
    sections = [
        {
            "title": "Источник",
            "content": "Загружено клиентом для копирования дизайна конкурента.",
            "image_path": preview_url,
            "mode": "competitor",
        }
    ]

    stored_template = await design_service.create_template(
        name=template_name[:150],
        type=template_type or "competitor",
        theme_tags=product_keywords or "",
        prompt=prompt_text,
        sections=sections,
        preview_url=preview_url,
    )

    negative_prompt = None
    if stored_template and stored_template.negative_prompt:
        negative_prompt = stored_template.negative_prompt

    return PromptGenerationResult(
        prompt=prompt_text,
        negative_prompt=negative_prompt,
        warnings=warnings,
        preview_url=preview_url,
        stored_template=stored_template,
        concept=concept_data,
        concept_raw=concept_raw,
    )
