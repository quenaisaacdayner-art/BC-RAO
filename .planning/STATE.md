# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-07)

**Core value:** Founders can generate Reddit posts that survive moderation and earn genuine engagement by mimicking native community behavior patterns, not by guessing.

**Current focus:** Phase 2 - Collection Pipeline

## Current Position

Phase: 3 of 6 (Pattern Engine)
Plan: 1 of 4 (NLP pipeline + scoring + pattern detection complete)
Status: In progress
Last activity: 2026-02-11 - Completed 03-01-PLAN.md (NLP pipeline)

Progress: [██████████░] 25% (1/4 Phase 3 plans complete)

## Performance Metrics

**Velocity:**
- Total plans completed: 9
- Average duration: 6.0 minutes
- Total execution time: 0.90 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1. Foundation & Core Setup | 5 | 32 min | 6.4 min |
| 2. Collection Pipeline | 3 | 17 min | 5.7 min |
| 3. Pattern Engine | 1 | 7 min | 7.0 min |

**Recent Trend:**
- Last 5 plans: 01-05 (5min), 02-01 (5min), 02-02 (5min), 02-03 (7min), 03-01 (7min)
- Trend: Steady velocity, Phase 3 started with 7min (NLP setup overhead)

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

### Pending Todos

None yet.

### Blockers/Concerns

None yet.

## Session Continuity

Last session: 2026-02-11 (plan 03-01 execution)
Stopped at: Completed 03-01-PLAN.md - NLP pipeline + scoring + pattern detection
Resume file: None
