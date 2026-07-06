import pytest
from pydantic import ValidationError

from mercora.domain.address import Address


def test_construct_minimal_address() -> None:
    addr = Address(line1="1 Infinite Loop", city="Cupertino", postal_code="95014")
    assert addr.country == "US"
    assert addr.line2 is None


def test_country_must_be_two_letters() -> None:
    with pytest.raises(ValidationError):
        Address(line1="1 Infinite Loop", city="Cupertino", postal_code="95014", country="USA")


def test_blank_line1_rejected() -> None:
    with pytest.raises(ValidationError):
        Address(line1="", city="Cupertino", postal_code="95014")
