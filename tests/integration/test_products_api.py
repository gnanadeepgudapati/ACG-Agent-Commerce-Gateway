from collections.abc import AsyncIterator, Callable

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from mercora.api.deps import get_session
from mercora.domain.product import Product
from mercora.infra.product_repository import ProductRepository
from mercora.main import app

MakeProduct = Callable[..., Product]


@pytest_asyncio.fixture
async def client(session: AsyncSession) -> AsyncIterator[AsyncClient]:
    async def override_get_session() -> AsyncIterator[AsyncSession]:
        yield session

    app.dependency_overrides[get_session] = override_get_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


async def test_healthz(client: AsyncClient) -> None:
    resp = await client.get("/healthz")
    assert resp.status_code == 200


async def test_search_products_empty(client: AsyncClient) -> None:
    resp = await client.get("/v1/products")
    assert resp.status_code == 200
    assert resp.json() == []


async def test_search_and_get_product(
    client: AsyncClient, session: AsyncSession, make_product: MakeProduct
) -> None:
    repo = ProductRepository(session)
    await repo.add(make_product())

    resp = await client.get("/v1/products", params={"color": "blue", "size": "M"})
    assert resp.status_code == 200
    assert [p["id"] for p in resp.json()] == ["TSHIRT-BLUE-M"]

    resp2 = await client.get("/v1/products/TSHIRT-BLUE-M")
    assert resp2.status_code == 200
    assert resp2.json()["id"] == "TSHIRT-BLUE-M"


async def test_get_missing_product_404(client: AsyncClient) -> None:
    resp = await client.get("/v1/products/nope")
    assert resp.status_code == 404


async def test_search_by_max_price(
    client: AsyncClient, session: AsyncSession, make_product: MakeProduct
) -> None:
    repo = ProductRepository(session)
    await repo.add(make_product(id="cheap"))

    resp = await client.get("/v1/products", params={"max_price_cents": 1000})
    assert resp.json() == []
