"""
Gmail notification — new listings only, grouped by instrument.
Also sends SMS via email-to-SMS gateway.
"""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from config import NOTIFY_EMAIL, GMAIL_SENDER, SMS_EMAIL

SOURCE_COLORS = {
    "Reverb":                  "#e05c00",
    "eBay":                    "#0064d2",
    "GBase":                   "#2d6a2d",
    "Craigslist":              "#7b3f9e",
    "Facebook Marketplace":    "#1877f2",
    "Acoustic Guitar Forum":   "#8b4513",
    "Gruhn Guitars":           "#555",
    "Retrofret":               "#555",
    "Carter Vintage":          "#1a1a1a",
    "Emerald City Guitars":    "#2e7d32",
    "Norman's Rare Guitars":   "#555",
    "TR Crandall Guitars":     "#555",
    "Austin Vintage Guitars":  "#bf4300",
    "Gary's Classic Guitars":  "#555",
    "Well Strung Guitars":     "#555",
    "Dave's Guitar Shop":      "#555",
    "Chicago Music Exchange":  "#555",
    "Elderly Instruments":     "#555",
    "Cream City Music":        "#555",
    "Guitar Center":           "#c8102e",
    "The Music Zoo":           "#1a1a1a",
    "The Gear Page":           "#2b5797",
    "Bernunzio Uptown Music":  "#8b6914",
    "Acoustic Vibes Music":    "#1b6ca8",
    "Matt Umanov Guitars":     "#555",
    "Thunder Road Guitars":    "#555",
    "Dream Guitars":           "#2e7d32",
    "Rumble Seat Music":       "#7b3f9e",
    "Fretted Americana":       "#8b4513",
    "Southside Guitars":       "#555",
}

# Instrument tab definitions — order matters for display
TABS = [
    {"label": "J-45",         "key": "j45",         "years": "1956–1965"},
    {"label": "Jaguar",       "key": "jaguar",       "years": "1958–1965"},
    {"label": "Jazzmaster",   "key": "jazzmaster",   "years": "1958–1965"},
    {"label": "Stratocaster", "key": "stratocaster", "years": "1962–1969"},
]


def _instrument_key(listing: dict) -> str:
    """Map a listing to one of our 4 tab keys."""
    instrument = (listing.get("instrument") or "").lower()
    title      = (listing.get("title") or "").lower()
    blob       = instrument + " " + title

    if "stratocaster" in blob or "strat" in blob:
        return "stratocaster"
    if "jazzmaster" in blob:
        return "jazzmaster"
    if "jaguar" in blob:
        return "jaguar"
    return "j45"  # default


def send_alerts(new_listings: list[dict], all_active: list[dict] = None) -> None:
    if not new_listings:
        return

    password = os.environ.get("GMAIL_APP_PASSWORD")
    if not password:
        print("[Email] No GMAIL_APP_PASSWORD set — skipping.")
        return

    count   = len(new_listings)
    subject = f"Guitar Hunter: {count} new listing{'s' if count != 1 else ''} found"
    html    = _build_html(new_listings)
    plain   = _build_plain(new_listings)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = GMAIL_SENDER
    msg["To"]      = NOTIFY_EMAIL
    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(html,  "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_SENDER, password)
            server.sendmail(GMAIL_SENDER, NOTIFY_EMAIL, msg.as_string())
            if SMS_EMAIL and "YOUR_10_DIGIT" not in SMS_EMAIL:
                _send_sms(server, new_listings)
        print(f"[Email] Sent alert for {count} new listings.")
    except Exception as e:
        print(f"[Email] Failed to send: {e}")


def _send_sms(server, new_listings: list[dict]) -> None:
    for l in new_listings:
        price_str = f"${l['price']:,.0f}" if l.get("price") else "POA"
        title     = (l.get("title") or "")[:60]
        source    = l.get("source") or ""
        url       = l.get("url") or ""
        body      = f"Guitar Hunter\n{title}\n{price_str} - {source}\n{url}"

        sms = MIMEText(body, "plain")
        sms["Subject"] = ""
        sms["From"]    = GMAIL_SENDER
        sms["To"]      = SMS_EMAIL
        try:
            server.sendmail(GMAIL_SENDER, SMS_EMAIL, sms.as_string())
            print(f"[SMS] Sent: {title[:40]}")
        except Exception as e:
            print(f"[SMS] Failed: {e}")


def _listing_card(l: dict) -> str:
    price_str    = f"${l['price']:,.0f}" if l.get("price") else "Price not listed"
    reasons      = l.get("match_reasons", [])
    score        = l.get("score", 0)
    source       = l.get("source", "")
    image_url    = l.get("image_url", "")
    url          = l.get("url", "")
    title        = l.get("title", "")
    source_color = SOURCE_COLORS.get(source, "#555")

    stars_filled = min(score, 5)
    stars_empty  = 5 - stars_filled
    stars_html = (
        f'<span style="color:#c8a84b;font-size:14px;">{"★" * stars_filled}</span>'
        f'<span style="color:#ddd;font-size:14px;">{"★" * stars_empty}</span>'
    )

    tags_html = "".join(
        f'<span style="display:inline-block;background:#eef6ee;color:#2d6a2d;'
        f'border-radius:4px;padding:2px 7px;font-size:10px;font-weight:500;'
        f'margin:2px 3px 2px 0;">{r}</span>'
        for r in reasons
    )

    source_badge = (
        f'<span style="display:inline-block;background:{source_color}15;'
        f'color:{source_color};border:1px solid {source_color}40;'
        f'border-radius:4px;padding:2px 7px;font-size:11px;font-weight:600;'
        f'margin-right:6px;">{source}</span>'
    )

    if image_url:
        image_block = (
            f'<td width="130" style="padding:0 16px 0 0;vertical-align:top;">'
            f'<a href="{url}"><img src="{image_url}" width="120" height="90"'
            f' style="border-radius:6px;object-fit:cover;display:block;border:1px solid #e8e4dc;" alt=""></a>'
            f'</td>'
        )
    else:
        image_block = (
            f'<td width="130" style="padding:0 16px 0 0;vertical-align:top;">'
            f'<div style="width:120px;height:90px;background:#f0ede8;border-radius:6px;'
            f'display:table-cell;text-align:center;vertical-align:middle;'
            f'font-size:28px;border:1px solid #e8e4dc;">🎸</div></td>'
        )

    return (
        '<tr><td style="padding:0 0 12px 0;">'
        '<table width="100%" cellpadding="0" cellspacing="0" style="'
        'background:#ffffff;border-radius:8px;border:2px solid #c8a84b;">'
        '<tr><td style="padding:16px 20px;">'
        '<table width="100%" cellpadding="0" cellspacing="0"><tr>'
        + image_block +
        '<td style="vertical-align:top;">'
        '<table width="100%" cellpadding="0" cellspacing="0">'
        '<tr>'
        f'<td><a href="{url}" style="font-size:15px;font-weight:600;color:#1a1a1a;'
        f'text-decoration:none;line-height:1.3;display:block;margin-bottom:6px;">{title}</a></td>'
        f'<td style="text-align:right;vertical-align:top;white-space:nowrap;padding-left:12px;">'
        f'<span style="font-size:22px;font-weight:700;color:#1a1a1a;letter-spacing:-0.5px;">{price_str}</span>'
        '</td></tr>'
        '<tr>'
        f'<td style="padding-bottom:8px;">{source_badge}{stars_html}</td>'
        f'<td style="text-align:right;vertical-align:top;">'
        f'<a href="{url}" style="display:inline-block;background:#1a1a1a;color:#fff;'
        f'font-size:12px;font-weight:500;padding:7px 14px;border-radius:5px;text-decoration:none;">View →</a>'
        '</td></tr>'
        f'<tr><td colspan="2">{tags_html}</td></tr>'
        '</table></td></tr></table></td></tr></table></td></tr>'
    )


def _section(title: str, listings: list[dict]) -> str:
    if not listings:
        return ""
    cards = "".join(_listing_card(l) for l in listings)
    count = len(listings)
    return (
        '<tr><td style="padding:16px 0 10px 0;">'
        '<span style="font-size:11px;font-weight:600;color:#c8a84b;'
        'text-transform:uppercase;letter-spacing:0.8px;">'
        f'✦ {title} ({count})'
        '</span></td></tr>'
        + cards +
        '<tr><td style="padding:4px 0 12px 0;">'
        '<table width="100%" cellpadding="0" cellspacing="0">'
        '<tr><td style="border-top:1px solid #e8e4dc;"></td></tr>'
        '</table></td></tr>'
    )


def _build_html(new_listings: list[dict]) -> str:
    # Group by instrument
    grouped = {tab["key"]: [] for tab in TABS}
    for l in new_listings:
        key = _instrument_key(l)
        grouped.setdefault(key, []).append(l)

    body = ""
    for tab in TABS:
        items = grouped.get(tab["key"], [])
        if items:
            body += _section(f"{tab['label']} ({tab['years']})", items)

    count      = len(new_listings)
    lowest     = min((l["price"] for l in new_listings if l.get("price")), default=None)
    lowest_str = f"${lowest:,.0f}" if lowest else "—"
    sources    = ", ".join(sorted({l.get("source", "") for l in new_listings}))

    # Build instrument summary line
    parts = []
    for tab in TABS:
        n = len(grouped.get(tab["key"], []))
        if n:
            parts.append(f"{tab['label']}: {n}")
    breakdown = " · ".join(parts)

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f0ede8;font-family:-apple-system,'Helvetica Neue',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f0ede8;padding:32px 16px;">
    <tr><td align="center">
      <table width="640" cellpadding="0" cellspacing="0" style="max-width:640px;width:100%;">
        <tr><td style="background:#1a1a1a;border-radius:8px 8px 0 0;padding:24px 32px;">
          <table width="100%" cellpadding="0" cellspacing="0"><tr>
            <td style="font-size:28px;width:44px;">🎸</td>
            <td style="padding-left:12px;">
              <div style="color:#fff;font-size:18px;font-weight:600;letter-spacing:-0.3px;">Guitar Hunter — {count} new listing{'s' if count != 1 else ''}</div>
              <div style="color:#888;font-size:13px;margin-top:2px;">{breakdown}</div>
            </td>
          </tr></table>
        </td></tr>
        <tr><td style="background:#f7f5f0;border-left:1px solid #e8e4dc;border-right:1px solid #e8e4dc;padding:14px 32px;">
          <table width="100%" cellpadding="0" cellspacing="0"><tr>
            <td style="font-size:12px;color:#888;"><strong style="color:#1a1a1a;font-size:15px;font-weight:600;display:block;">{count}</strong>New today</td>
            <td style="font-size:12px;color:#888;"><strong style="color:#1a1a1a;font-size:15px;font-weight:600;display:block;">{lowest_str}</strong>Lowest price</td>
            <td style="font-size:12px;color:#888;"><strong style="color:#1a1a1a;font-size:13px;font-weight:600;display:block;">{sources[:50]}</strong>Sources</td>
          </tr></table>
        </td></tr>
        <tr><td style="background:#f7f5f0;padding:16px 24px;border-left:1px solid #e8e4dc;border-right:1px solid #e8e4dc;">
          <table width="100%" cellpadding="0" cellspacing="0">
            {body}
          </table>
        </td></tr>
        <tr><td style="background:#f0ede8;border:1px solid #e8e4dc;border-top:none;border-radius:0 0 8px 8px;padding:16px 32px;">
          <p style="font-size:11px;color:#aaa;margin:0;line-height:1.6;">Guitar Hunter · Watching 15+ sources · Every 5 min</p>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""


def _build_plain(new_listings: list[dict]) -> str:
    grouped = {tab["key"]: [] for tab in TABS}
    for l in new_listings:
        key = _instrument_key(l)
        grouped.setdefault(key, []).append(l)

    lines = ["Guitar Hunter\n"]
    for tab in TABS:
        items = grouped.get(tab["key"], [])
        if not items:
            continue
        lines.append(f"\n{tab['label']} ({tab['years']})")
        lines.append("=" * 40)
        for l in items:
            price_str = f"${l['price']:,.0f}" if l.get("price") else "Price not listed"
            lines += [
                f"\n{l.get('title') or ''}",
                f"Source : {l.get('source') or ''}",
                f"Price  : {price_str}",
                f"URL    : {l.get('url') or ''}",
                "-" * 40,
            ]
    return "\n".join(lines)
