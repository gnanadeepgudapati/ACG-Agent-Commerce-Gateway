import pytest
from pydantic import ValidationError

from mercora.domain.money import Money


def test_construct_from_cents() -> None:
    m = Money(amount_cents=1050, currency="USD")
    assert m.amount_cents == 1050
    assert m.currency == "USD"


def test_add_same_currency() -> None:
    assert Money(amount_cents=1000, currency="USD") + Money(
        amount_cents=500, currency="USD"
    ) == Money(amount_cents=1500, currency="USD")


def test_add_different_currency_raises() -> None:
    with pytest.raises(ValueError, match="currency"):
        Money(amount_cents=1000, currency="USD") + Money(amount_cents=500, currency="EUR")


def test_subtract() -> None:
    assert Money(amount_cents=1000, currency="USD") - Money(
        amount_cents=300, currency="USD"
    ) == Money(amount_cents=700, currency="USD")


def test_subtract_below_zero_raises() -> None:
    with pytest.raises(ValueError, match="negative"):
        Money(amount_cents=300, currency="USD") - Money(amount_cents=1000, currency="USD")


def test_multiply_by_quantity() -> None:
    assert Money(amount_cents=1000, currency="USD") * 3 == Money(
        amount_cents=3000, currency="USD"
    )


def test_negative_amount_rejected() -> None:
    with pytest.raises(ValidationError):
        Money(amount_cents=-1, currency="USD")


def test_ordering() -> None:
    cheap = Money(amount_cents=1000, currency="USD")
    pricey = Money(amount_cents=2000, currency="USD")
    assert cheap < pricey
    assert pricey > cheap
    assert cheap <= Money(amount_cents=1000, currency="USD")


def test_ordering_different_currency_raises() -> None:
    with pytest.raises(ValueError, match="currency"):
        _ = Money(amount_cents=1000, currency="USD") < Money(amount_cents=1000, currency="EUR")


def test_is_immutable() -> None:
    m = Money(amount_cents=1000, currency="USD")
    with pytest.raises(ValidationError):
        m.amount_cents = 2000  # type: ignore[misc]


def test_str_formats_as_currency() -> None:
    assert str(Money(amount_cents=1050, currency="USD")) == "$10.50"


def test_zero() -> None:
    assert Money.zero("USD") == Money(amount_cents=0, currency="USD")
