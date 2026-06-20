-- ============================================
-- CUSTOM ORDER TRACKER MODULE
-- ============================================

CREATE TABLE IF NOT EXISTS custom_orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    order_number TEXT NOT NULL,
    customer_name TEXT NOT NULL,
    customer_phone TEXT,
    item_description TEXT NOT NULL,
    specifications JSONB DEFAULT '{}',
    reference_images JSONB DEFAULT '[]',
    measurements JSONB DEFAULT '{}',
    material TEXT,
    material_cost DECIMAL(10,2) DEFAULT 0,
    making_charges DECIMAL(10,2) DEFAULT 0,
    total_price DECIMAL(10,2) DEFAULT 0,
    advance_paid DECIMAL(10,2) DEFAULT 0,
    balance_due DECIMAL(10,2) DEFAULT 0,
    assigned_to TEXT,
    promised_date DATE,
    actual_delivery_date DATE,
    status TEXT DEFAULT 'received' CHECK (status IN ('received', 'design', 'material', 'production', 'finishing', 'quality_check', 'ready', 'delivered', 'alteration', 'cancelled')),
    progress_percent INTEGER DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_co_org ON custom_orders(organization_id);
CREATE INDEX IF NOT EXISTS idx_co_status ON custom_orders(organization_id, status);
CREATE INDEX IF NOT EXISTS idx_co_phone ON custom_orders(customer_phone);
CREATE INDEX IF NOT EXISTS idx_co_date ON custom_orders(promised_date);

CREATE TABLE IF NOT EXISTS customer_measurements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    customer_name TEXT NOT NULL,
    customer_phone TEXT NOT NULL,
    measurement_type TEXT DEFAULT 'body',
    data JSONB NOT NULL DEFAULT '{}',
    notes TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(organization_id, customer_phone, measurement_type)
);
CREATE INDEX IF NOT EXISTS idx_cm_org ON customer_measurements(organization_id);
CREATE INDEX IF NOT EXISTS idx_cm_phone ON customer_measurements(customer_phone);

CREATE TABLE IF NOT EXISTS design_catalog (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    category TEXT,
    images JSONB DEFAULT '[]',
    description TEXT,
    base_price DECIMAL(10,2),
    is_active BOOLEAN DEFAULT true,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_dc_org ON design_catalog(organization_id);

-- RLS
ALTER TABLE custom_orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE customer_measurements ENABLE ROW LEVEL SECURITY;
ALTER TABLE design_catalog ENABLE ROW LEVEL SECURITY;
CREATE POLICY "service_all_custom_orders" ON custom_orders FOR ALL USING (true);
CREATE POLICY "service_all_cm" ON customer_measurements FOR ALL USING (true);
CREATE POLICY "service_all_dc" ON design_catalog FOR ALL USING (true);

-- Register
INSERT INTO modules (id, name, description, icon, category, is_core, default_plans, sort_order, status)
VALUES ('custom_orders', 'Custom Orders', 'Track made-to-order items through production stages', 'ClipboardList', 'operations', false, '{pro,enterprise}', 16, 'active')
ON CONFLICT (id) DO NOTHING;

-- Templates
INSERT INTO industry_templates (id, name, description, icon, category, module_ids, sort_order)
VALUES 
('tailor', 'Tailor / Boutique', 'For tailors, boutiques, and alteration shops', 'Scissors', 'fashion', '{crm,custom_orders,billing,whatsapp,website,analytics}', 23),
('furniture_store', 'Furniture Store', 'For furniture manufacturing and retail', 'Armchair', 'retail', '{crm,custom_orders,inventory,billing,whatsapp,website,analytics}', 24),
('bakery_sweet', 'Bakery / Sweet Mart', 'For bakeries, sweet shops, custom cakes', 'Cake', 'food', '{crm,custom_orders,inventory,billing,whatsapp,website,analytics}', 25),
('jewellery', 'Jewellery Store', 'For jewellery making and retail', 'Gem', 'retail', '{crm,custom_orders,inventory,billing,whatsapp,website,analytics}', 26),
('printing_press', 'Printing Press', 'For printing, design, and branding services', 'Printer', 'service', '{crm,custom_orders,billing,whatsapp,website,analytics}', 27)
ON CONFLICT (id) DO NOTHING;

-- ============================================
-- CATALOG / DIGITAL MENU MODULE
-- ============================================

CREATE TABLE IF NOT EXISTS catalog_categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    image_url TEXT,
    sort_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_cat_cat_org ON catalog_categories(organization_id);

CREATE TABLE IF NOT EXISTS catalog_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    category_id UUID REFERENCES catalog_categories(id) ON DELETE SET NULL,
    name TEXT NOT NULL,
    description TEXT,
    price DECIMAL(10,2),
    compare_price DECIMAL(10,2),
    images JSONB DEFAULT '[]',
    variants JSONB DEFAULT '[]',
    tags TEXT[] DEFAULT '{}',
    in_stock BOOLEAN DEFAULT true,
    sort_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_cat_item_org ON catalog_items(organization_id);
CREATE INDEX IF NOT EXISTS idx_cat_item_cat ON catalog_items(category_id);

-- RLS
ALTER TABLE catalog_categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE catalog_items ENABLE ROW LEVEL SECURITY;
CREATE POLICY "service_all_cat_categories" ON catalog_categories FOR ALL USING (true);
CREATE POLICY "service_all_cat_items" ON catalog_items FOR ALL USING (true);

-- Register
INSERT INTO modules (id, name, description, icon, category, is_core, default_plans, sort_order, status)
VALUES ('catalog', 'Catalog / Menu', 'Digital product catalog shareable via WhatsApp', 'ShoppingBag', 'operations', false, '{starter,pro,enterprise}', 17, 'active')
ON CONFLICT (id) DO NOTHING;

-- Templates
INSERT INTO industry_templates (id, name, description, icon, category, module_ids, sort_order)
VALUES 
('clothing_fashion', 'Clothing / Fashion', 'For clothing stores and fashion boutiques', 'Shirt', 'fashion', '{crm,catalog,custom_orders,billing,whatsapp,website,analytics}', 28),
('gift_shop', 'Gift Shop', 'For gift shops, novelty stores', 'Gift', 'retail', '{crm,catalog,custom_orders,billing,whatsapp,website,analytics}', 29),
('electrical_shop', 'Electrical Shop', 'For electrical and electronics retail', 'Zap', 'retail', '{crm,catalog,inventory,billing,whatsapp,website,analytics}', 30),
('medical_shop', 'Medical / Pharmacy', 'For pharmacies and medical stores', 'Pill', 'healthcare', '{crm,catalog,inventory,billing,whatsapp,website,analytics}', 31)
ON CONFLICT (id) DO NOTHING;
