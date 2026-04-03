from fastapi import APIRouter

from app.db import reset_demo_data

router = APIRouter(prefix="/demo", tags=["demo"])


@router.post("/reset")
def demo_reset() -> dict[str, str]:
    reset_demo_data()
    return {"status": "ok", "message": "Demo data reset complete"}