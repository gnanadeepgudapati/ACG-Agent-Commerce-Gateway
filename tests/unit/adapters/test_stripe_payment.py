from dataclasses import dataclass, field
from typing import Any

import pytest
import stripe

from mercora.adapters.payment import PaymentDeclined
from mercora.adapters.stripe_payment import StripePaymentAdapter
from mercora.domain.money import Money


@dataclass
class _FakeIntent:
    id: str
    status: str


class _FakePaymentIntents:
    def __init__(self, intent: _FakeIntent | None = None, error: Exception | None = None) -> None:
        self._intent = intent
        self._error = error
        self.cancelled_ids: list[str] = []
        self.create_calls: list[dict[str, Any]] = []

    async def create_async(
        self, params: dict[str, Any], options: dict[str, Any] | None = None
    ) -> _FakeIntent:
        self.create_calls.append(params)
        if self._error:
            raise self._error
        assert self._intent is not None
        return self._intent

    async def cancel_async(self, authorization_id: str) -> None:
        self.cancelled_ids.append(authorization_id)


@dataclass
class _FakeV1:
    payment_intents: _FakePaymentIntents


@dataclass
class _FakeStripeClient:
    v1: _FakeV1 = field(init=False)
    payment_intents: _FakePaymentIntents

    def __post_init__(self) -> None:
        self.v1 = _FakeV1(self.payment_intents)


async def test_authorize_success() -> None:
    intents = _FakePaymentIntents(intent=_FakeIntent(id="pi_123", status="succeeded"))
    adapter = StripePaymentAdapter(_FakeStripeClient(intents))  # type: ignore[arg-type]

    auth = await adapter.authorize(
        Money(amount_cents=1000, currency="USD"), "pm_card_visa", "idem-1"
    )

    assert auth.id == "pi_123"
    assert auth.amount == Money(amount_cents=1000, currency="USD")
    assert intents.create_calls[0]["currency"] == "usd"


async def test_authorize_card_error_raises_payment_declined() -> None:
    error = stripe.CardError("declined", None, "card_declined")
    intents = _FakePaymentIntents(error=error)
    adapter = StripePaymentAdapter(_FakeStripeClient(intents))  # type: ignore[arg-type]

    with pytest.raises(PaymentDeclined):
        await adapter.authorize(
            Money(amount_cents=1000, currency="USD"), "pm_card_declined", "idem-1"
        )


async def test_authorize_non_succeeded_status_raises_payment_declined() -> None:
    intents = _FakePaymentIntents(intent=_FakeIntent(id="pi_123", status="requires_action"))
    adapter = StripePaymentAdapter(_FakeStripeClient(intents))  # type: ignore[arg-type]

    with pytest.raises(PaymentDeclined):
        await adapter.authorize(Money(amount_cents=1000, currency="USD"), "pm_card_visa", "idem-1")


async def test_void_cancels_payment_intent() -> None:
    intents = _FakePaymentIntents()
    adapter = StripePaymentAdapter(_FakeStripeClient(intents))  # type: ignore[arg-type]

    await adapter.void("pi_123")

    assert intents.cancelled_ids == ["pi_123"]
