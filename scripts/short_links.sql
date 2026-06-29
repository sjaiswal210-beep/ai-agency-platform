-- Short links for clean dashboard/panel URLs in messages
-- Run this in Supabase SQL Editor

CREATE TABLE IF NOT EXISTS short_links (
    code TEXT PRIMARY KEY,
    target_url TEXT NOT NULL,
    clicks INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now()
);
