"""
Filter and scoring engine.
Applies hard exclusions, year/price checks, and a boost score.
"""

import re
from config import (
    TARGET_MODELS,
    YEAR_MIN, YEAR_MAX,
    PRICE_MIN, PRICE_MAX,
    EXCLUDE_TERMS,
    BOOST_TERMS,
)


def filter_and_score(listings: list[dict]) -> list[dict]:
    """
    Returns filtered listings sorted by score (descending).
    Each listing gets a `score` field and a `match_reason` list.
    """
    passed = []

    for listing in listings:
        result = _evaluate(listing)
        if result:
            passed.append(result)

    # Deduplicate by ID
    seen = set()
    deduped = []
    for l in passed:
        if l["id"] not in seen:
            seen.add(l["id"])
            deduped.append(l)

    # Sort: highest score first, then by price ascending
    deduped.sort(key=lambda x: (-x["score"], x["price"] or 9999999))
    return deduped


def _evaluate(listing: dict) -> dict | None:
    blob = f"{listing.get('title', '')} {listing.get('description', '')}".lower()

    # ── 1. Must mention a target model ──────────────────────────
    if not any(model in blob for model in TARGET_MODELS):
        return None

    # ── 2. Must mention "gibson" ─────────────────────────────────
    if "gibson" not in blob:
        return None

    # ── 3. Hard exclusions ───────────────────────────────────────
    for term in EXCLUDE_TERMS:
        if term.lower() in blob:
            return None

# ── 4. Year check (strict) ───────────────────────────────────
years_found = re.findall(r"\b(19[3-9]\d)\b", blob)
if not years_found:
    return None  # No vintage year mentioned at all — skip it
in_range = [y for y in years_found if YEAR_MIN <= int(y) <= YEAR_MAX]
if not in_range:
    return None  # Years mentioned but none in 1956–1965 — skip it


    # ── 5. Price check ───────────────────────────────────────────
    price = listing.get("price")
    if price is not None:
        if not (PRICE_MIN <= price <= PRICE_MAX):
            return None

    # ── 6. Boost scoring ─────────────────────────────────────────
    score = 0
    match_reasons = []

    if years_found:
        score += 3
        match_reasons.append(f"year mention: {', '.join(set(years_found))}")

    for term in BOOST_TERMS:
        if term.lower() in blob:
            score += 1
            match_reasons.append(term)

    listing["score"]        = score
    listing["match_reasons"] = match_reasons
    return listing
