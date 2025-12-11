from fastapi import APIRouter, HTTPException, Query
from backend.schemas.user import ProfileOut, UserCreate
from backend.services.user_service import UserService
from typing import Optional

router = APIRouter(prefix="/profile", tags=["Profile"])


@router.get("/{tg_id}", response_model=ProfileOut)
async def get_profile(
    tg_id: int,
    username: Optional[str] = Query(None),
    full_name: Optional[str] = Query(None)
):
    """
    Профиль по tg_id — возвращает данные для бота.
    Автоматически создает пользователя, если его нет (если переданы username или full_name).
    """
    try:
        return await UserService.get_profile_by_tg(tg_id)
    except HTTPException as e:
        if e.status_code == 404 and (username is not None or full_name is not None):
            # Создаем пользователя, если его нет и переданы данные
            user_data = UserCreate(
                tg_id=tg_id,
                username=username,
                full_name=full_name
            )
            await UserService.create_user(user_data)
            # Повторно запрашиваем профиль
            return await UserService.get_profile_by_tg(tg_id)
        raise
