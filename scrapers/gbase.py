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
    "/gear?Q=gibson+j+45&s=used",
    "/gear?Q=gibson+j+50&s=used",
    "/gear?Q=gibson+country+western&s=used",
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


def fetch() -> list[dict]:
    results = []

    for path in SEARCHES:
        url = BASE_URL + path
        try:
            resp = requests.get(url, headers=HEADERS, timeout=20)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            # GBase gear listing cards
            cards = (
                soup.select("div.gear-item") or
                soup.select("div.item") or
                soup.select("li.result") or
                soup.select("[class*='gear-item']") or
                soup.select("[class*='listing']") or
                # Fallback: any anchor linking to /gear/ pages
                [a for a in soup.select("a[href*='/gear/']") if a.get_text(strip=True)]
            )

            for card in cards:
                # If card is just an <a> tag from fallback, handle it directly
                if card.name == "a":
                    title    = card.get_text(strip=True)
                    href     = card.get("href", "")
                    full_url = href if href.startswith("http") else BASE_URL + href
                    price    = None
                    desc     = title
                else:
                    title_el = card.select_one("h2, h3, .title, [class*='title'], a")
                    price_el = card.select_one(".price, [class*='price']")
                    link_el  = card.select_one("a[href*='/gear/']")

                    title    = title_el.get_text(strip=True) if title_el else ""
                    price    = _parse_price(price_el.get_text(strip=True) if price_el else "")
                    href     = link_el["href"] if link_el else ""
                    full_url = href if href.startswith("http") else BASE_URL + href
                    desc     = card.get_text(separator=" ", strip=True)[:500]

                if not title or len(title) < 5:
                    continue
                if price and not (PRICE_MIN <= price <= PRICE_MAX):
                    continue

                results.append({
                    "source":      "GBase",
                    "id":          f"gbase_{_slug(full_url)}",
                    "title":       title,
                    "price":       price,
                    "url":         full_url,
                    "description": desc,
                })

        except Exception as e:
            print(f"[GBase] Error fetching '{path}': {e}")

    # Dedupe
    seen, deduped = set(), []
    for r in results:
        if r["id"] not in seen:
            seen.add(r["id"])
            deduped.append(r)

    print(f"[GBase] Found {len(deduped)} listings")
    return deduped


def _parse_price(text: str) -> float | None:
    match = re.search(r"\$?([\d,]+)", text.replace("$", "").strip())
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
