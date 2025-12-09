from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AccessFileBase(BaseModel):
    group_id: int
    path: str
    login: Optional[str]
    password: Optional[str]

class AccessFileCreate(BaseModel):
    group_id: int | None = None
    login: str
    password: str
    filename: str | None = None
    skip_auth: bool = False  # Пропустить авторизацию на внешнем сервисе и создать пустой файл

class AccessFileOut(AccessFileBase):
    id: int
    last_updated: datetime
    locked_until: Optional[datetime]

    class Config:
        from_attributes = True
