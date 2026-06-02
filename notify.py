"""
Gmail notification — rich HTML email with new listings on top,
previous active results below.
"""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from config import NOTIFY_EMAIL, GMAIL_SENDER

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
        print(f"[Email] Sent alert for {count} new + {len(previous)} previous listings.")
    except Exception as e:
        print(f"[Email] Failed to send: {e}")


def _listing_card(l: dict, compact: bool = False) -> str:
    """Render a single listing card. compact=True for the previous section."""
    archived     = l.get("archived", False)
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
    stars_html   = (
        f'<span style="color:#c8a84b;font-size:{"12" if compact else "14"}px;">' + "★" * stars_filled + '</span>'
        f'<span style="color:#ddd;font-size:{"12" if compact else "14"}px;">'    + "★" * stars_empty  + '</span>'
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

    archived_style = 'opacity:0.45;filter:grayscale(0.4);' if archived else ''

    if compact:
        # Compact row — same image logic as full card, slightly smaller
        if image_url:
            compact_image = f'''
              <td width="90" style="padding:0 12px 0 0;vertical-align:top;">
                <a href="{url}">
                  <img src="{image_url}" width="80" height="60"
                       style="border-radius:5px;object-fit:cover;display:block;
                              border:1px solid #e8e4dc;" alt="{title}">
                </a>
              </td>'''
        else:
            compact_image = '''
              <td width="90" style="padding:0 12px 0 0;vertical-align:top;">
                <div style="width:80px;height:60px;background:#f0ede8;border-radius:5px;
                            display:table-cell;text-align:center;vertical-align:middle;
                            font-size:20px;border:1px solid #e8e4dc;">🎸</div>
              </td>'''

        return f'''
        <tr>
          <td style="padding:0 0 8px 0;">
            <table width="100%" cellpadding="0" cellspacing="0" style="
              background:#fafafa;border-radius:6px;
              border:1px solid #ece9e2;{archived_style}">
              <tr>
                <td style="padding:12px 16px;">
                  <table width="100%" cellpadding="0" cellspacing="0">
                    <tr>
                      {compact_image}
                      <td>
                        <a href="{url}" style="font-size:13px;font-weight:600;
                          color:#1a1a1a;text-decoration:none;line-height:1.3;
                          display:block;margin-bottom:4px;">{title}</a>
                        <div style="margin-bottom:5px;">
                          {source_badge}{stars_html}
                        </div>
                        <div>{tags_html}</div>
                      </td>
                      <td style="text-align:right;vertical-align:top;
                                 white-space:nowrap;padding-left:12px;">
                        <div style="font-size:18px;font-weight:700;color:#1a1a1a;
                                    letter-spacing:-0.5px;margin-bottom:6px;">{price_str}</div>
                        <a href="{url}" style="display:inline-block;background:#555;
                          color:#fff;font-size:11px;font-weight:500;padding:5px 11px;
                          border-radius:4px;text-decoration:none;">View →</a>
                      </td>
                    </tr>
                  </table>
                </td>
              </tr>
            </table>
          </td>
        </tr>'''
    else:
        # Full card — with image
        if image_url:
            image_block = f'''
              <td width="130" style="padding:0 16px 0 0;vertical-align:top;">
                <a href="{url}">
                  <img src="{image_url}" width="120" height="90"
                       style="border-radius:6px;object-fit:cover;display:block;
                              border:1px solid #e8e4dc;" alt="{title}">
                </a>
              </td>'''
        else:
            image_block = '''
              <td width="130" style="padding:0 16px 0 0;vertical-align:top;">
                <div style="width:120px;height:90px;background:#f0ede8;border-radius:6px;
                            display:table-cell;text-align:center;vertical-align:middle;
                            font-size:28px;border:1px solid #e8e4dc;">🎸</div>
              </td>'''

        return f'''
        <tr>
          <td style="padding:0 0 12px 0;">
            <table width="100%" cellpadding="0" cellspacing="0" style="
              background:#ffffff;border-radius:8px;
              border:2px solid #c8a84b;{archived_style}">
              <tr>
                <td style="padding:16px 20px;">
                  <table width="100%" cellpadding="0" cellspacing="0">
                    <tr>
                      {image_block}
                      <td style="vertical-align:top;">
                        <table width="100%" cellpadding="0" cellspacing="0">
                          <tr>
                            <td>
                              <a href="{url}" style="font-size:15px;font-weight:600;
                                color:#1a1a1a;text-decoration:none;line-height:1.3;
                                display:block;margin-bottom:6px;">{title}</a>
                            </td>
                            <td style="text-align:right;vertical-align:top;
                                       white-space:nowrap;padding-left:12px;">
                              <span style="font-size:22px;font-weight:700;color:#1a1a1a;
                                           letter-spacing:-0.5px;">{price_str}</span>
                            </td>
                          </tr>
                          <tr>
                            <td style="padding-bottom:8px;">
                              {source_badge}{stars_html}
                            </td>
                            <td style="text-align:right;vertical-align:top;">
                              <a href="{url}" style="display:inline-block;background:#1a1a1a;
                                color:#fff;font-size:12px;font-weight:500;padding:7px 14px;
                                border-radius:5px;text-decoration:none;">View →</a>
                            </td>
                          </tr>
                          <tr>
                            <td colspan="2">{tags_html}</td>
                          </tr>
                        </table>
                      </td>
                    </tr>
                  </table>
                </td>
              </tr>
            </table>
          </td>
        </tr>'''


def _is_j45(l: dict) -> bool:
    blob = f"{l.get('title','')} {l.get('description','')}".lower()
    return "j-45" in blob or "j45" in blob or "country western" in blob


def _section(title: str, listings: list[dict], compact: bool, gold: bool = False) -> str:
    if not listings:
        return ""
    color  = "#c8a84b" if gold else "#888"
    prefix = "✦ " if gold else ""
    cards  = "".join(_listing_card(l, compact=compact) for l in listings)
    return f'''
        <tr><td style="padding:16px 0 10px 0;">
          <span style="font-size:11px;font-weight:600;color:{color};
                       text-transform:uppercase;letter-spacing:0.8px;">{prefix}{title}</span>
        </td></tr>
        {cards}
        <tr><td style="padding:4px 0 12px 0;">
          <table width="100%" cellpadding="0" cellspacing="0">
            <tr><td style="border-top:1px solid #e8e4dc;"></td></tr>
          </table>
        </td></tr>'''


def _build_html(new_listings: list[dict], previous: list[dict]) -> str:
    new_j45   = [l for l in new_listings if     _is_j45(l)]
    new_other = [l for l in new_listings if not _is_j45(l)]
    prev_j45  = [l for l in previous     if     _is_j45(l)]
    prev_other= [l for l in previous     if not _is_j45(l)]

    body = ""
    body += _section(f"New listings — J-45 ({len(new_j45)})",              new_j45,    compact=False, gold=True)
    body += _section(f"New listings — J-50 & Country Western ({len(new_other)})", new_other, compact=False, gold=True)
    body += _section(f"Previous listings — J-45 ({len(prev_j45)})",        prev_j45,   compact=True,  gold=False)
    body += _section(f"Previous listings — J-50 & Country Western ({len(prev_other)})", prev_other, compact=True, gold=False)

    lowest     = min((l["price"] for l in new_listings if l.get("price")), default=None)
    lowest_str = f"${lowest:,.0f}" if lowest else "—"
    sources    = ", ".join(sorted({l.get("source", "") for l in new_listings}))
    count      = len(new_listings)

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f0ede8;
             font-family:-apple-system,'Helvetica Neue',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0"
         style="background:#f0ede8;padding:32px 16px;">
    <tr><td align="center">
      <table width="640" cellpadding="0" cellspacing="0" style="max-width:640px;width:100%;">

        <!-- Header -->
        <tr><td style="background:#1a1a1a;border-radius:8px 8px 0 0;padding:24px 32px;">
          <table width="100%" cellpadding="0" cellspacing="0"><tr>
            <td style="font-size:28px;width:44px;">🎸</td>
            <td style="padding-left:12px;">
              <div style="color:#fff;font-size:18px;font-weight:600;letter-spacing:-0.3px;">
                J45 Hunter — {count} new listing{'s' if count != 1 else ''}
              </div>
              <div style="color:#888;font-size:13px;margin-top:2px;">
                1956–1965 · $2,000–$7,500 · J-45, J-50, Country Western
              </div>
            </td>
          </tr></table>
        </td></tr>

        <!-- Summary bar -->
        <tr><td style="background:#f7f5f0;
                        border-left:1px solid #e8e4dc;border-right:1px solid #e8e4dc;
                        padding:14px 32px;">
          <table width="100%" cellpadding="0" cellspacing="0"><tr>
            <td style="font-size:12px;color:#888;">
              <strong style="color:#1a1a1a;font-size:15px;font-weight:600;
                             display:block;">{count}</strong>New today
            </td>
            <td style="font-size:12px;color:#888;">
              <strong style="color:#1a1a1a;font-size:15px;font-weight:600;
                             display:block;">{lowest_str}</strong>Lowest new
            </td>
            <td style="font-size:12px;color:#888;">
              <strong style="color:#1a1a1a;font-size:13px;font-weight:600;
                             display:block;">{sources[:40]}</strong>Sources
            </td>
            <td style="font-size:12px;color:#888;">
              <strong style="color:#1a1a1a;font-size:15px;font-weight:600;
                             display:block;">{len(previous)}</strong>Still active
            </td>
          </tr></table>
        </td></tr>

        <!-- Body -->
        <tr><td style="background:#f7f5f0;padding:16px 24px;
                        border-left:1px solid #e8e4dc;border-right:1px solid #e8e4dc;">
          <table width="100%" cellpadding="0" cellspacing="0">

            {body}

          </table>
        </td></tr>

        <!-- Footer -->
        <tr><td style="background:#f0ede8;border:1px solid #e8e4dc;border-top:none;
                        border-radius:0 0 8px 8px;padding:16px 32px;">
          <p style="font-size:11px;color:#aaa;margin:0;line-height:1.6;">
            J45 Hunter · Watching 12 sources · Every 20 min
          </p>
        </td></tr>

      </table>
    </td></tr>
  </table>
</body>
</html>"""


def _plain_section(title: str, listings: list[dict]) -> list[str]:
    if not listings:
        return []
    lines = [f"\n{title}", "=" * 40]
    for l in listings:
        price_str = f"${l['price']:,.0f}" if l.get("price") else "Price not listed"
        lines += [f"\n{l['title']}", f"Source : {l.get('source','')}",
                  f"Price  : {price_str}", f"URL    : {l.get('url','')}", "-" * 40]
    return lines


def _build_plain(new_listings: list[dict], previous: list[dict]) -> str:
    new_j45    = [l for l in new_listings if     _is_j45(l)]
    new_other  = [l for l in new_listings if not _is_j45(l)]
    prev_j45   = [l for l in previous     if     _is_j45(l)]
    prev_other = [l for l in previous     if not _is_j45(l)]

    lines = ["J45 Hunter\n"]
    lines += _plain_section("NEW — J-45", new_j45)
    lines += _plain_section("NEW — J-50 & Country Western", new_other)
    lines += _plain_section("PREVIOUS — J-45", prev_j45)
    lines += _plain_section("PREVIOUS — J-50 & Country Western", prev_other)
    return "\n".join(lines)
