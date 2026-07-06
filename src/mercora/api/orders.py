from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from mercora.api.deps import get_session
from mercora.domain.order import Order
from mercora.infra.order_repository import OrderRepository

router = APIRouter(prefix="/v1/orders", tags=["orders"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.get("/{order_id}", response_model=Order)
async def get_order_status(order_id: str, session: SessionDep) -> Order:
    order = await OrderRepository(session).get(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return order
