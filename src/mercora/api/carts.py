from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from mercora.api.deps import Principal, get_session, require_scope
from mercora.domain.cart import Cart
from mercora.infra.cart_repository import CartRepository
from mercora.infra.product_repository import ProductRepository

router = APIRouter(prefix="/v1/carts", tags=["carts"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]
ReadScope = Annotated[Principal, Depends(require_scope("cart:read"))]
WriteScope = Annotated[Principal, Depends(require_scope("cart:write"))]


class AddItemRequest(BaseModel):
    sku: str = Field(min_length=1)
    quantity: int = Field(gt=0)


async def _get_cart_or_404(repo: CartRepository, cart_id: str, partner_id: str) -> Cart:
    cart = await repo.get(cart_id, partner_id)
    if cart is None:
        raise HTTPException(status_code=404, detail="Cart not found")
    return cart


@router.post("", response_model=Cart, status_code=201)
async def create_cart(session: SessionDep, principal: WriteScope) -> Cart:
    return await CartRepository(session).create(principal.partner_id)


@router.get("/{cart_id}", response_model=Cart)
async def view_cart(cart_id: str, session: SessionDep, principal: ReadScope) -> Cart:
    return await _get_cart_or_404(CartRepository(session), cart_id, principal.partner_id)


@router.post("/{cart_id}/items", response_model=Cart)
async def add_item(
    cart_id: str, body: AddItemRequest, session: SessionDep, principal: WriteScope
) -> Cart:
    cart_repo = CartRepository(session)
    await _get_cart_or_404(cart_repo, cart_id, principal.partner_id)

    product = await ProductRepository(session).get(body.sku)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    if body.quantity > product.stock_qty:
        raise HTTPException(
            status_code=409,
            detail={"code": "OUT_OF_STOCK", "message": f"Only {product.stock_qty} in stock"},
        )

    return await cart_repo.add_item(
        cart_id,
        principal.partner_id,
        sku=body.sku,
        quantity=body.quantity,
        unit_price=product.price,
    )


@router.delete("/{cart_id}/items/{sku}", response_model=Cart)
async def remove_item(cart_id: str, sku: str, session: SessionDep, principal: WriteScope) -> Cart:
    cart_repo = CartRepository(session)
    await _get_cart_or_404(cart_repo, cart_id, principal.partner_id)
    return await cart_repo.remove_item(cart_id, principal.partner_id, sku)
