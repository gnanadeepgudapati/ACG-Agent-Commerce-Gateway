from typing import Any


def _fmt(money: dict[str, Any]) -> str:
    return f"${money['amount_cents'] / 100:.2f}"


def shape_product(product: dict[str, Any]) -> dict[str, Any]:
    return {
        "sku": product["id"],
        "name": product["name"],
        "price": _fmt(product["price"]),
        "attributes": product["attributes"],
        "in_stock": product["stock_qty"] > 0,
    }


def shape_cart(cart: dict[str, Any]) -> dict[str, Any]:
    return {
        "cart_id": cart["id"],
        "items": [
            {
                "sku": item["sku"],
                "quantity": item["quantity"],
                "line_total": _fmt(item["line_total"]),
            }
            for item in cart["items"]
        ],
        "subtotal": _fmt(cart["subtotal"]),
    }


def shape_order(order: dict[str, Any]) -> dict[str, Any]:
    return {
        "order_id": order["id"],
        "status": order["status"],
        "total": _fmt(order["total"]),
        "payment_authorization_id": order["payment_authorization_id"],
    }
