from mercora.core.rate_limit import RateLimiter


def test_allows_up_to_max_requests_within_window() -> None:
    clock = iter([0.0, 0.0, 0.0]).__next__
    limiter = RateLimiter(max_requests=2, window_seconds=60, clock=clock)

    assert limiter.allow("partner-a") is True
    assert limiter.allow("partner-a") is True


def test_blocks_once_max_requests_exceeded() -> None:
    times = iter([0.0, 0.0, 0.0])
    limiter = RateLimiter(max_requests=2, window_seconds=60, clock=lambda: next(times))

    assert limiter.allow("partner-a") is True
    assert limiter.allow("partner-a") is True
    assert limiter.allow("partner-a") is False


def test_window_expiry_allows_requests_again() -> None:
    times = iter([0.0, 0.0, 61.0])
    limiter = RateLimiter(max_requests=2, window_seconds=60, clock=lambda: next(times))

    assert limiter.allow("partner-a") is True
    assert limiter.allow("partner-a") is True
    assert limiter.allow("partner-a") is True


def test_partners_are_isolated() -> None:
    limiter = RateLimiter(max_requests=1, window_seconds=60, clock=lambda: 0.0)

    assert limiter.allow("partner-a") is True
    assert limiter.allow("partner-b") is True
    assert limiter.allow("partner-a") is False
