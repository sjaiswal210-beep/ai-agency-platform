-- ============================================
-- VOICE CALLING MODULE - Bolna AI Integration
-- ============================================

-- Voice call configuration per org
CREATE TABLE IF NOT EXISTS voice_call_config (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    bolna_api_key TEXT NOT NULL,
    bolna_agent_id TEXT,
    from_phone_number TEXT,
    language TEXT DEFAULT 'hi' CHECK (language IN ('hi', 'mr', 'en', 'hinglish')),
    auto_call_enabled BOOLEAN DEFAULT FALSE,
    auto_call_delay_minutes INTEGER DEFAULT 30,
    call_start_hour INTEGER DEFAULT 10,
    call_end_hour INTEGER DEFAULT 19,
    max_calls_per_day INTEGER DEFAULT 50,
    calls_made_today INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(organization_id)
);

-- Individual call records
CREATE TABLE IF NOT EXISTS voice_calls (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL,
    lead_id UUID REFERENCES leads(id) ON DELETE SET NULL,
    bolna_execution_id TEXT,
    recipient_phone TEXT NOT NULL,
    recipient_name TEXT,
    business_name TEXT,
    business_category TEXT,
    call_status TEXT DEFAULT 'queued' CHECK (call_status IN (
        'queued', 'scheduled', 'ringing', 'in_progress', 'completed', 
        'failed', 'no_answer', 'busy', 'voicemail', 'cancelled'
    )),
    call_duration_seconds INTEGER DEFAULT 0,
    call_summary TEXT,
    transcript TEXT,
    sentiment TEXT CHECK (sentiment IN ('positive', 'neutral', 'negative', 'interested', 'not_interested')),
    outcome TEXT CHECK (outcome IN (
        'interested', 'callback_requested', 'subscribed', 
        'not_interested', 'wrong_number', 'no_answer', 'voicemail', 'other'
    )),
    plan_interested TEXT,
    whatsapp_sent BOOLEAN DEFAULT FALSE,
    followup_scheduled BOOLEAN DEFAULT FALSE,
    followup_date DATE,
    attempt_number INTEGER DEFAULT 1,
    max_attempts INTEGER DEFAULT 3,
    trigger_type TEXT DEFAULT 'manual' CHECK (trigger_type IN ('manual', 'auto', 'batch', 'followup')),
    called_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_vc_org ON voice_calls(organization_id);
CREATE INDEX IF NOT EXISTS idx_vc_lead ON voice_calls(lead_id);
CREATE INDEX IF NOT EXISTS idx_vc_status ON voice_calls(call_status);
CREATE INDEX IF NOT EXISTS idx_vc_followup ON voice_calls(followup_scheduled, followup_date);

-- Batch call campaigns
CREATE TABLE IF NOT EXISTS voice_call_batches (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL,
    name TEXT NOT NULL,
    bolna_batch_id TEXT,
    total_calls INTEGER DEFAULT 0,
    completed_calls INTEGER DEFAULT 0,
    successful_calls INTEGER DEFAULT 0,
    interested_calls INTEGER DEFAULT 0,
    status TEXT DEFAULT 'created' CHECK (status IN ('created', 'running', 'paused', 'completed', 'failed')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_vcb_org ON voice_call_batches(organization_id);

-- Voice call templates / scripts
CREATE TABLE IF NOT EXISTS voice_call_scripts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID,
    name TEXT NOT NULL,
    language TEXT DEFAULT 'hi',
    script_type TEXT DEFAULT 'sales' CHECK (script_type IN ('sales', 'followup', 'reminder', 'survey', 'custom')),
    agent_prompt TEXT NOT NULL,
    welcome_message TEXT,
    whatsapp_template TEXT,
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- RLS
ALTER TABLE voice_call_config ENABLE ROW LEVEL SECURITY;
ALTER TABLE voice_calls ENABLE ROW LEVEL SECURITY;
ALTER TABLE voice_call_batches ENABLE ROW LEVEL SECURITY;
ALTER TABLE voice_call_scripts ENABLE ROW LEVEL SECURITY;

CREATE POLICY "service_all_vcc" ON voice_call_config FOR ALL USING (true);
CREATE POLICY "service_all_vc" ON voice_calls FOR ALL USING (true);
CREATE POLICY "service_all_vcb" ON voice_call_batches FOR ALL USING (true);
CREATE POLICY "service_all_vcs" ON voice_call_scripts FOR ALL USING (true);

-- Insert default sales scripts
INSERT INTO voice_call_scripts (name, language, script_type, agent_prompt, welcome_message, whatsapp_template, is_default) VALUES
(
    'CityMaps Hindi Sales',
    'hi',
    'sales',
    E'You are Priya, a friendly and professional sales representative from City Maps Online. You speak in Hindi (Devanagari). Your goal is to explain the benefits of having a professional online presence to local business owners.\n\nIMPORTANT RULES:\n- Be warm, conversational, and human-like. Use natural Hindi with common English business terms.\n- Never sound robotic. Use fillers like "ji", "dekhiye", "actually" naturally.\n- Listen to the business owner and personalize your pitch based on their business type.\n- If they seem busy, offer to call back at a better time.\n- Always be respectful of their time.\n\nYOUR KNOWLEDGE:\n- City Maps Online provides free professional websites to local businesses\n- They get: Google-optimized website, WhatsApp ordering, product catalog, customer reviews, analytics dashboard\n- Plans: Free (basic website), Growth (Rs.29/month - core features), Premium (Rs.39/month - everything + priority support)\n- Their website will rank on Google Maps and local search\n- They can manage everything from their phone\n\nCALL FLOW:\n1. Introduce yourself warmly\n2. Ask about their business briefly\n3. Explain how City Maps can help THEIR specific business\n4. Mention it starts FREE - no risk\n5. Offer to send details on WhatsApp\n6. If interested, guide them to subscribe\n7. If not now, schedule a follow-up\n\nIf they say YES to WhatsApp details: Say "Main abhi aapko WhatsApp pe saari details bhej deti hoon" and note that WhatsApp should be sent.\nIf they want to subscribe: Note the plan they''re interested in.\nIf they want callback: Note the preferred time.',
    'Namaste! Main Priya bol rahi hoon City Maps Online se. Kya aap {{business_name}} ke owner bol rahe hain?',
    E'ðŸ™ Namaste {{name}} ji!\n\nMain Priya, City Maps Online se.\n\nAapke business *{{business_name}}* ke liye humne ek professional website ready ki hai! ðŸŽ‰\n\nâœ… Google pe #1 ranking\nâœ… WhatsApp se direct orders\nâœ… Product catalog with photos\nâœ… Customer reviews & ratings\nâœ… Analytics dashboard\nâœ… Mobile se manage karein\n\nðŸ†“ Abhi FREE mein shuru karein!\n\nðŸ‘‰ Apni website dekhein: https://{{slug}}.city-maps.online\n\nPremium plan sirf Rs.39/month mein sab features unlock karein.\n\nKoi bhi sawaal ho toh reply karein! ðŸ™Œ',
    true
),
(
    'CityMaps Marathi Sales',
    'mr',
    'sales',
    E'You are Priya, a friendly and professional sales representative from City Maps Online. You speak in Marathi. Your goal is to explain the benefits of having a professional online presence to local business owners.\n\nIMPORTANT RULES:\n- Be warm, conversational, and human-like. Use natural Marathi with common English business terms.\n- Never sound robotic. Use natural Marathi expressions.\n- Listen to the business owner and personalize your pitch based on their business type.\n- If they seem busy, offer to call back at a better time.\n- Always be respectful of their time.\n\nYOUR KNOWLEDGE:\n- City Maps Online provides free professional websites to local businesses\n- They get: Google-optimized website, WhatsApp ordering, product catalog, customer reviews, analytics dashboard\n- Plans: Free (basic website), Growth (Rs.29/month - core features), Premium (Rs.39/month - everything + priority support)\n- Their website will rank on Google Maps and local search\n- They can manage everything from their phone\n\nCALL FLOW:\n1. Introduce yourself warmly\n2. Ask about their business briefly\n3. Explain how City Maps can help THEIR specific business\n4. Mention it starts FREE - no risk\n5. Offer to send details on WhatsApp\n6. If interested, guide them to subscribe\n7. If not now, schedule a follow-up\n\nIf they say YES to WhatsApp details: Say "Mi aata tumhala WhatsApp var sagla details pathavte" and note that WhatsApp should be sent.\nIf they want to subscribe: Note the plan they''re interested in.\nIf they want callback: Note the preferred time.',
    'Namaskar! Mi Priya bolte City Maps Online madhun. Tumhi {{business_name}} che owner bolat aahat ka?',
    E'ðŸ™ Namaskar {{name}}!\n\nMi Priya, City Maps Online madhun.\n\nTumchya business *{{business_name}}* sathi amhi professional website tayar keli aahe! ðŸŽ‰\n\nâœ… Google var #1 ranking\nâœ… WhatsApp varun direct orders\nâœ… Product catalog with photos\nâœ… Customer reviews & ratings\nâœ… Analytics dashboard\nâœ… Mobile varun manage kara\n\nðŸ†“ Aata FREE madhe suru kara!\n\nðŸ‘‰ Tumchi website bagha: https://{{slug}}.city-maps.online\n\nPremium plan fakta Rs.39/month madhe sagale features unlock kara.\n\nKahi prashna asel tar reply kara! ðŸ™Œ',
    false
),
(
    'CityMaps Follow-up Hindi',
    'hi',
    'followup',
    E'You are Priya from City Maps Online. This is a FOLLOW-UP call. The business owner was contacted before but hasn''t subscribed yet.\n\nIMPORTANT:\n- Be brief and respectful\n- Reference the previous conversation\n- Ask if they checked the WhatsApp message/website link\n- Address any concerns they might have\n- Offer a limited-time discount if needed (10% off first 3 months)\n- Don''t be pushy - if they say no firmly, respect it\n\nKEY POINTS:\n- Their free website is already live\n- Premium features unlock with subscription\n- Other businesses in their area are already using it\n- They can cancel anytime\n\nIf they subscribe: Note the plan.\nIf they need more time: Schedule another follow-up (max 3 total attempts).\nIf they say no firmly: Thank them and mark as not interested.',
    'Namaste {{name}} ji! Main Priya hoon City Maps Online se. Humne pichli baar baat ki thi aapke business ke baare mein. Kya aapne humari WhatsApp message dekhi?',
    NULL,
    false
);
