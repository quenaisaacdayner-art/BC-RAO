---
status: testing
phase: 05-monitoring-feedback-loop
source: 05-01-SUMMARY.md, 05-02-SUMMARY.md, 05-04-SUMMARY.md
started: 2026-02-11T12:00:00Z
updated: 2026-02-11T12:00:00Z
---

## Current Test
<!-- OVERWRITE each test - shows where we are -->

number: 1
name: Campaign Journey Shows Stage 5
expected: |
  Navigate to a campaign that has drafts generated (Stage 4 complete). The campaign page should display 5 stages in the stage indicator. Stage 5 "Deployment & Monitoring" should appear as active (unlocked) or locked depending on whether monitored_posts > 0. Stages 1-4 should show as complete.
awaiting: user response

## Tests

### 1. Campaign Journey Shows Stage 5
expected: Navigate to a campaign with drafts generated. Campaign page shows 5 stages in the stage indicator. Stage 5 "Deployment & Monitoring" appears as active/unlocked. Stages 1-4 show as complete.
result: [pending]

### 2. Stage 5 Content on Campaign Page
expected: On the campaign page, Stage 5 section shows monitoring CTA ("Go to Monitoring" or similar button) and displays monitored post count (0 if none registered yet).
result: [pending]

### 3. Monitoring Dashboard Page Loads
expected: Clicking the monitoring CTA or navigating to campaign/[id]/monitoring shows the monitoring dashboard with: page title "Post Monitoring", campaign name, URL registration input field, and an empty state message when no posts are registered.
result: [pending]

### 4. "I Posted This" Button on Draft Editor
expected: Open a draft in the editor that has "approved" or "posted" status. An "I posted this" button appears in the draft actions area. The button should NOT appear for drafts with "generated" or "discarded" status.
result: [pending]

### 5. Post Registration via Draft Editor
expected: Click "I posted this" on an approved draft. An inline URL input field expands below the button (light background, not a modal). Entering an invalid URL shows a validation error toast. Cancel button collapses the input.
result: [pending]

### 6. Post Registration via Monitoring Page
expected: On the monitoring dashboard, paste a valid Reddit post URL (format: reddit.com/r/subreddit/comments/id/...) into the registration input and click "Register Post". A success toast appears confirming monitoring has started. The post appears in the list below.
result: [pending]

### 7. Monitoring Stats Display
expected: After registering at least one post, the monitoring dashboard shows stats cards with counts for: Active, Removed, Shadowbanned, Total posts, and Success Rate percentage.
result: [pending]

### 8. Status Filter on Monitoring Page
expected: Filter buttons/tabs appear on the monitoring dashboard showing counts by status (All, Active, Removed, Shadowbanned). Clicking a filter updates the post list to show only posts with that status.
result: [pending]

### 9. Post Card Display
expected: Each monitored post appears as a card showing: post title, subreddit, status (Ativo/Removido/Shadowbanned), posted date, and ISC score at time of posting.
result: [pending]

### 10. Stage 5 Locked Before Stage 4
expected: Navigate to a campaign that has NOT completed Stage 4 (no drafts generated). Stage 5 should appear locked/disabled and its content should not be accessible.
result: [pending]

## Summary

total: 10
passed: 0
issues: 0
pending: 10
skipped: 0

## Gaps

[none yet]
