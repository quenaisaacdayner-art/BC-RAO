-- ============================================================
-- Migration 002: Add columns to syntax_blacklist for custom user patterns
-- ============================================================
-- The original table only supports system-detected patterns from monitoring.
-- This migration adds columns needed for user-added custom patterns and
-- campaign scoping.

-- Add campaign_id to scope patterns per campaign
ALTER TABLE syntax_blacklist
    ADD COLUMN IF NOT EXISTS campaign_id UUID REFERENCES campaigns(id) ON DELETE CASCADE;

-- Add category for user-friendly categorization (Promotional, Custom, etc.)
ALTER TABLE syntax_blacklist
    ADD COLUMN IF NOT EXISTS category TEXT;

-- Add is_system flag to distinguish system-detected vs user-added patterns
ALTER TABLE syntax_blacklist
    ADD COLUMN IF NOT EXISTS is_system BOOLEAN DEFAULT TRUE;

-- Make failure_type nullable for user-added patterns (they don't have a failure type)
ALTER TABLE syntax_blacklist
    ALTER COLUMN failure_type DROP NOT NULL;

-- Make subreddit nullable for patterns that apply to all subreddits
ALTER TABLE syntax_blacklist
    ALTER COLUMN subreddit DROP NOT NULL;

-- Create index on campaign_id for faster lookups
CREATE INDEX IF NOT EXISTS idx_blacklist_campaign ON syntax_blacklist(campaign_id);

-- Create index on is_system for filtering
CREATE INDEX IF NOT EXISTS idx_blacklist_is_system ON syntax_blacklist(is_system);
