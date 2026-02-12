---
status: diagnosed
trigger: "Stage 3 Click Navigation Broken - clicking Stage 3 (Community Intelligence) doesn't redirect to /analysis page"
created: 2026-02-11T00:00:00Z
updated: 2026-02-11T00:01:00Z
---

## Current Focus

hypothesis: CONFIRMED - Stage 3 URL maps to /profiles, not /analysis; also visual state issue with completed-but-not-active stages
test: Read campaign-stages.ts line 81 and StageIndicator.tsx styling logic
expecting: Stage 3 URL is wrong, visual state CSS has specificity/override issues
next_action: Report root causes

## Symptoms

expected: Clicking Stage 3 (Community Intelligence) on campaign detail page should navigate to /analysis page
actual: Click on Stage 3 does not navigate to /analysis (navigates to /profiles instead, or appears non-functional)
errors: None reported (silent - user expects /analysis but gets /profiles)
reproduction: Go to campaign detail page, click on Stage 3 indicator
started: Since stage indicator was implemented

## Eliminated

- hypothesis: Stage 3 is being treated as locked when it should not be
  evidence: Gating logic at line 82 is `locked: !stage2Complete` which is correct. If stage2 is complete, stage3 is unlocked. Click handler only blocks on `stage.locked`.
  timestamp: 2026-02-11T00:00:30Z

- hypothesis: Click handler is not calling router.push
  evidence: handleStageClick (line 48-57) correctly calls router.push(stage.url) when not locked. The function is correctly wired to onClick.
  timestamp: 2026-02-11T00:00:35Z

## Evidence

- timestamp: 2026-02-11T00:00:10Z
  checked: campaign-stages.ts line 81 - Stage 3 URL configuration
  found: Stage 3 URL is `/dashboard/campaigns/${campaignId}/profiles` (NOT /analysis)
  implication: PRIMARY ROOT CAUSE - The stage indicator navigates to /profiles, not /analysis as the user expects

- timestamp: 2026-02-11T00:00:15Z
  checked: Existing routes in app/dashboard/campaigns/[id]/
  found: Both /analysis AND /profiles routes exist as separate pages
  implication: The /analysis route exists and is a valid page. Stage 3 is pointing to the wrong one.

- timestamp: 2026-02-11T00:00:20Z
  checked: campaign detail page.tsx line 244 (Quick Actions section)
  found: The "Post Analysis" quick action card links to /analysis. The "Community Profiles" card links to /profiles. These are separate features.
  implication: Stage 3 "Community Intelligence" conceptually maps to analysis, but the stage config sends users to profiles instead.

- timestamp: 2026-02-11T00:00:25Z
  checked: StageIndicator.tsx CSS styling logic for completed vs active states
  found: Line 72-74 shows: completed gets `bg-green-50 border-green-200`, active gets `bg-blue-50 border-blue-200 shadow-sm`. Both classes can be applied if both `completed` and `active` are true (though current logic makes them mutually exclusive in computeStages). The real issue: when a stage is completed AND not active, only green styles apply but there is no visual distinction for "completed and clickable" vs just "completed". Completed stages look the same regardless of whether later stages exist.
  implication: SECONDARY ISSUE - completed stages lack strong visual affordance showing they are clickable

- timestamp: 2026-02-11T00:00:40Z
  checked: getStageUrl helper function at line 118-128
  found: This helper ALSO maps stage 3 to /profiles (line 123). Consistent with the stage config but also wrong if user expects /analysis.
  implication: The wrong URL is defined in TWO places: computeStages() and getStageUrl()

- timestamp: 2026-02-11T00:00:45Z
  checked: Stage 3 description in computeStages (line 78-79)
  found: name is "Community Intelligence", description is "Analyze community profiles and patterns"
  implication: The name says "Intelligence" and description says "Analyze" - both suggest the analysis page, not just the profiles page

## Resolution

root_cause: |
  TWO ROOT CAUSES FOUND:

  ROOT CAUSE 1 (Primary - Navigation): Stage 3 "Community Intelligence" URL is configured to
  point to `/dashboard/campaigns/${campaignId}/profiles` instead of `/dashboard/campaigns/${campaignId}/analysis`.
  This is defined in TWO locations:
    - campaign-stages.ts line 81: `url: /dashboard/campaigns/${campaignId}/profiles`
    - campaign-stages.ts line 123: `3: /dashboard/campaigns/${campaignId}/profiles`
  The /analysis route exists and is a separate page. "Community Intelligence" conceptually
  maps to analysis (analyzing community patterns), not just viewing profiles.

  ROOT CAUSE 2 (Secondary - Visual State): Completed stages in StageIndicator.tsx have
  weak visual differentiation. A completed stage shows green background (line 72:
  `bg-green-50 border-green-200`) but has no additional affordance (like hover effect
  differentiation or "completed" badge) to distinguish it from the active stage's blue
  styling (line 73: `bg-blue-50 border-blue-200`). While both have `hover:shadow-md`
  when not locked (line 71), the completed green vs active blue may not be obvious enough
  at a glance.

fix: |
  Not yet applied (diagnosis only)

verification: |
  Not yet verified

files_changed: []

## Fix Direction

### Fix 1: Change Stage 3 URL (Primary)
File: `bc-rao-frontend/lib/campaign-stages.ts`
- Line 81: Change `url: /dashboard/campaigns/${campaignId}/profiles` to `url: /dashboard/campaigns/${campaignId}/analysis`
- Line 123: Change `3: /dashboard/campaigns/${campaignId}/profiles` to `3: /dashboard/campaigns/${campaignId}/analysis`

### Fix 2: Improve Visual State (Secondary)
File: `bc-rao-frontend/components/dashboard/StageIndicator.tsx`
- Add stronger visual distinction for completed stages (e.g., ring/border emphasis, different hover color)
- Consider: completed stages could show a "ring-2 ring-green-300" or similar to make clickability more obvious
- The active stage's `animate-pulse` is good, but completed stages blend into the background
