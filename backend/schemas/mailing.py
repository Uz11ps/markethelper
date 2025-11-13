from pydantic import BaseModel
from datetime import datetime


class MailingBase(BaseModel):
    created_by_id: int
    audience_id: int
    content: str


class MailingCreate(MailingBase):
    pass


class MailingOut(MailingBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
