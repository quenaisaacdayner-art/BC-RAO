---
phase: 02-collection-pipeline
plan: 02
subsystem: api
tags: [celery, fastapi, sse, asyncio, server-sent-events, streaming, redis]

# Dependency graph
requires:
  - phase: 02-01
    provides: CollectionService with full pipeline orchestration
  - phase: 01-04
    provides: Celery app configuration with task routing
  - phase: 01-03
    provides: Auth dependencies for protected endpoints
provides:
  - Celery worker task for async collection execution with progress tracking
  - FastAPI endpoints for triggering collection and monitoring progress
  - SSE endpoint for real-time progress streaming
  - REST endpoints for querying collected posts with filters
affects: [03-analysis-pipeline, frontend-dashboard]

# Tech tracking
tech-stack:
  added: [celery.result.AsyncResult, asyncio.run for sync/async bridging]
  patterns: [SSE streaming with StreamingResponse, Celery task state polling, async generator functions]

key-files:
  created:
    - bc-rao-api/app/workers/collection_worker.py
    - bc-rao-api/app/api/v1/collection.py
  modified:
    - bc-rao-api/app/api/v1/router.py

key-decisions:
  - "SSE endpoint has no authentication (task_id acts as unguessable bearer token)"
  - "Bridge async CollectionService to sync Celery with asyncio.run()"
  - "Poll task state every 500ms for SSE progress updates"
  - "Guard progress callbacks with called_directly check for testability"

patterns-established:
  - "SSE streaming pattern: async generator with StreamingResponse and proper headers"
  - "Celery progress tracking: bind=True with update_state() in PROGRESS state"
  - "Task routing by naming convention: app.workers.tasks.{queue}.* routes to queue"

# Metrics
duration: 5min
completed: 2026-02-10
---

# Phase 02 Plan 02: Collection Pipeline API Integration Summary

**Celery worker with PROGRESS state tracking and FastAPI endpoints exposing async collection via SSE streaming, plus filtered post queries**

## Performance

- **Duration:** 5 min
- **Started:** 2026-02-10T04:53:02Z
- **Completed:** 2026-02-10T01:56:45Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Celery worker task bridges async CollectionService to sync Celery via asyncio.run()
- Real-time progress tracking via self.update_state() with PROGRESS meta
- SSE endpoint streams progress events every 500ms from Celery AsyncResult
- Five REST endpoints: trigger, progress stream, fetch posts, post detail, collection stats
- Post filtering by archetype, subreddit, and success score range with pagination

## Task Commits

Each task was committed atomically:

1. **Task 1: Celery collection worker with progress tracking** - `db4ca68` (feat)
2. **Task 2: FastAPI collection endpoints - trigger, SSE progress, fetch posts** - `fbde55b` (feat)

## Files Created/Modified
- `bc-rao-api/app/workers/collection_worker.py` - Celery task named "app.workers.tasks.scraping.collect_campaign_data" routes to scraping queue, emits PROGRESS state with scraped/filtered/classified counters
- `bc-rao-api/app/api/v1/collection.py` - Five endpoints: POST /campaigns/{id}/collect (202 Accepted), GET /collection/{task_id}/progress (SSE stream), GET /campaigns/{id}/posts (filtered list), GET /campaigns/{id}/posts/{post_id} (detail), GET /campaigns/{id}/collection-stats (aggregated)
- `bc-rao-api/app/api/v1/router.py` - Registered collection router in v1 API router

## Decisions Made

**1. SSE endpoint authentication strategy**
- SSE endpoint requires no authentication - task_id is unguessable UUID acting as bearer token
- Simplifies client-side EventSource usage (no custom headers support in browser EventSource API)
- Security maintained via UUID unpredictability (128-bit entropy)

**2. Async/sync bridging approach**
- Used asyncio.run() to bridge async CollectionService methods to sync Celery task
- Alternative (get_event_loop().run_until_complete) avoided due to nested event loop risks
- Guard progress callbacks with called_directly check for direct testing without Celery

**3. SSE polling interval**
- 500ms poll interval balances responsiveness with Redis/Celery load
- Faster than 1s provides smooth progress bar updates
- Slower than 100ms avoids excessive backend polling

**4. Billing limit enforcement deferred**
- Trigger endpoint does NOT enforce billing limits (deferred to Phase 6 per user decision)
- Focus on core loop functionality before monetization layer
- Plan tier passed to CollectionService for future quota checks

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - all integrations worked as expected.

## User Setup Required

None - no external service configuration required. Celery and Redis already configured in Phase 01-04.

## Next Phase Readiness

**Ready for:**
- Phase 03 (Analysis Pipeline) can consume collected posts from raw_posts table
- Frontend dashboard can trigger collection and display progress via SSE stream
- Post filtering UI can use archetype/subreddit/score filters with pagination

**Blockers/Concerns:**
- None

**Tech debt:**
- None

## Self-Check: PASSED

All files verified:
- ✓ bc-rao-api/app/workers/collection_worker.py exists
- ✓ bc-rao-api/app/api/v1/collection.py exists
- ✓ bc-rao-api/app/api/v1/router.py exists

All commits verified:
- ✓ db4ca68 (Task 1)
- ✓ fbde55b (Task 2)

---
*Phase: 02-collection-pipeline*
*Completed: 2026-02-10*
