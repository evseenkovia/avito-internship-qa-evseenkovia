from typing import Optional, Union

from pydantic import BaseModel, ConfigDict, Field


class Statistics(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    likes: int
    view_count: int = Field(alias="viewCount")
    contacts: int


class ItemRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    seller_id: int = Field(alias="sellerId")
    name: str
    price: Union[int, float]
    statistics: Optional[Statistics] = None


class ItemResponse(ItemRequest):
    model_config = ConfigDict(populate_by_name=True)
    id: str
    seller_id: int = Field(alias="sellerId", ge=0)
    name: str
    price: int = Field(ge=0)
    statistics: Statistics
    created_at: str = Field(alias="createdAt")
