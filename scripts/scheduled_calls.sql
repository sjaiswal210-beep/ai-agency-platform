-- Scheduled follow-up calls (fired ~10 min after a website is generated)
-- Run this in Supabase SQL Editor

CREATE TABLE IF NOT EXISTS scheduled_calls (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone TEXT NOT NULL,
    business_name TEXT,
    owner_name TEXT,
    category TEXT,
    slug TEXT,
    lead_id UUID,
    org_id UUID,
    call_at TIMESTAMPTZ NOT NULL,
    status TEXT DEFAULT 'pending',  -- pending | done | failed | cancelled
    attempts INTEGER DEFAULT 0,
    last_error TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_scheduled_calls_due ON scheduled_calls(status, call_at);
