import uuid

from mercora.adapters.shipping import Shipment, ShippingQuote
from mercora.domain.address import Address
from mercora.domain.cart import CartItem
from mercora.domain.money import Money


class MockShippingAdapter:
    def __init__(self, flat_rate_cents: int = 500, eta_days: int = 5) -> None:
        self._flat_rate_cents = flat_rate_cents
        self._eta_days = eta_days

    async def quote(self, address: Address, items: list[CartItem]) -> ShippingQuote:
        return ShippingQuote(
            cost=Money(amount_cents=self._flat_rate_cents, currency="USD"),
            carrier="MockCarrier",
            eta_days=self._eta_days,
        )

    async def create_shipment(self, order_id: str) -> Shipment:
        return Shipment(
            id=f"ship_{uuid.uuid4().hex[:12]}",
            tracking_number=uuid.uuid4().hex[:16].upper(),
        )
