from collections.abc import AsyncIterator

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from mercora.infra.db import init_db


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
