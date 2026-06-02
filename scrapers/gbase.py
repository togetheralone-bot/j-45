"""
GBase scraper — scrapes gbase.com search results.
No API available; uses BeautifulSoup to parse listings.
"""

import re
import requests
from bs4 import BeautifulSoup
from config import PRICE_MIN, PRICE_MAX

BASE_URL = "https://www.gbase.com"

SEARCHES = [
    "/guitars/acoustic-guitars?q=gibson+j-45",
    "/guitars/acoustic-guitars?q=gibson+j-50",
    "/guitars/acoustic-guitars?q=gibson+country+western",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def fetch() -> list[dict]:
    results = []

    for path in SEARCHES:
        url = BASE_URL + path
        try:
            resp = requests.get(url, headers=HEADERS, timeout=20)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            # GBase listing cards — class names may need updating if site redesigns
            cards = soup.select(".listing-item, .instrument-item, [class*='listing']")

            for card in cards:
                title_el = card.select_one("h2, h3, .title, [class*='title']")
                price_el = card.select_one(".price, [class*='price']")
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
