-- J45 Hunter — Supabase Schema
-- Run this in the Supabase SQL editor after creating your project

-- Main listings table
create table if not exists listings (
  id            text primary key,          -- e.g. "reverb_12345"
  source        text not null,
  title         text not null,
  price         numeric,
  url           text not null,
  description   text,
  image_url     text,
  score         integer default 0,
  match_reasons text[],                    -- array of reason strings
  is_j45        boolean default false,     -- true = J-45, false = J-50/CW
  first_seen    timestamptz default now(),
  last_seen     timestamptz default now(),
  archived      boolean default false,
  archived_at   timestamptz
);

-- Index for fast queries
create index if not exists idx_listings_last_seen  on listings (last_seen desc);
create index if not exists idx_listings_archived   on listings (archived);
create index if not exists idx_listings_is_j45     on listings (is_j45);
create index if not exists idx_listings_source     on listings (source);

-- Enable Row Level Security (keep data private)
alter table listings enable row level security;

-- Allow full access via service role key (used by the scraper)
create policy "service_role_all" on listings
  for all using (true);
