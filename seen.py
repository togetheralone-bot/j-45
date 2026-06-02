"""
Seen listings tracker.
Stores listing IDs in a local JSON file so we only alert on new ones.
In GitHub Actions the file is committed back to the repo each run.
"""

import json
import os
from datetime import datetime, timezone

SEEN_FILE = os.path.join(os.path.dirname(__file__), "data", "seen_listings.json")


def load_seen() -> set[str]:
    if not os.path.exists(SEEN_FILE):
        return set()
    try:
        with open(SEEN_FILE) as f:
            data = json.load(f)
        return set(data.get("ids", []))
    except (json.JSONDecodeError, KeyError):
        return set()


def save_seen(ids: set[str]) -> None:
    os.makedirs(os.path.dirname(SEEN_FILE), exist_ok=True)
    with open(SEEN_FILE, "w") as f:
        json.dump({
            "ids":        sorted(ids),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "count":      len(ids),
        }, f, indent=2)


def find_new(listings: list[dict], seen: set[str]) -> list[dict]:
    return [l for l in listings if l["id"] not in seen]


def mark_seen(listings: list[dict], seen: set[str]) -> set[str]:
    return seen | {l["id"] for l in listings}
