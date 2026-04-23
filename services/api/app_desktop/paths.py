from __future__ import annotations

import os
from pathlib import Path


APP_VENDOR = "PriceWatchRO"
APP_NAME = "PriceWatchRO"


def get_local_app_data_dir() -> Path:
    local_app_data = os.environ.get("LOCALAPPDATA")
    if not local_app_data:
        local_app_data = str(Path.home() / "AppData" / "Local")
    return Path(local_app_data)


def get_app_root_dir() -> Path:
    return get_local_app_data_dir() / APP_VENDOR / APP_NAME


def get_data_dir() -> Path:
    return get_app_root_dir() / "data"


def get_logs_dir() -> Path:
    return get_app_root_dir() / "logs"


def get_cache_dir() -> Path:
    return get_app_root_dir() / "cache"


def get_browser_dir() -> Path:
    return get_app_root_dir() / "browser"


def get_db_path() -> Path:
    return get_data_dir() / "price-watch.db"


def ensure_desktop_dirs() -> None:
    for path in [
        get_app_root_dir(),
        get_data_dir(),
        get_logs_dir(),
        get_cache_dir(),
        get_browser_dir(),
    ]:
        path.mkdir(parents=True, exist_ok=True)
