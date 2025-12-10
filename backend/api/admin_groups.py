from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional

from backend.models.subscription import AccessGroup
from backend.models.admin import Admin
from backend.api.admin import get_current_admin

router = APIRouter(prefix="/admin/groups", tags=["Admin Groups"])


class GroupCreate(BaseModel):
    name: str


class GroupUpdate(BaseModel):
    name: str


@router.get("/", response_model=List[dict])
async def list_groups(admin: Admin = Depends(get_current_admin)):
    """Получить список всех групп доступа"""
    groups = await AccessGroup.all()
    return [
        {
            "id": group.id,
            "name": group.name,
            "created_at": group.created_at.isoformat() if group.created_at else None,
        }
        for group in groups
    ]


@router.post("/", response_model=dict)
async def create_group(
    data: GroupCreate,
    admin: Admin = Depends(get_current_admin)
):
    """Создать новую группу доступа"""
    # Проверяем уникальность имени
    existing = await AccessGroup.get_or_none(name=data.name)
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Группа с именем '{data.name}' уже существует"
        )
    
    group = await AccessGroup.create(name=data.name)
    return {
        "id": group.id,
        "name": group.name,
        "created_at": group.created_at.isoformat() if group.created_at else None,
    }


@router.put("/{group_id}", response_model=dict)
async def update_group(
    group_id: int,
    data: GroupUpdate,
    admin: Admin = Depends(get_current_admin)
):
    """Обновить название группы"""
    group = await AccessGroup.get_or_none(id=group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Группа не найдена")
    
    # Проверяем уникальность нового имени
    existing = await AccessGroup.get_or_none(name=data.name)
    if existing and existing.id != group_id:
        raise HTTPException(
            status_code=400,
            detail=f"Группа с именем '{data.name}' уже существует"
        )
    
    group.name = data.name
    await group.save()
    
    return {
        "id": group.id,
        "name": group.name,
        "created_at": group.created_at.isoformat() if group.created_at else None,
    }


@router.delete("/{group_id}")
async def delete_group(
    group_id: int,
    admin: Admin = Depends(get_current_admin)
):
    """Удалить группу доступа"""
    group = await AccessGroup.get_or_none(id=group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Группа не найдена")
    
    # Проверяем, нет ли активных подписок с этой группой
    from backend.models.subscription import Subscription
    active_subs = await Subscription.filter(group_id=group_id).count()
    if active_subs > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Невозможно удалить группу: к ней привязано {active_subs} подписок"
        )
    
    await group.delete()
    return {"message": "Группа удалена успешно"}

