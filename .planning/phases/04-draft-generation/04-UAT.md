---
status: complete
phase: 04-draft-generation
source: [04-01-SUMMARY.md, 04-02-SUMMARY.md, 04-03-SUMMARY.md, 04-04-SUMMARY.md, 04-05-SUMMARY.md]
started: 2026-02-11T12:00:00Z
updated: 2026-02-11T12:00:00Z
---

## Current Test
<!-- OVERWRITE each test - shows where we are -->

[testing complete]

## Tests

### 1. Generation Form Layout
expected: Navigate to a campaign's draft generation page. You should see a single-form with three inputs: subreddit dropdown (populated with campaign's target subreddits), archetype selector (Journey/ProblemSolution/Feedback), and optional context textarea. Generate button at the bottom.
result: pass

### 2. ISC Gating Warning
expected: Select a subreddit that has a community profile with ISC score > 7.5 (high sensitivity). An orange warning banner should appear explaining the ISC score/tier. The archetype selector should auto-switch to "Feedback" and disable other options.
result: issue
reported: "e.forEach is not a function error when selecting subreddit, profile shows as 'No profile' even though subreddit was analyzed"
severity: major

### 3. Unprofiled Subreddit Warning
expected: Select a subreddit that has NOT been analyzed (no community profile). A yellow warning banner should appear saying accuracy may be reduced. Generation should still be allowed (button not disabled).
result: pass

### 4. Draft Generation with SSE Progress
expected: Fill in the generation form and click Generate. You should see real-time progress updates (Loading profile, ISC gating, Building prompt, Generating, Validating, Scoring, Saving). After completion, you should be automatically redirected to the draft editor page.
result: issue
reported: "depois de clicar em generate começa mas depois aparece conexão perdida - Connection lost. Please try again."
severity: major

### 5. Draft Editor Layout
expected: On the draft editor page, you should see a two-column layout: a textarea with monospace font on the left for editing the draft text, and a sidebar on the right showing vulnerability score and rhythm match score as radial gauges (0-10 scale with color tiers), plus metadata (subreddit, archetype, timestamp).
result: skipped
reason: Blocked by generation SSE issue (Test 4)

### 6. Draft Actions - Copy to Clipboard
expected: Click the "Copy" button in the draft editor. The icon should change from a Copy icon to a Check icon for about 2 seconds. The draft text should be copied to your clipboard (paste somewhere to verify).
result: skipped
reason: Blocked by generation SSE issue (Test 4)

### 7. Draft Actions - Regenerate with Feedback
expected: Click "Regenerate" in the draft editor. A feedback textarea should appear (collapsible). You can optionally type guidance. Clicking confirm should show SSE progress and redirect to a NEW draft editor page when complete.
result: skipped
reason: Blocked by generation SSE issue (Test 4)

### 8. Draft Actions - Approve
expected: Click "Approve" on a draft. The draft status should change to "approved" and you should be redirected back to the campaign page.
result: skipped
reason: Blocked by generation SSE issue (Test 4)

### 9. Draft Actions - Discard
expected: Click "Discard" on a draft. The draft should be deleted and you should be redirected back to the campaign page.
result: skipped
reason: Blocked by generation SSE issue (Test 4)

### 10. Draft List with Filtering
expected: Navigate to the draft list page (/dashboard/campaigns/[id]/drafts). You should see all campaign drafts in a responsive grid. Filter controls should be visible for status (all/pending/ready/discarded) and subreddit. If no drafts exist, an empty state with "Generate First Draft" button should show.
result: pass

### 11. 4-Stage Campaign Journey Indicator
expected: On the campaign detail page, you should see a stage indicator showing 4 stages: Project Briefing, Strategic Selection, Community Intelligence, Alchemical Transmutation. Completed stages show green with a check mark. The current active stage shows blue with a pulsing animation. Locked stages show gray with a lock icon.
result: issue
reported: "Stage 2 completed but still shows green without clear completed state. Stage 3 doesn't let me click to redirect to /analysis"
severity: major

### 12. Stage 4 Locked/Unlocked States
expected: If community profiles exist (Stage 3 complete), Stage 4 should be unlocked showing a Generate button and recent drafts preview. If Stage 3 is NOT complete, Stage 4 should show a lock icon with explanation text and a link to Community Profiles.
result: pass

### 13. Stage Click Navigation
expected: Click on a completed or active stage in the indicator. You should be navigated to the appropriate page for that stage. Click on a locked stage - a toast error should appear explaining that the previous stage must be completed first.
result: pass

### 14. Monthly Draft Limit Display
expected: When generating drafts, the system should enforce monthly limits (trial=10 drafts/month). If you exceed the limit, you should see a 403-style error message indicating the plan limit has been reached.
result: skipped
reason: Blocked by generation SSE issue (Test 4) - cannot generate drafts to hit limit

## Summary

total: 14
passed: 5
issues: 3
pending: 0
skipped: 6

## Gaps

- truth: "ISC gating warning appears when selecting high-sensitivity subreddit"
  status: failed
  reason: "User reported: e.forEach is not a function error when selecting subreddit, profile shows as 'No profile' even though subreddit was analyzed"
  severity: major
  test: 2
  root_cause: ""
  artifacts: []
  missing: []
  debug_session: ""

- truth: "Stage indicator shows correct completed/active/locked states and click navigation works"
  status: failed
  reason: "User reported: Stage 2 completed but still shows green without clear completed state. Stage 3 doesn't let me click to redirect to /analysis"
  severity: major
  test: 11
  root_cause: ""
  artifacts: []
  missing: []
  debug_session: ""

- truth: "Draft generation shows SSE progress and redirects to editor on completion"
  status: failed
  reason: "User reported: depois de clicar em generate começa mas depois aparece conexão perdida - Connection lost. Please try again."
  severity: major
  test: 4
  root_cause: ""
  artifacts: []
  missing: []
  debug_session: ""
