-- ============================================
-- SEED DATA - Module Registry + Industry Templates
-- ============================================

-- Insert all available modules
INSERT INTO modules (id, name, description, icon, category, is_core, default_plans, sort_order) VALUES
('crm', 'CRM', 'Customer relationship management - leads, contacts, pipeline', 'Users', 'core', true, '{starter,pro,enterprise}', 1),
('billing', 'Billing', 'Invoices, quotations, payments, expenses', 'Receipt', 'finance', true, '{starter,pro,enterprise}', 2),
('booking', 'Booking', 'Appointments, scheduling, staff management', 'Calendar', 'operations', false, '{pro,enterprise}', 3),
('inventory', 'Inventory', 'Products, stock tracking, suppliers', 'Package', 'operations', false, '{pro,enterprise}', 4),
('property', 'Property', 'Rooms, tenants, rent collection, occupancy', 'Building2', 'operations', false, '{pro,enterprise}', 5),
('membership', 'Membership', 'Plans, subscriptions, attendance tracking', 'CreditCard', 'finance', false, '{pro,enterprise}', 6),
('assets', 'Assets', 'Equipment tracking, warranty, maintenance', 'Cpu', 'operations', false, '{enterprise}', 7),
('projects', 'Projects', 'Project management, milestones, tasks', 'FolderKanban', 'operations', false, '{pro,enterprise}', 8),
('documents', 'Documents', 'Document management, templates, storage', 'FileText', 'core', false, '{pro,enterprise}', 9),
('website', 'Website', 'Business website builder and management', 'Globe', 'core', true, '{starter,pro,enterprise}', 10),
('whatsapp', 'WhatsApp', 'WhatsApp automation, broadcasts, reminders', 'MessageCircle', 'communication', false, '{pro,enterprise}', 11),
('ai_employee', 'AI Employee', 'AI-powered assistant for business operations', 'Bot', 'ai', false, '{enterprise}', 12),
('analytics', 'Analytics', 'Reports, dashboards, business insights', 'BarChart3', 'core', true, '{starter,pro,enterprise}', 13)
ON CONFLICT (id) DO NOTHING;

-- Insert industry templates
INSERT INTO industry_templates (id, name, description, icon, category, module_ids, sort_order) VALUES
('pg_hostel', 'PG / Hostel', 'For PG owners, hostels, and shared living spaces', 'Building2', 'accommodation', '{crm,property,billing,whatsapp,website,analytics}', 1),
('restaurant', 'Restaurant / Cafe', 'For restaurants, cafes, and food businesses', 'UtensilsCrossed', 'food', '{crm,billing,inventory,booking,website,whatsapp,analytics}', 2),
('salon_spa', 'Salon / Spa', 'For beauty salons, spas, and grooming services', 'Scissors', 'beauty', '{crm,booking,billing,membership,website,whatsapp,analytics}', 3),
('gym_fitness', 'Gym / Fitness', 'For gyms, fitness centers, and yoga studios', 'Dumbbell', 'fitness', '{crm,membership,billing,booking,website,whatsapp,analytics}', 4),
('photographer', 'Photographer', 'For photographers and videographers', 'Camera', 'creative', '{crm,booking,billing,projects,documents,website,analytics}', 5),
('solar_company', 'Solar Company', 'For solar installation and energy companies', 'Sun', 'energy', '{crm,billing,projects,assets,documents,website,whatsapp,analytics}', 6),
('doctor_clinic', 'Doctor / Clinic', 'For doctors, clinics, and healthcare providers', 'Stethoscope', 'healthcare', '{crm,booking,billing,documents,website,whatsapp,analytics}', 7),
('school_coaching', 'School / Coaching', 'For schools, coaching centers, and tutors', 'GraduationCap', 'education', '{crm,membership,billing,booking,documents,website,whatsapp,analytics}', 8),
('real_estate', 'Real Estate', 'For real estate agents and property dealers', 'Home', 'property', '{crm,property,billing,documents,projects,website,whatsapp,analytics}', 9),
('freelancer', 'Freelancer', 'For freelancers and independent professionals', 'Laptop', 'professional', '{crm,billing,projects,documents,website,analytics}', 10),
('kirana_retail', 'Kirana / Retail', 'For kirana stores and retail shops', 'ShoppingBag', 'retail', '{crm,inventory,billing,website,whatsapp,analytics}', 11),
('hotel_resort', 'Hotel / Resort', 'For hotels, resorts, and homestays', 'Hotel', 'accommodation', '{crm,property,booking,billing,inventory,website,whatsapp,analytics}', 12),
('contractor', 'Contractor / Builder', 'For contractors, builders, and construction', 'HardHat', 'construction', '{crm,projects,billing,assets,documents,website,analytics}', 13),
('lawyer_ca', 'Lawyer / CA', 'For lawyers, CAs, and professional services', 'Scale', 'professional', '{crm,billing,documents,projects,website,analytics}', 14)
ON CONFLICT (id) DO NOTHING;

-- ============================================
-- RLS POLICIES
-- ============================================
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE organization_modules ENABLE ROW LEVEL SECURITY;
ALTER TABLE org_users ENABLE ROW LEVEL SECURITY;
ALTER TABLE crm_contacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE crm_activities ENABLE ROW LEVEL SECURITY;
ALTER TABLE crm_pipelines ENABLE ROW LEVEL SECURITY;
ALTER TABLE billing_invoices ENABLE ROW LEVEL SECURITY;
ALTER TABLE billing_payments ENABLE ROW LEVEL SECURITY;
ALTER TABLE billing_expenses ENABLE ROW LEVEL SECURITY;
ALTER TABLE booking_services ENABLE ROW LEVEL SECURITY;
ALTER TABLE booking_staff ENABLE ROW LEVEL SECURITY;
ALTER TABLE booking_appointments ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;

-- Service role full access (backend uses service key)
CREATE POLICY "service_all_organizations" ON organizations FOR ALL USING (true);
CREATE POLICY "service_all_org_modules" ON organization_modules FOR ALL USING (true);
CREATE POLICY "service_all_org_users" ON org_users FOR ALL USING (true);
CREATE POLICY "service_all_crm_contacts" ON crm_contacts FOR ALL USING (true);
CREATE POLICY "service_all_crm_activities" ON crm_activities FOR ALL USING (true);
CREATE POLICY "service_all_crm_pipelines" ON crm_pipelines FOR ALL USING (true);
CREATE POLICY "service_all_billing_invoices" ON billing_invoices FOR ALL USING (true);
CREATE POLICY "service_all_billing_payments" ON billing_payments FOR ALL USING (true);
CREATE POLICY "service_all_billing_expenses" ON billing_expenses FOR ALL USING (true);
CREATE POLICY "service_all_booking_services" ON booking_services FOR ALL USING (true);
CREATE POLICY "service_all_booking_staff" ON booking_staff FOR ALL USING (true);
CREATE POLICY "service_all_booking_appointments" ON booking_appointments FOR ALL USING (true);
CREATE POLICY "service_all_audit_log" ON audit_log FOR ALL USING (true);

-- Auto-update trigger for organizations
CREATE TRIGGER organizations_updated_at
    BEFORE UPDATE ON organizations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
