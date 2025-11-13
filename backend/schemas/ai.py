from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AIRequestBase(BaseModel):
    user_id: int
    question: str
    answer: str
    rating_id: Optional[int]


class AIRequestCreate(AIRequestBase):
    pass


class AIRequestOut(AIRequestBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
