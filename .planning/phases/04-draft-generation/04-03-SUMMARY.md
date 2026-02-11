---
phase: 04-draft-generation
plan: 03
subsystem: ui
tags: [nextjs, react-hook-form, sse, streaming, isc-gating, draft-ui]

# Dependency graph
requires:
  - phase: 04-02
    provides: Draft generation API endpoints with SSE streaming
  - phase: 03-03
    provides: Community profiles with ISC scores and tiers
  - phase: 02-03
    provides: SSE proxy pattern and EventSource cleanup
provides:
  - Generation form with ISC gating UX (inline warning + auto-switch to Feedback)
  - Real-time SSE streaming feedback during draft generation
  - Draft list page with status and subreddit filtering
  - Warning system for unprofiled subreddits
affects: [04-04-draft-editor, generation-ux-refinement]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - ISC gating UX pattern (inline warning banner + archetype auto-switch)
    - SSE streaming progress during generation with EventSource cleanup
    - Single-form generation (not wizard) with three inputs only
    - Draft card component for list views with score preview

key-files:
  created:
    - bc-rao-frontend/components/drafts/ISCGatingWarning.tsx
    - bc-rao-frontend/components/drafts/GenerationForm.tsx
    - bc-rao-frontend/components/drafts/DraftCard.tsx
    - bc-rao-frontend/app/dashboard/campaigns/[id]/drafts/new/page.tsx
    - bc-rao-frontend/app/dashboard/campaigns/[id]/drafts/page.tsx
  modified: []

key-decisions:
  - "ISC gating enforced on frontend: inline warning + auto-switch to Feedback when ISC > 7.5"
  - "Unprofiled subreddits show yellow warning but allow generation with generic defaults"
  - "Single-form UX (not wizard) with three inputs: subreddit, archetype, context"
  - "EventSource cleanup pattern in useEffect return to prevent connection leaks"
  - "Draft cards navigate to draft editor on click for quick editing workflow"

patterns-established:
  - "ISC gating warning pattern: orange AlertTriangle banner for high sensitivity communities"
  - "Form validation with React Hook Form + Zod for generation inputs"
  - "SSE progress tracking with EventSource cleanup on unmount"
  - "Draft filtering by status and subreddit with responsive grid layout"

# Metrics
duration: 6min
completed: 2026-02-11
---

# Phase 04 Plan 03: Drafts Frontend Summary

**Generation form with ISC gating UX, SSE streaming progress, and draft list with filtering**

## Performance

- **Duration:** 6 min
- **Started:** 2026-02-11T03:01:27Z
- **Completed:** 2026-02-11T03:07:34Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- Single-form generation page with subreddit dropdown, archetype selector, and context textarea
- ISC gating warning appears for communities with ISC > 7.5 and auto-switches to Feedback archetype
- Real-time SSE streaming shows generation progress with automatic redirect to draft editor
- Draft list page with status and subreddit filters displays all campaign drafts in responsive grid
- Unprofiled subreddits show warning but still allow generation with generic defaults

## Task Commits

Each task was committed atomically:

1. **Task 1: Next.js API proxy routes for draft generation** - `c31c792` (feat) - Already existed from previous session
2. **Task 2: Generation form page with ISC gating and draft list** - `8d5fa3a` (feat)

## Files Created/Modified
- `bc-rao-frontend/components/drafts/ISCGatingWarning.tsx` - Orange warning banner for high ISC communities (> 7.5)
- `bc-rao-frontend/components/drafts/GenerationForm.tsx` - Single-form with subreddit dropdown, archetype selector, context textarea, ISC auto-switching
- `bc-rao-frontend/components/drafts/DraftCard.tsx` - Card showing archetype badge, subreddit, body preview, scores, status
- `bc-rao-frontend/app/dashboard/campaigns/[id]/drafts/new/page.tsx` - Generation page with SSE streaming progress and automatic redirect
- `bc-rao-frontend/app/dashboard/campaigns/[id]/drafts/page.tsx` - Draft list with status/subreddit filtering and empty state

## Decisions Made

**ISC gating UX pattern:**
- High ISC (> 7.5) communities show inline orange warning banner
- Archetype selector auto-switches to Feedback and disables other options
- Warning text explains ISC score and tier, mentions zero-link restriction
- Enforces safety on frontend to prevent risky archetype selection

**Unprofiled subreddit handling:**
- All campaign subreddits shown in dropdown, marked "(No profile)" if not analyzed
- Yellow warning banner appears when unprofiled subreddit selected
- Generation still allowed (backend uses generic defaults)
- Warns user that accuracy may be reduced without community profile

**Single-form generation flow:**
- NOT a wizard - one page with three inputs only
- Subreddit → Archetype → Optional Context → Generate button
- SSE streaming shows real-time progress during generation
- Auto-redirects to draft editor on completion
- EventSource properly cleaned up on unmount to prevent connection leaks

**Draft list filtering:**
- Status filter: all, pending, ready, discarded
- Subreddit filter: all campaign subreddits
- Empty state with "Generate First Draft" button when no drafts exist
- Responsive grid layout (1 col mobile, 2 cols tablet, 3 cols desktop)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - all components integrated smoothly with existing SSE proxy pattern and community profile data.

## User Setup Required

None - uses existing Supabase session and API proxy routes from previous phases.

## Next Phase Readiness

**Ready for Phase 04-04 (Draft Editor):**
- Generation form triggers draft creation and redirects to editor
- Draft list page links to editor on card click
- DraftCard component ready for integration into editor navigation
- SSE streaming pattern established for real-time feedback

**Ready for Phase 04-05 (Dashboard Journey Stages):**
- Generation page can be integrated into Stage 4 (Alchemical Transmutation)
- Draft count can be used for stage completion indicators
- ISC gating enforces safety before user even reaches editor

**No blockers.** All generation frontend components operational.

## Self-Check: PASSED

All key files verified on disk.
All commits verified in git history.

---
*Phase: 04-draft-generation*
*Completed: 2026-02-11*
