from tests.agentic.invariants import check_purchase_invariants

CART_WITH_ITEM = {
    "cart_id": "cart-1",
    "items": [{"sku": "TSHIRT-BLUE-M", "quantity": 1, "line_total": "$25.00"}],
    "subtotal": "$25.00",
}
PAID_ORDER = {
    "order_id": "order-1",
    "status": "paid",
    "total": "$27.00",
    "payment_authorization_id": "auth_123",
}


def test_all_invariants_pass_for_a_correct_purchase() -> None:
    results = check_purchase_invariants(
        cart=CART_WITH_ITEM, order=PAID_ORDER, expected_sku="TSHIRT-BLUE-M", max_total_cents=3000
    )
    assert all(r.passed for r in results)
    assert len(results) >= 3


def test_missing_order_fails_and_short_circuits() -> None:
    results = check_purchase_invariants(
        cart=CART_WITH_ITEM, order=None, expected_sku="TSHIRT-BLUE-M", max_total_cents=3000
    )
    assert len(results) == 1
    assert results[0].passed is False


def test_wrong_sku_fails_that_invariant() -> None:
    wrong_cart = {**CART_WITH_ITEM, "items": [{"sku": "TSHIRT-RED-M", "quantity": 1}]}
    results = check_purchase_invariants(
        cart=wrong_cart, order=PAID_ORDER, expected_sku="TSHIRT-BLUE-M", max_total_cents=3000
    )
    sku_result = next(r for r in results if "correct product" in r.description)
    assert sku_result.passed is False


def test_over_budget_fails_that_invariant() -> None:
    results = check_purchase_invariants(
        cart=CART_WITH_ITEM, order=PAID_ORDER, expected_sku="TSHIRT-BLUE-M", max_total_cents=2000
    )
    budget_result = next(r for r in results if "budget" in r.description)
    assert budget_result.passed is False


def test_unpaid_order_status_fails() -> None:
    results = check_purchase_invariants(
        cart=CART_WITH_ITEM,
        order={**PAID_ORDER, "status": "failed"},
        expected_sku="TSHIRT-BLUE-M",
        max_total_cents=3000,
    )
    status_result = next(r for r in results if "status" in r.description)
    assert status_result.passed is False
