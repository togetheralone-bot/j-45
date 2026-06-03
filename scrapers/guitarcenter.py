"""
Guitar Center used/vintage scraper.
Scrapes their used Gibson acoustic category pages directly.
Also handles Musician's Friend (same parent company, separate inventory).
"""

import re
import requests
from bs4 import BeautifulSoup
from config import PRICE_MIN, PRICE_MAX

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.guitarcenter.com/",
}

PAGES = [
    # Gibson (original)
    "https://www.guitarcenter.com/Used/Gibson/Acoustic-Guitars.gc",
    "https://www.guitarcenter.com/Vintage/Gibson/Acoustic-Guitars.gc",
    # Fender
    "https://www.guitarcenter.com/Used/Fender/Electric-Guitars.gc",
    "https://www.guitarcenter.com/Vintage/Fender/Electric-Guitars.gc",
]


def fetch() -> list[dict]:
    results = []
    seen = set()

    for page_url in PAGES:
        try:
            resp = requests.get(page_url, headers=HEADERS, timeout=20)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            # GC product cards — multiple possible selectors
            cards = (
                soup.select(".product-info") or
                soup.select("[class*='product-card']") or
                soup.select("[class*='product-item']") or
                soup.select("li[data-product]") or
                soup.select(".search-result-product-cell")
            )

            # Fallback — find all links to product pages
            if not cards:
                for a in soup.select("a[href*='/p/']"):
                    text = a.get_text(strip=True)
                    href = a.get("href", "")
                    if not text or len(text) < 10:
                        continue
                    full_url = href if href.startswith("http") else f"https://www.guitarcenter.com{href}"
                    if full_url in seen:
                        continue
                    seen.add(full_url)

                    # Get price from nearby elements
                    parent = a.find_parent()
                    price_text = parent.get_text() if parent else ""
                    price = _parse_price(price_text)

                    if price and not (PRICE_MIN <= price <= PRICE_MAX):
                        continue

                    results.append({
                        "source":      "Guitar Center",
                        "id":          f"gc_{_slug(full_url)}",
                        "title":       text,
                        "price":       price,
                        "url":         full_url,
                        "description": price_text[:300],
                        "image_url":   "",
                    })
                continue

            for card in cards:
                title_el = card.select_one(
                    "h2, h3, .product-name, [class*='product-name'], "
                    "[class*='title'], a[title]"
                )
                price_el = card.select_one(
                    ".price, [class*='price'], .sale-price, "
                    "[class*='sale'], [class*='cost']"
                )
                link_el  = card.select_one("a[href]")
                img_el   = card.select_one("img[src], img[data-src]")

                title    = title_el.get_text(strip=True) if title_el else ""
                price    = _parse_price(price_el.get_text(strip=True) if price_el else "")
                href     = link_el["href"] if link_el else ""
                full_url = href if href.startswith("http") else f"https://www.guitarcenter.com{href}"
                img      = ""
                if img_el:
                    img = img_el.get("src") or img_el.get("data-src") or ""

                if not title or len(title) < 5:
                    continue
                if full_url in seen:
                    continue
                seen.add(full_url)
                if price and not (PRICE_MIN <= price <= PRICE_MAX):
                    continue

                results.append({
                    "source":      "Guitar Center",
                    "id":          f"gc_{_slug(full_url)}",
                    "title":       title,
                    "price":       price,
                    "url":         full_url,
                    "description": card.get_text(separator=" ", strip=True)[:400],
                    "image_url":   img,
                })

        except Exception as e:
            print(f"[Guitar Center] Error on {page_url}: {e}")

    print(f"[Guitar Center] Found {len(results)} listings")
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
