from mercora.domain.cart import Cart, CartItem
from mercora.domain.money import Money


def test_empty_cart_subtotal_is_zero() -> None:
    cart = Cart(id="cart-1", currency="USD")
    assert cart.subtotal() == Money.zero("USD")


def test_line_total_multiplies_unit_price_by_quantity() -> None:
    item = CartItem(sku="SKU-1", quantity=3, unit_price=Money(amount_cents=1000, currency="USD"))
    assert item.line_total() == Money(amount_cents=3000, currency="USD")


def test_cart_subtotal_sums_line_items() -> None:
    cart = Cart(
        id="cart-1",
        currency="USD",
        items=[
            CartItem(sku="A", quantity=2, unit_price=Money(amount_cents=500, currency="USD")),
            CartItem(sku="B", quantity=1, unit_price=Money(amount_cents=1500, currency="USD")),
        ],
    )
    assert cart.subtotal() == Money(amount_cents=2500, currency="USD")


def test_quantity_must_be_positive() -> None:
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        CartItem(sku="A", quantity=0, unit_price=Money(amount_cents=500, currency="USD"))
