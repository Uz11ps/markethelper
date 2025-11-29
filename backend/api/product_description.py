import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, File, Form, UploadFile
from fastapi.security import HTTPBearer
import base64

from backend.schemas.product_description import (
    ProductDescriptionCreate,
    ProductDescriptionUpdate,
    ProductDescriptionResponse,
    GenerateProductDescriptionRequest,
    EditablePromptTemplateCreate,
    EditablePromptTemplateUpdate,
    EditablePromptTemplateResponse,
    InfographicProjectCreate,
    InfographicProjectUpdate,
    InfographicProjectResponse,
    EditPromptAreasRequest,
    GenerateInfographicRequest
)
from backend.models.product_description import ProductDescription, EditablePromptTemplate, InfographicProject
from backend.models.user import User
from backend.services import product_description_service
from backend.services.fal_service import fal_client, FalAIError

router = APIRouter(prefix="/product-description", tags=["Product Description"])
security = HTTPBearer()
logger = logging.getLogger("product_description_api")

async def get_current_user(token: str = Depends(security)) -> User:
    # TODO: Implement proper JWT token validation
    # For now, returning a dummy user - replace with actual auth logic
    user = await User.get_or_none(id=1)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

@router.post("/generate", response_model=dict)
async def generate_product_description(
    request: GenerateProductDescriptionRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Генерирует описание товара и 3 концепции на основе фотографий товара и референсов
    """
    try:
        result = await product_description_service.generate_product_description_with_concepts(
            user_id=current_user.id,
            product_images=request.product_images,
            reference_images=request.reference_images,
            title=request.title,
            user_prompt=request.user_prompt
        )
        return result
        
    except Exception as e:
        logger.error(f"Ошибка при генерации описания товара: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/auto-card")
async def auto_generate_card(
    request: GenerateProductDescriptionRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Принимает фото товара, описывает его через GPT и сразу запускает генерацию карточки в FAL.
    """
    try:
        result = await product_description_service.auto_generate_card_with_fal(
            user_id=current_user.id,
            product_images=request.product_images,
            reference_images=request.reference_images,
            title=request.title,
            user_prompt=request.user_prompt or "",
        )
        return result
    except FalAIError as exc:
        logger.error(f"FAL AI error: {exc}")
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.error(f"Ошибка при авто-генерации карточки: {exc}")
        raise HTTPException(status_code=500, detail="Не удалось создать карточку товара") from exc

@router.post("/upload-images")
async def upload_product_images(
    title: str = Form(...),
    user_prompt: str = Form(default=""),
    product_images: List[UploadFile] = File(...),
    reference_images: List[UploadFile] = File(default=[]),
    current_user: User = Depends(get_current_user)
):
    """
    Загружает изображения товара и референсов, генерирует описание
    """
    try:
        # Конвертируем загруженные файлы в base64
        product_images_b64 = []
        for img in product_images:
            content = await img.read()
            b64_string = base64.b64encode(content).decode('utf-8')
            product_images_b64.append(b64_string)
        
        reference_images_b64 = []
        for img in reference_images:
            content = await img.read()
            b64_string = base64.b64encode(content).decode('utf-8')
            reference_images_b64.append(b64_string)
        
        result = await product_description_service.generate_product_description_with_concepts(
            user_id=current_user.id,
            product_images=product_images_b64,
            reference_images=reference_images_b64,
            title=title,
            user_prompt=user_prompt
        )
        return result
        
    except Exception as e:
        logger.error(f"Ошибка при загрузке и обработке изображений: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[ProductDescriptionResponse])
async def get_product_descriptions(
    current_user: User = Depends(get_current_user)
):
    """
    Получает все описания товаров для текущего пользователя
    """
    try:
        descriptions = await product_description_service.get_product_descriptions_for_user(current_user.id)
        
        result = []
        for desc in descriptions:
            result.append(ProductDescriptionResponse(
                id=desc.id,
                title=desc.title,
                description=desc.description,
                product_images=desc.product_images,
                reference_images=desc.reference_images,
                generated_concepts=desc.generated_concepts,
                selected_concept_index=desc.selected_concept_index,
                editable_prompt_areas=desc.editable_prompt_areas,
                final_prompt=desc.final_prompt,
                created_at=desc.created_at.isoformat(),
                updated_at=desc.updated_at.isoformat()
            ))
        
        return result
        
    except Exception as e:
        logger.error(f"Ошибка при получении описаний товаров: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{description_id}", response_model=ProductDescriptionResponse)
async def get_product_description(
    description_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    Получает конкретное описание товара
    """
    try:
        desc = await ProductDescription.get_or_none(id=description_id, user_id=current_user.id)
        if not desc:
            raise HTTPException(status_code=404, detail="Описание товара не найдено")
        
        return ProductDescriptionResponse(
            id=desc.id,
            title=desc.title,
            description=desc.description,
            product_images=desc.product_images,
            reference_images=desc.reference_images,
            generated_concepts=desc.generated_concepts,
            selected_concept_index=desc.selected_concept_index,
            editable_prompt_areas=desc.editable_prompt_areas,
            final_prompt=desc.final_prompt,
            created_at=desc.created_at.isoformat(),
            updated_at=desc.updated_at.isoformat()
        )
        
    except Exception as e:
        logger.error(f"Ошибка при получении описания товара: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{description_id}/edit-prompt-areas")
async def edit_prompt_areas(
    description_id: int,
    request: EditPromptAreasRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Редактирует области промта (иконки, цвета, расположение)
    """
    try:
        result = await product_description_service.update_editable_prompt_areas(
            product_description_id=description_id,
            user_id=current_user.id,
            icon_edits=request.icon_edits,
            color_edits=request.color_edits,
            layout_edits=request.layout_edits
        )
        return result
        
    except Exception as e:
        logger.error(f"Ошибка при редактировании областей промта: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{description_id}/generate-final-prompt")
async def generate_final_prompt(
    description_id: int,
    concept_index: int,
    custom_edits: dict = None,
    current_user: User = Depends(get_current_user)
):
    """
    Генерирует финальный промт на основе выбранной концепции и редактирований
    """
    try:
        final_prompt = await product_description_service.generate_final_prompt_from_concept(
            product_description_id=description_id,
            user_id=current_user.id,
            concept_index=concept_index,
            custom_edits=custom_edits
        )
        
        return {
            "status": "success",
            "final_prompt": final_prompt,
            "concept_index": concept_index
        }
        
    except Exception as e:
        logger.error(f"Ошибка при генерации финального промта: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Проекты инфографики
@router.post("/infographic-projects", response_model=dict)
async def create_infographic_project(
    request: InfographicProjectCreate,
    current_user: User = Depends(get_current_user)
):
    """
    Создает новый проект инфографики
    """
    try:
        project = await product_description_service.create_infographic_project(
            user_id=current_user.id,
            project_type=request.project_type,
            title=request.title,
            product_description_id=request.product_description_id,
            generation_settings=request.generation_settings
        )
        
        return {
            "status": "success",
            "project_id": project.id,
            "message": "Проект инфографики создан"
        }
        
    except Exception as e:
        logger.error(f"Ошибка при создании проекта инфографики: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/infographic-projects", response_model=List[InfographicProjectResponse])
async def get_infographic_projects(
    current_user: User = Depends(get_current_user)
):
    """
    Получает все проекты инфографики для пользователя
    """
    try:
        projects = await product_description_service.get_infographic_projects_for_user(current_user.id)
        
        result = []
        for proj in projects:
            result.append(InfographicProjectResponse(
                id=proj.id,
                project_type=proj.project_type,
                title=proj.title,
                status=proj.status,
                generated_images=proj.generated_images,
                selected_image_url=proj.selected_image_url,
                generation_settings=proj.generation_settings,
                created_at=proj.created_at.isoformat(),
                updated_at=proj.updated_at.isoformat()
            ))
        
        return result
        
    except Exception as e:
        logger.error(f"Ошибка при получении проектов инфографики: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/infographic-projects/{project_id}/generate")
async def generate_infographic(
    project_id: int,
    request: GenerateInfographicRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Генерирует инфографику для проекта
    """
    try:
        # Получаем проект
        project = await InfographicProject.get_or_none(
            id=project_id, 
            user_id=current_user.id
        )
        if not project:
            raise HTTPException(status_code=404, detail="Проект не найден")
        
        # Получаем описание товара если есть
        if project.product_description_id:
            product_desc = await ProductDescription.get_or_none(
                id=project.product_description_id,
                user_id=current_user.id
            )
            if not product_desc:
                raise HTTPException(status_code=404, detail="Описание товара не найдено")
                
            # Генерируем финальный промт
            final_prompt = await product_description_service.generate_final_prompt_from_concept(
                product_description_id=product_desc.id,
                user_id=current_user.id,
                concept_index=request.concept_index,
                custom_edits=request.custom_prompt_edits
            )
            
            # Генерируем изображение через FAL AI
            try:
                generation_result = await fal_client.generate_image(
                    prompt=final_prompt,
                    **project.generation_settings
                )
                
                # Обновляем проект
                project.generated_images = generation_result.get('images', [])
                project.status = "generated"
                await project.save()
                
                return {
                    "status": "success",
                    "project_id": project.id,
                    "generated_images": project.generated_images,
                    "final_prompt": final_prompt
                }
                
            except FalAIError as e:
                raise HTTPException(status_code=502, detail=f"Ошибка генерации: {str(e)}")
        
        else:
            raise HTTPException(status_code=400, detail="Проект не связан с описанием товара")
            
    except Exception as e:
        logger.error(f"Ошибка при генерации инфографики: {e}")
        raise HTTPException(status_code=500, detail=str(e))
