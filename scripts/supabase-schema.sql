-- ============================================
-- AI Agency Platform - Supabase Database Schema
-- Run this in Supabase SQL Editor
-- ============================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- LEADS TABLE
-- ============================================
CREATE TABLE leads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    business_name TEXT NOT NULL,
    phone TEXT,
    email TEXT,
    website TEXT,
    address TEXT,
    category TEXT,
    rating FLOAT,
    review_count INTEGER DEFAULT 0,
    source TEXT DEFAULT 'google_maps',
    status TEXT DEFAULT 'new' CHECK (status IN (
        'new', 'analyzed', 'outreach_sent', 'responded', 'interested', 'converted', 'lost'
    )),
    opportunity_score FLOAT,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- WEBSITES TABLE
-- ============================================
CREATE TABLE websites (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lead_id UUID REFERENCES leads(id) ON DELETE CASCADE,
    template TEXT NOT NULL,
    content JSONB,
    preview_url TEXT,
    deployed_url TEXT,
    status TEXT DEFAULT 'generating' CHECK (status IN (
        'generating', 'preview', 'approved', 'deployed'
    )),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- OUTREACH MESSAGES TABLE
-- ============================================
CREATE TABLE outreach_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lead_id UUID REFERENCES leads(id) ON DELETE CASCADE,
    channel TEXT NOT NULL CHECK (channel IN ('email', 'whatsapp')),
    message TEXT NOT NULL,
    status TEXT DEFAULT 'pending' CHECK (status IN (
        'pending', 'sent', 'delivered', 'read', 'replied', 'failed'
    )),
    sent_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- AGENT ACTIVITY LOGS
-- ============================================
CREATE TABLE agent_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_name TEXT NOT NULL,
    action TEXT NOT NULL,
    lead_id UUID REFERENCES leads(id) ON DELETE SET NULL,
    details JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- INDEXES
-- ============================================
CREATE INDEX idx_leads_status ON leads(status);
CREATE INDEX idx_leads_category ON leads(category);
CREATE INDEX idx_leads_score ON leads(opportunity_score DESC);
CREATE INDEX idx_leads_created ON leads(created_at DESC);
CREATE INDEX idx_websites_lead ON websites(lead_id);
CREATE INDEX idx_websites_status ON websites(status);
CREATE INDEX idx_outreach_lead ON outreach_messages(lead_id);
CREATE INDEX idx_outreach_status ON outreach_messages(status);
CREATE INDEX idx_agent_logs_agent ON agent_logs(agent_name);
CREATE INDEX idx_agent_logs_created ON agent_logs(created_at DESC);

-- ============================================
-- AUTO-UPDATE TRIGGER
-- ============================================
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER leads_updated_at
    BEFORE UPDATE ON leads
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ============================================
-- ROW LEVEL SECURITY
-- ============================================
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE websites ENABLE ROW LEVEL SECURITY;
ALTER TABLE outreach_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_logs ENABLE ROW LEVEL SECURITY;

-- Service role has full access (backend uses service key)
CREATE POLICY "Service full access leads" ON leads FOR ALL USING (true);
CREATE POLICY "Service full access websites" ON websites FOR ALL USING (true);
CREATE POLICY "Service full access outreach" ON outreach_messages FOR ALL USING (true);
CREATE POLICY "Service full access logs" ON agent_logs FOR ALL USING (true);
