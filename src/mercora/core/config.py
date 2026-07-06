import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_dsn: str = os.environ.get("MERCORA_DATABASE_DSN", "sqlite+aiosqlite:///./mercora.db")


settings = Settings()
