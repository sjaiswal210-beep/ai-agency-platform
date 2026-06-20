-- ============================================
-- SUBSCRIPTION MANAGER MODULE - Database Schema
-- ============================================

-- Subscription Products (milk, tiffin, water can, newspaper)
CREATE TABLE IF NOT EXISTS subscription_products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    unit TEXT DEFAULT 'pcs',
    price DECIMAL(10,2) NOT NULL,
    category TEXT,
    is_available BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_sub_prod_org ON subscription_products(organization_id);

-- Customer Subscriptions
CREATE TABLE IF NOT EXISTS subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    customer_name TEXT NOT NULL,
    customer_phone TEXT NOT NULL,
    address TEXT,
    locality TEXT,
    product_id UUID REFERENCES subscription_products(id),
    product_name TEXT,
    quantity DECIMAL(6,2) DEFAULT 1,
    frequency TEXT DEFAULT 'daily' CHECK (frequency IN ('daily', 'alternate', 'weekdays', 'custom', 'weekly', 'monthly')),
    custom_days TEXT[] DEFAULT '{}',
    price_per_unit DECIMAL(10,2),
    monthly_estimate DECIMAL(10,2),
    route_id UUID,
    route_sequence INTEGER DEFAULT 0,
    delivery_boy_id UUID,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'paused', 'cancelled')),
    pause_from DATE,
    pause_until DATE,
    start_date DATE DEFAULT CURRENT_DATE,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_sub_org ON subscriptions(organization_id);
CREATE INDEX IF NOT EXISTS idx_sub_status ON subscriptions(organization_id, status);
CREATE INDEX IF NOT EXISTS idx_sub_phone ON subscriptions(customer_phone);
CREATE INDEX IF NOT EXISTS idx_sub_route ON subscriptions(route_id);

-- Delivery Log (daily records)
CREATE TABLE IF NOT EXISTS subscription_deliveries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    subscription_id UUID NOT NULL REFERENCES subscriptions(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    quantity DECIMAL(6,2),
    status TEXT DEFAULT 'delivered' CHECK (status IN ('delivered', 'skipped', 'extra', 'holiday', 'not_home', 'paused')),
    delivery_boy_id UUID,
    delivered_at TIMESTAMPTZ,
    notes TEXT,
    UNIQUE(subscription_id, date)
);
CREATE INDEX IF NOT EXISTS idx_sub_del_org ON subscription_deliveries(organization_id);
CREATE INDEX IF NOT EXISTS idx_sub_del_date ON subscription_deliveries(organization_id, date);
CREATE INDEX IF NOT EXISTS idx_sub_del_sub ON subscription_deliveries(subscription_id, date);

-- Monthly Bills
CREATE TABLE IF NOT EXISTS subscription_bills (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    subscription_id UUID REFERENCES subscriptions(id),
    customer_name TEXT NOT NULL,
    customer_phone TEXT NOT NULL,
    month INTEGER NOT NULL,
    year INTEGER NOT NULL,
    total_deliveries INTEGER DEFAULT 0,
    total_quantity DECIMAL(8,2) DEFAULT 0,
    rate DECIMAL(10,2),
    subtotal DECIMAL(10,2) DEFAULT 0,
    extras_amount DECIMAL(10,2) DEFAULT 0,
    deductions DECIMAL(10,2) DEFAULT 0,
    final_amount DECIMAL(10,2) DEFAULT 0,
    status TEXT DEFAULT 'generated' CHECK (status IN ('generated', 'sent', 'paid', 'partial', 'overdue')),
    paid_amount DECIMAL(10,2) DEFAULT 0,
    paid_date DATE,
    payment_method TEXT,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(subscription_id, month, year)
);
CREATE INDEX IF NOT EXISTS idx_sub_bill_org ON subscription_bills(organization_id);
CREATE INDEX IF NOT EXISTS idx_sub_bill_month ON subscription_bills(organization_id, year, month);
CREATE INDEX IF NOT EXISTS idx_sub_bill_status ON subscription_bills(status);

-- Delivery Routes
CREATE TABLE IF NOT EXISTS subscription_routes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    area TEXT,
    delivery_boy_name TEXT,
    delivery_boy_phone TEXT,
    customer_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_sub_route_org ON subscription_routes(organization_id);

-- Delivery Boys
CREATE TABLE IF NOT EXISTS subscription_delivery_boys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    phone TEXT,
    vehicle_type TEXT,
    routes TEXT[] DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_sub_dboy_org ON subscription_delivery_boys(organization_id);

-- RLS
ALTER TABLE subscription_products ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscription_deliveries ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscription_bills ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscription_routes ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscription_delivery_boys ENABLE ROW LEVEL SECURITY;

CREATE POLICY "service_all_sub_products" ON subscription_products FOR ALL USING (true);
CREATE POLICY "service_all_subscriptions" ON subscriptions FOR ALL USING (true);
CREATE POLICY "service_all_sub_deliveries" ON subscription_deliveries FOR ALL USING (true);
CREATE POLICY "service_all_sub_bills" ON subscription_bills FOR ALL USING (true);
CREATE POLICY "service_all_sub_routes" ON subscription_routes FOR ALL USING (true);
CREATE POLICY "service_all_sub_dboys" ON subscription_delivery_boys FOR ALL USING (true);

-- Add to modules registry
INSERT INTO modules (id, name, description, icon, category, is_core, default_plans, sort_order, status)
VALUES ('subscriptions', 'Subscriptions', 'Recurring deliveries, routes, auto-billing for dairy, tiffin, water', 'RefreshCw', 'operations', false, '{pro,enterprise}', 14, 'active')
ON CONFLICT (id) DO NOTHING;

-- Add industry templates
INSERT INTO industry_templates (id, name, description, icon, category, module_ids, sort_order)
VALUES 
('dairy_milk', 'Dairy / Milk Provider', 'For milk delivery, dairy products subscription', 'Milk', 'delivery', '{crm,subscriptions,billing,whatsapp,website,analytics}', 15),
('tiffin_service', 'Tiffin / Meal Service', 'For tiffin/meal subscription delivery', 'UtensilsCrossed', 'food', '{crm,subscriptions,billing,whatsapp,website,analytics}', 16),
('water_supplier', 'Water Can Supplier', 'For water can/mineral water delivery', 'Droplets', 'delivery', '{crm,subscriptions,billing,whatsapp,website,analytics}', 17)
ON CONFLICT (id) DO NOTHING;
