---
status: complete
phase: 02-collection-pipeline
source: 02-01-SUMMARY.md, 02-02-SUMMARY.md, 02-03-SUMMARY.md, 02-04-PLAN.md
started: 2026-02-10T22:00:00Z
updated: 2026-02-10T22:30:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Collection Page — Idle State
expected: Navigate to a campaign's collection page (/dashboard/campaigns/[id]/collect) for a campaign with no collected posts. You see an idle view with a "Start Collection" button and remaining runs count displayed.
result: pass

### 2. Trigger Collection — Live Progress
expected: Click "Start Collection". A live progress bar appears showing subreddit-by-subreddit progress with funnel stats updating in real time (scraped -> filtered -> classified counts). A navigation guard should warn you if you try to leave the page during collection.
result: skipped
reason: Backend (FastAPI + Celery + Redis) not deployed — no server to process collection requests

### 3. Collection Complete — Results View
expected: After collection finishes, the page auto-transitions to show results: funnel stats at the top (scraped -> filtered -> classified pipeline breakdown), then a filter bar, then a card grid of collected posts below.
result: skipped
reason: Backend not deployed — no collected data to display results view

### 4. Post Card Display
expected: Each card in the grid shows: post title (truncated if long), text snippet (3 lines max), an archetype badge (Journey, ProblemSolution, or Feedback), the subreddit name (r/subreddit), and a success score displayed as a number out of 10 with a small progress bar.
result: skipped
reason: Backend not deployed — no post data to render cards

### 5. Archetype Filter
expected: Use the archetype dropdown to select a specific archetype (e.g., Journey). The grid updates to show only posts with that archetype. Selecting "All Archetypes" shows all posts again.
result: skipped
reason: Backend not deployed — no post data to filter

### 6. Subreddit Filter
expected: Use the subreddit dropdown to filter posts by a specific subreddit. Only posts from that subreddit appear in the grid.
result: skipped
reason: Backend not deployed — no post data to filter

### 7. Score Range Filter
expected: Adjust the score range slider (0-10). Only posts within the selected score range appear in the grid. The current range is displayed (e.g., "Score: 3 - 8").
result: skipped
reason: Backend not deployed — no post data to filter

### 8. Post Detail Modal
expected: Click on a post card. A modal opens showing: full post title, archetype badge, subreddit badge, score with progress bar, full post text (scrollable), and metadata (author, date, upvotes, comments).
result: skipped
reason: Backend not deployed — no post data for modal

### 9. Funnel Stats Display
expected: The funnel stats section shows a three-step breakdown: total scraped -> passed regex filter (with filter rate %) -> top posts classified. Archetype distribution is shown as badges/pills with counts.
result: skipped
reason: Backend not deployed — no collection stats data

### 10. Collect More Button
expected: In the results view, a "Collect More" button is visible with remaining runs count. Clicking it triggers a new collection. New posts are appended without removing existing ones (deduplication handled).
result: skipped
reason: Backend not deployed — requires active collection capability

### 11. Page Revisit With Existing Data
expected: Navigate away from the collection page, then navigate back. The page detects existing collected posts and shows the results view directly (skips the idle state).
result: skipped
reason: Backend not deployed — no existing data to detect on revisit

### 12. Pagination
expected: If there are more than 20 posts, pagination controls appear below the grid showing "Showing 1-20 of N" with Previous/Next buttons. Clicking Next loads the next page of posts.
result: skipped
reason: Backend not deployed — no post data for pagination

## Summary

total: 12
passed: 1
issues: 0
pending: 0
skipped: 11

## Gaps

- truth: "Full Phase 2 UAT requires backend deployment (FastAPI + Celery + Redis)"
  status: blocked
  reason: "Backend not deployed to any hosting platform. 11 of 12 tests could not be executed."
  severity: blocker
  test: 2-12
  root_cause: "Backend infrastructure not deployed — only frontend (Vercel) is live"
  artifacts: []
  missing:
    - "Deploy bc-rao-api to Railway/Render/Fly.io"
    - "Configure APIFY_API_TOKEN, OPENROUTER_API_KEY, REDIS_URL, SUPABASE_SERVICE_ROLE_KEY on backend"
    - "Set NEXT_PUBLIC_API_URL on Vercel frontend pointing to backend URL"
  debug_session: ""
