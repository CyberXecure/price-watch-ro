from __future__ import annotations  
  
from typing import Optional  
  
from sqlmodel import Session  
  
from app.models import AlertEvent, WatchlistItem  
  
  
def normalize_unit(unit: Optional[str]) -> Optional[str]:  
    if unit is None:  
        return None  
  
    value = str(unit).strip().lower()  
    if not value:  
        return None  
  
    if value.startswith("lei/"):  
        value = value[4:]  
  
    aliases = {  
        "l": "l",  
        "litru": "l",  
        "litri": "l",  
        "kg": "kg",  
        "kilogram": "kg",  
        "kilograme": "kg",  
        "g": "g",  
        "gram": "g",  
        "grame": "g",  
        "buc": "buc",  
        "buc.": "buc",  
        "bucata": "buc",  
        "bucati": "buc",  
        "bucată": "buc",  
        "bucăți": "buc",  
    }  
  
    return aliases.get(value, value)  
  
  
def normalize_comparison_unit(unit: Optional[str]) -> Optional[str]:  
    return normalize_unit(unit)  
  
  
def pick_comparison(  
    *,  
    unit_price_value: float | None = None,  
    unit_price_unit: str | None = None,  
    comparison_price: float | None = None,  
    comparison_unit: str | None = None,  
    current_comparison_price: float | None = None,  
    current_comparison_unit: str | None = None,  
    price_total: float | None = None,  
    **_: object,  
):  
    value = (  
        unit_price_value  
        if unit_price_value is not None  
        else comparison_price  
        if comparison_price is not None  
        else current_comparison_price  
    )  
  
    unit = (  
        unit_price_unit  
        if unit_price_unit is not None  
        else comparison_unit  
        if comparison_unit is not None  
        else current_comparison_unit  
    )  
  
    if value is None:  
        value = price_total  
  
    return value, normalize_comparison_unit(unit)  
  
  
def status_label(status: Optional[str]) -> str:  
    mapping = {  
        "BEST_BUY": "Chilipir",  
        "FAIR_PRICE": "Preț cinstit",  
        "HIGH_PRICE": "Răsfăț",  
        "NORMAL": "Preț cinstit",  
    }  
    return mapping.get((status or "").upper(), "Preț cinstit")  
  
  
def classify_price_status(  
    *,  
    target_price: float | None,  
    target_unit: str | None,  
    comparison_price: float | None = None,  
    comparison_unit: str | None = None,  
    current_comparison_price: float | None = None,  
    current_comparison_unit: str | None = None,  
    **_: object,  
) -> str:  
    resolved_price = (  
        comparison_price  
        if comparison_price is not None  
        else current_comparison_price  
    )  
    resolved_unit = (  
        comparison_unit  
        if comparison_unit is not None  
        else current_comparison_unit  
    )  
  
    if (  
        target_price is None  
        or resolved_price is None  
        or target_price <= 0  
        or resolved_price <= 0  
    ):  
        return "FAIR_PRICE"  
  
    normalized_target_unit = normalize_unit(target_unit)  
    normalized_comparison = normalize_comparison_unit(resolved_unit)  
  
    if normalized_target_unit and normalized_comparison:  
        if normalized_target_unit != normalized_comparison:  
            return "FAIR_PRICE"  
  
    if resolved_price <= target_price:  
        return "BEST_BUY"  
  
    return "HIGH_PRICE"  
  
  
def maybe_create_status_change_event(  
    *,  
    session: Session,  
    watchlist_item: WatchlistItem,  
    old_status: str | None,  
    new_status: str | None,  
    old_price: float | None = None,  
    new_price: float | None = None,  
) -> AlertEvent | None:  
    normalized_old = old_status.upper() if old_status else None  
    normalized_new = new_status.upper() if new_status else None  
  
    if not normalized_new:  
        return None  
  
    if normalized_old == normalized_new:  
        return None  
  
    old_label = status_label(normalized_old)  
    new_label = status_label(normalized_new)  
    message = f"Status schimbat: {old_label} -> {new_label}"  
  
    event = AlertEvent(  
        watchlist_id=watchlist_item.watchlist_id,  
        watchlist_item_id=watchlist_item.id,  
        store_product_id=watchlist_item.store_product_id,  
        event_type="STATUS_CHANGED",  
        message=message,  
        old_status=normalized_old,  
        new_status=normalized_new,  
        old_price=old_price,  
        new_price=new_price,  
    )  
    session.add(event)  
    return event  
  
  
def evaluate_and_create_alerts_for_product(  
    *,  
    session: Session,  
    watchlist_item: WatchlistItem,  
    old_status: str | None = None,  
    new_status: str | None = None,  
    old_price: float | None = None,  
    new_price: float | None = None,  
    comparison_price: float | None = None,  
    comparison_unit: str | None = None,  
    current_comparison_price: float | None = None,  
    current_comparison_unit: str | None = None,  
    unit_price_value: float | None = None,  
    unit_price_unit: str | None = None,  
    price_total: float | None = None,  
    **_: object,  
) -> AlertEvent | None:  
    resolved_comparison_price, resolved_comparison_unit = pick_comparison(  
        unit_price_value=unit_price_value,  
        unit_price_unit=unit_price_unit,  
        comparison_price=comparison_price,  
        comparison_unit=comparison_unit,  
        current_comparison_price=current_comparison_price,  
        current_comparison_unit=current_comparison_unit,  
        price_total=price_total,  
    )  
  
    resolved_new_status = new_status  
    if resolved_new_status is None:  
        resolved_new_status = classify_price_status(  
            target_price=watchlist_item.target_price,  
            target_unit=watchlist_item.target_unit,  
            comparison_price=resolved_comparison_price,  
            comparison_unit=resolved_comparison_unit,  
        )  
  
    resolved_old_status = old_status or "FAIR_PRICE"  
  
    return maybe_create_status_change_event(  
        session=session,  
        watchlist_item=watchlist_item,  
        old_status=resolved_old_status,  
        new_status=resolved_new_status,  
        old_price=old_price,  
        new_price=new_price,  
    )  
