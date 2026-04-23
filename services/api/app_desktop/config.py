from __future__ import annotations

import os
from dataclasses import dataclass

from app_desktop.paths import ensure_desktop_dirs, get_browser_dir, get_db_path, get_logs_dir


@dataclass(frozen=True)
class DesktopConfig:
    app_mode: str
    host: str
    port: int
    db_path: str
    logs_dir: str
    browser_dir: str


def load_desktop_config() -> DesktopConfig:
    ensure_desktop_dirs()

    host = os.environ.get("PRICEWATCH_HOST", "127.0.0.1")
    port = int(os.environ.get("PRICEWATCH_PORT", "18400"))

    return DesktopConfig(
        app_mode="desktop",
        host=host,
        port=port,
        db_path=str(get_db_path()),
        logs_dir=str(get_logs_dir()),
        browser_dir=str(get_browser_dir()),
    )
