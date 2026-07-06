import time

import jwt
import pytest

from mercora.core.security import create_access_token, decode_access_token


def test_round_trip() -> None:
    token = create_access_token(
        client_id="agent-demo", partner_id="demo-partner", scopes=frozenset({"catalog:read"})
    )
    payload = decode_access_token(token)

    assert payload["sub"] == "agent-demo"
    assert payload["partner_id"] == "demo-partner"
    assert payload["scope"] == "catalog:read"


def test_expired_token_rejected() -> None:
    token = create_access_token(
        client_id="agent-demo",
        partner_id="demo-partner",
        scopes=frozenset({"catalog:read"}),
        expires_in=-1,
    )
    with pytest.raises(jwt.ExpiredSignatureError):
        decode_access_token(token)


def test_wrong_signature_rejected() -> None:
    token = create_access_token(
        client_id="agent-demo", partner_id="demo-partner", scopes=frozenset({"catalog:read"})
    )
    tampered = token[:-1] + ("A" if token[-1] != "A" else "B")
    with pytest.raises(jwt.PyJWTError):
        decode_access_token(tampered)


def test_multiple_scopes_sorted_and_space_separated() -> None:
    token = create_access_token(
        client_id="agent-demo",
        partner_id="demo-partner",
        scopes=frozenset({"checkout:write", "catalog:read"}),
    )
    payload = decode_access_token(token)
    assert payload["scope"] == "catalog:read checkout:write"


def test_includes_standard_claims() -> None:
    before = int(time.time())
    token = create_access_token(
        client_id="agent-demo", partner_id="demo-partner", scopes=frozenset({"catalog:read"})
    )
    payload = decode_access_token(token)

    assert payload["iss"] == "mercora"
    assert payload["aud"] == "mercora-api"
    assert payload["iat"] >= before
    assert payload["exp"] > payload["iat"]
