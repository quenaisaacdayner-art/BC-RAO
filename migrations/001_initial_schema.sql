-- ============================================================
-- BC-RAO Initial Schema Migration
-- ============================================================
-- This migration file is designed to be run in Supabase SQL Editor.
-- It creates all Phase 1+ tables, extensions, indexes, RLS policies,
-- and triggers required for the BC-RAO system.
--
-- Run this file in its entirety in the Supabase SQL Editor.
-- Ensure you are in the SQL Editor, not the Table Editor.
-- ============================================================

-- ============================================================
-- EXTENSIONS
-- ============================================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================
-- ENUM TYPES
-- ============================================================
CREATE TYPE plan_tier AS ENUM ('trial', 'starter', 'growth');
CREATE TYPE subscription_status AS ENUM ('active', 'trial', 'past_due', 'cancelled', 'expired');
CREATE TYPE campaign_status AS ENUM ('active', 'paused', 'archived');
CREATE TYPE post_archetype AS ENUM ('Journey', 'ProblemSolution', 'Feedback', 'Unclassified');
CREATE TYPE draft_status AS ENUM ('generated', 'edited', 'approved', 'posted', 'discarded');
CREATE TYPE post_lifecycle AS ENUM ('Ativo', 'Removido', '404', 'Shadowbanned', 'Auditado');
CREATE TYPE failure_category AS ENUM ('AdminRemoval', 'SocialRejection', 'Shadowban', 'Inertia');
CREATE TYPE usage_action AS ENUM ('collect', 'analyze', 'generate', 'monitor_register');
CREATE TYPE alert_type AS ENUM ('emergency', 'success', 'adjustment', 'trial_reminder', 'onboarding');

-- ============================================================
-- PROFILES (extends Supabase Auth)
-- ============================================================
CREATE TABLE profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    full_name TEXT,
    avatar_url TEXT,
    onboarding_completed BOOLEAN DEFAULT FALSE,
    onboarding_step INT DEFAULT 0,
    timezone TEXT DEFAULT 'UTC',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- SUBSCRIPTIONS
-- ============================================================
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    plan plan_tier NOT NULL DEFAULT 'trial',
    status subscription_status NOT NULL DEFAULT 'trial',
    stripe_customer_id TEXT UNIQUE,
    stripe_subscription_id TEXT UNIQUE,
    trial_starts_at TIMESTAMPTZ DEFAULT NOW(),
    trial_ends_at TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '7 days'),
    current_period_start TIMESTAMPTZ,
    current_period_end TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id)
);

-- ============================================================
-- CAMPAIGNS (organizational unit per user)
-- ============================================================
CREATE TABLE campaigns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    product_context TEXT NOT NULL,
    product_url TEXT,
    keywords TEXT[] NOT NULL DEFAULT '{}',
    target_subreddits TEXT[] NOT NULL DEFAULT '{}',
    status campaign_status DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_campaigns_user ON campaigns(user_id);

-- ============================================================
-- RAW POSTS (Module 1 output -> Module 2 input)
-- ============================================================
CREATE TABLE raw_posts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    subreddit TEXT NOT NULL,
    reddit_post_id TEXT NOT NULL,
    reddit_url TEXT,
    author TEXT,
    author_karma INT,
    title TEXT NOT NULL,
    raw_text TEXT NOT NULL,
    comment_count INT DEFAULT 0,
    upvote_ratio FLOAT,
    embedding vector(1536),
    archetype post_archetype DEFAULT 'Unclassified',
    rhythm_metadata JSONB DEFAULT '{}',
    success_score FLOAT,
    engagement_score FLOAT,
    is_ai_processed BOOLEAN DEFAULT FALSE,
    reddit_created_at TIMESTAMPTZ,
    collected_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(campaign_id, reddit_post_id)
);

CREATE INDEX idx_raw_posts_campaign ON raw_posts(campaign_id);
CREATE INDEX idx_raw_posts_subreddit ON raw_posts(subreddit);
CREATE INDEX idx_raw_posts_archetype ON raw_posts(archetype);
CREATE INDEX idx_raw_posts_score ON raw_posts(success_score DESC);

-- ============================================================
-- COMMUNITY PROFILES (Module 2 aggregated output)
-- ============================================================
CREATE TABLE community_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    subreddit TEXT NOT NULL,
    isc_score FLOAT NOT NULL DEFAULT 5.0,
    avg_sentence_length FLOAT,
    dominant_tone TEXT,
    formality_level FLOAT,
    top_success_hooks JSONB DEFAULT '[]',
    forbidden_patterns JSONB DEFAULT '[]',
    archetype_distribution JSONB DEFAULT '{}',
    sample_size INT DEFAULT 0,
    last_analyzed_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(campaign_id, subreddit)
);

-- ============================================================
-- GENERATED DRAFTS (Module 3 output)
-- ============================================================
CREATE TABLE generated_drafts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    subreddit TEXT NOT NULL,
    archetype post_archetype NOT NULL,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    vulnerability_score FLOAT,
    rhythm_match_score FLOAT,
    blacklist_violations INT DEFAULT 0,
    model_used TEXT NOT NULL,
    token_count INT,
    token_cost_usd FLOAT,
    generation_params JSONB DEFAULT '{}',
    status draft_status DEFAULT 'generated',
    user_edits TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_drafts_campaign ON generated_drafts(campaign_id);
CREATE INDEX idx_drafts_user ON generated_drafts(user_id);
CREATE INDEX idx_drafts_status ON generated_drafts(status);

-- ============================================================
-- SHADOW TABLE (Module 4 - Orchestrator)
-- ============================================================
CREATE TABLE shadow_table (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    draft_id UUID REFERENCES generated_drafts(id) ON DELETE SET NULL,
    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    post_url TEXT UNIQUE NOT NULL,
    subreddit TEXT NOT NULL,
    status_vida post_lifecycle DEFAULT 'Ativo',
    conversational_depth INT DEFAULT 0,
    isc_at_post FLOAT NOT NULL,
    account_status TEXT DEFAULT 'Established' CHECK (account_status IN ('New', 'WarmingUp', 'Established')),
    check_interval_hours INT DEFAULT 4,
    total_checks INT DEFAULT 0,
    last_check_status INT,
    last_check_at TIMESTAMPTZ DEFAULT NOW(),
    audit_result TEXT CHECK (audit_result IN ('SocialSuccess', 'Rejection', 'Inertia')),
    audit_completed_at TIMESTAMPTZ,
    submitted_at TIMESTAMPTZ DEFAULT NOW(),
    audit_due_at TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '7 days'),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_shadow_campaign ON shadow_table(campaign_id);
CREATE INDEX idx_shadow_status ON shadow_table(status_vida);
CREATE INDEX idx_shadow_audit_due ON shadow_table(audit_due_at) WHERE audit_result IS NULL;

-- ============================================================
-- SYNTAX BLACKLIST (Negative Reinforcement Memory)
-- ============================================================
CREATE TABLE syntax_blacklist (
    id SERIAL PRIMARY KEY,
    subreddit TEXT NOT NULL,
    forbidden_pattern TEXT NOT NULL,
    failure_type failure_category NOT NULL,
    source_post_id UUID REFERENCES shadow_table(id) ON DELETE SET NULL,
    confidence FLOAT DEFAULT 0.5,
    is_global BOOLEAN DEFAULT FALSE,
    added_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(subreddit, forbidden_pattern)
);

CREATE INDEX idx_blacklist_subreddit ON syntax_blacklist(subreddit);

-- ============================================================
-- USAGE TRACKING
-- ============================================================
CREATE TABLE usage_tracking (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    action_type usage_action NOT NULL,
    campaign_id UUID REFERENCES campaigns(id) ON DELETE SET NULL,
    token_count INT DEFAULT 0,
    cost_usd FLOAT DEFAULT 0.0,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_usage_user_action ON usage_tracking(user_id, action_type);
CREATE INDEX idx_usage_created ON usage_tracking(created_at);

-- ============================================================
-- EMAIL ALERT LOG
-- ============================================================
CREATE TABLE email_alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    shadow_id UUID REFERENCES shadow_table(id) ON DELETE SET NULL,
    alert_type alert_type NOT NULL,
    subject TEXT NOT NULL,
    body_preview TEXT,
    sent_at TIMESTAMPTZ DEFAULT NOW(),
    delivered BOOLEAN DEFAULT FALSE
);

-- ============================================================
-- AUDIT LOG
-- ============================================================
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    action TEXT NOT NULL,
    resource_type TEXT,
    resource_id UUID,
    details JSONB DEFAULT '{}',
    ip_address INET,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_audit_user ON audit_log(user_id);
CREATE INDEX idx_audit_action ON audit_log(action);

-- ============================================================
-- ROW LEVEL SECURITY - ENABLE
-- ============================================================
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE campaigns ENABLE ROW LEVEL SECURITY;
ALTER TABLE raw_posts ENABLE ROW LEVEL SECURITY;
ALTER TABLE community_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE generated_drafts ENABLE ROW LEVEL SECURITY;
ALTER TABLE shadow_table ENABLE ROW LEVEL SECURITY;
ALTER TABLE usage_tracking ENABLE ROW LEVEL SECURITY;
ALTER TABLE email_alerts ENABLE ROW LEVEL SECURITY;

-- ============================================================
-- ROW LEVEL SECURITY - POLICIES FOR PROFILES
-- ============================================================
CREATE POLICY profiles_select ON profiles
    FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY profiles_insert ON profiles
    FOR INSERT
    WITH CHECK (auth.uid() = id);

CREATE POLICY profiles_update ON profiles
    FOR UPDATE
    USING (auth.uid() = id)
    WITH CHECK (auth.uid() = id);

CREATE POLICY profiles_delete ON profiles
    FOR DELETE
    USING (auth.uid() = id);

-- ============================================================
-- ROW LEVEL SECURITY - POLICIES FOR SUBSCRIPTIONS
-- ============================================================
CREATE POLICY subscriptions_select ON subscriptions
    FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY subscriptions_insert ON subscriptions
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY subscriptions_update ON subscriptions
    FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY subscriptions_delete ON subscriptions
    FOR DELETE
    USING (auth.uid() = user_id);

-- ============================================================
-- ROW LEVEL SECURITY - POLICIES FOR CAMPAIGNS
-- ============================================================
CREATE POLICY campaigns_select ON campaigns
    FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY campaigns_insert ON campaigns
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY campaigns_update ON campaigns
    FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY campaigns_delete ON campaigns
    FOR DELETE
    USING (auth.uid() = user_id);

-- ============================================================
-- ROW LEVEL SECURITY - POLICIES FOR RAW_POSTS
-- ============================================================
CREATE POLICY raw_posts_select ON raw_posts
    FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY raw_posts_insert ON raw_posts
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY raw_posts_update ON raw_posts
    FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY raw_posts_delete ON raw_posts
    FOR DELETE
    USING (auth.uid() = user_id);

-- ============================================================
-- ROW LEVEL SECURITY - POLICIES FOR COMMUNITY_PROFILES
-- ============================================================
CREATE POLICY community_profiles_select ON community_profiles
    FOR SELECT
    USING (auth.uid() = (SELECT user_id FROM campaigns WHERE campaigns.id = community_profiles.campaign_id));

CREATE POLICY community_profiles_insert ON community_profiles
    FOR INSERT
    WITH CHECK (auth.uid() = (SELECT user_id FROM campaigns WHERE campaigns.id = community_profiles.campaign_id));

CREATE POLICY community_profiles_update ON community_profiles
    FOR UPDATE
    USING (auth.uid() = (SELECT user_id FROM campaigns WHERE campaigns.id = community_profiles.campaign_id))
    WITH CHECK (auth.uid() = (SELECT user_id FROM campaigns WHERE campaigns.id = community_profiles.campaign_id));

CREATE POLICY community_profiles_delete ON community_profiles
    FOR DELETE
    USING (auth.uid() = (SELECT user_id FROM campaigns WHERE campaigns.id = community_profiles.campaign_id));

-- ============================================================
-- ROW LEVEL SECURITY - POLICIES FOR GENERATED_DRAFTS
-- ============================================================
CREATE POLICY generated_drafts_select ON generated_drafts
    FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY generated_drafts_insert ON generated_drafts
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY generated_drafts_update ON generated_drafts
    FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY generated_drafts_delete ON generated_drafts
    FOR DELETE
    USING (auth.uid() = user_id);

-- ============================================================
-- ROW LEVEL SECURITY - POLICIES FOR SHADOW_TABLE
-- ============================================================
CREATE POLICY shadow_table_select ON shadow_table
    FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY shadow_table_insert ON shadow_table
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY shadow_table_update ON shadow_table
    FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY shadow_table_delete ON shadow_table
    FOR DELETE
    USING (auth.uid() = user_id);

-- ============================================================
-- ROW LEVEL SECURITY - POLICIES FOR USAGE_TRACKING
-- ============================================================
CREATE POLICY usage_tracking_select ON usage_tracking
    FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY usage_tracking_insert ON usage_tracking
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY usage_tracking_update ON usage_tracking
    FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY usage_tracking_delete ON usage_tracking
    FOR DELETE
    USING (auth.uid() = user_id);

-- ============================================================
-- ROW LEVEL SECURITY - POLICIES FOR EMAIL_ALERTS
-- ============================================================
CREATE POLICY email_alerts_select ON email_alerts
    FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY email_alerts_insert ON email_alerts
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY email_alerts_update ON email_alerts
    FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY email_alerts_delete ON email_alerts
    FOR DELETE
    USING (auth.uid() = user_id);

-- ============================================================
-- TRIGGER: AUTO-CREATE PROFILE ON SIGNUP
-- ============================================================
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO profiles (id, full_name)
  VALUES (NEW.id, NEW.raw_user_meta_data->>'full_name');
  INSERT INTO subscriptions (user_id) VALUES (NEW.id);
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION handle_new_user();

-- ============================================================
-- MIGRATION COMPLETE
-- ============================================================
-- All tables, indexes, RLS policies, and triggers have been created.
-- The database is now ready for BC-RAO backend operations.
-- ============================================================
