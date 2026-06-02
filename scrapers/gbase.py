"""
GBase scraper — scrapes gbase.com search results.
GBase uses a specific search URL structure and renders listings in a consistent grid.
"""

import re
import requests
from bs4 import BeautifulSoup
from config import PRICE_MIN, PRICE_MAX

BASE_URL = "https://www.gbase.com"

# GBase search URLs — verified structure as of 2025
SEARCHES = [
    "/search?q=gibson+j-45&t=acoustic",
    "/search?q=gibson+j-50&t=acoustic",
    "/search?q=gibson+country+western&t=acoustic",
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

    for path in SEARCHES:
        url = BASE_URL + path
        try:
            resp = requests.get(url, headers=HEADERS, timeout=20)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            # GBase renders gear cards with these selectors
            cards = (
                soup.select("div.gear-card") or
                soup.select("div.search-result-item") or
                soup.select("div.listing") or
                soup.select("li.gear-item") or
                soup.select("[class*='gear-card']") or
                soup.select("[class*='result-item']")
            )

            for card in cards:
                title_el = card.select_one("h2, h3, .gear-title, .title, [class*='title']")
                price_el = card.select_one(".price, .gear-price, [class*='price']")
                link_el  = card.select_one("a[href]")

                title = title_el.get_text(strip=True) if title_el else ""
                price = _parse_price(price_el.get_text(strip=True) if price_el else "")
                href  = link_el["href"] if link_el else ""
                full_url = href if href.startswith("http") else BASE_URL + href

                if not title:
                    continue
                if price and not (PRICE_MIN <= price <= PRICE_MAX):
                    continue

                results.append({
                    "source":      "GBase",
                    "id":          f"gbase_{_slug(full_url)}",
                    "title":       title,
                    "price":       price,
                    "url":         full_url,
                    "description": card.get_text(separator=" ", strip=True)[:500],
                })

        except Exception as e:
            print(f"[GBase] Error fetching '{path}': {e}")

    print(f"[GBase] Found {len(results)} listings")
    return results


def _parse_price(text: str) -> float | None:
    match = re.search(r"[\d,]+", text.replace("$", "").strip())
    if match:
        try:
            return float(match.group().replace(",", ""))
        except ValueError:
            pass
    return None


def _slug(url: str) -> str:
    return re.sub(r"[^a-z0-9]", "_", url.lower())[-60:]
