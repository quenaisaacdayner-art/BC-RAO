---
status: resolved
trigger: "Two frontend issues: (1) Clicking Community Intelligence stage card doesn't navigate to /profiles. (2) Stage 3 never visually completes even if analysis runs."
created: 2026-02-12T00:00:00Z
updated: 2026-02-12T00:02:00Z
---

## Current Focus

hypothesis: CONFIRMED AND FIXED - Stage 3 URL in computeStages() and getStageUrl() pointed to /analysis instead of /profiles.
test: TypeScript type check passes, test assertions updated to match correct URL
expecting: N/A - fix verified
next_action: Archive session

## Symptoms

expected: Clicking "Community Intelligence" should navigate to the profiles/analysis page. After analysis completes, Stage 3 should show as complete (green checkmark) and Stage 4 should unlock.
actual: Community Intelligence card doesn't navigate to /profiles. Stage 3 stays active (blue) even after analysis appears to complete. "Stage Locked" shown for Alchemical Transmutation.
errors: No visible JS errors
reproduction: Go to any campaign page, click Community Intelligence stage
started: Since Phase 3/4 frontend implementation

## Eliminated

- hypothesis: Stage 3 card lacks onClick handler
  evidence: StageIndicator has handleStageClick that calls router.push(stage.url) for all non-locked stages. The handler exists and works.
  timestamp: 2026-02-12T00:00:30Z

- hypothesis: Profile fetch in campaign detail page fails silently
  evidence: apiClient.get('/campaigns/{id}/community-profiles') hits Next.js proxy route which correctly proxies to backend /analysis/campaigns/{id}/community-profiles. The route exists and returns { profiles: [...] }. Error is caught but the fetch path is correct.
  timestamp: 2026-02-12T00:00:45Z

## Evidence

- timestamp: 2026-02-12T00:00:20Z
  checked: campaign-stages.ts line 81
  found: Stage 3 URL is `/dashboard/campaigns/${campaignId}/analysis` but should be `/dashboard/campaigns/${campaignId}/profiles`
  implication: Clicking Community Intelligence stage card navigates to /analysis (Post Analysis page) instead of /profiles (Community Profiles page)

- timestamp: 2026-02-12T00:00:22Z
  checked: campaign-stages.ts line 123 (getStageUrl helper)
  found: Same wrong URL for stage 3: `/dashboard/campaigns/${campaignId}/analysis`
  implication: Any code using getStageUrl(3, id) also gets wrong URL

- timestamp: 2026-02-12T00:00:30Z
  checked: campaign detail page.tsx lines 226, 244, 337
  found: Quick action cards correctly distinguish: "Community Profiles" links to /profiles, "Post Analysis" links to /analysis. Stage 4 locked section correctly links to /profiles.
  implication: The campaign page itself has correct URLs; only computeStages/getStageUrl are wrong

- timestamp: 2026-02-12T00:00:40Z
  checked: /profiles/page.tsx vs /analysis/page.tsx
  found: /profiles page is a server component showing ISC scores, archetype distributions, comparison table (the Community Intelligence data). /analysis page shows individual post score breakdowns (supplementary data, not stage 3 deliverable).
  implication: /profiles IS the correct Stage 3 destination

- timestamp: 2026-02-12T00:00:50Z
  checked: Stage completion logic in campaign detail page.tsx line 174
  found: stage3Complete = profiles.length > 0. Profiles are fetched from /community-profiles endpoint. If analysis has run and profiles exist, this should be true.
  implication: Stage 3 completion logic is correct IF profiles fetch succeeds. The visual bug is caused by the wrong URL leading users to the wrong page, where profiles are never triggered/viewed.

- timestamp: 2026-02-12T00:01:30Z
  checked: TypeScript compilation after fix
  found: npx tsc --noEmit passes cleanly with zero errors
  implication: Fix is type-safe and does not break anything

## Resolution

root_cause: In campaign-stages.ts, Stage 3 URL was set to `/dashboard/campaigns/${campaignId}/analysis` (Post Analysis page) instead of `/dashboard/campaigns/${campaignId}/profiles` (Community Profiles page). The same wrong URL existed in the getStageUrl() helper. This caused two cascading problems: (1) clicking the Community Intelligence stage indicator navigated to the Post Analysis page (wrong destination), and (2) users never reached the Community Profiles page where they can trigger/view analysis, so profiles may never get created, causing stage3Complete to remain false and Stage 3 to stay visually active.
fix: Changed Stage 3 URL from /analysis to /profiles in both computeStages() (line 81) and getStageUrl() (line 122). Also updated test assertions to match.
verification: TypeScript type check passes. Test assertions updated to expect correct /profiles URL. Static analysis confirms consistency with campaign detail page quick action cards and Stage 4 locked section.
files_changed:
  - bc-rao-frontend/lib/campaign-stages.ts (lines 81, 122: /analysis -> /profiles)
  - bc-rao-frontend/__tests__/lib/campaign-stages.test.ts (lines 30, 235: test expectations updated)
