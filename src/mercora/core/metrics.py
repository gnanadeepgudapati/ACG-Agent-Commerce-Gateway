from prometheus_client import CONTENT_TYPE_LATEST, Counter, generate_latest

http_requests_total = Counter(
    "mercora_http_requests_total", "Total HTTP requests", ["method", "path", "status"]
)
checkout_saga_total = Counter("mercora_checkout_saga_total", "Checkout saga outcomes", ["outcome"])
partner_requests_total = Counter(
    "mercora_partner_requests_total", "Authenticated requests per partner", ["partner_id"]
)


def render_metrics() -> tuple[bytes, str]:
    return generate_latest(), CONTENT_TYPE_LATEST
