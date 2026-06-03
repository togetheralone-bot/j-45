"""
Filter and scoring engine.
Checks each listing against all instruments in config.INSTRUMENTS.
A listing passes if it matches ANY instrument's criteria.
"""

import re
from config import INSTRUMENTS, BOOST_TERMS

# Parts/non-whole-guitar exclusions — checked against title+description
PARTS_TERMS = [
    # Explicit parts phrases
    "body only", "neck only", "body & neck", "body and neck",
    "parts guitar", "parts only", "project guitar", "parts/project",
    "for parts", "as-is parts", "body blank",
    "loaded body", "unloaded body",
    "neck pocket", "pickguard only",
    "tuning machine", "tuning peg",
    "tremolo arm", "tremolo only",
    "nut only", "fretboard only", "fingerboard only",
    # Instrument-specific body/neck
    "stratocaster body", "strat body",
    "stratocaster neck", "strat neck",
    "jazzmaster body", "jazzmaster neck",
    "jaguar body", "jaguar neck",
    "j-45 body", "j45 body",
    "j-45 neck", "j45 neck",
    "guitar body", "guitar neck",
]

# These are checked against the TITLE only (too risky in description)
TITLE_PARTS_TERMS = [
    " body ", "- body", "body -", "(body)",
    " neck ", "- neck", "neck -", "(neck)",
    "project body", "refinish body",
]


def filter_and_score(listings: list[dict]) -> list[dict]:
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

    deduped.sort(key=lambda x: (-x["score"], x["price"] or 9999999))
    return deduped


def _evaluate(listing: dict) -> dict | None:
    title = listing.get("title", "").lower()
    desc  = listing.get("description", "").lower()
    blob  = f"{title} {desc}"

    # Full blob parts check
    for term in PARTS_TERMS:
        if term in blob:
            return None

    # Title-only parts check (catches "1964 Strat Body" etc.)
    title_padded = f" {title} "
    for term in TITLE_PARTS_TERMS:
        if term in title_padded:
            return None

    for inst in INSTRUMENTS:
        result = _match_instrument(listing, blob, inst)
        if result:
            return result

    return None


def _match_instrument(listing: dict, blob: str, inst: dict) -> dict | None:
    # 1. Must mention the brand
    if inst["brand"] not in blob:
        return None

    # 2. Must mention a target model
    if not any(m in blob for m in inst["models"]):
        return None

    # 3. Hard exclusions
    for term in inst["exclude_terms"]:
        if term.lower() in blob:
            return None

    # 4. Year check — a year in range must be explicitly mentioned
    years_found = re.findall(r"\b(19[3-9]\d)\b", blob)
    if not years_found:
        return None
    in_range = [y for y in years_found if inst["year_min"] <= int(y) <= inst["year_max"]]
    if not in_range:
        return None

    # 5. Price check
    price = listing.get("price")
    if price is not None:
        if not (inst["price_min"] <= price <= inst["price_max"]):
            return None

    # 6. Boost scoring
    score = 3  # base for year match
    match_reasons = [f"year: {', '.join(set(in_range))}"]

    for term in BOOST_TERMS:
        if term.lower() in blob:
            score += 1
            match_reasons.append(term)

    listing = dict(listing)  # don't mutate original
    listing["score"]         = score
    listing["match_reasons"] = match_reasons
    listing["instrument"]    = inst["name"]
    return listing
