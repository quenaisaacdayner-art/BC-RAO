---
phase: 02-collection-pipeline
plan: 03
subsystem: ui
tags: [nextjs, sse, shadcn-ui, progress-tracking, eventSource]

# Dependency graph
requires:
  - phase: 02-02
    provides: FastAPI collection endpoints with SSE progress streaming
provides:
  - Collection trigger page at /dashboard/campaigns/[id]/collect
  - Live SSE progress tracker with funnel stats
  - SSE proxy routes bridging Next.js to FastAPI
  - Shadcn UI components (progress, dialog, slider, select, badge)
affects: [02-04-browsing-interface, 03-analyzer, 04-generator]

# Tech tracking
tech-stack:
  added: [Shadcn progress, dialog, slider, select, badge components]
  patterns: [SSE proxy pattern for backend streaming, EventSource cleanup pattern, navigation guards during async operations]

key-files:
  created:
    - bc-rao-frontend/app/dashboard/campaigns/[id]/collect/page.tsx
    - bc-rao-frontend/components/collection/ProgressTracker.tsx
    - bc-rao-frontend/app/api/collection/[taskId]/progress/route.ts
    - bc-rao-frontend/app/api/campaigns/[id]/collect/route.ts
    - bc-rao-frontend/components/ui/progress.tsx
    - bc-rao-frontend/components/ui/dialog.tsx
    - bc-rao-frontend/components/ui/slider.tsx
    - bc-rao-frontend/components/ui/select.tsx
    - bc-rao-frontend/components/ui/badge.tsx
  modified: []

key-decisions:
  - "SSE proxy routes authenticate ownership but stream task progress without auth (task_id acts as bearer token)"
  - "EventSource cleanup in useEffect return to prevent connection leaks"
  - "Three-phase collection flow: idle → collecting → complete"
  - "Navigation guard warns users during active collection"
  - "Hardcoded remaining runs display (billing enforcement deferred to Phase 6)"

patterns-established:
  - "SSE Proxy Pattern: Next.js API routes stream FastAPI SSE responses to browser EventSource"
  - "EventSource Cleanup: Always close() in useEffect cleanup to prevent memory leaks"
  - "Progress Tracking: Live funnel stats (scraped → filtered → classified) with animated counters"

# Metrics
duration: 7min
completed: 2026-02-10
---

# Phase 2 Plan 3: Collection UI Summary

**Live collection trigger page with SSE progress tracking showing real-time funnel stats (scraped → filtered → classified) across target subreddits**

## Performance

- **Duration:** 7 min
- **Started:** 2026-02-10T17:13:39Z
- **Completed:** 2026-02-10T17:20:40Z
- **Tasks:** 2
- **Files modified:** 11

## Accomplishments
- Collection page with three-phase flow (idle → collecting → complete) and navigation guards
- Live SSE progress tracker displaying current subreddit, step count, and funnel stats
- SSE proxy routes bridging Next.js EventSource to FastAPI streaming endpoints
- Installed 5 Shadcn UI components for current and future phase 2 features
- EventSource connection properly cleaned up on unmount to prevent leaks

## Task Commits

Each task was committed atomically:

1. **Task 1: Install Shadcn UI components + SSE proxy route** - `9fc4b64` (chore)
   - Installed progress, dialog, slider, select, badge via Shadcn CLI
   - Created SSE proxy at /api/collection/[taskId]/progress
   - Created collection trigger at /api/campaigns/[id]/collect

2. **Task 2: Collection page with trigger and live progress** - `149b677` (feat)
   - Built ProgressTracker component with EventSource SSE connection
   - Built collection page with idle/collecting/complete phases
   - Navigation guard warns on beforeunload during collection
   - Displays remaining runs count (hardcoded for trial tier)

## Files Created/Modified

- `bc-rao-frontend/app/dashboard/campaigns/[id]/collect/page.tsx` - Collection page with three-phase flow, trigger button, navigation guard
- `bc-rao-frontend/components/collection/ProgressTracker.tsx` - Live SSE progress component with funnel stats display
- `bc-rao-frontend/app/api/collection/[taskId]/progress/route.ts` - SSE proxy streaming FastAPI progress events
- `bc-rao-frontend/app/api/campaigns/[id]/collect/route.ts` - Collection trigger proxy with ownership validation
- `bc-rao-frontend/components/ui/progress.tsx` - Shadcn progress bar component
- `bc-rao-frontend/components/ui/dialog.tsx` - Shadcn dialog component (for Plan 04)
- `bc-rao-frontend/components/ui/slider.tsx` - Shadcn slider component (for Plan 04)
- `bc-rao-frontend/components/ui/select.tsx` - Shadcn select component (for Plan 04)
- `bc-rao-frontend/components/ui/badge.tsx` - Shadcn badge component (archetype tags)

## Decisions Made

**1. SSE proxy pattern for EventSource**
- Rationale: Browser EventSource can't send Authorization headers, Next.js API routes proxy to FastAPI with auth validation
- Impact: Clean separation - ownership validated on trigger, task_id acts as unguessable bearer for progress stream

**2. EventSource cleanup in useEffect return**
- Rationale: Without cleanup, EventSource connections persist after component unmount causing memory leaks
- Impact: Proper resource management, no connection leaks

**3. Hardcoded remaining runs display**
- Rationale: Billing limits deferred to Phase 6 per project decision, hardcode "5 remaining" for trial tier
- Impact: UI shows correct UX pattern, backend enforcement added in Phase 6

**4. Three-phase collection flow**
- Rationale: Clear user journey from trigger → monitoring → completion with appropriate actions at each stage
- Impact: Professional UX with navigation guards, auto-transition to results, retry capability

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed import error in ProgressTracker**
- **Found during:** Task 2 (initial build)
- **Issue:** Attempted to import Alert/AlertDescription from alert-dialog component which doesn't export them
- **Fix:** Removed invalid import, used simple div styling for error/success/warning states
- **Files modified:** bc-rao-frontend/components/collection/ProgressTracker.tsx
- **Verification:** Build succeeded with zero TypeScript errors
- **Committed in:** 149b677 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Necessary fix for correct TypeScript compilation. No scope creep.

## Issues Encountered

None - plan executed smoothly.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

**Ready for Plan 04 (Browsing Interface):**
- Collection page complete with SSE progress tracking
- Badge component ready for archetype tags
- Dialog, slider, select components ready for filtering UI
- Collection trigger returns to /dashboard/campaigns/[id]/browse (to be built)

**No blockers:**
- All Shadcn components installed and working
- SSE proxy pattern established and tested
- Build succeeds with zero errors

## Self-Check: PASSED

All files created:
- ✓ bc-rao-frontend/app/dashboard/campaigns/[id]/collect/page.tsx
- ✓ bc-rao-frontend/components/collection/ProgressTracker.tsx
- ✓ bc-rao-frontend/app/api/collection/[taskId]/progress/route.ts
- ✓ bc-rao-frontend/app/api/campaigns/[id]/collect/route.ts
- ✓ bc-rao-frontend/components/ui/progress.tsx
- ✓ bc-rao-frontend/components/ui/dialog.tsx
- ✓ bc-rao-frontend/components/ui/slider.tsx
- ✓ bc-rao-frontend/components/ui/select.tsx
- ✓ bc-rao-frontend/components/ui/badge.tsx

All commits verified:
- ✓ 9fc4b64 (Task 1)
- ✓ 149b677 (Task 2)

---
*Phase: 02-collection-pipeline*
*Completed: 2026-02-10*
