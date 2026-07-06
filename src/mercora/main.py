from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from mercora.adapters.flat_rate_tax import FlatRateTaxAdapter
from mercora.adapters.mock_payment import MockPaymentAdapter
from mercora.api import carts, checkout, oauth, orders, products
from mercora.core.config import settings
from mercora.core.rate_limit import RateLimiter
from mercora.infra.db import create_engine_and_sessionmaker, init_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    engine, session_maker = create_engine_and_sessionmaker(settings.database_dsn)
    await init_db(engine)
    app.state.session_maker = session_maker
    app.state.payment_adapter = MockPaymentAdapter()
    app.state.tax_adapter = FlatRateTaxAdapter()
    yield
    await engine.dispose()


app = FastAPI(title="Mercora", lifespan=lifespan)
app.state.rate_limiter = RateLimiter(
    max_requests=settings.rate_limit_max_requests,
    window_seconds=settings.rate_limit_window_seconds,
)
app.include_router(oauth.router)
app.include_router(products.router)
app.include_router(carts.router)
app.include_router(checkout.router)
app.include_router(orders.router)


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/readyz")
async def readyz() -> dict[str, str]:
    return {"status": "ready"}
