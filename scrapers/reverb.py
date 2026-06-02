"""
Reverb scraper — uses the public Reverb API (no auth required).

Two search strategies:
  1. Keyword search across all of Reverb (paginated, no condition filter)
  2. Direct shop queries for dealers we know are on Reverb
"""

import requests
from config import TARGET_MODELS, YEAR_MIN, YEAR_MAX, PRICE_MIN, PRICE_MAX

REVERB_API = "https://api.reverb.com/api/listings"

HEADERS = {
    "Accept": "application/hal+json",
    "Accept-Version": "3.0",
}

# Dealers whose own sites are blocked/JS-rendered but who also sell on Reverb.
REVERB_SHOPS = [
    "austin-vintage-guitars",
    "rumble-seat-music",
    "gruhn-guitars",
    "normans-rare-guitars",
    "guitar-center",
    "cream-city-music",
    "bernunzio-uptown-music",
    "retrofret-vintage-guitars",
    "dream-guitars",
]

# Multiple targeted queries to maximize coverage.
# No 'condition' filter — sellers categorize inconsistently, missing it cuts results.
# Year queries added to catch listings that don't say "vintage" but have the decade in title.
KEYWORD_QUERIES = [
    "gibson j-45 vintage",
    "gibson j-45 1950s",
    "gibson j-45 1960s",
    "gibson j-50 vintage",
    "gibson j-50 1950s",
    "gibson j-50 1960s",
    "gibson country western vintage",
    "gibson j-45 1955",
    "gibson j-45 1956",
    "gibson j-45 1957",
    "gibson j-45 1958",
    "gibson j-45 1959",
    "gibson j-45 1960",
    "gibson j-45 1961",
    "gibson j-45 1962",
    "gibson j-45 1963",
    "gibson j-45 1964",
    "gibson j-45 1965",
    "gibson j-45 1966",
    "gibson j-45 1967",
    "gibson j-45 1968",
    "gibson j-45 1969",
]

MAX_PAGES = 3  # 50 results × 3 pages = up to 150 per query


def fetch() -> list[dict]:
    results = []

    # 1. Broad keyword searches with pagination
    for query in KEYWORD_QUERIES:
        for page in range(1, MAX_PAGES + 1):
            params = {
                "query":     query,
                "price_min": PRICE_MIN,
                "price_max": PRICE_MAX,
                "per_page":  50,
                "page":      page,
            }
            try:
                resp = requests.get(REVERB_API, headers=HEADERS, params=params, timeout=15)
                resp.raise_for_status()
                data = resp.json()
                listings = data.get("listings", [])
                if not listings:
                    break  # No more results for this query
                for listing in listings:
                    results.append(_parse(listing, "Reverb"))
                # If we got fewer than 50, no point fetching next page
                if len(listings) < 50:
                    break
            except Exception as e:
                print(f"[Reverb] Error on '{query}' p{page}: {e}")
                break

    # 2. Direct shop queries for dealers on Reverb
    for shop_slug in REVERB_SHOPS:
        shop_url = f"{REVERB_API}?shop_slug={shop_slug}&per_page=50"
        try:
            resp = requests.get(shop_url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            shop_name = _shop_display_name(shop_slug)
            listings = resp.json().get("listings", [])
            for listing in listings:
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
        "austin-vintage-guitars":   "Austin Vintage Guitars",
        "rumble-seat-music":        "Rumble Seat Music",
        "gruhn-guitars":            "Gruhn Guitars",
        "normans-rare-guitars":     "Norman's Rare Guitars",
        "guitar-center":            "Guitar Center",
        "cream-city-music":         "Cream City Music",
        "bernunzio-uptown-music":   "Bernunzio Uptown Music",
        "retrofret-vintage-guitars": "Retrofret",
        "dream-guitars":            "Dream Guitars",
    }
    return names.get(slug, slug.replace("-", " ").title())


def _parse_price(val) -> float | None:
    try:
        return float(val)
    except (TypeError, ValueError):
        return None
