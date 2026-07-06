from mercora.mcp_server.shaping import shape_cart, shape_order, shape_product


def test_shape_product_trims_to_agent_relevant_fields() -> None:
    raw = {
        "id": "TSHIRT-BLUE-M",
        "name": "Classic Tee",
        "description": "A soft cotton crew-neck t-shirt.",
        "price": {"amount_cents": 2500, "currency": "USD"},
        "attributes": {"color": "blue", "size": "M"},
        "stock_qty": 5,
    }
    assert shape_product(raw) == {
        "sku": "TSHIRT-BLUE-M",
        "name": "Classic Tee",
        "price": "$25.00",
        "attributes": {"color": "blue", "size": "M"},
        "in_stock": True,
    }


def test_shape_product_out_of_stock() -> None:
    raw = {
        "id": "SKU-1",
        "name": "Widget",
        "description": "",
        "price": {"amount_cents": 100, "currency": "USD"},
        "attributes": {},
        "stock_qty": 0,
    }
    assert shape_product(raw)["in_stock"] is False


def test_shape_cart() -> None:
    raw = {
        "id": "cart-1",
        "currency": "USD",
        "items": [
            {
                "sku": "SKU-1",
                "quantity": 2,
                "unit_price": {"amount_cents": 1000, "currency": "USD"},
                "line_total": {"amount_cents": 2000, "currency": "USD"},
            }
        ],
        "subtotal": {"amount_cents": 2000, "currency": "USD"},
    }
    assert shape_cart(raw) == {
        "cart_id": "cart-1",
        "items": [{"sku": "SKU-1", "quantity": 2, "line_total": "$20.00"}],
        "subtotal": "$20.00",
    }


def test_shape_order() -> None:
    raw = {
        "id": "order-1",
        "status": "paid",
        "total": {"amount_cents": 5500, "currency": "USD"},
        "payment_authorization_id": "auth_abc123",
    }
    assert shape_order(raw) == {
        "order_id": "order-1",
        "status": "paid",
        "total": "$55.00",
        "payment_authorization_id": "auth_abc123",
    }
