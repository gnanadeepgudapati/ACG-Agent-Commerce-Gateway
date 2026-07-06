from collections.abc import AsyncIterator, Callable

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from mercora.api.deps import Principal, get_current_principal, get_session
from mercora.domain.product import Product
from mercora.infra.product_repository import ProductRepository
from mercora.main import app

MakeProduct = Callable[..., Product]


@pytest_asyncio.fixture
async def client(session: AsyncSession, principal: Principal) -> AsyncIterator[AsyncClient]:
    async def override_get_session() -> AsyncIterator[AsyncSession]:
        yield session

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_current_principal] = lambda: principal
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


async def test_create_cart(client: AsyncClient) -> None:
    resp = await client.post("/v1/carts")
    assert resp.status_code == 201
    body = resp.json()
    assert body["items"] == []
    assert body["subtotal"] == {"amount_cents": 0, "currency": "USD"}


async def test_view_missing_cart_404(client: AsyncClient) -> None:
    resp = await client.get("/v1/carts/does-not-exist")
    assert resp.status_code == 404


async def test_add_item_and_view_cart(
    client: AsyncClient, session: AsyncSession, make_product: MakeProduct
) -> None:
    await ProductRepository(session).add(make_product())
    cart_id = (await client.post("/v1/carts")).json()["id"]

    resp = await client.post(
        f"/v1/carts/{cart_id}/items", json={"sku": "TSHIRT-BLUE-M", "quantity": 2}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["items"][0]["sku"] == "TSHIRT-BLUE-M"
    assert body["subtotal"] == {"amount_cents": 5000, "currency": "USD"}

    view = await client.get(f"/v1/carts/{cart_id}")
    assert view.json() == body


async def test_add_item_missing_cart_404(client: AsyncClient) -> None:
    resp = await client.post("/v1/carts/nope/items", json={"sku": "SKU-1", "quantity": 1})
    assert resp.status_code == 404


async def test_add_item_missing_product_404(client: AsyncClient) -> None:
    cart_id = (await client.post("/v1/carts")).json()["id"]
    resp = await client.post(
        f"/v1/carts/{cart_id}/items", json={"sku": "does-not-exist", "quantity": 1}
    )
    assert resp.status_code == 404


async def test_add_item_exceeding_stock_409(
    client: AsyncClient, session: AsyncSession, make_product: MakeProduct
) -> None:
    await ProductRepository(session).add(make_product(stock_qty=1))
    cart_id = (await client.post("/v1/carts")).json()["id"]

    resp = await client.post(
        f"/v1/carts/{cart_id}/items", json={"sku": "TSHIRT-BLUE-M", "quantity": 2}
    )
    assert resp.status_code == 409
    assert resp.json()["detail"]["code"] == "OUT_OF_STOCK"


async def test_remove_item(
    client: AsyncClient, session: AsyncSession, make_product: MakeProduct
) -> None:
    await ProductRepository(session).add(make_product())
    cart_id = (await client.post("/v1/carts")).json()["id"]
    await client.post(f"/v1/carts/{cart_id}/items", json={"sku": "TSHIRT-BLUE-M", "quantity": 1})

    resp = await client.delete(f"/v1/carts/{cart_id}/items/TSHIRT-BLUE-M")
    assert resp.status_code == 200
    assert resp.json()["items"] == []


async def test_remove_item_missing_cart_404(client: AsyncClient) -> None:
    resp = await client.delete("/v1/carts/nope/items/SKU-1")
    assert resp.status_code == 404
