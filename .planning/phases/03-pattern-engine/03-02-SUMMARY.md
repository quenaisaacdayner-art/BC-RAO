---
phase: 03
plan: 02
subsystem: pattern-engine
tags: [analysis-service, background-worker, community-profiles, ISC-scoring, SSE-streaming, forbidden-patterns]
requires: [03-01]
provides:
  - analysis-service-layer
  - analysis-background-worker
  - auto-trigger-collection-to-analysis
  - community-profile-creation
  - 8-analysis-api-endpoints
affects: [03-03, 03-04, 04-01]
tech-stack:
  added: []
  patterns: [auto-chaining-pipelines, progress-callback-pattern, SSE-streaming]
key-files:
  created:
    - bc-rao-api/app/services/analysis_service.py
    - bc-rao-api/app/workers/analysis_worker.py
    - bc-rao-api/app/api/v1/analysis.py
  modified:
    - bc-rao-api/app/workers/task_runner.py
    - bc-rao-api/app/api/v1/router.py
key-decisions:
  - decision: "Auto-trigger analysis after collection success"
    rationale: "User decision LOCKED - seamless pipeline flow without manual trigger"
    impact: "Collection SUCCESS event includes analysis_task_id for frontend tracking"
  - decision: "Block profile creation for subreddits with < 10 posts"
    rationale: "ISC calculation requires statistical validity per quartile analysis"
    impact: "Subreddits with insufficient data skip profiling with error message"
  - decision: "System-detected patterns cannot be removed"
    rationale: "is_system=True patterns are from analysis, user can only add custom patterns"
    impact: "Custom pattern endpoint only allows insert, not delete of system patterns"
duration: 4.6 minutes
completed: 2026-02-10
---

# Phase 3 Plan 2: Analysis Service & API

**One-liner:** Analysis service orchestrating SpaCy NLP -> vulnerability scoring -> ISC calculation -> community profiling with auto-trigger from collection and 8 REST/SSE endpoints for profiles, scoring breakdowns, and forbidden patterns.

## Performance

**Execution time:** 4.6 minutes
**Tasks completed:** 2/2 (100%)
**Files created:** 3
**Files modified:** 2
**Lines of code:** ~1150 lines (service: 600, worker: 50, endpoints: 470, wiring: 30)

## Accomplishments

**Module 2 backend complete:**

1. **Analysis service layer** - AnalysisService orchestrates full pipeline:
   - Fetch raw posts from Supabase grouped by subreddit
   - Run NLP analysis via analyze_posts_batch
   - Calculate community averages for scoring context
   - Score each post using vulnerability + rhythm + formality formula
   - Update raw_posts.rhythm_metadata JSONB with NLP + scoring data
   - Calculate ISC score (blocks subreddits with < 10 posts)
   - Extract forbidden patterns with 6 categories
   - Upsert community_profiles with ISC, tone, formality, hooks, patterns, archetypes

2. **Background worker with auto-trigger** - Collection completion chains analysis automatically:
   - run_collection_background adds analysis_task_id to SUCCESS metadata
   - asyncio.create_task launches run_analysis_background_task
   - Progress callback updates Redis state for SSE streaming
   - Follows established collection worker pattern

3. **8 API endpoints** - Full REST + SSE coverage:
   - POST /analyze: Manual trigger with force_refresh support
   - GET /progress: SSE stream with 500ms polling (same pattern as collection)
   - GET /community-profile: Single profile with isc_tier computed
   - GET /community-profiles: All profiles for comparison table
   - GET /scoring-breakdown: Detailed post scoring with penalty_phrases for inline highlighting
   - GET /analyzed-posts: Paginated posts with subreddit filter, sorting (total_score/vulnerability/rhythm)
   - GET /forbidden-patterns: Aggregated patterns by category with counts
   - POST /forbidden-patterns: Add custom user patterns (is_system=false)

4. **Service methods** - 7 async methods in AnalysisService:
   - run_analysis(): Main orchestration with progress callbacks
   - get_community_profile(): Single profile fetch with ISC tier
   - get_community_profiles(): All profiles for campaign
   - get_scoring_breakdown(): Post scoring with penalty phrases
   - get_analyzed_posts(): Paginated query with filters
   - get_forbidden_patterns(): Aggregate from community_profiles + custom
   - add_custom_pattern(): Insert user patterns (syntax_blacklist table)

**Key integration points:**

- AnalysisService imports analyze_posts_batch, calculate_post_score, calculate_isc_score, extract_forbidden_patterns
- Auto-trigger wiring in task_runner.py chains analysis after collection success
- SSE endpoint follows collection pattern: Redis state polling, terminal states, 500ms interval
- Community profile upsert with on_conflict="campaign_id,subreddit" handles re-analysis

**Auto-trigger flow:**

```
Collection SUCCESS
  └─> generate analysis_task_id
  └─> add to collection success metadata
  └─> asyncio.create_task(run_analysis_background_task)
  └─> Frontend tracks both task_ids via SSE
```

## Task Commits

| Task | Commit | Description |
|------|--------|-------------|
| 1 | 0cff7f8 | Analysis service + worker with auto-trigger |
| 2 | 677a9e6 | Analysis API endpoints + router registration |

## Files

**Created:**

- `bc-rao-api/app/services/analysis_service.py` (600 lines) - Service layer orchestrating NLP -> scoring -> profiling pipeline
- `bc-rao-api/app/workers/analysis_worker.py` (50 lines) - Background worker with progress callback
- `bc-rao-api/app/api/v1/analysis.py` (470 lines) - 8 REST + SSE endpoints for analysis operations

**Modified:**

- `bc-rao-api/app/workers/task_runner.py` - Added run_analysis_background_task and auto-trigger wiring
- `bc-rao-api/app/api/v1/router.py` - Registered analysis router with analysis tags

**Key patterns:**

- Progress callback pattern: `progress_callback(AnalysisProgress(...))` updates Redis state
- SSE streaming: async generator yielding `event: X\ndata: {...}\n\n` format
- Auto-chaining pipelines: Collection SUCCESS launches analysis task
- Community profile calculation: Group by subreddit, calculate averages, score posts, compute ISC

## Decisions Made

**1. Auto-trigger analysis after collection success**

- **Context:** User decision from 03-01 research - seamless pipeline flow
- **Decision:** Collection worker auto-launches analysis with analysis_task_id in success metadata
- **Impact:** Frontend can track both collection + analysis via separate SSE streams
- **Locked:** Yes - user explicitly chose auto-trigger over manual

**2. Block profile creation for subreddits with < 10 posts**

- **Context:** ISC calculation requires quartile analysis (top 25%, bottom 25%)
- **Decision:** Skip subreddits with < 10 posts, log "insufficient data" error
- **Impact:** Community profiles only created for statistically valid samples
- **Validation:** calculate_isc_score raises ValueError if len(posts) < 10

**3. System-detected patterns cannot be removed**

- **Context:** Forbidden patterns come from two sources: analysis (is_system=true) and user (is_system=false)
- **Decision:** POST /forbidden-patterns only allows insert of custom patterns, no delete endpoint
- **Impact:** Users augment system patterns but cannot override analysis results
- **Rationale:** Analysis patterns reflect actual community behavior, should not be editable

**4. Scoring breakdown includes penalty phrases for inline highlighting**

- **Context:** Frontend needs to highlight jargon/links that penalized the score
- **Decision:** get_scoring_breakdown merges check_post_penalties + stored rhythm_metadata penalties
- **Impact:** UI can render inline markers for "synergy" (jargon), "http://..." (link), etc.
- **Data structure:** `penalty_phrases: [{phrase, severity, category}]`

**5. Community averages drive post scoring**

- **Context:** Post scores calculated relative to community norms (formality, rhythm)
- **Decision:** Calculate community averages first, then score each post using those averages
- **Impact:** Score reflects "how well does this post match r/SaaS behavior" not absolute quality
- **Formula:** `calculate_post_score(post_data, community_avg)` uses avg_sentence_length, formality_level

## Deviations from Plan

None - plan executed exactly as written.

## Issues and Blockers

**Resolved:**

- None

**Future considerations:**

1. **syntax_blacklist table not yet created** - add_custom_pattern wrapped in try/except to handle gracefully until migration added
2. **Sorting by JSONB fields** - get_analyzed_posts sorts by success_score column (mirrors rhythm_metadata->total_score) because Supabase doesn't support JSONB path sorting easily
3. **Custom pattern match counts** - Custom patterns return count=0 because they haven't been run through pattern extractor yet (future enhancement)

## Next Phase Readiness

**Phase 3 Plan 3 (Analysis UI):**
- Analysis service ready ✓
- SSE endpoint ready ✓
- Community profile data structure ready ✓
- Scoring breakdown with penalty phrases ready ✓

**Phase 4 (Generation):**
- Community profiles available as context for LLM prompt ✓
- Top success hooks available as examples ✓
- Forbidden patterns available for post validation ✓
- ISC score available for content strategy decisions ✓

**Blockers:** None

**Dependencies satisfied:**
- 03-01 (NLP pipeline): analyze_posts_batch, calculate_post_score, calculate_isc_score, extract_forbidden_patterns all imported ✓

**Ready for:** 03-03 (Analysis UI components), 04-01 (Generation service)

## Self-Check: PASSED

Files verified:
- bc-rao-api/app/services/analysis_service.py ✓
- bc-rao-api/app/workers/analysis_worker.py ✓

Commits verified:
- 0cff7f8 ✓
- 677a9e6 ✓
