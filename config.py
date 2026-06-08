"""
Guitar Hunter — Search Configuration
Edit this file to change what you're hunting for.
"""
import os

INSTRUMENTS = [
    {
        "name":      "Gibson J-45",
        "brand":     "gibson",
        "models":    ["j-45", "j45", "j 45"],
        "year_min":  1956,
        "year_max":  1965,
        "price_min": 2000,
        "price_max": 7000,
        "exclude_terms": [
            '1 9/16"', "1 9/16", "1-9/16",
            "reissue", "re-issue", "replica", "copy", "tribute",
            "custom shop", "customshop", "custom-shop",
            "historic", "murphy lab", "limited edition", "ltd",
            "inspired by",
            "50s j-45", "60s j-45", "70s j-45", "50s j45", "60s j45",
            # Modern year in title — these are reissues/commemoratives
            "2015", "2016", "2017", "2018", "2019",
            "2020", "2021", "2022", "2023", "2024", "2025",
        ],
    },
    {
        "name":      "Fender Jazzmaster",
        "brand":     "fender",
        "models":    ["jazzmaster"],
        "year_min":  1958,
        "year_max":  1965,
        "price_min": 2000,
        "price_max": 5500,
        "exclude_terms": [
            "reissue", "re-issue", "mij", "japan", "japanese",
            "vintage ii", "vintage 2", "modern", "brand new",
            "replica", "copy", "tribute",
            "custom shop", "customshop", "custom-shop",
            "masterbuilt", "master built",
            "limited edition", "ltd",
            "signature", "sig model",
            "2015", "2016", "2017", "2018", "2019",
            "2020", "2021", "2022", "2023", "2024", "2025",
        ],
    },
    {
        "name":      "Fender Jaguar",
        "brand":     "fender",
        "models":    ["jaguar"],
        "year_min":  1958,
        "year_max":  1965,
        "price_min": 2000,
        "price_max": 5000,
        "exclude_terms": [
            "reissue", "re-issue", "mij", "japan", "japanese",
            "vintage ii", "vintage 2", "modern", "brand new",
            "replica", "copy", "tribute",
            "custom shop", "customshop", "custom-shop",
            "masterbuilt", "master built",
            "limited edition", "ltd",
            "signature", "johnny marr", "kurt cobain",
            "mustang",  # Fender Mustang ≠ Jaguar
            "2015", "2016", "2017", "2018", "2019",
            "2020", "2021", "2022", "2023", "2024", "2025",
        ],
    },
    {
        "name":      "Fender Stratocaster",
        "brand":     "fender",
        "models":    ["stratocaster", "strat"],
        "year_min":  1962,
        "year_max":  1969,
        "price_min": 5000,
        "price_max": 10500,
        "exclude_terms": [
            "reissue", "re-issue", "mij", "japan", "japanese",
            "vintage ii", "vintage 2", "modern", "brand new",
            "replica", "copy", "tribute",
            "custom shop", "customshop", "custom-shop",
            "masterbuilt", "master built",
            "american vintage", "american original", "player",
            "limited edition", "ltd",
            "signature", "srv", "hendrix", "clapton", "beck",
            "2015", "2016", "2017", "2018", "2019",
            "2020", "2021", "2022", "2023", "2024", "2025",
        ],
    },
]

BOOST_TERMS = [
    "original tuners",
    "original case",
    "original pickups",
    "all original",
    "sunburst",
    "natural",
    "round shoulder",
    "ladder braced",
    "low action",
    "no cracks",
    "no repairs",
    "ohsc",
]

NOTIFY_EMAIL = os.environ.get("NOTIFY_EMAIL", "")
GMAIL_SENDER  = os.environ.get("GMAIL_SENDER",  "")
SMS_EMAIL = os.environ.get("SMS_EMAIL", "")

# ── Legacy flat values (used by scrapers — do not edit) ──────────
TARGET_MODELS = list({m for inst in INSTRUMENTS for m in inst["models"]})
YEAR_MIN      = min(inst["year_min"] for inst in INSTRUMENTS)
YEAR_MAX      = max(inst["year_max"] for inst in INSTRUMENTS)
PRICE_MIN     = min(inst["price_min"] for inst in INSTRUMENTS)
PRICE_MAX     = max(inst["price_max"] for inst in INSTRUMENTS)
EXCLUDE_TERMS = list({t for inst in INSTRUMENTS for t in inst["exclude_terms"]})
