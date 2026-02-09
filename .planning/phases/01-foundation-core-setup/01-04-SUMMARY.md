---
phase: 01-foundation-core-setup
plan: 04
subsystem: infra
tags: [celery, redis, openrouter, cost-tracking, background-workers, llm]

# Dependency graph
requires:
  - phase: 01-01
    provides: FastAPI scaffold with config, error handling, Supabase integration
provides:
  - Celery worker infrastructure with 4 task queues (scraping, analysis, generation, monitoring)
  - InferenceClient abstraction for OpenRouter with per-task model routing
  - CostTracker enforcing plan caps before LLM calls
  - UsageService for FastAPI endpoints
affects: [01-05, 02-pattern-engine, 03-content-generation, 04-monitoring-orchestrator]

# Tech tracking
tech-stack:
  added: [celery[redis], redis, httpx (already present)]
  patterns: [task-based model routing, budget-first inference calls, usage tracking per action type]

key-files:
  created:
    - bc-rao-api/app/workers/celery_app.py
    - bc-rao-api/app/workers/__init__.py
    - bc-rao-api/app/inference/client.py
    - bc-rao-api/app/inference/router.py
    - bc-rao-api/app/inference/cost_tracker.py
    - bc-rao-api/app/services/usage_service.py
    - bc-rao-api/docker-compose.yml
  modified:
    - bc-rao-api/pyproject.toml

key-decisions:
  - "JSON serialization for Celery tasks (security: no pickle)"
  - "Task routing by namespace pattern (app.workers.tasks.{queue}.*)"
  - "Budget checked BEFORE each LLM call to prevent overruns"
  - "Fallback model on primary failure for resilience"
  - "Cost estimation per model tier (production: parse from OpenRouter headers)"

patterns-established:
  - "InferenceClient(task=) pattern: task-based model resolution"
  - "CostTracker as service dependency for all LLM calls"
  - "usage_tracking table as source of truth for budget checks"

# Metrics
duration: 6min
completed: 2026-02-09
---

# Phase 01 Plan 04: Worker Infrastructure Summary

**Celery worker with 4 queues and InferenceClient for OpenRouter with per-task model routing and plan cap enforcement**

## Performance

- **Duration:** 6 minutes (332 seconds)
- **Started:** 2026-02-09T20:22:37Z
- **Completed:** 2026-02-09T20:28:09Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments
- Celery worker infrastructure configured with Redis backend and 4 task queues (scraping, analysis, generation, monitoring)
- InferenceClient abstraction routes 4 task types to appropriate OpenRouter models (Haiku for cheap tasks, Sonnet-4 for generation)
- CostTracker enforces plan caps ($5 trial, $15 starter, $40 growth) before every LLM call
- Automatic fallback to secondary models on primary failure for resilience
- All usage tracked to usage_tracking table with token counts and costs

## Task Commits

Each task was committed atomically:

1. **Task 1: Celery + Redis worker infrastructure with docker-compose** - `83a5f8c` (feat)
2. **Task 2: InferenceClient with model routing and cost tracking** - `a87448a` (feat)

## Files Created/Modified
- `bc-rao-api/app/workers/celery_app.py` - Celery app with 4 task queues, JSON serialization, acks_late for reliability
- `bc-rao-api/app/workers/__init__.py` - Re-exports celery_app and ping test task
- `bc-rao-api/docker-compose.yml` - Redis 7 service and worker service definitions
- `bc-rao-api/app/inference/router.py` - MODEL_ROUTING dict mapping tasks to models, COST_CAPS per plan
- `bc-rao-api/app/inference/client.py` - InferenceClient with OpenRouter API calls, budget checking, fallback handling
- `bc-rao-api/app/inference/cost_tracker.py` - CostTracker for budget checks and usage recording
- `bc-rao-api/app/services/usage_service.py` - UsageService for FastAPI endpoints
- `bc-rao-api/pyproject.toml` - Added celery[redis] and redis dependencies

## Decisions Made

**JSON serialization for Celery (not pickle):** Security best practice. Pickle serialization can execute arbitrary code.

**Task routing by namespace pattern:** `app.workers.tasks.{queue}.*` routes to appropriate queue automatically. Cleaner than explicit routing per task.

**Budget checked BEFORE each LLM call:** Prevents mid-call failures and partial usage. User sees PLAN_LIMIT_REACHED immediately.

**Fallback model on primary failure:** Improves reliability. If Claude Haiku fails, try Gemini Flash. Users get response even if primary provider has issues.

**Cost estimation per model tier:** Simplified calculation for MVP. Production should parse actual cost from OpenRouter response headers for accuracy.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Installed celery and redis dependencies**
- **Found during:** Task 1 verification
- **Issue:** celery and redis packages not installed, preventing imports
- **Fix:** Ran `pip install "celery[redis]>=5.3.0" "redis>=5.0.0"` and added to pyproject.toml
- **Files modified:** pyproject.toml (committed), pip installation (runtime)
- **Verification:** Import succeeds, Celery app name prints correctly
- **Committed in:** 83a5f8c (Task 1 commit includes pyproject.toml update)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Necessary for code execution. No scope creep.

## Issues Encountered
None - plan executed smoothly after dependency installation.

## User Setup Required
None - no external service configuration required. Redis runs via docker-compose.

However, for production use:
- Set OPENROUTER_API_KEY in .env
- Set REDIS_URL, CELERY_BROKER_URL, CELERY_RESULT_BACKEND in .env
- Run `docker-compose up -d` to start Redis and worker

## Next Phase Readiness
- Worker infrastructure ready for Module 1 (collection tasks), Module 2 (analysis tasks), Module 3 (generation tasks), Module 4 (monitoring tasks)
- InferenceClient ready for use in Modules 1-3 for LLM calls
- Cost tracking prevents budget overruns - safe to start processing user data
- Need: Actual task implementations in app/workers/tasks/ (coming in module plans)

---
*Phase: 01-foundation-core-setup*
*Completed: 2026-02-09*

## Self-Check: PASSED

All files verified:
- bc-rao-api/app/workers/celery_app.py ✓
- bc-rao-api/app/workers/__init__.py ✓
- bc-rao-api/app/inference/client.py ✓
- bc-rao-api/app/inference/router.py ✓
- bc-rao-api/app/inference/cost_tracker.py ✓
- bc-rao-api/app/services/usage_service.py ✓
- bc-rao-api/docker-compose.yml ✓

All commits verified:
- 83a5f8c (Task 1: Celery worker infrastructure) ✓
- a87448a (Task 2: InferenceClient with model routing) ✓
