from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from mercora.api.deps import get_session
from mercora.domain.product import Product
from mercora.infra.product_repository import ProductRepository

router = APIRouter(prefix="/v1/products", tags=["products"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.get("", response_model=list[Product])
async def search_products(
    session: SessionDep,
    q: str | None = None,
    color: str | None = None,
    size: str | None = None,
    max_price_cents: int | None = None,
) -> list[Product]:
    repo = ProductRepository(session)
    return await repo.search(q=q, color=color, size=size, max_price_cents=max_price_cents)


@router.get("/{product_id}", response_model=Product)
async def get_product(product_id: str, session: SessionDep) -> Product:
    repo = ProductRepository(session)
    product = await repo.get(product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product
