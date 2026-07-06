from typing import Annotated

from fastapi import APIRouter, Form, HTTPException
from pydantic import BaseModel

from mercora.core.oauth_clients import CLIENTS
from mercora.core.security import create_access_token

router = APIRouter(prefix="/oauth", tags=["oauth"])


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    scope: str


@router.post("/token", response_model=TokenResponse)
async def issue_token(
    grant_type: Annotated[str, Form()],
    client_id: Annotated[str, Form()],
    client_secret: Annotated[str, Form()],
    scope: Annotated[str | None, Form()] = None,
) -> TokenResponse:
    if grant_type != "client_credentials":
        raise HTTPException(status_code=400, detail="unsupported_grant_type")

    client = CLIENTS.get(client_id)
    if client is None or client.client_secret != client_secret:
        raise HTTPException(status_code=401, detail="invalid_client")

    requested_scopes = frozenset(scope.split()) if scope else client.scopes
    if not requested_scopes.issubset(client.scopes):
        raise HTTPException(status_code=400, detail="invalid_scope")

    token = create_access_token(
        client_id=client.client_id, partner_id=client.partner_id, scopes=requested_scopes
    )
    return TokenResponse(
        access_token=token, expires_in=3600, scope=" ".join(sorted(requested_scopes))
    )
