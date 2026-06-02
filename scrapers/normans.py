"""
Norman's Rare Guitars — TWO systems running simultaneously:

1. normansrareguitars.com/products/ — Shopify (already in dealers.py)
2. normansrareguitars.com/shop/     — Custom Next.js platform (same as Carter Vintage)
   This scraper handles the /shop/ side which contains vintage inventory.
"""

import re
import requests
from bs4 import BeautifulSoup
from config import PRICE_MIN, PRICE_MAX

BASE_URL = "https://normansrareguitars.com"

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

            for a in soup.select("a[href*='/shop/']"):
                href = a.get("href", "")
                if not re.search(r"/shop/[^/]+/\w{20,}", href):
                    continue

                full_url = href if href.startswith("http") else BASE_URL + href
                if full_url in seen:
                    continue
                seen.add(full_url)

                text  = a.get_text(separator=" ", strip=True)
                price = _extract_price(text)
                title = re.sub(r"\$[\d,]+\.?\d*", "", text).strip()

                if not title:
                    continue
                if price and not (PRICE_MIN <= price <= PRICE_MAX):
                    continue

                img     = a.select_one("img[src]")
                img_url = img["src"] if img else ""

                results.append({
                    "source":      "Norman's Rare Guitars",
                    "id":          f"normans_shop_{_slug(full_url)}",
                    "title":       title,
                    "price":       price,
                    "url":         full_url,
                    "description": text,
                    "image_url":   img_url,
                })

        except Exception as e:
            print(f"[Norman's /shop/] Error on '{url}': {e}")

    print(f"[Norman's Rare Guitars /shop/] Found {len(results)} listings")
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
