---
status: testing
phase: 03-pattern-engine
source: [03-01-SUMMARY.md, 03-02-SUMMARY.md, 03-03-SUMMARY.md, 03-04-SUMMARY.md]
started: 2026-02-11T12:00:00Z
updated: 2026-02-11T16:00:00Z
---

## Current Test
<!-- OVERWRITE each test - shows where we are -->

number: 6
name: Expandable Scoring Breakdown
expected: |
  Click on a post card on the analysis page. It expands to show a detailed breakdown of 4 scoring factors (vulnerability, rhythm, formality, penalties) with numeric values. Collapsing and re-expanding does not re-fetch the data (cached).
awaiting: user retest after fix a5af939

## Tests

### 1. Community Profiles Comparison Table
expected: Navigate to a campaign's profiles page. You should see a sortable table listing all analyzed subreddits with ISC scores, dominant tone, formality level, and archetype distribution. Clicking a column header sorts the table. Clicking a row navigates to that subreddit's detail page.
result: pass

### 2. ISC Gauge Visualization
expected: On a subreddit's profile detail page, the Summary tab shows an ISC gauge with a numeric score (1.0-10.0), a color-coded progress bar (green/yellow/orange/red), a tier label (Low/Moderate/High/Very High Sensitivity), and a description of what the score means.
result: pass

### 3. Archetype Pie Chart
expected: On a subreddit's profile detail page, the Archetypes tab shows a donut chart with color-coded segments for Journey (blue), ProblemSolution (green), Feedback (amber), and Unclassified (gray). Hovering shows tooltips with counts.
result: pass

### 4. Analysis Progress with SSE
expected: When analysis runs (auto-triggered after collection, or manually triggered), you see a live progress indicator updating in real-time showing how many posts have been analyzed. On completion, a toast notification appears with a link to view profiles.
result: issue-fixed
reported: "a analise (manual ou automaticamente) nao é executada depois do estagio da coleta e depois de fazer uma coleta o botao de fazer analise manual esta bloqueado entao nenhum dos 2 esta funcionando"
severity: blocker
fix: "Added analysis_task_id passthrough in ProgressTracker, analyzing phase in collect page, ManualAnalysisTrigger component, and analyze proxy route. Also fixed 404 API paths on campaign detail page (258b3dc, f18b7e4, b1e36f4)."

### 5. Analysis Page with Post Scoring
expected: Navigate to a campaign's analysis page. You should see a list of analyzed posts that can be sorted by scoring factors (rhythm, vulnerability, formality, penalties). Each post shows a score badge and preview text.
result: pass

### 6. Expandable Scoring Breakdown
expected: Click on a post card on the analysis page. It expands to show a detailed breakdown of 4 scoring factors (vulnerability, rhythm, formality, penalties) with numeric values. Collapsing and re-expanding does not re-fetch the data (cached).
result: issue
reported: "aparece o erro da imagem quando tentou clicar em qualquer cartao — TypeError: Cannot read properties of undefined (reading 'length')"
severity: blocker
fix: "Changed interface field from penalties to penalty_phrases to match backend, added null guards on all .toFixed() calls (a5af939)"

### 7. Inline Penalty Highlighting
expected: In an expanded post scoring breakdown, the post text shows inline highlights on penalized words/phrases (marketing jargon like "synergy", URLs). Highlights are color-coded by severity (red/orange/yellow). Hovering a highlight shows the penalty category in a tooltip.
result: [pending]

### 8. Blacklist Management Page
expected: Navigate to a campaign's blacklist page. You see category summary cards at the top showing pattern counts per category (Promotional, Self-referential, Link patterns, Low-effort, Spam, Off-topic). Below, a detailed table groups patterns by category with lock icons on system-detected patterns.
result: [pending]

### 9. Add Custom Forbidden Pattern
expected: On the blacklist page, there is a form to add a custom forbidden pattern. Enter a pattern string, select a category, and submit. The new pattern appears in the table without a lock icon (user-added, not system). System patterns with lock icons cannot be deleted.
result: [pending]

### 10. Campaign Navigation Cards
expected: On the campaign detail page, you see navigation cards linking to Profiles, Analysis, and Blacklist pages. Each card has an icon and description. Clicking a card navigates to the respective page.
result: [pending]

### 11. Insufficient Data Handling
expected: If a subreddit has fewer than 10 collected posts, the profiles page shows a "Need more data" message for that subreddit instead of attempting to display an invalid profile or ISC score.
result: [pending]

## Summary

total: 11
passed: 4
issues: 1
pending: 6
skipped: 0

## Gaps

- truth: "Analysis auto-triggers after collection and manual analysis button works"
  status: fixed
  reason: "User reported: analysis not auto-triggered after collection, manual analysis button blocked after collection completes"
  severity: blocker
  test: 4
  root_cause: "ProgressTracker didn't pass analysis_task_id; collect page had no analyzing phase; campaign page had wrong API paths causing 404s"
  artifacts: ["258b3dc", "f18b7e4", "b1e36f4"]

- truth: "Expanding post card shows scoring breakdown without crash"
  status: fixed
  reason: "TypeError: Cannot read properties of undefined (reading 'length') — backend returns penalty_phrases but frontend expected penalties"
  severity: blocker
  test: 6
  root_cause: "Field name mismatch (penalties vs penalty_phrases) and missing null guards on .toFixed() calls"
  artifacts: ["a5af939"]
