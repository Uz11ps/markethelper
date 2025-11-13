from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import HTTPException, status
from backend.models.admin import Admin
from backend.schemas.admin import AdminCreate, AdminUpdate
import os

# JWT настройки
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 часа


class AdminService:
    """Сервис для работы с администраторами"""

    @staticmethod
    async def create_admin(data: AdminCreate) -> Admin:
        """Создание нового администратора"""
        # Проверка существования username
        existing = await Admin.filter(username=data.username).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists"
            )

        # Создание админа
        admin = await Admin.create(
            username=data.username,
            password_hash=Admin.hash_password(data.password),
            full_name=data.full_name,
            email=data.email,
            is_super_admin=data.is_super_admin
        )

        return admin

    @staticmethod
    async def authenticate(username: str, password: str) -> Optional[Admin]:
        """Аутентификация администратора"""
        admin = await Admin.filter(username=username, is_active=True).first()

        if not admin:
            return None

        if not admin.verify_password(password):
            return None

        # Обновляем время последнего входа
        admin.last_login = datetime.utcnow()
        await admin.save()

        return admin

    @staticmethod
    def create_access_token(admin_id: int) -> str:
        """Создание JWT токена"""
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode = {
            "sub": str(admin_id),
            "exp": expire
        }
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    @staticmethod
    async def get_current_admin(token: str) -> Admin:
        """Получение текущего администратора по токену"""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            admin_id: str = payload.get("sub")
            if admin_id is None:
                raise credentials_exception
        except JWTError:
            raise credentials_exception

        admin = await Admin.filter(id=int(admin_id), is_active=True).first()
        if admin is None:
            raise credentials_exception

        return admin

    @staticmethod
    async def get_all_admins() -> list[Admin]:
        """Получение всех администраторов"""
        return await Admin.all()

    @staticmethod
    async def get_admin_by_id(admin_id: int) -> Optional[Admin]:
        """Получение администратора по ID"""
        return await Admin.filter(id=admin_id).first()

    @staticmethod
    async def update_admin(admin_id: int, data: AdminUpdate) -> Admin:
        """Обновление данных администратора"""
        admin = await Admin.filter(id=admin_id).first()
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Admin not found"
            )

        if data.full_name is not None:
            admin.full_name = data.full_name
        if data.email is not None:
            admin.email = data.email
        if data.password is not None:
            admin.password_hash = Admin.hash_password(data.password)
        if data.is_active is not None:
            admin.is_active = data.is_active

        await admin.save()
        return admin

    @staticmethod
    async def delete_admin(admin_id: int) -> bool:
        """Удаление администратора"""
        admin = await Admin.filter(id=admin_id).first()
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Admin not found"
            )

        await admin.delete()
        return True
