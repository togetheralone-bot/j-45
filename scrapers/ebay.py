"""
eBay scraper — uses rssbay.net to generate RSS feeds from eBay searches.
This is a free workaround since eBay removed their native RSS feeds and
their developer API approval process is unreliable.

rssbay.net wraps eBay searches in RSS format with no API key required.
"""

import re
import requests
import xml.etree.ElementTree as ET
from config import PRICE_MIN, PRICE_MAX

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

# rssbay.net feed URL format
# Uses /feed endpoint with keyword (singular), globalId, price range
BASE = "https://rssbay.net/feed"

SEARCHES = [
    "gibson j-45 vintage",
    "gibson j-50 vintage",
    "gibson country western guitar vintage",
]


def fetch() -> list[dict]:
    results = []

    for query in SEARCHES:
        url = (
            f"{BASE}?keyword={query.replace(' ', '+')}"
            f"&globalId=EBAY-US"
            f"&buyitnow=1"
            f"&auction=1"
            f"&condition=-"
            f"&MinPrice={PRICE_MIN}"
            f"&MaxPrice={PRICE_MAX}"
        )
        try:
            resp = requests.get(url, headers=HEADERS, timeout=20)
            resp.raise_for_status()
            items = _parse_rss(resp.text)
            results.extend(items)
        except Exception as e:
            print(f"[eBay/rssbay] Error for '{query}': {e}")

    # Dedupe by ID
    seen, deduped = set(), []
    for r in results:
        if r["id"] not in seen:
            seen.add(r["id"])
            deduped.append(r)

    print(f"[eBay] Found {len(deduped)} listings via rssbay.net")
    return deduped


def _parse_rss(xml_text: str) -> list[dict]:
    items = []
    try:
        root = ET.fromstring(xml_text)

        for item in root.findall(".//item"):
            title = _text(item, "title")
            url   = _text(item, "link")
            desc  = _text(item, "description")
            price = _extract_price(title + " " + desc)

            if not title or not url:
                continue
            if price and not (PRICE_MIN <= price <= PRICE_MAX):
                continue

            # Extract item ID from eBay URL
            id_match = re.search(r"/(\d{10,})", url)
            item_id  = f"ebay_{id_match.group(1)}" if id_match else f"ebay_{_slug(url)}"

            # Try to get image from description
            img_match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', desc)
            image_url = img_match.group(1) if img_match else ""

            clean_desc = re.sub(r"<[^>]+>", " ", desc).strip()[:400]

            items.append({
                "source":      "eBay",
                "id":          item_id,
                "title":       title,
                "price":       price,
                "url":         url.split("?")[0],
                "description": clean_desc,
                "image_url":   image_url,
            })

    except ET.ParseError as e:
        print(f"[eBay/rssbay] RSS parse error: {e}")

    return items


def _text(el, tag: str) -> str:
    child = el.find(tag)
    return child.text.strip() if child is not None and child.text else ""


def _extract_price(text: str) -> float | None:
    # rssbay uses "USD 4,500.00" format; also handle "$4,500"
    match = re.search(r"(?:USD|\$)\s*([\d,]+\.?\d*)", text)
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
