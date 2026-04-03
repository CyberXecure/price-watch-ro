from datetime import datetime

from sqlmodel import Session, select

from app.models import AlertEvent, WatchlistItem

from enum import Enum

def normalize_comparison_unit(unit) -> str | None:
    if unit is None:
        return None

    # dacă vine enum Python, folosim .name / .value, nu str(enum)
    if isinstance(unit, Enum):
        raw_name = getattr(unit, "name", None)
        raw_value = getattr(unit, "value", None)

        if raw_name in {"LEI_PER_L", "LEI_PER_KG", "LEI_PER_BUC", "TOTAL"}:
            return raw_name

        if isinstance(raw_value, str):
            value = raw_value.strip().lower()
        else:
            value = str(raw_value).strip().lower()
    else:
        value = str(unit).strip().lower()

    mapping = {
        "lei/l": "LEI_PER_L",
        "lei/kg": "LEI_PER_KG",
        "lei/buc": "LEI_PER_BUC",
        "total": "TOTAL",
        "lei_per_l": "LEI_PER_L",
        "lei_per_kg": "LEI_PER_KG",
        "lei_per_buc": "LEI_PER_BUC",
        "comparisonunit.lei_per_l": "LEI_PER_L",
        "comparisonunit.lei_per_kg": "LEI_PER_KG",
        "comparisonunit.lei_per_buc": "LEI_PER_BUC",
        "comparisonunit.total": "TOTAL",
        "LEI_PER_L".lower(): "LEI_PER_L",
        "LEI_PER_KG".lower(): "LEI_PER_KG",
        "LEI_PER_BUC".lower(): "LEI_PER_BUC",
        "TOTAL".lower(): "TOTAL",
    }

    return mapping.get(value, value.upper())

def pick_comparison(
    price_total,
    unit_price_value,
    unit_price_unit,
):
    if unit_price_value is not None and unit_price_unit:
        normalized_unit = str(unit_price_unit).strip().lower()

        if normalized_unit == "l":
            return unit_price_value, "LEI_PER_L"
        if normalized_unit == "kg":
            return unit_price_value, "LEI_PER_KG"
        if normalized_unit == "buc":
            return unit_price_value, "LEI_PER_BUC"

    if price_total is not None:
        return price_total, "TOTAL"

    return None, None


def status_label(status: str | None) -> str:
    value = (status or "normal").strip().lower()

    if value == "best_buy":
        return "Chilipir"
    if value == "high_price":
        return "Răsfăț"
    return "Preț cinstit"


def _normalize_status(status: str | None) -> str:
    value = (status or "normal").strip().lower()
    if value in {"best_buy", "normal", "high_price"}:
        return value
    return "normal"


def _evaluate_status(
    target_price,
    target_unit,
    comparison_price,
    comparison_unit,
) -> str:
    if target_price is None:
        return "normal"

    normalized_target_unit = normalize_comparison_unit(target_unit)
    normalized_comparison_unit = normalize_comparison_unit(comparison_unit)

    if comparison_price is None or not normalized_comparison_unit:
        return "normal"

    if normalized_target_unit and normalized_target_unit != normalized_comparison_unit:
        return "normal"

    if comparison_price <= target_price:
        return "best_buy"

    return "high_price"


def evaluate_and_create_alerts_for_product(
    session: Session,
    product,
    comparison_price,
    comparison_unit,
):
    normalized_comparison_unit = normalize_comparison_unit(comparison_unit)

    items = session.exec(
        select(WatchlistItem).where(
            WatchlistItem.store_product_id == product.id,
            WatchlistItem.is_active == True,  # noqa: E712
        )
    ).all()

    for watchlist_item in items:
        old_status = _normalize_status(watchlist_item.current_status)
        new_status = _evaluate_status(
            target_price=watchlist_item.target_price,
            target_unit=watchlist_item.target_unit,
            comparison_price=comparison_price,
            comparison_unit=normalized_comparison_unit,
        )

        if new_status == old_status:
            continue

        watchlist_item.current_status = new_status
        if watchlist_item.target_unit:
            watchlist_item.target_unit = normalize_comparison_unit(watchlist_item.target_unit)

        session.add(watchlist_item)

        if watchlist_item.store_product_id is None:
            continue

        old_label = status_label(old_status)
        new_label = status_label(new_status)
        message = f"Status schimbat: {old_label} -> {new_label}"

        event = AlertEvent(
            watchlist_item_id=watchlist_item.id,
            store_product_id=watchlist_item.store_product_id,
            triggered_at=datetime.utcnow(),
            old_status=old_status.upper(),
            new_status=new_status.upper(),
            comparison_price=comparison_price,
            comparison_unit=normalized_comparison_unit,
            message=message,
            is_read=False,
        )
        session.add(event)