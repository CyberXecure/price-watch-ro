import json
import re
from typing import Any, Optional
from urllib.parse import urlparse

from bs4 import BeautifulSoup


def clean_text(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    value = re.sub(r"\s+", " ", value).strip()
    return value or None


def clean_product_title(value: Optional[str]) -> Optional[str]:
    text = clean_text(value)
    if not text:
        return None

    patterns = [
        r"\s*-\s*Prospețime și varietate\s*-\s*Freshful\.ro\s*$",
        r"\s*-\s*Freshful\.ro\s*$",
        r"\s*-\s*Freshful\s*$",
    ]

    for pattern in patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE).strip()

    return text


def slug_to_brand_name(slug: str) -> str:
    parts = [p for p in slug.split("-") if p]
    if not parts:
        return slug

    normalized = []
    for part in parts:
        if part.lower() in {"and", "of", "the"}:
            normalized.append(part.lower())
        else:
            normalized.append(part.capitalize())

    return " ".join(normalized)


def extract_brand_from_url(url: str) -> Optional[str]:
    path = urlparse(url).path.strip("/")
    if not path:
        return None

    last_segment = path.split("/")[-1]
    match = re.match(r"^\d+-(.+)$", last_segment)
    if not match:
        return None

    slug = match.group(1)
    parts = [p for p in slug.split("-") if p]
    if not parts:
        return None

    stop_words = {
        "pui", "pulpe", "ficat", "piept", "aripi", "oua", "ouă", "lapte", "iaurt",
        "smantana", "smântâna", "unt", "cascaval", "cașcaval", "branza", "brânză",
        "betisoare", "bețișoare", "igienice", "bumbac", "buchet", "trandafiri",
        "flori", "diverse", "culori", "grill", "de", "din", "superioare", "dezosate",
        "proaspat", "proaspăt", "proaspete", "kg", "g", "l", "ml", "buc", "fire",
        "limonada", "limonadă", "cu", "lamaie", "lămâie", "verde", "zmeura", "zmeură",
        "eco",
    }

    brand_parts: list[str] = []
    for part in parts:
        lower = part.lower()

        if re.fullmatch(r"\d+(?:\.\d+)?", lower):
            break
        if re.fullmatch(r"\d+(?:kg|g|l|ml|buc)", lower):
            break
        if lower in stop_words:
            break

        brand_parts.append(part)

    if not brand_parts:
        return None

    return slug_to_brand_name("-".join(brand_parts))


def infer_brand_from_title(title: Optional[str]) -> Optional[str]:
    if not title:
        return None

    first_word = clean_text(title.split(" ")[0]) if title else None
    if not first_word:
        return None

    blocked = {
        "pui", "lapte", "ouă", "oua", "mere", "banane", "cartofi",
        "iaurt", "apă", "apa", "ulei", "pâine", "paine", "brânză",
        "branza", "cașcaval", "cascaval", "detergent", "scutece",
        "bețișoare", "betisoare", "buchet", "limonadă", "limonada",
        "lămâi", "lamai",
    }

    if first_word.lower() in blocked:
        return None

    if re.search(r"\d", first_word):
        return None

    return first_word


def parse_price_string(value: Optional[str]) -> Optional[float]:
    if not value:
        return None

    text = value.strip()
    text = text.replace("\xa0", " ")
    text = text.replace("RON", "")
    text = text.replace("lei", "")
    text = text.replace("LEI", "")
    text = text.strip()
    text = text.replace(",", ".")

    match = re.search(r"(\d+(?:\.\d{1,2})?)", text)
    if not match:
        return None

    try:
        return float(match.group(1))
    except ValueError:
        return None


def parse_unit_price_text(value: Optional[str]) -> tuple[Optional[float], Optional[str]]:
    if not value:
        return None, None

    text = value.strip().lower()
    text = text.replace("\xa0", " ")
    text = text.replace(",", ".")

    number_match = re.search(r"(\d+(?:\.\d{1,2})?)", text)
    if not number_match:
        return None, None

    unit = None
    if "/l" in text or "lei/l" in text:
        unit = "l"
    elif "/kg" in text or "lei/kg" in text:
        unit = "kg"
    elif "/buc" in text or "lei/buc" in text:
        unit = "buc"

    try:
        value_float = float(number_match.group(1))
    except ValueError:
        return None, None

    return value_float, unit


def extract_discount_percent(text: str) -> Optional[float]:
    if not text:
        return None

    patterns = [
        r"economisești\s*(\d+(?:[.,]\d+)?)\s*%",
        r"economisesti\s*(\d+(?:[.,]\d+)?)\s*%",
        r"reducere\s*(\d+(?:[.,]\d+)?)\s*%",
        r"discount\s*(\d+(?:[.,]\d+)?)\s*%",
        r"promo\s*(\d+(?:[.,]\d+)?)\s*%",
        r"ofert[ăa]\s*(\d+(?:[.,]\d+)?)\s*%",
        r"(?:economisești|economisesti|reducere|discount|promo|ofert[ăa]).{0,20}?-\s*(\d+(?:[.,]\d+)?)\s*%",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                value = float(match.group(1).replace(",", "."))
            except ValueError:
                continue

            if value <= 0 or value >= 100:
                continue

            return value

    return None

def extract_promo_label(text: str) -> Optional[str]:
    for pattern in [r"\b(DEALS)\b", r"\b(PROMO)\b", r"\b(OFERT[ĂA])\b"]:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return clean_text(match.group(1).upper())
    return None


def extract_deposit_value(text: str) -> Optional[float]:
    match = re.search(r"\+\s*(\d+(?:[.,]\d{1,2})?)\s*Lei", text, re.IGNORECASE)
    if not match:
        return None

    try:
        return float(match.group(1).replace(",", "."))
    except ValueError:
        return None



def detect_availability(text: str) -> str:
    if not text:
        return "unknown"

    normalized = text.lower()
    normalized = normalized.replace("\xa0", " ")
    normalized = re.sub(r"\s+", " ", normalized)

    strong_out_of_stock_patterns = [
        "produsul nu este momentan în stoc",
        "produsul nu este momentan in stoc",
        "nu este momentan în stoc",
        "nu este momentan in stoc",
        "nu este în stoc",
        "nu este in stoc",
        "momentan indisponibil",
        "produs indisponibil",
        "stoc epuizat",
        "out of stock",
        "unavailable",
    ]

    strong_in_stock_patterns = [
        "adaugă în coș",
        "adauga in cos",
        "adaugă in coș",
        "adauga în cos",
    ]

    for pattern in strong_out_of_stock_patterns:
        if pattern in normalized:
            return "out_of_stock"

    for pattern in strong_in_stock_patterns:
        if pattern in normalized:
            return "in_stock"

    return "unknown"

def detect_bundle_count(text: str) -> Optional[int]:
    if not text:
        return None

    normalized = text.lower().replace("\xa0", " ")
    normalized = re.sub(r"\s+", " ", normalized)

    patterns = [
        r"\b(\d{1,2})\s*(?:buc|buc\.|bucati|bucăți)\b",
        r"\b(\d{1,2})\s*x\s*(?:buc|buc\.|bucati|bucăți)\b",
    ]

    for pattern in patterns:
        match = re.search(pattern, normalized, re.IGNORECASE)
        if match:
            try:
                value = int(match.group(1))
            except ValueError:
                continue

            if value > 1:
                return value

    return None


def detect_bundle_discount_percent(text: str) -> Optional[float]:
    if not text:
        return None

    normalized = text.lower().replace("\xa0", " ")
    normalized = re.sub(r"\s+", " ", normalized)

    patterns = [
        r"-\s*(\d+(?:[.,]\d+)?)\s*%",
        r"economise[șs]ti\s*(\d+(?:[.,]\d+)?)\s*%",
        r"economisesti\s*(\d+(?:[.,]\d+)?)\s*%",
    ]

    for pattern in patterns:
        match = re.search(pattern, normalized, re.IGNORECASE)
        if match:
            try:
                value = float(match.group(1).replace(",", "."))
            except ValueError:
                continue

            if value > 0 and value < 100:
                return value

    return None

def infer_measure_from_package(package_text: Optional[str]) -> tuple[str, Optional[float], Optional[str]]:
    if not package_text:
        return "unknown", None, None

    text = package_text.lower().strip()

    def parse_number(raw: str, count_mode: bool = False) -> float:
        raw = raw.strip()

        if count_mode:
            if "." in raw and "," not in raw:
                raw = raw.replace(".", "")
            else:
                raw = raw.replace(".", "").replace(",", "")
            return float(raw)

        raw = raw.replace(",", ".")
        return float(raw)

    volume_match = re.search(r"(\d+(?:[.,]\d+)?)\s*(l|ml)\b", text)
    if volume_match:
        value = parse_number(volume_match.group(1))
        unit = volume_match.group(2)
        if unit == "ml":
            return "volume", round(value / 1000, 4), "l"
        return "volume", value, "l"

    weight_match = re.search(r"(\d+(?:[.,]\d+)?)\s*(kg|g)\b", text)
    if weight_match:
        value = parse_number(weight_match.group(1))
        unit = weight_match.group(2)
        if unit == "g":
            return "weight", round(value / 1000, 4), "kg"
        return "weight", value, "kg"

    count_match = re.search(r"(\d+(?:[.,]\d+)?)\s*(buc|capsule|tablete|fire)\b", text)
    if count_match:
        value = parse_number(count_match.group(1), count_mode=True)
        return "count", value, "buc"

    return "unknown", None, None


def validate_unit_price_for_measure(
    measure_type: str,
    unit_price_value: Optional[float],
    unit_price_unit: Optional[str],
) -> tuple[Optional[float], Optional[str]]:
    if unit_price_value is None or unit_price_unit is None:
        return None, None

    allowed = {
        "volume": "l",
        "weight": "kg",
        "count": "buc",
    }

    expected_unit = allowed.get(measure_type)
    if expected_unit is None:
        return unit_price_value, unit_price_unit

    if unit_price_unit != expected_unit:
        return None, None

    return unit_price_value, unit_price_unit


def derive_unit_price_from_package(
    price_total: Optional[float],
    measure_type: str,
    measure_value: Optional[float],
) -> tuple[Optional[float], Optional[str]]:
    if price_total is None or measure_value is None or measure_value == 0:
        return None, None

    if measure_type == "count":
        return round(price_total / measure_value, 4), "buc"

    if measure_type == "volume":
        return round(price_total / measure_value, 4), "l"

    if measure_type == "weight":
        return round(price_total / measure_value, 4), "kg"

    return None, None


def extract_json_ld_candidates(soup: BeautifulSoup) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []

    for script in soup.find_all("script", type="application/ld+json"):
        raw = script.string or script.get_text()
        if not raw:
            continue

        try:
            parsed = json.loads(raw)
        except Exception:
            continue

        if isinstance(parsed, list):
            for item in parsed:
                if isinstance(item, dict):
                    result.append(item)
        elif isinstance(parsed, dict):
            result.append(parsed)

    return result


def extract_brand_and_product_from_json_ld(candidates: list[dict[str, Any]]) -> dict[str, Any]:
    data: dict[str, Any] = {}

    for item in candidates:
        item_type = item.get("@type")
        if item_type in ("Product", ["Product"]):
            data["title"] = data.get("title") or clean_product_title(item.get("name"))

            image = item.get("image")
            if isinstance(image, list) and image:
                data["image_url"] = data.get("image_url") or image[0]
            elif isinstance(image, str):
                data["image_url"] = data.get("image_url") or image

            brand = item.get("brand")
            if isinstance(brand, dict):
                data["brand"] = data.get("brand") or clean_text(brand.get("name"))
            elif isinstance(brand, str):
                data["brand"] = data.get("brand") or clean_text(brand)

            offers = item.get("offers")
            if isinstance(offers, dict):
                json_ld_price = parse_price_string(str(offers.get("price")))
                if json_ld_price is not None:
                    data["json_ld_price_total"] = json_ld_price
                data["currency"] = data.get("currency") or offers.get("priceCurrency")

    return data


def extract_category_from_breadcrumbs(candidates: list[dict[str, Any]]) -> Optional[str]:
    for item in candidates:
        item_type = item.get("@type")
        if item_type in ("BreadcrumbList", ["BreadcrumbList"]):
            elements = item.get("itemListElement", [])
            names: list[str] = []

            for el in elements:
                if not isinstance(el, dict):
                    continue

                name = None
                if isinstance(el.get("item"), dict):
                    name = el.get("item", {}).get("name")
                if not name:
                    name = el.get("name")

                cleaned = clean_text(name)
                if cleaned:
                    names.append(cleaned)

            filtered = [x for x in names if x.lower() not in {"freshful", "acasă", "home"}]

            if len(filtered) >= 2:
                return filtered[-2]
            if filtered:
                return filtered[-1]

    return None


def extract_meta_content(soup: BeautifulSoup, attr_name: str, attr_value: str) -> Optional[str]:
    tag = soup.find("meta", attrs={attr_name: attr_value})
    if not tag:
        return None
    return clean_text(tag.get("content"))


def find_first_text_matching(patterns: list[str], text: str) -> Optional[str]:
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return clean_text(match.group(1))
    return None


def extract_package_text(text: str) -> Optional[str]:
    patterns = [
        r"\b(\d+(?:[.,]\d+)?\s*(?:kg|g|ml|l|buc|fire))\b",
    ]

    for pattern in patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            candidate = clean_text(match.group(1))
            if not candidate:
                continue

            lowered = candidate.lower()
            if "lei" in lowered or "ron" in lowered:
                continue

            tail = text[match.end():match.end() + 3].lower()
            if tail.startswith("ei"):
                continue

            return candidate

    return None


def extract_main_product_text(soup: BeautifulSoup) -> str:
    selectors = [
        "main",
        '[data-testid="product-details"]',
        '[data-testid="product-page"]',
        '[data-testid="product-main"]',
        '[class*="product"]',
        '[class*="Product"]',
    ]

    chunks: list[str] = []

    for selector in selectors:
        try:
            nodes = soup.select(selector)
        except Exception:
            nodes = []

        for node in nodes[:3]:
            text = clean_text(node.get_text(" ", strip=True))
            if text and len(text) > 100:
                chunks.append(text)

    if chunks:
        return max(chunks, key=len)

    return clean_text(soup.get_text(" ", strip=True)) or ""


def extract_prices_from_text(text: str) -> list[float]:
    values: list[float] = []

    for match in re.finditer(
        r"(\d+(?:[.,]\d{1,2})?)\s*Lei(?!\s*/\s*(?:l|kg|buc))",
        text,
        re.IGNORECASE,
    ):
        raw_value = match.group(1)
        try:
            value = float(raw_value.replace(",", "."))
        except ValueError:
            continue

        start = max(0, match.start() - 24)
        end = min(len(text), match.end() + 40)
        context = text[start:end].lower()

        if "+" in context:
            continue
        if re.search(r"\b\d+\s*buc\b", context):
            continue
        if re.search(r"adaugă în coș|adauga in cos", context):
            continue
        if re.search(r"cod\b", context):
            continue

        if 0.5 <= value <= 500:
            values.append(value)

    return values


def extract_primary_offer_prices(text: str) -> tuple[Optional[float], Optional[float]]:
    normalized = re.sub(r"\s+", " ", text).strip()

    patterns = [
        r"(\d+(?:[.,]\d{1,2})?)\s*Lei(?!\s*/\s*(?:l|kg|buc)).{0,80}?(?:Economisești|economisești|economisesti)\s*\d+(?:[.,]\d+)?\s*%.{0,80}?(\d+(?:[.,]\d{1,2})?)\s*Lei",
        r"(\d+(?:[.,]\d{1,2})?)\s*Lei(?!\s*/\s*(?:l|kg|buc)).{0,80}?-\s*\d+(?:[.,]\d+)?\s*%.{0,80}?(\d+(?:[.,]\d{1,2})?)\s*Lei",
    ]

    for pattern in patterns:
        match = re.search(pattern, normalized, re.IGNORECASE)
        if not match:
            continue

        first = parse_price_string(match.group(1))
        second = parse_price_string(match.group(2))

        if first is None or second is None:
            continue

        if first >= second:
            current_price = second
            old_price = first
        else:
            current_price = first
            old_price = second

        if old_price > current_price:
            return current_price, old_price

    return None, None


def choose_price_total(
    *,
    json_ld_price_total: Optional[float],
    explicit_unit_price_value: Optional[float],
    explicit_unit_price_unit: Optional[str],
    measure_type: str,
    measure_value: Optional[float],
    text: str,
) -> tuple[Optional[float], Optional[float]]:
    text_current, text_old = extract_primary_offer_prices(text)
    all_prices = sorted(set(extract_prices_from_text(text)))

    if (
        json_ld_price_total is not None
        and explicit_unit_price_value is not None
        and measure_type in {"count", "weight", "volume"}
        and measure_value
    ):
        implied_from_unit = round(explicit_unit_price_value * measure_value, 2)

        if abs(json_ld_price_total - implied_from_unit) <= 0.2:
            old_price = text_old if text_old and text_old > json_ld_price_total else None
            return json_ld_price_total, old_price

    if text_current is not None:
        old_price = text_old if text_old and text_old > text_current else None
        return text_current, old_price

    if json_ld_price_total is not None:
        old_price = text_old if text_old and text_old > json_ld_price_total else None
        return json_ld_price_total, old_price

    if all_prices:
        current = max(all_prices)
        old_candidates = [x for x in all_prices if x > current]
        old_price = min(old_candidates) if old_candidates else None
        return current, old_price

    return None, None


def parse_freshful_product_html(html: str, url: str) -> dict[str, Any]:
    soup = BeautifulSoup(html, "lxml")
    full_text = clean_text(soup.get_text(" ", strip=True)) or ""
    product_text = extract_main_product_text(soup)

    data: dict[str, Any] = {
        "url": url,
        "currency": "RON",
    }

    json_ld_candidates = extract_json_ld_candidates(soup)
    data.update({
        k: v for k, v in extract_brand_and_product_from_json_ld(json_ld_candidates).items()
        if v is not None
    })

    raw_og_title = extract_meta_content(soup, "property", "og:title")
    raw_og_image = extract_meta_content(soup, "property", "og:image")
    raw_og_description = extract_meta_content(soup, "property", "og:description")

    data["title"] = data.get("title") or clean_product_title(raw_og_title)
    data["image_url"] = data.get("image_url") or raw_og_image

    if not data.get("title") and soup.title:
        data["title"] = clean_product_title(soup.title.get_text())

    package_text = extract_package_text(product_text) or extract_package_text(full_text) or extract_package_text(data.get("title") or "")
    if package_text:
        data["package_text"] = package_text

    measure_type, measure_value, measure_unit = infer_measure_from_package(data.get("package_text"))
    data["base_measure_type"] = measure_type
    data["base_measure_value"] = measure_value
    data["base_measure_unit"] = measure_unit

    data["discount_percent"] = extract_discount_percent(product_text) or extract_discount_percent(full_text)
    data["promo_label"] = extract_promo_label(product_text) or extract_promo_label(full_text)
    data["deposit_value"] = extract_deposit_value(product_text) or extract_deposit_value(full_text)

    unit_price_candidate = (
        find_first_text_matching(
            [
                r"(\d+(?:[.,]\d{1,2})\s*lei\s*/\s*(?:l|kg|buc))",
                r"(\d+(?:[.,]\d{1,2})\s*/\s*(?:l|kg|buc))",
            ],
            product_text,
        )
        or find_first_text_matching(
            [
                r"(\d+(?:[.,]\d{1,2})\s*lei\s*/\s*(?:l|kg|buc))",
                r"(\d+(?:[.,]\d{1,2})\s*/\s*(?:l|kg|buc))",
            ],
            full_text,
        )
    )

    unit_price_value, unit_price_unit = parse_unit_price_text(unit_price_candidate)
    unit_price_value, unit_price_unit = validate_unit_price_for_measure(
        measure_type=measure_type,
        unit_price_value=unit_price_value,
        unit_price_unit=unit_price_unit,
    )

    price_total, old_price = choose_price_total(
        json_ld_price_total=data.get("json_ld_price_total"),
        explicit_unit_price_value=unit_price_value,
        explicit_unit_price_unit=unit_price_unit,
        measure_type=measure_type,
        measure_value=measure_value,
        text=product_text or full_text,
    )

    if price_total is None:
        price_candidate = find_first_text_matching(
            [
                r"(\d+(?:[.,]\d{1,2})\s*lei(?!\s*/\s*(?:l|kg|buc)))",
                r"(\d+(?:[.,]\d{1,2})\s*RON)",
            ],
            product_text or full_text,
        )
        price_total = parse_price_string(price_candidate)

    if unit_price_value is None and measure_value is not None and measure_value > 0 and price_total is not None:
        unit_price_value, unit_price_unit = derive_unit_price_from_package(
            price_total=price_total,
            measure_type=measure_type,
            measure_value=measure_value,
        )

    json_ld_price_total = data.get("json_ld_price_total")
    data["price_total"] = price_total
    data["old_price"] = old_price
    data["unit_price_value"] = unit_price_value
    data["unit_price_unit"] = unit_price_unit

    if (
        data["price_total"] is not None
        and data["unit_price_value"] is not None
        and measure_type in {"count", "weight", "volume"}
        and measure_value
    ):
        implied_total = round(data["unit_price_value"] * measure_value, 2)

        # Dacă prețul extras și totalul derivat din prețul unitar sunt foarte apropiate,
        # păstrăm prețul extras din PDP (de ex. 22.99 în loc de 23.00).
        if abs(data["price_total"] - implied_total) <= 0.2:
            pass
        elif json_ld_price_total is not None and abs(json_ld_price_total - implied_total) <= 0.2:
            data["price_total"] = json_ld_price_total
        else:
            data["price_total"] = implied_total

    breadcrumb_category = extract_category_from_breadcrumbs(json_ld_candidates)
    data["category"] = data.get("category") or breadcrumb_category

    if not data.get("brand"):
        brand_from_description = find_first_text_matching(
            [r"brand[:\s]+([A-Za-zĂÂÎȘȚăâîșț0-9\-\& ]{2,50})"],
            raw_og_description or "",
        )
        data["brand"] = (
            brand_from_description
            or extract_brand_from_url(url)
            or infer_brand_from_title(data.get("title"))
        )

    data["external_id"] = None
    availability_from_product_text = detect_availability(product_text)
    availability_from_full_text = detect_availability(full_text)
    availability_from_html = detect_availability(html)

    if availability_from_product_text == "out_of_stock":
        data["availability"] = "out_of_stock"
    elif availability_from_full_text == "out_of_stock":
        data["availability"] = "out_of_stock"
    elif availability_from_html == "out_of_stock":
        data["availability"] = "out_of_stock"
    elif availability_from_product_text == "in_stock":
        data["availability"] = "in_stock"
    elif availability_from_full_text == "in_stock":
        data["availability"] = "in_stock"
    elif availability_from_html == "in_stock":
        data["availability"] = "in_stock"
    elif (
        data.get("price_total") is not None
        and data.get("unit_price_value") is not None
    ):
        data["availability"] = "in_stock"
    else:
        data["availability"] = "unknown"
import json
import re
from typing import Any, Optional
from urllib.parse import urlparse

from bs4 import BeautifulSoup


def clean_text(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    value = re.sub(r"\s+", " ", value).strip()
    return value or None


def clean_product_title(value: Optional[str]) -> Optional[str]:
    text = clean_text(value)
    if not text:
        return None

    patterns = [
        r"\s*-\s*Prospețime și varietate\s*-\s*Freshful\.ro\s*$",
        r"\s*-\s*Freshful\.ro\s*$",
        r"\s*-\s*Freshful\s*$",
    ]

    for pattern in patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE).strip()

    return text


def slug_to_brand_name(slug: str) -> str:
    parts = [p for p in slug.split("-") if p]
    if not parts:
        return slug

    normalized = []
    for part in parts:
        if part.lower() in {"and", "of", "the"}:
            normalized.append(part.lower())
        else:
            normalized.append(part.capitalize())

    return " ".join(normalized)


def extract_brand_from_url(url: str) -> Optional[str]:
    path = urlparse(url).path.strip("/")
    if not path:
        return None

    last_segment = path.split("/")[-1]
    match = re.match(r"^\d+-(.+)$", last_segment)
    if not match:
        return None

    slug = match.group(1)
    parts = [p for p in slug.split("-") if p]
    if not parts:
        return None

    stop_words = {
        "pui", "pulpe", "ficat", "piept", "aripi", "oua", "ouă", "lapte", "iaurt",
        "smantana", "smântâna", "unt", "cascaval", "cașcaval", "branza", "brânză",
        "betisoare", "bețișoare", "igienice", "bumbac", "buchet", "trandafiri",
        "flori", "diverse", "culori", "grill", "de", "din", "superioare", "dezosate",
        "proaspat", "proaspăt", "proaspete", "kg", "g", "l", "ml", "buc", "fire",
        "limonada", "limonadă", "cu", "lamaie", "lămâie", "verde", "zmeura", "zmeură",
        "eco",
    }

    brand_parts: list[str] = []
    for part in parts:
        lower = part.lower()

        if re.fullmatch(r"\d+(?:\.\d+)?", lower):
            break
        if re.fullmatch(r"\d+(?:kg|g|l|ml|buc)", lower):
            break
        if lower in stop_words:
            break

        brand_parts.append(part)

    if not brand_parts:
        return None

    return slug_to_brand_name("-".join(brand_parts))


def infer_brand_from_title(title: Optional[str]) -> Optional[str]:
    if not title:
        return None

    first_word = clean_text(title.split(" ")[0]) if title else None
    if not first_word:
        return None

    blocked = {
        "pui", "lapte", "ouă", "oua", "mere", "banane", "cartofi",
        "iaurt", "apă", "apa", "ulei", "pâine", "paine", "brânză",
        "branza", "cașcaval", "cascaval", "detergent", "scutece",
        "bețișoare", "betisoare", "buchet", "limonadă", "limonada",
        "lămâi", "lamai",
    }

    if first_word.lower() in blocked:
        return None

    if re.search(r"\d", first_word):
        return None

    return first_word


def parse_price_string(value: Optional[str]) -> Optional[float]:
    if not value:
        return None

    text = value.strip()
    text = text.replace("\xa0", " ")
    text = text.replace("RON", "")
    text = text.replace("lei", "")
    text = text.replace("LEI", "")
    text = text.strip()
    text = text.replace(",", ".")

    match = re.search(r"(\d+(?:\.\d{1,2})?)", text)
    if not match:
        return None

    try:
        return float(match.group(1))
    except ValueError:
        return None


def parse_unit_price_text(value: Optional[str]) -> tuple[Optional[float], Optional[str]]:
    if not value:
        return None, None

    text = value.strip().lower()
    text = text.replace("\xa0", " ")
    text = text.replace(",", ".")

    number_match = re.search(r"(\d+(?:\.\d{1,2})?)", text)
    if not number_match:
        return None, None

    unit = None
    if "/l" in text or "lei/l" in text:
        unit = "l"
    elif "/kg" in text or "lei/kg" in text:
        unit = "kg"
    elif "/buc" in text or "lei/buc" in text:
        unit = "buc"

    try:
        value_float = float(number_match.group(1))
    except ValueError:
        return None, None

    return value_float, unit


def extract_discount_percent(text: str) -> Optional[float]:
    if not text:
        return None

    patterns = [
        r"economisești\s*(\d+(?:[.,]\d+)?)\s*%",
        r"economisesti\s*(\d+(?:[.,]\d+)?)\s*%",
        r"reducere\s*(\d+(?:[.,]\d+)?)\s*%",
        r"discount\s*(\d+(?:[.,]\d+)?)\s*%",
        r"promo\s*(\d+(?:[.,]\d+)?)\s*%",
        r"ofert[ăa]\s*(\d+(?:[.,]\d+)?)\s*%",
        r"(?:economisești|economisesti|reducere|discount|promo|ofert[ăa]).{0,20}?-\s*(\d+(?:[.,]\d+)?)\s*%",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                value = float(match.group(1).replace(",", "."))
            except ValueError:
                continue

            if value <= 0 or value >= 100:
                continue

            return value

    return None

def extract_promo_label(text: str) -> Optional[str]:
    for pattern in [r"\b(DEALS)\b", r"\b(PROMO)\b", r"\b(OFERT[ĂA])\b"]:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return clean_text(match.group(1).upper())
    return None


def extract_deposit_value(text: str) -> Optional[float]:
    match = re.search(r"\+\s*(\d+(?:[.,]\d{1,2})?)\s*Lei", text, re.IGNORECASE)
    if not match:
        return None

    try:
        return float(match.group(1).replace(",", "."))
    except ValueError:
        return None



def infer_measure_from_package(package_text: Optional[str]) -> tuple[str, Optional[float], Optional[str]]:
    if not package_text:
        return "unknown", None, None

    text = package_text.lower().strip()

    def parse_number(raw: str, count_mode: bool = False) -> float:
        raw = raw.strip()

        if count_mode:
            if "." in raw and "," not in raw:
                raw = raw.replace(".", "")
            else:
                raw = raw.replace(".", "").replace(",", "")
            return float(raw)

        raw = raw.replace(",", ".")
        return float(raw)

    volume_match = re.search(r"(\d+(?:[.,]\d+)?)\s*(l|ml)\b", text)
    if volume_match:
        value = parse_number(volume_match.group(1))
        unit = volume_match.group(2)
        if unit == "ml":
            return "volume", round(value / 1000, 4), "l"
        return "volume", value, "l"

    weight_match = re.search(r"(\d+(?:[.,]\d+)?)\s*(kg|g)\b", text)
    if weight_match:
        value = parse_number(weight_match.group(1))
        unit = weight_match.group(2)
        if unit == "g":
            return "weight", round(value / 1000, 4), "kg"
        return "weight", value, "kg"

    count_match = re.search(r"(\d+(?:[.,]\d+)?)\s*(buc|capsule|tablete|fire)\b", text)
    if count_match:
        value = parse_number(count_match.group(1), count_mode=True)
        return "count", value, "buc"

    return "unknown", None, None


def validate_unit_price_for_measure(
    measure_type: str,
    unit_price_value: Optional[float],
    unit_price_unit: Optional[str],
) -> tuple[Optional[float], Optional[str]]:
    if unit_price_value is None or unit_price_unit is None:
        return None, None

    allowed = {
        "volume": "l",
        "weight": "kg",
        "count": "buc",
    }

    expected_unit = allowed.get(measure_type)
    if expected_unit is None:
        return unit_price_value, unit_price_unit

    if unit_price_unit != expected_unit:
        return None, None

    return unit_price_value, unit_price_unit


def derive_unit_price_from_package(
    price_total: Optional[float],
    measure_type: str,
    measure_value: Optional[float],
) -> tuple[Optional[float], Optional[str]]:
    if price_total is None or measure_value is None or measure_value == 0:
        return None, None

    if measure_type == "count":
        return round(price_total / measure_value, 4), "buc"

    if measure_type == "volume":
        return round(price_total / measure_value, 4), "l"

    if measure_type == "weight":
        return round(price_total / measure_value, 4), "kg"

    return None, None


def extract_json_ld_candidates(soup: BeautifulSoup) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []

    for script in soup.find_all("script", type="application/ld+json"):
        raw = script.string or script.get_text()
        if not raw:
            continue

        try:
            parsed = json.loads(raw)
        except Exception:
            continue

        if isinstance(parsed, list):
            for item in parsed:
                if isinstance(item, dict):
                    result.append(item)
        elif isinstance(parsed, dict):
            result.append(parsed)

    return result


def extract_brand_and_product_from_json_ld(candidates: list[dict[str, Any]]) -> dict[str, Any]:
    data: dict[str, Any] = {}

    for item in candidates:
        item_type = item.get("@type")
        if item_type in ("Product", ["Product"]):
            data["title"] = data.get("title") or clean_product_title(item.get("name"))

            image = item.get("image")
            if isinstance(image, list) and image:
                data["image_url"] = data.get("image_url") or image[0]
            elif isinstance(image, str):
                data["image_url"] = data.get("image_url") or image

            brand = item.get("brand")
            if isinstance(brand, dict):
                data["brand"] = data.get("brand") or clean_text(brand.get("name"))
            elif isinstance(brand, str):
                data["brand"] = data.get("brand") or clean_text(brand)

            offers = item.get("offers")
            if isinstance(offers, dict):
                json_ld_price = parse_price_string(str(offers.get("price")))
                if json_ld_price is not None:
                    data["json_ld_price_total"] = json_ld_price
                data["currency"] = data.get("currency") or offers.get("priceCurrency")

    return data


def extract_category_from_breadcrumbs(candidates: list[dict[str, Any]]) -> Optional[str]:
    for item in candidates:
        item_type = item.get("@type")
        if item_type in ("BreadcrumbList", ["BreadcrumbList"]):
            elements = item.get("itemListElement", [])
            names: list[str] = []

            for el in elements:
                if not isinstance(el, dict):
                    continue

                name = None
                if isinstance(el.get("item"), dict):
                    name = el.get("item", {}).get("name")
                if not name:
                    name = el.get("name")

                cleaned = clean_text(name)
                if cleaned:
                    names.append(cleaned)

            filtered = [x for x in names if x.lower() not in {"freshful", "acasă", "home"}]

            if len(filtered) >= 2:
                return filtered[-2]
            if filtered:
                return filtered[-1]

    return None


def extract_meta_content(soup: BeautifulSoup, attr_name: str, attr_value: str) -> Optional[str]:
    tag = soup.find("meta", attrs={attr_name: attr_value})
    if not tag:
        return None
    return clean_text(tag.get("content"))


def find_first_text_matching(patterns: list[str], text: str) -> Optional[str]:
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return clean_text(match.group(1))
    return None


def extract_package_text(text: str) -> Optional[str]:
    patterns = [
        r"\b(\d+(?:[.,]\d+)?\s*(?:kg|g|ml|l|buc|fire))\b",
    ]

    for pattern in patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            candidate = clean_text(match.group(1))
            if not candidate:
                continue

            lowered = candidate.lower()
            if "lei" in lowered or "ron" in lowered:
                continue

            tail = text[match.end():match.end() + 3].lower()
            if tail.startswith("ei"):
                continue

            return candidate

    return None


def extract_main_product_text(soup: BeautifulSoup) -> str:
    selectors = [
        "main",
        '[data-testid="product-details"]',
        '[data-testid="product-page"]',
        '[data-testid="product-main"]',
        '[class*="product"]',
        '[class*="Product"]',
    ]

    chunks: list[str] = []

    for selector in selectors:
        try:
            nodes = soup.select(selector)
        except Exception:
            nodes = []

        for node in nodes[:3]:
            text = clean_text(node.get_text(" ", strip=True))
            if text and len(text) > 100:
                chunks.append(text)

    if chunks:
        return max(chunks, key=len)

    return clean_text(soup.get_text(" ", strip=True)) or ""


def extract_prices_from_text(text: str) -> list[float]:
    values: list[float] = []

    for match in re.finditer(
        r"(\d+(?:[.,]\d{1,2})?)\s*Lei(?!\s*/\s*(?:l|kg|buc))",
        text,
        re.IGNORECASE,
    ):
        raw_value = match.group(1)
        try:
            value = float(raw_value.replace(",", "."))
        except ValueError:
            continue

        start = max(0, match.start() - 24)
        end = min(len(text), match.end() + 40)
        context = text[start:end].lower()

        if "+" in context:
            continue
        if re.search(r"\b\d+\s*buc\b", context):
            continue
        if re.search(r"adaugă în coș|adauga in cos", context):
            continue
        if re.search(r"cod\b", context):
            continue

        if 0.5 <= value <= 500:
            values.append(value)

    return values


def extract_primary_offer_prices(text: str) -> tuple[Optional[float], Optional[float]]:
    normalized = re.sub(r"\s+", " ", text).strip()

    patterns = [
        r"(\d+(?:[.,]\d{1,2})?)\s*Lei(?!\s*/\s*(?:l|kg|buc)).{0,80}?(?:Economisești|economisești|economisesti)\s*\d+(?:[.,]\d+)?\s*%.{0,80}?(\d+(?:[.,]\d{1,2})?)\s*Lei",
        r"(\d+(?:[.,]\d{1,2})?)\s*Lei(?!\s*/\s*(?:l|kg|buc)).{0,80}?-\s*\d+(?:[.,]\d+)?\s*%.{0,80}?(\d+(?:[.,]\d{1,2})?)\s*Lei",
    ]

    for pattern in patterns:
        match = re.search(pattern, normalized, re.IGNORECASE)
        if not match:
            continue

        first = parse_price_string(match.group(1))
        second = parse_price_string(match.group(2))

        if first is None or second is None:
            continue

        if first >= second:
            current_price = second
            old_price = first
        else:
            current_price = first
            old_price = second

        if old_price > current_price:
            return current_price, old_price

    return None, None


def choose_price_total(
    *,
    json_ld_price_total: Optional[float],
    explicit_unit_price_value: Optional[float],
    explicit_unit_price_unit: Optional[str],
    measure_type: str,
    measure_value: Optional[float],
    text: str,
) -> tuple[Optional[float], Optional[float]]:
    text_current, text_old = extract_primary_offer_prices(text)
    all_prices = sorted(set(extract_prices_from_text(text)))

    if (
        json_ld_price_total is not None
        and explicit_unit_price_value is not None
        and measure_type in {"count", "weight", "volume"}
        and measure_value
    ):
        implied_from_unit = round(explicit_unit_price_value * measure_value, 2)

        if abs(json_ld_price_total - implied_from_unit) <= 0.2:
            old_price = text_old if text_old and text_old > json_ld_price_total else None
            return json_ld_price_total, old_price

    if text_current is not None:
        old_price = text_old if text_old and text_old > text_current else None
        return text_current, old_price

    if json_ld_price_total is not None:
        old_price = text_old if text_old and text_old > json_ld_price_total else None
        return json_ld_price_total, old_price

    if all_prices:
        current = max(all_prices)
        old_candidates = [x for x in all_prices if x > current]
        old_price = min(old_candidates) if old_candidates else None
        return current, old_price

    return None, None


def parse_freshful_product_html(html: str, url: str) -> dict[str, Any]:
    soup = BeautifulSoup(html, "lxml")
    full_text = clean_text(soup.get_text(" ", strip=True)) or ""
    product_text = extract_main_product_text(soup)

    data: dict[str, Any] = {
        "url": url,
        "currency": "RON",
    }

    json_ld_candidates = extract_json_ld_candidates(soup)
    data.update({
        k: v for k, v in extract_brand_and_product_from_json_ld(json_ld_candidates).items()
        if v is not None
    })

    raw_og_title = extract_meta_content(soup, "property", "og:title")
    raw_og_image = extract_meta_content(soup, "property", "og:image")
    raw_og_description = extract_meta_content(soup, "property", "og:description")

    data["title"] = data.get("title") or clean_product_title(raw_og_title)
    data["image_url"] = data.get("image_url") or raw_og_image

    if not data.get("title") and soup.title:
        data["title"] = clean_product_title(soup.title.get_text())

    package_text = extract_package_text(product_text) or extract_package_text(full_text) or extract_package_text(data.get("title") or "")
    if package_text:
        data["package_text"] = package_text

    measure_type, measure_value, measure_unit = infer_measure_from_package(data.get("package_text"))
    data["base_measure_type"] = measure_type
    data["base_measure_value"] = measure_value
    data["base_measure_unit"] = measure_unit

    data["discount_percent"] = extract_discount_percent(product_text) or extract_discount_percent(full_text)
    data["promo_label"] = extract_promo_label(product_text) or extract_promo_label(full_text)
    data["deposit_value"] = extract_deposit_value(product_text) or extract_deposit_value(full_text)

    unit_price_candidate = (
        find_first_text_matching(
            [
                r"(\d+(?:[.,]\d{1,2})\s*lei\s*/\s*(?:l|kg|buc))",
                r"(\d+(?:[.,]\d{1,2})\s*/\s*(?:l|kg|buc))",
            ],
            product_text,
        )
        or find_first_text_matching(
            [
                r"(\d+(?:[.,]\d{1,2})\s*lei\s*/\s*(?:l|kg|buc))",
                r"(\d+(?:[.,]\d{1,2})\s*/\s*(?:l|kg|buc))",
            ],
            full_text,
        )
    )

    unit_price_value, unit_price_unit = parse_unit_price_text(unit_price_candidate)
    unit_price_value, unit_price_unit = validate_unit_price_for_measure(
        measure_type=measure_type,
        unit_price_value=unit_price_value,
        unit_price_unit=unit_price_unit,
    )

    price_total, old_price = choose_price_total(
        json_ld_price_total=data.get("json_ld_price_total"),
        explicit_unit_price_value=unit_price_value,
        explicit_unit_price_unit=unit_price_unit,
        measure_type=measure_type,
        measure_value=measure_value,
        text=product_text or full_text,
    )

    if price_total is None:
        price_candidate = find_first_text_matching(
            [
                r"(\d+(?:[.,]\d{1,2})\s*lei(?!\s*/\s*(?:l|kg|buc)))",
                r"(\d+(?:[.,]\d{1,2})\s*RON)",
            ],
            product_text or full_text,
        )
        price_total = parse_price_string(price_candidate)

    if unit_price_value is None and measure_value is not None and measure_value > 0 and price_total is not None:
        unit_price_value, unit_price_unit = derive_unit_price_from_package(
            price_total=price_total,
            measure_type=measure_type,
            measure_value=measure_value,
        )

    json_ld_price_total = data.get("json_ld_price_total")
    data["price_total"] = price_total
    data["old_price"] = old_price
    data["unit_price_value"] = unit_price_value
    data["unit_price_unit"] = unit_price_unit

    if (
        data["price_total"] is not None
        and data["unit_price_value"] is not None
        and measure_type in {"count", "weight", "volume"}
        and measure_value
    ):
        implied_total = round(data["unit_price_value"] * measure_value, 2)

        # Dacă prețul extras și totalul derivat din prețul unitar sunt foarte apropiate,
        # păstrăm prețul extras din PDP (de ex. 22.99 în loc de 23.00).
        if abs(data["price_total"] - implied_total) <= 0.2:
            pass
        elif json_ld_price_total is not None and abs(json_ld_price_total - implied_total) <= 0.2:
            data["price_total"] = json_ld_price_total
        else:
            data["price_total"] = implied_total

    breadcrumb_category = extract_category_from_breadcrumbs(json_ld_candidates)
    data["category"] = data.get("category") or breadcrumb_category

    if not data.get("brand"):
        brand_from_description = find_first_text_matching(
            [r"brand[:\s]+([A-Za-zĂÂÎȘȚăâîșț0-9\-\& ]{2,50})"],
            raw_og_description or "",
        )
        data["brand"] = (
            brand_from_description
            or extract_brand_from_url(url)
            or infer_brand_from_title(data.get("title"))
        )

    data["external_id"] = None
    availability_from_product_text = detect_availability(product_text)
    availability_from_full_text = detect_availability(full_text)
    availability_from_html = detect_availability(html)

    if availability_from_product_text == "out_of_stock":
        data["availability"] = "out_of_stock"
    elif availability_from_product_text == "in_stock":
        data["availability"] = "in_stock"
    elif availability_from_full_text == "out_of_stock":
        data["availability"] = "out_of_stock"
    elif availability_from_html == "out_of_stock":
        data["availability"] = "out_of_stock"
    elif availability_from_full_text == "in_stock":
        data["availability"] = "in_stock"
    elif availability_from_html == "in_stock":
        data["availability"] = "in_stock"
    elif (
        data.get("price_total") is not None
        and data.get("unit_price_value") is not None
    ):
        data["availability"] = "in_stock"
    else:
        data["availability"] = "unknown"
    if not data.get("title"):
        raise ValueError("Nu am putut extrage titlul produsului din HTML.")


    bundle_count = detect_bundle_count(product_text or full_text or html)
    bundle_discount_percent = detect_bundle_discount_percent(product_text or full_text or html)

    if bundle_count is not None and bundle_count > 1:
        data["promo_kind"] = "bundle"

        if not data.get("promo_label"):
            data["promo_label"] = "OFERTĂ"

        if data.get("discount_percent") is None and bundle_discount_percent is not None:
            data["discount_percent"] = bundle_discount_percent
    if data.get("price_total") is None:
        raise ValueError("Nu am putut extrage prețul produsului din HTML.")

    return data


def debug_freshful_product_html(html: str, url: str) -> dict[str, Any]:
    soup = BeautifulSoup(html, "lxml")
    full_text = clean_text(soup.get_text(" ", strip=True)) or ""
    product_text = extract_main_product_text(soup)

    json_ld_candidates = extract_json_ld_candidates(soup)
    parsed = parse_freshful_product_html(html, url)

    return {
        "url": url,
        "page_title": clean_text(soup.title.get_text()) if soup.title else None,
        "page_title_clean": clean_product_title(soup.title.get_text()) if soup.title else None,
        "og_title": extract_meta_content(soup, "property", "og:title"),
        "og_title_clean": clean_product_title(extract_meta_content(soup, "property", "og:title")),
        "og_image": extract_meta_content(soup, "property", "og:image"),
        "og_description": extract_meta_content(soup, "property", "og:description"),
        "json_ld_count": len(json_ld_candidates),
        "json_ld_types": [item.get("@type") for item in json_ld_candidates if isinstance(item, dict)],
        "breadcrumb_category": extract_category_from_breadcrumbs(json_ld_candidates),
        "product_text_preview": product_text[:1200],
        "detected_promo_label": extract_promo_label(product_text) or extract_promo_label(full_text),
        "detected_discount_percent": extract_discount_percent(product_text) or extract_discount_percent(full_text),
        "detected_deposit_value": extract_deposit_value(product_text) or extract_deposit_value(full_text),
        "brand_from_url": extract_brand_from_url(url),
        "text_price_match": find_first_text_matching(
            [
                r"(\d+(?:[.,]\d{1,2})\s*lei(?!\s*/\s*(?:l|kg|buc)))",
                r"(\d+(?:[.,]\d{1,2})\s*RON)",
            ],
            product_text or full_text,
        ),
        "text_unit_price_match": find_first_text_matching(
            [
                r"(\d+(?:[.,]\d{1,2})\s*lei\s*/\s*(?:l|kg|buc))",
                r"(\d+(?:[.,]\d{1,2})\s*/\s*(?:l|kg|buc))",
            ],
            product_text or full_text,
        ),
        "text_package_match": extract_package_text(product_text) or extract_package_text(full_text),
        "parsed": parsed,
    }










