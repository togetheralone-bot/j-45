"""
Bernunzio Uptown Music scraper.
bernunzio.com — custom WordPress/WooCommerce site.
Also lists on Reverb (already covered), but direct scrape catches
anything listed only on their own site.
"""

import re
import requests
from bs4 import BeautifulSoup
from config import PRICE_MIN, PRICE_MAX

BASE_URL = "https://bernunzio.com"

SEARCH_URLS = [
    f"{BASE_URL}/?s=gibson+j-45&post_type=product",
    f"{BASE_URL}/?s=gibson+j-50&post_type=product",
    f"{BASE_URL}/?s=gibson+country+western&post_type=product",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def fetch() -> list[dict]:
    results = []

    for url in SEARCH_URLS:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=20)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            # WooCommerce product grid
            cards = soup.select(
                ".product, li.type-product, .product-card, "
                "[class*='product-item'], article.product"
            )

            for card in cards:
                title_el = card.select_one(
                    "h2, h3, .woocommerce-loop-product__title, .product-title"
                )
                price_el = card.select_one(
                    ".price, .amount, ins .amount, [class*='price']"
                )
                link_el  = card.select_one("a[href]")
                img_el   = card.select_one("img[src]")

                title    = title_el.get_text(strip=True) if title_el else ""
                price    = _parse_price(price_el.get_text(strip=True) if price_el else "")
                href     = link_el["href"] if link_el else ""
                img_url  = img_el["src"] if img_el else ""

                if not title or len(title) < 5:
                    continue
                if price and not (PRICE_MIN <= price <= PRICE_MAX):
                    continue

                results.append({
                    "source":      "Bernunzio Uptown Music",
                    "id":          f"bernunzio_{_slug(href)}",
                    "title":       title,
                    "price":       price,
                    "url":         href,
                    "description": card.get_text(separator=" ", strip=True)[:400],
                    "image_url":   img_url,
                })

        except Exception as e:
            print(f"[Bernunzio] Error: {e}")

    print(f"[Bernunzio] Found {len(results)} listings")
    return results


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
