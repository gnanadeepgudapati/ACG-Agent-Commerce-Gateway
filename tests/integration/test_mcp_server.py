import json
from collections.abc import AsyncIterator, Callable

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from mcp.server.fastmcp import FastMCP
from sqlalchemy.ext.asyncio import AsyncSession

from mercora.adapters.flat_rate_tax import FlatRateTaxAdapter
from mercora.adapters.mock_payment import MockPaymentAdapter
from mercora.api.deps import get_payment_adapter, get_session, get_tax_adapter
from mercora.domain.product import Product
from mercora.infra.product_repository import ProductRepository
from mercora.main import app
from mercora.mcp_server.client import MercoraClient
from mercora.mcp_server.server import build_server

MakeProduct = Callable[..., Product]

ADDRESS = {"line1": "1 Infinite Loop", "city": "Cupertino", "postal_code": "95014"}


def _decode(result: object) -> list[dict[str, object]]:
    assert isinstance(result, list)
    return [json.loads(block.text) for block in result]  # type: ignore[attr-defined]


@pytest_asyncio.fixture
async def mcp_server(session: AsyncSession) -> AsyncIterator[FastMCP]:
    async def override_get_session() -> AsyncIterator[AsyncSession]:
        yield session

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_payment_adapter] = lambda: MockPaymentAdapter()
    app.dependency_overrides[get_tax_adapter] = lambda: FlatRateTaxAdapter(rate=0.10)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield build_server(MercoraClient(http_client))
    app.dependency_overrides.clear()


async def test_lists_all_seven_tools(mcp_server: FastMCP) -> None:
    tools = await mcp_server.list_tools()
    assert {t.name for t in tools} == {
        "search_products",
        "get_product",
        "create_cart",
        "add_item",
        "view_cart",
        "checkout",
        "get_order_status",
    }


async def test_search_products_canonical_demo(
    mcp_server: FastMCP, session: AsyncSession, make_product: MakeProduct
) -> None:
    await ProductRepository(session).add(make_product())

    result = await mcp_server.call_tool(
        "search_products", {"color": "blue", "size": "M", "max_price_cents": 3000}
    )

    products = _decode(result)
    assert products == [
        {
            "sku": "TSHIRT-BLUE-M",
            "name": "Classic Tee",
            "price": "$25.00",
            "attributes": {"color": "blue", "size": "M"},
            "in_stock": True,
        }
    ]


async def test_get_product_missing_returns_structured_error(mcp_server: FastMCP) -> None:
    result = await mcp_server.call_tool("get_product", {"sku": "nope"})
    assert _decode(result) == [{"error": {"code": "ERROR", "message": "Product not found"}}]


async def test_full_purchase_flow_through_mcp_tools(
    mcp_server: FastMCP, session: AsyncSession, make_product: MakeProduct
) -> None:
    await ProductRepository(session).add(make_product(stock_qty=10))

    cart = _decode(await mcp_server.call_tool("create_cart", {}))[0]
    cart_id = cart["cart_id"]

    added = _decode(
        await mcp_server.call_tool(
            "add_item", {"cart_id": cart_id, "sku": "TSHIRT-BLUE-M", "quantity": 2}
        )
    )[0]
    assert added["subtotal"] == "$50.00"

    viewed = _decode(await mcp_server.call_tool("view_cart", {"cart_id": cart_id}))[0]
    assert viewed == added

    order = _decode(
        await mcp_server.call_tool(
            "checkout",
            {
                "cart_id": cart_id,
                "address": ADDRESS,
                "payment_token": "tok_ok",
                "idempotency_key": "mcp-key-1",
            },
        )
    )[0]
    assert order["status"] == "paid"
    assert order["total"] == "$55.00"

    status = _decode(
        await mcp_server.call_tool("get_order_status", {"order_id": order["order_id"]})
    )[0]
    assert status == order


async def test_checkout_payment_declined_returns_structured_error(
    mcp_server: FastMCP, session: AsyncSession, make_product: MakeProduct
) -> None:
    await ProductRepository(session).add(make_product(stock_qty=10))
    cart = _decode(await mcp_server.call_tool("create_cart", {}))[0]
    await mcp_server.call_tool(
        "add_item", {"cart_id": cart["cart_id"], "sku": "TSHIRT-BLUE-M", "quantity": 1}
    )

    result = _decode(
        await mcp_server.call_tool(
            "checkout",
            {
                "cart_id": cart["cart_id"],
                "address": ADDRESS,
                "payment_token": "tok_decline",
                "idempotency_key": "mcp-key-2",
            },
        )
    )[0]

    assert result["error"]["code"] == "PAYMENT_DECLINED"
