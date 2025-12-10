from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from backend.models.token_purchase import TokenPurchaseRequest
from backend.models.user import User
from backend.models.admin import Admin
from backend.api.admin import get_current_admin

router = APIRouter(prefix="/admin/tokens", tags=["Admin Tokens"])


class TokenPurchaseRequestResponse(BaseModel):
    id: int
    user_id: int
    username: Optional[str]
    full_name: Optional[str]
    amount: int
    cost: float
    status: str
    payment_method: Optional[str]
    created_at: datetime
    processed_at: Optional[datetime]

    class Config:
        from_attributes = True


class ApproveTokenPurchase(BaseModel):
    payment_method: Optional[str] = None


@router.get("/purchases", response_model=List[TokenPurchaseRequestResponse])
async def get_token_purchases(
    status_filter: Optional[str] = None,
    _: Admin = Depends(get_current_admin)
):
    """Получение списка заявок на покупку токенов"""
    query = TokenPurchaseRequest.all().prefetch_related("user")
    
    if status_filter:
        query = query.filter(status=status_filter.upper())
    
    requests = await query.order_by("-created_at")
    
    return [
        TokenPurchaseRequestResponse(
            id=req.id,
            user_id=req.user.id,
            username=req.user.username,
            full_name=req.user.full_name,
            amount=req.amount,
            cost=float(req.cost),
            status=req.status,
            payment_method=req.payment_method,
            created_at=req.created_at,
            processed_at=req.processed_at
        )
        for req in requests
    ]


@router.post("/purchases/{purchase_id}/approve")
async def approve_token_purchase(
    purchase_id: int,
    data: ApproveTokenPurchase,
    _: Admin = Depends(get_current_admin)
):
    """Одобрение заявки на покупку токенов"""
    purchase = await TokenPurchaseRequest.filter(id=purchase_id).prefetch_related("user").first()
    
    if not purchase:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Заявка не найдена"
        )
    
    if purchase.status != "PENDING":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Заявка уже обработана"
        )
    
    # Начисляем токены пользователю (используем bonus_balance, так как он используется для списания)
    user = purchase.user
    user.bonus_balance += purchase.amount
    await user.save()
    
    # Обновляем статус заявки
    purchase.status = "APPROVED"
    purchase.processed_at = datetime.utcnow()
    if data.payment_method:
        purchase.payment_method = data.payment_method
    await purchase.save()
    
    return {
        "message": "Заявка одобрена",
        "user_id": user.id,
        "tokens_added": purchase.amount,
        "new_balance": user.bonus_balance
    }


@router.post("/purchases/{purchase_id}/reject")
async def reject_token_purchase(
    purchase_id: int,
    _: Admin = Depends(get_current_admin)
):
    """Отклонение заявки на покупку токенов"""
    purchase = await TokenPurchaseRequest.filter(id=purchase_id).first()
    
    if not purchase:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Заявка не найдена"
        )
    
    if purchase.status != "PENDING":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Заявка уже обработана"
        )
    
    purchase.status = "REJECTED"
    purchase.processed_at = datetime.utcnow()
    await purchase.save()
    
    return {"message": "Заявка отклонена"}


@router.put("/users/{user_id}/tokens")
async def update_user_tokens(
    user_id: int,
    tokens: int,
    _: Admin = Depends(get_current_admin)
):
    """Изменение баланса токенов пользователя"""
    user = await User.filter(id=user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    user.bonus_balance = tokens
    await user.save()
    
    return {
        "message": "Баланс токенов обновлен",
        "user_id": user.id,
        "new_balance": user.bonus_balance
    }

