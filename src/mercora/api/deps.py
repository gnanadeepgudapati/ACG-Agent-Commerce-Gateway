from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from mercora.adapters.payment import PaymentAdapter
from mercora.adapters.tax import TaxAdapter
from mercora.core.metrics import partner_requests_total
from mercora.core.rate_limit import RateLimiter
from mercora.core.security import decode_access_token

_bearer_scheme = HTTPBearer(auto_error=False)


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    session_maker = request.app.state.session_maker
    async with session_maker() as session:
        yield session


def get_payment_adapter(request: Request) -> PaymentAdapter:
    return request.app.state.payment_adapter  # type: ignore[no-any-return]


def get_tax_adapter(request: Request) -> TaxAdapter:
    return request.app.state.tax_adapter  # type: ignore[no-any-return]


@dataclass(frozen=True)
class Principal:
    client_id: str
    partner_id: str
    scopes: frozenset[str]


async def get_current_principal(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
) -> Principal:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Missing bearer token")
    try:
        payload = decode_access_token(credentials.credentials)
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired token") from exc

    partner_id = payload["partner_id"]
    limiter: RateLimiter = request.app.state.rate_limiter
    if not limiter.allow(partner_id):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    partner_requests_total.labels(partner_id=partner_id).inc()

    return Principal(
        client_id=payload["sub"],
        partner_id=partner_id,
        scopes=frozenset(payload.get("scope", "").split()),
    )


def require_scope(scope: str) -> Callable[[Principal], Principal]:
    def _checker(
        principal: Annotated[Principal, Depends(get_current_principal)],
    ) -> Principal:
        if scope not in principal.scopes:
            raise HTTPException(status_code=403, detail=f"Missing required scope: {scope}")
        return principal

    return _checker
