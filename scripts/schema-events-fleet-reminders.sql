-- ============================================
-- EVENT / VENUE MANAGER MODULE
-- ============================================

CREATE TABLE IF NOT EXISTS venues (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    capacity INTEGER DEFAULT 100,
    type TEXT DEFAULT 'hall' CHECK (type IN ('hall', 'lawn', 'terrace', 'banquet', 'conference', 'outdoor', 'other')),
    amenities JSONB DEFAULT '[]',
    photos JSONB DEFAULT '[]',
    price_per_day DECIMAL(12,2),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_venue_org ON venues(organization_id);

CREATE TABLE IF NOT EXISTS event_bookings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    venue_id UUID REFERENCES venues(id) ON DELETE SET NULL,
    client_name TEXT NOT NULL,
    client_phone TEXT,
    client_email TEXT,
    event_type TEXT DEFAULT 'wedding' CHECK (event_type IN ('wedding', 'reception', 'birthday', 'corporate', 'engagement', 'baby_shower', 'anniversary', 'conference', 'other')),
    event_date DATE NOT NULL,
    slot TEXT DEFAULT 'fullday' CHECK (slot IN ('morning', 'evening', 'fullday')),
    guest_count INTEGER DEFAULT 100,
    package_id UUID,
    status TEXT DEFAULT 'tentative' CHECK (status IN ('tentative', 'confirmed', 'completed', 'cancelled')),
    total_amount DECIMAL(12,2) DEFAULT 0,
    advance_paid DECIMAL(12,2) DEFAULT 0,
    balance_due DECIMAL(12,2) DEFAULT 0,
    special_requirements TEXT,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_eb_org ON event_bookings(organization_id);
CREATE INDEX IF NOT EXISTS idx_eb_date ON event_bookings(event_date);
CREATE INDEX IF NOT EXISTS idx_eb_status ON event_bookings(organization_id, status);

CREATE TABLE IF NOT EXISTS event_packages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    price DECIMAL(12,2),
    per_plate_price DECIMAL(10,2),
    min_guests INTEGER DEFAULT 50,
    includes JSONB DEFAULT '[]',
    add_ons JSONB DEFAULT '[]',
    is_active BOOLEAN DEFAULT true,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_ep_org ON event_packages(organization_id);

CREATE TABLE IF NOT EXISTS event_vendors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    event_booking_id UUID REFERENCES event_bookings(id) ON DELETE CASCADE,
    vendor_name TEXT NOT NULL,
    vendor_phone TEXT,
    service_type TEXT,
    amount DECIMAL(10,2) DEFAULT 0,
    payment_status TEXT DEFAULT 'pending' CHECK (payment_status IN ('pending', 'partial', 'paid')),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_ev_org ON event_vendors(organization_id);
CREATE INDEX IF NOT EXISTS idx_ev_booking ON event_vendors(event_booking_id);

CREATE TABLE IF NOT EXISTS event_checklist (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_booking_id UUID NOT NULL REFERENCES event_bookings(id) ON DELETE CASCADE,
    task TEXT NOT NULL,
    assigned_to TEXT,
    due_date DATE,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'done')),
    sort_order INTEGER DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_ec_booking ON event_checklist(event_booking_id);

-- ============================================
-- FLEET / VEHICLE MANAGER MODULE
-- ============================================

CREATE TABLE IF NOT EXISTS fleet_vehicles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    vehicle_number TEXT NOT NULL,
    type TEXT DEFAULT 'car' CHECK (type IN ('car', 'bike', 'auto', 'truck', 'van', 'bus', 'tempo', 'other')),
    make TEXT,
    model TEXT,
    year INTEGER,
    color TEXT,
    fuel_type TEXT DEFAULT 'petrol' CHECK (fuel_type IN ('petrol', 'diesel', 'cng', 'electric', 'hybrid')),
    insurance_expiry DATE,
    puc_expiry DATE,
    fitness_expiry DATE,
    odometer INTEGER DEFAULT 0,
    status TEXT DEFAULT 'available' CHECK (status IN ('available', 'on_trip', 'maintenance', 'inactive')),
    assigned_driver_id UUID,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_fv_org ON fleet_vehicles(organization_id);
CREATE INDEX IF NOT EXISTS idx_fv_status ON fleet_vehicles(organization_id, status);

CREATE TABLE IF NOT EXISTS fleet_drivers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    phone TEXT,
    license_number TEXT,
    license_expiry DATE,
    documents JSONB DEFAULT '{}',
    assigned_vehicle_id UUID,
    status TEXT DEFAULT 'available' CHECK (status IN ('available', 'on_trip', 'off_duty')),
    rating DECIMAL(3,2) DEFAULT 5.0,
    total_trips INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_fd_org ON fleet_drivers(organization_id);

CREATE TABLE IF NOT EXISTS fleet_trips (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    vehicle_id UUID REFERENCES fleet_vehicles(id),
    driver_id UUID REFERENCES fleet_drivers(id),
    customer_name TEXT,
    customer_phone TEXT,
    pickup_location TEXT,
    drop_location TEXT,
    scheduled_at TIMESTAMPTZ,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    distance_km DECIMAL(8,2),
    fare DECIMAL(10,2),
    payment_status TEXT DEFAULT 'pending' CHECK (payment_status IN ('pending', 'paid', 'cancelled')),
    status TEXT DEFAULT 'booked' CHECK (status IN ('booked', 'dispatched', 'in_progress', 'completed', 'cancelled')),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_ft_org ON fleet_trips(organization_id);
CREATE INDEX IF NOT EXISTS idx_ft_status ON fleet_trips(organization_id, status);
CREATE INDEX IF NOT EXISTS idx_ft_date ON fleet_trips(scheduled_at);

CREATE TABLE IF NOT EXISTS fleet_maintenance (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    vehicle_id UUID NOT NULL REFERENCES fleet_vehicles(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL,
    type TEXT DEFAULT 'service' CHECK (type IN ('service', 'repair', 'tire', 'oil', 'battery', 'ac', 'body', 'other')),
    description TEXT,
    cost DECIMAL(10,2) DEFAULT 0,
    vendor TEXT,
    date DATE DEFAULT CURRENT_DATE,
    odometer_at_service INTEGER,
    next_service_due_km INTEGER,
    next_service_due_date DATE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_fm_vehicle ON fleet_maintenance(vehicle_id);

CREATE TABLE IF NOT EXISTS fleet_fuel (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    vehicle_id UUID NOT NULL REFERENCES fleet_vehicles(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL,
    date DATE DEFAULT CURRENT_DATE,
    liters DECIMAL(8,2),
    amount DECIMAL(10,2),
    odometer INTEGER,
    fuel_station TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_ff_vehicle ON fleet_fuel(vehicle_id);

-- ============================================
-- RENEWAL / REMINDER ENGINE MODULE
-- ============================================

CREATE TABLE IF NOT EXISTS reminders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    customer_name TEXT NOT NULL,
    customer_phone TEXT NOT NULL,
    customer_email TEXT,
    type TEXT DEFAULT 'general' CHECK (type IN ('insurance', 'vehicle_service', 'amc', 'warranty', 'checkup', 'document', 'subscription', 'followup', 'general')),
    item_description TEXT,
    reference_number TEXT,
    due_date DATE NOT NULL,
    remind_days_before INTEGER[] DEFAULT '{30,7,1}',
    recurrence TEXT DEFAULT 'none' CHECK (recurrence IN ('none', 'monthly', 'quarterly', 'half_yearly', 'yearly')),
    message_template TEXT,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'reminded', 'renewed', 'lapsed', 'cancelled')),
    last_reminded_at TIMESTAMPTZ,
    renewed_at TIMESTAMPTZ,
    amount DECIMAL(10,2),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_rem_org ON reminders(organization_id);
CREATE INDEX IF NOT EXISTS idx_rem_due ON reminders(due_date);
CREATE INDEX IF NOT EXISTS idx_rem_status ON reminders(organization_id, status);
CREATE INDEX IF NOT EXISTS idx_rem_type ON reminders(organization_id, type);

CREATE TABLE IF NOT EXISTS reminder_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    reminder_id UUID NOT NULL REFERENCES reminders(id) ON DELETE CASCADE,
    sent_at TIMESTAMPTZ DEFAULT NOW(),
    channel TEXT DEFAULT 'whatsapp' CHECK (channel IN ('whatsapp', 'sms', 'email')),
    status TEXT DEFAULT 'sent' CHECK (status IN ('sent', 'delivered', 'failed')),
    message TEXT
);
CREATE INDEX IF NOT EXISTS idx_rl_reminder ON reminder_logs(reminder_id);

-- RLS
ALTER TABLE venues ENABLE ROW LEVEL SECURITY;
ALTER TABLE event_bookings ENABLE ROW LEVEL SECURITY;
ALTER TABLE event_packages ENABLE ROW LEVEL SECURITY;
ALTER TABLE event_vendors ENABLE ROW LEVEL SECURITY;
ALTER TABLE event_checklist ENABLE ROW LEVEL SECURITY;
ALTER TABLE fleet_vehicles ENABLE ROW LEVEL SECURITY;
ALTER TABLE fleet_drivers ENABLE ROW LEVEL SECURITY;
ALTER TABLE fleet_trips ENABLE ROW LEVEL SECURITY;
ALTER TABLE fleet_maintenance ENABLE ROW LEVEL SECURITY;
ALTER TABLE fleet_fuel ENABLE ROW LEVEL SECURITY;
ALTER TABLE reminders ENABLE ROW LEVEL SECURITY;
ALTER TABLE reminder_logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "service_all_venues" ON venues FOR ALL USING (true);
CREATE POLICY "service_all_eb" ON event_bookings FOR ALL USING (true);
CREATE POLICY "service_all_ep" ON event_packages FOR ALL USING (true);
CREATE POLICY "service_all_ev2" ON event_vendors FOR ALL USING (true);
CREATE POLICY "service_all_ec" ON event_checklist FOR ALL USING (true);
CREATE POLICY "service_all_fv" ON fleet_vehicles FOR ALL USING (true);
CREATE POLICY "service_all_fd" ON fleet_drivers FOR ALL USING (true);
CREATE POLICY "service_all_ft" ON fleet_trips FOR ALL USING (true);
CREATE POLICY "service_all_fm" ON fleet_maintenance FOR ALL USING (true);
CREATE POLICY "service_all_ff" ON fleet_fuel FOR ALL USING (true);
CREATE POLICY "service_all_reminders" ON reminders FOR ALL USING (true);
CREATE POLICY "service_all_rl" ON reminder_logs FOR ALL USING (true);

-- Register modules
INSERT INTO modules (id, name, description, icon, category, is_core, default_plans, sort_order, status) VALUES
('events', 'Events / Venue', 'Event bookings, venue management, vendor coordination', 'PartyPopper', 'operations', false, '{pro,enterprise}', 20, 'active'),
('fleet', 'Fleet / Vehicles', 'Vehicle tracking, trips, drivers, maintenance, fuel', 'Truck', 'operations', false, '{pro,enterprise}', 21, 'active'),
('reminders', 'Reminders', 'Automated renewal and follow-up reminders', 'Bell', 'communication', false, '{pro,enterprise}', 22, 'active')
ON CONFLICT (id) DO NOTHING;

-- Templates
INSERT INTO industry_templates (id, name, description, icon, category, module_ids, sort_order) VALUES
('marriage_hall', 'Marriage Hall / Banquet', 'For marriage halls, banquet halls, party venues', 'PartyPopper', 'events', '{crm,events,billing,whatsapp,website,analytics}', 38),
('event_planner', 'Event Planner / Decorator', 'For event planners, decorators, caterers', 'Sparkles', 'events', '{crm,events,billing,whatsapp,website,analytics}', 39),
('dj_sound', 'DJ / Sound Rental', 'For DJ services, sound system rental', 'Music', 'events', '{crm,events,inventory,billing,whatsapp,website,analytics}', 40),
('cab_transport', 'Cab / Transport', 'For cab services, car rentals, transport', 'Car', 'transport', '{crm,fleet,billing,whatsapp,website,analytics}', 41),
('packers_movers', 'Packers & Movers', 'For packers, movers, logistics', 'Package', 'transport', '{crm,fleet,job_cards,billing,whatsapp,website,analytics}', 42),
('insurance_agent', 'Insurance Agent', 'For insurance agents and financial advisors', 'Shield', 'finance', '{crm,reminders,billing,documents,whatsapp,website,analytics}', 43),
('optical_shop', 'Optical Shop', 'For optical stores and eye care', 'Eye', 'healthcare', '{crm,custom_orders,reminders,billing,whatsapp,website,analytics}', 44),
('pest_control', 'Pest Control', 'For pest control services', 'Bug', 'service', '{crm,job_cards,reminders,billing,whatsapp,website,analytics}', 45),
('laundry', 'Laundry / Dry Clean', 'For laundry and dry cleaning services', 'Shirt', 'service', '{crm,subscriptions,custom_orders,billing,whatsapp,website,analytics}', 46)
ON CONFLICT (id) DO NOTHING;
