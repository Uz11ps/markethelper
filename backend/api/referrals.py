import os
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.models import User, Referral, ReferralPayout
from backend.services.settings_service import SettingsService

# Загружаем переменные окружения из .env
load_dotenv()

router = APIRouter(prefix="/referrals", tags=["Referrals"])

# Имя бота для реферальных ссылок (можно задать через переменную окружения)
BOT_USERNAME = os.getenv("BOT_USERNAME", "fghghhjgk_bot")


@router.post("/bind")
async def bind_referral(referred_tg: int, referrer_tg: int):
    """
    Привязка реферала при старте бота /start=REFERRER_ID
    """
    referred = await User.get_or_none(tg_id=referred_tg)
    referrer = await User.get_or_none(tg_id=referrer_tg)

    if not referred or not referrer:
        raise HTTPException(status_code=404, detail="User not found")
    if referred.id == referrer.id:
        raise HTTPException(status_code=400, detail="Self-referral not allowed")

    if referred.referrer_id:
        return {"message": "Already bound"}

    referred.referrer = referrer
    await referred.save()

    await Referral.create(referrer=referrer, referred=referred)
    return {"message": "Referral bound"}


@router.get("/{tg_id}/info")
async def get_referral_info(tg_id: int):
    """
    Возвращает реферальную ссылку, количество рефералов и информацию о выплатах
    """
    user = await User.get_or_none(tg_id=tg_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    ref_link = f"https://t.me/{BOT_USERNAME}?start=ref_{user.tg_id}"
    ref_count = await Referral.filter(referrer=user).count()
    
    # Получаем стоимость одного реферала в рублях
    rub_per_referral = await SettingsService.get_referral_rub_per_referral()
    total_rub = ref_count * rub_per_referral
    
    # Получаем информацию о выплатах
    pending_payouts = await ReferralPayout.filter(referrer=user, status="PENDING").all()
    total_pending_rub = sum(p.amount_rub for p in pending_payouts)
    total_pending_count = sum(p.referral_count for p in pending_payouts)
    
    approved_payouts = await ReferralPayout.filter(referrer=user, status="APPROVED").all()
    total_approved_rub = sum(p.amount_rub for p in approved_payouts)

    return {
        "ref_link": ref_link,
        "ref_count": ref_count,
        "rub_per_referral": rub_per_referral,
        "total_rub": total_rub,
        "pending_rub": total_pending_rub,
        "pending_count": total_pending_count,
        "approved_rub": total_approved_rub,
        "available_rub": total_rub - total_approved_rub - total_pending_rub
    }


@router.get("/{tg_id}/list")
async def list_referrals(tg_id: int):
    """
    Возвращает список всех рефералов пользователя
    """
    user = await User.get_or_none(tg_id=tg_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    referrals = await Referral.filter(referrer=user).prefetch_related("referred")

    return [
        {
            "username": r.referred.username,
            "full_name": r.referred.full_name,
            "activated": r.activated,
        }
        for r in referrals
    ]


class CreatePayoutRequest(BaseModel):
    """Схема создания заявки на выплату"""
    referral_count: int


@router.post("/{tg_id}/payout")
async def create_payout_request(tg_id: int, data: CreatePayoutRequest):
    """
    Создать заявку на выплату рублей за рефералов
    """
    user = await User.get_or_none(tg_id=tg_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if data.referral_count <= 0:
        raise HTTPException(status_code=400, detail="Referral count must be positive")
    
    # Проверяем что у пользователя есть столько рефералов
    total_referrals = await Referral.filter(referrer=user).count()
    if data.referral_count > total_referrals:
        raise HTTPException(status_code=400, detail="Not enough referrals")
    
    # Проверяем что нет активных заявок
    pending_payouts = await ReferralPayout.filter(referrer=user, status="PENDING").all()
    if pending_payouts:
        raise HTTPException(status_code=400, detail="You already have pending payout requests")
    
    # Получаем стоимость одного реферала
    rub_per_referral = await SettingsService.get_referral_rub_per_referral()
    amount_rub = data.referral_count * rub_per_referral
    
    # Создаем заявку
    payout = await ReferralPayout.create(
        referrer=user,
        referral_count=data.referral_count,
        amount_rub=amount_rub,
        status="PENDING"
    )
    
    return {
        "id": payout.id,
        "referral_count": payout.referral_count,
        "amount_rub": payout.amount_rub,
        "status": payout.status,
        "message": "Payout request created"
    }