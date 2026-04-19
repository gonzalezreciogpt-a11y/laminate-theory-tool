from __future__ import annotations

from dataclasses import dataclass
import os


def _read_int(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    try:
        return int(raw_value)
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    app_env: str
    app_base_url: str
    port: int
    log_level: str

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"


def get_settings() -> Settings:
    return Settings(
        app_env=os.getenv("APP_ENV", "development"),
        app_base_url=os.getenv("APP_BASE_URL", "").strip(),
        port=_read_int("PORT", 8000),
        log_level=os.getenv("LOG_LEVEL", "info").strip().lower() or "info",
    )


settings = get_settings()
