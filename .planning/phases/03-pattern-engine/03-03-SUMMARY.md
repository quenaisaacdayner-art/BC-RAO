---
phase: 03-pattern-engine
plan: 03
subsystem: ui
tags: [react, nextjs, recharts, sse, visualization, profiles]

# Dependency graph
requires:
  - phase: 03-02
    provides: Community profile analysis endpoints and SSE progress tracking
provides:
  - Community profiles comparison table showing ISC scores, tones, formality, archetypes
  - Tabbed profile detail pages with Summary, Archetypes, Rhythm, Forbidden Patterns sections
  - ISC gauge visualization with color-coded tiers
  - Archetype pie chart visualization
  - Analysis progress tracking with SSE and toast notifications
affects: [generation, monitoring]

# Tech tracking
tech-stack:
  added: [recharts, shadcn/ui tabs, shadcn/ui table]
  patterns: [SSE EventSource with cleanup, comparison table with sorting, tabbed detail views]

key-files:
  created:
    - bc-rao-frontend/app/api/campaigns/[id]/community-profiles/route.ts
    - bc-rao-frontend/app/api/campaigns/[id]/community-profile/route.ts
    - bc-rao-frontend/app/api/analysis/[taskId]/progress/route.ts
    - bc-rao-frontend/components/analysis/AnalysisProgress.tsx
    - bc-rao-frontend/components/analysis/ISCGauge.tsx
    - bc-rao-frontend/components/analysis/ArchetypePie.tsx
    - bc-rao-frontend/components/analysis/ComparisonTable.tsx
    - bc-rao-frontend/app/dashboard/campaigns/[id]/profiles/page.tsx
    - bc-rao-frontend/app/dashboard/campaigns/[id]/profiles/[subreddit]/page.tsx
  modified: []

key-decisions:
  - "Used Recharts for data visualization - donut charts for archetype distribution"
  - "ISC gauge uses color-coded progress bar with tier labels (Low/Moderate/High/Very High)"
  - "Comparison table sorts by ISC score by default (highest sensitivity first)"
  - "Analysis progress uses same SSE proxy pattern as collection progress"
  - "Toast notification on analysis complete with link to profiles page"
  - "Insufficient data subreddits show 'Need more data' instead of profile"

patterns-established:
  - "Visualization pattern: ISC gauge with numeric score, tier badge, color bar, and description"
  - "Tabbed detail pattern: Summary (metrics + gauge), Archetypes (chart + breakdown), Rhythm (sentence analysis), Forbidden Patterns (category counts)"
  - "SSE progress pattern: EventSource with cleanup in useEffect return, toast on complete"

# Metrics
duration: 9min
completed: 2026-02-11
---

# Phase 03 Plan 03: Community Profiles Frontend Summary

**Comparison table with sortable ISC scores and tabbed profile detail pages showing ISC gauge, archetype donut charts, rhythm analysis, and forbidden pattern categories**

## Performance

- **Duration:** 9 min
- **Started:** 2026-02-11T01:34:41Z
- **Completed:** 2026-02-11T01:43:39Z
- **Tasks:** 2
- **Files modified:** 9 created

## Accomplishments
- Users can view all subreddit profiles in sortable comparison table with ISC scores, tones, formality levels
- Individual subreddit profiles show tabbed sections: Summary with ISC gauge and key metrics, Archetypes with pie chart, Rhythm with sentence analysis, Forbidden Patterns with category counts
- ISC score visualization with color-coded tiers (green/yellow/orange/red for Low/Moderate/High/Very High sensitivity)
- Analysis progress tracking with SSE updates and toast notification on completion with link to profiles

## Task Commits

Each task was committed atomically:

1. **Task 1: Install Recharts + API proxy routes + analysis progress component** - `1d0b3cc` (chore)
2. **Task 2: Community profiles pages with comparison table + tabbed detail + chart components** - `28be1c4` (feat)

## Files Created/Modified
- `bc-rao-frontend/app/api/campaigns/[id]/community-profiles/route.ts` - Proxy to FastAPI list profiles endpoint with ownership validation
- `bc-rao-frontend/app/api/campaigns/[id]/community-profile/route.ts` - Proxy to FastAPI single profile endpoint with subreddit param
- `bc-rao-frontend/app/api/analysis/[taskId]/progress/route.ts` - SSE proxy for analysis progress (no auth, task_id as bearer)
- `bc-rao-frontend/components/analysis/AnalysisProgress.tsx` - SSE progress tracker with toast notification on complete
- `bc-rao-frontend/components/analysis/ISCGauge.tsx` - Color-coded gauge with score, tier label, progress bar, and description
- `bc-rao-frontend/components/analysis/ArchetypePie.tsx` - Recharts donut chart with legend and tooltips
- `bc-rao-frontend/components/analysis/ComparisonTable.tsx` - Sortable table with ISC scores, click to navigate to detail
- `bc-rao-frontend/app/dashboard/campaigns/[id]/profiles/page.tsx` - Profiles list with comparison table and empty state
- `bc-rao-frontend/app/dashboard/campaigns/[id]/profiles/[subreddit]/page.tsx` - Tabbed detail page with 4 sections

## Decisions Made
- Recharts donut chart for archetype distribution: innerRadius=60, outerRadius=100, color-coded by archetype (Journey=blue, ProblemSolution=green, Feedback=amber, Unclassified=gray)
- ISC gauge color coding: green (1-3), yellow (3-5), orange (5-7), red (7-10) matching tier sensitivity levels
- Comparison table sorts by ISC score descending by default - users likely want to see most sensitive communities first
- AnalysisProgress uses same EventSource + cleanup pattern as collection ProgressTracker for consistency
- Toast notification duration 10 seconds with action button to view profiles
- Insufficient data subreddits (<10 posts) show warning message instead of attempting to display invalid profile

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Added shadcn/ui Table component**
- **Found during:** Task 2 (ComparisonTable component creation)
- **Issue:** Table component not installed, import failing during build
- **Fix:** Ran `npx shadcn@latest add table -y`
- **Files modified:** bc-rao-frontend/components/ui/table.tsx
- **Verification:** Build succeeded after adding component
- **Committed in:** 28be1c4 (Task 2 commit)

**2. [Rule 1 - Bug] Fixed TypeScript error in ArchetypePie Tooltip formatter**
- **Found during:** Task 2 (Next.js build verification)
- **Issue:** Tooltip formatter type signature didn't allow undefined value parameter
- **Fix:** Changed formatter parameter type from `(value: number)` to `(value: number | undefined)` and added null coalescing `${value || 0}`
- **Files modified:** bc-rao-frontend/components/analysis/ArchetypePie.tsx
- **Verification:** Build passed without TypeScript errors
- **Committed in:** 28be1c4 (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (1 missing critical, 1 bug)
**Impact on plan:** Table component essential for ComparisonTable to function. TypeScript fix necessary for build to pass. No scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Community profiles frontend complete and ready for generation pipeline integration
- Users can view ISC scores, archetype distributions, rhythm patterns, and forbidden pattern categories
- Analysis progress tracking provides real-time feedback during analysis pipeline execution
- Profile detail pages provide comprehensive intelligence for content strategy decisions

---
*Phase: 03-pattern-engine*
*Completed: 2026-02-11*

## Self-Check: PASSED

All files verified:
- bc-rao-frontend/app/api/campaigns/[id]/community-profiles/route.ts ✓
- bc-rao-frontend/app/api/campaigns/[id]/community-profile/route.ts ✓

All commits verified:
- 1d0b3cc ✓
- 28be1c4 ✓
