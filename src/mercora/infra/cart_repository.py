import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from mercora.domain.cart import Cart, CartItem
from mercora.domain.money import Money
from mercora.infra.orm import CartItemORM, CartORM


class CartNotFoundError(Exception):
    pass


def _to_domain(row: CartORM) -> Cart:
    return Cart(
        id=row.id,
        partner_id=row.partner_id,
        currency=row.currency,
        items=[
            CartItem(
                sku=item.sku,
                quantity=item.quantity,
                unit_price=Money(amount_cents=item.unit_price_cents, currency=row.currency),
            )
            for item in row.items
        ],
    )


class CartRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, partner_id: str, currency: str = "USD") -> Cart:
        row = CartORM(id=str(uuid.uuid4()), partner_id=partner_id, currency=currency)
        self._session.add(row)
        await self._session.commit()
        return Cart(id=row.id, partner_id=partner_id, currency=currency, items=[])

    async def get(self, cart_id: str, partner_id: str) -> Cart | None:
        row = await self._session.get(CartORM, cart_id)
        if row is None or row.partner_id != partner_id:
            return None
        return _to_domain(row)

    async def _require(self, cart_id: str, partner_id: str) -> CartORM:
        row = await self._session.get(CartORM, cart_id)
        if row is None or row.partner_id != partner_id:
            raise CartNotFoundError(cart_id)
        return row

    async def add_item(
        self, cart_id: str, partner_id: str, *, sku: str, quantity: int, unit_price: Money
    ) -> Cart:
        row = await self._require(cart_id, partner_id)
        existing = next((item for item in row.items if item.sku == sku), None)
        if existing is not None:
            existing.quantity += quantity
        else:
            row.items.append(
                CartItemORM(sku=sku, quantity=quantity, unit_price_cents=unit_price.amount_cents)
            )
        await self._session.commit()
        await self._session.refresh(row, attribute_names=["items"])
        return _to_domain(row)

    async def remove_item(self, cart_id: str, partner_id: str, sku: str) -> Cart:
        row = await self._require(cart_id, partner_id)
        row.items = [item for item in row.items if item.sku != sku]
        await self._session.commit()
        await self._session.refresh(row, attribute_names=["items"])
        return _to_domain(row)
