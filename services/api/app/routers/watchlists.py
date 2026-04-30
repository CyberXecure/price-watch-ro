import re
from datetime import datetime
import requests
import time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.adapters.freshful.client import fetch_html
from app.adapters.freshful.parser import parse_freshful_product_html
from app.adapters.freshful.rendered_parser import parse_freshful_product_rendered
from app.db import get_session
from app.models import PriceSnapshot, StoreProduct, Watchlist, WatchlistItem
from app.routers.imports import FreshfulImportRequest, upsert_product_snapshot_and_watchlist

router = APIRouter(prefix="/watchlists", tags=["watchlists"])


def _slugify(value: str) -> str:
    text = (value or "").strip().lower()

    replacements = {
        "ă": "a",
        "â": "a",
        "î": "i",
        "ș": "s",
        "ş": "s",
        "ț": "t",
        "ţ": "t",
    }

    for src, dst in replacements.items():
        text = text.replace(src, dst)

    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-{2,}", "-", text).strip("-")

    return text or "lista"


def _build_unique_watchlist_slug(
    session: Session,
    base_name: str,
    current_watchlist_id: int | None = None,
) -> str:
    base_slug = _slugify(base_name)
    slug = base_slug
    counter = 2

    while True:
        existing = session.exec(
            select(Watchlist).where(Watchlist.slug == slug)
        ).first()

        if not existing or existing.id == current_watchlist_id:
            return slug

        slug = f"{base_slug}-{counter}"
        counter += 1


def _ui_unit_from_db_enum(unit: str | None) -> str | None:
    if unit is None:
        return None

    raw = str(unit).strip()
    if not raw:
        return None

    normalized = raw.upper()

    if "LEI_PER_BUC" in normalized:
        return "lei/buc"
    if "LEI_PER_KG" in normalized:
        return "lei/kg"
    if "LEI_PER_L" in normalized:
        return "lei/l"
    if "TOTAL" in normalized:
        return "total"

    lowered = raw.lower()
    if lowered in {"buc", "lei/buc"}:
        return "lei/buc"
    if lowered in {"kg", "lei/kg"}:
        return "lei/kg"
    if lowered in {"l", "lei/l"}:
        return "lei/l"
    if lowered == "total":
        return "total"

    return raw


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


def _extract_count_from_package_text(package_text: str | None) -> float | None:
    if not package_text:
        return None

    text = str(package_text).strip().lower()

    match = re.search(
        r"(\d+(?:[.,]\d+)?)\s*(?:buc|buc\.|bucati|bucăți|oua|ouă)",
        text,
    )
    if not match:
        return None

    raw = match.group(1).replace(".", "").replace(",", ".")
    try:
        value = float(raw)
    except ValueError:
        return None

    if value <= 0:
        return None

    return value


def _is_discount_consistent(
    *,
    price_total: float | None,
    old_price: float | None,
    discount_percent: float | None,
    tolerance_percent_points: float = 3.0,
) -> bool:
    if (
        price_total is None
        or old_price is None
        or discount_percent is None
        or old_price <= 0
        or price_total <= 0
        or old_price <= price_total
    ):
        return False

    computed = ((old_price - price_total) / old_price) * 100.0
    return abs(computed - discount_percent) <= tolerance_percent_points


def _detect_promo_kind(
    *,
    package_text: str | None,
    bundle_count: int | float | None = None,
    promo_label: str | None,
    discount_percent: float | None,
    old_price: float | None,
    price_total: float | None,
) -> str | None:
    has_promo = (
        (promo_label is not None and str(promo_label).strip() != "")
        or (discount_percent is not None and discount_percent > 0)
        or (
            old_price is not None
            and price_total is not None
            and old_price > price_total
        )
    )

    if not has_promo:
        return None

    if bundle_count is not None:
        try:
            parsed_bundle_count = float(bundle_count)
        except (TypeError, ValueError):
            parsed_bundle_count = None

        if parsed_bundle_count is not None and parsed_bundle_count > 1:
            return "bundle"

    count = _extract_count_from_package_text(package_text)
    if count is not None and count > 1:
        return "bundle"

    return "standard"

def _sanitize_promo_fields(
    *,
    package_text: str | None,
    availability: str | None = None,
    bundle_count: int | float | None = None,
    promo_label: str | None,
    discount_percent: float | None,
    old_price: float | None,
    price_total: float | None,
) -> dict[str, Any]:
    safe_promo_label = promo_label if promo_label and str(promo_label).strip() else None
    safe_discount_percent = discount_percent
    safe_old_price = old_price

    normalized_availability = str(availability).strip().lower() if availability is not None else ""
    if normalized_availability == "out_of_stock":
        return {
            "promo_label": None,
            "discount_percent": None,
            "old_price": None,
            "promo_kind": None,
        }

    if (
        safe_old_price is not None
        and price_total is not None
        and safe_old_price <= price_total
    ):
        safe_old_price = None

    if safe_discount_percent is not None:
        if (
            safe_old_price is None
            or price_total is None
            or not _is_discount_consistent(
                price_total=price_total,
                old_price=safe_old_price,
                discount_percent=safe_discount_percent,
            )
        ):
            safe_discount_percent = None

    promo_kind = _detect_promo_kind(
        package_text=package_text,
        bundle_count=bundle_count,
        promo_label=safe_promo_label,
        discount_percent=safe_discount_percent,
        old_price=safe_old_price,
        price_total=price_total,
    )

    if promo_kind is None and safe_old_price is None and safe_discount_percent is None:
        safe_promo_label = None

    return {
        "promo_label": safe_promo_label,
        "discount_percent": safe_discount_percent,
        "old_price": safe_old_price,
        "promo_kind": promo_kind,
    }

def _build_payload_from_parsed(
    parsed: dict[str, Any],
    watchlist_id: int,
    item: WatchlistItem,
) -> FreshfulImportRequest:
    return FreshfulImportRequest(
        url=parsed.get("url") or "",
        title=parsed.get("title") or "Produs",
        brand=parsed.get("brand"),
        image_url=parsed.get("image_url"),
        category=parsed.get("category"),
        base_measure_type=parsed.get("base_measure_type") or "unknown",
        base_measure_value=parsed.get("base_measure_value"),
        base_measure_unit=parsed.get("base_measure_unit"),
        external_id=parsed.get("external_id"),
        price_total=parsed.get("price_total"),
        currency=parsed.get("currency") or "RON",
        unit_price_value=parsed.get("unit_price_value"),
        unit_price_unit=parsed.get("unit_price_unit"),
        old_price=parsed.get("old_price"),
        promo_label=_normalize_promo_label(parsed.get("promo_label")),
        discount_percent=parsed.get("discount_percent"),
        promo_kind=parsed.get("promo_kind"),
        deposit_value=parsed.get("deposit_value"),
        availability=parsed.get("availability") or "unknown",
        watchlist_id=watchlist_id,
        target_price=item.target_price,
        target_unit=item.target_unit,
        notify_best_buy=item.notify_best_buy,
        notify_high_price=item.notify_high_price,
    )


def _merge_refresh_parsed(
    *,
    static_parsed: dict[str, Any] | None,
    rendered_parsed: dict[str, Any] | None,
    product: StoreProduct,
) -> dict[str, Any]:
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
        "bundle_count": _first_non_empty(
            rendered_parsed.get("bundle_count"),
            static_parsed.get("bundle_count"),
        ),
        "availability": (
            static_parsed.get("availability")
            if rendered_parsed.get("availability") in (None, "", "unknown")
            else _first_non_empty(
                rendered_parsed.get("availability"),
                static_parsed.get("availability"),
                "unknown",
            )
        ),
    }

    return merged


def _validate_rendered_pricing_consistency(
    *,
    merged_parsed: dict[str, Any],
    rendered_parsed: dict[str, Any] | None,
    product: StoreProduct,
) -> dict[str, bool]:
    rendered_parsed = rendered_parsed or {}

    price_total = merged_parsed.get("price_total")
    unit_price_value = merged_parsed.get("unit_price_value")
    unit_price_unit = merged_parsed.get("unit_price_unit")
    old_price = merged_parsed.get("old_price")
    discount_percent = merged_parsed.get("discount_percent")

    package_text = merged_parsed.get("package_text") or product.package_text

    checks = {
        "price_ok": True,
        "old_price_ok": True,
        "discount_ok": True,
    }

    if price_total is None or price_total <= 0:
        checks["price_ok"] = False

    count = _extract_count_from_package_text(package_text)
    if (
        count is not None
        and count > 1
        and unit_price_value is not None
        and unit_price_unit == "buc"
        and price_total is not None
        and price_total > 0
    ):
        expected_total = unit_price_value * count
        ratio_diff = abs(expected_total - price_total)

        if ratio_diff > 0.25:
            checks["price_ok"] = False

    if old_price is not None and price_total is not None:
        if old_price <= price_total:
            checks["old_price_ok"] = False

    if discount_percent is not None:
        checks["discount_ok"] = _is_discount_consistent(
            price_total=price_total,
            old_price=old_price,
            discount_percent=discount_percent,
        )

    return checks


def _apply_rendered_promo_safely(
    *,
    merged_parsed: dict[str, Any],
    static_parsed: dict[str, Any] | None,
    rendered_parsed: dict[str, Any] | None,
    product: StoreProduct,
) -> tuple[dict[str, Any], dict[str, bool]]:
    static_parsed = static_parsed or {}
    rendered_parsed = rendered_parsed or {}

    checks = _validate_rendered_pricing_consistency(
        merged_parsed=merged_parsed,
        rendered_parsed=rendered_parsed,
        product=product,
    )

    safe = dict(merged_parsed)

    if not checks["price_ok"]:
        safe["price_total"] = _first_non_empty(
            static_parsed.get("price_total"),
            merged_parsed.get("price_total"),
        )
        safe["unit_price_value"] = _first_non_empty(
            static_parsed.get("unit_price_value"),
            merged_parsed.get("unit_price_value"),
        )
        safe["unit_price_unit"] = _first_non_empty(
            static_parsed.get("unit_price_unit"),
            merged_parsed.get("unit_price_unit"),
        )

    if not checks["old_price_ok"]:
        safe["old_price"] = _first_non_empty(
            static_parsed.get("old_price"),
            None,
        )

    if not checks["discount_ok"]:
        safe["discount_percent"] = _first_non_empty(
            static_parsed.get("discount_percent"),
            None,
        )

    static_price_total = static_parsed.get("price_total")
    rendered_price_total = rendered_parsed.get("price_total")

    rendered_suspicious_vs_static = (
        static_price_total is not None
        and rendered_price_total is not None
        and rendered_price_total < (static_price_total * 0.8)
    )

    if rendered_suspicious_vs_static:
        safe["price_total"] = _first_non_empty(
            static_parsed.get("price_total"),
            merged_parsed.get("price_total"),
        )
        safe["old_price"] = _first_non_empty(
            static_parsed.get("old_price"),
            merged_parsed.get("old_price"),
        )
        safe["discount_percent"] = _first_non_empty(
            static_parsed.get("discount_percent"),
            merged_parsed.get("discount_percent"),
        )
        safe["promo_label"] = _first_non_empty(
            static_parsed.get("promo_label"),
            merged_parsed.get("promo_label"),
        )
        safe["unit_price_value"] = _first_non_empty(
            static_parsed.get("unit_price_value"),
            merged_parsed.get("unit_price_value"),
        )
        safe["unit_price_unit"] = _first_non_empty(
            static_parsed.get("unit_price_unit"),
            merged_parsed.get("unit_price_unit"),
        )
        checks["price_ok"] = False

    safe["promo_label"] = _first_non_empty(
        rendered_parsed.get("promo_label"),
        static_parsed.get("promo_label"),
        merged_parsed.get("promo_label"),
    )

    if rendered_suspicious_vs_static:
        safe["promo_label"] = _first_non_empty(
            static_parsed.get("promo_label"),
            merged_parsed.get("promo_label"),
        )

    bundle_kind = _first_non_empty(
        static_parsed.get("promo_kind"),
        rendered_parsed.get("promo_kind"),
        merged_parsed.get("promo_kind"),
    )

    if bundle_kind == "bundle":
        safe["promo_kind"] = "bundle"
        safe["price_total"] = _first_non_empty(
            static_parsed.get("price_total"),
            merged_parsed.get("price_total"),
        )
        safe["old_price"] = None
        safe["unit_price_value"] = _first_non_empty(
            static_parsed.get("unit_price_value"),
            merged_parsed.get("unit_price_value"),
        )
        safe["unit_price_unit"] = _first_non_empty(
            static_parsed.get("unit_price_unit"),
            merged_parsed.get("unit_price_unit"),
        )
        safe["promo_label"] = _first_non_empty(
            static_parsed.get("promo_label"),
            rendered_parsed.get("promo_label"),
            merged_parsed.get("promo_label"),
            "OFERTĂ",
        )
        safe["discount_percent"] = None

    safe["price_total"] = _first_non_empty(
        static_parsed.get("price_total"),
        merged_parsed.get("price_total"),
        safe.get("price_total"),
    )
    safe["unit_price_value"] = _first_non_empty(
        static_parsed.get("unit_price_value"),
        merged_parsed.get("unit_price_value"),
        safe.get("unit_price_value"),
    )
    safe["unit_price_unit"] = _first_non_empty(
        static_parsed.get("unit_price_unit"),
        merged_parsed.get("unit_price_unit"),
        safe.get("unit_price_unit"),
    )

    if safe.get("promo_kind") == "bundle":
        safe["old_price"] = None
        safe["discount_percent"] = None
    else:
        safe["old_price"] = _first_non_empty(
            static_parsed.get("old_price"),
            merged_parsed.get("old_price"),
            safe.get("old_price"),
        )

    return safe, checks


def _normalize_comparison_unit_for_status(unit: str | None) -> str:
    ui_unit = _ui_unit_from_db_enum(unit)

    if ui_unit is None:
        return ""

    normalized = str(ui_unit).strip().lower()

    if normalized in {"lei/buc", "buc", "/buc"}:
        return "lei/buc"
    if normalized in {"lei/kg", "kg", "/kg"}:
        return "lei/kg"
    if normalized in {"lei/l", "l", "/l"}:
        return "lei/l"
    if normalized == "total":
        return "total"

    return normalized


def _classify_price_status(
    *,
    target_price: float | None,
    target_unit: str | None,
    current_comparison_price: float | None,
    current_comparison_unit: str | None,
) -> str:
    if (
        target_price is None
        or current_comparison_price is None
        or current_comparison_price <= 0
    ):
        return "fair_price"

    normalized_target_unit = _normalize_comparison_unit_for_status(target_unit)
    normalized_current_unit = _normalize_comparison_unit_for_status(current_comparison_unit)

    if normalized_target_unit and normalized_current_unit:
        if normalized_target_unit != normalized_current_unit:
            return "fair_price"

    lower_bound = target_price * 0.95
    upper_bound = target_price * 1.05

    if current_comparison_price <= lower_bound:
        return "best_buy"

    if current_comparison_price >= upper_bound:
        return "high_price"

    return "fair_price"


def _compute_status_label(status: str) -> str:
    mapping = {
        "best_buy": "Chilipir",
        "fair_price": "Preț cinstit",
        "high_price": "Răsfăț",
    }
    return mapping.get(status, status)



def _ensure_promo_engine_ready_for_rendered() -> None:
    last_error = None

    for _ in range(3):
        try:
            response = requests.post(
                "http://127.0.0.1:18400/health/promo-engine/start",
                timeout=10,
            )
            response.raise_for_status()
        except Exception as exc:
            last_error = exc

        time.sleep(2)

        for _ in range(30):
            try:
                probe = requests.get(
                    "http://127.0.0.1:9222/json/version",
                    timeout=2,
                )
                probe.raise_for_status()
                return
            except Exception as exc:
                last_error = exc
                time.sleep(0.5)

    if last_error:
        raise last_error


def _latest_snapshot_for_product(
    session: Session,
    store_product_id: int,
) -> PriceSnapshot | None:
    return session.exec(
        select(PriceSnapshot)
        .where(PriceSnapshot.store_product_id == store_product_id)
        .order_by(PriceSnapshot.captured_at.desc(), PriceSnapshot.id.desc())
    ).first()


def _preserve_recent_promo_fields(
    *,
    parsed: dict[str, Any],
    previous_snapshot: PriceSnapshot | None,
    max_age_hours: float = 12.0,
) -> dict[str, Any]:
    if previous_snapshot is None:
        return parsed

    has_new_promo = any(
        [
            parsed.get("promo_label"),
            parsed.get("discount_percent") is not None and parsed.get("discount_percent") > 0,
            parsed.get("old_price") is not None
            and parsed.get("price_total") is not None
            and parsed.get("old_price") > parsed.get("price_total"),
        ]
    )

    if has_new_promo:
        return parsed

    previous_has_promo = any(
        [
            previous_snapshot.promo_label,
            previous_snapshot.discount_percent is not None and previous_snapshot.discount_percent > 0,
            previous_snapshot.old_price is not None
            and previous_snapshot.price_total is not None
            and previous_snapshot.old_price > previous_snapshot.price_total,
        ]
    )

    if not previous_has_promo:
        return parsed

    now = datetime.utcnow()
    age_hours = (now - previous_snapshot.captured_at).total_seconds() / 3600.0

    if age_hours > max_age_hours:
        return parsed

    safe = dict(parsed)
    safe["promo_label"] = previous_snapshot.promo_label
    safe["discount_percent"] = previous_snapshot.discount_percent
    safe["old_price"] = previous_snapshot.old_price

    return safe

def _build_refresh_response(
    *,
    session: Session,
    item: WatchlistItem,
    product: StoreProduct,
    parser_used: str,
    static_parsed: dict[str, Any] | None,
    rendered_parsed: dict[str, Any] | None,
    rendered_error: str | None,
    saved_snapshot_id: int | None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    latest_snapshot = _latest_snapshot_for_product(session, item.store_product_id)

    current_status = None
    current_status_label = None
    latest_comparison_price = None
    latest_comparison_unit = None
    sanitized_promo = {
        "promo_label": None,
        "discount_percent": None,
        "old_price": None,
        "promo_kind": None,
    }

    if latest_snapshot:
        if getattr(latest_snapshot, "promo_kind", None):
            sanitized_promo = {
                "promo_label": latest_snapshot.promo_label,
                "discount_percent": latest_snapshot.discount_percent,
                "old_price": latest_snapshot.old_price,
                "promo_kind": latest_snapshot.promo_kind,
            }
        else:
            sanitized_promo = _sanitize_promo_fields(
                package_text=product.package_text,
                bundle_count=_first_non_empty(
                    rendered_parsed.get("bundle_count") if rendered_parsed else None,
                    static_parsed.get("bundle_count") if static_parsed else None,
                ),
                promo_label=latest_snapshot.promo_label,
                discount_percent=latest_snapshot.discount_percent,
                old_price=latest_snapshot.old_price,
                price_total=latest_snapshot.price_total,
            )

        current_status = _classify_price_status(
            target_price=item.target_price,
            target_unit=item.target_unit,
            current_comparison_price=latest_snapshot.unit_price_value,
            current_comparison_unit=latest_snapshot.unit_price_unit,
        )
        current_status_label = _compute_status_label(current_status)
        latest_comparison_price = latest_snapshot.unit_price_value
        latest_comparison_unit = _ui_unit_from_db_enum(latest_snapshot.unit_price_unit)

    response = {
        "ok": True,
        "message": "Produs actualizat",
        "parser_used": parser_used,
        "rendered_error": rendered_error,
        "watchlist_item_id": item.id,
        "store_product_id": product.id,
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
        "latest_old_price": sanitized_promo["old_price"],
        "latest_promo_label": sanitized_promo["promo_label"],
        "latest_discount_percent": sanitized_promo["discount_percent"],
        "latest_promo_kind": sanitized_promo["promo_kind"],
        "latest_deposit_value": latest_snapshot.deposit_value if latest_snapshot else None,
                "latest_availability": latest_snapshot.availability if latest_snapshot else None,
        "latest_comparison_price": latest_comparison_price,
        "latest_comparison_unit": latest_comparison_unit,
        "latest_captured_at": latest_snapshot.captured_at.isoformat() if latest_snapshot else None,
        "current_status": current_status,
        "current_status_label": current_status_label,
    }

    if extra:
        response.update(extra)

    return response

@router.get("")
def list_watchlists(session: Session = Depends(get_session)):
    return session.exec(select(Watchlist).order_by(Watchlist.created_at.asc())).all()


@router.get("/with-summary")
def list_watchlists_with_summary(session: Session = Depends(get_session)):
    watchlists = session.exec(
        select(Watchlist).order_by(Watchlist.created_at.asc())
    ).all()

    result = []
    for watchlist in watchlists:
        items = session.exec(
            select(WatchlistItem).where(WatchlistItem.watchlist_id == watchlist.id)
        ).all()

        total_items = len(items)
        total_chilipir = 0
        total_pret_cinstit = 0
        total_rasfat = 0

        for item in items:
            latest_snapshot = _latest_snapshot_for_product(session, item.store_product_id)
            if not latest_snapshot:
                continue

            status = _classify_price_status(
                target_price=item.target_price,
                target_unit=item.target_unit,
                current_comparison_price=latest_snapshot.unit_price_value,
                current_comparison_unit=latest_snapshot.unit_price_unit,
            )

            if status == "best_buy":
                total_chilipir += 1
            elif status == "high_price":
                total_rasfat += 1
            else:
                total_pret_cinstit += 1

        result.append(
            {
                "id": watchlist.id,
                "slug": watchlist.slug,
                "name": watchlist.name,
                "icon": watchlist.icon,
                "description": watchlist.description,
                "sort_order": watchlist.sort_order,
                "created_at": watchlist.created_at,
                "updated_at": watchlist.updated_at,
                "total_items": total_items,
                "total_chilipir": total_chilipir,
                "total_pret_cinstit": total_pret_cinstit,
                "total_rasfat": total_rasfat,
            }
        )

    return result


@router.post("")
def create_watchlist(payload: dict[str, Any], session: Session = Depends(get_session)):
    name = (payload.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Name is required")

    existing_name = session.exec(
        select(Watchlist).where(Watchlist.name == name)
    ).first()
    if existing_name:
        raise HTTPException(status_code=400, detail="Există deja o listă cu acest nume")

    now = datetime.utcnow()
    watchlist = Watchlist(
        slug=_build_unique_watchlist_slug(session, name),
        name=name,
        icon=payload.get("icon"),
        description=payload.get("description"),
        sort_order=int(payload.get("sort_order") or 0),
        created_at=now,
        updated_at=now,
    )
    session.add(watchlist)
    session.commit()
    session.refresh(watchlist)
    return watchlist


@router.get("/{watchlist_id}")
def get_watchlist(watchlist_id: int, session: Session = Depends(get_session)):
    watchlist = session.get(Watchlist, watchlist_id)
    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    return watchlist


@router.patch("/{watchlist_id}")
def update_watchlist(
    watchlist_id: int,
    payload: dict[str, Any],
    session: Session = Depends(get_session),
):
    watchlist = session.get(Watchlist, watchlist_id)
    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")

    if "name" in payload:
        name = (payload.get("name") or "").strip()
        if not name:
            raise HTTPException(status_code=400, detail="Name is required")

        existing_name = session.exec(
            select(Watchlist).where(
                Watchlist.name == name,
                Watchlist.id != watchlist_id,
            )
        ).first()
        if existing_name:
            raise HTTPException(status_code=400, detail="Există deja o listă cu acest nume")

        watchlist.name = name
        watchlist.slug = _build_unique_watchlist_slug(
            session,
            name,
            current_watchlist_id=watchlist_id,
        )

    if "icon" in payload:
        watchlist.icon = payload.get("icon")

    if "description" in payload:
        watchlist.description = payload.get("description")

    if "sort_order" in payload:
        watchlist.sort_order = int(payload.get("sort_order") or 0)

    watchlist.updated_at = datetime.utcnow()

    session.add(watchlist)
    session.commit()
    session.refresh(watchlist)
    return watchlist


@router.delete("/{watchlist_id}")
def delete_watchlist(watchlist_id: int, session: Session = Depends(get_session)):
    watchlist = session.get(Watchlist, watchlist_id)
    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")

    items = session.exec(
        select(WatchlistItem).where(WatchlistItem.watchlist_id == watchlist_id)
    ).all()

    for item in items:
        session.delete(item)

    session.delete(watchlist)
    session.commit()

    return {"ok": True, "deleted_watchlist_id": watchlist_id}


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
        .order_by(WatchlistItem.created_at.asc())
    ).all()

    result = []
    for item in items:
        product = session.get(StoreProduct, item.store_product_id)
        if not product:
            continue

        latest_snapshot = _latest_snapshot_for_product(session, item.store_product_id)

        latest_price_total = latest_snapshot.price_total if latest_snapshot else None
        latest_unit_price_value = latest_snapshot.unit_price_value if latest_snapshot else None
        latest_unit_price_unit = latest_snapshot.unit_price_unit if latest_snapshot else None

        latest_bundle_count = None
        if latest_snapshot and product.url and "freshful.ro" in product.url:
            try:
                rendered_latest = parse_product_page_rendered(product.url)
                latest_bundle_count = rendered_latest.get("bundle_count")
            except Exception:
                latest_bundle_count = None

        if latest_snapshot and getattr(latest_snapshot, "promo_kind", None):
            sanitized_promo = {
                "promo_label": latest_snapshot.promo_label,
                "discount_percent": latest_snapshot.discount_percent,
                "old_price": latest_snapshot.old_price,
                "promo_kind": latest_snapshot.promo_kind,
            }

            if latest_bundle_count is not None:
                sanitized_promo["promo_kind"] = "bundle"
                sanitized_promo["old_price"] = None
                sanitized_promo["discount_percent"] = None
        else:
            sanitized_promo = _sanitize_promo_fields(
                package_text=product.package_text,
                bundle_count=latest_bundle_count,
                promo_label=latest_snapshot.promo_label if latest_snapshot else None,
                discount_percent=latest_snapshot.discount_percent if latest_snapshot else None,
                old_price=latest_snapshot.old_price if latest_snapshot else None,
                price_total=latest_snapshot.price_total if latest_snapshot else None,
            )

        current_status = _classify_price_status(
            target_price=item.target_price,
            target_unit=item.target_unit,
            current_comparison_price=latest_unit_price_value,
            current_comparison_unit=latest_unit_price_unit,
        )
        current_status_label = _compute_status_label(current_status)

        result.append(
            {
                "watchlist_item_id": item.id,
                "watchlist_id": item.watchlist_id,
                "store_product_id": item.store_product_id,
                "product_title": product.title,
                "product_brand": product.brand,
                "product_category": product.category,
                "product_url": product.url,
                "product_image_url": product.image_url,
                "package_text": product.package_text,
                "current_status": current_status,
                "current_status_label": current_status_label,
                "target_price": item.target_price,
                "target_unit": item.target_unit,
                "latest_price_total": latest_price_total,
                "latest_comparison_price": latest_unit_price_value,
                "latest_comparison_unit": _ui_unit_from_db_enum(latest_unit_price_unit),
                "latest_unit_price_value": latest_unit_price_value,
                "latest_unit_price_unit": _ui_unit_from_db_enum(latest_unit_price_unit),
                "latest_old_price": sanitized_promo["old_price"],
                "latest_promo_label": sanitized_promo["promo_label"],
                "latest_discount_percent": sanitized_promo["discount_percent"],
                "latest_promo_kind": sanitized_promo["promo_kind"],
                "latest_deposit_value": latest_snapshot.deposit_value if latest_snapshot else None,
                "latest_availability": latest_snapshot.availability if latest_snapshot else None,
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
    payload: dict[str, Any],
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

    if "target_price" in payload:
        item.target_price = payload.get("target_price")

    if "target_unit" in payload:
        item.target_unit = payload.get("target_unit")

    if "notify_best_buy" in payload:
        item.notify_best_buy = bool(payload.get("notify_best_buy"))

    if "notify_high_price" in payload:
        item.notify_high_price = bool(payload.get("notify_high_price"))

    if "is_active" in payload:
        item.is_active = bool(payload.get("is_active"))

    item.updated_at = datetime.utcnow()

    session.add(item)
    session.commit()
    session.refresh(item)
    return item


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
        previous_snapshot = _latest_snapshot_for_product(session, item.store_product_id)

        html = fetch_html(product.url)
        static_parsed = parse_freshful_product_html(html, product.url)
        static_parsed = _preserve_recent_promo_fields(
            parsed=static_parsed,
            previous_snapshot=previous_snapshot,
            max_age_hours=12.0,
        )

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



@router.post("/{watchlist_id}/refresh-active-rendered")
def refresh_active_watchlist_items_rendered(
    watchlist_id: int,
    session: Session = Depends(get_session),
):
    try:
        _ensure_promo_engine_ready_for_rendered()
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Promo engine start failed: {type(exc).__name__}: {exc}",
        ) from exc
    watchlist = session.get(Watchlist, watchlist_id)
    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")

    items = session.exec(
        select(WatchlistItem).where(
            WatchlistItem.watchlist_id == watchlist_id,
            WatchlistItem.is_active == True,  # noqa: E712
        )
    ).all()

    results: list[dict[str, Any]] = []

    for item in items:
        product = session.get(StoreProduct, item.store_product_id)
        if not product:
            results.append(
                {
                    "watchlist_item_id": item.id,
                    "ok": False,
                    "detail": "Store product not found",
                }
            )
            continue

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

            safe_parsed, pricing_checks = _apply_rendered_promo_safely(
                merged_parsed=merged_parsed,
                static_parsed=static_parsed,
                rendered_parsed=rendered_parsed,
                product=product,
            )

            if safe_parsed.get("price_total") is None:
                results.append(
                    {
                        "watchlist_item_id": item.id,
                        "ok": False,
                        "detail": "missing price_total after validation",
                    }
                )
                continue

            payload = _build_payload_from_parsed(safe_parsed, watchlist_id, item)
            upsert_result = upsert_product_snapshot_and_watchlist(
                payload=payload,
                session=session,
                forced_watchlist_item_id=item.id,
            )

            results.append(
                {
                    "watchlist_item_id": item.id,
                    "ok": True,
                    "snapshot_id": upsert_result.get("snapshot_id"),
                    "parser_used": "rendered",
                    "rendered_pricing_checks": pricing_checks,
                    "safe_price_total": safe_parsed.get("price_total"),
                    "safe_old_price": safe_parsed.get("old_price"),
                    "safe_discount_percent": safe_parsed.get("discount_percent"),
                    "safe_promo_kind": safe_parsed.get("promo_kind"),
                }
            )
        except Exception as exc:
            results.append(
                {
                    "watchlist_item_id": item.id,
                    "ok": False,
                    "detail": f"{type(exc).__name__}: {exc}",
                }
            )

    return {
        "ok": True,
        "watchlist_id": watchlist_id,
        "processed": len(results),
        "results": results,
    }


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

        safe_parsed, pricing_checks = _apply_rendered_promo_safely(
            merged_parsed=merged_parsed,
            static_parsed=static_parsed,
            rendered_parsed=rendered_parsed,
            product=product,
        )

        if safe_parsed.get("price_total") is None:
            raise HTTPException(
                status_code=400,
                detail="Rendered refresh failed: missing price_total after validation",
            )

        payload = _build_payload_from_parsed(safe_parsed, watchlist_id, item)
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
            extra={
                "rendered_pricing_checks": pricing_checks,
                "safe_price_total": safe_parsed.get("price_total"),
                "safe_unit_price_value": safe_parsed.get("unit_price_value"),
                "safe_unit_price_unit": safe_parsed.get("unit_price_unit"),
                "safe_old_price": safe_parsed.get("old_price"),
                "safe_discount_percent": safe_parsed.get("discount_percent"),
            },
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Rendered refresh failed: {type(exc).__name__}: {exc}",
        ) from exc













