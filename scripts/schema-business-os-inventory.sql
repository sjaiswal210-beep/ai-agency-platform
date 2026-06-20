-- ============================================
-- INVENTORY MODULE - Database Schema
-- ============================================

-- Product Categories
CREATE TABLE IF NOT EXISTS inventory_categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    parent_id UUID REFERENCES inventory_categories(id),
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_inv_cat_org ON inventory_categories(organization_id);

-- Products
CREATE TABLE IF NOT EXISTS inventory_products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    sku TEXT,
    description TEXT,
    category_id UUID REFERENCES inventory_categories(id) ON DELETE SET NULL,
    price DECIMAL(12,2) DEFAULT 0,
    cost_price DECIMAL(12,2) DEFAULT 0,
    currency TEXT DEFAULT 'INR',
    unit TEXT DEFAULT 'pcs',
    stock_quantity INTEGER DEFAULT 0,
    low_stock_threshold INTEGER DEFAULT 5,
    barcode TEXT,
    image_url TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_inv_prod_org ON inventory_products(organization_id);
CREATE INDEX IF NOT EXISTS idx_inv_prod_cat ON inventory_products(category_id);
CREATE INDEX IF NOT EXISTS idx_inv_prod_sku ON inventory_products(organization_id, sku);
CREATE INDEX IF NOT EXISTS idx_inv_prod_stock ON inventory_products(organization_id, stock_quantity);

-- Suppliers
CREATE TABLE IF NOT EXISTS inventory_suppliers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    phone TEXT,
    email TEXT,
    address TEXT,
    gst_number TEXT,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_inv_sup_org ON inventory_suppliers(organization_id);

-- Stock Movements (in/out tracking)
CREATE TABLE IF NOT EXISTS inventory_movements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES inventory_products(id) ON DELETE CASCADE,
    type TEXT NOT NULL CHECK (type IN ('purchase', 'sale', 'adjustment', 'return', 'transfer')),
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(12,2),
    supplier_id UUID REFERENCES inventory_suppliers(id),
    reference TEXT,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_inv_mov_org ON inventory_movements(organization_id);
CREATE INDEX IF NOT EXISTS idx_inv_mov_prod ON inventory_movements(product_id);
CREATE INDEX IF NOT EXISTS idx_inv_mov_date ON inventory_movements(created_at DESC);

-- RLS
ALTER TABLE inventory_categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE inventory_products ENABLE ROW LEVEL SECURITY;
ALTER TABLE inventory_suppliers ENABLE ROW LEVEL SECURITY;
ALTER TABLE inventory_movements ENABLE ROW LEVEL SECURITY;

CREATE POLICY "service_all_inv_categories" ON inventory_categories FOR ALL USING (true);
CREATE POLICY "service_all_inv_products" ON inventory_products FOR ALL USING (true);
CREATE POLICY "service_all_inv_suppliers" ON inventory_suppliers FOR ALL USING (true);
CREATE POLICY "service_all_inv_movements" ON inventory_movements FOR ALL USING (true);
