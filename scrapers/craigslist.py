"""
Craigslist scraper.
Craigslist blocks RSS from datacenter IPs so we scrape the HTML search page instead.
"""

import re
import requests
from bs4 import BeautifulSoup
from config import PRICE_MIN, PRICE_MAX

CITIES = {
    "austin":        "Austin, TX",
    "houston":       "Houston, TX",
    "sanantonio":    "San Antonio, TX",
    "dallas":        "Dallas, TX",
    "elpaso":        "El Paso, TX",
    "oklahomacity":  "Oklahoma City, OK",
}

QUERIES = [
    # Gibson (original)
    "gibson+j-45", "gibson+j-50", "gibson+country+western",
    # Fender
    "fender+jazzmaster", "fender+jaguar", "fender+stratocaster+vintage",
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

    for subdomain, display_name in CITIES.items():
        for query in QUERIES:
            url = (
                f"https://{subdomain}.craigslist.org/search/msa"
                f"?query={query}&min_price={PRICE_MIN}&max_price={PRICE_MAX}"
                f"&sort=date"
            )
            try:
                resp = requests.get(url, headers=HEADERS, timeout=20)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "html.parser")

                # Craigslist search results — li.cl-search-result or li.result-row
                cards = soup.select("li.cl-search-result, li.result-row, [class*='cl-search-result']")

                for card in cards:
                    title_el = card.select_one(".titlestring, .result-title, a[class*='title']")
                    price_el = card.select_one(".priceinfo, .result-price, [class*='price']")
                    link_el  = card.select_one("a[href]")

                    title = title_el.get_text(strip=True) if title_el else ""
                    price = _parse_price(price_el.get_text(strip=True) if price_el else "")
                    href  = link_el["href"] if link_el else ""
                    full_url = href if href.startswith("http") else f"https://{subdomain}.craigslist.org{href}"

                    if not title:
                        continue
                    if price and not (PRICE_MIN <= price <= PRICE_MAX):
                        continue

                    results.append({
                        "source":      f"Craigslist ({display_name})",
                        "id":          f"cl_{subdomain}_{_slug(full_url)}",
                        "title":       title,
                        "price":       price,
                        "url":         full_url,
                        "description": card.get_text(separator=" ", strip=True)[:400],
                        "image_url":   "",
                    })

            except Exception as e:
                print(f"[Craigslist] Error for {display_name}/{query}: {e}")

    seen, deduped = set(), []
    for r in results:
        if r["id"] not in seen:
            seen.add(r["id"])
            deduped.append(r)

    print(f"[Craigslist] Found {len(deduped)} listings")
    return deduped


def _parse_price(text: str) -> float | None:
    match = re.search(r"\$\s?([\d,]+)", text)
    if match:
        try:
            return float(match.group(1).replace(",", ""))
        except ValueError:
            pass
    return None


def _slug(url: str) -> str:
    return re.sub(r"[^a-z0-9]", "_", url.lower())[-60:]
