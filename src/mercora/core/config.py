import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_dsn: str = os.environ.get("MERCORA_DATABASE_DSN", "sqlite+aiosqlite:///./mercora.db")
    jwt_secret: str = os.environ.get("MERCORA_JWT_SECRET", "local-dev-secret-do-not-use-in-prod")
    jwt_issuer: str = os.environ.get("MERCORA_JWT_ISSUER", "mercora")
    jwt_audience: str = os.environ.get("MERCORA_JWT_AUDIENCE", "mercora-api")
    rate_limit_max_requests: int = int(os.environ.get("MERCORA_RATE_LIMIT_MAX_REQUESTS", "100"))
    rate_limit_window_seconds: float = float(
        os.environ.get("MERCORA_RATE_LIMIT_WINDOW_SECONDS", "60")
    )
    stripe_test_key: str | None = os.environ.get("STRIPE_TEST_KEY")


settings = Settings()
