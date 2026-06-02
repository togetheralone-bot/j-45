"""
Reverb scraper — uses the public Reverb API (no auth required).
"""

import requests
from config import TARGET_MODELS, YEAR_MIN, YEAR_MAX, PRICE_MIN, PRICE_MAX

REVERB_API = "https://api.reverb.com/api/listings"

HEADERS = {
    "Accept": "application/hal+json",
    "Accept-Version": "3.0",
}


def fetch() -> list[dict]:
    results = []

    for model in ["gibson j-45", "gibson j-50", "gibson country western"]:
        params = {
            "query": f"{model} vintage",
            "condition": "used",
            "price_min": PRICE_MIN,
            "price_max": PRICE_MAX,
            "per_page": 50,
        }

        try:
            resp = requests.get(REVERB_API, headers=HEADERS, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()

            for listing in data.get("listings", []):
                # Grab first photo URL if available
                photos = listing.get("photos", [])
                image_url = ""
                if photos:
                    # photos is a list of dicts with _links.large_crop.href
                    try:
                        image_url = photos[0].get("_links", {}).get("large_crop", {}).get("href", "")
                        if not image_url:
                            image_url = photos[0].get("_links", {}).get("full", {}).get("href", "")
                    except (AttributeError, IndexError):
                        pass

                results.append({
                    "source":      "Reverb",
                    "id":          f"reverb_{listing.get('id')}",
                    "title":       listing.get("title", ""),
                    "price":       _parse_price(listing.get("price", {}).get("amount")),
                    "url":         listing.get("_links", {}).get("web", {}).get("href", ""),
                    "description": listing.get("description", ""),
                    "image_url":   image_url,
                })

        except Exception as e:
            print(f"[Reverb] Error fetching '{model}': {e}")

    return results


def _parse_price(val) -> float | None:
    try:
        return float(val)
    except (TypeError, ValueError):
        return None
