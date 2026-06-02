"""
The Gear Page classifieds scraper.
Forum: https://www.thegearpage.net/board/index.php?forums/guitars-for-sale.10/
Uses the forum search to find threads mentioning our target models.
"""

import re
import requests
from bs4 import BeautifulSoup
from config import PRICE_MIN, PRICE_MAX

BASE_URL   = "https://www.thegearpage.net"
FORUM_URL  = f"{BASE_URL}/board/index.php"

SEARCHES = ["gibson j-45", "gibson j-50", "gibson country western"]

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

    for query in SEARCHES:
        # Search within the Guitars for Sale subforum (node 10)
        url = (
            f"{FORUM_URL}?search/&q={query.replace(' ', '+')}"
            f"&t=post&c[child_nodes]=1&c[node]=10&o=date"
        )
        try:
            resp = requests.get(url, headers=HEADERS, timeout=20)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            # XenForo thread result rows
            for item in soup.select(".structItem, .discussionListItem, [class*='thread']"):
                title_el = item.select_one(
                    ".structItem-title, .title, h3 a, h4 a, [class*='title'] a"
                )
                link_el  = item.select_one("a[href*='threads']")

                if not title_el:
                    continue

                title = title_el.get_text(strip=True)
                href  = link_el["href"] if link_el else title_el.get("href", "")
                full_url = href if href.startswith("http") else BASE_URL + href

                # Extract price from title if listed
                price = _extract_price(title)
                if price and not (PRICE_MIN <= price <= PRICE_MAX):
                    continue

                results.append({
                    "source":      "The Gear Page",
                    "id":          f"tgp_{_slug(full_url)}",
                    "title":       title,
                    "price":       price,
                    "url":         full_url,
                    "description": item.get_text(separator=" ", strip=True)[:400],
                    "image_url":   "",
                })

        except Exception as e:
            print(f"[The Gear Page] Error for '{query}': {e}")

    # Dedupe
    seen, deduped = set(), []
    for r in results:
        if r["id"] not in seen:
            seen.add(r["id"])
            deduped.append(r)

    print(f"[The Gear Page] Found {len(deduped)} listings")
    return deduped


def _extract_price(text: str) -> float | None:
    match = re.search(r"\$\s?([\d,]+)", text)
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
