import os

import httpx

from mercora.core.logging import configure_logging
from mercora.core.telemetry import configure_tracing
from mercora.mcp_server.client import MercoraClient
from mercora.mcp_server.server import build_server


def main() -> None:
    configure_logging()
    configure_tracing(service_name="mercora-mcp-server")
    base_url = os.environ.get("MERCORA_API_URL", "http://localhost:8000")
    token = os.environ.get("MERCORA_API_TOKEN")
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    http_client = httpx.AsyncClient(base_url=base_url, headers=headers)
    client = MercoraClient(http_client)
    server = build_server(client)
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
