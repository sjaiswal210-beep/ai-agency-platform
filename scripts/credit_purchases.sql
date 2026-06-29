-- Credit purchase log (Razorpay top-ups). Run in Supabase SQL Editor.
CREATE TABLE IF NOT EXISTS credit_purchases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    website_id TEXT NOT NULL,
    amount NUMERIC NOT NULL,
    payment_id TEXT,
    order_id TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_credit_purchases_website ON credit_purchases(website_id);

-- owner_credits table (if not already created)
CREATE TABLE IF NOT EXISTS owner_credits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    website_id TEXT UNIQUE NOT NULL,
    balance NUMERIC DEFAULT 0,
    updated_at TIMESTAMPTZ DEFAULT now()
);