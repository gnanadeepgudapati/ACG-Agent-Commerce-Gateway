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


class OrderORM(Base):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(primary_key=True)
    cart_id: Mapped[str]
    currency: Mapped[str]
    subtotal_cents: Mapped[int]
    tax_cents: Mapped[int]
    total_cents: Mapped[int]
    status: Mapped[str]
    payment_authorization_id: Mapped[str]
    address_line1: Mapped[str]
    address_line2: Mapped[str | None]
    address_city: Mapped[str]
    address_state: Mapped[str | None]
    address_postal_code: Mapped[str]
    address_country: Mapped[str]
    items: Mapped[list["OrderItemORM"]] = relationship(
        back_populates="order", cascade="all, delete-orphan", lazy="selectin"
    )


class OrderItemORM(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.id"))
    sku: Mapped[str]
    quantity: Mapped[int]
    unit_price_cents: Mapped[int]
    order: Mapped["OrderORM"] = relationship(back_populates="items")


class IdempotencyKeyORM(Base):
    __tablename__ = "idempotency_keys"

    key: Mapped[str] = mapped_column(primary_key=True)
    order_id: Mapped[str]
