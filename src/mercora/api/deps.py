from collections.abc import AsyncIterator

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from mercora.adapters.payment import PaymentAdapter
from mercora.adapters.tax import TaxAdapter


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    session_maker = request.app.state.session_maker
    async with session_maker() as session:
        yield session


def get_payment_adapter(request: Request) -> PaymentAdapter:
    return request.app.state.payment_adapter  # type: ignore[no-any-return]


def get_tax_adapter(request: Request) -> TaxAdapter:
    return request.app.state.tax_adapter  # type: ignore[no-any-return]
