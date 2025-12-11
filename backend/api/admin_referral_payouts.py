from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from datetime import datetime
from backend.models import ReferralPayout, User, Admin
from backend.api.admin import get_current_admin

router = APIRouter(prefix="/admin/referral-payouts", tags=["Admin - Referral Payouts"])


class ApprovePayoutRequest(BaseModel):
    """Схема подтверждения выплаты"""
    comment: str | None = None


class RejectPayoutRequest(BaseModel):
    """Схема отклонения выплаты"""
    comment: str


@router.get("/")
async def list_payouts(admin: Admin = Depends(get_current_admin)):
    """Получить список всех заявок на выплату"""
    payouts = await ReferralPayout.all().prefetch_related("referrer", "processed_by").order_by("-created_at")
    
    return [
        {
            "id": p.id,
            "referrer_tg_id": p.referrer.tg_id,
            "referrer_username": p.referrer.username,
            "referrer_full_name": p.referrer.full_name,
            "referral_count": p.referral_count,
            "amount_rub": p.amount_rub,
            "status": p.status,
            "admin_comment": p.admin_comment,
            "processed_by": p.processed_by.username if p.processed_by else None,
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "processed_at": p.processed_at.isoformat() if p.processed_at else None,
        }
        for p in payouts
    ]


@router.post("/{payout_id}/approve")
async def approve_payout(
    payout_id: int,
    data: ApprovePayoutRequest,
    admin: Admin = Depends(get_current_admin)
):
    """Подтвердить выплату"""
    payout = await ReferralPayout.get_or_none(id=payout_id)
    if not payout:
        raise HTTPException(status_code=404, detail="Payout not found")
    
    if payout.status != "PENDING":
        raise HTTPException(status_code=400, detail="Payout is not pending")
    
    payout.status = "APPROVED"
    payout.processed_by = admin
    payout.processed_at = datetime.utcnow()
    if data.comment:
        payout.admin_comment = data.comment
    await payout.save()
    
    return {"message": "Payout approved", "payout_id": payout.id}


@router.post("/{payout_id}/reject")
async def reject_payout(
    payout_id: int,
    data: RejectPayoutRequest,
    admin: Admin = Depends(get_current_admin)
):
    """Отклонить выплату"""
    payout = await ReferralPayout.get_or_none(id=payout_id)
    if not payout:
        raise HTTPException(status_code=404, detail="Payout not found")
    
    if payout.status != "PENDING":
        raise HTTPException(status_code=400, detail="Payout is not pending")
    
    payout.status = "REJECTED"
    payout.processed_by = admin
    payout.processed_at = datetime.utcnow()
    payout.admin_comment = data.comment
    await payout.save()
    
    return {"message": "Payout rejected", "payout_id": payout.id}

