"""
GBase scraper.
Correct search URL format: https://www.gbase.com/gear?Q=gibson+j+45
"""

import re
import requests
from bs4 import BeautifulSoup
from config import PRICE_MIN, PRICE_MAX

BASE_URL = "https://www.gbase.com"

SEARCHES = [
    # Gibson (original)
    "/gear?Q=gibson+j+45&s=used",
    # Fender
    "/gear?Q=fender+jazzmaster&s=used",
    "/gear?Q=fender+jaguar&s=used",
    "/gear?Q=fender+stratocaster+vintage&s=used",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.gbase.com/",
}

SOLD_MARKERS = ["*sold", "* sold", "sold *", "[sold]", "(sold)", "- sold", "sold-", "**sold"]


def fetch() -> list[dict]:
    results = []

    for path in SEARCHES:
        url = BASE_URL + path
        try:
            resp = requests.get(url, headers=HEADERS, timeout=20)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            cards = (
                soup.select("div.gear-item") or
                soup.select("div.item") or
                soup.select("li.result") or
                soup.select("[class*='gear-item']") or
                soup.select("[class*='listing']") or
                [a for a in soup.select("a[href*='/gear/']") if a.get_text(strip=True)]
            )

            for card in cards:
                if card.name == "a":
                    raw_text = card.get_text(strip=True)
                    href     = card.get("href", "")
                    full_url = href if href.startswith("http") else BASE_URL + href
                    price    = _parse_price(raw_text)
                    title    = _clean_title(raw_text)
                    desc     = raw_text
                else:
                    title_el = card.select_one("h2, h3, .title, [class*='title'], a")
                    price_el = card.select_one(".price, [class*='price']")
                    link_el  = card.select_one("a[href*='/gear/']")

                    raw_text = card.get_text(separator=" ", strip=True)
                    title    = _clean_title(title_el.get_text(strip=True) if title_el else raw_text)
                    price    = _parse_price(price_el.get_text(strip=True) if price_el else raw_text)
                    href     = link_el["href"] if link_el else ""
                    full_url = href if href.startswith("http") else BASE_URL + href
                    desc     = raw_text[:500]

                if not title or len(title) < 5:
                    continue
                if price and not (PRICE_MIN <= price <= PRICE_MAX):
                    continue

                # Skip sold listings
                check = (title + " " + (desc or "")).lower()
                if any(marker in check for marker in SOLD_MARKERS):
                    continue

                results.append({
                    "source":      "GBase",
                    "id":          f"gbase_{_slug(full_url)}",
                    "title":       title,
                    "price":       price,
                    "url":         full_url,
                    "description": desc,
                    "image_url":   "",
                })

        except Exception as e:
            print(f"[GBase] Error fetching '{path}': {e}")

    seen, deduped = set(), []
    for r in results:
        if r["id"] not in seen:
            seen.add(r["id"])
            deduped.append(r)

    print(f"[GBase] Found {len(deduped)} listings")
    return deduped


def _clean_title(text: str) -> str:
    price_match  = re.search(r"\$[\d,]+", text)
    before_price = text[:price_match.start()].strip() if price_match else text.strip()

    END_WORDS = [
        "sunburst", "natural", "burst", "cherry", "black", "blonde",
        "adj", "adv", "original", "case", "ohsc", "refret", "neck",
        "top", "back", "sides", "bound", "binding", "inlay",
    ]

    best_cut = before_price
    best_pos = 0
    lower    = before_price.lower()

    for word in END_WORDS:
        idx = lower.rfind(word)
        if idx != -1:
            end = idx + len(word)
            if end > best_pos:
                best_pos = end
                best_cut = before_price[:end].strip()

    if best_pos > 8 and len(best_cut) >= 10:
        return best_cut

    fallback = re.sub(r"([a-z])([A-Z][a-z])", r"\1", before_price).strip()
    return fallback if len(fallback) >= 10 else before_price


def _parse_price(text: str) -> float | None:
    match = re.search(r"\$([\d,]+)", text)
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
