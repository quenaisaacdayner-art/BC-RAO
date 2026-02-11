# Phase 3: Pattern Engine - Context

**Gathered:** 2026-02-10
**Status:** Ready for planning

<domain>
## Phase Boundary

System analyzes collected posts with SpaCy NLP, calculates ISC scores per subreddit, and builds community profiles with rhythm patterns and forbidden patterns. Users can view community intelligence and scoring breakdowns. Draft generation and monitoring are separate phases.

</domain>

<decisions>
## Implementation Decisions

### Community Profile Display
- ISC score shown as number + tier label with color coding (e.g., "7.8 — High Sensitivity") with color gauge
- Archetype distribution (Journey/ProblemSolution/Feedback) shown as pie/donut chart
- Profile page uses tabbed sections: Summary tab with key metrics, then tabs for Archetypes, Rhythm, Blacklist, etc.
- Comparison table across all target subreddits as the entry point, click into individual subreddit profiles for detail

### Post Scoring Breakdown
- Show 3-4 key contributing factors per post (rhythm match, vulnerability, formality, penalties) — not full sub-detail breakdown
- Penalties highlighted inline in post text (problematic phrases highlighted in red/orange, like a linter)
- Dedicated "Analysis" page for viewing posts with scores and expandable breakdowns — separate from Phase 2's post browsing
- Sorting/filtering by scoring factors: Claude's discretion on appropriate filtering based on data complexity

### Analysis Trigger & Feedback
- Analysis runs automatically after collection completes — seamless pipeline, no manual trigger needed
- SSE-style progress tracking during analysis: "Analyzing post 47/230…" with rhythm analysis and scoring steps visible
- If insufficient data for a subreddit: block profile creation, show "Need more data" and suggest re-collecting with wider criteria
- After analysis completes: toast notification "Analysis complete" with link to profiles — user decides when to navigate

### Forbidden Patterns Surface
- Show pattern categories only (Promotional, Self-referential, Link patterns, etc.) with counts per category — not raw pattern strings
- Users can add custom forbidden patterns (e.g., competitor names) but cannot remove system-detected ones
- Separate dedicated blacklist page showing all forbidden patterns across all subreddits, filterable by subreddit
- No provenance tracking in display — just categories and counts, keep it simple

### Claude's Discretion
- SpaCy pipeline configuration and NLP analysis details
- ISC scoring algorithm and weight tuning
- Exact threshold for "insufficient data" blocking profile creation
- Community profile tab structure and content organization
- Scoring filter/sort implementation approach
- Rhythm pattern visualization within profile tabs

</decisions>

<specifics>
## Specific Ideas

- Community profiles entry point is a comparison table (like a leaderboard/dashboard) — click into individual subreddits for detail tabs
- Analysis progress should feel like the collection SSE progress from Phase 2 — consistent UX pattern
- Penalty highlighting inline in post text should feel like a code linter (red/orange underlines or highlights on problematic phrases)
- Blacklist page is global (all subreddits) with subreddit filter — not buried inside individual profiles

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 03-pattern-engine*
*Context gathered: 2026-02-10*
