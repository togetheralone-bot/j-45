"""
Facebook Marketplace scraper — uses Playwright (headless browser).
FB has no API and blocks plain HTTP requests, so we drive a real browser.

IMPORTANT: This requires you to save your FB session cookies once (see README).
Without a logged-in session, FB shows a login wall and returns nothing.

Setup (one time):
    pip install playwright
    playwright install chromium
    python scrapers/fb_setup.py   ← logs you in and saves session to fb_session.json
"""

import json
import os
import re
from pathlib import Path
from config import PRICE_MIN, PRICE_MAX

SESSION_FILE = Path(__file__).parent.parent / "data" / "fb_session.json"

# Each entry: (city_label, marketplace_search_url)
# Location radius is set to ~100 miles in the URL (radiusKm=160)
CITIES = [
    ("Austin, TX",       "https://www.facebook.com/marketplace/austin/search?query=gibson+j-45&minPrice={min}&maxPrice={max}&radiusKm=100"),
    ("Houston, TX",      "https://www.facebook.com/marketplace/houston/search?query=gibson+j-45&minPrice={min}&maxPrice={max}&radiusKm=100"),
    ("San Antonio, TX",  "https://www.facebook.com/marketplace/san-antonio/search?query=gibson+j-45&minPrice={min}&maxPrice={max}&radiusKm=100"),
    ("Dallas, TX",       "https://www.facebook.com/marketplace/dallas/search?query=gibson+j-45&minPrice={min}&maxPrice={max}&radiusKm=100"),
    ("El Paso, TX",      "https://www.facebook.com/marketplace/el-paso/search?query=gibson+j-45&minPrice={min}&maxPrice={max}&radiusKm=100"),
    ("Oklahoma City, OK","https://www.facebook.com/marketplace/oklahoma-city/search?query=gibson+j-45&minPrice={min}&maxPrice={max}&radiusKm=100"),
]

EXTRA_QUERIES = [
    # Gibson (original)
    "gibson+j-50", "gibson+country+western+guitar",
    # Fender
    "fender+jazzmaster+vintage", "fender+jaguar+vintage", "fender+stratocaster+vintage",
]


def fetch() -> list[dict]:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("[Facebook] Playwright not installed — skipping. Run: pip install playwright && playwright install chromium")
        return []

    if not SESSION_FILE.exists():
        print("[Facebook] No session file found — skipping. Run: python scrapers/fb_setup.py")
        return []

    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            storage_state=str(SESSION_FILE),
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 800},
        )
        page = context.new_page()

        all_searches = []
        for city_label, url_template in CITIES:
            # Primary query (j-45) baked into URL template
            all_searches.append((city_label, url_template.format(min=PRICE_MIN, max=PRICE_MAX)))
            # Extra queries for the same city
            for extra_q in EXTRA_QUERIES:
                extra_url = url_template.replace("gibson+j-45", extra_q).format(min=PRICE_MIN, max=PRICE_MAX)
                all_searches.append((city_label, extra_url))

        for city_label, url in all_searches:
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(3000)  # Let JS render listings

                # Check for login wall
                if "log in" in page.title().lower() or page.url.startswith("https://www.facebook.com/login"):
                    print(f"[Facebook] Session expired for {city_label} — re-run fb_setup.py")
                    break

                # Scrape listing cards
                cards = page.query_selector_all('[data-testid="marketplace_feed_item"], [class*="x1i10hfl"]')

                # Fallback: any link containing /marketplace/item/
                if not cards:
                    cards = page.query_selector_all('a[href*="/marketplace/item/"]')

                for card in cards:
                    try:
                        text  = card.inner_text().strip()
                        href  = card.get_attribute("href") or ""
                        url_  = f"https://www.facebook.com{href}" if href.startswith("/") else href

                        if not text or "/marketplace/item/" not in url_:
                            continue

                        price = _extract_price(text)
                        if price and not (PRICE_MIN <= price <= PRICE_MAX):
                            continue

                        # Grab the first line as title, rest as description
                        lines = [l.strip() for l in text.splitlines() if l.strip()]
                        title = lines[0] if lines else text[:80]
                        desc  = " ".join(lines[1:])[:400]

                        results.append({
                            "source":      f"Facebook Marketplace ({city_label})",
                            "id":          f"fb_{_slug(url_)}",
                            "title":       title,
                            "price":       price,
                            "url":         url_,
                            "description": desc,
                        })
                    except Exception:
                        pass

            except Exception as e:
                print(f"[Facebook] Error scraping {city_label}: {e}")

        context.close()
        browser.close()

    # Dedupe by ID within this scraper
    seen, deduped = set(), []
    for r in results:
        if r["id"] not in seen:
            seen.add(r["id"])
            deduped.append(r)

    print(f"[Facebook] Found {len(deduped)} listings across {len(CITIES)} cities")
    return deduped


def _extract_price(text: str) -> float | None:
    match = re.search(r"\$\s?([\d,]+)", text)
    if match:
        try:
            return float(match.group(1).replace(",", ""))
        except ValueError:
            pass
    return None


def _slug(url: str) -> str:
    return re.sub(r"[^a-z0-9]", "_", url.lower())[-60:]
