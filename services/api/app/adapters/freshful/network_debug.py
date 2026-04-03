from playwright.sync_api import sync_playwright

CDP_URL = "http://127.0.0.1:9222"


def debug_freshful_network(url: str) -> dict:
    captured = []

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(CDP_URL)

        if not browser.contexts:
            raise ValueError("Nu există contexte Chrome disponibile prin CDP.")

        context = browser.contexts[0]
        page = context.new_page()

        def handle_response(response):
            req_url = ""
            try:
                req_url = response.url
                content_type = response.headers.get("content-type", "")

                interesting = (
                    "json" in content_type.lower()
                    or "graphql" in req_url.lower()
                    or "api" in req_url.lower()
                    or "product" in req_url.lower()
                    or "price" in req_url.lower()
                    or "promotion" in req_url.lower()
                    or "promo" in req_url.lower()
                )

                if not interesting:
                    return

                body_preview = ""
                read_error = None

                try:
                    if "json" in content_type.lower() or "text" in content_type.lower():
                        body_preview = response.text()[:3000]
                    else:
                        body_preview = "<non-text response>"
                except Exception as exc:
                    read_error = f"{type(exc).__name__}: {exc!r}"
                    body_preview = "<unreadable>"

                captured.append(
                    {
                        "url": req_url,
                        "status": response.status,
                        "content_type": content_type,
                        "body_preview": body_preview,
                        "read_error": read_error,
                    }
                )
            except Exception as exc:
                captured.append(
                    {
                        "url": req_url or "<unknown>",
                        "status": None,
                        "content_type": "",
                        "body_preview": "",
                        "read_error": f"{type(exc).__name__}: {exc!r}",
                    }
                )

        page.on("response", handle_response)

        page.goto(url, wait_until="domcontentloaded", timeout=45000)
        page.wait_for_timeout(6000)

        try:
            body_text = page.locator("body").inner_text(timeout=4000)
        except Exception:
            body_text = ""

        try:
            page.close()
        except Exception:
            pass

        try:
            browser.close()
        except Exception:
            pass

    return {
        "page_url": url,
        "cdp_url": CDP_URL,
        "body_preview": body_text[:4000],
        "responses": captured[:80],
    }