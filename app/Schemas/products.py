import uuid
from pydantic import BaseModel, ConfigDict, Field


class ProductCreate(BaseModel):
    product_name: str = Field(min_length=1, max_length=250)
    product_price: float = Field(gt=0)
    is_available: bool = True


class ProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # lets it read SQLAlchemy objects

    id: uuid.UUID
    product_name: str
    product_price: float
    is_available: bool