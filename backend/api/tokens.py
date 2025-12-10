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
    result = await TokenService.charge(request.tg_id, request.action)
    return ChargeTokensResponse(**result)


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
