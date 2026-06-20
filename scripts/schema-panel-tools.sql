-- ============================================
-- PANEL TOOLS CONTROL - Which tools show per website/org
-- ============================================

-- Available panel tools registry
CREATE TABLE IF NOT EXISTS panel_tools (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    icon TEXT,
    category TEXT DEFAULT 'manage',
    description TEXT,
    url_pattern TEXT NOT NULL,
    sort_order INTEGER DEFAULT 0,
    is_default BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Per-website tool overrides (admin can disable specific tools)
CREATE TABLE IF NOT EXISTS website_tool_config (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    website_id UUID NOT NULL,
    tool_id TEXT NOT NULL REFERENCES panel_tools(id),
    enabled BOOLEAN DEFAULT true,
    UNIQUE(website_id, tool_id)
);

CREATE INDEX IF NOT EXISTS idx_wtc_website ON website_tool_config(website_id);

-- Seed default panel tools
INSERT INTO panel_tools (id, name, icon, category, url_pattern, sort_order, is_default) VALUES
('products', 'Products', '🛒', 'manage', '/api/store/{website_id}/manage', 1, true),
('social_post', 'Social Post', '📷', 'manage', '/api/branding/{website_id}/social-post/preview', 2, true),
('qr_code', 'QR Code', '📸', 'manage', '/api/qr/{website_id}', 3, true),
('analytics', 'Analytics', '📈', 'manage', '/api/owner-analytics/{website_id}', 4, true),
('daily_content', 'Daily Content', '📅', 'manage', '/api/daily/{website_id}', 5, true),
('create_offer', 'Create Offer', '🎁', 'manage', '/api/offers/{website_id}', 6, true),
('google_setup', 'Google Setup', '📍', 'manage', '/api/google-profile/{website_id}/setup-guide', 7, true),
('logo', 'Logo', '🎨', 'manage', '/api/logo-gen/{website_id}/preview', 8, true),
('promo_videos', 'Promo Videos', '🎬', 'manage', '/api/panel/{website_id}/video-creator', 9, true),
('video_creator', 'Video Creator', '🤖', 'manage', '/api/panel/{website_id}/ai-video', 10, true),
('reviews', 'Reviews', '⭐', 'growth', '/api/panel/{website_id}/reviews', 11, true),
('assistant', 'Business Assistant', '💬', 'growth', '/api/panel/{website_id}/assistant', 12, true),
('wa_growth', 'WA Growth', '📨', 'growth', '/api/panel/{website_id}/wa-growth', 13, true),
('competitors', 'Competitors', '📈', 'growth', '/api/panel/{website_id}/competitors', 14, true),
('edit_website', 'Edit Website', '✎', 'edit', 'editor', 15, true),
('social_links', 'Social Links', '🔗', 'edit', '/api/panel/{website_id}/social-links', 16, true),
('gallery', 'Gallery Photos', '🖼', 'edit', '/api/panel/{website_id}/gallery', 17, true),
('festival_offers', 'Festival Offers', '🎆', 'edit', '/api/offers/{website_id}', 18, true)
ON CONFLICT (id) DO NOTHING;

-- RLS
ALTER TABLE panel_tools ENABLE ROW LEVEL SECURITY;
ALTER TABLE website_tool_config ENABLE ROW LEVEL SECURITY;
CREATE POLICY "service_all_panel_tools" ON panel_tools FOR ALL USING (true);
CREATE POLICY "service_all_wtc" ON website_tool_config FOR ALL USING (true);
