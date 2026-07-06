from typing import Protocol

from mercora.domain.money import Money


class TaxAdapter(Protocol):
    async def compute(self, amount: Money) -> Money: ...
