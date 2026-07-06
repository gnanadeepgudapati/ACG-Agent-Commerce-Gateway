from collections.abc import AsyncIterator, Callable

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from mercora.api.deps import Principal
from mercora.domain.money import Money
from mercora.domain.product import Product
from mercora.infra.db import init_db

TEST_PARTNER_ID = "demo-partner"
OTHER_PARTNER_ID = "other-partner"

ALL_SCOPES = frozenset({"catalog:read", "cart:read", "cart:write", "checkout:write", "orders:read"})


@pytest.fixture
def make_principal() -> Callable[..., Principal]:
    def _make(partner_id: str = TEST_PARTNER_ID, scopes: frozenset[str] = ALL_SCOPES) -> Principal:
        return Principal(client_id="test-client", partner_id=partner_id, scopes=scopes)

    return _make


@pytest.fixture
def principal(make_principal: Callable[..., Principal]) -> Principal:
    return make_principal()


@pytest.fixture
def make_product() -> Callable[..., Product]:
    def _make(**overrides: object) -> Product:
        defaults: dict[str, object] = dict(
            id="TSHIRT-BLUE-M",
            name="Classic Tee",
            description="A soft cotton t-shirt.",
            price=Money(amount_cents=2500, currency="USD"),
            attributes={"color": "blue", "size": "M"},
            stock_qty=10,
        )
        defaults.update(overrides)
        return Product(**defaults)  # type: ignore[arg-type]

    return _make


@pytest_asyncio.fixture
async def session() -> AsyncIterator[AsyncSession]:
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
    )
    await init_db(engine)
    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    async with session_maker() as db_session:
        yield db_session
    await engine.dispose()
