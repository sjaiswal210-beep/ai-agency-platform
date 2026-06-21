-- ============================================
-- WHATSAPP INTEGRATION - Per-business API config
-- ============================================

-- Each business stores their own WhatsApp API credentials
CREATE TABLE IF NOT EXISTS whatsapp_config (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    provider TEXT DEFAULT 'meta_cloud' CHECK (provider IN ('meta_cloud', 'wati', 'aisensy', 'interakt', 'twilio', 'gupshup', 'custom')),
    api_key TEXT,
    phone_number_id TEXT,
    business_account_id TEXT,
    access_token TEXT,
    webhook_verify_token TEXT,
    base_url TEXT,
    is_active BOOLEAN DEFAULT true,
    daily_limit INTEGER DEFAULT 1000,
    messages_sent_today INTEGER DEFAULT 0,
    last_reset_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(organization_id)
);
CREATE INDEX IF NOT EXISTS idx_wa_config_org ON whatsapp_config(organization_id);

-- Message templates (pre-approved templates)
CREATE TABLE IF NOT EXISTS whatsapp_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    category TEXT DEFAULT 'utility' CHECK (category IN ('utility', 'marketing', 'authentication')),
    trigger_event TEXT CHECK (trigger_event IN ('booking_confirmed', 'booking_reminder', 'payment_received', 'payment_due', 'invoice_sent', 'delivery_done', 'subscription_bill', 'renewal_reminder', 'follow_up', 'welcome', 'custom')),
    message_body TEXT NOT NULL,
    variables TEXT[] DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_wa_tmpl_org ON whatsapp_templates(organization_id);
CREATE INDEX IF NOT EXISTS idx_wa_tmpl_trigger ON whatsapp_templates(trigger_event);

-- Message log (track all sent messages)
CREATE TABLE IF NOT EXISTS whatsapp_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    template_id UUID REFERENCES whatsapp_templates(id),
    to_phone TEXT NOT NULL,
    to_name TEXT,
    message TEXT NOT NULL,
    trigger_event TEXT,
    status TEXT DEFAULT 'sent' CHECK (status IN ('queued', 'sent', 'delivered', 'read', 'failed')),
    error_message TEXT,
    sent_at TIMESTAMPTZ DEFAULT NOW(),
    delivered_at TIMESTAMPTZ,
    read_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_wa_msg_org ON whatsapp_messages(organization_id);
CREATE INDEX IF NOT EXISTS idx_wa_msg_date ON whatsapp_messages(sent_at DESC);
CREATE INDEX IF NOT EXISTS idx_wa_msg_status ON whatsapp_messages(status);

-- Automation rules (when to send what)
CREATE TABLE IF NOT EXISTS whatsapp_automations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    trigger_event TEXT NOT NULL,
    template_id UUID REFERENCES whatsapp_templates(id),
    delay_minutes INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    conditions JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_wa_auto_org ON whatsapp_automations(organization_id);

-- RLS
ALTER TABLE whatsapp_config ENABLE ROW LEVEL SECURITY;
ALTER TABLE whatsapp_templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE whatsapp_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE whatsapp_automations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "service_all_wa_config" ON whatsapp_config FOR ALL USING (true);
CREATE POLICY "service_all_wa_templates" ON whatsapp_templates FOR ALL USING (true);
CREATE POLICY "service_all_wa_messages" ON whatsapp_messages FOR ALL USING (true);
CREATE POLICY "service_all_wa_automations" ON whatsapp_automations FOR ALL USING (true);
