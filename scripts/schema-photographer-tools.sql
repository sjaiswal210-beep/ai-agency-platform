-- ============================================
-- PHOTOGRAPHER MODULE - Complete Toolkit
-- ============================================

-- Portfolio Albums
CREATE TABLE IF NOT EXISTS photo_albums (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT,
    category TEXT DEFAULT 'wedding' CHECK (category IN ('wedding', 'pre_wedding', 'birthday', 'corporate', 'product', 'portrait', 'maternity', 'newborn', 'event', 'fashion', 'food', 'real_estate', 'other')),
    cover_url TEXT,
    is_public BOOLEAN DEFAULT true,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_photo_album_org ON photo_albums(organization_id);

-- Portfolio Photos
CREATE TABLE IF NOT EXISTS photo_portfolio (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    album_id UUID REFERENCES photo_albums(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    thumbnail_url TEXT,
    caption TEXT,
    is_featured BOOLEAN DEFAULT false,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_photo_port_org ON photo_portfolio(organization_id);
CREATE INDEX IF NOT EXISTS idx_photo_port_album ON photo_portfolio(album_id);

-- Client Events (shoots booked)
CREATE TABLE IF NOT EXISTS photo_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    client_name TEXT NOT NULL,
    client_phone TEXT,
    client_email TEXT,
    event_type TEXT DEFAULT 'wedding',
    event_date DATE NOT NULL,
    event_time TEXT,
    venue TEXT,
    duration_hours INTEGER DEFAULT 4,
    package_id UUID,
    status TEXT DEFAULT 'confirmed' CHECK (status IN ('inquiry', 'confirmed', 'completed', 'delivered', 'cancelled')),
    total_amount DECIMAL(10,2) DEFAULT 0,
    advance_paid DECIMAL(10,2) DEFAULT 0,
    balance_due DECIMAL(10,2) DEFAULT 0,
    notes TEXT,
    crew_members TEXT,
    equipment_needed TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_photo_event_org ON photo_events(organization_id);
CREATE INDEX IF NOT EXISTS idx_photo_event_date ON photo_events(event_date);
CREATE INDEX IF NOT EXISTS idx_photo_event_status ON photo_events(organization_id, status);

-- Packages / Pricing
CREATE TABLE IF NOT EXISTS photo_packages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    category TEXT DEFAULT 'wedding',
    price DECIMAL(10,2) NOT NULL,
    duration_hours INTEGER DEFAULT 4,
    deliverables TEXT,
    includes TEXT[] DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_photo_pkg_org ON photo_packages(organization_id);

-- Client Delivery (share albums with clients - password protected)
CREATE TABLE IF NOT EXISTS photo_deliveries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    event_id UUID REFERENCES photo_events(id) ON DELETE SET NULL,
    client_name TEXT NOT NULL,
    client_phone TEXT,
    access_code TEXT NOT NULL,
    title TEXT NOT NULL,
    photos JSONB DEFAULT '[]',
    photo_count INTEGER DEFAULT 0,
    download_enabled BOOLEAN DEFAULT true,
    watermark_enabled BOOLEAN DEFAULT false,
    expiry_date DATE,
    view_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_photo_del_org ON photo_deliveries(organization_id);
CREATE INDEX IF NOT EXISTS idx_photo_del_code ON photo_deliveries(access_code);

-- Equipment Tracker
CREATE TABLE IF NOT EXISTS photo_equipment (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    type TEXT DEFAULT 'camera' CHECK (type IN ('camera', 'lens', 'lighting', 'tripod', 'drone', 'audio', 'memory_card', 'battery', 'bag', 'prop', 'other')),
    brand TEXT,
    model TEXT,
    serial_number TEXT,
    purchase_date DATE,
    purchase_price DECIMAL(10,2),
    condition TEXT DEFAULT 'good' CHECK (condition IN ('new', 'good', 'fair', 'needs_repair')),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_photo_equip_org ON photo_equipment(organization_id);

-- Enquiry/Lead tracking for photographers
CREATE TABLE IF NOT EXISTS photo_enquiries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    phone TEXT,
    email TEXT,
    event_type TEXT,
    event_date DATE,
    venue TEXT,
    budget TEXT,
    message TEXT,
    status TEXT DEFAULT 'new' CHECK (status IN ('new', 'contacted', 'quotation_sent', 'confirmed', 'lost')),
    source TEXT DEFAULT 'website',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_photo_enq_org ON photo_enquiries(organization_id);
CREATE INDEX IF NOT EXISTS idx_photo_enq_status ON photo_enquiries(organization_id, status);

-- RLS
ALTER TABLE photo_albums ENABLE ROW LEVEL SECURITY;
ALTER TABLE photo_portfolio ENABLE ROW LEVEL SECURITY;
ALTER TABLE photo_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE photo_packages ENABLE ROW LEVEL SECURITY;
ALTER TABLE photo_deliveries ENABLE ROW LEVEL SECURITY;
ALTER TABLE photo_equipment ENABLE ROW LEVEL SECURITY;
ALTER TABLE photo_enquiries ENABLE ROW LEVEL SECURITY;

CREATE POLICY "service_all_photo_albums" ON photo_albums FOR ALL USING (true);
CREATE POLICY "service_all_photo_portfolio" ON photo_portfolio FOR ALL USING (true);
CREATE POLICY "service_all_photo_events" ON photo_events FOR ALL USING (true);
CREATE POLICY "service_all_photo_packages" ON photo_packages FOR ALL USING (true);
CREATE POLICY "service_all_photo_deliveries" ON photo_deliveries FOR ALL USING (true);
CREATE POLICY "service_all_photo_equipment" ON photo_equipment FOR ALL USING (true);
CREATE POLICY "service_all_photo_enquiries" ON photo_enquiries FOR ALL USING (true);

-- Add photographer tools to panel_tools
INSERT INTO panel_tools (id, name, icon, category, url_pattern, sort_order, is_default) VALUES
('portfolio', 'Portfolio', '📸', 'photographer', '/api/photo/{website_id}/portfolio', 19, false),
('client_gallery', 'Client Delivery', '📦', 'photographer', '/api/photo/{website_id}/delivery', 20, false),
('packages', 'Packages', '💰', 'photographer', '/api/photo/{website_id}/packages', 21, false),
('shoot_calendar', 'Shoot Calendar', '📅', 'photographer', '/api/photo/{website_id}/calendar', 22, false),
('enquiries', 'Enquiries', '📩', 'photographer', '/api/photo/{website_id}/enquiries', 23, false),
('equipment', 'Equipment', '📷', 'photographer', '/api/photo/{website_id}/equipment', 24, false),
('quotation', 'Quotation', '📝', 'photographer', '/api/photo/{website_id}/quotation', 25, false),
('photo_invoice', 'Invoice', '🧾', 'photographer', '/api/photo/{website_id}/invoice', 26, false)
ON CONFLICT (id) DO NOTHING;
