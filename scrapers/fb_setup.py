#!/usr/bin/env python3
"""
fb_setup.py — One-time Facebook session saver.

Run this locally (not in GitHub Actions) to log into Facebook
and save your session so the scraper can reuse it.

Usage:
    pip install playwright
    playwright install chromium
    python scrapers/fb_setup.py

A browser window will open. Log in to Facebook normally.
Once you're logged in and see your feed, press Enter in this terminal.
Your session will be saved to data/fb_session.json.

You'll need to re-run this if your session expires (~30-90 days).
GitHub Actions will use the saved session file automatically.
"""

import json
from pathlib import Path

SESSION_FILE = Path(__file__).parent.parent / "data" / "fb_session.json"


def main():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright not installed. Run:")
        print("  pip install playwright")
        print("  playwright install chromium")
        return

    print("\n── Facebook Session Setup ──────────────────────────────")
    print("A browser window will open. Log in to Facebook normally.")
    print("Once you're on your feed/home page, come back here")
    print("and press Enter to save your session.\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Visible window so you can log in
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        )
        page = context.new_page()
        page.goto("https://www.facebook.com/login")

        input("  >> Log in to Facebook in the browser, then press Enter here...")

        # Save the session (cookies + localStorage)
        SESSION_FILE.parent.mkdir(exist_ok=True)
        context.storage_state(path=str(SESSION_FILE))
        print(f"\n  ✓ Session saved to {SESSION_FILE}")
        print("  The scraper will use this session automatically.\n")

        browser.close()

    print("── Done ────────────────────────────────────────────────")
    print("Next steps:")
    print("  1. Commit data/fb_session.json to your GitHub repo")
    print("     (it's in .gitignore by default — remove that line for fb_session.json)")
    print("  2. OR: add it as a GitHub Actions secret (see README)")
    print()


if __name__ == "__main__":
    main()
