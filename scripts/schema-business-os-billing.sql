-- ============================================
-- BILLING MODULE - Database Schema
-- ============================================

-- Invoices and Quotations
CREATE TABLE IF NOT EXISTS billing_invoices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    invoice_number TEXT NOT NULL,
    contact_id UUID REFERENCES crm_contacts(id) ON DELETE SET NULL,
    type TEXT DEFAULT 'invoice' CHECK (type IN ('invoice', 'quotation', 'receipt', 'credit_note')),
    status TEXT DEFAULT 'draft' CHECK (status IN ('draft', 'sent', 'paid', 'overdue', 'cancelled', 'partially_paid')),
    items JSONB NOT NULL DEFAULT '[]',
    subtotal DECIMAL(12,2) DEFAULT 0,
    tax_amount DECIMAL(12,2) DEFAULT 0,
    discount_amount DECIMAL(12,2) DEFAULT 0,
    total DECIMAL(12,2) DEFAULT 0,
    currency TEXT DEFAULT 'INR',
    tax_config JSONB DEFAULT '{}',
    notes TEXT,
    terms TEXT,
    due_date DATE,
    paid_at TIMESTAMPTZ,
    paid_amount DECIMAL(12,2) DEFAULT 0,
    pdf_url TEXT,
    is_recurring BOOLEAN DEFAULT false,
    recurring_config JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_invoice_org ON billing_invoices(organization_id);
CREATE INDEX IF NOT EXISTS idx_invoice_status ON billing_invoices(organization_id, status);
CREATE INDEX IF NOT EXISTS idx_invoice_contact ON billing_invoices(contact_id);
CREATE INDEX IF NOT EXISTS idx_invoice_type ON billing_invoices(organization_id, type);
CREATE INDEX IF NOT EXISTS idx_invoice_due ON billing_invoices(due_date);
CREATE INDEX IF NOT EXISTS idx_invoice_number ON billing_invoices(organization_id, invoice_number);

-- Payments
CREATE TABLE IF NOT EXISTS billing_payments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    invoice_id UUID REFERENCES billing_invoices(id) ON DELETE SET NULL,
    contact_id UUID REFERENCES crm_contacts(id) ON DELETE SET NULL,
    amount DECIMAL(12,2) NOT NULL,
    currency TEXT DEFAULT 'INR',
    method TEXT CHECK (method IN ('cash', 'upi', 'bank_transfer', 'card', 'cheque', 'razorpay', 'other')),
    reference TEXT,
    notes TEXT,
    payment_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_payment_org ON billing_payments(organization_id);
CREATE INDEX IF NOT EXISTS idx_payment_invoice ON billing_payments(invoice_id);
CREATE INDEX IF NOT EXISTS idx_payment_date ON billing_payments(organization_id, payment_date);

-- Expenses
CREATE TABLE IF NOT EXISTS billing_expenses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    category TEXT,
    description TEXT NOT NULL,
    amount DECIMAL(12,2) NOT NULL,
    currency TEXT DEFAULT 'INR',
    vendor TEXT,
    receipt_url TEXT,
    expense_date DATE DEFAULT CURRENT_DATE,
    created_by UUID,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_expense_org ON billing_expenses(organization_id);
CREATE INDEX IF NOT EXISTS idx_expense_date ON billing_expenses(organization_id, expense_date);
CREATE INDEX IF NOT EXISTS idx_expense_category ON billing_expenses(organization_id, category);
