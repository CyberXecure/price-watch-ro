from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.db import get_session
from app.models import AlertEvent
from app.schemas import AlertEventRead
from app.services.pricing import status_label

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=list[AlertEventRead])
def list_alerts(session: Session = Depends(get_session)) -> list[AlertEventRead]:
    rows = session.exec(
        select(AlertEvent).order_by(AlertEvent.triggered_at.desc())
    ).all()

    return [
        AlertEventRead(
            id=row.id,
            watchlist_item_id=row.watchlist_item_id,
            store_product_id=row.store_product_id,
            triggered_at=row.triggered_at,
            old_status=row.old_status,
            old_status_label=status_label(row.old_status),
            new_status=row.new_status,
            new_status_label=status_label(row.new_status),
            comparison_price=row.comparison_price,
            comparison_unit=row.comparison_unit,
            message=row.message,
            is_read=row.is_read,
        )
        for row in rows
    ]
