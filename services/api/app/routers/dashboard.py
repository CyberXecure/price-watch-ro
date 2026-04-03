from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.db import get_session
from app.enums import PriceStatus
from app.models import StoreProduct, Watchlist, WatchlistItem
from app.schemas import DashboardSummary

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def get_dashboard_summary(
    session: Session = Depends(get_session),
) -> DashboardSummary:
    watchlists = session.exec(select(Watchlist)).all()
    products = session.exec(select(StoreProduct)).all()
    items = session.exec(select(WatchlistItem)).all()

    total_chilipir = sum(1 for item in items if item.current_status == PriceStatus.BEST_BUY)
    total_pret_cinstit = sum(1 for item in items if item.current_status == PriceStatus.NORMAL)
    total_rasfat = sum(1 for item in items if item.current_status == PriceStatus.HIGH_PRICE)

    return DashboardSummary(
        total_watchlists=len(watchlists),
        total_products=len(products),
        total_watchlist_items=len(items),
        total_chilipir=total_chilipir,
        total_pret_cinstit=total_pret_cinstit,
        total_rasfat=total_rasfat,
    )