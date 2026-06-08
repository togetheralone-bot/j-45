"""
True Vintage Guitar scraper — truevintageguitar.com
Shopify store but /products.json is IP-blocked from GitHub Actions.
Workaround: scrape the collection pages directly via HTML.
Small inventory (~30 items total) so one pass covers everything.
"""

import re
import requests
from bs4 import BeautifulSoup
from config import PRICE_MIN, PRICE_MAX

BASE_URL = "https://truevintageguitar.com"

# Scrape brand-specific collections — all current inventory
PAGES = [
    f"{BASE_URL}/collections/gibson",
    f"{BASE_URL}/collections/fender",
    f"{BASE_URL}/collections/all-current-inventory",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer":         "https://truevintageguitar.com/",
}


def fetch() -> list[dict]:
    results = []
    seen    = set()

    for page_url in PAGES:
        try:
            resp = requests.get(page_url, headers=HEADERS, timeout=20)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            # Product links follow /collections/.../products/<slug>
            for a in soup.select("a[href*='/products/']"):
                href = a.get("href", "")
                # Must be a product link, not a blog/page link
                if not re.search(r"/products/[a-z0-9\-]+$", href):
                    continue

                full_url = href if href.startswith("http") else BASE_URL + href

                # Dedupe by URL
                if full_url in seen:
                    continue
                seen.add(full_url)

                # Title — get from link text or nearby heading
                title = a.get_text(separator=" ", strip=True)

                # Price — look in the same anchor or nearby sibling text
                parent_text = ""
                node = a
                for _ in range(4):
                    if node.parent:
                        node = node.parent
                    parent_text = node.get_text(separator=" ", strip=True)
                    if "$" in parent_text:
                        break

                price = _parse_price(parent_text)

                # Clean up title — strip price strings and image alt text noise
                title = re.sub(r"\$[\d,]+\.?\d*", "", title).strip()
                title = re.sub(r"\s{2,}", " ", title).strip()

                if not title or len(title) < 8:
                    continue

                # Get image from nearby img tag
                img_el    = a.select_one("img[src]")
                image_url = ""
                if img_el:
                    src = img_el.get("src", "")
                    # Shopify CDN — use full size
                    image_url = re.sub(r"\?.*$", "", src)
                    if not image_url.startswith("http"):
                        image_url = "https:" + image_url

                if price and not (PRICE_MIN <= price <= PRICE_MAX):
                    continue

                results.append({
                    "source":      "True Vintage Guitar",
                    "id":          f"tvg_{_slug(full_url)}",
                    "title":       title,
                    "price":       price,
                    "url":         full_url,
                    "description": "",
                    "image_url":   image_url,
                })

        except Exception as e:
            print(f"[True Vintage Guitar] Error on '{page_url}': {e}")

    # Dedupe by ID
    seen_ids, deduped = set(), []
    for r in results:
        if r["id"] not in seen_ids:
            seen_ids.add(r["id"])
            deduped.append(r)

    print(f"[True Vintage Guitar] Found {len(deduped)} listings")
    return deduped


def _parse_price(text: str) -> float | None:
    match = re.search(r"\$([\d,]+\.?\d*)", text)
    if match:
        try:
            v = float(match.group(1).replace(",", ""))
            if 100 < v < 200000:
                return v
        except ValueError:
            pass
    return None


def _slug(url: str) -> str:
    return re.sub(r"[^a-z0-9]", "_", url.lower())[-60:]
