from pydantic import BaseModel, Field

from mercora.domain.money import Money


class Product(BaseModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str
    price: Money
    attributes: dict[str, str] = Field(default_factory=dict)
    stock_qty: int = Field(ge=0)
