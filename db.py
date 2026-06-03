"""
db.py — Supabase database interface.

Handles writing listings from the scraper and reading them for the UI/email.

Setup:
  1. Create a free Supabase project at supabase.com
  2. Run supabase_schema.sql in the SQL editor
  3. Go to Project Settings → API and copy:
       - Project URL  → add as SUPABASE_URL secret in GitHub Actions
       - service_role key → add as SUPABASE_KEY secret in GitHub Actions
"""

import os
import json
import requests
from datetime import datetime, timezone

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")


def _headers() -> dict:
    return {
        "apikey":        SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type":  "application/json",
        "Prefer":        "return=minimal",
    }


def is_configured() -> bool:
    return bool(SUPABASE_URL and SUPABASE_KEY)


def upsert_listings(listings: list[dict]) -> None:
    """Insert new listings or update last_seen on existing ones."""
    if not is_configured() or not listings:
        return

    now = datetime.now(timezone.utc).isoformat()

    rows = []
    for l in listings:
        rows.append({
            "id":            l["id"],
            "source":        l.get("source", ""),
            "title":         l.get("title", ""),
            "price":         l.get("price"),
            "url":           l.get("url", ""),
            "description":   l.get("description", ""),
            "image_url":     l.get("image_url", ""),
            "score":         l.get("score", 0),
            "match_reasons": l.get("match_reasons", []),
            "is_j45":        _is_j45(l),
            "instrument":    l.get("instrument", ""),
            "last_seen":     now,
        })

    # Upsert in batches of 100
    for i in range(0, len(rows), 100):
        batch = rows[i:i+100]
        resp = requests.post(
            f"{SUPABASE_URL}/rest/v1/listings",
            headers={**_headers(), "Prefer": "resolution=merge-duplicates,return=minimal"},
            json=batch,
            timeout=20,
        )
        if not resp.ok:
            print(f"[DB] Upsert error: {resp.status_code} {resp.text[:200]}")


def get_active_listings() -> list[dict]:
    """Fetch all non-archived listings, sorted by score desc then price asc."""
    if not is_configured():
        return []

    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/listings",
        headers=_headers(),
        params={
            "archived": "eq.false",
            "order":    "score.desc,price.asc",
            "limit":    500,
        },
        timeout=20,
    )
    if resp.ok:
        return resp.json()
    print(f"[DB] Fetch error: {resp.status_code} {resp.text[:200]}")
    return []


def get_archived_ids() -> set[str]:
    """Return IDs of all archived listings (to exclude from emails)."""
    if not is_configured():
        return set()

    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/listings",
        headers=_headers(),
        params={
            "archived": "eq.true",
            "select":   "id",
            "limit":    1000,
        },
        timeout=20,
    )
    if resp.ok:
        return {row["id"] for row in resp.json()}
    return set()


def archive_listing(listing_id: str) -> bool:
    """Mark a listing as archived."""
    if not is_configured():
        return False

    now = datetime.now(timezone.utc).isoformat()
    resp = requests.patch(
        f"{SUPABASE_URL}/rest/v1/listings",
        headers=_headers(),
        params={"id": f"eq.{listing_id}"},
        json={"archived": True, "archived_at": now},
        timeout=20,
    )
    return resp.ok


def unarchive_listing(listing_id: str) -> bool:
    """Restore an archived listing."""
    if not is_configured():
        return False

    resp = requests.patch(
        f"{SUPABASE_URL}/rest/v1/listings",
        headers=_headers(),
        params={"id": f"eq.{listing_id}"},
        json={"archived": False, "archived_at": None},
        timeout=20,
    )
    return resp.ok


def _is_j45(l: dict) -> bool:
    blob = f"{l.get('title', '')} {l.get('description', '')}".lower()
    return "j-45" in blob or "j45" in blob
