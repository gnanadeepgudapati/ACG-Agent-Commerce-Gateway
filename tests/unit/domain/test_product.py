import pytest
from pydantic import ValidationError

from mercora.domain.money import Money
from mercora.domain.product import Product


def make_product(**overrides: object) -> Product:
    defaults: dict[str, object] = dict(
        id="TSHIRT-BLUE-M",
        name="Classic Tee",
        description="A soft cotton t-shirt.",
        price=Money(amount_cents=2500, currency="USD"),
        attributes={"color": "blue", "size": "M"},
        stock_qty=10,
    )
    defaults.update(overrides)
    return Product(**defaults)  # type: ignore[arg-type]


def test_construct_product() -> None:
    p = make_product()
    assert p.id == "TSHIRT-BLUE-M"
    assert p.attributes["color"] == "blue"


def test_stock_qty_cannot_be_negative() -> None:
    with pytest.raises(ValidationError):
        make_product(stock_qty=-1)


def test_default_attributes_is_empty_dict() -> None:
    p = Product(
        id="SKU-1",
        name="Widget",
        description="A widget.",
        price=Money(amount_cents=500, currency="USD"),
        stock_qty=1,
    )
    assert p.attributes == {}
