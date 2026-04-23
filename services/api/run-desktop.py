from __future__ import annotations

import os

import uvicorn

from app_desktop.config import load_desktop_config
from app_desktop.logging_setup import setup_desktop_logging


def main() -> None:
    config = load_desktop_config()

    os.environ["PRICEWATCH_APP_MODE"] = config.app_mode
    os.environ["PRICEWATCH_DB_PATH"] = config.db_path
    os.environ["PRICEWATCH_BROWSER_DIR"] = config.browser_dir

    setup_desktop_logging(config.logs_dir)

    uvicorn.run(
        "app.main:app",
        host=config.host,
        port=config.port,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()
