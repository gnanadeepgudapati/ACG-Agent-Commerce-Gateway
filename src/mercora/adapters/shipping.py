from typing import Protocol

from pydantic import BaseModel

from mercora.domain.address import Address
from mercora.domain.cart import CartItem
from mercora.domain.money import Money


class ShippingQuote(BaseModel):
    cost: Money
    carrier: str
    eta_days: int


class Shipment(BaseModel):
    id: str
    tracking_number: str


class ShippingAdapter(Protocol):
    async def quote(self, address: Address, items: list[CartItem]) -> ShippingQuote: ...

    async def create_shipment(self, order_id: str) -> Shipment: ...
