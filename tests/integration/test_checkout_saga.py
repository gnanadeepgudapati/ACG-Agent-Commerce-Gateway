from collections.abc import Callable

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from mercora.adapters.flat_rate_tax import FlatRateTaxAdapter
from mercora.adapters.mock_payment import MockPaymentAdapter
from mercora.domain.address import Address
from mercora.domain.money import Money
from mercora.domain.product import Product
from mercora.infra.cart_repository import CartRepository
from mercora.infra.idempotency_repository import IdempotencyRepository
from mercora.infra.order_repository import OrderRepository
from mercora.infra.product_repository import ProductRepository
from mercora.orchestration.checkout_saga import CheckoutSaga
from mercora.orchestration.errors import (
    CartEmptyError,
    CartNotFoundForCheckoutError,
    OutOfStockError,
    PaymentDeclinedError,
)

MakeProduct = Callable[..., Product]

ADDRESS = Address(line1="1 Infinite Loop", city="Cupertino", postal_code="95014")
PARTNER = "demo-partner"


def make_saga(session: AsyncSession, payment_adapter: object | None = None) -> CheckoutSaga:
    return CheckoutSaga(
        cart_repo=CartRepository(session),
        product_repo=ProductRepository(session),
        order_repo=OrderRepository(session),
        idempotency_repo=IdempotencyRepository(session),
        payment_adapter=payment_adapter or MockPaymentAdapter(),
        tax_adapter=FlatRateTaxAdapter(rate=0.10),
    )


async def _cart_with_item(
    session: AsyncSession, make_product: MakeProduct, *, stock_qty: int = 10, quantity: int = 2
) -> str:
    await ProductRepository(session).add(make_product(stock_qty=stock_qty))
    cart = await CartRepository(session).create(PARTNER)
    await CartRepository(session).add_item(
        cart.id,
        PARTNER,
        sku="TSHIRT-BLUE-M",
        quantity=quantity,
        unit_price=Money(amount_cents=2500, currency="USD"),
    )
    return cart.id


async def test_successful_checkout(session: AsyncSession, make_product: MakeProduct) -> None:
    cart_id = await _cart_with_item(session, make_product, stock_qty=10, quantity=2)
    saga = make_saga(session)

    order = await saga.checkout(
        cart_id=cart_id,
        partner_id=PARTNER,
        address=ADDRESS,
        payment_token="tok_ok",
        idempotency_key="key-1",
    )

    assert order.status == "paid"
    assert order.partner_id == PARTNER
    assert order.subtotal == Money(amount_cents=5000, currency="USD")
    assert order.tax == Money(amount_cents=500, currency="USD")
    assert order.total == Money(amount_cents=5500, currency="USD")

    remaining = await ProductRepository(session).get("TSHIRT-BLUE-M")
    assert remaining is not None
    assert remaining.stock_qty == 8


async def test_checkout_missing_cart_raises(session: AsyncSession) -> None:
    saga = make_saga(session)
    with pytest.raises(CartNotFoundForCheckoutError):
        await saga.checkout(
            cart_id="no-such-cart",
            partner_id=PARTNER,
            address=ADDRESS,
            payment_token="tok_ok",
            idempotency_key="key-1",
        )


async def test_checkout_other_partner_cart_raises(
    session: AsyncSession, make_product: MakeProduct
) -> None:
    cart_id = await _cart_with_item(session, make_product)
    saga = make_saga(session)

    with pytest.raises(CartNotFoundForCheckoutError):
        await saga.checkout(
            cart_id=cart_id,
            partner_id="other-partner",
            address=ADDRESS,
            payment_token="tok_ok",
            idempotency_key="key-1",
        )


async def test_checkout_empty_cart_raises(session: AsyncSession) -> None:
    cart = await CartRepository(session).create(PARTNER)
    saga = make_saga(session)

    with pytest.raises(CartEmptyError):
        await saga.checkout(
            cart_id=cart.id,
            partner_id=PARTNER,
            address=ADDRESS,
            payment_token="tok_ok",
            idempotency_key="key-1",
        )


async def test_checkout_out_of_stock_releases_no_reservation(
    session: AsyncSession, make_product: MakeProduct
) -> None:
    cart_id = await _cart_with_item(session, make_product, stock_qty=1, quantity=2)
    saga = make_saga(session)

    with pytest.raises(OutOfStockError):
        await saga.checkout(
            cart_id=cart_id,
            partner_id=PARTNER,
            address=ADDRESS,
            payment_token="tok_ok",
            idempotency_key="key-1",
        )

    remaining = await ProductRepository(session).get("TSHIRT-BLUE-M")
    assert remaining is not None
    assert remaining.stock_qty == 1


async def test_checkout_payment_declined_releases_reservation(
    session: AsyncSession, make_product: MakeProduct
) -> None:
    cart_id = await _cart_with_item(session, make_product, stock_qty=10, quantity=2)
    saga = make_saga(session)

    with pytest.raises(PaymentDeclinedError):
        await saga.checkout(
            cart_id=cart_id,
            partner_id=PARTNER,
            address=ADDRESS,
            payment_token="tok_decline",
            idempotency_key="key-1",
        )

    remaining = await ProductRepository(session).get("TSHIRT-BLUE-M")
    assert remaining is not None
    assert remaining.stock_qty == 10


async def test_checkout_is_idempotent(session: AsyncSession, make_product: MakeProduct) -> None:
    cart_id = await _cart_with_item(session, make_product, stock_qty=10, quantity=2)
    saga = make_saga(session)

    first = await saga.checkout(
        cart_id=cart_id,
        partner_id=PARTNER,
        address=ADDRESS,
        payment_token="tok_ok",
        idempotency_key="same-key",
    )
    second = await saga.checkout(
        cart_id=cart_id,
        partner_id=PARTNER,
        address=ADDRESS,
        payment_token="tok_ok",
        idempotency_key="same-key",
    )

    assert first.id == second.id
    remaining = await ProductRepository(session).get("TSHIRT-BLUE-M")
    assert remaining is not None
    assert remaining.stock_qty == 8


async def test_checkout_idempotency_key_isolated_per_partner(
    session: AsyncSession, make_product: MakeProduct
) -> None:
    await ProductRepository(session).add(make_product(stock_qty=10))
    cart_a = await CartRepository(session).create(PARTNER)
    await CartRepository(session).add_item(
        cart_a.id,
        PARTNER,
        sku="TSHIRT-BLUE-M",
        quantity=1,
        unit_price=Money(amount_cents=2500, currency="USD"),
    )
    cart_b = await CartRepository(session).create("other-partner")
    await CartRepository(session).add_item(
        cart_b.id,
        "other-partner",
        sku="TSHIRT-BLUE-M",
        quantity=1,
        unit_price=Money(amount_cents=2500, currency="USD"),
    )
    saga = make_saga(session)

    order_a = await saga.checkout(
        cart_id=cart_a.id,
        partner_id=PARTNER,
        address=ADDRESS,
        payment_token="tok_ok",
        idempotency_key="shared-key",
    )
    order_b = await saga.checkout(
        cart_id=cart_b.id,
        partner_id="other-partner",
        address=ADDRESS,
        payment_token="tok_ok",
        idempotency_key="shared-key",
    )

    assert order_a.id != order_b.id
