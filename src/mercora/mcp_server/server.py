from typing import Any

from mcp.server.fastmcp import FastMCP

from mercora.mcp_server.client import MercoraApiError, MercoraClient
from mercora.mcp_server.shaping import shape_cart, shape_order, shape_product


def _error_payload(exc: MercoraApiError) -> dict[str, Any]:
    if isinstance(exc.detail, dict) and "code" in exc.detail:
        return {"error": exc.detail}
    return {"error": {"code": "ERROR", "message": str(exc.detail)}}


def build_server(client: MercoraClient) -> FastMCP:
    mcp = FastMCP("mercora")

    @mcp.tool()
    async def search_products(
        query: str | None = None,
        color: str | None = None,
        size: str | None = None,
        max_price_cents: int | None = None,
    ) -> Any:
        """Search the product catalog by free-text query and structured filters."""
        try:
            products = await client.search_products(
                q=query, color=color, size=size, max_price_cents=max_price_cents
            )
        except MercoraApiError as exc:
            return _error_payload(exc)
        return [shape_product(p) for p in products]

    @mcp.tool()
    async def get_product(sku: str) -> Any:
        """Fetch full detail for a single product by SKU."""
        try:
            return shape_product(await client.get_product(sku))
        except MercoraApiError as exc:
            return _error_payload(exc)

    @mcp.tool()
    async def create_cart() -> Any:
        """Start a new, empty cart session."""
        try:
            return shape_cart(await client.create_cart())
        except MercoraApiError as exc:
            return _error_payload(exc)

    @mcp.tool()
    async def add_item(cart_id: str, sku: str, quantity: int) -> Any:
        """Add a line item (by SKU and quantity) to an existing cart."""
        try:
            return shape_cart(await client.add_item(cart_id, sku, quantity))
        except MercoraApiError as exc:
            return _error_payload(exc)

    @mcp.tool()
    async def view_cart(cart_id: str) -> Any:
        """Inspect a cart's current items and running subtotal."""
        try:
            return shape_cart(await client.view_cart(cart_id))
        except MercoraApiError as exc:
            return _error_payload(exc)

    @mcp.tool()
    async def checkout(
        cart_id: str, address: dict[str, Any], payment_token: str, idempotency_key: str
    ) -> Any:
        """Complete an orchestrated purchase: reserve inventory, tax, authorize payment, create
        order."""
        try:
            return shape_order(
                await client.checkout(cart_id, address, payment_token, idempotency_key)
            )
        except MercoraApiError as exc:
            return _error_payload(exc)

    @mcp.tool()
    async def get_order_status(order_id: str) -> Any:
        """Look up the fulfillment status of a previously placed order."""
        try:
            return shape_order(await client.get_order_status(order_id))
        except MercoraApiError as exc:
            return _error_payload(exc)

    return mcp
