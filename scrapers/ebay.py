"""
eBay scraper.

Two modes:
  1. Browse API (preferred) — set EBAY_APP_ID + EBAY_CERT_ID as GitHub secrets
  2. HTML scrape fallback — works without any API keys

To get free API keys (takes 5 min):
  https://developer.ebay.com → Create account → Create app → Copy App ID + Cert ID
"""

import os
import re
import requests
from bs4 import BeautifulSoup
from config import PRICE_MIN, PRICE_MAX

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

QUERIES = [
    "gibson j-45 vintage 1950s 1960s",
    "gibson j-50 vintage 1950s 1960s",
    "gibson country western guitar vintage",
]


def fetch() -> list[dict]:
    app_id = os.environ.get("EBAY_APP_ID")

    if app_id:
        results = _fetch_api(app_id)
        if results:
            print(f"[eBay] Found {len(results)} listings via API")
            return results
        print("[eBay] API returned no results, falling back to HTML scrape")

    results = _fetch_html()
    print(f"[eBay] Found {len(results)} listings via HTML scrape")
    return results


# ── API mode ─────────────────────────────────────────────────────

def _fetch_api(app_id: str) -> list[dict]:
    token = _get_token(app_id)
    if not token:
        return []

    results = []
    api_headers = {**HEADERS, "Authorization": f"Bearer {token}"}

    for query in QUERIES:
        params = {
            "q": query,
            "filter": f"price:[{PRICE_MIN}..{PRICE_MAX}],priceCurrency:USD,conditions:{{USED}}",
            "limit": 50,
            "sort": "newlyListed",
        }
        try:
            resp = requests.get(
                "https://api.ebay.com/buy/browse/v1/item_summary/search",
                headers=api_headers, params=params, timeout=15
            )
            resp.raise_for_status()
            for item in resp.json().get("itemSummaries", []):
                results.append({
                    "source":      "eBay",
                    "id":          f"ebay_{item.get('itemId')}",
                    "title":       item.get("title", ""),
                    "price":       _parse_float(item.get("price", {}).get("value")),
                    "url":         item.get("itemWebUrl", ""),
                    "description": item.get("shortDescription", ""),
                })
        except Exception as e:
            print(f"[eBay API] Error for '{query}': {e}")

    return results


def _get_token(app_id: str) -> str | None:
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


# ── HTML scrape fallback ─────────────────────────────────────────

def _fetch_html() -> list[dict]:
    results = []

    search_urls = [
        f"https://www.ebay.com/sch/i.html?_nkw=gibson+j-45+vintage+1960s&_sacat=33034&LH_ItemCondition=3000&_udlo={PRICE_MIN}&_udhi={PRICE_MAX}&LH_TitleDesc=1&_sop=10",
        f"https://www.ebay.com/sch/i.html?_nkw=gibson+j-50+vintage+1960s&_sacat=33034&LH_ItemCondition=3000&_udlo={PRICE_MIN}&_udhi={PRICE_MAX}&LH_TitleDesc=1&_sop=10",
        f"https://www.ebay.com/sch/i.html?_nkw=gibson+country+western+guitar+vintage&_sacat=33034&LH_ItemCondition=3000&_udlo={PRICE_MIN}&_udhi={PRICE_MAX}&LH_TitleDesc=1&_sop=10",
    ]

    for url in search_urls:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=20)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            for card in soup.select(".s-item"):
                title_el = card.select_one(".s-item__title")
                price_el = card.select_one(".s-item__price")
                link_el  = card.select_one("a.s-item__link")

                title = title_el.get_text(strip=True) if title_el else ""
                if not title or title.lower() == "shop on ebay":
                    continue

                price    = _parse_price(price_el.get_text(strip=True) if price_el else "")
                item_url = link_el["href"].split("?")[0] if link_el else ""
                item_id  = re.search(r"/(\d{10,})", item_url)

                if price and not (PRICE_MIN <= price <= PRICE_MAX):
                    continue

                results.append({
                    "source":      "eBay",
                    "id":          f"ebay_{item_id.group(1) if item_id else _slug(item_url)}",
                    "title":       title,
                    "price":       price,
                    "url":         item_url,
                    "description": "",
                })

        except Exception as e:
            print(f"[eBay HTML] Error: {e}")

    return results


def _parse_price(text: str) -> float | None:
    match = re.search(r"[\d,]+\.?\d*", text.replace("$", "").replace(",", ""))
    if match:
        try:
            return float(match.group())
        except ValueError:
            pass
    return None


def _parse_float(val) -> float | None:
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def _slug(url: str) -> str:
    return re.sub(r"[^a-z0-9]", "_", url.lower())[-60:]
