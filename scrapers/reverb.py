"""
Reverb scraper — uses the public Reverb API (no auth required).

Two search strategies:
  1. Keyword search across all of Reverb
  2. Direct shop queries for dealers we know are on Reverb
     (catches listings from Wix/custom sites that also sell on Reverb)
"""

import requests
from config import TARGET_MODELS, YEAR_MIN, YEAR_MAX, PRICE_MIN, PRICE_MAX

REVERB_API = "https://api.reverb.com/api/listings"

HEADERS = {
    "Accept": "application/hal+json",
    "Accept-Version": "3.0",
}

# Dealers whose own sites are Wix/JS-rendered but who also sell on Reverb.
# We query their Reverb shops directly to catch listings their site hides from scrapers.
REVERB_SHOPS = [
    "austin-vintage-guitars",
    "rumble-seat-music",
]

KEYWORD_QUERIES = [
    # Gibson (original)
    "gibson j-45 vintage",
    # Fender
    "fender jazzmaster vintage",
    "fender jaguar vintage",
    "fender stratocaster vintage 1962",
    "fender stratocaster vintage 1963",
    "fender stratocaster vintage 1964",
    "fender stratocaster vintage 1965",
    "fender stratocaster vintage 1966",
    "fender stratocaster vintage 1967",
    "fender stratocaster vintage 1968",
    "fender stratocaster vintage 1969",
]


def fetch() -> list[dict]:
    results = []

    # 1. Broad keyword searches
    for query in KEYWORD_QUERIES:
        params = {
            "query":     query,
            "condition": "used",
            "price_min": PRICE_MIN,
            "price_max": PRICE_MAX,
            "per_page":  50,
            "year_max":  YEAR_MAX,
        }
        try:
            resp = requests.get(REVERB_API, headers=HEADERS, params=params, timeout=15)
            resp.raise_for_status()
            for listing in resp.json().get("listings", []):
                results.append(_parse(listing, "Reverb"))
        except Exception as e:
            print(f"[Reverb] Error on '{query}': {e}")

    # 2. Direct shop queries for Wix dealers on Reverb
    for shop_slug in REVERB_SHOPS:
        shop_url = f"https://api.reverb.com/api/listings?shop_slug={shop_slug}&per_page=50"
        try:
            resp = requests.get(shop_url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            shop_name = _shop_display_name(shop_slug)
            for listing in resp.json().get("listings", []):
                results.append(_parse(listing, shop_name))
        except Exception as e:
            print(f"[Reverb/{shop_slug}] Error: {e}")

    # Dedupe by ID
    seen, deduped = set(), []
    for r in results:
        if r["id"] not in seen:
            seen.add(r["id"])
            deduped.append(r)

    print(f"[Reverb] Found {len(deduped)} listings")
    return deduped


def _parse(listing: dict, source: str) -> dict:
    photos    = listing.get("photos", [])
    image_url = ""
    if photos:
        try:
            image_url = (
                photos[0].get("_links", {}).get("large_crop", {}).get("href", "") or
                photos[0].get("_links", {}).get("full", {}).get("href", "")
            )
        except (AttributeError, IndexError):
            pass

    return {
        "source":      source,
        "id":          f"reverb_{listing.get('id')}",
        "title":       listing.get("title", ""),
        "price":       _parse_price(listing.get("price", {}).get("amount")),
        "url":         listing.get("_links", {}).get("web", {}).get("href", ""),
        "description": listing.get("description", ""),
        "image_url":   image_url,
    }


def _shop_display_name(slug: str) -> str:
    names = {
        "austin-vintage-guitars": "Austin Vintage Guitars",
        "rumble-seat-music":      "Rumble Seat Music",
    }
    return names.get(slug, slug.replace("-", " ").title())


def _parse_price(val) -> float | None:
    try:
        return float(val)
    except (TypeError, ValueError):
        return None
