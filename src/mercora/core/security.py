import time
import uuid
from typing import Any

import jwt

from mercora.core.config import settings

ALGORITHM = "HS256"


def create_access_token(
    *, client_id: str, partner_id: str, scopes: frozenset[str], expires_in: int = 3600
) -> str:
    now = int(time.time())
    payload = {
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "sub": client_id,
        "partner_id": partner_id,
        "scope": " ".join(sorted(scopes)),
        "iat": now,
        "exp": now + expires_in,
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    return jwt.decode(
        token,
        settings.jwt_secret,
        algorithms=[ALGORITHM],
        audience=settings.jwt_audience,
        issuer=settings.jwt_issuer,
    )
