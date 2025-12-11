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
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"[approve_token_purchase] Одобрение заявки {purchase_id}, payment_method={data.payment_method}")
        
        purchase = await TokenPurchaseRequest.filter(id=purchase_id).prefetch_related("user").first()
        
        if not purchase:
            logger.error(f"[approve_token_purchase] Заявка не найдена: {purchase_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Заявка не найдена"
            )
        
        if purchase.status != "PENDING":
            logger.warning(f"[approve_token_purchase] Заявка уже обработана: {purchase_id}, status={purchase.status}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Заявка уже обработана"
            )
        
        # Загружаем пользователя явно, если он не загружен
        if not purchase.user:
            await purchase.fetch_related("user")
        
        user = purchase.user
        if not user:
            logger.error(f"[approve_token_purchase] Пользователь не найден для заявки {purchase_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден"
            )
        
        old_balance = user.bonus_balance
        # Начисляем токены пользователю (используем bonus_balance, так как он используется для списания)
        user.bonus_balance += purchase.amount
        # Указываем update_fields для частичной модели
        await user.save(update_fields=['bonus_balance'])
        
        logger.info(f"[approve_token_purchase] Токены начислены: user_id={user.id}, amount={purchase.amount}, balance {old_balance} -> {user.bonus_balance}")
        
        # Обновляем статус заявки
        purchase.status = "APPROVED"
        purchase.processed_at = datetime.utcnow()
        if data.payment_method:
            purchase.payment_method = data.payment_method
        await purchase.save()
        
        logger.info(f"[approve_token_purchase] Заявка {purchase_id} успешно одобрена")
        
        return {
            "message": "Заявка одобрена",
            "user_id": user.id,
            "tokens_added": purchase.amount,
            "new_balance": user.bonus_balance
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[approve_token_purchase] Неожиданная ошибка: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при одобрении заявки: {str(e)}"
        )


@router.post("/purchases/{purchase_id}/reject")
async def reject_token_purchase(
    purchase_id: int,
    _: Admin = Depends(get_current_admin)
):
    """Отклонение заявки на покупку токенов"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"[reject_token_purchase] Отклонение заявки {purchase_id}")
        
        purchase = await TokenPurchaseRequest.filter(id=purchase_id).first()
        
        if not purchase:
            logger.error(f"[reject_token_purchase] Заявка не найдена: {purchase_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Заявка не найдена"
            )
        
        if purchase.status != "PENDING":
            logger.warning(f"[reject_token_purchase] Заявка уже обработана: {purchase_id}, status={purchase.status}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Заявка уже обработана"
            )
        
        purchase.status = "REJECTED"
        purchase.processed_at = datetime.utcnow()
        await purchase.save()
        
        logger.info(f"[reject_token_purchase] Заявка {purchase_id} успешно отклонена")
        
        return {"message": "Заявка отклонена"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[reject_token_purchase] Неожиданная ошибка: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при отклонении заявки: {str(e)}"
        )


@router.put("/users/{user_id}/tokens")
async def update_user_tokens(
    user_id: int,
    tokens: int,
    _: Admin = Depends(get_current_admin)
):
    """Изменение баланса токенов пользователя"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"[update_user_tokens] Обновление баланса пользователя {user_id}: {tokens}")
        
        user = await User.filter(id=user_id).first()
        
        if not user:
            logger.error(f"[update_user_tokens] Пользователь не найден: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден"
            )
        
        old_balance = user.bonus_balance
        user.bonus_balance = tokens
        # Указываем update_fields для частичной модели
        await user.save(update_fields=['bonus_balance'])
        
        logger.info(f"[update_user_tokens] Баланс обновлен: user_id={user.id}, balance {old_balance} -> {user.bonus_balance}")
        
        return {
            "message": "Баланс токенов обновлен",
            "user_id": user.id,
            "new_balance": user.bonus_balance
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[update_user_tokens] Неожиданная ошибка: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при обновлении баланса: {str(e)}"
        )

