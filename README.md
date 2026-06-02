# 🎸 J45 Hunter

Monitors Reverb, eBay, GBase, 7 vintage dealer shops, Craigslist (18 cities), and the Acoustic Guitar Forum for your exact specs — every 20 minutes, 24/7, for free.

## Your Search Specs

| Setting | Value |
|---|---|
| **Models** | Gibson J-45, J-50, Country Western |
| **Years** | 1956–1965 |
| **Price** | $2,000–$7,500 |
| **Excluded** | Any listing mentioning `1 9/16"` nut |
| **Notification** | Gmail |

---

## Sources Monitored

| Source | Method |
|---|---|
| Reverb | Official API |
| eBay | Official API |
| GBase | Scraper |
| Gruhn Guitars | Scraper |
| Retrofret | Scraper |
| Carter Vintage | Scraper |
| Elderly Instruments | Scraper |
| Norman's Rare Guitars | Scraper |
| Dave's Guitar Shop | Scraper |
| Chicago Music Exchange | Scraper |
| Craigslist (18 cities) | RSS feed |
| Acoustic Guitar Forum | Scraper |

---

## Setup (One Time — ~15 minutes)

### Step 1 — Put the code on GitHub

1. Go to [github.com](https://github.com) and create a new **private** repository named `j45-hunter`
2. Upload all these files into it (drag and drop works, or use `git push`)

### Step 2 — Set up Gmail App Password

This lets the script send email *as* you without using your real password.

1. Make sure your Google account has **2-Step Verification** enabled
   - Go to [myaccount.google.com](https://myaccount.google.com) → Security → 2-Step Verification
2. Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
3. Create a new App Password — name it `j45-hunter`
4. Copy the 16-character password it gives you (you'll use it in Step 3)

### Step 3 — Add secrets to GitHub

In your GitHub repo, go to **Settings → Secrets and variables → Actions → New repository secret**

Add these secrets:

| Secret Name | Value |
|---|---|
| `GMAIL_APP_PASSWORD` | The 16-character App Password from Step 2 |
| `EBAY_APP_ID` | *(optional — see below)* |
| `EBAY_CERT_ID` | *(optional — see below)* |

### Step 4 — Edit config.py

Open `config.py` and update these two lines with your actual email addresses:

```python
NOTIFY_EMAIL = "YOUR_EMAIL@gmail.com"   # where you want alerts sent
GMAIL_SENDER  = "YOUR_GMAIL@gmail.com"  # the Gmail account sending them
```

Commit and push the change.

### Step 5 — That's it

GitHub Actions will pick up the `*/20 * * * *` schedule automatically. The hunter runs every 20 minutes from now on.

---

## eBay API (Optional but Recommended)

eBay has a free developer API that's more reliable than scraping. Takes 5 minutes to set up.

1. Go to [developer.ebay.com](https://developer.ebay.com) and create a free account
2. Create a new app — choose **Production** keys
3. Copy your **App ID (Client ID)** → add as `EBAY_APP_ID` secret
4. Copy your **Cert ID (Client Secret)** → add as `EBAY_CERT_ID` secret

Without these, eBay is simply skipped (you'll see a note in the logs).

---

## Running It Manually

You can trigger a run anytime from the GitHub Actions tab:

- **Normal run**: Actions → J45 Hunter → Run workflow → `test_mode: false`
- **Test run** (prints matches, no email, no state change): `test_mode: true`

Or run locally if you have Python 3.12+:

```bash
pip install -r requirements.txt

# Test run — see what matches right now
python hunt.py --test

# Normal run
GMAIL_APP_PASSWORD=your_app_password python hunt.py

# Reset seen listings (get alerted on all current matches again)
python hunt.py --reset
```

---

## How Alerts Work

When a new listing is found you'll get an email like this:

```
Subject: 🎸 J45 Hunter: 2 new listings found

[3★] 1962 Gibson J-45 Sunburst w/ Original Case
      Retrofret · $4,800
      Reasons: year mention: 1962, sunburst, original case

[1★] Gibson J-50 1959 — Clean!
      GBase · $3,200
      Reasons: year mention: 1959
```

Stars indicate how closely a listing matches your "nice to have" criteria (original tuners, all original, sunburst, no cracks, etc.).

---

## Adjusting Your Search

Edit `config.py` at any time:

- **Add/remove cities**: edit `CITIES` in `scrapers/craigslist.py`
- **Change year range**: `YEAR_MIN` / `YEAR_MAX`
- **Change price range**: `PRICE_MIN` / `PRICE_MAX`
- **Add exclusion terms**: `EXCLUDE_TERMS`
- **Add boost terms**: `BOOST_TERMS`

---

## Troubleshooting

**Not getting emails?**
- Check the Actions run log (GitHub → Actions → latest run) for errors
- Make sure `NOTIFY_EMAIL` and `GMAIL_SENDER` in `config.py` are correct
- Verify your Gmail App Password is set correctly in Secrets
- Check your spam folder once

**A dealer scraper stopped working?**
- Shop sites occasionally redesign. The scraper for that shop will just return 0 results.
- Open `scrapers/dealers.py`, find the shop, and update the CSS selectors.
- The other sources keep running fine in the meantime.

**Want to add a source?**
- Add a new file to `scrapers/` that exports a `fetch() -> list[dict]` function
- Each dict needs: `source`, `id`, `title`, `price`, `url`, `description`
- Import and add it to `SCRAPER_MODULES` in `hunt.py`
