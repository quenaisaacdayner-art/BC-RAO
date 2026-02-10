# Phase 2: Collection Pipeline - Context

**Gathered:** 2026-02-10
**Status:** Ready for planning

<domain>
## Phase Boundary

System scrapes Reddit via Apify, filters posts with regex, classifies archetypes with LLM, and stores behavioral data in raw_posts table. Users can trigger collection, see live progress, and browse classified results. Creating drafts and pattern analysis are separate phases.

</domain>

<decisions>
## Implementation Decisions

### Collection trigger & progress
- Collection is part of a guided flow after campaign creation — "Now let's collect data for your subreddits" step
- Live progress bar with real-time stats: "Scraped 847 posts → 142 passed regex → 14 classified" with animated progress
- User is encouraged to stay on the page — "Collection in progress, are you sure?" prompt if navigating away
- Collection runs count: display remaining collections based on plan (5 free / 20 pro per week) — billing enforcement itself deferred to Phase 6, but UI should show the count

### Filtering & classification visibility
- Detailed funnel breakdown visible: "1,200 scraped → 180 passed regex (85% filtered) → 18 top posts classified" with expandable filter reasons
- Archetypes presented as grouped sections: "Journey Posts (7)" / "Problem-Solution Posts (5)" / "Feedback Posts (6)"
- No LLM classification reasoning exposed to user — just the archetype label
- Success score display: Claude's discretion on whether numeric score + bar or tier labels

### Collected data browsing
- Card grid layout (Reddit-style) — title, snippet, archetype badge, score, subreddit. Click to expand.
- Three filters available: archetype dropdown, subreddit dropdown, and score range slider
- Post detail opens in a modal: full Reddit post text, metadata (author, date, upvotes, comments), archetype, success score
- Re-collection via "Collect More" button — appends new posts with deduplication, does not replace
- Show remaining collection runs on the button (e.g., "Collect More (3 left)")

### Pipeline behavior & errors
- Partial failure: continue with successful subreddits, show warning for failed ones ("Failed to collect from r/xyz — try again later")
- No automatic retry — user can manually "Collect More" to try again
- Zero-match subreddits: aggregate warning only ("Some subreddits had no matching posts") — not per-subreddit granular feedback
- No cost estimate before collection — just run it, costs are low

### Claude's Discretion
- Completion UX (auto-transition to results vs toast notification)
- Success score display format (numeric + bar vs tier labels)
- Exact progress bar implementation and update frequency
- Card grid column count and responsive breakpoints
- Filter UI component choices (dropdowns, sliders, chips)

</decisions>

<specifics>
## Specific Ideas

- Guided flow after campaign creation — not a standalone action, feels like the natural next step
- Funnel visualization should make the user feel like the system is doing smart work (1200 → 180 → 18 progression)
- "Collect More" button should clearly show how many collections remain on their plan

</specifics>

<deferred>
## Deferred Ideas

- Billing enforcement for collection limits (5 free / 20 pro per week) — Phase 6 handles plan limit enforcement, but Phase 2 UI should be designed to support displaying remaining count
- Scheduled/automatic collection — would be a new capability, not in scope

</deferred>

---

*Phase: 02-collection-pipeline*
*Context gathered: 2026-02-10*
