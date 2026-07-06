import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from mercora.domain.money import Money
from mercora.infra.cart_repository import CartNotFoundError, CartRepository


async def test_create_returns_empty_cart(session: AsyncSession) -> None:
    repo = CartRepository(session)
    cart = await repo.create()

    assert cart.items == []
    assert cart.currency == "USD"


async def test_get_missing_returns_none(session: AsyncSession) -> None:
    repo = CartRepository(session)
    assert await repo.get("does-not-exist") is None


async def test_add_item_then_get(session: AsyncSession) -> None:
    repo = CartRepository(session)
    cart = await repo.create()

    updated = await repo.add_item(
        cart.id, sku="SKU-1", quantity=2, unit_price=Money(amount_cents=1000, currency="USD")
    )

    assert updated.subtotal == Money(amount_cents=2000, currency="USD")
    refetched = await repo.get(cart.id)
    assert refetched == updated


async def test_add_item_to_missing_cart_raises(session: AsyncSession) -> None:
    repo = CartRepository(session)
    with pytest.raises(CartNotFoundError):
        await repo.add_item(
            "no-such-cart",
            sku="SKU-1",
            quantity=1,
            unit_price=Money(amount_cents=1000, currency="USD"),
        )


async def test_add_item_same_sku_increments_quantity(session: AsyncSession) -> None:
    repo = CartRepository(session)
    cart = await repo.create()
    await repo.add_item(
        cart.id, sku="SKU-1", quantity=1, unit_price=Money(amount_cents=1000, currency="USD")
    )

    updated = await repo.add_item(
        cart.id, sku="SKU-1", quantity=2, unit_price=Money(amount_cents=1000, currency="USD")
    )

    assert len(updated.items) == 1
    assert updated.items[0].quantity == 3


async def test_remove_item(session: AsyncSession) -> None:
    repo = CartRepository(session)
    cart = await repo.create()
    await repo.add_item(
        cart.id, sku="SKU-1", quantity=1, unit_price=Money(amount_cents=1000, currency="USD")
    )

    updated = await repo.remove_item(cart.id, "SKU-1")

    assert updated.items == []


async def test_remove_item_from_missing_cart_raises(session: AsyncSession) -> None:
    repo = CartRepository(session)
    with pytest.raises(CartNotFoundError):
        await repo.remove_item("no-such-cart", "SKU-1")
