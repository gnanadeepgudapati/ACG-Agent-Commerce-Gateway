from pydantic import BaseModel, Field

from mercora.domain.money import Money


class CartItem(BaseModel):
    sku: str = Field(min_length=1)
    quantity: int = Field(gt=0)
    unit_price: Money

    def line_total(self) -> Money:
        return self.unit_price * self.quantity


class Cart(BaseModel):
    id: str = Field(min_length=1)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    items: list[CartItem] = Field(default_factory=list)

    def subtotal(self) -> Money:
        total = Money.zero(self.currency)
        for item in self.items:
            total = total + item.line_total()
        return total
