from collections.abc import AsyncIterator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from mercora.main import app


@pytest_asyncio.fixture
async def client() -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def test_issue_token_success(client: AsyncClient) -> None:
    resp = await client.post(
        "/oauth/token",
        data={
            "grant_type": "client_credentials",
            "client_id": "agent-demo",
            "client_secret": "agent-demo-secret",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert "catalog:read" in body["scope"]
    assert body["access_token"]


async def test_issue_token_wrong_secret(client: AsyncClient) -> None:
    resp = await client.post(
        "/oauth/token",
        data={
            "grant_type": "client_credentials",
            "client_id": "agent-demo",
            "client_secret": "wrong-secret",
        },
    )
    assert resp.status_code == 401


async def test_issue_token_unknown_client(client: AsyncClient) -> None:
    resp = await client.post(
        "/oauth/token",
        data={
            "grant_type": "client_credentials",
            "client_id": "nobody",
            "client_secret": "whatever",
        },
    )
    assert resp.status_code == 401


async def test_issue_token_unsupported_grant_type(client: AsyncClient) -> None:
    resp = await client.post(
        "/oauth/token",
        data={
            "grant_type": "password",
            "client_id": "agent-demo",
            "client_secret": "agent-demo-secret",
        },
    )
    assert resp.status_code == 400


async def test_issue_token_scope_beyond_client_grant_rejected(client: AsyncClient) -> None:
    resp = await client.post(
        "/oauth/token",
        data={
            "grant_type": "client_credentials",
            "client_id": "partner-acme",
            "client_secret": "partner-acme-secret",
            "scope": "cart:write",
        },
    )
    assert resp.status_code == 400


async def test_issue_token_narrower_scope_allowed(client: AsyncClient) -> None:
    resp = await client.post(
        "/oauth/token",
        data={
            "grant_type": "client_credentials",
            "client_id": "agent-demo",
            "client_secret": "agent-demo-secret",
            "scope": "catalog:read",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["scope"] == "catalog:read"
