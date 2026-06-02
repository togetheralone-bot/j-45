"""
Gmail notification — rich HTML email with new listings on top,
previous active results below.
"""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from config import NOTIFY_EMAIL, GMAIL_SENDER, SMS_EMAIL, SMS_EMAIL

SOURCE_COLORS = {
    "Reverb":                  "#e05c00",
    "eBay":                    "#0064d2",
    "GBase":                   "#2d6a2d",
    "Craigslist":              "#7b3f9e",
    "Facebook Marketplace":    "#1877f2",
    "Acoustic Guitar Forum":   "#8b4513",
    "Gruhn Guitars":           "#555",
    "Retrofret":               "#555",
    "Carter Vintage":          "#555",
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
    "Guitar Center":            "#c8102e",
    "The Gear Page":            "#2b5797",
    "Bernunzio Uptown Music":   "#8b6914",
    "Acoustic Vibes Music":     "#1b6ca8",
    "Matt Umanov Guitars":      "#555",
    "Thunder Road Guitars":     "#555",
    "Dream Guitars":            "#2e7d32",
    "Rumble Seat Music":        "#7b3f9e",
    "Fretted Americana":        "#8b4513",
    "Austin Vintage Guitars":   "#bf4300",
    "Rumble Seat Music":        "#7b3f9e",
}


def send_alerts(new_listings: list[dict], all_active: list[dict] = None) -> None:
    if not new_listings:
        return

    password = os.environ.get("GMAIL_APP_PASSWORD")
    if not password:
        print("[Email] No GMAIL_APP_PASSWORD set — skipping.")
        return

    all_active = all_active or []

    # Previous = active listings that are NOT in the new batch
    new_ids  = {l["id"] for l in new_listings}
    previous = [l for l in all_active if l["id"] not in new_ids]

    count   = len(new_listings)
    subject = f"🎸 J45 Hunter: {count} new listing{'s' if count != 1 else ''} found"
    html    = _build_html(new_listings, previous)
    plain   = _build_plain(new_listings, previous)

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
            # Also send SMS for each new listing if configured
            if SMS_EMAIL and SMS_EMAIL != "YOUR_10_DIGIT_NUMBER@tmomail.net":
                _send_sms(server, new_listings)
        print(f"[Email] Sent alert for {count} new + {len(previous)} previous listings.")
    except Exception as e:
        print(f"[Email] Failed to send: {e}")




def _send_sms(server, new_listings: list[dict]) -> None:
    """Send a brief SMS per new listing via T-Mobile email-to-SMS gateway."""
    for l in new_listings:
        price_str = ("$" + "{:,.0f}".format(l["price"])) if l.get("price") else "POA"
        title     = (l.get("title") or "")[:60]
        source    = l.get("source") or ""
        url       = l.get("url") or ""
        body      = "J45 Hunter\n" + title + "\n" + price_str + " - " + source + "\n" + url

        sms = MIMEText(body, "plain")
        sms["Subject"] = ""
        sms["From"]    = GMAIL_SENDER
        sms["To"]      = SMS_EMAIL
        try:
            server.sendmail(GMAIL_SENDER, SMS_EMAIL, sms.as_string())
            print("[SMS] Sent: " + title[:40])
        except Exception as e:
            print("[SMS] Failed: " + str(e))
