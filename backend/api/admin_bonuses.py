from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List
from datetime import datetime

from backend.models.pending_bonus import PendingBonus
from backend.models.admin import Admin
from backend.api.admin import get_current_admin
from backend.models.user import User
import httpx

router = APIRouter(prefix="/admin/bonuses", tags=["Admin Bonuses"])

BOT_URL = "http://bot:8001/notify"


async def notify_user(tg_id: int, message: str):
    async with httpx.AsyncClient() as client:
        try:
            await client.post(BOT_URL, json={"tg_id": tg_id, "message": message})
        except Exception as e:
            print(f"⚠ Ошибка при отправке уведомления: {e}")


@router.get("/pending", response_model=List[dict])
async def list_pending_bonuses(admin: Admin = Depends(get_current_admin)):
    """Получить список ожидающих подтверждения реферальных бонусов"""
    pending_bonuses = await PendingBonus.filter(status="pending").prefetch_related(
        "referrer", "referred", "referral", "request"
    )
    
    result = []
    for bonus in pending_bonuses:
        result.append({
            "id": bonus.id,
            "referrer_id": bonus.referrer.id,
            "referrer_tg_id": bonus.referrer.tg_id,
            "referrer_username": bonus.referrer.username,
            "referred_id": bonus.referred.id,
            "referred_tg_id": bonus.referred.tg_id,
            "referred_username": bonus.referred.username,
            "bonus_amount": bonus.bonus_amount,
            "status": bonus.status,
            "request_id": bonus.request.id if bonus.request else None,
            "created_at": bonus.created_at.isoformat() if bonus.created_at else None,
        })
    
    return result


@router.post("/{bonus_id}/approve")
async def approve_bonus(
    bonus_id: int,
    admin: Admin = Depends(get_current_admin)
):
    """Подтвердить и начислить реферальный бонус"""
    bonus = await PendingBonus.filter(id=bonus_id).prefetch_related(
        "referrer", "referred", "referral"
    ).first()
    
    if not bonus:
        raise HTTPException(status_code=404, detail="Бонус не найден")
    
    if bonus.status != "pending":
        raise HTTPException(status_code=400, detail=f"Бонус уже обработан (статус: {bonus.status})")
    
    # Начисляем бонус
    referrer = await bonus.referrer
    referrer.bonus_balance += bonus.bonus_amount
    await referrer.save()
    
    # Обновляем статус бонуса
    bonus.status = "approved"
    bonus.approved_at = datetime.utcnow()
    bonus.approved_by = admin
    await bonus.save()
    
    # Уведомляем реферера
    await notify_user(
        referrer.tg_id,
        f"🎉 Ваш реферал @{bonus.referred.username} активировал подписку! "
        f"Вам начислено +{bonus.bonus_amount} бонусов на баланс."
    )
    
    return {
        "message": "Бонус успешно начислен",
        "bonus_id": bonus.id,
        "referrer_id": referrer.id,
        "bonus_amount": bonus.bonus_amount,
        "new_balance": referrer.bonus_balance
    }


@router.post("/{bonus_id}/reject")
async def reject_bonus(
    bonus_id: int,
    admin: Admin = Depends(get_current_admin)
):
    """Отклонить реферальный бонус"""
    bonus = await PendingBonus.filter(id=bonus_id).prefetch_related(
        "referrer", "referred"
    ).first()
    
    if not bonus:
        raise HTTPException(status_code=404, detail="Бонус не найден")
    
    if bonus.status != "pending":
        raise HTTPException(status_code=400, detail=f"Бонус уже обработан (статус: {bonus.status})")
    
    # Обновляем статус бонуса
    bonus.status = "rejected"
    bonus.approved_at = datetime.utcnow()
    bonus.approved_by = admin
    await bonus.save()
    
    return {
        "message": "Бонус отклонен",
        "bonus_id": bonus.id
    }

