from sqlalchemy.ext.asyncio import AsyncSession

from mercora.domain.money import Money
from mercora.domain.product import Product
from mercora.infra.product_repository import ProductRepository


def make_product(**overrides: object) -> Product:
    defaults: dict[str, object] = dict(
        id="TSHIRT-BLUE-M",
        name="Classic Tee",
        description="A soft cotton t-shirt.",
        price=Money(amount_cents=2500, currency="USD"),
        attributes={"color": "blue", "size": "M"},
        stock_qty=10,
    )
    defaults.update(overrides)
    return Product(**defaults)  # type: ignore[arg-type]


async def test_add_and_get_round_trips(session: AsyncSession) -> None:
    repo = ProductRepository(session)
    await repo.add(make_product())

    fetched = await repo.get("TSHIRT-BLUE-M")

    assert fetched == make_product()


async def test_get_missing_returns_none(session: AsyncSession) -> None:
    repo = ProductRepository(session)
    assert await repo.get("does-not-exist") is None


async def test_search_by_text_query(session: AsyncSession) -> None:
    repo = ProductRepository(session)
    await repo.add(make_product(id="A", name="Classic Tee"))
    await repo.add(make_product(id="B", name="Denim Jacket"))

    results = await repo.search(q="tee")

    assert [p.id for p in results] == ["A"]


async def test_search_by_color_and_size(session: AsyncSession) -> None:
    repo = ProductRepository(session)
    await repo.add(make_product(id="A", attributes={"color": "blue", "size": "M"}))
    await repo.add(make_product(id="B", attributes={"color": "red", "size": "M"}))

    results = await repo.search(color="blue", size="M")

    assert [p.id for p in results] == ["A"]


async def test_search_by_max_price(session: AsyncSession) -> None:
    repo = ProductRepository(session)
    await repo.add(make_product(id="cheap", price=Money(amount_cents=1000, currency="USD")))
    await repo.add(make_product(id="pricey", price=Money(amount_cents=5000, currency="USD")))

    results = await repo.search(max_price_cents=3000)

    assert [p.id for p in results] == ["cheap"]
