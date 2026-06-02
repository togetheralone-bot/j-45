"""
J45 Hunter — Search Configuration
Edit this file to change what you're hunting for.
"""

# ── Target Models ────────────────────────────────────────────────
TARGET_MODELS = ["j-45", "j45", "j 45", "j-50", "j50", "j 50", "country western"]

# ── Year Range ───────────────────────────────────────────────────
YEAR_MIN = 1954
YEAR_MAX = 1965

# ── Price Range (USD) ────────────────────────────────────────────
PRICE_MIN = 2000
PRICE_MAX = 7000

# ── Hard Exclusions (listing is dropped if any of these appear) ──
EXCLUDE_TERMS = [
    '1 9/16"',
    "1 9/16",
    "1-9/16",
    "reissue",
    "re-issue",
    "replica",
    "copy",
    "tribute",
    "custom shop",
    "historic",
    "murphy lab",
    "limited edition",
    "inspired by",
    "50s j-45",
    "60s j-45",
    "70s j-45",
    "50s j45",
    "60s j45",
]

# ── Soft Score Boosters (nice to have — raises listing priority) ─
BOOST_TERMS = [
    "original tuners",
    "original case",
    "all original",
    "sunburst",
    "natural",
    "round shoulder",
    "ladder braced",
    "low action",
    "no cracks",
    "no repairs",
]

# ── Notification (Gmail) ─────────────────────────────────────────
NOTIFY_EMAIL = "YOUR_EMAIL@gmail.com"        # where alerts are sent TO
GMAIL_SENDER  = "YOUR_GMAIL@gmail.com"       # the Gmail account sending alerts
# GMAIL_APP_PASSWORD is set as a GitHub Actions secret (never put it here)

# ── SMS Notification (T-Mobile email-to-SMS) ─────────────────────
# Format: 10digitnumber@tmomail.net
# Leave empty to disable SMS
SMS_EMAIL = "YOUR_10_DIGIT_NUMBER@tmomail.net"

# ── Scrape Interval ──────────────────────────────────────────────
# Controlled by GitHub Actions schedule in .github/workflows/hunt.yml
# Default: every 5 minutes
