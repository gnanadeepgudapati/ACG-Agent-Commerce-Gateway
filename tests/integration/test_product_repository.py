from collections.abc import Callable

from sqlalchemy.ext.asyncio import AsyncSession

from mercora.domain.money import Money
from mercora.domain.product import Product
from mercora.infra.product_repository import ProductRepository

MakeProduct = Callable[..., Product]


async def test_add_and_get_round_trips(session: AsyncSession, make_product: MakeProduct) -> None:
    repo = ProductRepository(session)
    await repo.add(make_product())

    fetched = await repo.get("TSHIRT-BLUE-M")

    assert fetched == make_product()


async def test_get_missing_returns_none(session: AsyncSession) -> None:
    repo = ProductRepository(session)
    assert await repo.get("does-not-exist") is None


async def test_search_by_text_query(session: AsyncSession, make_product: MakeProduct) -> None:
    repo = ProductRepository(session)
    await repo.add(make_product(id="A", name="Classic Tee"))
    await repo.add(make_product(id="B", name="Denim Jacket"))

    results = await repo.search(q="tee")

    assert [p.id for p in results] == ["A"]


async def test_search_by_color_and_size(session: AsyncSession, make_product: MakeProduct) -> None:
    repo = ProductRepository(session)
    await repo.add(make_product(id="A", attributes={"color": "blue", "size": "M"}))
    await repo.add(make_product(id="B", attributes={"color": "red", "size": "M"}))

    results = await repo.search(color="blue", size="M")

    assert [p.id for p in results] == ["A"]


async def test_search_by_max_price(session: AsyncSession, make_product: MakeProduct) -> None:
    repo = ProductRepository(session)
    await repo.add(make_product(id="cheap", price=Money(amount_cents=1000, currency="USD")))
    await repo.add(make_product(id="pricey", price=Money(amount_cents=5000, currency="USD")))

    results = await repo.search(max_price_cents=3000)

    assert [p.id for p in results] == ["cheap"]


async def test_decrement_stock(session: AsyncSession, make_product: MakeProduct) -> None:
    repo = ProductRepository(session)
    await repo.add(make_product(stock_qty=10))

    await repo.decrement_stock("TSHIRT-BLUE-M", 3)

    updated = await repo.get("TSHIRT-BLUE-M")
    assert updated is not None
    assert updated.stock_qty == 7


async def test_increment_stock(session: AsyncSession, make_product: MakeProduct) -> None:
    repo = ProductRepository(session)
    await repo.add(make_product(stock_qty=10))

    await repo.increment_stock("TSHIRT-BLUE-M", 3)

    updated = await repo.get("TSHIRT-BLUE-M")
    assert updated is not None
    assert updated.stock_qty == 13
