from collections.abc import AsyncIterator, Callable

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from mercora.adapters.flat_rate_tax import FlatRateTaxAdapter
from mercora.adapters.mock_payment import MockPaymentAdapter
from mercora.api.deps import (
    Principal,
    get_current_principal,
    get_payment_adapter,
    get_session,
    get_tax_adapter,
)
from mercora.domain.product import Product
from mercora.infra.product_repository import ProductRepository
from mercora.main import app

MakeProduct = Callable[..., Product]

OTHER_PARTNER_ID = "other-partner"


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


def _as(principal: Principal) -> None:
    app.dependency_overrides[get_current_principal] = lambda: principal


async def test_partner_cannot_view_other_partners_cart(
    client: AsyncClient, make_principal: Callable[..., Principal]
) -> None:
    _as(make_principal())
    cart_id = (await client.post("/v1/carts")).json()["id"]

    _as(make_principal(partner_id=OTHER_PARTNER_ID))
    resp = await client.get(f"/v1/carts/{cart_id}")

    assert resp.status_code == 404


async def test_partner_cannot_add_item_to_other_partners_cart(
    client: AsyncClient,
    session: AsyncSession,
    make_product: Callable[..., Product],
    make_principal: Callable[..., Principal],
) -> None:
    await ProductRepository(session).add(make_product())
    _as(make_principal())
    cart_id = (await client.post("/v1/carts")).json()["id"]

    _as(make_principal(partner_id=OTHER_PARTNER_ID))
    resp = await client.post(
        f"/v1/carts/{cart_id}/items", json={"sku": "TSHIRT-BLUE-M", "quantity": 1}
    )

    assert resp.status_code == 404


async def test_partner_cannot_checkout_other_partners_cart(
    client: AsyncClient,
    session: AsyncSession,
    make_product: Callable[..., Product],
    make_principal: Callable[..., Principal],
) -> None:
    await ProductRepository(session).add(make_product())
    _as(make_principal())
    cart_id = (await client.post("/v1/carts")).json()["id"]
    await client.post(f"/v1/carts/{cart_id}/items", json={"sku": "TSHIRT-BLUE-M", "quantity": 1})

    _as(make_principal(partner_id=OTHER_PARTNER_ID))
    resp = await client.post(
        "/v1/checkout",
        json={
            "cart_id": cart_id,
            "address": {"line1": "1 Infinite Loop", "city": "Cupertino", "postal_code": "95014"},
            "payment_token": "tok_ok",
            "idempotency_key": "isolation-key",
        },
    )

    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "CART_NOT_FOUND"


async def test_partner_cannot_view_other_partners_order(
    client: AsyncClient,
    session: AsyncSession,
    make_product: Callable[..., Product],
    make_principal: Callable[..., Principal],
) -> None:
    await ProductRepository(session).add(make_product())
    _as(make_principal())
    cart_id = (await client.post("/v1/carts")).json()["id"]
    await client.post(f"/v1/carts/{cart_id}/items", json={"sku": "TSHIRT-BLUE-M", "quantity": 1})
    order = await client.post(
        "/v1/checkout",
        json={
            "cart_id": cart_id,
            "address": {"line1": "1 Infinite Loop", "city": "Cupertino", "postal_code": "95014"},
            "payment_token": "tok_ok",
            "idempotency_key": "isolation-key-2",
        },
    )
    order_id = order.json()["id"]

    _as(make_principal(partner_id=OTHER_PARTNER_ID))
    resp = await client.get(f"/v1/orders/{order_id}")

    assert resp.status_code == 404
