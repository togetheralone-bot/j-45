"""
Gmail notification — sends an email alert for new listings.
Uses Gmail's SMTP with an App Password (not your regular password).

Setup:
  1. Enable 2FA on your Google account
  2. Go to myaccount.google.com → Security → App Passwords
  3. Create a password for "Mail" / "Other (j45-hunter)"
  4. Add it as GMAIL_APP_PASSWORD in GitHub Actions secrets
"""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from config import NOTIFY_EMAIL, GMAIL_SENDER


def send_alerts(new_listings: list[dict]) -> None:
    if not new_listings:
        return

    password = os.environ.get("GMAIL_APP_PASSWORD")
    if not password:
        print("[Email] No GMAIL_APP_PASSWORD set — skipping notifications.")
        return

    subject = f"🎸 J45 Hunter: {len(new_listings)} new listing{'s' if len(new_listings) != 1 else ''} found"
    html    = _build_html(new_listings)
    plain   = _build_plain(new_listings)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = GMAIL_SENDER
    msg["To"]      = NOTIFY_EMAIL
    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_SENDER, password)
            server.sendmail(GMAIL_SENDER, NOTIFY_EMAIL, msg.as_string())
        print(f"[Email] Sent alert for {len(new_listings)} listing(s).")
    except Exception as e:
        print(f"[Email] Failed to send: {e}")


def _build_html(listings: list[dict]) -> str:
    rows = ""
    for l in listings:
        price_str = f"${l['price']:,.0f}" if l.get("price") else "Price not listed"
        reasons   = ", ".join(l.get("match_reasons", [])) or "—"
        score     = l.get("score", 0)
        stars     = "⭐" * min(score, 5)

        rows += f"""
        <tr>
          <td style="padding:12px;border-bottom:1px solid #eee;">
            <strong><a href="{l['url']}" style="color:#1a1a1a;text-decoration:none;">{l['title']}</a></strong><br>
            <span style="color:#888;font-size:13px;">{l['source']}</span>
          </td>
          <td style="padding:12px;border-bottom:1px solid #eee;white-space:nowrap;">
            <strong style="font-size:16px;">{price_str}</strong>
          </td>
          <td style="padding:12px;border-bottom:1px solid #eee;">
            {stars}<br>
            <span style="color:#888;font-size:12px;">{reasons}</span>
          </td>
          <td style="padding:12px;border-bottom:1px solid #eee;">
            <a href="{l['url']}" style="background:#1a1a1a;color:#fff;padding:6px 14px;border-radius:4px;text-decoration:none;font-size:13px;">View →</a>
          </td>
        </tr>
        """

    return f"""
    <html><body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;color:#1a1a1a;max-width:700px;margin:0 auto;padding:20px;">
      <h2 style="border-bottom:2px solid #1a1a1a;padding-bottom:10px;">🎸 J45 Hunter — New Listings</h2>
      <table style="width:100%;border-collapse:collapse;">
        <thead>
          <tr style="background:#f5f5f5;">
            <th style="padding:10px;text-align:left;">Listing</th>
            <th style="padding:10px;text-align:left;">Price</th>
            <th style="padding:10px;text-align:left;">Match Score</th>
            <th style="padding:10px;text-align:left;"></th>
          </tr>
        </thead>
        <tbody>{rows}</tbody>
      </table>
      <p style="color:#aaa;font-size:12px;margin-top:20px;">
        J45 Hunter · Watching: 1956–1965 · $2,000–$7,500 · J-45, J-50, Country Western
      </p>
    </body></html>
    """


def _build_plain(listings: list[dict]) -> str:
    lines = ["J45 Hunter — New Listings\n", "=" * 40]
    for l in listings:
        price_str = f"${l['price']:,.0f}" if l.get("price") else "Price not listed"
        lines.append(f"\n{l['title']}")
        lines.append(f"Source : {l['source']}")
        lines.append(f"Price  : {price_str}")
        lines.append(f"Score  : {l.get('score', 0)}")
        lines.append(f"URL    : {l['url']}")
        lines.append("-" * 40)
    return "\n".join(lines)
