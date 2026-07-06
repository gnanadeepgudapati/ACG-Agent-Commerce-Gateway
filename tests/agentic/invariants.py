from dataclasses import dataclass


@dataclass
class Invariant:
    description: str
    passed: bool


def _parse_money(formatted: str) -> int:
    return round(float(formatted.lstrip("$")) * 100)


def check_purchase_invariants(
    *,
    cart: dict | None,
    order: dict | None,
    expected_sku: str,
    max_total_cents: int,
) -> list[Invariant]:
    if order is None:
        return [Invariant("order was created", False)]

    results = [
        Invariant("order was created", True),
        Invariant("order status is paid", order.get("status") == "paid"),
    ]

    purchased_skus = {item["sku"] for item in (cart or {}).get("items", [])}
    results.append(
        Invariant(
            f"cart contained the correct product ({expected_sku})", expected_sku in purchased_skus
        )
    )

    total_cents = _parse_money(order.get("total", "$999999.99"))
    results.append(
        Invariant(
            f"total within budget (<= {max_total_cents} cents)", total_cents <= max_total_cents
        )
    )

    return results
