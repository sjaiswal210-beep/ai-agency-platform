-- ============================================
-- BOOKING MODULE - Database Schema
-- ============================================

-- Services offered by the business
CREATE TABLE IF NOT EXISTS booking_services (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    duration_minutes INTEGER DEFAULT 60,
    price DECIMAL(10,2),
    currency TEXT DEFAULT 'INR',
    category TEXT,
    is_active BOOLEAN DEFAULT true,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_service_org ON booking_services(organization_id);
CREATE INDEX IF NOT EXISTS idx_service_active ON booking_services(organization_id, is_active);

-- Staff members who provide services
CREATE TABLE IF NOT EXISTS booking_staff (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    avatar_url TEXT,
    services TEXT[] DEFAULT '{}',
    availability JSONB DEFAULT '{"mon":{"start":"09:00","end":"18:00"},"tue":{"start":"09:00","end":"18:00"},"wed":{"start":"09:00","end":"18:00"},"thu":{"start":"09:00","end":"18:00"},"fri":{"start":"09:00","end":"18:00"},"sat":{"start":"09:00","end":"14:00"},"sun":null}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_staff_org ON booking_staff(organization_id);

-- Appointments
CREATE TABLE IF NOT EXISTS booking_appointments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    service_id UUID REFERENCES booking_services(id) ON DELETE SET NULL,
    staff_id UUID REFERENCES booking_staff(id) ON DELETE SET NULL,
    contact_id UUID REFERENCES crm_contacts(id) ON DELETE SET NULL,
    customer_name TEXT NOT NULL,
    customer_phone TEXT,
    customer_email TEXT,
    date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    status TEXT DEFAULT 'confirmed' CHECK (status IN ('pending', 'confirmed', 'completed', 'cancelled', 'no_show')),
    notes TEXT,
    source TEXT DEFAULT 'manual' CHECK (source IN ('manual', 'online', 'whatsapp', 'phone')),
    reminder_sent BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_appt_org ON booking_appointments(organization_id);
CREATE INDEX IF NOT EXISTS idx_appt_date ON booking_appointments(organization_id, date);
CREATE INDEX IF NOT EXISTS idx_appt_staff ON booking_appointments(staff_id, date);
CREATE INDEX IF NOT EXISTS idx_appt_status ON booking_appointments(organization_id, status);
