---
phase: 04-draft-generation
plan: 04
subsystem: frontend
tags: [nextjs, react, draft-editor, score-visualization, ssr, clipboard]

# Dependency graph
requires:
  - phase: 01-foundation
    provides: Next.js setup, shadcn/ui components, Supabase client
  - phase: 03-pattern-engine
    provides: ISCGauge component pattern for radial score gauges
  - phase: 04-02
    provides: Draft CRUD endpoints, regeneration with SSE streaming
provides:
  - Full-page draft editor with two-column layout (text left, scores/actions right)
  - Score visualization with radial gauges for vulnerability and rhythm match
  - Four draft actions (Approve, Copy, Regenerate with feedback, Discard)
  - Copy to clipboard functionality with visual feedback
  - SSE integration for regeneration progress tracking
affects: [04-05-dashboard-journey, user-draft-workflow]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Two-column editor layout (text editor left, sidebar right)
    - Radial gauge pattern reused from ISCGauge for score visualization
    - Copy to clipboard with icon toggle feedback (Copy → Check for 2s)
    - Collapsible regeneration feedback textarea
    - SSE progress tracking for regeneration with EventSource cleanup

key-files:
  created:
    - bc-rao-frontend/app/api/drafts/[draftId]/route.ts
    - bc-rao-frontend/app/api/drafts/[draftId]/regenerate/route.ts
    - bc-rao-frontend/components/drafts/CopyButton.tsx
    - bc-rao-frontend/components/drafts/ScoreSidebar.tsx
    - bc-rao-frontend/components/drafts/DraftActions.tsx
    - bc-rao-frontend/components/drafts/DraftEditor.tsx
    - bc-rao-frontend/app/dashboard/campaigns/[id]/drafts/[draftId]/edit/page.tsx
  modified: []

key-decisions:
  - "Two-column layout: plain textarea with monospace font on left, scores and actions sidebar on right"
  - "Scores display as radial gauges (0-10 scale) with tier coloring (Excellent/Good/Moderate/Low)"
  - "No re-scoring on manual edits - scores reflect generated draft only, editing is free-form"
  - "Copy button shows Check icon for 2 seconds after successful copy"
  - "Regenerate action shows collapsible feedback textarea - can provide guidance or leave blank"
  - "All actions redirect back to campaign page on completion"
  - "SSE used for regeneration progress tracking, EventSource cleanup on unmount"

patterns-established:
  - "Draft editor layout: DraftEditor wraps textarea + ScoreSidebar + DraftActions"
  - "Score gauge reuse: ScoreSidebar uses same Progress component pattern as ISCGauge"
  - "Action flow: Approve/Discard call PATCH/DELETE then redirect, Regenerate triggers SSE then redirects to new draft"
  - "Copy button pattern: navigator.clipboard.writeText with 2-second visual feedback"

# Metrics
duration: 4min
completed: 2026-02-11
---

# Phase 04 Plan 04: Draft Editor UI Summary

**Full-page draft editor with score visualization, four action buttons, and SSE-powered regeneration**

## Performance

- **Duration:** 4 min
- **Started:** 2026-02-11T00:02:01Z
- **Completed:** 2026-02-11T00:05:59Z
- **Tasks:** 2
- **Files created:** 7

## Accomplishments
- Full-page draft editor with two-column layout operational (text editor left, scores/actions right)
- Score visualization with radial gauges for vulnerability and rhythm match scores
- Four draft actions implemented: Approve, Copy to clipboard, Regenerate with feedback, Discard
- Copy button provides visual feedback (Check icon for 2 seconds after copy)
- Regenerate action supports optional feedback textarea for iteration guidance
- SSE integration for real-time regeneration progress tracking
- All actions properly redirect back to campaign page on completion

## Task Commits

Each task was committed atomically:

1. **Task 1: Next.js API proxy routes for draft operations** - `c31c792` (feat)
2. **Task 2: Draft editor with score sidebar and action buttons** - `72189af` (feat)

## Files Created/Modified
- `bc-rao-frontend/app/api/drafts/[draftId]/route.ts` - GET/PATCH/DELETE proxy routes for single draft operations
- `bc-rao-frontend/app/api/drafts/[draftId]/regenerate/route.ts` - POST proxy route for regeneration with task_id return
- `bc-rao-frontend/components/drafts/CopyButton.tsx` - Copy to clipboard with Check icon feedback
- `bc-rao-frontend/components/drafts/ScoreSidebar.tsx` - Radial gauges for vulnerability and rhythm match scores plus metadata
- `bc-rao-frontend/components/drafts/DraftActions.tsx` - Four action buttons (Approve, Copy, Regenerate, Discard)
- `bc-rao-frontend/components/drafts/DraftEditor.tsx` - Two-column layout wrapper component
- `bc-rao-frontend/app/dashboard/campaigns/[id]/drafts/[draftId]/edit/page.tsx` - Full draft editor page with SSE integration

## Decisions Made

**Two-column editor layout:**
- Plain textarea with monospace font on left for draft text editing
- Scores and actions sidebar on right (320px fixed width on lg+ screens)
- Responsive: stacks vertically on mobile (grid-cols-1 on sm)

**Score visualization:**
- Radial gauges reuse Progress component pattern from ISCGauge
- 0-10 scale with tier coloring: Excellent (8-10, green), Good (6-8, blue), Moderate (4-6, yellow), Low (0-4, red)
- Display vulnerability score and rhythm match score separately
- Metadata section shows subreddit, archetype, generated timestamp

**No re-scoring on edits:**
- Scores reflect the generated draft only
- Manual editing is free-form with no re-scoring
- Note displayed in sidebar: "Scores reflect the generated draft only. Manual editing is free-form and does not trigger re-scoring."

**Copy to clipboard:**
- Uses navigator.clipboard.writeText() browser API
- Icon toggle: Copy → Check for 2 seconds after successful copy
- Copies current edited text (not original generated text)

**Regenerate with feedback:**
- Collapsible feedback textarea appears when Regenerate clicked
- User can provide guidance or leave blank for different variation
- Triggers POST to regeneration endpoint, receives task_id
- SSE tracking via EventSource for progress updates
- Redirects to new draft edit page on completion
- EventSource cleanup on unmount to prevent connection leaks

**Action redirects:**
- Approve: PATCH status=approved + body=editedText, redirect to campaign page
- Discard: DELETE draft, redirect to campaign page
- Regenerate: POST with feedback, SSE tracking, redirect to new draft on complete
- All actions disable buttons during processing to prevent double-clicks

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - all components render correctly, SSE pattern well-established from Phase 2, radial gauge pattern reused from Phase 3.

## User Setup Required

None - uses existing shadcn/ui components (Button, Card, Textarea, Progress, Separator, Label) and Supabase client from Phase 1.

## Next Phase Readiness

**Ready for Phase 04-05 (Dashboard Journey Stages):**
- Draft editor route `/dashboard/campaigns/[id]/drafts/[draftId]/edit` operational
- Score visualization matches ISCGauge pattern from community profiles
- All four draft actions functional (approve, copy, regenerate, discard)
- SSE integration ready for regeneration progress tracking
- Copy to clipboard enables pasting into Reddit

**No blockers.** Draft editor UI complete with all required functionality.

## Self-Check: PASSED

All key files verified on disk.
All commits verified in git history.

---
*Phase: 04-draft-generation*
*Completed: 2026-02-11*
