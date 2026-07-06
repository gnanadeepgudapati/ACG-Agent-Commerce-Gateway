from dataclasses import dataclass


@dataclass(frozen=True)
class OAuthClient:
    client_id: str
    client_secret: str
    partner_id: str
    scopes: frozenset[str]


CLIENTS: dict[str, OAuthClient] = {
    "agent-demo": OAuthClient(
        client_id="agent-demo",
        client_secret="agent-demo-secret",
        partner_id="demo-partner",
        scopes=frozenset(
            {"catalog:read", "cart:read", "cart:write", "checkout:write", "orders:read"}
        ),
    ),
    "partner-acme": OAuthClient(
        client_id="partner-acme",
        client_secret="partner-acme-secret",
        partner_id="acme-partner",
        scopes=frozenset({"catalog:read", "checkout:write", "orders:read"}),
    ),
}
