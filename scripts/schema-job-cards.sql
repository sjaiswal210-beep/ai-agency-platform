-- ============================================
-- JOB CARD / SERVICE TICKET MODULE
-- ============================================

CREATE TABLE IF NOT EXISTS job_cards (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    job_number TEXT NOT NULL,
    customer_name TEXT NOT NULL,
    customer_phone TEXT,
    customer_address TEXT,
    device_type TEXT DEFAULT 'other' CHECK (device_type IN ('vehicle_2w', 'vehicle_4w', 'mobile', 'laptop', 'appliance', 'electrical', 'plumbing', 'ac_hvac', 'cctv', 'other')),
    device_brand TEXT,
    device_model TEXT,
    registration_no TEXT,
    serial_number TEXT,
    problem_description TEXT NOT NULL,
    diagnosis_notes TEXT,
    assigned_to TEXT,
    priority TEXT DEFAULT 'normal' CHECK (priority IN ('normal', 'urgent', 'emergency')),
    status TEXT DEFAULT 'received' CHECK (status IN ('received', 'diagnosed', 'awaiting_parts', 'in_progress', 'quality_check', 'ready', 'delivered', 'cancelled')),
    estimated_cost DECIMAL(10,2),
    estimated_hours INTEGER,
    parts_cost DECIMAL(10,2) DEFAULT 0,
    labor_cost DECIMAL(10,2) DEFAULT 0,
    total_cost DECIMAL(10,2) DEFAULT 0,
    advance_paid DECIMAL(10,2) DEFAULT 0,
    warranty_until DATE,
    photos JSONB DEFAULT '[]',
    received_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    delivered_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_jc_org ON job_cards(organization_id);
CREATE INDEX IF NOT EXISTS idx_jc_status ON job_cards(organization_id, status);
CREATE INDEX IF NOT EXISTS idx_jc_phone ON job_cards(customer_phone);
CREATE INDEX IF NOT EXISTS idx_jc_number ON job_cards(organization_id, job_number);

CREATE TABLE IF NOT EXISTS job_parts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_card_id UUID NOT NULL REFERENCES job_cards(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL,
    part_name TEXT NOT NULL,
    quantity INTEGER DEFAULT 1,
    unit_price DECIMAL(10,2) DEFAULT 0,
    total_price DECIMAL(10,2) DEFAULT 0,
    source TEXT DEFAULT 'stock' CHECK (source IN ('stock', 'ordered', 'customer_provided')),
    vendor TEXT,
    status TEXT DEFAULT 'installed' CHECK (status IN ('available', 'ordered', 'received', 'installed')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_jp_job ON job_parts(job_card_id);

CREATE TABLE IF NOT EXISTS job_status_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_card_id UUID NOT NULL REFERENCES job_cards(id) ON DELETE CASCADE,
    from_status TEXT,
    to_status TEXT NOT NULL,
    changed_by TEXT,
    notes TEXT,
    photo_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_jsh_job ON job_status_history(job_card_id);

CREATE TABLE IF NOT EXISTS service_reminders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    customer_name TEXT NOT NULL,
    customer_phone TEXT NOT NULL,
    device_info TEXT,
    reminder_type TEXT DEFAULT 'service_due' CHECK (reminder_type IN ('service_due', 'amc', 'insurance', 'puc', 'warranty', 'followup')),
    due_date DATE NOT NULL,
    message TEXT,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'completed', 'skipped')),
    recurrence TEXT DEFAULT 'none' CHECK (recurrence IN ('none', 'monthly', 'quarterly', 'half_yearly', 'yearly')),
    last_sent_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_sr_org ON service_reminders(organization_id);
CREATE INDEX IF NOT EXISTS idx_sr_due ON service_reminders(due_date);
CREATE INDEX IF NOT EXISTS idx_sr_status ON service_reminders(status);

CREATE TABLE IF NOT EXISTS technicians (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    phone TEXT,
    specialization TEXT,
    is_active BOOLEAN DEFAULT true,
    active_jobs INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_tech_org ON technicians(organization_id);

-- RLS
ALTER TABLE job_cards ENABLE ROW LEVEL SECURITY;
ALTER TABLE job_parts ENABLE ROW LEVEL SECURITY;
ALTER TABLE job_status_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE service_reminders ENABLE ROW LEVEL SECURITY;
ALTER TABLE technicians ENABLE ROW LEVEL SECURITY;

CREATE POLICY "service_all_job_cards" ON job_cards FOR ALL USING (true);
CREATE POLICY "service_all_job_parts" ON job_parts FOR ALL USING (true);
CREATE POLICY "service_all_jsh" ON job_status_history FOR ALL USING (true);
CREATE POLICY "service_all_sr" ON service_reminders FOR ALL USING (true);
CREATE POLICY "service_all_techs" ON technicians FOR ALL USING (true);

-- Register module
INSERT INTO modules (id, name, description, icon, category, is_core, default_plans, sort_order, status)
VALUES ('job_cards', 'Job Cards', 'Service tickets for repair, maintenance, and field service', 'Wrench', 'operations', false, '{pro,enterprise}', 15, 'active')
ON CONFLICT (id) DO NOTHING;

-- Industry templates
INSERT INTO industry_templates (id, name, description, icon, category, module_ids, sort_order)
VALUES 
('garage_bike', 'Garage / Bike Service', 'For bike and car service centers', 'Wrench', 'automotive', '{crm,job_cards,inventory,billing,whatsapp,website,analytics}', 18),
('mobile_repair', 'Mobile / Computer Repair', 'For mobile and laptop repair shops', 'Smartphone', 'repair', '{crm,job_cards,inventory,billing,whatsapp,website,analytics}', 19),
('ac_repair', 'AC / Appliance Repair', 'For AC, fridge, washing machine service', 'Thermometer', 'repair', '{crm,job_cards,billing,whatsapp,website,analytics}', 20),
('electrician_service', 'Electrician Service', 'For electrician and wiring services', 'Zap', 'service', '{crm,job_cards,billing,whatsapp,website,analytics}', 21),
('plumber_service', 'Plumber Service', 'For plumbing and water services', 'Droplets', 'service', '{crm,job_cards,billing,whatsapp,website,analytics}', 22)
ON CONFLICT (id) DO NOTHING;
