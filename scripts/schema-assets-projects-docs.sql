-- ============================================
-- ASSETS, PROJECTS, DOCUMENTS - Full Tables
-- ============================================

-- ASSETS
CREATE TABLE IF NOT EXISTS assets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    type TEXT DEFAULT 'equipment' CHECK (type IN ('equipment', 'vehicle', 'furniture', 'electronics', 'machinery', 'solar_panel', 'inverter', 'camera', 'other')),
    brand TEXT, model TEXT, serial_number TEXT,
    purchase_date DATE, purchase_price DECIMAL(12,2),
    warranty_expiry DATE, amc_expiry DATE,
    location TEXT, assigned_to TEXT,
    condition TEXT DEFAULT 'good' CHECK (condition IN ('new', 'good', 'fair', 'needs_repair', 'retired')),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_assets_org ON assets(organization_id);

CREATE TABLE IF NOT EXISTS asset_service_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    asset_id UUID NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL,
    type TEXT DEFAULT 'maintenance' CHECK (type IN ('maintenance', 'repair', 'amc_renewal', 'inspection', 'upgrade')),
    description TEXT, cost DECIMAL(10,2) DEFAULT 0,
    vendor TEXT, date DATE DEFAULT CURRENT_DATE,
    next_due_date DATE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_ash_asset ON asset_service_history(asset_id);

-- PROJECTS
CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name TEXT NOT NULL, client_name TEXT, client_phone TEXT,
    description TEXT, budget_estimated DECIMAL(12,2) DEFAULT 0,
    budget_actual DECIMAL(12,2) DEFAULT 0,
    start_date DATE, end_date DATE,
    progress_percent INTEGER DEFAULT 0,
    status TEXT DEFAULT 'active' CHECK (status IN ('planning', 'active', 'on_hold', 'completed', 'cancelled')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_projects_org ON projects(organization_id);

CREATE TABLE IF NOT EXISTS project_milestones (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    name TEXT NOT NULL, description TEXT,
    deadline DATE, status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed')),
    payment_amount DECIMAL(10,2) DEFAULT 0, payment_status TEXT DEFAULT 'pending',
    sort_order INTEGER DEFAULT 0, created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_pm_project ON project_milestones(project_id);

CREATE TABLE IF NOT EXISTS project_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    milestone_id UUID REFERENCES project_milestones(id),
    title TEXT NOT NULL, assigned_to TEXT,
    status TEXT DEFAULT 'todo' CHECK (status IN ('todo', 'doing', 'done')),
    due_date DATE, notes TEXT, created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_pt_project ON project_tasks(project_id);

CREATE TABLE IF NOT EXISTS project_expenses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    category TEXT, description TEXT NOT NULL,
    amount DECIMAL(10,2) NOT NULL, vendor TEXT, receipt_url TEXT,
    date DATE DEFAULT CURRENT_DATE, created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_pe_project ON project_expenses(project_id);

-- DOCUMENTS
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    type TEXT DEFAULT 'file' CHECK (type IN ('file', 'contract', 'agreement', 'kyc', 'invoice', 'certificate', 'template', 'image', 'other')),
    folder TEXT DEFAULT 'general',
    file_url TEXT, description TEXT,
    tags TEXT[] DEFAULT '{}',
    linked_to TEXT,
    version INTEGER DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_docs_org ON documents(organization_id);
CREATE INDEX IF NOT EXISTS idx_docs_folder ON documents(organization_id, folder);

-- RLS
ALTER TABLE assets ENABLE ROW LEVEL SECURITY;
ALTER TABLE asset_service_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE project_milestones ENABLE ROW LEVEL SECURITY;
ALTER TABLE project_tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE project_expenses ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;

CREATE POLICY "service_all_assets" ON assets FOR ALL USING (true);
CREATE POLICY "service_all_ash" ON asset_service_history FOR ALL USING (true);
CREATE POLICY "service_all_projects" ON projects FOR ALL USING (true);
CREATE POLICY "service_all_pm" ON project_milestones FOR ALL USING (true);
CREATE POLICY "service_all_pt" ON project_tasks FOR ALL USING (true);
CREATE POLICY "service_all_pe" ON project_expenses FOR ALL USING (true);
CREATE POLICY "service_all_docs" ON documents FOR ALL USING (true);