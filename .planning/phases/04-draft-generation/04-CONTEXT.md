# Phase 4: Draft Generation - Context

**Gathered:** 2026-02-10
**Status:** Ready for planning

<domain>
## Phase Boundary

Users generate conditioned drafts that match community behavioral DNA, respect blacklist constraints, and adapt to ISC sensitivity levels. Covers the generation pipeline (prompt construction, blacklist enforcement, ISC gating), draft editor with scoring, and dashboard journey stages (Project Briefing → Strategic Selection → Community Intelligence → Alchemical Transmutation). Monitoring and feedback loop are separate phases.

</domain>

<decisions>
## Implementation Decisions

### Generation flow
- Single form (not wizard): one page with subreddit dropdown, archetype selector, optional context textarea, and generate button
- Three inputs only: subreddit, archetype, optional context — no tone selector or length preference
- All campaign subreddits shown in dropdown, not just profiled ones — warn if no community profile exists and generate with generic defaults
- ISC gating UX: inline warning banner + auto-switch to Feedback archetype when ISC > 7.5 — other archetypes disabled for that subreddit with explanation

### Draft editor experience
- Full-page editor layout: draft text on left, scores/metadata on right sidebar
- Sidebar gauges for vulnerability and rhythm match scores — radial gauges consistent with community profile ISC gauge pattern
- No live re-scoring on manual edits — scores reflect the generated draft only, editing is free-form
- Four actions: Approve (saves as ready), Discard (deletes), Regenerate (new draft with optional feedback), Copy to clipboard (for pasting into Reddit)

### Dashboard journey stages
- Per-campaign stage indicator (not global dashboard) — each campaign shows its own 4-stage progress
- Enforced linear progression — must complete each stage before the next unlocks (can't generate before analysis is done)
- Stage 4 (Alchemical Transmutation): simple generate button on campaign page with draft list below, not a complex hub
- Auto-advance with toast notification when prerequisites are met ("Community Intelligence complete — you can now generate drafts")

### Claude's Discretion
- LLM prompt construction strategy and template design
- Blacklist enforcement implementation (pre-generation filter vs post-generation check)
- Draft text editor component choice (plain textarea vs rich editor)
- Stage indicator visual design (stepper, badges, progress dots)
- Error states and loading patterns during generation

</decisions>

<specifics>
## Specific Ideas

- Sidebar gauges should be consistent with the ISC gauge already built in Phase 3 community profiles
- Copy to clipboard is important — the end goal is pasting into Reddit
- Stage transitions should feel seamless, auto-advancing without user friction

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 04-draft-generation*
*Context gathered: 2026-02-10*
