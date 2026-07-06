from typing import Literal

from pydantic import BaseModel, Field

from mercora.domain.address import Address
from mercora.domain.cart import CartItem
from mercora.domain.money import Money

OrderStatus = Literal["paid", "failed"]


class Order(BaseModel):
    id: str = Field(min_length=1)
    cart_id: str = Field(min_length=1)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    items: list[CartItem]
    address: Address
    subtotal: Money
    tax: Money
    total: Money
    status: OrderStatus
    payment_authorization_id: str
