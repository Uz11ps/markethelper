from backend.models.file import AccessFile
from fastapi import APIRouter, HTTPException
from backend.services import file_service

router = APIRouter(prefix="/cookie", tags=["Cookie Updater"])

@router.post("/files/{file_id}/refresh_cookies")
async def refresh_cookies(file_id: int):
    file = await AccessFile.get_or_none(id=file_id)
    if not file:
        raise HTTPException(404, "Файл не найден")

    file = await file_service.FileService.generate_and_save_cookies(file)
    # Уведомления отправляются автоматически в generate_and_save_cookies
    return {"status": "ok", "last_updated": file.last_updated}

@router.post("/{group_id}/regen")
async def regen_group_file(group_id: int):
    """
    Перегенерировать куки для файла группы (авторизация по логину/паролю из БД).
    """
    file = await file_service.FileService.get_group_file(group_id)
    file = await file_service.FileService.generate_and_save_cookies(file)
    # Уведомления отправляются автоматически в generate_and_save_cookies
    return {
        "status": "regenerated",
        "group_id": group_id,
        "path": file.path,
        "last_updated": file.last_updated,
        "locked_until": file.locked_until,
    }

@router.get("/{group_id}/get")
async def get_group_file(group_id: int):
    file = await file_service.FileService.get_group_file(group_id)
    content = await file_service.FileService.read_file_content(file)
    return {"group_id": group_id, "file": file.path, "cookies": content}
