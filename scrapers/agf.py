"""
Acoustic Guitar Forum (AGF) classifieds scraper.
URL: https://www.acousticguitarforum.com/forums/forumdisplay.php?f=17
"""

import re
import requests
from bs4 import BeautifulSoup
from config import PRICE_MIN, PRICE_MAX

BASE_URL  = "https://www.acousticguitarforum.com"
FORUM_URL = f"{BASE_URL}/forums/forumdisplay.php?f=17"  # For Sale forum

SEARCHES = ["j-45", "j-50", "country western"]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def fetch() -> list[dict]:
    results = []

    try:
        resp = requests.get(FORUM_URL, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # vBulletin thread rows
        thread_rows = soup.select("tr.threadbit, div.threadbit, [id^='thread_']")

        for row in thread_rows:
            title_el = row.select_one("a.title, a[id^='thread_title']")
            if not title_el:
                continue

            title = title_el.get_text(strip=True)
            href  = title_el.get("href", "")
            url   = href if href.startswith("http") else BASE_URL + "/" + href.lstrip("/")

            # Only include threads that mention our target models
            title_lower = title.lower()
            if not any(s in title_lower for s in SEARCHES):
                continue

            price = _extract_price(title)

            if price and not (PRICE_MIN <= price <= PRICE_MAX):
                continue

            results.append({
                "source":      "Acoustic Guitar Forum",
                "id":          f"agf_{_slug(url)}",
                "title":       title,
                "price":       price,
                "url":         url,
                "description": "",
            })

    except Exception as e:
        print(f"[AGF] Error: {e}")

    return results


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
