from sqlalchemy import JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mercora.infra.db import Base


class ProductORM(Base):
    __tablename__ = "products"

    id: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str]
    description: Mapped[str]
    price_cents: Mapped[int]
    currency: Mapped[str]
    attributes: Mapped[dict[str, str]] = mapped_column(JSON, default=dict)
    stock_qty: Mapped[int]


class CartORM(Base):
    __tablename__ = "carts"

    id: Mapped[str] = mapped_column(primary_key=True)
    currency: Mapped[str]
    items: Mapped[list["CartItemORM"]] = relationship(
        back_populates="cart", cascade="all, delete-orphan", lazy="selectin"
    )


class CartItemORM(Base):
    __tablename__ = "cart_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    cart_id: Mapped[str] = mapped_column(ForeignKey("carts.id"))
    sku: Mapped[str]
    quantity: Mapped[int]
    unit_price_cents: Mapped[int]
    cart: Mapped["CartORM"] = relationship(back_populates="items")
