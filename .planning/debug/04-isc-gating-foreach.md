---
status: diagnosed
trigger: "ISC Gating forEach Error - e.forEach is not a function when selecting subreddit in draft generation form"
created: 2026-02-11T00:00:00Z
updated: 2026-02-11T00:00:00Z
symptoms_prefilled: true
goal: find_root_cause_only
---

## Current Focus

hypothesis: CONFIRMED - Backend returns {profiles: [...]} object but original frontend code called .forEach() directly on the response object
test: Traced full data flow from backend -> proxy -> frontend
expecting: Shape mismatch between API response and frontend consumption
next_action: Root cause confirmed. Fix already applied in commit 2806c17 but may need rebuild.

## Symptoms

expected: Selecting a subreddit in the draft generation form should load its community profile and ISC score for gating
actual: e.forEach is not a function error; community profile shows "No profile"
errors: e.forEach is not a function
reproduction: Select a subreddit in draft generation form
started: Phase 4 UAT Test 2

## Eliminated

- hypothesis: Subreddit name mismatch between campaigns.target_subreddits and community_profiles.subreddit
  evidence: Both use the same subreddit string - flows from campaign.target_subreddits -> raw_posts.subreddit -> community_profiles.subreddit. Verified in collection_service.py line 341 and analysis_service.py line 303.
  timestamp: 2026-02-11

- hypothesis: Backend endpoint returns wrong data structure
  evidence: Backend analysis.py line 272 returns {"profiles": profiles} where profiles is List[dict] from service. The shape is correct and consistent with CommunityProfileListResponse model (line 54-56 in models/analysis.py).
  timestamp: 2026-02-11

- hypothesis: Frontend proxy transforms the response
  evidence: Proxy at community-profiles/route.ts line 88 passes backend response through directly with NextResponse.json(data). No transformation occurs.
  timestamp: 2026-02-11

- hypothesis: RLS policies blocking community profile reads
  evidence: Backend uses service role key (supabase_client.py line 15 confirms "service role key"), bypassing RLS. Campaign ownership is validated at the API layer (analysis.py line 257).
  timestamp: 2026-02-11

## Evidence

- timestamp: 2026-02-11
  checked: Backend endpoint at bc-rao-api/app/api/v1/analysis.py line 236-272
  found: Returns {"profiles": profiles} where profiles is a List[dict]
  implication: Response is an object with "profiles" key, NOT a flat array

- timestamp: 2026-02-11
  checked: Frontend proxy at bc-rao-frontend/app/api/campaigns/[id]/community-profiles/route.ts line 88
  found: Passes backend response through directly (return NextResponse.json(data))
  implication: Frontend receives {"profiles": [...]} object

- timestamp: 2026-02-11
  checked: Git history - commit 2806c17 diff for page.tsx
  found: BEFORE fix (original code): `const profilesData: CommunityProfile[] = await profilesResponse.json()` then `profilesData.forEach(...)`. AFTER fix: Added Array.isArray check and responseData.profiles unwrapping
  implication: Original code called .forEach() on the {"profiles": [...]} object, causing TypeError

- timestamp: 2026-02-11
  checked: Current page.tsx at bc-rao-frontend/app/dashboard/campaigns/[id]/drafts/new/page.tsx lines 82-94
  found: Fix from 2806c17 IS present in source code - properly unwraps responseData.profiles
  implication: Source code is fixed but may not be rebuilt/deployed

- timestamp: 2026-02-11
  checked: UAT document at .planning/phases/04-draft-generation/04-UAT.md Test 2 (lines 20-24)
  found: Still listed as "issue" with original report text. UAT doc was written before fix commit 2806c17 and updated in eca8328 but original issue text was preserved without re-testing.
  implication: The fix exists but hasn't been verified by user yet

- timestamp: 2026-02-11
  checked: "No profile" display logic in GenerationForm.tsx line 96-99
  found: Shows "(No profile)" when iscData[subreddit] is falsy. If the forEach crash occurs in the try/catch at page.tsx line 97, iscData stays as empty {} and ALL subreddits show "No profile"
  implication: "No profile" is a cascading symptom of the forEach crash, not a separate bug

## Resolution

root_cause: |
  API response format mismatch. The backend endpoint GET /v1/analysis/campaigns/{id}/community-profiles
  returns {"profiles": [...]} (an object wrapping an array), but the original frontend code at
  page.tsx line 82 treated the response as a flat array:

    const profilesData: CommunityProfile[] = await profilesResponse.json();
    profilesData.forEach(...)  // TypeError: e.forEach is not a function

  Calling .forEach() on a plain object throws "e.forEach is not a function" (minified as "e").

  The "No profile" display is a cascading effect: the forEach crash is caught by the try/catch
  at line 97, preventing iscData from being populated. With iscData remaining as {}, every
  subreddit in the dropdown shows "(No profile)" regardless of whether profiles exist in the DB.

  FILES:
  - bc-rao-frontend/app/dashboard/campaigns/[id]/drafts/new/page.tsx (line 82, original bug)
  - bc-rao-api/app/api/v1/analysis.py (line 272, returns {profiles: [...]})
  - bc-rao-frontend/app/api/campaigns/[id]/community-profiles/route.ts (line 88, passthrough proxy)

fix: |
  Fix was already applied in commit 2806c17. The code now correctly unwraps the response:

    const responseData = await profilesResponse.json();
    const profilesData: CommunityProfile[] = Array.isArray(responseData)
      ? responseData
      : responseData.profiles || [];

  This handles both possible formats (flat array or {profiles: [...]}) defensively.

  STATUS: Fix exists in source code. Needs rebuild (npm run build / restart dev server) and
  user re-verification.

verification: Pending user re-test after rebuild
files_changed:
  - bc-rao-frontend/app/dashboard/campaigns/[id]/drafts/new/page.tsx
