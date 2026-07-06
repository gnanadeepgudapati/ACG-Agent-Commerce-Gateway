from sqlalchemy.ext.asyncio import AsyncSession

from mercora.domain.address import Address
from mercora.domain.cart import CartItem
from mercora.domain.money import Money
from mercora.domain.order import Order
from mercora.infra.orm import OrderItemORM, OrderORM


def _to_domain(row: OrderORM) -> Order:
    return Order(
        id=row.id,
        cart_id=row.cart_id,
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
        address=Address(
            line1=row.address_line1,
            line2=row.address_line2,
            city=row.address_city,
            state=row.address_state,
            postal_code=row.address_postal_code,
            country=row.address_country,
        ),
        subtotal=Money(amount_cents=row.subtotal_cents, currency=row.currency),
        tax=Money(amount_cents=row.tax_cents, currency=row.currency),
        total=Money(amount_cents=row.total_cents, currency=row.currency),
        status=row.status,  # type: ignore[arg-type]
        payment_authorization_id=row.payment_authorization_id,
    )


class OrderRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, order: Order) -> None:
        self._session.add(
            OrderORM(
                id=order.id,
                cart_id=order.cart_id,
                partner_id=order.partner_id,
                currency=order.currency,
                subtotal_cents=order.subtotal.amount_cents,
                tax_cents=order.tax.amount_cents,
                total_cents=order.total.amount_cents,
                status=order.status,
                payment_authorization_id=order.payment_authorization_id,
                address_line1=order.address.line1,
                address_line2=order.address.line2,
                address_city=order.address.city,
                address_state=order.address.state,
                address_postal_code=order.address.postal_code,
                address_country=order.address.country,
                items=[
                    OrderItemORM(
                        sku=item.sku,
                        quantity=item.quantity,
                        unit_price_cents=item.unit_price.amount_cents,
                    )
                    for item in order.items
                ],
            )
        )
        await self._session.commit()

    async def get(self, order_id: str, partner_id: str) -> Order | None:
        row = await self._session.get(OrderORM, order_id)
        if row is None or row.partner_id != partner_id:
            return None
        return _to_domain(row)
