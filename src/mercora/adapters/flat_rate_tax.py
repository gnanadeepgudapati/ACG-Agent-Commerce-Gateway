from mercora.domain.money import Money


class FlatRateTaxAdapter:
    def __init__(self, rate: float = 0.08) -> None:
        self._rate = rate

    async def compute(self, amount: Money) -> Money:
        return Money(amount_cents=round(amount.amount_cents * self._rate), currency=amount.currency)
