---
status: complete
phase: 05-monitoring-feedback-loop
source: 05-01-SUMMARY.md, 05-02-SUMMARY.md, 05-04-SUMMARY.md
started: 2026-02-11T12:00:00Z
updated: 2026-02-12T12:20:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Campaign Journey Shows Stage 5
expected: Navigate to a campaign with drafts generated. Campaign page shows 5 stages in the stage indicator. Stage 5 "Deployment & Monitoring" appears as active/unlocked. Stages 1-4 show as complete.
result: pass

### 2. Stage 5 Content on Campaign Page
expected: On the campaign page, Stage 5 section shows monitoring CTA ("Go to Monitoring" or similar button) and displays monitored post count (0 if none registered yet).
result: pass

### 3. Monitoring Dashboard Page Loads
expected: Clicking the monitoring CTA or navigating to campaign/[id]/monitoring shows the monitoring dashboard with: page title "Post Monitoring", campaign name, URL registration input field, and an empty state message when no posts are registered.
result: pass

### 4. "I Posted This" Button on Draft Editor
expected: Open a draft in the editor that has "approved" or "posted" status. An "I posted this" button appears in the draft actions area. The button should NOT appear for drafts with "generated" or "discarded" status.
result: pass

### 5. Post Registration via Draft Editor
expected: Click "I posted this" on an approved draft. An inline URL input field expands below the button (light background, not a modal). Entering an invalid URL shows a validation error toast. Cancel button collapses the input.
result: pass

### 6. Post Registration via Monitoring Page
expected: On the monitoring dashboard, paste a valid Reddit post URL (format: reddit.com/r/subreddit/comments/id/...) into the registration input and click "Register Post". A success toast appears confirming monitoring has started. The post appears in the list below.
result: pass

### 7. Monitoring Stats Display
expected: After registering at least one post, the monitoring dashboard shows stats cards with counts for: Active, Removed, Shadowbanned, Total posts, and Success Rate percentage.
result: issue
reported: "depois de adicionar uma URL e ir ate /monitoring atravez de qualquer botao aparece o erro RangeError: Invalid time value - client-side crash on monitoring page"
severity: blocker
fix: Frontend-backend field name mismatch (posted_at vs submitted_at, shadow_id vs id, isc_at_posting vs isc_at_post, active vs active_count etc). Fixed by aligning frontend interfaces to backend ShadowEntry and MonitoringDashboardStats models. Commit: be134ac. Retested: pass.

### 8. Status Filter on Monitoring Page
expected: Filter buttons/tabs appear on the monitoring dashboard showing counts by status (All, Active, Removed, Shadowbanned). Clicking a filter updates the post list to show only posts with that status.
result: pass

### 9. Post Card Display
expected: Each monitored post appears as a card showing: post title, subreddit, status (Ativo/Removido/Shadowbanned), posted date, and ISC score at time of posting.
result: pass

### 10. Stage 5 Locked Before Stage 4
expected: Navigate to a campaign that has NOT completed Stage 4 (no drafts generated). Stage 5 should appear locked/disabled and its content should not be accessible.
result: pass

## Summary

total: 10
passed: 9
issues: 1
pending: 0
skipped: 0

## Gaps

- truth: "Monitoring dashboard shows stats cards after registering a post"
  status: fixed
  reason: "User reported: depois de adicionar uma URL e ir ate /monitoring atravez de qualquer botao aparece o erro RangeError: Invalid time value"
  severity: blocker
  test: 7
  root_cause: "Frontend-backend field name mismatch: PostCard.tsx used posted_at (undefined), MonitoringStats used active/removed/shadowbanned/total instead of active_count/removed_count/shadowbanned_count/total_count"
  artifacts:
    - path: "bc-rao-frontend/components/monitoring/PostCard.tsx"
      issue: "Interface fields mismatched backend ShadowEntry model"
    - path: "bc-rao-frontend/components/monitoring/MonitoringStats.tsx"
      issue: "Interface fields mismatched backend MonitoringDashboardStats model"
    - path: "bc-rao-frontend/app/dashboard/campaigns/[id]/monitoring/page.tsx"
      issue: "Interface fields mismatched backend models"
  fix_commit: be134ac
  fix_verified: true
