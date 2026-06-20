-- ============================================
-- Business OS - Phase 1 Database Schema
-- Multi-Tenant Module Framework
-- Run this in Supabase SQL Editor
-- ============================================

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- ORGANIZATIONS (Every business is a tenant)
-- ============================================
CREATE TABLE IF NOT EXISTS organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    logo_url TEXT,
    brand_color TEXT DEFAULT '#6366f1',
    plan TEXT DEFAULT 'starter' CHECK (plan IN ('starter', 'pro', 'enterprise', 'custom')),
    subdomain TEXT UNIQUE,
    custom_domain TEXT,
    owner_id UUID,
    phone TEXT,
    email TEXT,
    address TEXT,
    city TEXT,
    settings JSONB DEFAULT '{}',
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'suspended', 'cancelled')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_org_slug ON organizations(slug);
CREATE INDEX IF NOT EXISTS idx_org_owner ON organizations(owner_id);
CREATE INDEX IF NOT EXISTS idx_org_subdomain ON organizations(subdomain);
CREATE INDEX IF NOT EXISTS idx_org_status ON organizations(status);

-- ============================================
-- MODULES REGISTRY (All available modules)
-- ============================================
CREATE TABLE IF NOT EXISTS modules (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    icon TEXT,
    category TEXT DEFAULT 'general' CHECK (category IN ('core', 'operations', 'finance', 'communication', 'ai', 'general')),
    version TEXT DEFAULT '1.0.0',
    is_core BOOLEAN DEFAULT false,
    dependencies TEXT[] DEFAULT '{}',
    default_plans TEXT[] DEFAULT '{starter,pro,enterprise}',
    sort_order INTEGER DEFAULT 0,
    config_schema JSONB DEFAULT '{}',
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'deprecated', 'beta')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- ORGANIZATION MODULES (Which modules enabled per org)
-- ============================================
CREATE TABLE IF NOT EXISTS organization_modules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    module_id TEXT NOT NULL REFERENCES modules(id),
    enabled BOOLEAN DEFAULT true,
    config JSONB DEFAULT '{}',
    enabled_at TIMESTAMPTZ DEFAULT NOW(),
    enabled_by UUID,
    UNIQUE(organization_id, module_id)
);

CREATE INDEX IF NOT EXISTS idx_orgmod_org ON organization_modules(organization_id);
CREATE INDEX IF NOT EXISTS idx_orgmod_module ON organization_modules(module_id);
CREATE INDEX IF NOT EXISTS idx_orgmod_enabled ON organization_modules(organization_id, enabled);

-- ============================================
-- ORG USERS (Multi-org membership)
-- ============================================
CREATE TABLE IF NOT EXISTS org_users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    role TEXT DEFAULT 'member' CHECK (role IN ('owner', 'admin', 'manager', 'member', 'viewer')),
    permissions JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    joined_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, organization_id)
);

CREATE INDEX IF NOT EXISTS idx_orguser_user ON org_users(user_id);
CREATE INDEX IF NOT EXISTS idx_orguser_org ON org_users(organization_id);

-- ============================================
-- INDUSTRY TEMPLATES
-- ============================================
CREATE TABLE IF NOT EXISTS industry_templates (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    icon TEXT,
    category TEXT,
    module_ids TEXT[] NOT NULL,
    default_config JSONB DEFAULT '{}',
    sort_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- AUDIT LOG
-- ============================================
CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID REFERENCES organizations(id) ON DELETE SET NULL,
    user_id UUID,
    action TEXT NOT NULL,
    entity_type TEXT,
    entity_id TEXT,
    old_value JSONB,
    new_value JSONB,
    ip_address TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_org ON audit_log(organization_id);
CREATE INDEX IF NOT EXISTS idx_audit_created ON audit_log(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_log(action);
