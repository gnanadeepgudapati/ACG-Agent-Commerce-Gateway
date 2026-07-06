from mercora.adapters.mock_shipping import MockShippingAdapter
from mercora.domain.address import Address
from mercora.domain.money import Money

ADDRESS = Address(line1="1 Infinite Loop", city="Cupertino", postal_code="95014")


async def test_quote_returns_flat_rate() -> None:
    adapter = MockShippingAdapter(flat_rate_cents=750, eta_days=3)

    quote = await adapter.quote(ADDRESS, [])

    assert quote.cost == Money(amount_cents=750, currency="USD")
    assert quote.eta_days == 3


async def test_create_shipment_returns_unique_ids() -> None:
    adapter = MockShippingAdapter()

    a = await adapter.create_shipment("order-1")
    b = await adapter.create_shipment("order-2")

    assert a.id != b.id
    assert a.tracking_number != b.tracking_number
