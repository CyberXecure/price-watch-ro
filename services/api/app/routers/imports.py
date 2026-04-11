from datetime import datetime

import httpx
from bs4 import BeautifulSoup
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlmodel import Session, select

from app.adapters.freshful.parser import parse_freshful_product_html
from app.db import get_session
from app.models import PriceSnapshot, StoreProduct, Watchlist, WatchlistItem
from app.schemas import FreshfulImportRequest
from app.services.pricing import (
    evaluate_and_create_alerts_for_product,
    pick_comparison,
)

router = APIRouter(prefix="/imports", tags=["imports"])


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)


def fetch_html(url: str) -> str:
    headers = {
        "User-Agent": USER_AGENT,
        "Accept-Language": "ro-RO,ro;q=0.9,en-US;q=0.8,en;q=0.7",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    }

    with httpx.Client(
        timeout=45.0,
        follow_redirects=True,
        headers=headers,
    ) as client:
        response = client.get(url)
        response.raise_for_status()
        return response.text


def _clean_text(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = " ".join(str(value).split()).strip()
    return cleaned or None


def _page_title_clean(title: str | None) -> str | None:
    title = _clean_text(title)
    if not title:
        return None

    suffixes = [
        " - Prospețime și varietate - Freshful.ro",
        " – Prospețime și varietate – Freshful.ro",
        " - Freshful.ro",
        " – Freshful.ro",
    ]
    for suffix in suffixes:
        if title.endswith(suffix):
            return title[: -len(suffix)].strip()
    return title


def _build_debug_payload(html: str, url: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")

    page_title = _clean_text(soup.title.string if soup.title and soup.title.string else None)
    og_title = None
    og_image = None
    og_description = None

    for meta in soup.find_all("meta"):
        prop = (meta.get("property") or meta.get("name") or "").strip().lower()
        content = _clean_text(meta.get("content"))
        if not content:
            continue
        if prop == "og:title":
            og_title = content
        elif prop == "og:image":
            og_image = content
        elif prop == "og:description":
            og_description = content

    json_ld_blocks = soup.find_all("script", attrs={"type": "application/ld+json"})
    json_ld_types: list[str] = []
    for block in json_ld_blocks:
        text_value = _clean_text(block.get_text(" ", strip=True))
        if not text_value:
            continue
        if "BreadcrumbList" in text_value:
            json_ld_types.append("BreadcrumbList")
        if "Product" in text_value:
            json_ld_types.append("Product")

    parsed = parse_freshful_product_html(html, url)

    product_text_preview = _clean_text(soup.get_text(" ", strip=True))
    if product_text_preview:
        product_text_preview = product_text_preview[:2500]

    return {
        "url": url,
        "page_title": page_title,
        "page_title_clean": _page_title_clean(page_title),
        "og_title": og_title,
        "og_title_clean": _page_title_clean(og_title),
        "og_image": og_image,
        "og_description": og_description,
        "json_ld_count": len(json_ld_blocks),
        "json_ld_types": sorted(set(json_ld_types)),
        "breadcrumb_category": parsed.get("category"),
        "product_text_preview": product_text_preview,
        "detected_current_price": parsed.get("price_total"),
        "detected_old_price": parsed.get("old_price"),
        "detected_promo_label": parsed.get("promo_label"),
        "detected_discount_percent": parsed.get("discount_percent"),
        "detected_deposit_value": parsed.get("deposit_value"),
        "brand_from_url": parsed.get("brand"),
        "text_price_match": None,
        "text_unit_price_match": None,
        "text_package_match": parsed.get("package_text"),
        "parsed": parsed,
    }


def _infer_default_target_unit(parsed: dict) -> str:
    unit = (parsed.get("unit_price_unit") or "").strip().lower()

    if unit == "l":
        return "lei/l"
    if unit == "kg":
        return "lei/kg"
    if unit == "buc":
        return "lei/buc"

    return "total"


def _normalize_request_target_unit(unit: str | None) -> str | None:
    if not unit:
        return None

    value = str(unit).strip().lower()
    mapping = {
        "lei/l": "lei/l",
        "lei/kg": "lei/kg",
        "lei/buc": "lei/buc",
        "total": "total",
        "lei_per_l": "lei/l",
        "lei_per_kg": "lei/kg",
        "lei_per_buc": "lei/buc",
        "comparisonunit.lei_per_l": "lei/l",
        "comparisonunit.lei_per_kg": "lei/kg",
        "comparisonunit.lei_per_buc": "lei/buc",
        "comparisonunit.total": "total",
        "l": "lei/l",
        "kg": "lei/kg",
        "buc": "lei/buc",
    }
    return mapping.get(value, value)


def _db_enum_from_ui_unit(unit: str | None) -> str | None:
    normalized = _normalize_request_target_unit(unit)
    mapping = {
        "lei/l": "LEI_PER_L",
        "lei/kg": "LEI_PER_KG",
        "lei/buc": "LEI_PER_BUC",
        "total": "TOTAL",
    }
    return mapping.get(normalized)


def _ui_unit_from_db_enum(unit: str | None) -> str | None:
    normalized = str(unit).strip().upper() if unit is not None else None
    mapping = {
        "LEI_PER_L": "lei/l",
        "LEI_PER_KG": "lei/kg",
        "LEI_PER_BUC": "lei/buc",
        "TOTAL": "total",
    }
    return mapping.get(normalized)


def _build_payload_from_parsed(
    parsed: dict,
    watchlist_id: int | None,
    target_price: float | None,
    target_unit: str | None,
    notify_best_buy: bool = True,
    notify_high_price: bool = True,
) -> FreshfulImportRequest:
    effective_target_unit = _normalize_request_target_unit(target_unit) or _infer_default_target_unit(parsed)

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
        promo_label=parsed.get("promo_label"),
        discount_percent=parsed.get("discount_percent"),
        deposit_value=parsed.get("deposit_value"),
        availability=parsed.get("availability", "unknown"),
        watchlist_id=watchlist_id,
        target_price=target_price,
        target_unit=effective_target_unit,
        notify_best_buy=notify_best_buy,
        notify_high_price=notify_high_price,
    )


def upsert_product_snapshot_and_watchlist(
    payload: FreshfulImportRequest,
    session: Session,
    forced_watchlist_item_id: int | None = None,
):
    existing_product = session.exec(
        select(StoreProduct).where(StoreProduct.url == payload.url)
    ).first()

    if existing_product:
        product = existing_product

        if payload.title:
            product.title = payload.title
        if payload.brand:
            product.brand = payload.brand
        if payload.category:
            product.category = payload.category
        if payload.image_url:
            product.image_url = payload.image_url
        if payload.package_text:
            product.package_text = payload.package_text

        if payload.base_measure_type and str(payload.base_measure_type).lower() != "unknown":
            product.base_measure_type = payload.base_measure_type
        if payload.base_measure_value is not None:
            product.base_measure_value = payload.base_measure_value
        if payload.base_measure_unit:
            product.base_measure_unit = payload.base_measure_unit

        if payload.external_id:
            product.external_id = payload.external_id

        product.updated_at = datetime.utcnow()
        session.add(product)
        session.commit()
        session.refresh(product)
    else:
        product = StoreProduct(
            source_code="freshful",
            external_id=payload.external_id,
            title=payload.title,
            brand=payload.brand,
            category=payload.category,
            url=payload.url,
            image_url=payload.image_url,
            package_text=payload.package_text,
            base_measure_type=payload.base_measure_type,
            base_measure_value=payload.base_measure_value,
            base_measure_unit=payload.base_measure_unit,
            is_active=True,
        )
        session.add(product)
        session.commit()
        session.refresh(product)

    comparison_price, comparison_unit = pick_comparison(
        price_total=payload.price_total,
        unit_price_value=payload.unit_price_value,
        unit_price_unit=payload.unit_price_unit,
    )

    normalized_comparison_unit_ui = _normalize_request_target_unit(comparison_unit)
    normalized_comparison_unit_db = _db_enum_from_ui_unit(normalized_comparison_unit_ui)
    if normalized_comparison_unit_db is None:
        normalized_comparison_unit_db = "TOTAL"

    normalized_target_unit_ui = _normalize_request_target_unit(payload.target_unit)
    normalized_target_unit_db = _db_enum_from_ui_unit(normalized_target_unit_ui)

    snapshot = PriceSnapshot(
        store_product_id=product.id,
        captured_at=datetime.utcnow(),
        price_total=payload.price_total,
        currency=payload.currency,
        unit_price_value=payload.unit_price_value,
        unit_price_unit=normalized_comparison_unit_db,
        comparison_price=comparison_price,
        comparison_unit=normalized_comparison_unit_db,
        old_price=payload.old_price,
        promo_label=payload.promo_label,
        discount_percent=payload.discount_percent,
        deposit_value=payload.deposit_value,
        availability=payload.availability,
    )
    session.add(snapshot)
    session.commit()
    session.refresh(snapshot)

    watchlist_item = None
    watchlist_item_id_value = None
    watchlist_item_store_product_id_value = None
    current_status_value = None

    if payload.watchlist_id is not None:
        watchlist = session.get(Watchlist, payload.watchlist_id)
        if not watchlist:
            raise HTTPException(status_code=404, detail="Watchlist not found")

        effective_target_unit_db = normalized_target_unit_db or normalized_comparison_unit_db
        if effective_target_unit_db not in {"LEI_PER_L", "LEI_PER_KG", "LEI_PER_BUC", "TOTAL"}:
            effective_target_unit_db = "TOTAL"

        if forced_watchlist_item_id is not None:
            watchlist_item = session.exec(
                select(WatchlistItem).where(
                    WatchlistItem.id == forced_watchlist_item_id,
                    WatchlistItem.watchlist_id == payload.watchlist_id,
                )
            ).first()

            if not watchlist_item:
                raise HTTPException(
                    status_code=404,
                    detail="Forced watchlist item not found",
                )

            watchlist_item.store_product_id = product.id
            watchlist_item.target_price = payload.target_price
            watchlist_item.target_unit = effective_target_unit_db
            watchlist_item.notify_best_buy = payload.notify_best_buy
            watchlist_item.notify_high_price = payload.notify_high_price
            watchlist_item.is_active = True

            session.add(watchlist_item)
            session.commit()
            session.refresh(watchlist_item)
        else:
            watchlist_item = session.exec(
                select(WatchlistItem).where(
                    WatchlistItem.watchlist_id == payload.watchlist_id,
                    WatchlistItem.store_product_id == product.id,
                )
            ).first()

            if watchlist_item:
                if payload.target_price is not None:
                    watchlist_item.target_price = payload.target_price
                if normalized_target_unit_db is not None:
                    watchlist_item.target_unit = normalized_target_unit_db
                watchlist_item.notify_best_buy = payload.notify_best_buy
                watchlist_item.notify_high_price = payload.notify_high_price
                watchlist_item.is_active = True
                session.add(watchlist_item)
            else:
                watchlist_item = WatchlistItem(
                    watchlist_id=payload.watchlist_id,
                    store_product_id=product.id,
                    target_price=payload.target_price,
                    target_unit=effective_target_unit_db,
                    current_status="normal",
                    notify_best_buy=payload.notify_best_buy,
                    notify_high_price=payload.notify_high_price,
                    is_active=True,
                )
                session.add(watchlist_item)

            session.commit()
            session.refresh(watchlist_item)

    if watchlist_item is not None:
        evaluate_and_create_alerts_for_product(
            session=session,
            watchlist_item=watchlist_item,
            comparison_price=comparison_price,
            comparison_unit=normalized_comparison_unit_ui,
            price_total=payload.price_total,
            old_price=payload.old_price,
            new_price=payload.price_total,
        )
        session.commit()

        session.refresh(watchlist_item)
        watchlist_item_id_value = watchlist_item.id
        watchlist_item_store_product_id_value = watchlist_item.store_product_id
        current_status_value = watchlist_item.current_status

    return {
        "product_id": product.id,
        "product_title": product.title,
        "product_url": product.url,
        "snapshot_id": snapshot.id,
        "snapshot_price_total": snapshot.price_total,
        "snapshot_old_price": snapshot.old_price,
        "snapshot_promo_label": snapshot.promo_label,
        "snapshot_discount_percent": snapshot.discount_percent,
        "comparison_price": comparison_price,
        "comparison_unit": _ui_unit_from_db_enum(normalized_comparison_unit_db),
        "watchlist_item_id": watchlist_item_id_value,
        "watchlist_item_store_product_id": watchlist_item_store_product_id_value,
        "current_status": current_status_value,
        "current_status_label": None,
        "message": "Freshful import completed",
    }


@router.post("/freshful-url-debug")
def import_freshful_url_debug(
    url: str = Query(...),
):
    try:
        html = fetch_html(url)
        return _build_debug_payload(html, url)
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Freshful debug failed: {exc}",
        ) from exc


@router.post("/freshful-url-auto")
def import_freshful_url_auto(
    url: str = Query(...),
    watchlist_id: int | None = Query(default=None),
    target_price: float | None = Query(default=None),
    target_unit: str | None = Query(default=None),
    session: Session = Depends(get_session),
):
    try:
        html = fetch_html(url)
        parsed = parse_freshful_product_html(html, url)

        payload = _build_payload_from_parsed(
            parsed=parsed,
            watchlist_id=watchlist_id,
            target_price=target_price,
            target_unit=target_unit,
        )
        return upsert_product_snapshot_and_watchlist(payload=payload, session=session)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Freshful import failed: {exc}",
        ) from exc