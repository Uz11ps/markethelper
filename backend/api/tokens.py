from fastapi import APIRouter
from backend.schemas.token import (
    ChargeTokensRequest,
    ChargeTokensResponse,
    TokenPricingResponse
)
from backend.services.token_service import TokenService

router = APIRouter(prefix="/tokens", tags=["Tokens"])


@router.get("/pricing", response_model=TokenPricingResponse)
async def get_pricing():
    """Стоимость доступных действий"""
    pricing = await TokenService.get_pricing()
    return TokenPricingResponse(**pricing)


@router.post("/charge", response_model=ChargeTokensResponse)
async def charge_tokens(request: ChargeTokensRequest):
    """Списать токены у пользователя по действию"""
    result = await TokenService.charge(request.tg_id, request.action)
    return ChargeTokensResponse(**result)
