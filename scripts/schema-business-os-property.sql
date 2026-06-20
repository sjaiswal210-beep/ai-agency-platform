-- ============================================
-- PROPERTY MODULE - Database Schema
-- ============================================

-- Properties (buildings/locations)
CREATE TABLE IF NOT EXISTS property_buildings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    address TEXT,
    type TEXT DEFAULT 'pg' CHECK (type IN ('pg', 'hostel', 'apartment', 'hotel', 'commercial', 'other')),
    total_rooms INTEGER DEFAULT 0,
    total_beds INTEGER DEFAULT 0,
    amenities TEXT[] DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_prop_bldg_org ON property_buildings(organization_id);

-- Rooms
CREATE TABLE IF NOT EXISTS property_rooms (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    building_id UUID NOT NULL REFERENCES property_buildings(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    floor TEXT,
    room_type TEXT DEFAULT 'single' CHECK (room_type IN ('single', 'double', 'triple', 'dormitory', 'suite')),
    capacity INTEGER DEFAULT 1,
    rent_amount DECIMAL(10,2) DEFAULT 0,
    deposit_amount DECIMAL(10,2) DEFAULT 0,
    status TEXT DEFAULT 'available' CHECK (status IN ('available', 'occupied', 'maintenance', 'reserved')),
    amenities TEXT[] DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_prop_room_org ON property_rooms(organization_id);
CREATE INDEX IF NOT EXISTS idx_prop_room_bldg ON property_rooms(building_id);
CREATE INDEX IF NOT EXISTS idx_prop_room_status ON property_rooms(organization_id, status);

-- Tenants
CREATE TABLE IF NOT EXISTS property_tenants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    room_id UUID REFERENCES property_rooms(id) ON DELETE SET NULL,
    name TEXT NOT NULL,
    phone TEXT,
    email TEXT,
    id_proof_type TEXT,
    id_proof_number TEXT,
    emergency_contact TEXT,
    move_in_date DATE,
    move_out_date DATE,
    rent_amount DECIMAL(10,2),
    deposit_paid DECIMAL(10,2) DEFAULT 0,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'moved_out', 'evicted')),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_prop_tenant_org ON property_tenants(organization_id);
CREATE INDEX IF NOT EXISTS idx_prop_tenant_room ON property_tenants(room_id);
CREATE INDEX IF NOT EXISTS idx_prop_tenant_status ON property_tenants(organization_id, status);

-- Rent Payments
CREATE TABLE IF NOT EXISTS property_rent_payments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES property_tenants(id) ON DELETE CASCADE,
    amount DECIMAL(10,2) NOT NULL,
    month TEXT NOT NULL,
    year INTEGER NOT NULL,
    status TEXT DEFAULT 'paid' CHECK (status IN ('paid', 'pending', 'partial', 'overdue')),
    payment_date DATE,
    method TEXT,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_prop_rent_org ON property_rent_payments(organization_id);
CREATE INDEX IF NOT EXISTS idx_prop_rent_tenant ON property_rent_payments(tenant_id);

-- Complaints
CREATE TABLE IF NOT EXISTS property_complaints (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    tenant_id UUID REFERENCES property_tenants(id) ON DELETE SET NULL,
    room_id UUID REFERENCES property_rooms(id) ON DELETE SET NULL,
    title TEXT NOT NULL,
    description TEXT,
    category TEXT DEFAULT 'general',
    priority TEXT DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'urgent')),
    status TEXT DEFAULT 'open' CHECK (status IN ('open', 'in_progress', 'resolved', 'closed')),
    resolved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_prop_comp_org ON property_complaints(organization_id);
CREATE INDEX IF NOT EXISTS idx_prop_comp_status ON property_complaints(status);

-- RLS
ALTER TABLE property_buildings ENABLE ROW LEVEL SECURITY;
ALTER TABLE property_rooms ENABLE ROW LEVEL SECURITY;
ALTER TABLE property_tenants ENABLE ROW LEVEL SECURITY;
ALTER TABLE property_rent_payments ENABLE ROW LEVEL SECURITY;
ALTER TABLE property_complaints ENABLE ROW LEVEL SECURITY;

CREATE POLICY "service_all_prop_buildings" ON property_buildings FOR ALL USING (true);
CREATE POLICY "service_all_prop_rooms" ON property_rooms FOR ALL USING (true);
CREATE POLICY "service_all_prop_tenants" ON property_tenants FOR ALL USING (true);
CREATE POLICY "service_all_prop_rent" ON property_rent_payments FOR ALL USING (true);
CREATE POLICY "service_all_prop_complaints" ON property_complaints FOR ALL USING (true);
