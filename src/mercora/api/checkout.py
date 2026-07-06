from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from mercora.adapters.payment import PaymentAdapter
from mercora.adapters.tax import TaxAdapter
from mercora.api.deps import get_payment_adapter, get_session, get_tax_adapter
from mercora.domain.address import Address
from mercora.domain.order import Order
from mercora.infra.cart_repository import CartRepository
from mercora.infra.idempotency_repository import IdempotencyRepository
from mercora.infra.order_repository import OrderRepository
from mercora.infra.product_repository import ProductRepository
from mercora.orchestration.checkout_saga import CheckoutSaga
from mercora.orchestration.errors import CheckoutError

router = APIRouter(prefix="/v1", tags=["checkout"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]
PaymentDep = Annotated[PaymentAdapter, Depends(get_payment_adapter)]
TaxDep = Annotated[TaxAdapter, Depends(get_tax_adapter)]

_ERROR_STATUS = {
    "CART_NOT_FOUND": 404,
    "CART_EMPTY": 400,
    "OUT_OF_STOCK": 409,
    "PAYMENT_DECLINED": 402,
}


class CheckoutRequest(BaseModel):
    cart_id: str = Field(min_length=1)
    address: Address
    payment_token: str = Field(min_length=1)
    idempotency_key: str = Field(min_length=1)


@router.post("/checkout", response_model=Order, status_code=201)
async def checkout(
    body: CheckoutRequest, session: SessionDep, payment_adapter: PaymentDep, tax_adapter: TaxDep
) -> Order:
    saga = CheckoutSaga(
        cart_repo=CartRepository(session),
        product_repo=ProductRepository(session),
        order_repo=OrderRepository(session),
        idempotency_repo=IdempotencyRepository(session),
        payment_adapter=payment_adapter,
        tax_adapter=tax_adapter,
    )
    try:
        return await saga.checkout(
            cart_id=body.cart_id,
            address=body.address,
            payment_token=body.payment_token,
            idempotency_key=body.idempotency_key,
        )
    except CheckoutError as exc:
        status_code = _ERROR_STATUS.get(exc.code, 400)
        raise HTTPException(
            status_code=status_code, detail={"code": exc.code, "message": str(exc)}
        ) from exc
