from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.schemas.token import (
    ChargeTokensRequest,
    ChargeTokensResponse,
    TokenPricingResponse
)
from backend.services.token_service import TokenService
from backend.services.settings_service import SettingsService
from backend.models.token_purchase import TokenPurchaseRequest
from backend.models.user import User

router = APIRouter(prefix="/tokens", tags=["Tokens"])


class TokenPurchaseRequestCreate(BaseModel):
    tg_id: int
    amount: int
    cost: float


class TokenPurchaseRequestResponse(BaseModel):
    id: int
    message: str


@router.get("/pricing", response_model=TokenPricingResponse)
async def get_pricing():
    """Стоимость доступных действий"""
    pricing = await TokenService.get_pricing()
    return TokenPricingResponse(**pricing)


@router.get("/models")
async def get_image_models():
    """Получить список доступных моделей генерации изображений для пользователей"""
    models = await SettingsService.get_available_image_models()
    return models


@router.post("/charge", response_model=ChargeTokensResponse)
async def charge_tokens(request: ChargeTokensRequest):
    """Списать токены у пользователя по действию"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"[charge_tokens] Запрос на списание токенов: tg_id={request.tg_id}, action={request.action}")
        result = await TokenService.charge(request.tg_id, request.action)
        logger.info(f"[charge_tokens] Токены успешно списаны: {result}")
        return ChargeTokensResponse(**result)
    except HTTPException as e:
        # Передаем детали HTTPException как есть
        logger.warning(f"[charge_tokens] HTTPException: {e.status_code} - {e.detail}")
        raise
    except Exception as e:
        logger.error(f"[charge_tokens] Неожиданная ошибка: {e}", exc_info=True)
        # Включаем детали ошибки в ответ для отладки (в продакшене можно скрыть)
        import traceback
        error_detail = str(e)
        if logger.level <= logging.DEBUG:
            error_detail += f"\n{traceback.format_exc()}"
        raise HTTPException(status_code=500, detail=f"Ошибка при списании токенов: {error_detail}")


@router.post("/purchase", response_model=TokenPurchaseRequestResponse)
async def create_token_purchase_request(data: TokenPurchaseRequestCreate):
    """Создать заявку на пополнение токенов"""
    user = await User.get_or_none(tg_id=data.tg_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if data.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    
    if data.cost <= 0:
        raise HTTPException(status_code=400, detail="Cost must be positive")
    
    purchase = await TokenPurchaseRequest.create(
        user=user,
        amount=data.amount,
        cost=data.cost,
        status="PENDING"
    )
    
    return TokenPurchaseRequestResponse(
        id=purchase.id,
        message="Заявка на пополнение создана"
    )


@router.get("/topup-settings")
async def get_topup_settings():
    """Получить настройки пополнения баланса (для пользователей бота)"""
    token_price = await SettingsService.get_token_price()
    topup_options = await SettingsService.get_topup_options()
    return {
        "token_price": token_price,
        "topup_options": topup_options
    }
