from pydantic import BaseModel, Field
from typing import Optional, Union

class Statistics(BaseModel):
    likes: int
    viewCount: int
    contacts: int

class ItemRequest(BaseModel):
    sellerId: int
    name: str
    price: Union[int, float]
    statistics: Optional[Statistics] = None
    
class ItemResponse(ItemRequest):
    id: str
    sellerId: int = Field(ge=0)
    name: str
    price: int = Field(ge=0)
    statistics: Statistics
    createdAt: str
    