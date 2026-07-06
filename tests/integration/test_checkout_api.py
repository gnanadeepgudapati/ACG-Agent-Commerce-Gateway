from collections.abc import AsyncIterator, Callable

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from mercora.adapters.flat_rate_tax import FlatRateTaxAdapter
from mercora.adapters.mock_payment import MockPaymentAdapter
from mercora.api.deps import get_payment_adapter, get_session, get_tax_adapter
from mercora.domain.product import Product
from mercora.infra.product_repository import ProductRepository
from mercora.main import app

MakeProduct = Callable[..., Product]

ADDRESS = {"line1": "1 Infinite Loop", "city": "Cupertino", "postal_code": "95014"}


@pytest_asyncio.fixture
async def client(session: AsyncSession) -> AsyncIterator[AsyncClient]:
    async def override_get_session() -> AsyncIterator[AsyncSession]:
        yield session

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_payment_adapter] = lambda: MockPaymentAdapter()
    app.dependency_overrides[get_tax_adapter] = lambda: FlatRateTaxAdapter(rate=0.10)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


async def _cart_with_item(
    client: AsyncClient, session: AsyncSession, make_product: MakeProduct
) -> str:
    await ProductRepository(session).add(make_product(stock_qty=10))
    cart_id = (await client.post("/v1/carts")).json()["id"]
    await client.post(f"/v1/carts/{cart_id}/items", json={"sku": "TSHIRT-BLUE-M", "quantity": 2})
    return cart_id


async def test_checkout_success_then_get_order(
    client: AsyncClient, session: AsyncSession, make_product: MakeProduct
) -> None:
    cart_id = await _cart_with_item(client, session, make_product)

    resp = await client.post(
        "/v1/checkout",
        json={
            "cart_id": cart_id,
            "address": ADDRESS,
            "payment_token": "tok_ok",
            "idempotency_key": "key-1",
        },
    )
    assert resp.status_code == 201
    order = resp.json()
    assert order["status"] == "paid"
    assert order["total"] == {"amount_cents": 5500, "currency": "USD"}

    view = await client.get(f"/v1/orders/{order['id']}")
    assert view.status_code == 200
    assert view.json() == order


async def test_checkout_missing_cart_404(client: AsyncClient) -> None:
    resp = await client.post(
        "/v1/checkout",
        json={
            "cart_id": "no-such-cart",
            "address": ADDRESS,
            "payment_token": "tok_ok",
            "idempotency_key": "key-1",
        },
    )
    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "CART_NOT_FOUND"


async def test_checkout_payment_declined_402(
    client: AsyncClient, session: AsyncSession, make_product: MakeProduct
) -> None:
    cart_id = await _cart_with_item(client, session, make_product)

    resp = await client.post(
        "/v1/checkout",
        json={
            "cart_id": cart_id,
            "address": ADDRESS,
            "payment_token": "tok_decline",
            "idempotency_key": "key-1",
        },
    )
    assert resp.status_code == 402
    assert resp.json()["detail"]["code"] == "PAYMENT_DECLINED"


async def test_get_missing_order_404(client: AsyncClient) -> None:
    resp = await client.get("/v1/orders/does-not-exist")
    assert resp.status_code == 404
