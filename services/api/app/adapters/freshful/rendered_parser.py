import asyncio
import re
import sys
from typing import Optional

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

from app.adapters.freshful.parser import (
    clean_product_title,
    clean_text,
    extract_brand_from_url,
    infer_brand_from_title,
    infer_measure_from_package,
)

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

CDP_URL = "http://127.0.0.1:9222"


def parse_money_to_float(value: Optional[str]) -> Optional[float]:
    if not value:
        return None

    text = value.strip().replace("\xa0", " ").replace(",", ".")
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

    text = value.strip().lower().replace("\xa0", " ").replace(",", ".")
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


def extract_package_from_title(title: Optional[str]) -> Optional[str]:
    if not title:
        return None

    match = re.search(r"(\d+(?:[.,]\d+)?\s*(?:kg|g|ml|l|buc|fire))\b", title, re.IGNORECASE)
    if not match:
        return None

    return clean_text(match.group(1))


def detect_discount_percent(text: str) -> Optional[float]:
    if not text:
        return None

    patterns = [
        r"Economisești\s*(\d+(?:[.,]\d+)?)\s*%",
        r"economisesti\s*(\d+(?:[.,]\d+)?)\s*%",
        r"-\s*(\d+(?:[.,]\d+)?)\s*%",
        r"(\d+(?:[.,]\d+)?)\s*%",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1).replace(",", "."))
            except ValueError:
                continue

    return None


def detect_promo_label(text: str) -> Optional[str]:
    if not text:
        return None

    lowered = text.lower()

    if "economisești" in lowered or "economisesti" in lowered:
        return "DEALS"

    if re.search(r"\bDEALS\b", text, re.IGNORECASE):
        return "DEALS"
    if re.search(r"\bPROMO\b", text, re.IGNORECASE):
        return "PROMO"
    if re.search(r"\bOFERT[ĂA]\b", text, re.IGNORECASE):
        return "OFERTĂ"

    return None


def detect_deposit_value(text: str) -> Optional[float]:
    match = re.search(r"\+\s*(\d+(?:[.,]\d{1,2})?)\s*Lei", text, re.IGNORECASE)
    if not match:
        return None
    return parse_money_to_float(match.group(1))


def extract_main_title(page) -> Optional[str]:
    for selector in [
        "h1",
        '[data-testid="product-title"]',
        '[data-testid="product-name"]',
    ]:
        try:
            locator = page.locator(selector).first
            if locator.count() > 0:
                text = clean_text(locator.inner_text(timeout=1500))
                if text:
                    return text
        except Exception:
            continue
    return None


def extract_brand(page, title: Optional[str], url: str) -> Optional[str]:
    candidates: list[str] = []

    for selector in [
        '[data-testid="product-brand"]',
        'a[href*="/brand/"]',
        '[class*="brand"]',
        '[class*="Brand"]',
    ]:
        try:
            locator = page.locator(selector)
            count = locator.count()
            for i in range(min(count, 8)):
                try:
                    text = clean_text(locator.nth(i).inner_text(timeout=800))
                    if text and len(text) <= 80:
                        candidates.append(text)
                except Exception:
                    continue
        except Exception:
            continue

    for candidate in candidates:
        if title and candidate.lower() in title.lower():
            return candidate

    return extract_brand_from_url(url) or infer_brand_from_title(title)


def extract_main_image_url(page) -> Optional[str]:
    for selector in [
        'main img[src*="freshful"]',
        'img[src*="sylius_shop_product_thumbnail"]',
        "main img",
    ]:
        try:
            locator = page.locator(selector)
            count = locator.count()
            for i in range(min(count, 10)):
                try:
                    src = locator.nth(i).get_attribute("src", timeout=1000)
                    if not src:
                        continue

                    if src.startswith("/_next/image?url="):
                        match = re.search(r"url=([^&]+)", src)
                        if match:
                            from urllib.parse import unquote
                            return unquote(match.group(1))

                    if "cdn.freshful.ro" in src:
                        return src
                except Exception:
                    continue
        except Exception:
            continue

    return None


def extract_main_product_block(page) -> dict:
    js = """
    () => {
      function cleanText(s) {
        return (s || "").replace(/\\s+/g, " ").trim();
      }

      const h1 = document.querySelector("h1");
      if (!h1) {
        return { block_text: cleanText(document.body.innerText).slice(0, 8000), block_html: "", block_level: "body" };
      }

      let current = h1;
      for (let i = 0; i < 8; i++) {
        if (!current) break;

        const text = cleanText(current.innerText || current.textContent || "");
        if (
          text &&
          /Lei|Adaugă în coș|Adauga in cos|Economisești|economisesti|%/i.test(text) &&
          text.length < 12000
        ) {
          return {
            block_text: text,
            block_html: (current.outerHTML || "").slice(0, 20000),
            block_level: `${current.tagName} ${current.className || ""}`.trim(),
          };
        }

        current = current.parentElement;
      }

      return {
        block_text: cleanText(document.body.innerText).slice(0, 8000),
        block_html: "",
        block_level: "body",
      };
    }
    """

    try:
        return page.evaluate(js)
    except Exception:
        body_text = clean_text(page.locator("body").inner_text(timeout=4000)) or ""
        return {
            "block_text": body_text[:8000],
            "block_html": "",
            "block_level": "body",
        }


def extract_money_candidates(text: str) -> list[float]:
    values: list[float] = []

    for match in re.finditer(r"(\d+(?:[.,]\d{1,2})?)\s*Lei(?!\s*/\s*(?:l|kg|buc))", text, re.IGNORECASE):
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
        if 0.5 <= value <= 500:
            values.append(value)

    return values


def pick_best_price_pair(
    candidates: list[float],
    discount_percent: Optional[float],
) -> tuple[Optional[float], Optional[float]]:
    if not candidates:
        return None, None

    unique_sorted = sorted(set(candidates))

    if len(unique_sorted) == 1:
        return unique_sorted[0], None

    if discount_percent is not None and 0 < discount_percent < 100:
        best_pair = None
        best_error = float("inf")

        for current in unique_sorted:
            for old in unique_sorted:
                if old <= current:
                    continue

                implied = (1 - current / old) * 100
                error = abs(implied - discount_percent)

                if error < best_error:
                    best_error = error
                    best_pair = (current, old)

        if best_pair and best_error <= 8:
            return best_pair

    return unique_sorted[0], unique_sorted[1]


def detect_unit_price(text: str) -> tuple[Optional[float], Optional[str]]:
    matches = re.findall(r"(\d+(?:[.,]\d{1,2})?\s*Lei\s*/\s*(?:l|kg|buc))", text, re.IGNORECASE)
    if not matches:
        return None, None

    parsed_values: list[tuple[float, str]] = []
    for item in matches:
        value, unit = parse_unit_price_text(item)
        if value is not None and unit is not None:
            parsed_values.append((value, unit))

    if not parsed_values:
        return None, None

    parsed_values.sort(key=lambda x: x[0])
    return parsed_values[0]


def choose_rendered_price_total(
    *,
    unit_price_value: Optional[float],
    measure_type: str,
    measure_value: Optional[float],
    candidates: list[float],
    discount_percent: Optional[float],
) -> tuple[Optional[float], Optional[float]]:
    current, old = pick_best_price_pair(candidates, discount_percent)

    if (
        unit_price_value is not None
        and measure_type in {"count", "weight", "volume"}
        and measure_value
        and candidates
    ):
        implied_total = round(unit_price_value * measure_value, 2)
        nearest = min(candidates, key=lambda x: abs(x - implied_total))
        if abs(nearest - implied_total) <= 0.25:
            old_price = old if old and old > nearest else None
            return nearest, old_price

    return current, old


def detect_rendered_price_block(page) -> dict:
    body_text = clean_text(page.locator("body").inner_text(timeout=4000)) or ""
    nearby = extract_main_product_block(page)

    target_text = nearby["block_text"] or body_text

    title = extract_main_title(page)
    brand = extract_brand(page, title=title, url=page.url)
    image_url = extract_main_image_url(page)

    package_text = extract_package_from_title(title)
    measure_type, measure_value, measure_unit = infer_measure_from_package(package_text)

    discount_percent = detect_discount_percent(target_text) or detect_discount_percent(body_text)
    promo_label = detect_promo_label(target_text) or detect_promo_label(body_text)
    deposit_value = detect_deposit_value(target_text) or detect_deposit_value(body_text)

    unit_price_value, unit_price_unit = detect_unit_price(target_text)
    if unit_price_value is None:
        unit_price_value, unit_price_unit = detect_unit_price(body_text)

    money_candidates = extract_money_candidates(target_text)
    if not money_candidates:
        money_candidates = extract_money_candidates(body_text)

    price_total, old_price = choose_rendered_price_total(
        unit_price_value=unit_price_value,
        measure_type=measure_type,
        measure_value=measure_value,
        candidates=money_candidates,
        discount_percent=discount_percent,
    )

    return {
        "title": title,
        "brand": brand,
        "image_url": image_url,
        "package_text": package_text,
        "price_total": price_total,
        "old_price": old_price,
        "promo_label": promo_label,
        "discount_percent": discount_percent,
        "deposit_value": deposit_value,
        "unit_price_value": unit_price_value,
        "unit_price_unit": unit_price_unit,
        "base_measure_type": measure_type,
        "base_measure_value": measure_value,
        "base_measure_unit": measure_unit,
        "money_candidates": money_candidates[:50],
        "target_text": target_text[:5000],
        "body_text": body_text[:5000],
        "block_level": nearby["block_level"],
        "block_html": nearby["block_html"],
        "cdp_url": CDP_URL,
    }


def parse_freshful_product_rendered(url: str) -> dict:
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(CDP_URL)

        if not browser.contexts:
            raise ValueError("Nu există contexte Chrome disponibile prin CDP.")

        context = browser.contexts[0]
        page = context.new_page()

        try:
            page.goto(url, wait_until="domcontentloaded", timeout=45000)
            page.wait_for_timeout(5000)

            try:
                page.locator("h1").first.wait_for(timeout=5000)
            except Exception:
                pass

            rendered = detect_rendered_price_block(page)
        except PlaywrightTimeoutError as exc:
            raise ValueError(f"Rendered parser timeout for Freshful page: {exc}") from exc
        finally:
            try:
                page.close()
            except Exception:
                pass

    title = clean_product_title(rendered.get("title"))
    brand = clean_text(rendered.get("brand")) or extract_brand_from_url(url) or infer_brand_from_title(title)
    image_url = rendered.get("image_url")

    package_text = rendered.get("package_text") or extract_package_from_title(title)
    measure_type, measure_value, measure_unit = infer_measure_from_package(package_text)

    price_total = rendered.get("price_total")
    old_price = rendered.get("old_price")
    discount_percent = rendered.get("discount_percent")
    promo_label = rendered.get("promo_label")
    deposit_value = rendered.get("deposit_value")
    unit_price_value = rendered.get("unit_price_value")
    unit_price_unit = rendered.get("unit_price_unit")

    if (
        unit_price_value is None
        and price_total is not None
        and measure_value is not None
        and measure_value > 0
    ):
        unit_price_value = round(price_total / measure_value, 4)
        if measure_type == "volume":
            unit_price_unit = "l"
        elif measure_type == "weight":
            unit_price_unit = "kg"
        elif measure_type == "count":
            unit_price_unit = "buc"

    data = {
        "url": url,
        "currency": "RON",
        "title": title,
        "brand": brand,
        "image_url": image_url,
        "category": None,
        "package_text": package_text,
        "price_total": price_total,
        "old_price": old_price,
        "promo_label": promo_label,
        "discount_percent": discount_percent,
        "deposit_value": deposit_value,
        "unit_price_value": unit_price_value,
        "unit_price_unit": unit_price_unit,
        "base_measure_type": measure_type,
        "base_measure_value": measure_value,
        "base_measure_unit": measure_unit,
        "external_id": None,
        "availability": "unknown",
        "_rendered_debug": rendered,
        "_using_cdp": True,
        "_cdp_url": CDP_URL,
    }

    if not data["title"]:
        raise ValueError("Rendered parser: nu am putut extrage titlul produsului.")

    if data["price_total"] is None:
        raise ValueError("Rendered parser: nu am putut extrage prețul curent al produsului.")

    return data
