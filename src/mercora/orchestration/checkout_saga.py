import uuid

from mercora.adapters.payment import Authorization, PaymentAdapter, PaymentDeclined
from mercora.adapters.tax import TaxAdapter
from mercora.domain.address import Address
from mercora.domain.cart import Cart
from mercora.domain.money import Money
from mercora.domain.order import Order
from mercora.infra.cart_repository import CartRepository
from mercora.infra.idempotency_repository import IdempotencyRepository
from mercora.infra.order_repository import OrderRepository
from mercora.infra.product_repository import ProductRepository
from mercora.orchestration.errors import (
    CartEmptyError,
    CartNotFoundForCheckoutError,
    OutOfStockError,
    PaymentDeclinedError,
)

Reservation = tuple[str, int]


class CheckoutSaga:
    def __init__(
        self,
        cart_repo: CartRepository,
        product_repo: ProductRepository,
        order_repo: OrderRepository,
        idempotency_repo: IdempotencyRepository,
        payment_adapter: PaymentAdapter,
        tax_adapter: TaxAdapter,
    ) -> None:
        self._carts = cart_repo
        self._products = product_repo
        self._orders = order_repo
        self._idempotency = idempotency_repo
        self._payment = payment_adapter
        self._tax = tax_adapter

    async def checkout(
        self,
        *,
        cart_id: str,
        partner_id: str,
        address: Address,
        payment_token: str,
        idempotency_key: str,
    ) -> Order:
        namespaced_key = f"{partner_id}:{idempotency_key}"
        existing_order_id = await self._idempotency.get(namespaced_key)
        if existing_order_id is not None:
            order = await self._orders.get(existing_order_id, partner_id)
            assert order is not None
            return order

        cart = await self._carts.get(cart_id, partner_id)
        if cart is None:
            raise CartNotFoundForCheckoutError(cart_id)
        if not cart.items:
            raise CartEmptyError(cart_id)

        reserved = await self._reserve_inventory(cart)

        try:
            tax = await self._tax.compute(cart.subtotal)
            total = cart.subtotal + tax
            authorization = await self._authorize_payment(total, payment_token, namespaced_key)
        except Exception:
            await self._release_inventory(reserved)
            raise

        try:
            order = Order(
                id=str(uuid.uuid4()),
                cart_id=cart_id,
                partner_id=partner_id,
                currency=cart.currency,
                items=cart.items,
                address=address,
                subtotal=cart.subtotal,
                tax=tax,
                total=total,
                status="paid",
                payment_authorization_id=authorization.id,
            )
            await self._orders.add(order)
            await self._idempotency.record(namespaced_key, order.id)
            return order
        except Exception:
            await self._payment.void(authorization.id)
            await self._release_inventory(reserved)
            raise

    async def _reserve_inventory(self, cart: Cart) -> list[Reservation]:
        reserved: list[Reservation] = []
        for item in cart.items:
            product = await self._products.get(item.sku)
            if product is None or product.stock_qty < item.quantity:
                await self._release_inventory(reserved)
                raise OutOfStockError(item.sku)
            await self._products.decrement_stock(item.sku, item.quantity)
            reserved.append((item.sku, item.quantity))
        return reserved

    async def _release_inventory(self, reserved: list[Reservation]) -> None:
        for sku, qty in reserved:
            await self._products.increment_stock(sku, qty)

    async def _authorize_payment(self, total: Money, token: str, idem_key: str) -> Authorization:
        try:
            return await self._payment.authorize(total, token, idem_key)
        except PaymentDeclined as exc:
            raise PaymentDeclinedError(str(exc)) from exc
