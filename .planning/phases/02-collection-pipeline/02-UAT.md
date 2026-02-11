---
status: testing
phase: 02-collection-pipeline
source: 02-01-SUMMARY.md, 02-02-SUMMARY.md, 02-03-SUMMARY.md, 02-04-PLAN.md
started: 2026-02-11T14:00:00Z
updated: 2026-02-11T14:10:00Z
---

## Current Test

number: 4
name: Collection Complete — Auto-Transition
expected: |
  When collection finishes, the page auto-transitions from the progress view to a results view showing funnel stats and collected posts.
awaiting: user response

## Tests

### 1. Collection Page — Idle State
expected: Navigate to a campaign's collection page. You see a "Start Collection" button and remaining runs count.
result: pass

### 2. Trigger Collection — Request Sent
expected: Click "Start Collection". The page transitions to a collecting state with a progress tracker appearing. A navigation guard should warn you if you try to leave the page during collection.
result: pass

### 3. Live Progress — SSE Streaming
expected: During collection, you see live progress: current subreddit being processed, step count (e.g., "Processing 2/5 subreddits"), and funnel stats updating in real time (scraped count, filtered count, classified count).
result: issue
reported: "ao clicar o botao Start Collection comeca a coleta mas depois envia essa mensagem de conexion perdida - Error: Connection lost. Please refresh the page."
severity: blocker

### 4. Collection Complete — Auto-Transition
expected: When collection finishes, the page auto-transitions from the progress view to a results view showing funnel stats and collected posts.
result: [pending]

### 5. Funnel Stats Display
expected: The results view shows a funnel breakdown: total scraped -> passed regex filter (with percentage) -> classified posts. Archetype distribution is visible (Journey, ProblemSolution, Feedback counts).
result: [pending]

### 6. Post Card Grid
expected: Collected posts appear in a card grid. Each card shows: post title (truncated if long), text snippet, archetype badge (Journey/ProblemSolution/Feedback), subreddit name (r/subreddit), and success score.
result: [pending]

### 7. Archetype Filter
expected: Use the archetype dropdown to filter by a specific archetype (e.g., Journey). The grid updates to show only matching posts. Selecting "All" shows everything again.
result: [pending]

### 8. Subreddit Filter
expected: Use the subreddit dropdown to filter posts by a specific subreddit. Only posts from that subreddit appear.
result: [pending]

### 9. Score Range Filter
expected: Adjust the score range slider. Only posts within the selected range appear in the grid.
result: [pending]

### 10. Post Detail Modal
expected: Click on a post card. A modal opens showing: full post title, full post text (scrollable), archetype badge, subreddit, success score, and metadata (author, date, upvotes, comments).
result: [pending]

### 11. Collect More
expected: In the results view, a "Collect More" button is visible with remaining runs count. Clicking it triggers a new collection that appends new posts.
result: [pending]

### 12. Page Revisit
expected: Navigate away from the collection page, then navigate back. The page detects existing collected posts and shows the results view directly (skips idle state).
result: [pending]

## Summary

total: 12
passed: 2
issues: 1
pending: 9
skipped: 0

## Gaps

- truth: "Live SSE progress streaming shows real-time collection progress without connection drops"
  status: failed
  reason: "User reported: ao clicar o botao Start Collection comeca a coleta mas depois envia essa mensagem de conexion perdida - Error: Connection lost. Please refresh the page."
  severity: blocker
  test: 3
  root_cause: ""
  artifacts: []
  missing: []
  debug_session: ""
