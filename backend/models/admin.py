from tortoise import fields
from tortoise.models import Model
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class Admin(Model):
    """
    Модель администратора
    """
    id = fields.IntField(pk=True)
    username = fields.CharField(255, unique=True, index=True)
    password_hash = fields.CharField(255)
    full_name = fields.CharField(255, null=True)
    email = fields.CharField(255, null=True, unique=True)

    is_active = fields.BooleanField(default=True)
    is_super_admin = fields.BooleanField(default=False)

    created_at = fields.DatetimeField(auto_now_add=True)
    last_login = fields.DatetimeField(null=True)

    class Meta:
        table = "admins"

    @classmethod
    def hash_password(cls, password: str) -> str:
        """Хеширование пароля"""
        return pwd_context.hash(password)

    def verify_password(self, password: str) -> bool:
        """Проверка пароля"""
        return pwd_context.verify(password, self.password_hash)
