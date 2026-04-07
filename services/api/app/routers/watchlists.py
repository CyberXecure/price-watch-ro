from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from app.adapters.freshful.parser import parse_freshful_product_html
from app.adapters.freshful.rendered_parser import parse_freshful_product_rendered
from app.db import get_session
from app.models import PriceSnapshot, StoreProduct, Watchlist, WatchlistItem
from app.routers.imports import fetch_html, upsert_product_snapshot_and_watchlist
from app.schemas import FreshfulImportRequest

import traceback

router = APIRouter(prefix="/watchlists", tags=["watchlists"])


class WatchlistCreateRequest(BaseModel):
    name: str


class WatchlistUpdateItemRequest(BaseModel):
    target_price: Optional[float] = None
    target_unit: Optional[str] = None
    notify_best_buy: Optional[bool] = None
    notify_high_price: Optional[bool] = None
    is_active: Optional[bool] = None


def status_label(status: str) -> str:
    if status == "best_buy":
        return "Chilipir"
    if status == "normal":
        return "Preț cinstit"
    if status == "high_price":
        return "Răsfăț"
    return status


def _latest_snapshot_for_product(
    session: Session,
    store_product_id: int,
) -> PriceSnapshot | None:
    return session.exec(
        select(PriceSnapshot)
        .where(PriceSnapshot.store_product_id == store_product_id)
        .order_by(PriceSnapshot.captured_at.desc(), PriceSnapshot.id.desc())
    ).first()


def _infer_default_target_unit(parsed: dict) -> str | None:
    unit = (parsed.get("unit_price_unit") or "").strip().lower()

    if unit == "l":
        return "lei/l"
    if unit == "kg":
        return "lei/kg"
    if unit == "buc":
        return "lei/buc"

    return "total"


def _build_payload_from_parsed(
    parsed: dict,
    watchlist_id: int,
    item: WatchlistItem,
) -> FreshfulImportRequest:
    return FreshfulImportRequest(
        url=parsed["url"],
        title=parsed["title"],
        brand=parsed.get("brand"),
        image_url=parsed.get("image_url"),
        category=parsed.get("category"),
        package_text=parsed.get("package_text"),
        base_measure_type=parsed.get("base_measure_type", "unknown"),
        base_measure_value=parsed.get("base_measure_value"),
        base_measure_unit=parsed.get("base_measure_unit"),
        external_id=parsed.get("external_id"),
        price_total=parsed["price_total"],
        currency=parsed.get("currency", "RON"),
        unit_price_value=parsed.get("unit_price_value"),
        unit_price_unit=parsed.get("unit_price_unit"),
        old_price=parsed.get("old_price"),
        promo_label=_normalize_promo_label(parsed.get("promo_label")),
        discount_percent=parsed.get("discount_percent"),
        deposit_value=parsed.get("deposit_value"),
        availability=parsed.get("availability"),
        watchlist_id=watchlist_id,
        target_price=item.target_price,
        target_unit=item.target_unit or _infer_default_target_unit(parsed),
        notify_best_buy=item.notify_best_buy,
        notify_high_price=item.notify_high_price,
    )

def _first_non_empty(*values):
    for value in values:
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        return value
    return None

def _normalize_promo_label(value: str | None) -> str | None:
    if value is None:
        return None

    text = str(value).strip()
    if not text:
        return None

    normalized = (
        text.upper()
        .replace("Ă", "A")
        .replace("Â", "A")
        .replace("Î", "I")
        .replace("Ș", "S")
        .replace("Ş", "S")
        .replace("Ț", "T")
        .replace("Ţ", "T")
    )

    mapping = {
        "DEAL": "OFERTĂ",
        "DEALS": "OFERTĂ",
        "OFERTA": "OFERTĂ",
        "PROMO": "OFERTĂ",
    }

    return mapping.get(normalized, text)

def _merge_refresh_parsed(
    *,
    static_parsed: dict | None,
    rendered_parsed: dict | None,
    product: StoreProduct,
) -> dict:
    static_parsed = static_parsed or {}
    rendered_parsed = rendered_parsed or {}

    merged = {
        "url": _first_non_empty(
            rendered_parsed.get("url"),
            static_parsed.get("url"),
            product.url,
        ),
        "title": _first_non_empty(
            rendered_parsed.get("title"),
            static_parsed.get("title"),
            product.title,
        ),
        "brand": _first_non_empty(
            rendered_parsed.get("brand"),
            static_parsed.get("brand"),
            product.brand,
        ),
        "image_url": _first_non_empty(
            rendered_parsed.get("image_url"),
            static_parsed.get("image_url"),
            product.image_url,
        ),
        "category": _first_non_empty(
            rendered_parsed.get("category"),
            static_parsed.get("category"),
            product.category,
        ),
        "package_text": _first_non_empty(
            rendered_parsed.get("package_text"),
            static_parsed.get("package_text"),
            product.package_text,
        ),
        "base_measure_type": _first_non_empty(
            rendered_parsed.get("base_measure_type"),
            static_parsed.get("base_measure_type"),
            product.base_measure_type,
            "unknown",
        ),
        "base_measure_value": _first_non_empty(
            rendered_parsed.get("base_measure_value"),
            static_parsed.get("base_measure_value"),
            product.base_measure_value,
        ),
        "base_measure_unit": _first_non_empty(
            rendered_parsed.get("base_measure_unit"),
            static_parsed.get("base_measure_unit"),
            product.base_measure_unit,
        ),
        "external_id": _first_non_empty(
            rendered_parsed.get("external_id"),
            static_parsed.get("external_id"),
            product.external_id,
        ),
        "currency": _first_non_empty(
            rendered_parsed.get("currency"),
            static_parsed.get("currency"),
            "RON",
        ),
        "price_total": _first_non_empty(
            rendered_parsed.get("price_total"),
            static_parsed.get("price_total"),
        ),
        "unit_price_value": _first_non_empty(
            rendered_parsed.get("unit_price_value"),
            static_parsed.get("unit_price_value"),
        ),
        "unit_price_unit": _first_non_empty(
            rendered_parsed.get("unit_price_unit"),
            static_parsed.get("unit_price_unit"),
        ),
        "old_price": _first_non_empty(
            rendered_parsed.get("old_price"),
            static_parsed.get("old_price"),
        ),
        "promo_label": _first_non_empty(
            rendered_parsed.get("promo_label"),
            static_parsed.get("promo_label"),
        ),
        "discount_percent": _first_non_empty(
            rendered_parsed.get("discount_percent"),
            static_parsed.get("discount_percent"),
        ),
        "deposit_value": _first_non_empty(
            rendered_parsed.get("deposit_value"),
            static_parsed.get("deposit_value"),
        ),
        "availability": _first_non_empty(
            rendered_parsed.get("availability"),
            static_parsed.get("availability"),
            "unknown",
        ),
    }

    return merged

def _build_refresh_response(
    *,
    session: Session,
    item: WatchlistItem,
    product: StoreProduct,
    parser_used: str,
    static_parsed: dict | None = None,
    rendered_parsed: dict | None = None,
    rendered_error: str | None = None,
    saved_snapshot_id: int | None = None,
):
    session.refresh(item)
    latest_snapshot = _latest_snapshot_for_product(session, item.store_product_id)

    return {
        "ok": True,
        "message": "Produs actualizat",
        "parser_used": parser_used,
        "rendered_error": rendered_error,
        "watchlist_item_id": item.id,
        "store_product_id": item.store_product_id,
        "product_url": product.url,
        "product_title": product.title,
        "static_price_total": static_parsed.get("price_total") if static_parsed else None,
        "static_old_price": static_parsed.get("old_price") if static_parsed else None,
        "static_promo_label": static_parsed.get("promo_label") if static_parsed else None,
        "rendered_price_total": rendered_parsed.get("price_total") if rendered_parsed else None,
        "rendered_old_price": rendered_parsed.get("old_price") if rendered_parsed else None,
        "rendered_promo_label": rendered_parsed.get("promo_label") if rendered_parsed else None,
        "rendered_discount_percent": rendered_parsed.get("discount_percent") if rendered_parsed else None,
        "saved_snapshot_id": saved_snapshot_id,
        "latest_snapshot_id": latest_snapshot.id if latest_snapshot else None,
        "latest_price_total": latest_snapshot.price_total if latest_snapshot else None,
        "latest_old_price": latest_snapshot.old_price if latest_snapshot else None,
        "latest_promo_label": latest_snapshot.promo_label if latest_snapshot else None,
        "latest_discount_percent": latest_snapshot.discount_percent if latest_snapshot else None,
        "latest_deposit_value": latest_snapshot.deposit_value if latest_snapshot else None,
        "latest_comparison_price": latest_snapshot.comparison_price if latest_snapshot else None,
        "latest_comparison_unit": latest_snapshot.comparison_unit if latest_snapshot else None,
        "latest_captured_at": latest_snapshot.captured_at if latest_snapshot else None,
        "current_status": item.current_status,
        "current_status_label": status_label(item.current_status),
    }


@router.get("")
def list_watchlists(session: Session = Depends(get_session)):
    return session.exec(select(Watchlist).order_by(Watchlist.id.asc())).all()


@router.post("")
def create_watchlist(
    payload: WatchlistCreateRequest,
    session: Session = Depends(get_session),
):
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Name is required")

    watchlist = Watchlist(name=name)
    session.add(watchlist)
    session.commit()
    session.refresh(watchlist)
    return watchlist


@router.get("/with-summary")
def list_watchlists_with_summary(session: Session = Depends(get_session)):
    watchlists = session.exec(select(Watchlist).order_by(Watchlist.id.asc())).all()

    result = []
    for watchlist in watchlists:
        items = session.exec(
            select(WatchlistItem).where(WatchlistItem.watchlist_id == watchlist.id)
        ).all()

        result.append(
            {
                "id": watchlist.id,
                "name": watchlist.name,
                "created_at": watchlist.created_at,
                "total_items": len(items),
                "total_chilipir": sum(1 for x in items if x.current_status == "best_buy"),
                "total_pret_cinstit": sum(1 for x in items if x.current_status == "normal"),
                "total_rasfat": sum(1 for x in items if x.current_status == "high_price"),
            }
        )

    return result


@router.get("/{watchlist_id}")
def get_watchlist(
    watchlist_id: int,
    session: Session = Depends(get_session),
):
    watchlist = session.get(Watchlist, watchlist_id)
    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    return watchlist


@router.get("/{watchlist_id}/summary")
def get_watchlist_summary(
    watchlist_id: int,
    session: Session = Depends(get_session),
):
    watchlist = session.get(Watchlist, watchlist_id)
    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")

    items = session.exec(
        select(WatchlistItem).where(WatchlistItem.watchlist_id == watchlist_id)
    ).all()

    return {
        "watchlist_id": watchlist.id,
        "watchlist_name": watchlist.name,
        "total_items": len(items),
        "total_chilipir": sum(1 for x in items if x.current_status == "best_buy"),
        "total_pret_cinstit": sum(1 for x in items if x.current_status == "normal"),
        "total_rasfat": sum(1 for x in items if x.current_status == "high_price"),
    }


@router.get("/{watchlist_id}/items/detailed")
def get_watchlist_items_detailed(
    watchlist_id: int,
    session: Session = Depends(get_session),
):
    watchlist = session.get(Watchlist, watchlist_id)
    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")

    items = session.exec(
        select(WatchlistItem)
        .where(WatchlistItem.watchlist_id == watchlist_id)
        .order_by(WatchlistItem.id.desc())
    ).all()

    result = []
    for item in items:
        product = session.get(StoreProduct, item.store_product_id)
        latest_snapshot = _latest_snapshot_for_product(session, item.store_product_id)

        result.append(
            {
                "watchlist_item_id": item.id,
                "watchlist_id": item.watchlist_id,
                "store_product_id": item.store_product_id,
                "product_title": product.title if product else None,
                "product_brand": product.brand if product else None,
                "product_category": product.category if product else None,
                "product_url": product.url if product else None,
                "product_image_url": product.image_url if product else None,
                "package_text": product.package_text if product else None,
                "current_status": item.current_status,
                "current_status_label": status_label(item.current_status),
                "target_price": item.target_price,
                "target_unit": item.target_unit,
                "latest_price_total": latest_snapshot.price_total if latest_snapshot else None,
                "latest_comparison_price": latest_snapshot.comparison_price if latest_snapshot else None,
                "latest_comparison_unit": latest_snapshot.comparison_unit if latest_snapshot else None,
                "latest_unit_price_value": latest_snapshot.unit_price_value if latest_snapshot else None,
                "latest_unit_price_unit": latest_snapshot.unit_price_unit if latest_snapshot else None,
                "latest_old_price": latest_snapshot.old_price if latest_snapshot else None,
                "latest_promo_label": latest_snapshot.promo_label if latest_snapshot else None,
                "latest_discount_percent": latest_snapshot.discount_percent if latest_snapshot else None,
                "latest_deposit_value": latest_snapshot.deposit_value if latest_snapshot else None,
                "latest_captured_at": latest_snapshot.captured_at if latest_snapshot else None,
                "notify_best_buy": item.notify_best_buy,
                "notify_high_price": item.notify_high_price,
                "is_active": item.is_active,
                "created_at": item.created_at,
            }
        )

    return result


@router.patch("/{watchlist_id}/items/{item_id}")
def update_watchlist_item(
    watchlist_id: int,
    item_id: int,
    payload: WatchlistUpdateItemRequest,
    session: Session = Depends(get_session),
):
    item = session.exec(
        select(WatchlistItem).where(
            WatchlistItem.watchlist_id == watchlist_id,
            WatchlistItem.id == item_id,
        )
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="Watchlist item not found")

    if payload.target_price is not None:
        item.target_price = payload.target_price
    if payload.target_unit is not None:
        item.target_unit = payload.target_unit
    if payload.notify_best_buy is not None:
        item.notify_best_buy = payload.notify_best_buy
    if payload.notify_high_price is not None:
        item.notify_high_price = payload.notify_high_price
    if payload.is_active is not None:
        item.is_active = payload.is_active

    session.add(item)
    session.commit()
    session.refresh(item)

    return {
        "watchlist_item_id": item.id,
        "watchlist_id": item.watchlist_id,
        "store_product_id": item.store_product_id,
        "target_price": item.target_price,
        "target_unit": item.target_unit,
        "notify_best_buy": item.notify_best_buy,
        "notify_high_price": item.notify_high_price,
        "is_active": item.is_active,
        "current_status": item.current_status,
        "current_status_label": status_label(item.current_status),
        "updated_at": datetime.utcnow(),
    }


@router.post("/{watchlist_id}/items/{item_id}/refresh")
def refresh_watchlist_item(
    watchlist_id: int,
    item_id: int,
    session: Session = Depends(get_session),
):
    item = session.exec(
        select(WatchlistItem).where(
            WatchlistItem.watchlist_id == watchlist_id,
            WatchlistItem.id == item_id,
        )
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Watchlist item not found")

    product = session.get(StoreProduct, item.store_product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Store product not found")

    try:
        html = fetch_html(product.url)
        static_parsed = parse_freshful_product_html(html, product.url)

        payload = _build_payload_from_parsed(static_parsed, watchlist_id, item)
        upsert_result = upsert_product_snapshot_and_watchlist(
            payload=payload,
            session=session,
            forced_watchlist_item_id=item.id,
        )

        session.refresh(item)

        return _build_refresh_response(
            session=session,
            item=item,
            product=product,
            parser_used="static",
            static_parsed=static_parsed,
            rendered_parsed=None,
            rendered_error=None,
            saved_snapshot_id=upsert_result.get("snapshot_id"),
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Static refresh failed: {type(exc).__name__}: {exc}",
        ) from exc


@router.post("/{watchlist_id}/items/{item_id}/refresh-rendered")
def refresh_watchlist_item_rendered(
    watchlist_id: int,
    item_id: int,
    session: Session = Depends(get_session),
):
    item = session.exec(
        select(WatchlistItem).where(
            WatchlistItem.watchlist_id == watchlist_id,
            WatchlistItem.id == item_id,
        )
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Watchlist item not found")

    product = session.get(StoreProduct, item.store_product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Store product not found")

    static_parsed = None

    try:
        try:
            html = fetch_html(product.url)
            static_parsed = parse_freshful_product_html(html, product.url)
        except Exception:
            static_parsed = None

        rendered_parsed = parse_freshful_product_rendered(product.url)

        merged_parsed = _merge_refresh_parsed(
            static_parsed=static_parsed,
            rendered_parsed=rendered_parsed,
            product=product,
        )

        if merged_parsed.get("price_total") is None:
            raise HTTPException(
                status_code=400,
                detail="Rendered refresh failed: missing price_total",
            )

        payload = _build_payload_from_parsed(merged_parsed, watchlist_id, item)
        upsert_result = upsert_product_snapshot_and_watchlist(
            payload=payload,
            session=session,
            forced_watchlist_item_id=item.id,
        )

        session.refresh(item)

        return _build_refresh_response(
            session=session,
            item=item,
            product=product,
            parser_used="rendered",
            static_parsed=static_parsed,
            rendered_parsed=rendered_parsed,
            rendered_error=None,
            saved_snapshot_id=upsert_result.get("snapshot_id"),
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Rendered refresh failed: {type(exc).__name__}: {exc}",
        ) from exc