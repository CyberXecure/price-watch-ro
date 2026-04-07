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