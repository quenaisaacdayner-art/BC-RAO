---
status: testing
phase: 01-foundation-core-setup
source: 01-01-SUMMARY.md, 01-02-SUMMARY.md, 01-03-SUMMARY.md, 01-04-SUMMARY.md, 01-05-SUMMARY.md, 01-06-PLAN.md
started: 2026-02-09T21:00:00Z
updated: 2026-02-09T21:00:00Z
---

## Current Test
<!-- OVERWRITE each test - shows where we are -->

number: 1
name: Home Page Redirect
expected: |
  Visit http://localhost:3000 while not logged in. You should be redirected to /login page showing a centered card with "Welcome back" heading and a login form.
awaiting: user response

## Tests

### 1. Home Page Redirect
expected: Visit http://localhost:3000 while not logged in. You should be redirected to /login page showing a centered card with "Welcome back" heading and a login form.
result: [pending]

### 2. Signup Flow
expected: Click "Sign up" link on login page. Fill in full name, email, and password (min 6 chars). Submit. You should be redirected to /dashboard.
result: [pending]

### 3. Dashboard Sidebar Navigation
expected: After login, dashboard shows a collapsible left sidebar with "BC-RAO" branding at top, navigation items for Overview and Campaigns, a dark/light mode toggle at bottom, and a user menu.
result: [pending]

### 4. Sidebar Collapse
expected: Click the sidebar toggle. Sidebar collapses to icon-only mode (just icons, no labels). Click again to expand back to full sidebar with icons + labels.
result: [pending]

### 5. Dark/Light Mode Toggle
expected: Click the theme toggle (Sun/Moon icon) in the sidebar footer. Page switches between dark and light mode. Colors update across the entire dashboard.
result: [pending]

### 6. Overview Empty State
expected: With no campaigns created, the Overview page shows a centered welcome card with "Welcome to BC-RAO" heading, a message about creating a campaign, and a "Create Campaign" button linking to the campaign creation form.
result: [pending]

### 7. Campaigns Empty State
expected: Navigate to Campaigns page from sidebar. With no campaigns, shows an empty state card with "No campaigns yet" heading, explanation text, and a "Create your first campaign" button.
result: [pending]

### 8. Campaign Creation Form
expected: Click "Create your first campaign" or navigate to /dashboard/campaigns/new. A single-page form appears with all fields visible: Campaign Name, Product Context (textarea), Product URL (optional), Keywords (textarea, comma-separated), and Target Subreddits (with autocomplete input).
result: [pending]

### 9. Subreddit Autocomplete
expected: In the subreddit field, type "saas" and wait ~300ms. A dropdown appears with matching Reddit subreddits showing name and member count. Click one to select it. Selected subreddit appears as a removable chip below the input.
result: [pending]

### 10. Keyword Validation
expected: Try submitting the campaign form with fewer than 5 comma-separated keywords. A validation error appears saying "Between 5 and 15 keywords required". Form does not submit.
result: [pending]

### 11. Campaign Creation Success
expected: Fill all fields correctly (name, product context with 10+ chars, at least 1 subreddit, 5-15 keywords). Submit. You should be redirected to the campaigns list with a success toast notification.
result: [pending]

### 12. Campaign List with Stats
expected: After creating a campaign, the Campaigns page shows a card grid. Each card displays: campaign name, status badge, truncated product context, keyword tags, subreddit names, and stats row showing "Posts: 0 | Drafts: 0 | Monitors: 0".
result: [pending]

### 13. Campaign Detail Page
expected: Click on a campaign card. Detail page shows all campaign information: name, status, full product context, product URL, all keywords as badges, subreddits, stats (zeros), and created/updated dates. Has "Edit Campaign" and "Delete Campaign" buttons.
result: [pending]

### 14. Edit Campaign
expected: Click "Edit Campaign" on detail page. Form opens pre-filled with current values. Change a field (e.g. add a keyword). Save. Changes persist when you view the campaign again.
result: [pending]

### 15. Delete Campaign
expected: Click "Delete Campaign". A confirmation dialog appears warning the action cannot be undone. Click "Delete Campaign" to confirm. Campaign is removed and you're redirected to the campaigns list.
result: [pending]

### 16. Logout
expected: Click the user menu in the sidebar footer. Click "Log out" (or similar). You are signed out and redirected to /login page.
result: [pending]

### 17. Login with Existing Account
expected: After logging out, log back in with the same email and password used during signup. You should be redirected to /dashboard with your previous data intact (campaigns still there).
result: [pending]

## Summary

total: 17
passed: 0
issues: 0
pending: 17
skipped: 0

## Gaps

[none yet]
