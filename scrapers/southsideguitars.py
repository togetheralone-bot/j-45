"""
Southside Guitars scraper.
URL: https://southsideguitars.com/products/Acoustic-Guitars-c147989494
Ecwid-based store — product data is rendered in the HTML.
"""

import re
import requests
from bs4 import BeautifulSoup
from config import PRICE_MIN, PRICE_MAX, TARGET_MODELS, YEAR_MIN, YEAR_MAX

BASE_URL = "https://southsideguitars.com"
CATEGORY_URL = f"{BASE_URL}/products/Acoustic-Guitars-c147989494"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def fetch() -> list[dict]:
    results = []

    try:
        resp = requests.get(CATEGORY_URL, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Ecwid product links follow the pattern /products/<slug>-p<id>
        product_links = soup.select("a[href*='/products/'][href*='-p']")

        seen_urls = set()
        for link in product_links:
            href = link.get("href", "")
            if not href or href in seen_urls:
                continue
            # Skip category links (no -p<digits> suffix)
            if not re.search(r"-p\d+", href):
                continue
            seen_urls.add(href)

            full_url = href if href.startswith("http") else BASE_URL + href
            title = link.get_text(strip=True)

            # Dedupe duplicate anchor text on same card
            if not title or len(title) < 5:
                continue

            title_lower = title.lower()

            # Must match one of our target models
            if not any(m.lower() in title_lower for m in TARGET_MODELS):
                continue

            # Must fall within our year range
            year = _extract_year(title)
            if year and not (YEAR_MIN <= year <= YEAR_MAX):
                continue

            # Grab price from sibling text in the card
            price = _extract_price_near(link, soup)

            if price and not (PRICE_MIN <= price <= PRICE_MAX):
                continue

            results.append({
                "source":      "Southside Guitars",
                "id":          f"southside_{_slug(full_url)}",
                "title":       title,
                "price":       price,
                "url":         full_url,
                "description": "",
            })

    except Exception as e:
        print(f"[Southside Guitars] Error: {e}")

    print(f"[Southside Guitars] Found {len(results)} listings")
    return results


def _extract_price_near(link_el, soup) -> float | None:
    """Walk up to the card container and find a price string."""
    node = link_el
    for _ in range(5):
        if node.parent:
            node = node.parent
        text = node.get_text(separator=" ", strip=True)
        match = re.search(r"\$\s?([\d,]+(?:\.\d{2})?)", text)
        if match:
            try:
                return float(match.group(1).replace(",", ""))
            except ValueError:
                pass
    return None


def _extract_year(text: str) -> int | None:
    match = re.search(r"\b(1[89]\d{2})\b", text)
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            pass
    return None


def _slug(url: str) -> str:
    return re.sub(r"[^a-z0-9]", "_", url.lower())[-60:]
