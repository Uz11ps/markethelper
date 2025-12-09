# backend/api/files.py
from datetime import datetime, timezone
import os
from fastapi import APIRouter, HTTPException, Depends
from backend.core.config import COOKIE_DIR
from backend.models.file import AccessFile
from backend.models.subscription import AccessGroup
from backend.models.admin import Admin
from backend.api.admin import get_current_admin
from backend.schemas.file import AccessFileCreate
from backend.services.file_service import FileService

router = APIRouter(prefix="/files", tags=["Files"])

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

@router.post("/add")
async def add_access_file(data: AccessFileCreate, admin: Admin = Depends(get_current_admin)):

    if data.group_id:
        group = await AccessGroup.get_or_none(id=data.group_id)
        if not group:
            group_name = f"Group_{int(datetime.utcnow().timestamp())}"
            group = await AccessGroup.create(name=group_name)
    else:
        group_name = f"Group_{int(datetime.utcnow().timestamp())}"
        group = await AccessGroup.create(name=group_name)
    cookie_file_name = data.filename or f"{data.login}_{int(datetime.utcnow().timestamp())}.txt"
    cookie_file_path = os.path.join(COOKIE_DIR, cookie_file_name)

    file = await AccessFile.create(
        group=group,
        login=data.login,
        password=data.password,
        path=cookie_file_path
    )

    file = await FileService.generate_and_save_cookies(file, filename=cookie_file_name)

    return {
        "status": "ok",
        "file_id": file.id,
        "group_id": group.id,
        "path": file.path,
        "last_updated": file.last_updated,
    }