from fastapi import APIRouter, Depends, HTTPException
from backend.schemas import UserOut, UserUpdate, UserCreate
from backend.services.user_service import UserService

router = APIRouter(prefix="/admin/users", tags=["Admin - Users"])


@router.get("/", response_model=list[UserOut])
async def list_users():
    return await UserService.list_users()

@router.get("/{user_id}", response_model=UserOut)
async def get_user(user_id: int):
    return await UserService.get_user(user_id)

@router.post("/")
async def create_user(data: UserCreate):
    return await UserService.create_user(data)

@router.patch("/{user_id}", response_model=UserOut)
async def update_user(user_id: int, data: UserUpdate):
    return await UserService.update_user(user_id, data)


@router.delete("/{user_id}")
async def deactivate_user(user_id: int):
    return await UserService.deactivate_user(user_id)
