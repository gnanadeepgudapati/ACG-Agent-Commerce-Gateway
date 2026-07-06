from mercora.core.metrics import checkout_saga_total, http_requests_total, render_metrics


def test_render_metrics_includes_incremented_counter() -> None:
    http_requests_total.labels(method="GET", path="/v1/products", status="200").inc()

    body, content_type = render_metrics()

    assert "mercora_http_requests_total" in body.decode()
    assert content_type.startswith("text/plain")


def test_checkout_saga_counter_has_outcome_label() -> None:
    checkout_saga_total.labels(outcome="success").inc()

    body, _ = render_metrics()

    assert 'mercora_checkout_saga_total{outcome="success"}' in body.decode()
