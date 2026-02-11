---
phase: 04-draft-generation
plan: 05
subsystem: ui
tags: [nextjs, stage-indicator, campaign-journey, ux, toast-notifications]

# Dependency graph
requires:
  - phase: 04-03
    provides: Draft list page and DraftCard component
  - phase: 04-04
    provides: Draft editor UI with score visualization
  - phase: 03-03
    provides: Community profiles with ISC scores
provides:
  - 4-stage campaign journey indicator with linear progression enforcement
  - Auto-advance toast notifications when stages unlock
  - Stage 4 (Alchemical Transmutation) section on campaign page
  - Draft generation quick action card with lock/unlock states
  - Recent drafts preview in Stage 4 section
affects: [user-onboarding, campaign-workflow, draft-discovery]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Stage computation with linear progression enforcement
    - Auto-advance toast with Continue action button using Sonner
    - Responsive stage indicator (horizontal desktop, vertical mobile)
    - Stage state visualization (completed/active/locked with icons)
    - Conditional rendering based on stage completion

key-files:
  created:
    - bc-rao-frontend/lib/campaign-stages.ts
    - bc-rao-frontend/components/dashboard/StageIndicator.tsx
  modified:
    - bc-rao-frontend/app/dashboard/campaigns/[id]/page.tsx
    - bc-rao-frontend/components/drafts/DraftCard.tsx

key-decisions:
  - "4-stage journey: Project Briefing → Strategic Selection → Community Intelligence → Alchemical Transmutation"
  - "Linear progression enforced: each stage locked until previous stage completes"
  - "Stage computation based on campaign data (config, posts, profiles, drafts)"
  - "Auto-advance toast appears when stage unlocks with Continue action button"
  - "Stage 4 shows locked state with explanation until Stage 3 (profiles) complete"
  - "Recent 3 drafts preview in Stage 4 with View All link to full draft list"
  - "4th quick action card for Draft Generation with purple icon, locked until Stage 3"
  - "DraftCard navigation fixed to use campaign-specific URL pattern"

patterns-established:
  - "computeStages() utility for stage state calculation from campaign data"
  - "StageIndicator responsive layout: horizontal with chevrons (desktop), vertical stacked (mobile)"
  - "Stage click handling: navigate if unlocked, show toast error if locked"
  - "Auto-advance detection via useEffect watching stages array for locked→active transitions"
  - "Stage 4 conditional rendering: locked message vs generate button + drafts list"

# Metrics
duration: 4min
completed: 2026-02-11
---

# Phase 04 Plan 05: Dashboard Journey Stages Summary

**4-stage campaign journey indicator with auto-advance notifications and Stage 4 draft generation section**

## Performance

- **Duration:** 4 min
- **Started:** 2026-02-11T03:11:44Z
- **Completed:** 2026-02-11T03:15:59Z
- **Tasks:** 2
- **Files modified:** 4 (2 created, 2 modified)

## Accomplishments
- 4-stage campaign journey indicator renders on campaign detail page with computed stages
- Linear progression enforced: Stage 1 always unlocked, Stage 2-4 locked until previous completes
- Auto-advance toast notifications with Continue action button when stages unlock
- Responsive StageIndicator: horizontal with chevron arrows (desktop), vertical stacked (mobile)
- Stage states visualized: Completed (green + check), Active (blue + pulsing), Locked (gray + lock)
- Stage 4 (Alchemical Transmutation) section with locked/unlocked states on campaign page
- When Stage 3 incomplete: lock icon with explanation and link to Community Profiles
- When Stage 3 complete: generate button + recent 3 drafts preview + View All link
- 4th quick action card for Draft Generation added to campaign page (locked until Stage 3)
- DraftCard navigation fixed to use campaign-specific URL pattern

## Task Commits

Each task was committed atomically:

1. **Task 1: Stage computation utility and StageIndicator component** - `39bad9c` (feat)
2. **Task 2: Update campaign page with stages and Stage 4 content** - `2b27584` (feat)

## Files Created/Modified
- `bc-rao-frontend/lib/campaign-stages.ts` - Stage computation logic with linear progression enforcement
- `bc-rao-frontend/components/dashboard/StageIndicator.tsx` - Responsive stage indicator with auto-advance toast notifications
- `bc-rao-frontend/app/dashboard/campaigns/[id]/page.tsx` - Integrated StageIndicator, Stage 4 section, 4th quick action card
- `bc-rao-frontend/components/drafts/DraftCard.tsx` - Fixed navigation URL to campaign-specific draft edit page

## Decisions Made

**4-stage journey structure:**
- Stage 1 (Project Briefing): Campaign setup complete when product_context + keywords + target_subreddits exist
- Stage 2 (Strategic Selection): Collection complete when posts_collected > 0
- Stage 3 (Community Intelligence): Analysis complete when community profiles exist
- Stage 4 (Alchemical Transmutation): Generation complete when drafts_generated > 0
- Each stage has name, description, completed/active/locked state, and URL

**Linear progression enforcement:**
- Stage 1 never locked (campaign setup always accessible)
- Stage 2-4 locked until previous stage completes
- Only one stage active at a time (first non-completed stage)
- Clicking locked stage shows toast error with explanation
- Clicking unlocked stage navigates to appropriate page

**Auto-advance toast notifications:**
- useEffect watches stages array for changes
- Detects locked→active transitions (stage just unlocked)
- Shows success toast with stage name and Continue action button
- Action button navigates directly to newly unlocked stage
- 5-second duration for user visibility

**Stage 4 integration:**
- Conditional rendering based on Stage 3 completion (profiles.length > 0)
- Locked state: lock icon, explanation text, button to view Community Profiles
- Unlocked state: generate button + recent drafts section + View All link
- Recent drafts fetched (top 3, status=ready or pending) for preview
- Empty state message when no drafts exist yet

**Responsive stage indicator:**
- Desktop: horizontal layout with chevron arrows between stages
- Mobile: vertical stacked layout
- Each stage is a clickable card (unless locked)
- Completed stages: green background, green border, check icon
- Active stage: blue background, blue border, pulsing animation, stage number
- Locked stages: gray background, gray border, lock icon, 50% opacity

**4th quick action card:**
- Purple icon (Wand2) for Draft Generation
- When Stage 3 complete: clickable, navigates to generation page
- When Stage 3 incomplete: grayed out with lock icon and "Complete analysis to unlock" text
- Matches design pattern of existing 3 cards (Community Profiles, Post Analysis, Forbidden Patterns)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - all components integrated smoothly with existing campaign page and draft functionality.

## User Setup Required

None - uses existing Supabase session and API proxy routes from previous phases.

## Next Phase Readiness

**Phase 04 (Draft Generation) Complete:**
- All 5 plans executed successfully
- Draft generation flow complete from start to finish
- User journey clearly visualized with stage indicator
- ISC gating enforced, community DNA integrated into drafts
- Editor with score visualization and four actions operational
- Stage-based progression ensures users complete prerequisite steps

**Ready for Phase 05 (Monitoring & Feedback):**
- Campaign structure supports adding monitors
- Draft data available for performance tracking
- Stage indicator can be extended with Stage 5 if needed
- Auto-advance pattern established for future stages

**Ready for Phase 06 (Billing & Limits):**
- Draft count tracking ready for monthly limit enforcement
- Campaign stats structure supports billing metrics
- Stage completion data useful for onboarding analytics

**No blockers.** Draft generation phase complete with full user journey visualization.

## Self-Check: PASSED

All key files verified on disk.
All commits verified in git history.

---
*Phase: 04-draft-generation*
*Completed: 2026-02-11*
