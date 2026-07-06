import logging
import time
import uuid
from collections.abc import Awaitable, Callable

from fastapi import Request, Response

from mercora.core.logging import request_id_var
from mercora.core.metrics import http_requests_total

_logger = logging.getLogger("mercora.request")


async def request_context_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    token = request_id_var.set(request_id)
    start = time.monotonic()
    try:
        response = await call_next(request)
    finally:
        request_id_var.reset(token)
    duration_ms = (time.monotonic() - start) * 1000
    response.headers["X-Request-ID"] = request_id

    route = request.scope.get("route")
    path = getattr(route, "path", request.url.path)
    http_requests_total.labels(
        method=request.method, path=path, status=str(response.status_code)
    ).inc()

    _logger.info(
        "request completed",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(duration_ms, 2),
        },
    )
    return response
