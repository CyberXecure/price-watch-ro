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


app.include_router(watchlists_router)
app.include_router(products_router)
app.include_router(alerts_router)
app.include_router(demo_router)
app.include_router(dashboard_router)
app.include_router(imports_router)