"""
Dealer scrapers — individual vintage guitar shops.
Each shop gets its own function since their HTML structures differ.
These are the most likely to break if a shop redesigns — fix individually.
"""

import re
import requests
from bs4 import BeautifulSoup
from config import PRICE_MIN, PRICE_MAX

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

DEALERS = [
    {
        "name": "Gruhn Guitars",
        "urls": [
            "https://www.gruhn.com/shop/acoustic-guitars/?search=gibson+j-45",
            "https://www.gruhn.com/shop/acoustic-guitars/?search=gibson+j-50",
            "https://www.gruhn.com/shop/acoustic-guitars/?search=gibson+country+western",
        ],
        "id_prefix": "gruhn",
    },
    {
        "name": "Retrofret",
        "urls": [
            "https://retrofret.com/products?q=gibson+j-45",
            "https://retrofret.com/products?q=gibson+j-50",
            "https://retrofret.com/products?q=gibson+country+western",
        ],
        "id_prefix": "retrofret",
    },
    {
        "name": "Carter Vintage",
        "urls": [
            "https://cartervintage.com/collections/acoustic-guitars?q=gibson+j-45",
            "https://cartervintage.com/collections/acoustic-guitars?q=gibson+j-50",
        ],
        "id_prefix": "carter",
    },
    {
        "name": "Elderly Instruments",
        "urls": [
            "https://www.elderly.com/collections/used-acoustic-guitars?q=gibson+j-45",
            "https://www.elderly.com/collections/used-acoustic-guitars?q=gibson+j-50",
        ],
        "id_prefix": "elderly",
    },
    {
        "name": "Norman's Rare Guitars",
        "urls": [
            "https://www.normansrareguitars.com/search?type=product&q=gibson+j-45+vintage",
            "https://www.normansrareguitars.com/search?type=product&q=gibson+j-50+vintage",
        ],
        "id_prefix": "normans",
    },
    {
        "name": "Dave's Guitar Shop",
        "urls": [
            "https://www.davesguitar.com/search?q=gibson+j-45+vintage",
            "https://www.davesguitar.com/search?q=gibson+j-50+vintage",
        ],
        "id_prefix": "daves",
    },
    {
        "name": "Chicago Music Exchange",
        "urls": [
            "https://www.chicagomusicexchange.com/search?q=gibson+j-45+vintage",
            "https://www.chicagomusicexchange.com/search?q=gibson+j-50+vintage",
        ],
        "id_prefix": "cme",
    },
]


def fetch() -> list[dict]:
    results = []
    for dealer in DEALERS:
        results.extend(_scrape_dealer(dealer))
    return results


def _scrape_dealer(dealer: dict) -> list[dict]:
    results = []

    for url in dealer["urls"]:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=20)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            # Generic product card selectors — works for most Shopify-based stores
            # and common CMS patterns. May need tuning per-shop.
            cards = soup.select(
                ".product-item, .product-card, .product, "
                "[class*='product-item'], article.product, "
                ".inventory-item, [class*='listing-item']"
            )

            # Fallback: look for any linked heading that mentions Gibson
            if not cards:
                cards = _fallback_cards(soup)

            for card in cards:
                title_el = card.select_one("h2, h3, h4, .product-title, .product-name, [class*='title']")
                price_el = card.select_one(".price, [class*='price'], .amount")
                link_el  = card.select_one("a[href]")

                title = title_el.get_text(strip=True) if title_el else card.get_text(strip=True)[:80]
                price = _parse_price(price_el.get_text(strip=True) if price_el else "")
                href  = link_el["href"] if link_el else ""

                base  = _base_url(url)
                full_url = href if href.startswith("http") else base + href

                if not title or len(title) < 5:
                    continue

                if price and not (PRICE_MIN <= price <= PRICE_MAX):
                    continue

                results.append({
                    "source":      dealer["name"],
                    "id":          f"{dealer['id_prefix']}_{_slug(full_url)}",
                    "title":       title,
                    "price":       price,
                    "url":         full_url,
                    "description": card.get_text(separator=" ", strip=True)[:500],
                })

        except Exception as e:
            print(f"[{dealer['name']}] Error fetching '{url}': {e}")

    return results


def _fallback_cards(soup: BeautifulSoup) -> list:
    """Last-resort: grab any anchor whose text mentions Gibson."""
    seen = set()
    cards = []
    for a in soup.find_all("a", href=True):
        text = a.get_text(strip=True).lower()
        if "gibson" in text and a["href"] not in seen:
            seen.add(a["href"])
            cards.append(a)
    return cards


def _parse_price(text: str) -> float | None:
    match = re.search(r"[\d,]+", text.replace("$", "").strip())
    if match:
        try:
            return float(match.group().replace(",", ""))
        except ValueError:
            pass
    return None


def _base_url(url: str) -> str:
    parts = url.split("/")
    return f"{parts[0]}//{parts[2]}"


def _slug(url: str) -> str:
    return re.sub(r"[^a-z0-9]", "_", url.lower())[-60:]
