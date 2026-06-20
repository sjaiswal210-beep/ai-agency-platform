-- ============================================
-- CRM MODULE - Database Schema
-- ============================================

-- CRM Contacts (Leads, Customers, Vendors, etc.)
CREATE TABLE IF NOT EXISTS crm_contacts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    type TEXT DEFAULT 'lead' CHECK (type IN ('lead', 'customer', 'vendor', 'partner', 'employee')),
    name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    company TEXT,
    designation TEXT,
    avatar_url TEXT,
    stage TEXT DEFAULT 'new',
    score INTEGER DEFAULT 0,
    tags TEXT[] DEFAULT '{}',
    custom_fields JSONB DEFAULT '{}',
    source TEXT,
    assigned_to UUID,
    last_contacted_at TIMESTAMPTZ,
    notes TEXT,
    is_deleted BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_crm_org ON crm_contacts(organization_id);
CREATE INDEX IF NOT EXISTS idx_crm_type ON crm_contacts(organization_id, type);
CREATE INDEX IF NOT EXISTS idx_crm_stage ON crm_contacts(organization_id, stage);
CREATE INDEX IF NOT EXISTS idx_crm_phone ON crm_contacts(phone);
CREATE INDEX IF NOT EXISTS idx_crm_email ON crm_contacts(email);
CREATE INDEX IF NOT EXISTS idx_crm_deleted ON crm_contacts(organization_id, is_deleted);

-- CRM Activities (Calls, Meetings, Tasks, Notes)
CREATE TABLE IF NOT EXISTS crm_activities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    contact_id UUID NOT NULL REFERENCES crm_contacts(id) ON DELETE CASCADE,
    type TEXT NOT NULL CHECK (type IN ('call', 'meeting', 'task', 'note', 'email', 'whatsapp')),
    title TEXT,
    description TEXT,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'completed', 'cancelled')),
    due_date TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_by UUID,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_activity_org ON crm_activities(organization_id);
CREATE INDEX IF NOT EXISTS idx_activity_contact ON crm_activities(contact_id);
CREATE INDEX IF NOT EXISTS idx_activity_type ON crm_activities(organization_id, type);
CREATE INDEX IF NOT EXISTS idx_activity_status ON crm_activities(status);

-- CRM Pipelines (Customizable per org)
CREATE TABLE IF NOT EXISTS crm_pipelines (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name TEXT NOT NULL DEFAULT 'Default Pipeline',
    stages JSONB NOT NULL DEFAULT '[{"id":"new","name":"New","color":"#3b82f6"},{"id":"contacted","name":"Contacted","color":"#eab308"},{"id":"qualified","name":"Qualified","color":"#8b5cf6"},{"id":"proposal","name":"Proposal","color":"#f97316"},{"id":"won","name":"Won","color":"#22c55e"},{"id":"lost","name":"Lost","color":"#ef4444"}]',
    is_default BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_pipeline_org ON crm_pipelines(organization_id);
