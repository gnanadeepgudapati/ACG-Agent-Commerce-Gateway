from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from mcp.server.fastmcp import FastMCP
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from mercora.api.deps import get_session
from mercora.infra.db import init_db
from mercora.infra.product_repository import ProductRepository
from mercora.infra.seed_data import CATALOG
from mercora.main import app
from mercora.mcp_server.client import MercoraClient
from mercora.mcp_server.server import build_server


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--runs", action="store", default=5, type=int, help="Number of agentic eval runs"
    )


@pytest_asyncio.fixture
async def seeded_mcp_server() -> AsyncIterator[FastMCP]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", poolclass=StaticPool)
    await init_db(engine)
    session_maker = async_sessionmaker(engine, expire_on_commit=False)

    async def override_get_session() -> AsyncIterator[object]:
        async with session_maker() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session

    async with session_maker() as session:
        repo = ProductRepository(session)
        for product in CATALOG:
            await repo.add(product)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as unauth_client:
        token_resp = await unauth_client.post(
            "/oauth/token",
            data={
                "grant_type": "client_credentials",
                "client_id": "agent-demo",
                "client_secret": "agent-demo-secret",
            },
        )
        token = token_resp.json()["access_token"]

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={"Authorization": f"Bearer {token}"},
    ) as http_client:
        yield build_server(MercoraClient(http_client))

    app.dependency_overrides.clear()
    await engine.dispose()
