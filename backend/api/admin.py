from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List

from backend.schemas.admin import (
    AdminCreate,
    AdminLogin,
    AdminResponse,
    AdminUpdate,
    Token
)
from backend.services.admin_service import AdminService
from backend.models.admin import Admin

router = APIRouter(prefix="/admin", tags=["Admin"])
security = HTTPBearer()


async def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Admin:
    """Dependency для получения текущего админа"""
    token = credentials.credentials
    return await AdminService.get_current_admin(token)


async def require_super_admin(
    admin: Admin = Depends(get_current_admin)
) -> Admin:
    """Dependency для проверки прав суперадмина"""
    if not admin.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin rights required"
        )
    return admin


@router.post("/register", response_model=AdminResponse)
async def register_admin(
    data: AdminCreate,
    _: Admin = Depends(require_super_admin)
):
    """Регистрация нового администратора (только для суперадмина)"""
    admin = await AdminService.create_admin(data)
    return admin


@router.post("/login", response_model=Token)
async def login(data: AdminLogin):
    """Вход администратора"""
    admin = await AdminService.authenticate(data.username, data.password)

    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    access_token = AdminService.create_access_token(admin.id)
    return Token(access_token=access_token)


@router.get("/me", response_model=AdminResponse)
async def get_me(admin: Admin = Depends(get_current_admin)):
    """Получение данных текущего администратора"""
    return admin


@router.get("/all", response_model=List[AdminResponse])
async def get_all_admins(_: Admin = Depends(require_super_admin)):
    """Получение списка всех администраторов (только для суперадмина)"""
    admins = await AdminService.get_all_admins()
    return admins


# ВАЖНО: Маршрут с параметром должен быть ПОСЛЕДНИМ, чтобы не перехватывать специфичные маршруты
# (например, /admin/groups не должен попадать в /admin/{admin_id})
@router.get("/{admin_id}", response_model=AdminResponse)
async def get_admin(
    admin_id: int,
    _: Admin = Depends(get_current_admin)
):
    """Получение администратора по ID"""
    admin = await AdminService.get_admin_by_id(admin_id)
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin not found"
        )
    return admin


@router.put("/{admin_id}", response_model=AdminResponse)
async def update_admin(
    admin_id: int,
    data: AdminUpdate,
    current_admin: Admin = Depends(get_current_admin)
):
    """Обновление данных администратора"""
    # Админ может редактировать только себя, суперадмин - всех
    if admin_id != current_admin.id and not current_admin.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    admin = await AdminService.update_admin(admin_id, data)
    return admin


@router.delete("/{admin_id}")
async def delete_admin(
    admin_id: int,
    _: Admin = Depends(require_super_admin)
):
    """Удаление администратора (только для суперадмина)"""
    await AdminService.delete_admin(admin_id)
    return {"message": "Admin deleted successfully"}
