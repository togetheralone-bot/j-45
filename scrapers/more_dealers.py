"""
Additional dealer scrapers:
  - Acoustic Vibes Music   (Shopify)
  - Matt Umanov Guitars    (Shopify)
  - Thunder Road Guitars   (WordPress/custom)
  - Dream Guitars          (WordPress/WooCommerce)
  - Rumble Seat Music      (Wix — JS-rendered, best-effort)
  - Fretted Americana      (custom site)
"""

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
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# ── Shopify stores ────────────────────────────────────────────────────────────
SHOPIFY_DEALERS = [
    {
        "name":      "Acoustic Vibes Music",
        "base":      "https://acousticvibesmusic.com",
        "id_prefix": "acousticvibes",
    },
    {
        "name":      "Matt Umanov Guitars",
        "base":      "https://www.umanovguitars.com",
        "id_prefix": "umanov",
    },
]


def fetch() -> list[dict]:
    results = []
    for dealer in SHOPIFY_DEALERS:
        results.extend(_fetch_shopify(dealer))
    results.extend(_fetch_thunder_road())
    results.extend(_fetch_dream_guitars())
    results.extend(_fetch_rumble_seat())
    results.extend(_fetch_fretted_americana())
    return results


def _fetch_shopify(dealer: dict) -> list[dict]:
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

                is_gibson = "gibson" in blob and any(m in blob for m in ["j-45", "j45", "j-50", "j50", "country western"])
                is_fender = "fender" in blob and any(m in blob for m in ["jazzmaster", "jaguar", "stratocaster"])
                if not (is_gibson or is_fender):
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


def _fetch_thunder_road() -> list[dict]:
    """Thunder Road Guitars — WordPress with custom store."""
    results = []
    urls = [
        # Gibson (original)
        "https://thunderroadguitars.com/store?s=gibson+j-45",
        "https://thunderroadguitars.com/store?s=gibson+j-50",
        "https://thunderroadguitars.com/store?s=gibson+country+western",
        # Fender
        "https://thunderroadguitars.com/store?s=fender+jazzmaster",
        "https://thunderroadguitars.com/store?s=fender+jaguar",
        "https://thunderroadguitars.com/store?s=fender+stratocaster",
    ]
    for url in urls:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=20)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            for card in soup.select(".product, .instrument, article, [class*='product']"):
                title_el = card.select_one("h2, h3, h4, .title, [class*='title']")
                price_el = card.select_one(".price, [class*='price'], .amount")
                link_el  = card.select_one("a[href]")
                img_el   = card.select_one("img[src]")

                title = title_el.get_text(strip=True) if title_el else ""
                price = _parse_price(price_el.get_text(strip=True) if price_el else "")
                href  = link_el["href"] if link_el else ""

                if not title or len(title) < 5:
                    continue
                if price and not (PRICE_MIN <= price <= PRICE_MAX):
                    continue

                results.append({
                    "source":      "Thunder Road Guitars",
                    "id":          f"thunderroad_{_slug(href)}",
                    "title":       title,
                    "price":       price,
                    "url":         href,
                    "description": card.get_text(separator=" ", strip=True)[:400],
                    "image_url":   img_el["src"] if img_el else "",
                })
        except Exception as e:
            print(f"[Thunder Road] Error: {e}")

    print(f"[Thunder Road Guitars] Found {len(results)} listings")
    return results


def _fetch_dream_guitars() -> list[dict]:
    """
    Dream Guitars — WooCommerce site.
    Search results are JS-rendered so we scrape their vintage steel-string
    category pages instead which are server-rendered.
    """
    results = []
    seen = set()

    # Their vintage category pages are server-rendered and paginated
    base_urls = [
        "https://www.dreamguitars.com/shop/instruments/guitars/steel-string-guitars/vintage-steel-string-guitars/",
        "https://www.dreamguitars.com/shop/instruments/guitars/steel-string-guitars/flattop/",
    ]

    for base_url in base_urls:
        for page in range(1, 5):
            url = base_url if page == 1 else f"{base_url}page/{page}/"
            try:
                resp = requests.get(url, headers=HEADERS, timeout=20)
                if resp.status_code == 404:
                    break
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "html.parser")

                cards = soup.select("li.product, .product, [class*='product-item']")
                if not cards:
                    break

                for card in cards:
                    title_el = card.select_one("h2, h3, .woocommerce-loop-product__title, .product-title")
                    price_el = card.select_one(".price, .amount, ins .amount")
                    link_el  = card.select_one("a[href]")
                    img_el   = card.select_one("img[src], img[data-src]")

                    title = title_el.get_text(strip=True) if title_el else ""
                    price = _parse_price(price_el.get_text(strip=True) if price_el else "")
                    href  = link_el["href"] if link_el else ""
                    img   = (img_el.get("src") or img_el.get("data-src", "")) if img_el else ""

                    if not title or len(title) < 5:
                        continue
                    if href in seen:
                        continue
                    seen.add(href)
                    if price and not (PRICE_MIN <= price <= PRICE_MAX):
                        continue

                    results.append({
                        "source":      "Dream Guitars",
                        "id":          f"dream_{_slug(href)}",
                        "title":       title,
                        "price":       price,
                        "url":         href,
                        "description": card.get_text(separator=" ", strip=True)[:400],
                        "image_url":   img,
                    })

            except Exception as e:
                print(f"[Dream Guitars] Error {url}: {e}")
                break

    print(f"[Dream Guitars] Found {len(results)} listings")
    return results


def _fetch_rumble_seat() -> list[dict]:
    """
    Rumble Seat Music — Wix site, JS-rendered.
    Best-effort HTML scrape; may return 0 if Wix blocks or renders client-side.
    """
    results = []
    urls = [
        # Gibson (original)
        "https://www.rumbleseatmusic.com/shop?q=gibson+j-45",
        "https://www.rumbleseatmusic.com/shop?q=gibson+j-50",
        # Fender
        "https://www.rumbleseatmusic.com/shop?q=fender+jazzmaster",
        "https://www.rumbleseatmusic.com/shop?q=fender+jaguar",
        "https://www.rumbleseatmusic.com/shop?q=fender+stratocaster",
    ]
    for url in urls:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=20)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            for card in soup.select("[class*='product'], [class*='item'], [data-hook='product-item']"):
                title_el = card.select_one("[data-hook='product-item-name'], h2, h3, .title")
                price_el = card.select_one("[data-hook='product-item-price-to-pay'], .price")
                link_el  = card.select_one("a[href]")

                title = title_el.get_text(strip=True) if title_el else ""
                price = _parse_price(price_el.get_text(strip=True) if price_el else "")
                href  = link_el["href"] if link_el else ""
                full_url = href if href.startswith("http") else "https://www.rumbleseatmusic.com" + href

                if not title or len(title) < 5:
                    continue
                if price and not (PRICE_MIN <= price <= PRICE_MAX):
                    continue

                results.append({
                    "source":      "Rumble Seat Music",
                    "id":          f"rumbleseat_{_slug(full_url)}",
                    "title":       title,
                    "price":       price,
                    "url":         full_url,
                    "description": card.get_text(separator=" ", strip=True)[:400],
                    "image_url":   "",
                })
        except Exception as e:
            print(f"[Rumble Seat] Error: {e}")

    print(f"[Rumble Seat Music] Found {len(results)} listings")
    return results


def _fetch_fretted_americana() -> list[dict]:
    """Fretted Americana — vintage specialist, custom site."""
    results = []
    urls = [
        # Gibson (original)
        "https://www.frettedamericana.com/guitars/acoustic/?s=gibson+j-45",
        "https://www.frettedamericana.com/guitars/acoustic/?s=gibson+j-50",
        "https://www.frettedamericana.com/guitars/acoustic/?s=gibson+country+western",
        # Fender
        "https://www.frettedamericana.com/guitars/electric/?s=fender+jazzmaster",
        "https://www.frettedamericana.com/guitars/electric/?s=fender+jaguar",
        "https://www.frettedamericana.com/guitars/electric/?s=fender+stratocaster",
        # General inventory
        "https://www.frettedamericana.com/inventory/",
    ]
    for url in urls:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=20)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            for card in soup.select(".product, .instrument, article, [class*='product'], [class*='listing']"):
                title_el = card.select_one("h2, h3, h4, .title, [class*='title']")
                price_el = card.select_one(".price, [class*='price']")
                link_el  = card.select_one("a[href]")

                title = title_el.get_text(strip=True) if title_el else ""
                price = _parse_price(price_el.get_text(strip=True) if price_el else "")
                href  = link_el["href"] if link_el else ""
                full_url = href if href.startswith("http") else "https://www.frettedamericana.com" + href

                if not title or len(title) < 5:
                    continue
                if price and not (PRICE_MIN <= price <= PRICE_MAX):
                    continue

                results.append({
                    "source":      "Fretted Americana",
                    "id":          f"fretted_{_slug(full_url)}",
                    "title":       title,
                    "price":       price,
                    "url":         full_url,
                    "description": card.get_text(separator=" ", strip=True)[:400],
                    "image_url":   "",
                })
        except Exception as e:
            print(f"[Fretted Americana] Error: {e}")

    print(f"[Fretted Americana] Found {len(results)} listings")
    return results


def _parse_price(text: str) -> float | None:
    match = re.search(r"[\d,]+\.?\d*", text.replace("$", "").replace(",", ""))
    if match:
        try:
            v = float(match.group().replace(",", ""))
            if 100 < v < 100000:
                return v
        except ValueError:
            pass
    return None


def _slug(url: str) -> str:
    return re.sub(r"[^a-z0-9]", "_", url.lower())[-60:]
