#!/usr/bin/env python3
"""
J45 Hunter — Main entrypoint.

Usage:
    python hunt.py                # Normal run (alert on new listings only)
    python hunt.py --test         # Print top matches, no email, no state update
    python hunt.py --email-test   # Send real email with top 20 matches, no state update
    python hunt.py --reset        # Clear seen listings
"""

import sys
import time
from datetime import datetime, timezone

from scrapers import reverb, ebay, gbase, dealers, craigslist, agf, facebook, guitarcenter, gearpage, bernunzio
from filter import filter_and_score
from seen import load_seen, save_seen, find_new, mark_seen
from notify import send_alerts

SCRAPER_MODULES = [
    ("Reverb",               reverb.fetch),
    ("eBay",                 ebay.fetch),
    ("GBase",                gbase.fetch),
    ("Dealers",              dealers.fetch),
    ("Craigslist",           craigslist.fetch),
    ("Facebook Marketplace", facebook.fetch),
    ("Guitar Forum",         agf.fetch),
    ("Guitar Center",        guitarcenter.fetch),
    ("The Gear Page",        gearpage.fetch),
    ("Bernunzio",            bernunzio.fetch),
]


def main(test_mode=False, reset_mode=False, email_test_mode=False):
    print(f"\n{'='*50}")
    print(f"  J45 Hunter  —  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"{'='*50}\n")

    if reset_mode:
        save_seen(set())
        print("✓ Seen listings cleared. Next run will alert on everything.")
        return

    # ── Gather all listings ──────────────────────────────────────
    all_raw = []
    for name, fetch_fn in SCRAPER_MODULES:
        print(f"  Scraping {name}...", end=" ", flush=True)
        t0 = time.time()
        try:
            results = fetch_fn()
            all_raw.extend(results)
            print(f"{len(results)} listings ({time.time()-t0:.1f}s)")
        except Exception as e:
            print(f"ERROR: {e}")

    print(f"\n  Total raw listings: {len(all_raw)}")

    # ── Filter and score ─────────────────────────────────────────
    matched = filter_and_score(all_raw)
    print(f"  Matched your specs: {len(matched)}")

    if test_mode:
        print("\n── TEST MODE — Top matches ─────────────────────────────\n")
        for l in matched[:20]:
            price_str = f"${l['price']:,.0f}" if l.get("price") else "?"
            print(f"  [{l['score']}★] {l['title']}")
            print(f"       {l['source']} · {price_str} · {l['url']}")
            print(f"       Reasons: {', '.join(l.get('match_reasons', []))}\n")
        return

    if email_test_mode:
        top20 = matched[:20]
        print(f"\n  📧 EMAIL TEST — Sending top {len(top20)} matches to your inbox...")
        print(f"  (Seen listings NOT updated)\n")
        # Treat first 3 as "new", rest as "previous" for preview purposes
        send_alerts(new_listings=top20[:3], all_active=top20)
        print("\n  ✓ Done. Check your inbox.\n")
        return

    # ── Find new listings ────────────────────────────────────────
    seen     = load_seen()
    new_ones = find_new(matched, seen)
    print(f"  New since last run: {len(new_ones)}")

    if new_ones:
        print(f"\n  🎸 Sending alert for {len(new_ones)} new listing(s)...")
        # Pass new listings + full active list (up to 20 for previous section)
        send_alerts(new_listings=new_ones, all_active=matched[:20])

    # ── Update seen ──────────────────────────────────────────────
    updated_seen = mark_seen(matched, seen)
    save_seen(updated_seen)
    print(f"\n  ✓ Done. Tracking {len(updated_seen)} seen listing IDs.\n")


if __name__ == "__main__":
    test_mode       = "--test"       in sys.argv
    reset_mode      = "--reset"      in sys.argv
    email_test_mode = "--email-test" in sys.argv
    main(test_mode=test_mode, reset_mode=reset_mode, email_test_mode=email_test_mode)
