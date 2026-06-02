"""
Carter Vintage scraper — custom Next.js/Vercel site.
NOT Shopify — uses a proprietary backend at backend.cartervintage.com.

The shop page renders listings server-side as linked items in the HTML.
We scrape the acoustic guitars category pages and filter locally.
"""

import re
import requests
from bs4 import BeautifulSoup
from config import PRICE_MIN, PRICE_MAX

BASE_URL = "https://cartervintage.com"

# Their acoustic category — sorted newest first so we catch new arrivals
PAGES = [
    f"{BASE_URL}/shop?sort=LISTING_TIME_DESC",
    f"{BASE_URL}/shop?sort=LISTING_TIME_DESC&page=2",
    f"{BASE_URL}/shop?sort=LISTING_TIME_DESC&page=3",
    f"{BASE_URL}/shop?sort=LISTING_TIME_DESC&page=4",
    f"{BASE_URL}/shop?sort=LISTING_TIME_DESC&page=5",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def fetch() -> list[dict]:
    results = []
    seen = set()

    for url in PAGES:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=20)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            # Each listing is an <a> tag linking to /shop/{slug}/{id}
            # with an image thumbnail and the title+price as text
            for a in soup.select("a[href*='/shop/']"):
                href = a.get("href", "")
                # Filter out nav/menu links — product links have the ID hash at the end
                if not re.search(r"/shop/[^/]+/\w{20,}", href):
                    continue

                full_url = href if href.startswith("http") else BASE_URL + href
                if full_url in seen:
                    continue
                seen.add(full_url)

                # Text content is "Title $Price"
                text  = a.get_text(separator=" ", strip=True)
                price = _extract_price(text)
                title = re.sub(r"\$[\d,]+\.?\d*", "", text).strip()

                if not title:
                    continue
                if price and not (PRICE_MIN <= price <= PRICE_MAX):
                    continue

                # Image is in a child <img> tag
                img   = a.select_one("img[src]")
                img_url = img["src"] if img else ""

                results.append({
                    "source":      "Carter Vintage",
                    "id":          f"carter_{_slug(full_url)}",
                    "title":       title,
                    "price":       price,
                    "url":         full_url,
                    "description": text,
                    "image_url":   img_url,
                })

        except Exception as e:
            print(f"[Carter Vintage] Error on '{url}': {e}")

    print(f"[Carter Vintage] Found {len(results)} listings")
    return results


def _extract_price(text: str) -> float | None:
    match = re.search(r"\$([\d,]+\.?\d*)", text)
    if match:
        try:
            v = float(match.group(1).replace(",", ""))
            if 100 < v < 100000:
                return v
        except ValueError:
            pass
    return None


def _slug(url: str) -> str:
    return re.sub(r"[^a-z0-9]", "_", url.lower())[-60:]
