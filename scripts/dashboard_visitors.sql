-- Dashboard Visitors: tracks which phone number opened which generated website
-- Run this in Supabase SQL Editor

CREATE TABLE IF NOT EXISTS dashboard_visitors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone TEXT NOT NULL,
    org_slug TEXT NOT NULL,
    org_id UUID,
    org_name TEXT,
    last_source TEXT DEFAULT 'web',
    visit_count INTEGER DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_dashboard_visitors_phone ON dashboard_visitors(phone);
CREATE INDEX IF NOT EXISTS idx_dashboard_visitors_slug ON dashboard_visitors(org_slug);
CREATE UNIQUE INDEX IF NOT EXISTS idx_dashboard_visitors_phone_slug ON dashboard_visitors(phone, org_slug);

-- Add owner_phone to organizations if it does not exist (for OTP login)
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS owner_phone TEXT;
CREATE INDEX IF NOT EXISTS idx_organizations_owner_phone ON organizations(owner_phone);

-- Mobile sessions table (for app OTP login tokens)
CREATE TABLE IF NOT EXISTS mobile_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone TEXT NOT NULL,
    org_id UUID,
    token TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_mobile_sessions_token ON mobile_sessions(token);
