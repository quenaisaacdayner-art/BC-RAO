---
phase: 04-draft-generation
plan: 02
subsystem: api
tags: [fastapi, sse, streaming, celery, background-tasks, draft-api, plan-limits]

# Dependency graph
requires:
  - phase: 01-foundation
    provides: FastAPI setup, JWT auth, Supabase integration, error handling
  - phase: 02-collection
    provides: SSE streaming pattern, background task pattern
  - phase: 04-01
    provides: GenerationService with full CRUD operations
provides:
  - FastAPI endpoints for draft generation, listing, updating, regenerating, deleting
  - SSE streaming for real-time generation progress
  - Monthly plan limit enforcement (trial=10, starter=50, growth=unlimited)
  - Celery worker tasks for background generation (horizontal scaling ready)
affects: [04-03-drafts-frontend, generation-workflows]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - SSE streaming for generation progress (500ms polling interval)
    - Monthly draft limit enforcement before generation trigger
    - Background task pattern with Redis state tracking
    - Async/sync bridging in Celery tasks (asyncio.run)

key-files:
  created:
    - bc-rao-api/app/api/v1/drafts.py
    - bc-rao-api/app/workers/generation_worker.py
  modified:
    - bc-rao-api/app/api/v1/router.py

key-decisions:
  - "Monthly plan limits enforced on both generate and regenerate endpoints (403 PLAN_LIMIT_REACHED)"
  - "SSE streaming endpoint no authentication (task_id acts as unguessable UUID bearer token)"
  - "Background tasks via asyncio (Railway) + Celery tasks preserved for horizontal scaling"
  - "Progress events match GenerationService pipeline: Loading profile → ISC gating → Building prompt → Generating → Validating → Scoring → Saving"

patterns-established:
  - "Plan limit check pattern: check_monthly_draft_limit() helper function called before generation trigger"
  - "Background task pattern: run_generation_background() + run_regeneration_background() functions in endpoints file"
  - "SSE event types: status (progress messages), complete (final draft), error (failures), done (stream close)"
  - "Regeneration preserves original draft params and appends feedback to context (via GenerationService)"

# Metrics
duration: 4min
completed: 2026-02-10
---

# Phase 04 Plan 02: Drafts API Endpoints Summary

**FastAPI endpoints for draft generation with SSE streaming, CRUD operations, and monthly plan limit enforcement**

## Performance

- **Duration:** 4 min
- **Started:** 2026-02-10T23:53:17Z
- **Completed:** 2026-02-10T23:57:36Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Six draft endpoints operational: generate (POST with SSE stream), list (GET), update (PATCH), regenerate (POST), delete (DELETE)
- SSE streaming delivers real-time progress during generation (Loading profile → Generating → Validating → Saving)
- Monthly plan limits prevent abuse (trial=10, starter=50, growth=unlimited drafts/month)
- Celery worker tasks ready for horizontal scaling (Railway uses lightweight task_runner)

## Task Commits

Each task was committed atomically:

1. **Task 1: FastAPI draft endpoints with SSE streaming** - `7f75324` (feat)
2. **Task 2: Celery generation worker with progress tracking** - `31f4718` (feat)

## Files Created/Modified
- `bc-rao-api/app/api/v1/drafts.py` - Six draft endpoints with SSE streaming for generation progress
- `bc-rao-api/app/workers/generation_worker.py` - Celery tasks for background generation and regeneration
- `bc-rao-api/app/api/v1/router.py` - Updated to include drafts router with tags

## Decisions Made

**Monthly plan limit enforcement:**
- Trial tier: 10 drafts/month
- Starter tier: 50 drafts/month
- Growth tier: Unlimited (-1 in PLAN_LIMITS)
- Limits checked before both generate and regenerate endpoints
- Returns 403 with PLAN_LIMIT_REACHED error code when exceeded

**SSE streaming pattern:**
- No authentication on stream endpoint (task_id acts as bearer token)
- Follows established collection.py pattern (500ms polling interval)
- Event types: pending, started, progress, success, error, done
- Progress events emit status messages during generation pipeline phases

**Background task architecture:**
- Railway deployment uses asyncio background tasks (run_generation_background, run_regeneration_background)
- Celery tasks preserved for horizontal scaling (generate_draft_task, regenerate_draft_task)
- Both use identical progress tracking and state management
- Tasks route to "generation" queue via Celery routing config

**Regeneration preserves context:**
- Loads original draft parameters from database
- Appends user feedback to original context
- Creates new draft (doesn't modify original)
- Counts toward monthly limit like new generation

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - all endpoints verified, SSE streaming pattern well-established from Phase 2.

## User Setup Required

None - endpoints use existing Supabase integration and GenerationService from Plan 01.

## Next Phase Readiness

**Ready for Phase 04-03 (Drafts Frontend):**
- POST /campaigns/:id/drafts/generate returns task_id for SSE tracking
- SSE stream delivers progress events for UI progress bar
- GET /campaigns/:id/drafts supports status and subreddit filtering
- PATCH /drafts/:id allows approving, discarding, editing drafts
- POST /drafts/:id/regenerate supports user feedback iteration

**No blockers.** All draft CRUD operations operational via API.

## Self-Check: PASSED

All key files verified on disk.
All commits verified in git history.

---
*Phase: 04-draft-generation*
*Completed: 2026-02-10*
