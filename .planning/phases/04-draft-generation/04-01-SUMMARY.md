---
phase: 04-draft-generation
plan: 01
subsystem: generation
tags: [llm, prompt-engineering, openrouter, inference, isc-gating, blacklist-validation, draft-generation]

# Dependency graph
requires:
  - phase: 01-foundation
    provides: InferenceClient, Supabase integration, error handling utilities
  - phase: 03-pattern-engine
    provides: NLP pipeline, scoring functions, community profiles, ISC calculation
provides:
  - Draft generation pipeline with ISC gating and blacklist validation
  - Dynamic prompt construction from community profiles
  - Post-generation scoring (vulnerability + rhythm match)
  - 5-branch account status decision tree
affects: [04-02-drafts-api, 04-03-drafts-frontend, generation-workflows]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Dynamic prompt construction from community intelligence
    - ISC-based archetype gating (5-branch decision tree)
    - Post-generation blacklist validation with regex patterns
    - Generic defaults for unprofiled subreddits

key-files:
  created:
    - bc-rao-api/app/models/draft.py
    - bc-rao-api/app/generation/__init__.py
    - bc-rao-api/app/generation/isc_gating.py
    - bc-rao-api/app/generation/blacklist_validator.py
    - bc-rao-api/app/generation/prompt_builder.py
    - bc-rao-api/app/generation/generation_service.py
  modified: []

key-decisions:
  - "ISC gating enforces 5 branches: New accounts (warm-up), High ISC > 7.5 (Feedback only), ProblemSolution/Journey/Feedback archetype rules"
  - "Generic defaults used when no community profile exists - system never crashes on profile absence"
  - "Post-generation blacklist validation catches LLM violations that slip through prompt instructions"
  - "Vulnerability and rhythm scores calculated via existing NLP pipeline for consistency"

patterns-established:
  - "ISC gating pattern: validate_generation_request() returns constraints list injected into prompt"
  - "Prompt builder pattern: GENERIC_DEFAULTS dict for unprofiled subreddits"
  - "Blacklist validator pattern: Compile patterns at check time (patterns from DB, not module-level)"
  - "Generation service pipeline: profile load → blacklist load → ISC gating → prompt build → LLM call → post-validation → scoring → storage"

# Metrics
duration: 15min
completed: 2026-02-11
---

# Phase 04 Plan 01: Generation Pipeline Core Summary

**ISC-gated draft generation with dynamic prompts from community profiles, 5-branch account status decision tree, and post-generation blacklist validation**

## Performance

- **Duration:** 15 min
- **Started:** 2026-02-11T02:43:07Z
- **Completed:** 2026-02-11T02:58:12Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- Draft generation pipeline transforms community intelligence into conditioned LLM prompts
- ISC gating enforces all 5 decision tree branches (New accounts, High ISC > 7.5, archetype-specific rules)
- Post-generation blacklist validation catches forbidden patterns in generated text
- Profile absence handled gracefully with generic defaults - no crashes

## Task Commits

Each task was committed atomically:

1. **Task 1: Draft models and ISC gating + blacklist validator** - `3a585ef` (feat)
2. **Task 2: Prompt builder and generation service** - `cf31b1f` (feat)

## Files Created/Modified
- `bc-rao-api/app/models/draft.py` - Pydantic models for draft requests/responses and blacklist validation
- `bc-rao-api/app/generation/__init__.py` - Generation module initialization
- `bc-rao-api/app/generation/isc_gating.py` - ISC gating with 5-branch decision tree
- `bc-rao-api/app/generation/blacklist_validator.py` - Post-generation regex validation and link/jargon scanning
- `bc-rao-api/app/generation/prompt_builder.py` - Dynamic prompt construction from community profiles
- `bc-rao-api/app/generation/generation_service.py` - Full generation pipeline orchestration

## Decisions Made

**ISC gating decision tree implementation:**
- New accounts forced to Feedback archetype with max vulnerability, zero links (warm-up mode)
- High ISC > 7.5 blocks Journey/ProblemSolution, forces Feedback with zero links
- ProblemSolution: 90% pain / 10% solution ratio, no greetings, product mention only in last 10%
- Journey: Technical diary style with milestones, numbers, metrics
- Feedback: Invert authority, ask community to find flaws

**Generic defaults strategy:**
- When no community profile exists, use GENERIC_DEFAULTS (isc_score=5.0, formality="Casual but clear")
- Log warning but continue generation - never crash on missing profile
- System displays warning in UI that profile doesn't exist

**Post-generation validation:**
- Blacklist validation runs after LLM generation (catches violations that slip through prompt)
- Violations logged but don't block draft creation - user can see warnings and regenerate
- Link density, sentence length, jargon scanning utilities for future scoring enhancements

**InferenceClient usage:**
- Uses existing InferenceClient from Phase 1 (not separate OpenAI SDK)
- Task type "generate_draft" routes to appropriate model via MODEL_ROUTING
- Budget checking and cost tracking automatically enforced

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - all imports verified, pipeline orchestration logic straightforward.

## User Setup Required

None - no external service configuration required. Generation uses existing InferenceClient and Supabase integrations.

## Next Phase Readiness

**Ready for Phase 04-02 (Drafts API endpoints):**
- GenerationService provides complete CRUD operations
- All models defined and validated
- ISC gating and blacklist validation ready for API integration

**Ready for Phase 04-03 (Drafts Frontend):**
- DraftResponse model matches frontend requirements
- ISC gating returns forced_archetype for UI auto-switch
- Blacklist violations tracked for display in draft editor

**No blockers.** Generation core complete and tested via imports.

## Self-Check: PASSED

All key files verified on disk.
All commits verified in git history.

---
*Phase: 04-draft-generation*
*Completed: 2026-02-11*
