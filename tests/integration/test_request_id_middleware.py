from collections.abc import AsyncIterator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from mercora.main import app


@pytest_asyncio.fixture
async def client() -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def test_response_includes_generated_request_id(client: AsyncClient) -> None:
    resp = await client.get("/healthz")
    assert resp.status_code == 200
    assert resp.headers["x-request-id"]


async def test_incoming_request_id_is_echoed_back(client: AsyncClient) -> None:
    resp = await client.get("/healthz", headers={"X-Request-ID": "client-supplied-id"})
    assert resp.headers["x-request-id"] == "client-supplied-id"


async def test_different_requests_get_different_ids(client: AsyncClient) -> None:
    first = await client.get("/healthz")
    second = await client.get("/healthz")
    assert first.headers["x-request-id"] != second.headers["x-request-id"]
