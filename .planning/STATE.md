# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-07)

**Core value:** Founders can generate Reddit posts that survive moderation and earn genuine engagement by mimicking native community behavior patterns, not by guessing.

**Current focus:** Phase 4.1 — Draft Generation Anti-AI Optimization

## Current Position

Phase: 4.1 (Draft Generation Anti-AI Optimization)
Plan: 1 of 3 complete
Status: In progress
Last activity: 2026-02-13 - Completed 04.1-01-PLAN.md (Prompt Input Pipeline Optimization)

Progress: [████████░░░░░░░░░░░░░░░░] 33% (1/3 Phase 4.1 plans complete)

## Performance Metrics

**Velocity:**
- Total plans completed: 21
- Average duration: 6.1 minutes
- Total execution time: 2.18 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1. Foundation & Core Setup | 5 | 32 min | 6.4 min |
| 2. Collection Pipeline | 3 | 17 min | 5.7 min |
| 3. Pattern Engine | 4 | 28 min | 7.0 min |
| 4. Draft Generation | 5 | 33 min | 6.6 min |
| 5. Monitoring & Feedback Loop | 3 | 22 min | 7.3 min |
| 4.1. Anti-AI Optimization | 1 | 9 min | 9.0 min |

**Recent Trend:**
- Last 5 plans: 05-01 (6min), 05-02 (8min), 05-04 (8min), 04.1-01 (9min)
- Trend: Slight uptick for prompt engineering complexity

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Spec is locked source of truth: Comprehensive system spec already covers schema, API, modules, pricing, deployment
- Core loop first, monitoring/billing later: Get Collect → Analyze → Generate working end-to-end before adding Module 4 and Stripe
- Stub auth during core loop build: Move faster on module development, add real Supabase Auth when connecting frontend
- Real integrations from start (no mocks): Apify and OpenRouter ready, skip mock layer complexity
- Full dashboard from start: End-to-end UI (Next.js) not just API - user wants to see the value loop visually
- Made Supabase env vars optional (01-01): Allows imports without .env file, production must set explicitly
- Removed pyproject.toml scripts section (01-01): Invalid format, developers run uvicorn manually
- Used Next.js 16.1 instead of 15.5 (01-02): Latest stable, Shadcn/UI compatible, Turbopack faster builds
- Tailwind CSS v4 with @import directive (01-02): No tailwind.config.ts needed, simpler setup
- Middleware at project root (01-02): Required Next.js convention for SSR token refresh
- Inter font over Geist (01-02): Professional SaaS aesthetic aligned with research patterns
- Client-side Supabase Auth (01-03): Forms call supabase.auth SDK directly, simpler than backend proxy
- Profile auto-creation via DB trigger (01-03): DB trigger from 01-01 ensures profile + subscription always created atomically
- JSON serialization for Celery (01-04): Security best practice, no pickle execution risk
- Budget checked before LLM calls (01-04): Prevents mid-call failures, immediate PLAN_LIMIT_REACHED error
- Fallback models on primary failure (01-04): Improves reliability, try Gemini Flash if Claude Haiku fails
- Campaign stats use placeholder zeros (01-05): Collector, analyzer, monitor phases will populate real data
- Overview page conditional empty state (01-05): Better UX for new users, clear onboarding flow
- Collapsible sidebar with icon mode (01-05): Balances screen space, matches Vercel dashboard style
- Top 10% LLM classification sampling (02-01): Control costs by only classifying highest-scoring filtered posts
- Partial failure handling in pipelines (02-01): Continue on subreddit errors, return partial results with error list
- Database-level deduplication (02-01): Supabase upsert with ignore_duplicates instead of app-level checks
- Regex pre-filter before LLM (02-01): Module-level compiled patterns score posts 0-10, target ~80% rejection
- SSE endpoint no authentication (02-02): task_id acts as unguessable UUID bearer token, simplifies EventSource usage
- Async/sync bridging with asyncio.run (02-02): Bridge async CollectionService to sync Celery task
- 500ms SSE polling interval (02-02): Balances smooth progress updates with backend load
- Billing limits deferred to Phase 6 (02-02): Focus on core loop before monetization
- SSE proxy pattern (02-03): Next.js API routes proxy FastAPI SSE to browser EventSource, validate ownership on trigger
- EventSource cleanup pattern (02-03): Always close() in useEffect return to prevent connection leaks
- Three-phase collection flow (02-03): Idle → collecting → complete with navigation guards and auto-transitions
- Hardcoded remaining runs UI (02-03): Display "5 remaining" for trial tier, backend enforcement in Phase 6
- SpaCy pipeline with 3 custom components (03-01): formality_scorer, tone_classifier, rhythm_analyzer for local NLP
- Disable NER in SpaCy model (03-01): Named entity recognition not needed, saves memory
- Vulnerability scoring as authenticity proxy (03-01): Personal pronouns, emotions, questions identify authentic vs promotional
- Weighted scoring formula (03-01): vulnerability*0.25 + rhythm*0.25 + formality*0.2 - jargon*0.15 - links*0.15
- ISC minimum 10 posts (03-01): Statistical validity requirement for quartile analysis
- 6 pattern categories (03-01): Promotional, Self-referential, Link patterns, Low-effort, Spam indicators, Off-topic
- Compiled regex at module level (03-01): One-time compilation, significant performance gain
- Auto-trigger analysis after collection (03-02): Seamless pipeline flow, analysis_task_id in collection success metadata
- Block profile creation for < 10 posts (03-02): ISC requires statistical validity for quartile analysis
- System patterns immutable (03-02): is_system=true patterns from analysis cannot be deleted, users only add custom
- PostScoreBreakdown caches fetched data (03-04): Prevents re-fetching when user collapses/re-expands same post
- Blacklist category cards before table (03-04): Show pattern distribution summary (counts by category) before detailed list
- Campaign detail navigation cards (03-04): Icon-coded cards link to profiles, analysis, blacklist from main campaign page
- ISC gating 5-branch decision tree (04-01): New accounts warm-up mode, High ISC > 7.5 blocks risky archetypes, archetype-specific rules
- Generic defaults for unprofiled subreddits (04-01): Never crash on missing profile, use GENERIC_DEFAULTS with warning
- Post-generation blacklist validation (04-01): Catches LLM violations that slip through prompt instructions
- InferenceClient for all generation (04-01): Uses existing Phase 1 client, not separate OpenAI SDK
- Monthly draft limits enforced (04-02): Trial=10, Starter=50, Growth=unlimited drafts/month, 403 when exceeded
- SSE streaming for generation progress (04-02): Same 500ms polling pattern as collection, no auth on stream endpoint
- Background tasks via asyncio for Railway (04-02): Celery tasks preserved for horizontal scaling reference
- ISC gating enforced on frontend (04-03): Inline warning + auto-switch to Feedback when ISC > 7.5
- Single-form generation UX (04-03): One page with three inputs (subreddit, archetype, context), not wizard
- Unprofiled subreddits allow generation (04-03): Yellow warning shown, backend uses generic defaults with reduced accuracy
- 4-stage campaign journey (04-05): Project Briefing → Strategic Selection → Community Intelligence → Alchemical Transmutation
- Linear stage progression (04-05): Each stage locked until previous completes, auto-advance toast when unlocked
- Stage 4 on campaign page (04-05): Generate button + recent drafts preview, locked until Stage 3 complete
- Reddit httpx over PRAW (05-01): Lightweight HTTP-only Reddit client using .json endpoints, no heavy wrapper
- OAuth token caching (05-01): Cache Reddit tokens for 3500s to avoid repeated requests
- Dual-check shadowban detection (05-01): Auth sees post but anon doesn't = shadowbanned
- Email rate limiting (05-01): Max 1 emergency shadowban alert per 24h per user
- Graceful email fallback (05-01): Skip email sends if RESEND_API_KEY empty (development mode)
- Consecutive failure logic (05-02): Requires 2 consecutive checks before flagging shadowban (prevents false positives)
- Pattern extraction reuses existing check_post_penalties (05-02): Regex-based extractor from pattern_extractor.py, no new LLM-based extractor
- 15-min asyncio monitoring scheduler (05-02): While-loop with asyncio.sleep(900), no APScheduler/Celery beat needed
- Pattern injection with upsert (05-02): Ignore duplicates on syntax_blacklist to avoid constraint errors
- 5-stage campaign journey (05-04): Stage 5 "Deployment & Monitoring" locked until Stage 4 (drafts generated) complete
- monitored_posts stat field (05-04): Campaign.stats.monitored_posts tracks Stage 5 completion
- "I posted this" button entry point (05-04): Draft editor post registration for approved/posted drafts
- Inline URL input UX (05-04): Lightweight expandable form below button, not modal
- Client-side Reddit URL validation (05-04): Regex pattern validates before POST to /api/monitoring
- Temperature 0.85 for all archetypes (04.1-01): Up from 0.7 for creative variance, uniform start before per-archetype tuning
- frequency_penalty=0.3 and presence_penalty=0.2 (04.1-01): Creative variance without incoherence
- No top_p for Claude Sonnet 4 (04.1-01): API rejects combined temperature+top_p (verified constraint, returns 400)
- Positive humanization rules (04.1-01): 3-5 diverse Good/Bad examples per rule to prevent LLM from copying any single example verbatim
- Uniform random template selection (04.1-01): 12 templates with random.choice sufficient, no weighted selection needed

### Pending Todos

None yet.

### Roadmap Evolution

- Phase 4.1 inserted after Phase 4: Draft Generation Anti-AI Optimization (URGENT) — Rewrite generation pipeline to eliminate 6 AI-detectable anti-patterns identified in .planning/debug/generic-ai-detectable-drafts.md

### Blockers/Concerns

**Phase 5 Plan 01 concerns:**
- Account status tracking using subscription.plan as proxy - proper account_status field should be added to profiles table
- Email alert metadata (check_result dict) logged but not persisted to database - consider JSONB metadata column for shadow_table

**Phase 5 Plan 02 concerns:**
- Periodic scheduler (schedule_periodic_monitoring) must be launched at app startup - needs integration into main.py or startup event
- Metadata JSONB column not yet added to shadow_table schema - consecutive failure logic stores last_check_result in metadata field, but this will fail if column doesn't exist. Need to either: (a) add metadata column to shadow_table schema, or (b) store consecutive check state in Redis instead of DB
- 7-day audit dispatch relies on dispatch_pending_checks catching audit_due_at posts - may miss exact 7-day mark by up to 15 minutes (acceptable for now, can improve in future)

## Session Continuity

Last session: 2026-02-13 (Phase 4.1 Plan 01 execution complete)
Stopped at: Completed 04.1-01-PLAN.md (Prompt Input Pipeline Optimization)
Resume file: None
