from collections.abc import AsyncIterator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from mercora.api.deps import get_session
from mercora.main import app


@pytest_asyncio.fixture
async def client(session: AsyncSession) -> AsyncIterator[AsyncClient]:
    async def override_get_session() -> AsyncIterator[AsyncSession]:
        yield session

    app.dependency_overrides[get_session] = override_get_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


async def _token(client: AsyncClient, client_id: str, client_secret: str) -> str:
    resp = await client.post(
        "/oauth/token",
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        },
    )
    token: str = resp.json()["access_token"]
    return token


async def test_missing_token_rejected(client: AsyncClient) -> None:
    resp = await client.get("/v1/products")
    assert resp.status_code == 401


async def test_invalid_token_rejected(client: AsyncClient) -> None:
    resp = await client.get("/v1/products", headers={"Authorization": "Bearer not-a-real-token"})
    assert resp.status_code == 401


async def test_valid_token_with_required_scope_allowed(client: AsyncClient) -> None:
    token = await _token(client, "agent-demo", "agent-demo-secret")
    resp = await client.get("/v1/products", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200


async def test_token_missing_required_scope_forbidden(client: AsyncClient) -> None:
    token = await _token(client, "partner-acme", "partner-acme-secret")
    resp = await client.post("/v1/carts", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403
