from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mercora.domain.money import Money
from mercora.domain.product import Product
from mercora.infra.orm import ProductORM


def _to_domain(row: ProductORM) -> Product:
    return Product(
        id=row.id,
        name=row.name,
        description=row.description,
        price=Money(amount_cents=row.price_cents, currency=row.currency),
        attributes=row.attributes,
        stock_qty=row.stock_qty,
    )


class ProductRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, product: Product) -> None:
        self._session.add(
            ProductORM(
                id=product.id,
                name=product.name,
                description=product.description,
                price_cents=product.price.amount_cents,
                currency=product.price.currency,
                attributes=product.attributes,
                stock_qty=product.stock_qty,
            )
        )
        await self._session.commit()

    async def get(self, product_id: str) -> Product | None:
        row = await self._session.get(ProductORM, product_id)
        return _to_domain(row) if row else None

    async def search(
        self,
        *,
        q: str | None = None,
        color: str | None = None,
        size: str | None = None,
        max_price_cents: int | None = None,
    ) -> list[Product]:
        rows = (await self._session.execute(select(ProductORM))).scalars().all()
        products = [_to_domain(row) for row in rows]

        if q:
            needle = q.lower()
            products = [
                p for p in products if needle in p.name.lower() or needle in p.description.lower()
            ]
        if color:
            products = [
                p for p in products if p.attributes.get("color", "").lower() == color.lower()
            ]
        if size:
            products = [
                p for p in products if p.attributes.get("size", "").lower() == size.lower()
            ]
        if max_price_cents is not None:
            products = [p for p in products if p.price.amount_cents <= max_price_cents]

        return products
