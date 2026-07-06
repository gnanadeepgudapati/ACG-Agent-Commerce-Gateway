from typing import Protocol

from pydantic import BaseModel

from mercora.domain.money import Money


class Authorization(BaseModel):
    id: str
    amount: Money


class PaymentDeclined(Exception):
    pass


class PaymentAdapter(Protocol):
    async def authorize(self, amount: Money, token: str, idem_key: str) -> Authorization: ...

    async def void(self, authorization_id: str) -> None: ...
