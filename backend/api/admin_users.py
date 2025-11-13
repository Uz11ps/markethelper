from fastapi import APIRouter, Depends, Query
from typing import List, Optional

from backend.models.user import User
from backend.models.admin import Admin
from backend.api.admin import get_current_admin
from backend.schemas.user import UserResponse

router = APIRouter(prefix="/admin/users", tags=["Admin Users"])


@router.get("/", response_model=List[UserResponse])
async def get_all_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    _: Admin = Depends(get_current_admin)
):
    """Получение списка всех пользователей с пагинацией и поиском"""
    query = User.all()

    if search:
        query = query.filter(
            username__icontains=search
        ) | query.filter(
            full_name__icontains=search
        )

    users = await query.offset(skip).limit(limit)
    return users


@router.get("/stats")
async def get_users_stats(_: Admin = Depends(get_current_admin)):
    """Получение статистики по пользователям"""
    total_users = await User.all().count()
    users_with_referrals = await User.filter(referrer__isnull=False).count()
    total_bonus_balance = await User.all().values_list("bonus_balance", flat=True)

    return {
        "total_users": total_users,
        "users_with_referrals": users_with_referrals,
        "total_bonus_distributed": sum(total_bonus_balance) if total_bonus_balance else 0
    }


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_details(
    user_id: int,
    _: Admin = Depends(get_current_admin)
):
    """Получение детальной информации о пользователе"""
    user = await User.filter(id=user_id).first()
    if not user:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.put("/{user_id}/bonus")
async def update_user_bonus(
    user_id: int,
    bonus_amount: int,
    _: Admin = Depends(get_current_admin)
):
    """Изменение бонусного баланса пользователя"""
    user = await User.filter(id=user_id).first()
    if not user:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    user.bonus_balance = bonus_amount
    await user.save()

    return {"message": "Bonus updated successfully", "new_balance": user.bonus_balance}


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    _: Admin = Depends(get_current_admin)
):
    """Удаление пользователя"""
    user = await User.filter(id=user_id).first()
    if not user:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    await user.delete()
    return {"message": "User deleted successfully"}
