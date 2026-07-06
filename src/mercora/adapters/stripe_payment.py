import stripe

from mercora.adapters.payment import Authorization, PaymentDeclined
from mercora.domain.money import Money


class StripePaymentAdapter:
    """Payment adapter backed by the Stripe API (test mode in local/dev)."""

    def __init__(self, client: stripe.StripeClient) -> None:
        self._client = client

    async def authorize(self, amount: Money, token: str, idem_key: str) -> Authorization:
        try:
            intent = await self._client.v1.payment_intents.create_async(
                {
                    "amount": amount.amount_cents,
                    "currency": amount.currency.lower(),
                    "payment_method": token,
                    "confirm": True,
                    "off_session": True,
                    "automatic_payment_methods": {
                        "enabled": True,
                        "allow_redirects": "never",
                    },
                },
                options={"idempotency_key": idem_key},
            )
        except stripe.CardError as exc:
            raise PaymentDeclined(str(exc)) from exc

        if intent.status != "succeeded":
            raise PaymentDeclined(f"payment intent ended in status: {intent.status}")

        return Authorization(id=intent.id, amount=amount)

    async def void(self, authorization_id: str) -> None:
        await self._client.v1.payment_intents.cancel_async(authorization_id)
