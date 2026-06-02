# J45 Hunter UI — Setup Guide

## Step 1 — Supabase

1. Go to supabase.com and create a free account
2. Click "New project" — name it `j45-hunter`
3. Once created, go to the SQL editor (left sidebar)
4. Paste and run the contents of `supabase_schema.sql` (in the scraper repo)
5. Go to Project Settings → API and copy:
   - **Project URL** — looks like `https://xxxx.supabase.co`
   - **anon/public key** — long JWT string
   - **service_role key** — different long JWT string (keep this secret)

## Step 2 — Add Supabase secrets to GitHub Actions (scraper)

In your j45-hunter GitHub repo → Settings → Secrets → Actions, add:
- `SUPABASE_URL` = your Project URL
- `SUPABASE_KEY` = your **service_role** key

## Step 3 — Deploy UI to Vercel

1. Go to vercel.com and create a free account
2. Click "Add New Project"
3. Upload this `j45-hunter-ui` folder (or push it to a GitHub repo and import it)
4. Under "Environment Variables" add:
   - `NEXT_PUBLIC_SUPABASE_URL` = your Project URL (same as above)
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY` = your **anon/public** key
   - `SUPABASE_SERVICE_KEY` = your **service_role** key
5. Click Deploy

Vercel will give you a URL like `j45-hunter-ui.vercel.app`.

## Step 4 — Run the scraper once

Trigger a manual normal run from GitHub Actions.
This populates the database for the first time.
Then open your Vercel URL — you should see all current listings.

## How archiving works

- Click **Archive** on any listing card
- It disappears from the active feed immediately
- The next email will still show it but greyed out
- Click **Show archived** at the bottom to see and restore archived listings
