"""
Craigslist scraper — uses Craigslist's built-in RSS feeds.
Focused on Texas + Oklahoma cities per user request.
"""

import re
import requests
import xml.etree.ElementTree as ET
from config import PRICE_MIN, PRICE_MAX

# Craigslist subdomain → display name
CITIES = {
    "austin":        "Austin, TX",
    "houston":       "Houston, TX",
    "sanantonio":    "San Antonio, TX",
    "dallas":        "Dallas, TX",
    "elpaso":        "El Paso, TX",
    "oklahomacity":  "Oklahoma City, OK",
}

QUERIES = ["gibson+j-45", "gibson+j-50", "gibson+country+western"]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; j45-hunter/1.0)"
}


def fetch() -> list[dict]:
    results = []

    for subdomain, display_name in CITIES.items():
        for query in QUERIES:
            url = (
                f"https://{subdomain}.craigslist.org/search/msa"
                f"?query={query}&min_price={PRICE_MIN}&max_price={PRICE_MAX}&format=rss"
            )
            try:
                resp = requests.get(url, headers=HEADERS, timeout=15)
                resp.raise_for_status()
                items = _parse_rss(resp.text)

                for item in items:
                    item["source"] = f"Craigslist ({display_name})"
                    item["id"]     = f"cl_{subdomain}_{_slug(item.get('url', ''))}"
                    results.append(item)

            except Exception as e:
                print(f"[Craigslist] Error for {display_name}/{query}: {e}")

    return results


def _parse_rss(xml_text: str) -> list[dict]:
    items = []
    try:
        root = ET.fromstring(xml_text)
        ns = {"rss": "http://purl.org/rss/1.0/"}

        for item in root.findall(".//item") or root.findall(".//rss:item", ns):
            title = _text(item, "title")
            url   = _text(item, "link")
            desc  = _text(item, "description")
            price = _extract_price(title + " " + desc)

            if price and not (PRICE_MIN <= price <= PRICE_MAX):
                continue

            items.append({
                "title":       title,
                "url":         url,
                "price":       price,
                "description": re.sub(r"<[^>]+>", "", desc)[:500],
            })
    except ET.ParseError as e:
        print(f"[Craigslist] RSS parse error: {e}")

    return items


def _text(el, tag: str) -> str:
    child = el.find(tag)
    return child.text.strip() if child is not None and child.text else ""


def _extract_price(text: str) -> float | None:
    match = re.search(r"\$\s?([\d,]+)", text)
    if match:
        try:
            return float(match.group(1).replace(",", ""))
        except ValueError:
            pass
    return None


def _slug(url: str) -> str:
    return re.sub(r"[^a-z0-9]", "_", url.lower())[-60:]
