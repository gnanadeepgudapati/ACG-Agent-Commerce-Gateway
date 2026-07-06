import uuid

from mercora.adapters.payment import Authorization, PaymentDeclined
from mercora.domain.money import Money


class MockPaymentAdapter:
    """Test-mode payment adapter. Declines when token == 'tok_decline'."""

    async def authorize(self, amount: Money, token: str, idem_key: str) -> Authorization:
        if token == "tok_decline":
            raise PaymentDeclined("card declined")
        return Authorization(id=f"auth_{uuid.uuid4().hex[:12]}", amount=amount)

    async def void(self, authorization_id: str) -> None:
        pass
