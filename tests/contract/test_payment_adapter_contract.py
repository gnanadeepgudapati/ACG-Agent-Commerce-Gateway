"""Contract tests: every PaymentAdapter implementation must satisfy the same behavioral
guarantees, so swapping providers never requires touching orchestration code."""

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import pytest
import stripe

from mercora.adapters.mock_payment import MockPaymentAdapter
from mercora.adapters.payment import PaymentAdapter, PaymentDeclined
from mercora.adapters.stripe_payment import StripePaymentAdapter
from mercora.domain.money import Money


@dataclass
class _FakeIntent:
    id: str
    status: str


class _FakePaymentIntents:
    def __init__(self, decline: bool = False) -> None:
        self._decline = decline

    async def create_async(
        self, params: dict[str, Any], options: dict[str, Any] | None = None
    ) -> _FakeIntent:
        if self._decline:
            raise stripe.CardError("declined", None, "card_declined")
        return _FakeIntent(id="pi_contract_test", status="succeeded")

    async def cancel_async(self, authorization_id: str) -> None:
        pass


@dataclass
class _FakeV1:
    payment_intents: _FakePaymentIntents


@dataclass
class _FakeStripeClient:
    v1: _FakeV1 = field(init=False)
    payment_intents: _FakePaymentIntents

    def __post_init__(self) -> None:
        self.v1 = _FakeV1(self.payment_intents)


def _make_mock_adapter(decline: bool) -> PaymentAdapter:
    return MockPaymentAdapter()


def _make_stripe_adapter(decline: bool) -> PaymentAdapter:
    client = _FakeStripeClient(_FakePaymentIntents(decline=decline))
    return StripePaymentAdapter(client)  # type: ignore[arg-type]


ADAPTER_FACTORIES: list[tuple[str, Callable[[bool], PaymentAdapter], str, str]] = [
    ("mock", _make_mock_adapter, "tok_ok", "tok_decline"),
    ("stripe", _make_stripe_adapter, "pm_card_visa", "pm_card_visa"),
]


@pytest.mark.parametrize(
    "name,factory,success_token,_decline_token",
    ADAPTER_FACTORIES,
    ids=[a[0] for a in ADAPTER_FACTORIES],
)
async def test_authorize_returns_authorization_matching_amount(
    name: str, factory: Callable[[bool], PaymentAdapter], success_token: str, _decline_token: str
) -> None:
    adapter = factory(False)
    amount = Money(amount_cents=1500, currency="USD")

    auth = await adapter.authorize(amount, success_token, "idem-contract-1")

    assert auth.amount == amount
    assert auth.id


@pytest.mark.parametrize(
    "name,factory,_success_token,decline_token",
    ADAPTER_FACTORIES,
    ids=[a[0] for a in ADAPTER_FACTORIES],
)
async def test_declined_payment_raises_payment_declined(
    name: str, factory: Callable[[bool], PaymentAdapter], _success_token: str, decline_token: str
) -> None:
    adapter = factory(True)
    amount = Money(amount_cents=1500, currency="USD")

    with pytest.raises(PaymentDeclined):
        await adapter.authorize(amount, decline_token, "idem-contract-2")


@pytest.mark.parametrize(
    "name,factory,success_token,_decline_token",
    ADAPTER_FACTORIES,
    ids=[a[0] for a in ADAPTER_FACTORIES],
)
async def test_void_does_not_raise_for_valid_authorization(
    name: str, factory: Callable[[bool], PaymentAdapter], success_token: str, _decline_token: str
) -> None:
    adapter = factory(False)
    amount = Money(amount_cents=1500, currency="USD")
    auth = await adapter.authorize(amount, success_token, "idem-contract-3")

    await adapter.void(auth.id)
