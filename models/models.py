from typing import Optional, Union

from pydantic import BaseModel, Field


class Statistics(BaseModel):
    likes: int
    view_count: int = Field(alias="viewCount")
    contacts: int


class ItemRequest(BaseModel):
    seller_id: int = Field(alias="sellerId")
    name: str
    price: Union[int, float]
    statistics: Optional[Statistics] = None


class ItemResponse(ItemRequest):
    id: str
    seller_id: int = Field(alias="sellerId", ge=0)
    name: str
    price: int = Field(ge=0)
    statistics: Statistics
    created_at: str = Field(alias="createdAt")
