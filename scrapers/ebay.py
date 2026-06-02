"""
eBay scraper — uses the eBay Browse API.
Requires a free eBay developer account to get an API key.
Set EBAY_APP_ID as a GitHub Actions secret.
"""

import os
import requests
from config import PRICE_MIN, PRICE_MAX

EBAY_API = "https://api.ebay.com/buy/browse/v1/item_summary/search"

QUERIES = [
    "gibson j-45 vintage",
    "gibson j-50 vintage",
    "gibson country western guitar vintage",
]


def fetch() -> list[dict]:
    app_id = os.environ.get("EBAY_APP_ID")
    if not app_id:
        print("[eBay] No EBAY_APP_ID set — skipping.")
        return []

    token = _get_token(app_id)
    if not token:
        return []

    results = []
    headers = {"Authorization": f"Bearer {token}"}

    for query in QUERIES:
        params = {
            "q": query,
            "filter": f"price:[{PRICE_MIN}..{PRICE_MAX}],priceCurrency:USD,conditions:{{USED}}",
            "limit": 50,
            "sort": "newlyListed",
        }

        try:
            resp = requests.get(EBAY_API, headers=headers, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()

            for item in data.get("itemSummaries", []):
                results.append({
                    "source":      "eBay",
                    "id":          f"ebay_{item.get('itemId')}",
                    "title":       item.get("title", ""),
                    "price":       _parse_price(item),
                    "url":         item.get("itemWebUrl", ""),
                    "description": item.get("shortDescription", ""),
                })

        except Exception as e:
            print(f"[eBay] Error fetching '{query}': {e}")

    return results


def _get_token(app_id: str) -> str | None:
    """Exchange App ID for OAuth token (client credentials flow)."""
    app_secret = os.environ.get("EBAY_CERT_ID", "")
    try:
        resp = requests.post(
            "https://api.ebay.com/identity/v1/oauth2/token",
            auth=(app_id, app_secret),
            data={
                "grant_type": "client_credentials",
                "scope": "https://api.ebay.com/oauth/api_scope",
            },
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json().get("access_token")
    except Exception as e:
        print(f"[eBay] Token error: {e}")
        return None


def _parse_price(item: dict) -> float | None:
    try:
        return float(item["price"]["value"])
    except (KeyError, TypeError, ValueError):
        return None
