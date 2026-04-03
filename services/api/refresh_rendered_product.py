import sys
from pprint import pprint

import httpx

from app.adapters.freshful.rendered_parser import parse_freshful_product_rendered

API_BASE = "http://127.0.0.1:8000"


def main():
    if len(sys.argv) < 4:
        print(
            "Usage: python refresh_rendered_product.py <watchlist_id> <item_id> <product_url>"
        )
        sys.exit(1)

    watchlist_id = int(sys.argv[1])
    item_id = int(sys.argv[2])
    product_url = sys.argv[3]

    print("=== 1) Parse rendered ===")
    parsed = parse_freshful_product_rendered(product_url)
    pprint(parsed)

    print("\n=== 2) Read existing watchlist item ===")
    with httpx.Client(timeout=60) as client:
        items = client.get(
            f"{API_BASE}/watchlists/{watchlist_id}/items/detailed"
        ).raise_for_status()
        items_json = client.get(
            f"{API_BASE}/watchlists/{watchlist_id}/items/detailed"
        ).json()

    item = next((x for x in items_json if x["watchlist_item_id"] == item_id), None)
    if not item:
        raise RuntimeError(f"Watchlist item {item_id} not found in watchlist {watchlist_id}")

    print(item)

    target_price = item.get("target_price")
    target_unit = item.get("target_unit") or (
        "lei/l"
        if parsed.get("unit_price_unit") == "l"
        else "lei/kg"
        if parsed.get("unit_price_unit") == "kg"
        else "lei/buc"
        if parsed.get("unit_price_unit") == "buc"
        else "total"
    )

    print("\n=== 3) Save through imports endpoint ===")
    params = {
        "url": parsed["url"],
        "watchlist_id": watchlist_id,
        "target_price": target_price,
    }

    with httpx.Client(timeout=120) as client:
        response = client.post(
            f"{API_BASE}/imports/freshful-url-auto",
            params=params,
        )
        response.raise_for_status()
        result = response.json()

    print("\n=== 4) Import result ===")
    pprint(result)

    print("\n=== DONE ===")


if __name__ == "__main__":
    main()