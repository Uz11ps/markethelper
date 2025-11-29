import logging
import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

from openai import AsyncOpenAI
from dotenv import load_dotenv

from backend.models.product_description import (
    ProductDescription,
    EditablePromptTemplate,
    InfographicProject,
)
from backend.models.user import User
from backend.services import ai_service
from backend.services.fal_service import fal_client

load_dotenv()

logger = logging.getLogger("product_description_service")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if OPENAI_API_KEY:
    client_openai = AsyncOpenAI(api_key=OPENAI_API_KEY)
else:
    client_openai = None
    logger.warning("OPENAI_API_KEY is not set. Product description features will be unavailable.")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROMPT_FILE_PATH = PROJECT_ROOT / "промт (генерация по товару.txt"
_PROMPT_CACHE: Optional[str] = None


class ConceptParseError(ValueError):
    """
    Возникает при невозможности распарсить ответ GPT в ожидаемый JSON.
    """

    def __init__(self, message: str, raw_response: str):
        super().__init__(message)
        self.raw_response = raw_response


def _load_prompt_template() -> str:
    global _PROMPT_CACHE
    if _PROMPT_CACHE:
        return _PROMPT_CACHE
    if not PROMPT_FILE_PATH.exists():
        raise FileNotFoundError(f"Prompt file not found: {PROMPT_FILE_PATH}")
    _PROMPT_CACHE = PROMPT_FILE_PATH.read_text(encoding="utf-8")
    return _PROMPT_CACHE

def _guess_mime_type(b64_data: str) -> str:
    if b64_data.startswith("iVBOR"):
        return "image/png"
    if b64_data.startswith("/9j/"):
        return "image/jpeg"
    if b64_data.startswith("R0lGOD"):
        return "image/gif"
    return "image/jpeg"


def _normalize_model_response(result_text: str) -> str:
    """
    Удаляет Markdown-обёртки ```json и возвращает чистый текст ответа модели.
    """
    normalized = (result_text or "").strip()
    if normalized.startswith("```"):
        parts = normalized.split("\n")
        if len(parts) > 2:
            normalized = "\n".join(parts[1:-1])
        normalized = normalized.strip("` \n")
    return normalized.strip()


def _parse_concepts(raw_text: str) -> List[Dict[str, Any]]:
    """
    Превращает строку JSON в список концепций и валидирует размер.
    """
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise ConceptParseError("Не удалось распознать ответ от AI", raw_text) from exc

    if not isinstance(data, list):
        raise ConceptParseError("Ответ должен содержать массив концепций", raw_text)
    if len(data) != 3:
        raise ConceptParseError("Ответ должен содержать массив из 3 концепций", raw_text)
    return data


def _build_concept_messages(
    product_images: List[str],
    reference_images: Optional[List[str]],
    title: str,
    user_prompt: str,
) -> List[Dict[str, Any]]:
    """
    Формирует контент для мультимодального запроса в GPT.
    """
    base_prompt = _load_prompt_template()
    content: List[Dict[str, Any]] = [{"type": "text", "text": base_prompt}]

    clean_prompt = user_prompt.strip()
    if clean_prompt:
        content.append({"type": "text", "text": f"Дополнительное требование: {clean_prompt}"})

    title_clean = title.strip()
    if title_clean:
        content.append({"type": "text", "text": f"Название товара: {title_clean}"})

    for idx, img_b64 in enumerate(product_images, 1):
        mime = _guess_mime_type(img_b64)
        data_uri = f"data:{mime};base64,{img_b64}"
        content.append({"type": "text", "text": f"Изображение товара {idx}:"})
        content.append({"type": "image_url", "image_url": {"url": data_uri}})

    for idx, img_b64 in enumerate(reference_images or [], 1):
        mime = _guess_mime_type(img_b64)
        data_uri = f"data:{mime};base64,{img_b64}"
        content.append({"type": "text", "text": f"Референсное изображение {idx}:"})
        content.append({"type": "image_url", "image_url": {"url": data_uri}})

    return content


async def _request_concepts_raw(
    *,
    product_images: List[str],
    reference_images: Optional[List[str]],
    title: str,
    user_prompt: str,
) -> str:
    """
    Отправляет запрос в OpenAI и возвращает необработанный текст ответа.
    """
    if not client_openai:
        raise ValueError("OpenAI API не настроен")

    content = _build_concept_messages(product_images, reference_images, title, user_prompt)

    response = await client_openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "Ты — мультимодальный ИИ-ассистент для генерации концепций инфографики маркетплейсов.",
            },
            {"role": "user", "content": content},
        ],
        temperature=0.7,
    )

    if not response.choices:
        raise RuntimeError("OpenAI вернул пустой ответ")

    result_text = response.choices[0].message.content or ""
    return _normalize_model_response(result_text)


def _build_final_prompt(
    concept: Dict[str, Any],
    *,
    image_analysis: Optional[str] = None,
) -> str:
    """
    Собирает финальный текстовый промпт из концепции и доп.анализа товара.
    """
    offers = concept.get("💥 Офферы", [])
    offer_lines = "\n".join(f"• {offer}" for offer in offers) if offers else ""
    size = concept.get("rekomenduemiy_razmer", {}) or {}
    width = size.get("width", 1080)
    height = size.get("height", 1080)

    parts = [
        "## ИНФОГРАФИКА ДЛЯ МАРКЕТПЛЕЙСА",
        f"**Концепция:** {concept.get('concept_name', 'Без названия')}",
        f"**Описание стиля:** {concept.get('🔍 Описание', '')}",
        f"**Товар и использование:** {concept.get('📍 Использование товара', '')}",
        f"**Фон:** {concept.get('🏞️ Фон', '')}",
        f"**Заголовок:** {concept.get('🏷️ Заголовок', '')}",
        "**Ключевые преимущества:**",
        offer_lines or "• —",
        f"**Стиль текста:** {concept.get('🖋️ Стиль текста', '')}",
        f"**Иконки:** {concept.get('🖌️ Стиль иконок', '')} - {concept.get('🧩 Расположение иконок', '')}",
        f"**Цветовая палитра:** {concept.get('cvetovaya_palitra', '')}",
        f"**Размер:** {width}x{height}",
        f"**Тип макета:** {concept.get('tip_maketa', 'standart_1')}",
    ]

    analysis_text = (image_analysis or "").strip()
    if analysis_text:
        parts.append("")
        parts.append("**Анализ товара (GPT):**")
        parts.append(analysis_text)

    return "\n".join(parts).strip()

async def generate_product_description_with_concepts(
    user_id: int,
    product_images: List[str], 
    reference_images: Optional[List[str]] = None,
    title: str = "",
    user_prompt: str = ""
) -> Dict[str, Any]:
    """
    Генерирует описание товара и 3 концепции на основе фотографий товара и референсов.
    """
    reference_images = reference_images or []

    try:
        raw_response = await _request_concepts_raw(
            product_images=product_images,
            reference_images=reference_images,
            title=title,
            user_prompt=user_prompt,
        )
        concepts = _parse_concepts(raw_response)
        logger.info("Получен ответ от OpenAI для описания товара")
    except ConceptParseError as exc:
        logger.error("Не удалось парсить JSON ответ от OpenAI")
        return {
            "status": "error",
            "message": str(exc),
            "raw_response": exc.raw_response,
        }
    except Exception as e:
        logger.error(f"Ошибка при обращении к OpenAI: {e}")
        raise

    product_desc = await ProductDescription.create(
        user_id=user_id,
        title=title,
        description=f"Автоматически сгенерированное описание для {title}",
        product_images=product_images,
        reference_images=reference_images,
        generated_concepts=concepts,
        editable_prompt_areas={
            "icons": {},
            "colors": {},
            "layout": {}
        }
    )

    return {
        "status": "success",
        "product_description_id": product_desc.id,
        "concepts": concepts,
        "message": "Концепции успешно созданы"
    }

async def update_editable_prompt_areas(
    product_description_id: int,
    user_id: int,
    icon_edits: Dict[str, str],
    color_edits: Dict[str, str],
    layout_edits: Dict[str, str]
) -> Dict[str, Any]:
    """
    Обновляет редактируемые области промта
    """
    try:
        product_desc = await ProductDescription.get(
            id=product_description_id, 
            user_id=user_id
        )
        
        # Обновляем области
        editable_areas = product_desc.editable_prompt_areas or {}
        editable_areas.update({
            "icons": {**editable_areas.get("icons", {}), **icon_edits},
            "colors": {**editable_areas.get("colors", {}), **color_edits},
            "layout": {**editable_areas.get("layout", {}), **layout_edits}
        })
        
        product_desc.editable_prompt_areas = editable_areas
        await product_desc.save()
        
        return {
            "status": "success",
            "message": "Области редактирования обновлены",
            "editable_areas": editable_areas
        }
        
    except Exception as e:
        logger.error(f"Ошибка при обновлении областей: {e}")
        raise

async def generate_final_prompt_from_concept(
    product_description_id: int,
    user_id: int,
    concept_index: int,
    custom_edits: Optional[Dict[str, Any]] = None
) -> str:
    """
    Генерирует финальный промт на основе выбранной концепции и редактирований
    """
    try:
        product_desc = await ProductDescription.get(
            id=product_description_id, 
            user_id=user_id
        )
        
        if not product_desc.generated_concepts:
            raise ValueError("Концепции не найдены")
            
        if concept_index >= len(product_desc.generated_concepts):
            raise ValueError("Неверный индекс концепции")
            
        concept = product_desc.generated_concepts[concept_index]
        custom_edits = custom_edits or {}
        editable_areas = product_desc.editable_prompt_areas or {}
        
        # Применяем редактирования к концепции
        if custom_edits.get("icons") or editable_areas.get("icons"):
            icon_edits = {**editable_areas.get("icons", {}), **custom_edits.get("icons", {})}
            concept["🖌️ Стиль иконок"] = icon_edits.get("style", concept.get("🖌️ Стиль иконок", ""))
            concept["🧩 Расположение иконок"] = icon_edits.get("layout", concept.get("🧩 Расположение иконок", ""))
        
        if custom_edits.get("colors") or editable_areas.get("colors"):
            color_edits = {**editable_areas.get("colors", {}), **custom_edits.get("colors", {})}
            concept["cvetovaya_palitra"] = color_edits.get("palette", concept.get("cvetovaya_palitra", ""))
        
        if custom_edits.get("layout") or editable_areas.get("layout"):
            layout_edits = {**editable_areas.get("layout", {}), **custom_edits.get("layout", {})}
            concept["🏞️ Фон"] = layout_edits.get("background", concept.get("🏞️ Фон", ""))
        
        final_prompt = _build_final_prompt(concept)

        # Сохраняем финальный промт
        product_desc.selected_concept_index = concept_index
        product_desc.final_prompt = final_prompt
        await product_desc.save()
        
        return final_prompt
        
    except Exception as e:
        logger.error(f"Ошибка при генерации финального промта: {e}")
        raise


async def auto_generate_card_with_fal(
    *,
    user_id: int,
    product_images: List[str],
    reference_images: Optional[List[str]] = None,
    title: str = "",
    user_prompt: str = "",
) -> Dict[str, Any]:
    """
    Полный конвейер: GPT описывает товар, строит концепции по шаблону и отправляет финальный промт в FAL.
    """
    if not product_images:
        raise ValueError("Нужно передать хотя бы одно изображение товара.")

    reference_images = reference_images or []

    analysis = await ai_service.describe_product_images(
        product_images_base64=product_images,
        max_items=3,
    )

    prompt_parts: List[str] = []
    user_prompt_clean = (user_prompt or "").strip()
    if user_prompt_clean:
        prompt_parts.append(user_prompt_clean)
    if analysis:
        prompt_parts.append(f"Автоматический анализ товара:\n{analysis}")
    combined_prompt = "\n\n".join(prompt_parts)

    raw_response = await _request_concepts_raw(
        product_images=product_images,
        reference_images=reference_images,
        title=title or "Auto marketplace card",
        user_prompt=combined_prompt,
    )
    concepts = _parse_concepts(raw_response)
    concept = concepts[0]

    final_prompt = _build_final_prompt(concept, image_analysis=analysis)

    reference_payload: List[str] = []
    reference_payload.extend(product_images)
    if reference_images:
        reference_payload.extend(reference_images)

    fal_result = await fal_client.generate_image(
        prompt=final_prompt,
        reference_images_base64=reference_payload or None,
        product_image_count=len(product_images),
    )

    return {
        "status": "success",
        "user_id": user_id,
        "image_description": analysis,
        "final_prompt": final_prompt,
        "concept": concept,
        "concepts": concepts,
        "fal_result": fal_result,
    }

async def create_infographic_project(
    user_id: int,
    project_type: str,  # "product" or "reference"
    title: str,
    product_description_id: Optional[int] = None,
    generation_settings: Optional[Dict[str, Any]] = None
) -> InfographicProject:
    """
    Создает новый проект инфографики
    """
    try:
        project = await InfographicProject.create(
            user_id=user_id,
            project_type=project_type,
            title=title,
            product_description_id=product_description_id,
            generation_settings=generation_settings or {},
            status="draft"
        )
        
        return project
        
    except Exception as e:
        logger.error(f"Ошибка при создании проекта инфографики: {e}")
        raise

async def get_product_descriptions_for_user(user_id: int) -> List[ProductDescription]:
    """
    Получает все описания товаров для пользователя
    """
    try:
        descriptions = await ProductDescription.filter(user_id=user_id).all()
        return descriptions
        
    except Exception as e:
        logger.error(f"Ошибка при получении описаний товаров: {e}")
        raise

async def get_infographic_projects_for_user(user_id: int) -> List[InfographicProject]:
    """
    Получает все проекты инфографики для пользователя
    """
    try:
        projects = await InfographicProject.filter(user_id=user_id).prefetch_related("product_description").all()
        return projects
        
    except Exception as e:
        logger.error(f"Ошибка при получении проектов инфографики: {e}")
        raise
