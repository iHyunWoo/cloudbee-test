from pydantic import BaseModel, Field


class ItemCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    price: float = Field(ge=0)
    description: str | None = Field(default=None, max_length=500)


class Item(ItemCreate):
    id: int


class HealthResponse(BaseModel):
    status: str
    version: str
