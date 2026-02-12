-- Migration 003: Add style_guide and style_metrics columns to community_profiles
-- These columns store qualitative style analysis data for humanized post generation.

-- style_metrics: SpaCy-extracted structural data (vocabulary, punctuation, formatting)
-- Deterministic, free to recompute, useful for frontend display
ALTER TABLE community_profiles
    ADD COLUMN IF NOT EXISTS style_metrics JSONB DEFAULT '{}';

-- style_guide: LLM-generated natural language style guide
-- Costs tokens, is the actual prompt injection data for generation
ALTER TABLE community_profiles
    ADD COLUMN IF NOT EXISTS style_guide JSONB DEFAULT '{}';

COMMENT ON COLUMN community_profiles.style_metrics IS
    'SpaCy-extracted structural style metrics (vocabulary frequency, punctuation habits, formatting conventions)';

COMMENT ON COLUMN community_profiles.style_guide IS
    'LLM-generated natural language style guide for the community (voice, vocabulary, formatting)';
