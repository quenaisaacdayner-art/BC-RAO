---
phase: 02-collection-pipeline
plan: 01
subsystem: api
tags: [apify, reddit, regex, llm, pydantic, supabase]

# Dependency graph
requires:
  - phase: 01-foundation
    provides: InferenceClient with budget tracking, Supabase client, error handling patterns
provides:
  - Apify client wrapper for Reddit scraping
  - Regex pre-filter with quality scoring (~80% rejection rate)
  - CollectionService pipeline orchestration (scrape -> filter -> classify -> store)
  - RawPost Pydantic models for API and database operations
affects: [02-collection-pipeline (plans 02+), 03-analysis-engine]

# Tech tracking
tech-stack:
  added: [apify-client>=1.6.0]
  patterns:
    - "Pipeline orchestration with partial failure handling"
    - "Module-level compiled regex patterns for performance"
    - "Supabase upsert with ignore_duplicates for deduplication"
    - "Top-N sampling strategy for LLM classification cost control"

key-files:
  created:
    - bc-rao-api/app/integrations/apify_client.py
    - bc-rao-api/app/services/regex_filter.py
    - bc-rao-api/app/services/collection_service.py
    - bc-rao-api/app/models/raw_posts.py
  modified:
    - bc-rao-api/pyproject.toml

key-decisions:
  - "Classify only top 10% of filtered posts to control LLM costs"
  - "Partial failure handling: continue on subreddit errors, accumulate error list"
  - "Supabase upsert for deduplication instead of application-level checks"
  - "Relevance scoring before LLM to prioritize highest-quality posts"

patterns-established:
  - "Pipeline services use progress callbacks for real-time updates"
  - "Pre-compiled regex patterns at module level for efficiency"
  - "Graceful fallback on LLM parse failure (archetype=Unclassified)"

# Metrics
duration: 5min
completed: 2026-02-10
---

# Phase 02 Plan 01: Collection Pipeline Core Summary

**Apify Reddit scraper, regex quality filter (~80% rejection), LLM archetype classification for top 10%, and Supabase storage with deduplication**

## Performance

- **Duration:** 5 min
- **Started:** 2026-02-10T17:04:22Z
- **Completed:** 2026-02-10T17:09:22Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- Apify SDK integration for Reddit post scraping with actor configuration
- Regex pre-filter scoring posts 0-10 based on quality signals (pronouns, questions, emotion, storytelling)
- CollectionService orchestrating full pipeline with partial failure tolerance
- LLM archetype classification (Journey, ProblemSolution, Feedback) for highest-scoring posts
- Database storage with ON CONFLICT deduplication on (campaign_id, reddit_post_id)

## Task Commits

Each task was committed atomically:

1. **Task 1: Apify client wrapper + regex pre-filter module + raw_posts Pydantic models** - `28821bb` (feat)
2. **Task 2: Collection service - full pipeline orchestration** - `00aa996` (feat)

## Files Created/Modified
- `bc-rao-api/app/integrations/apify_client.py` - Apify SDK wrapper for Reddit scraping with error handling
- `bc-rao-api/app/services/regex_filter.py` - Quality scoring with compiled patterns (personal pronouns, emotional language, storytelling markers vs. bot markers, link-only, short posts)
- `bc-rao-api/app/services/collection_service.py` - Pipeline orchestrator coordinating scrape -> filter -> classify -> store with progress callbacks
- `bc-rao-api/app/models/raw_posts.py` - Pydantic models (RawPostCreate, RawPostResponse, CollectionProgress, CollectionResult)
- `bc-rao-api/pyproject.toml` - Added apify-client>=1.6.0 dependency

## Decisions Made

**1. Top 10% sampling for LLM classification**
- Only classify highest-scoring 10% of filtered posts via InferenceClient
- Rationale: Control costs while focusing AI on best candidates
- Remaining 90% stored as "Unclassified" for potential future processing

**2. Partial failure handling**
- On subreddit scraping/processing error: log error, continue to next subreddit
- Return CollectionResult with status="partial" if any errors occurred
- Rationale: Don't fail entire pipeline if one subreddit times out or returns errors

**3. Supabase upsert for deduplication**
- Use `.upsert(on_conflict="campaign_id,reddit_post_id", ignore_duplicates=True)`
- Rationale: Database-level dedup more reliable than application-level checks, handles race conditions

**4. Relevance scoring before LLM**
- Regex filter assigns 0-10 relevance_score based on keyword matches, quality signals, engagement
- Target ~80% rejection rate (keep top ~20%)
- Rationale: Pre-filter reduces noise before expensive LLM classification

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - all modules implemented cleanly, imports verified successfully.

## User Setup Required

**External services require manual configuration.** Users must configure:

**Environment variables:**
- `APIFY_API_TOKEN` - Get from https://console.apify.com/account/integrations
- `APIFY_REDDIT_ACTOR_ID` - Reddit scraper actor ID from Apify store

**Verification:**
```bash
# After setting env vars
cd bc-rao-api
python -c "from app.integrations.apify_client import scrape_subreddit; print('Apify client ready')"
```

Without these, `scrape_subreddit()` will raise `AppError(APIFY_ERROR, "Apify API token not configured")`.

## Next Phase Readiness

**Ready for:**
- Plan 02: Collection API endpoints (POST /collection/run, GET /collection/posts, etc.)
- Plan 03: Frontend collection UI with progress tracking

**Provides:**
- `CollectionService.run_collection()` - Full pipeline orchestration
- `CollectionService.get_posts()` - Paginated post listing with filters
- `CollectionService.get_post_detail()` - Single post retrieval
- `CollectionService.get_collection_stats()` - Aggregated statistics

**No blockers.**

## Self-Check: PASSED

All files exist:
- bc-rao-api/app/integrations/apify_client.py ✓
- bc-rao-api/app/services/regex_filter.py ✓
- bc-rao-api/app/services/collection_service.py ✓
- bc-rao-api/app/models/raw_posts.py ✓

All commits exist:
- 28821bb ✓
- 00aa996 ✓

---
*Phase: 02-collection-pipeline*
*Completed: 2026-02-10*
