# backend/api/files.py
from datetime import datetime, timezone
import os
from fastapi import APIRouter, HTTPException, Depends, Form
from backend.core.config import COOKIE_DIR
from backend.models.file import AccessFile
from backend.models.subscription import AccessGroup
from backend.models.admin import Admin
from backend.api.admin import get_current_admin
from backend.schemas.file import AccessFileCreate
from backend.services.file_service import FileService

router = APIRouter(prefix="/files", tags=["Files"])

# Admin endpoints для управления файлами
admin_router = APIRouter(prefix="/admin/files", tags=["Admin Files"])

# Admin endpoints для управления файлами
admin_router = APIRouter(prefix="/admin/files", tags=["Admin Files"])

@router.get("/{group_id}/status")
async def group_file_status(group_id: int):
    file = await FileService.get_group_file(group_id)
    valid, msg = await FileService.is_cookie_valid(file)
    return {"group_id": group_id, "valid": valid, "message": msg, "path": file.path}

@router.get("/user/{tg_id}/get")
async def get_user_file(tg_id: int):
    file = await FileService.get_user_file_by_tg(tg_id)
    content = await FileService.read_file_content(file)

    updated_at = None
    if getattr(file, "last_updated", None):
        dt = file.last_updated
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        updated_at = dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

    return {
        "tg_id": tg_id,
        "file": file.path,
        "cookies": content,
        "file_id": file.id,
        "id": file.id,           
        "group_id": getattr(file, "group_id", None),
        "updated_at": updated_at,
    }

@router.post("/user/{tg_id}/regen")
async def regen_user_file(tg_id: int, data: dict | None = None):
    filename = None
    if data and isinstance(data, dict):
        filename = data.get("filename")

    file = await FileService.regen_user_file_by_tg(tg_id, filename=filename)
    content = await FileService.read_file_content(file) 

    return {
        "status": "regenerated",
        "tg_id": tg_id,
        "file": file.path,
        "file_id": file.id,
        "updated_at": file.last_updated.isoformat() if file.last_updated else None,
        "locked_until": file.locked_until.isoformat() if file.locked_until else None,
        "cookies": content, 
    }

@admin_router.get("/group/{group_id}")
async def get_group_files(group_id: int, admin: Admin = Depends(get_current_admin)):
    """Получить все файлы группы"""
    group = await AccessGroup.get_or_none(id=group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Группа не найдена")
    
    files = await AccessFile.filter(group=group).all()
    return [
        {
            "id": file.id,
            "path": file.path,
            "filename": os.path.basename(file.path) if file.path else None,
            "login": file.login,
            "last_updated": file.last_updated.isoformat() if file.last_updated else None,
            "locked_until": file.locked_until.isoformat() if file.locked_until else None,
        }
        for file in files
    ]


@admin_router.post("/add")
async def add_access_file(
    group_id: int = Form(...),
    login: str = Form(...),
    password: str = Form(...),
    filename: str = Form(None),
    skip_auth: bool = Form(False),
    admin: Admin = Depends(get_current_admin)
):
    """Добавить файл доступа (для админки через FormData)"""
    # Если group_id не указан, создаем новую группу
    group = await AccessGroup.get_or_none(id=group_id)
    if not group:
        raise HTTPException(status_code=404, detail=f"Группа с ID {group_id} не найдена")
    
    cookie_file_name = filename or f"{login}_{int(datetime.utcnow().timestamp())}.txt"
    cookie_file_path = os.path.join(COOKIE_DIR, cookie_file_name)

    file = await AccessFile.create(
        group=group,
        login=login,
        password=password,
        path=cookie_file_path
    )

    # Если skip_auth=True, создаем пустой файл без авторизации на внешнем сервисе
    if skip_auth:
        file = await FileService.create_empty_cookie_file(file, filename=cookie_file_name)
    else:
        try:
            file = await FileService.generate_and_save_cookies(file, filename=cookie_file_name)
        except HTTPException as e:
            # Если авторизация не удалась, но skip_auth не установлен,
            # возвращаем ошибку с предложением использовать skip_auth
            if e.status_code in (404, 503, 504):
                raise HTTPException(
                    e.status_code,
                    f"{e.detail}. "
                    f"Вы можете создать файл без авторизации, установив параметр skip_auth=true"
                )
            raise

    return {
        "status": "ok",
        "file_id": file.id,
        "group_id": group.id,
        "path": file.path,
        "last_updated": file.last_updated.isoformat() if file.last_updated else None,
        "skip_auth": skip_auth,
    }