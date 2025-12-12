from pydantic import BaseModel, Field
from typing import Literal


class ChargeTokensRequest(BaseModel):
    tg_id: int = Field(..., description="Telegram ID пользователя")
    action: Literal["image_generation", "ai_chat"]
    cost: int = Field(None, description="Стоимость действия (опционально, если не указана - используется стандартная)")


class ChargeTokensResponse(BaseModel):
    action: str
    cost: int
    balance: int
    label: str


class TokenPricingResponse(BaseModel):
    image_generation_cost: int
    gpt_request_cost: int
