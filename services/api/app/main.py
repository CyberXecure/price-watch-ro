import urllib.request
import subprocess
import os
import time
import json
from datetime import datetime, timezone
import asyncio
import json
import sys
from urllib.error import URLError
from urllib.request import urlopen

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import API_TITLE
from app.db import init_db
from app.routers.alerts import router as alerts_router
from app.routers.dashboard import router as dashboard_router
from app.routers.demo import router as demo_router
from app.routers.imports import router as imports_router
from app.routers.products import router as products_router
from app.routers.watchlists import router as watchlists_router

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

app = FastAPI(title=API_TITLE)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://localhost",
        "http://127.0.0.1",
        "tauri://localhost",
        "http://tauri.localhost",
        "null",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/rendered")
def health_rendered() -> dict[str, str | int | None]:
    target = "http://127.0.0.1:9222/json/version"

    try:
        with urlopen(target, timeout=2) as response:
            status_code = getattr(response, "status", 200)
            payload = json.loads(response.read().decode("utf-8"))

        return {
            "status": "ok",
            "target": target,
            "http_status": status_code,
            "browser": payload.get("Browser"),
            "websocket_debugger_url": payload.get("webSocketDebuggerUrl"),
            "detail": None,
        }
    except URLError as exc:
        return {
            "status": "error",
            "target": target,
            "http_status": None,
            "browser": None,
            "websocket_debugger_url": None,
            "detail": f"{type(exc).__name__}: {exc}",
        }
    except Exception as exc:
        return {
            "status": "error",
            "target": target,
            "http_status": None,
            "browser": None,
            "websocket_debugger_url": None,
            "detail": f"{type(exc).__name__}: {exc}",
        }


app.include_router(watchlists_router)
app.include_router(products_router)
app.include_router(alerts_router)
app.include_router(demo_router)
app.include_router(dashboard_router)
app.include_router(imports_router)


def _find_chrome_path() -> str | None:
    candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ]

    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate

    return None


def _start_promo_engine() -> dict:
    chrome_path = _find_chrome_path()
    profile_dir = r"D:\dev\chrome-freshful-debug"

    if not chrome_path:
        return {
            "status": "error",
            "detail": "Nu am găsit Google Chrome instalat.",
            "target": "http://127.0.0.1:9222/json/version",
        }

    try:
        startupinfo = None
        creationflags = 0

        if sys.platform.startswith("win"):
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 2
            creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)

        subprocess.Popen(
            [
                chrome_path,
                "--remote-debugging-port=9222",
                f"--user-data-dir={profile_dir}",
                "--lang=ro",
                "--accept-lang=ro-RO,ro",
                "--new-window",
                "--window-position=3000,3000",
                "--window-size=400,300",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            shell=False,
            startupinfo=startupinfo,
            creationflags=creationflags,
        )

        for _ in range(8):
            time.sleep(1)
            health = _promo_engine_health()
            if health.get("status") == "ok":
                return {
                    "status": "ok",
                    "detail": "Chrome CDP pornit cu succes.",
                    "target": health.get("target"),
                    "browser": health.get("browser"),
                    "websocket_debugger_url": health.get("websocket_debugger_url"),
                    "last_checked_at": health.get("last_checked_at"),
                }

        health = _promo_engine_health()
        return {
            "status": "error",
            "detail": "Chrome a fost pornit, dar CDP nu a devenit disponibil la timp.",
            "target": health.get("target"),
            "browser": health.get("browser"),
            "websocket_debugger_url": health.get("websocket_debugger_url"),
            "last_checked_at": health.get("last_checked_at"),
        }
    except Exception as exc:
        return {
            "status": "error",
            "detail": f"Nu am putut porni Chrome CDP: {type(exc).__name__}: {exc}",
            "target": "http://127.0.0.1:9222/json/version",
        }


def _promo_engine_health() -> dict:
    target = "http://127.0.0.1:9222/json/version"
    checked_at = datetime.now(timezone.utc).isoformat()

    try:
        with urllib.request.urlopen(target, timeout=2) as response:
            raw = response.read().decode("utf-8", errors="replace")
            data = json.loads(raw)

        return {
            "status": "ok",
            "mode": "external",
            "detail": "Chrome CDP disponibil",
            "target": target,
            "websocket_debugger_url": data.get("webSocketDebuggerUrl"),
            "browser": data.get("Browser"),
            "last_checked_at": checked_at,
        }
    except Exception as exc:
        return {
            "status": "error",
            "mode": "external",
            "detail": f"Promo engine indisponibil: {type(exc).__name__}: {exc}",
            "target": target,
            "websocket_debugger_url": None,
            "browser": None,
            "last_checked_at": checked_at,
        }


@app.get("/health/promo-engine")
def health_promo_engine():
    return _promo_engine_health()



@app.post("/health/promo-engine/start")
def start_promo_engine():
    return _start_promo_engine()
