"""
Dealer scrapers — individual vintage guitar shops.

Shopify stores use the /products.json API (reliable, no HTML parsing needed).
Non-Shopify stores use targeted HTML scrapers built from their actual page structure.
"""

import re
import json
import requests
from bs4 import BeautifulSoup
from config import PRICE_MIN, PRICE_MAX

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# ── Shopify stores ────────────────────────────────────────────────────────────
# All expose /products.json — structured, reliable, no HTML parsing.
SHOPIFY_DEALERS = [
    {
        "name":      "Carter Vintage",
        "base":      "https://cartervintage.com",
        "id_prefix": "carter",
    },
    {
        "name":      "Emerald City Guitars",
        "base":      "https://emeraldcityguitars.com",
        "id_prefix": "emerald",
    },
    {
        "name":      "Norman's Rare Guitars",
        "base":      "https://normansrareguitars.com",
        "id_prefix": "normans",
    },
    {
        "name":      "TR Crandall Guitars",
        "base":      "https://trcrandall.com",
        "id_prefix": "trcrandall",
    },
    {
        "name":      "Dave's Guitar Shop",
        "base":      "https://www.davesguitar.com",
        "id_prefix": "daves",
    },
    {
        "name":      "Chicago Music Exchange",
        "base":      "https://www.chicagomusicexchange.com",
        "id_prefix": "cme",
    },
    {
        "name":      "Elderly Instruments",
        "base":      "https://www.elderly.com",
        "id_prefix": "elderly",
    },
    {
        "name":      "Cream City Music",
        "base":      "https://www.creamcitymusic.com",
        "id_prefix": "creamcity",
    },
]

# ── Non-Shopify stores ────────────────────────────────────────────────────────
# Each has a custom scraper matched to its actual HTML structure.

def fetch() -> list[dict]:
    results = []
    for dealer in SHOPIFY_DEALERS:
        results.extend(_fetch_shopify(dealer))
    results.extend(_fetch_gruhn())
    results.extend(_fetch_retrofret())
    results.extend(_fetch_garysguitars())
    results.extend(_fetch_wellstrung())
    return results


# ── Shopify JSON scraper ──────────────────────────────────────────────────────

def _fetch_shopify(dealer: dict) -> list[dict]:
    """
    Pulls all products from Shopify's public /products.json endpoint,
    filters for Gibson J-45/J-50/Country Western locally.
    """
    results = []
    base = dealer["base"]
    seen = set()

    for page in range(1, 6):
        url = f"{base}/products.json?limit=250&page={page}"
        try:
            resp = requests.get(url, headers=HEADERS, timeout=20)
            if resp.status_code == 404:
                break
            resp.raise_for_status()
            products = resp.json().get("products", [])
            if not products:
                break

            for p in products:
                title  = p.get("title", "")
                handle = p.get("handle", "")
                body   = p.get("body_html", "")
                blob   = f"{title} {body}".lower()

                if "gibson" not in blob:
                    continue
                if not any(m in blob for m in ["j-45", "j45", "j-50", "j50", "country western"]):
                    continue
                if handle in seen:
                    continue
                seen.add(handle)

                price = None
                for variant in p.get("variants", []):
                    try:
                        v = float(variant.get("price", 0))
                        if v > 0:
                            price = v
                            break
                    except (ValueError, TypeError):
                        pass

                # price None or 0.00 = sold/unavailable — skip
                if not price:
                    continue
                if not (PRICE_MIN <= price <= PRICE_MAX):
                    continue

                images = p.get("images", [])
                image_url = images[0].get("src", "") if images else ""

                results.append({
                    "source":      dealer["name"],
                    "id":          f"{dealer['id_prefix']}_{handle[:50]}",
                    "title":       title,
                    "price":       price,
                    "url":         f"{base}/products/{handle}",
                    "description": re.sub(r"<[^>]+>", " ", body).strip()[:500],
                    "image_url":   image_url,
                })

        except Exception as e:
            print(f"[{dealer['name']}] Error page {page}: {e}")
            break

    print(f"[{dealer['name']}] Found {len(results)} listings")
    return results


# ── Gruhn Guitars ─────────────────────────────────────────────────────────────
# Custom PHP site. Search via query param, listings in a table/grid layout.

def _fetch_gruhn() -> list[dict]:
    results = []
    urls = [
        "https://www.gruhn.com/shop/acoustic-guitars/?search=gibson+j-45",
        "https://www.gruhn.com/shop/acoustic-guitars/?search=gibson+j-50",
        "https://www.gruhn.com/shop/acoustic-guitars/?search=gibson+country+western",
    ]
    for url in urls:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=20)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            # Gruhn uses WooCommerce-style product li elements
            for card in soup.select("li.product, .product-item, .type-product"):
                title_el = card.select_one("h2, h3, .woocommerce-loop-product__title")
                price_el = card.select_one(".price, .amount, ins .amount")
                link_el  = card.select_one("a[href]")

                title    = title_el.get_text(strip=True) if title_el else ""
                price    = _parse_price(price_el.get_text(strip=True) if price_el else "")
                href     = link_el["href"] if link_el else ""

                if not title:
                    continue
                if price and not (PRICE_MIN <= price <= PRICE_MAX):
                    continue

                results.append({
                    "source":      "Gruhn Guitars",
                    "id":          f"gruhn_{_slug(href)}",
                    "title":       title,
                    "price":       price,
                    "url":         href,
                    "description": card.get_text(separator=" ", strip=True)[:400],
                })
        except Exception as e:
            print(f"[Gruhn] Error: {e}")

    print(f"[Gruhn Guitars] Found {len(results)} listings")
    return results


# ── Retrofret ─────────────────────────────────────────────────────────────────
# Classic ASP site. Search results in a table layout.

def _fetch_retrofret() -> list[dict]:
    results = []
    urls = [
        "https://retrofret.com/results.asp?Find=gibson+j-45&Category=Acoustics",
        "https://retrofret.com/results.asp?Find=gibson+j-50&Category=Acoustics",
        "https://retrofret.com/results.asp?Find=gibson+country+western&Category=Acoustics",
    ]
    for url in urls:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=20)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            # Retrofret renders results as table rows with instrument links
            for a in soup.select("a[href*='instrument.asp']"):
                title = a.get_text(strip=True)
                href  = a["href"]
                full_url = href if href.startswith("http") else f"https://retrofret.com/{href.lstrip('/')}"

                # Try to find price in parent row
                row   = a.find_parent("tr") or a.find_parent("td")
                price = _parse_price(row.get_text() if row else "")

                if not title or len(title) < 5:
                    continue
                if price and not (PRICE_MIN <= price <= PRICE_MAX):
                    continue

                results.append({
                    "source":      "Retrofret",
                    "id":          f"retrofret_{_slug(full_url)}",
                    "title":       title,
                    "price":       price,
                    "url":         full_url,
                    "description": row.get_text(separator=" ", strip=True)[:400] if row else "",
                })
        except Exception as e:
            print(f"[Retrofret] Error: {e}")

    print(f"[Retrofret] Found {len(results)} listings")
    return results


# ── Gary's Classic Guitars ────────────────────────────────────────────────────
# Drupal-based custom site. Has a dedicated Gibson acoustics category page.
# Each listing is a linked div with title and price in predictable elements.

def _fetch_garysguitars() -> list[dict]:
    results = []
    # Gary's has a specific Gibson acoustics category — much more reliable
    # than a keyword search on his custom CMS
    urls = [
        "https://www.garysguitars.com/vintage-gibson-acoustic-guitars",
    ]
    for url in urls:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=20)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            # Gary's site uses a node/catalog structure with h3 titles and price spans
            for node in soup.select(".views-row, .node-type-instrument, .views-field-title"):
                title_el = node.select_one("h3, h2, .field-content a, a")
                price_el = node.select_one(".price, .field-price, [class*=price]")
                link_el  = node.select_one("a[href]")

                title = title_el.get_text(strip=True) if title_el else ""
                price = _parse_price(price_el.get_text(strip=True) if price_el else "")
                href  = link_el["href"] if link_el else ""
                full_url = href if href.startswith("http") else f"https://www.garysguitars.com{href}"

                if not title or len(title) < 5:
                    continue
                # Require a parseable price — Gary's always shows price on listings
                if not price:
                    continue
                if not (PRICE_MIN <= price <= PRICE_MAX):
                    continue

                results.append({
                    "source":      "Gary's Classic Guitars",
                    "id":          f"garys_{_slug(full_url)}",
                    "title":       title,
                    "price":       price,
                    "url":         full_url,
                    "description": node.get_text(separator=" ", strip=True)[:400],
                })
        except Exception as e:
            print(f"[Gary's Classic Guitars] Error: {e}")

    print(f"[Gary's Classic Guitars] Found {len(results)} listings")
    return results


# ── Well Strung Guitars ───────────────────────────────────────────────────────
# WordPress site with a custom post type for guitars at /guitar/{slug}.
# Inventory page at /shop-inventory/ with standard WooCommerce-style cards.

def _fetch_wellstrung() -> list[dict]:
    results = []
    urls = [
        "https://wellstrungguitars.com/?s=gibson+j-45&post_type=guitar",
        "https://wellstrungguitars.com/?s=gibson+j-50&post_type=guitar",
        "https://wellstrungguitars.com/?s=gibson+country+western&post_type=guitar",
    ]
    for url in urls:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=20)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            # WordPress search results — article cards
            for article in soup.select("article, .guitar-card, .entry, [class*='guitar']"):
                title_el = article.select_one("h2, h3, .entry-title, [class*='title']")
                price_el = article.select_one(".price, [class*='price'], .woocommerce-Price-amount")
                link_el  = article.select_one("a[href]")

                title = title_el.get_text(strip=True) if title_el else ""
                price = _parse_price(price_el.get_text(strip=True) if price_el else "")
                href  = link_el["href"] if link_el else ""

                if not title or len(title) < 5:
                    continue
                if price and not (PRICE_MIN <= price <= PRICE_MAX):
                    continue

                results.append({
                    "source":      "Well Strung Guitars",
                    "id":          f"wellstrung_{_slug(href)}",
                    "title":       title,
                    "price":       price,
                    "url":         href,
                    "description": article.get_text(separator=" ", strip=True)[:400],
                })
        except Exception as e:
            print(f"[Well Strung Guitars] Error: {e}")

    print(f"[Well Strung Guitars] Found {len(results)} listings")
    return results


# ── Helpers ───────────────────────────────────────────────────────────────────

def _parse_price(text: str) -> float | None:
    match = re.search(r"[\d,]+", text.replace("$", "").replace(",", ""))
    if match:
        try:
            v = float(match.group().replace(",", ""))
            # Sanity check — ignore obviously wrong values
            if 100 < v < 100000:
                return v
        except ValueError:
            pass
    return None


def _slug(url: str) -> str:
    return re.sub(r"[^a-z0-9]", "_", url.lower())[-60:]
