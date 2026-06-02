"""
Guitar Center used/vintage scraper.
GC has a massive used inventory distributed across stores nationwide.
Uses their search page which renders product data in structured HTML.
"""

import re
import requests
from bs4 import BeautifulSoup
from config import PRICE_MIN, PRICE_MAX

BASE_URL = "https://www.guitarcenter.com"

SEARCH_URLS = [
    f"{BASE_URL}/Used/Gibson/J-45-Acoustic-Guitars.gc?N=4294819439+4294819441&Nrpp=48",
    f"{BASE_URL}/Used/Gibson/J-50-Acoustic-Guitars.gc?N=4294819439+4294819441&Nrpp=48",
    f"{BASE_URL}/Vintage/Gibson/Acoustic-Guitars.gc?Nrpp=48",
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

    for url in SEARCH_URLS:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=20)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            # GC product cards
            cards = (
                soup.select(".product-grid-item, .product-card, [class*='product-tile']") or
                soup.select("li[data-product-id], [data-sku], [class*='product-item']")
            )

            for card in cards:
                title_el = card.select_one(
                    "h2, h3, .product-title, [class*='product-name'], [class*='title']"
                )
                price_el = card.select_one(
                    ".price, [class*='price'], .sale-price, [class*='sale']"
                )
                link_el  = card.select_one("a[href]")

                title = title_el.get_text(strip=True) if title_el else ""
                price = _parse_price(price_el.get_text(strip=True) if price_el else "")
                href  = link_el["href"] if link_el else ""
                full_url = href if href.startswith("http") else BASE_URL + href

                if not title or len(title) < 5:
                    continue
                if price and not (PRICE_MIN <= price <= PRICE_MAX):
                    continue

                results.append({
                    "source":      "Guitar Center",
                    "id":          f"gc_{_slug(full_url)}",
                    "title":       title,
                    "price":       price,
                    "url":         full_url,
                    "description": card.get_text(separator=" ", strip=True)[:400],
                    "image_url":   _get_image(card),
                })

        except Exception as e:
            print(f"[Guitar Center] Error: {e}")

    # Dedupe
    seen, deduped = set(), []
    for r in results:
        if r["id"] not in seen:
            seen.add(r["id"])
            deduped.append(r)

    print(f"[Guitar Center] Found {len(deduped)} listings")
    return deduped


def _get_image(card) -> str:
    img = card.select_one("img[src], img[data-src], img[data-lazy]")
    if not img:
        return ""
    return img.get("src") or img.get("data-src") or img.get("data-lazy") or ""


def _parse_price(text: str) -> float | None:
    match = re.search(r"[\d,]+\.?\d*", text.replace("$", "").replace(",", ""))
    if match:
        try:
            v = float(match.group().replace(",", ""))
            if 100 < v < 100000:
                return v
        except ValueError:
            pass
    return None


def _slug(url: str) -> str:
    return re.sub(r"[^a-z0-9]", "_", url.lower())[-60:]
