from __future__ import annotations

from functools import total_ordering
from typing import Self

from pydantic import BaseModel, ConfigDict, Field


@total_ordering
class Money(BaseModel):
    """An exact monetary amount, stored as integer minor units (cents) to avoid float rounding."""

    model_config = ConfigDict(frozen=True)

    amount_cents: int = Field(ge=0)
    currency: str = Field(min_length=3, max_length=3)

    @classmethod
    def zero(cls, currency: str) -> Self:
        return cls(amount_cents=0, currency=currency)

    def _check_same_currency(self, other: Money) -> None:
        if self.currency != other.currency:
            raise ValueError(
                f"currency mismatch: {self.currency} vs {other.currency}"
            )

    def __add__(self, other: Money) -> Money:
        self._check_same_currency(other)
        return Money(amount_cents=self.amount_cents + other.amount_cents, currency=self.currency)

    def __sub__(self, other: Money) -> Money:
        self._check_same_currency(other)
        result = self.amount_cents - other.amount_cents
        if result < 0:
            raise ValueError("subtraction would result in a negative Money amount")
        return Money(amount_cents=result, currency=self.currency)

    def __mul__(self, quantity: int) -> Money:
        return Money(amount_cents=self.amount_cents * quantity, currency=self.currency)

    def __lt__(self, other: Money) -> bool:
        self._check_same_currency(other)
        return self.amount_cents < other.amount_cents

    def __str__(self) -> str:
        return f"${self.amount_cents / 100:.2f}"
