from fastapi import APIRouter, HTTPException, Query
from backend.schemas.user import ProfileOut, UserCreate
from backend.services.user_service import UserService
from typing import Optional
import logging

logger = logging.getLogger(__name__)

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
        logger.info(f"[get_profile] Запрос профиля для tg_id={tg_id}, username={username}, full_name={full_name}")
        return await UserService.get_profile_by_tg(tg_id)
    except HTTPException as e:
        logger.info(f"[get_profile] HTTPException: status={e.status_code}, detail={e.detail}")
        if e.status_code == 404 and (username is not None or full_name is not None):
            # Создаем пользователя, если его нет и переданы данные
            logger.info(f"[get_profile] Создаем пользователя tg_id={tg_id}")
            try:
                user_data = UserCreate(
                    tg_id=tg_id,
                    username=username,
                    full_name=full_name
                )
                created_user = await UserService.create_user(user_data)
                logger.info(f"[get_profile] Пользователь создан: {created_user}")
                # Повторно запрашиваем профиль
                return await UserService.get_profile_by_tg(tg_id)
            except Exception as create_error:
                logger.error(f"[get_profile] Ошибка при создании пользователя: {create_error}", exc_info=True)
                raise HTTPException(status_code=500, detail=f"Ошибка при создании пользователя: {str(create_error)}")
        raise
    except Exception as e:
        logger.error(f"[get_profile] Неожиданная ошибка: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")
