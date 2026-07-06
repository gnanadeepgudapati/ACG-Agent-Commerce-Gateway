import json

from mcp.server.fastmcp import FastMCP


async def test_seeded_mcp_server_fixture_is_authenticated_and_seeded(
    seeded_mcp_server: FastMCP,
) -> None:
    result = await seeded_mcp_server.call_tool(
        "search_products", {"color": "blue", "size": "M", "max_price_cents": 3000}
    )
    products = [json.loads(block.text) for block in result]  # type: ignore[attr-defined]

    assert products == [
        {
            "sku": "TSHIRT-BLUE-M",
            "name": "Classic Tee",
            "price": "$25.00",
            "attributes": {"color": "blue", "size": "M"},
            "in_stock": True,
        }
    ]
