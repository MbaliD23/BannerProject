from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    app_env: str
    database_url: str
    storage_path: Path
    site_config_path: Path
    category_config_path: Path
    schedule_time: str
    timezone: str
    headless: bool
    timeout_ms: int
    retries: int
    ocr_engine: str
    tesseract_cmd: str | None
    demo_mode: bool
    log_level: str


def _bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    load_dotenv(ROOT / ".env")
    return Settings(
        app_env=os.getenv("APP_ENV", "development"),
        database_url=os.getenv(
            "DATABASE_URL",
            "postgresql+psycopg://banner:banner@localhost:5432/banner_analytics?connect_timeout=5",
        ),
        storage_path=(ROOT / os.getenv("BANNER_STORAGE_PATH", "data/banners")).resolve(),
        site_config_path=(ROOT / os.getenv("SITE_CONFIG_PATH", "config/sites.yaml")).resolve(),
        category_config_path=(
            ROOT / os.getenv("CATEGORY_CONFIG_PATH", "config/categories.yaml")
        ).resolve(),
        schedule_time=os.getenv("SCHEDULE_TIME", "06:00"),
        timezone=os.getenv("SCHEDULE_TIMEZONE", "Africa/Johannesburg"),
        headless=_bool(os.getenv("COLLECTOR_HEADLESS"), True),
        timeout_ms=int(os.getenv("COLLECTOR_TIMEOUT_MS", "45000")),
        retries=int(os.getenv("COLLECTOR_RETRIES", "3")),
        ocr_engine=os.getenv("OCR_ENGINE", "easyocr").lower(),
        tesseract_cmd=os.getenv("TESSERACT_CMD") or None,
        demo_mode=_bool(os.getenv("DEMO_MODE"), False),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
    )


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def load_sites() -> list[dict[str, Any]]:
    return [site for site in load_yaml(get_settings().site_config_path).get("sites", []) if site.get("enabled")]


def load_taxonomy() -> dict[str, Any]:
    return load_yaml(get_settings().category_config_path)

