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


# ВАЖНО: Маршруты с параметрами должны быть ПОСЛЕДНИМИ в файле,
# чтобы не перехватывать специфичные маршруты из других роутеров
# (например, /admin/groups не должен попадать в /admin/{admin_id})
# Но порядок регистрации роутеров в app.py также важен!
# Используем str для проверки зарезервированных путей
# ВАЖНО: Этот маршрут должен быть ПОСЛЕДНИМ в роутере, чтобы не перехватывать специфичные маршруты
@router.get("/{admin_id}", response_model=AdminResponse)
async def get_admin(
    admin_id: str,
    _: Admin = Depends(get_current_admin)
):
    """Получение администратора по ID"""
    # Проверяем, что это не зарезервированное слово
    # Если это зарезервированный путь, возвращаем 404, чтобы FastAPI мог проверить другие роутеры
    reserved_paths = ["groups", "users", "settings", "tokens", "subscriptions", "bonuses", "requests", "files", "me", "all", "login", "register"]
    if admin_id in reserved_paths:
        # Возвращаем 404, чтобы указать, что этот маршрут не подходит
        # FastAPI должен проверить другие роутеры
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Route '{admin_id}' is reserved and should be handled by a specific router"
        )
    
    # Пытаемся преобразовать в int
    try:
        admin_id_int = int(admin_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin not found"
        )
    
    admin = await AdminService.get_admin_by_id(admin_id_int)
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin not found"
        )
    return admin


@router.put("/{admin_id}", response_model=AdminResponse)
async def update_admin(
    admin_id: str,
    data: AdminUpdate,
    current_admin: Admin = Depends(get_current_admin)
):
    """Обновление данных администратора"""
    # Проверяем, что это не зарезервированное слово
    reserved_paths = ["groups", "users", "settings", "tokens", "subscriptions", "bonuses", "requests", "files", "me", "all", "login", "register"]
    if admin_id in reserved_paths:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin not found"
        )
    
    # Пытаемся преобразовать в int
    try:
        admin_id_int = int(admin_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin not found"
        )
    
    # Админ может редактировать только себя, суперадмин - всех
    if admin_id_int != current_admin.id and not current_admin.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    admin = await AdminService.update_admin(admin_id_int, data)
    return admin


@router.delete("/{admin_id}")
async def delete_admin(
    admin_id: str,
    _: Admin = Depends(require_super_admin)
):
    """Удаление администратора (только для суперадмина)"""
    # Проверяем, что это не зарезервированное слово
    reserved_paths = ["groups", "users", "settings", "tokens", "subscriptions", "bonuses", "requests", "files", "me", "all", "login", "register"]
    if admin_id in reserved_paths:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin not found"
        )
    
    # Пытаемся преобразовать в int
    try:
        admin_id_int = int(admin_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin not found"
        )
    
    await AdminService.delete_admin(admin_id_int)
    return {"message": "Admin deleted successfully"}
