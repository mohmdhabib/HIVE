-- HIVE Database Schema Migration 001
-- PostgreSQL / Supabase Schema

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- 1. WORKERS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS workers (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    niche TEXT NOT NULL,
    audience TEXT NOT NULL,
    voice TEXT NOT NULL,
    objective TEXT NOT NULL,
    content_pillars JSONB NOT NULL DEFAULT '[]'::jsonb,
    revenue_target JSONB NOT NULL DEFAULT '{"monthly_target_usd": 1000.0, "primary_stream": "affiliate", "target_rpm": 15.0}'::jsonb,
    status TEXT NOT NULL DEFAULT 'idle',
    enabled BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- ============================================================================
-- 2. TASKS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    worker_id TEXT NOT NULL REFERENCES workers(id) ON DELETE CASCADE,
    objective TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'needs_approval',
    priority TEXT NOT NULL DEFAULT 'medium',
    target_platform TEXT NOT NULL DEFAULT 'instagram',
    approval_required BOOLEAN NOT NULL DEFAULT true,
    approved_at TIMESTAMPTZ,
    approved_by TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    completed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_tasks_worker_id ON tasks(worker_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at DESC);

-- ============================================================================
-- 3. CONTENT PIECES TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS content_pieces (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    hook TEXT NOT NULL,
    body_script TEXT NOT NULL,
    caption TEXT NOT NULL,
    hashtags JSONB NOT NULL DEFAULT '[]'::jsonb,
    visual_brief TEXT NOT NULL,
    target_platform TEXT NOT NULL,
    monetization_hypothesis TEXT NOT NULL,
    factual_checks JSONB NOT NULL DEFAULT '[]'::jsonb,
    estimated_risk_level TEXT NOT NULL DEFAULT 'low',
    risks_and_caveats JSONB NOT NULL DEFAULT '[]'::jsonb,
    quality_score FLOAT NOT NULL DEFAULT 1.0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE INDEX IF NOT EXISTS idx_content_pieces_task_id ON content_pieces(task_id);

-- ============================================================================
-- 4. WORKER MEMORY TABLE (Isolated per worker)
-- ============================================================================
CREATE TABLE IF NOT EXISTS worker_memory (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    worker_id TEXT NOT NULL REFERENCES workers(id) ON DELETE CASCADE,
    category TEXT NOT NULL, -- 'topic_history', 'successful_pattern', 'failed_pattern', 'audience_performance', 'strategy_change'
    key TEXT NOT NULL,
    content JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE INDEX IF NOT EXISTS idx_worker_memory_worker_category ON worker_memory(worker_id, category);

-- ============================================================================
-- 5. AUDIT LOGS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    actor TEXT NOT NULL DEFAULT 'system',
    action TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    resource_id TEXT NOT NULL,
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at DESC);

-- ============================================================================
-- 6. REVENUE EVENTS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS revenue_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    worker_id TEXT NOT NULL REFERENCES workers(id) ON DELETE CASCADE,
    content_id UUID REFERENCES content_pieces(id) ON DELETE SET NULL,
    source TEXT NOT NULL, -- 'affiliate', 'sponsorship', 'lead', 'product'
    amount DECIMAL(12, 2) NOT NULL,
    currency TEXT NOT NULL DEFAULT 'USD',
    attribution JSONB NOT NULL DEFAULT '{}'::jsonb,
    verified BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE INDEX IF NOT EXISTS idx_revenue_events_worker ON revenue_events(worker_id);

-- ============================================================================
-- 7. SEED INITIAL 5 WORKERS
-- ============================================================================
INSERT INTO workers (id, name, niche, audience, voice, objective, content_pillars, revenue_target)
VALUES
(
    'tech',
    'Signal Tech',
    'AI and technology',
    'Curious professionals, developers, and builders',
    'Clear, useful, curious, evidence-led, technical yet accessible',
    'Grow a trusted AI and technology audience monetized through dev tool sponsorships and SaaS affiliate referrals',
    '["LLM breakthroughs", "Developer tools", "AI productivity workflows", "Hardware benchmarks"]'::jsonb,
    '{"monthly_target_usd": 2500.0, "primary_stream": "affiliate", "target_rpm": 22.0}'::jsonb
),
(
    'business',
    'Founder Brief',
    'Business and startups',
    'Founders, operators, and aspiring entrepreneurs',
    'Practical, analytical, direct, metrics-focused, anti-fluff',
    'Build an engaged audience around venture creation, B2B playbooks, and business breakdowns',
    '["Unit economics", "Bootstrapping stories", "B2B sales tactics", "Pricing teardowns"]'::jsonb,
    '{"monthly_target_usd": 3000.0, "primary_stream": "sponsorships", "target_rpm": 28.0}'::jsonb
),
(
    'entertainment',
    'Culture Loop',
    'Entertainment',
    'Pop-culture fans, movie/gaming enthusiasts, and internet culture trackers',
    'Energetic, concise, playful, punchy, visually descriptive',
    'Create high-velocity short-form entertainment formats that drive viral reach and platform creator rewards',
    '["Film breakdown", "Gaming lore", "Streaming highlights", "Cultural moments"]'::jsonb,
    '{"monthly_target_usd": 1500.0, "primary_stream": "digital_products", "target_rpm": 12.0}'::jsonb
),
(
    'education',
    'Curiosity Daily',
    'Education and facts',
    'Lifelong learners, students, and curious generalists',
    'Simple, engaging, impeccably accurate, wonder-driven',
    'Make complex scientific, historical, and economic facts intuitive and memorable',
    '["Science explained", "History deep dives", "Cognitive psychology", "Everyday economics"]'::jsonb,
    '{"monthly_target_usd": 1800.0, "primary_stream": "affiliate", "target_rpm": 16.0}'::jsonb
),
(
    'lifestyle',
    'Everyday Edit',
    'Lifestyle and trends',
    'Urban professionals and young adults interested in intentional living and smart consumer choices',
    'Approachable, modern, aesthetic, candid, quality-focused',
    'Curate practical trends, workspace setups, and mindful habits with transparent affiliate monetization',
    '["Desk setups", "Minimalist gear", "Daily routines", "Habit optimization"]'::jsonb,
    '{"monthly_target_usd": 2200.0, "primary_stream": "affiliate", "target_rpm": 20.0}'::jsonb
)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    niche = EXCLUDED.niche,
    audience = EXCLUDED.audience,
    voice = EXCLUDED.voice,
    objective = EXCLUDED.objective,
    content_pillars = EXCLUDED.content_pillars,
    revenue_target = EXCLUDED.revenue_target,
    updated_at = timezone('utc'::text, now());

-- ============================================================================
-- 8. ROW LEVEL SECURITY (RLS) POLICIES
-- ============================================================================
ALTER TABLE workers ENABLE ROW LEVEL SECURITY;
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE content_pieces ENABLE ROW LEVEL SECURITY;
ALTER TABLE worker_memory ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE revenue_events ENABLE ROW LEVEL SECURITY;

-- Service role bypasses RLS
CREATE POLICY "Service role full access workers" ON workers FOR ALL USING (true);
CREATE POLICY "Service role full access tasks" ON tasks FOR ALL USING (true);
CREATE POLICY "Service role full access content_pieces" ON content_pieces FOR ALL USING (true);
CREATE POLICY "Service role full access worker_memory" ON worker_memory FOR ALL USING (true);
CREATE POLICY "Service role full access audit_logs" ON audit_logs FOR ALL USING (true);
CREATE POLICY "Service role full access revenue_events" ON revenue_events FOR ALL USING (true);

-- Authenticated operator read-only policies
CREATE POLICY "Authenticated read workers" ON workers FOR SELECT TO authenticated USING (true);
CREATE POLICY "Authenticated read tasks" ON tasks FOR SELECT TO authenticated USING (true);
CREATE POLICY "Authenticated read content_pieces" ON content_pieces FOR SELECT TO authenticated USING (true);
CREATE POLICY "Authenticated read worker_memory" ON worker_memory FOR SELECT TO authenticated USING (true);
CREATE POLICY "Authenticated read audit_logs" ON audit_logs FOR SELECT TO authenticated USING (true);
CREATE POLICY "Authenticated read revenue_events" ON revenue_events FOR SELECT TO authenticated USING (true);

