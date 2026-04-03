from pprint import pprint
import sys

from sqlalchemy import text
from sqlmodel import Session

from app.adapters.freshful.rendered_parser import parse_freshful_product_rendered
from app.db import engine
from app.routers.imports import upsert_product_snapshot_and_watchlist
from app.schemas import FreshfulImportRequest


def infer_target_unit_from_parsed(parsed: dict) -> str:
    unit = (parsed.get("unit_price_unit") or "").strip().lower()

    if unit == "l":
        return "lei/l"
    if unit == "kg":
        return "lei/kg"
    if unit == "buc":
        return "lei/buc"

    return "total"


def normalize_target_unit(unit: str | None) -> str | None:
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
    }

    return mapping.get(value, value)


def load_watchlist_item(session: Session, watchlist_id: int, item_id: int) -> dict:
    query = """
    SELECT
        wi.id AS watchlist_item_id,
        wi.watchlist_id AS watchlist_id,
        wi.store_product_id AS store_product_id,
        wi.target_price AS target_price,
        wi.target_unit AS target_unit,
        wi.notify_best_buy AS notify_best_buy,
        wi.notify_high_price AS notify_high_price,
        wi.is_active AS is_active,
        sp.title AS product_title,
        sp.url AS product_url
    FROM watchlistitem wi
    JOIN storeproduct sp ON sp.id = wi.store_product_id
    WHERE wi.watchlist_id = :watchlist_id AND wi.id = :item_id
    """

    row = session.exec(
        text(query),
        params={"watchlist_id": watchlist_id, "item_id": item_id},
    ).first()

    if not row:
        raise RuntimeError(
            f"Watchlist item {item_id} not found in watchlist {watchlist_id}"
        )

    if hasattr(row, "_mapping"):
        return dict(row._mapping)

    return dict(row)


def load_latest_snapshot(session: Session, store_product_id: int) -> dict | None:
    query = """
    SELECT
        ps.id,
        ps.store_product_id,
        ps.price_total,
        ps.old_price,
        ps.promo_label,
        ps.discount_percent,
        ps.deposit_value,
        ps.comparison_price,
        ps.comparison_unit,
        ps.unit_price_value,
        ps.unit_price_unit,
        ps.captured_at
    FROM pricesnapshot ps
    WHERE ps.store_product_id = :store_product_id
    ORDER BY ps.captured_at DESC, ps.id DESC
    LIMIT 1
    """

    row = session.exec(
        text(query),
        params={"store_product_id": store_product_id},
    ).first()

    if not row:
        return None

    if hasattr(row, "_mapping"):
        return dict(row._mapping)

    return dict(row)


def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: python refresh_rendered_item.py <watchlist_id> <item_id>")
        sys.exit(1)

    watchlist_id = int(sys.argv[1])
    item_id = int(sys.argv[2])

    with Session(engine) as session:
        print("=== 1) Citește watchlist item ===")
        item = load_watchlist_item(session, watchlist_id, item_id)
        pprint(item)

        product_url = item["product_url"]
        target_price = item.get("target_price")
        target_unit = item.get("target_unit")
        notify_best_buy = item.get("notify_best_buy", True)
        notify_high_price = item.get("notify_high_price", True)

        print("\n=== 2) Parse rendered via CDP ===")
        parsed = parse_freshful_product_rendered(product_url)
        pprint(parsed)

        effective_target_unit = normalize_target_unit(target_unit) or infer_target_unit_from_parsed(parsed)

        print("\n=== 3) Save direct in DB via upsert_product_snapshot_and_watchlist ===")
        payload = FreshfulImportRequest(
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
            availability=parsed.get("availability"),
            watchlist_id=watchlist_id,
            target_price=target_price,
            target_unit=effective_target_unit,
            notify_best_buy=bool(notify_best_buy),
            notify_high_price=bool(notify_high_price),
        )

        result = upsert_product_snapshot_and_watchlist(
            payload=payload,
            session=session,
            forced_watchlist_item_id=item_id,
        )
        pprint(result)

        print("\n=== 4) Verify latest snapshot from DB ===")
        latest = load_latest_snapshot(session, result["product_id"])
        pprint(latest)

        print("\n=== 5) Verify watchlist item link ===")
        item_after = load_watchlist_item(session, watchlist_id, item_id)
        pprint(item_after)

    print("\n=== DONE ===")


if __name__ == "__main__":
    main()