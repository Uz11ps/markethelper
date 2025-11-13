
from fastapi import APIRouter, HTTPException
from backend.models import User, Referral

router = APIRouter(prefix="/referrals", tags=["Referrals"])


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
    Возвращает реферальную ссылку и количество рефералов
    """
    user = await User.get_or_none(tg_id=tg_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    ref_link = f"https://t.me/trading_freee_bot?start=ref_{user.tg_id}"
    ref_count = await Referral.filter(referrer=user).count()

    return {"ref_link": ref_link, "ref_count": ref_count}


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