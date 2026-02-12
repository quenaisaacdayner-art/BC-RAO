---
status: resolved
trigger: "The system generates Reddit posts that look obviously AI-generated instead of being humanized and adapted to each subreddit's native patterns."
created: 2026-02-12T00:00:00Z
updated: 2026-02-12T02:00:00Z
---

## Current Focus

hypothesis: CONFIRMED and FIXED - 7 pipeline gaps identified and 5 fixed directly (2 medium-priority deferred).
test: All existing tests pass (25 blacklist + 35 ISC gating). New AI detection and prompt builder verified.
expecting: N/A - fixes applied and verified
next_action: Archive session

## Symptoms

expected: Posts should mimic native community behavior patterns - use subreddit-specific slang, tone, rhythm, structure. Posts should be indistinguishable from human-written posts on that subreddit.
actual: Posts are generic, use formal/corporate language, have obvious AI structure (bullet points, generic intros, ChatGPT-style language). Posts don't reflect the specific subreddit's communication patterns.
errors: No runtime errors - the system runs, but the output quality is poor. The analysis appears in the frontend visually, but it's unclear if the backend actually feeds pattern data into the generation prompts.
reproduction: Generate a draft for any subreddit - the output looks like generic AI content rather than native subreddit content.
started: Systemic issue since Phase 4 implementation.

## Eliminated

## Evidence

- timestamp: 2026-02-12T00:10:00Z
  checked: InferenceClient._call_openrouter() (client.py:134-162)
  found: |
    CRITICAL BUG: The OpenRouter API call sends ONLY a single "user" role message.
    PromptBuilder produces separate system + user prompts, but GenerationService
    combines them into a single string (line 145: combined_prompt = f"{prompts['system']}\n\n{prompts['user']}")
    and InferenceClient sends it as: {"role": "user", "content": combined_prompt}
    The system prompt is NOT sent as a system message - it's all crammed into user content.
  implication: |
    The LLM treats the entire prompt as a user request rather than having the system
    persona + constraints set separately. This significantly degrades instruction following.

- timestamp: 2026-02-12T00:15:00Z
  checked: PromptBuilder.build_prompt() (prompt_builder.py:31-119)
  found: |
    The prompt template includes Community DNA with numerical scores only.
    MISSING: No example posts from the subreddit. No vocabulary samples.
    The top_success_hooks from the community profile are NEVER used in the prompt.
    The _describe_rhythm() method exists but is NEVER CALLED in build_prompt().
  implication: |
    The LLM receives abstract numbers but zero concrete examples of how the community
    actually writes. Numbers like "formality: 6.2/10" are useless without examples.

- timestamp: 2026-02-12T00:20:00Z
  checked: Community profile data stored in DB (analysis_service.py:260-312)
  found: |
    _build_community_profile() DOES compute top_success_hooks (first sentences of
    top 5 posts by score) and stores them in the community_profiles table.
    But top_success_hooks and forbidden_patterns are NEVER read by PromptBuilder.
  implication: |
    Rich qualitative data IS collected and stored but is never passed to the generation
    prompt. The profile has example hooks from successful posts, but they're invisible.

- timestamp: 2026-02-12T00:25:00Z
  checked: Blacklist loading in generation_service.py (lines 100-110)
  found: |
    The generation service queries syntax_blacklist for columns: "regex_pattern, category, pattern_description"
    But the syntax_blacklist table schema has columns: forbidden_pattern, failure_type, confidence, etc.
    There is NO column called "regex_pattern" or "pattern_description" in the table.
  implication: |
    The blacklist patterns are NEVER actually loaded from the database. The LLM
    receives no forbidden patterns.

- timestamp: 2026-02-12T00:30:00Z
  checked: Prompt anti-AI instructions (prompt_builder.py full file)
  found: |
    The prompt has NO explicit anti-AI writing instructions. It says:
    "Write as if you are a genuine community member" but never specifies what to avoid.
  implication: |
    Without explicit anti-AI instructions, the LLM defaults to its polished, formal
    writing style which is the hallmark of AI-generated content.

- timestamp: 2026-02-12T00:35:00Z
  checked: NLP Pipeline data richness (nlp_pipeline.py, scorers.py)
  found: |
    The NLP pipeline produces ONLY numerical metrics. No extraction of common phrases,
    slang, opening patterns, punctuation habits, community-specific jargon.
  implication: |
    The Pattern Engine produces only abstract scores, not qualitative style data.
    (DEFERRED - requires NLP pipeline enhancement)

- timestamp: 2026-02-12T00:40:00Z
  checked: Post-generation validation (blacklist_validator.py)
  found: |
    Post-generation validation ONLY checks against DB blacklist patterns.
    No check for common AI writing patterns in the generated output.
  implication: |
    Even if the LLM produces AI-sounding content, the post-generation validation
    won't catch it. There's no quality gate for humanization.

## Resolution

root_cause: |
  MULTI-POINT PIPELINE FAILURE - 7 gaps where humanization data is lost or never applied:

  GAP 1 (CRITICAL - FIXED): InferenceClient sends system+user prompt as single "user" message
  GAP 2 (CRITICAL - FIXED): Prompt contains only numerical scores, no example text from community
  GAP 3 (CRITICAL - FIXED): Blacklist query uses wrong column names (regex_pattern vs forbidden_pattern)
  GAP 4 (HIGH - FIXED): No anti-AI writing instructions in prompt
  GAP 5 (HIGH - FIXED): top_success_hooks stored in DB but never injected into generation prompt
  GAP 6 (MEDIUM - DEFERRED): NLP pipeline extracts only numerical metrics, no qualitative style data
  GAP 7 (MEDIUM - FIXED): No post-generation AI-pattern detection

  FIXED DATA FLOW:
  ```
  raw_posts (rich text)
    -> NLP Pipeline (numbers + top_success_hooks extracted during profiling)
    -> community_profiles DB (stores numbers + hooks + forbidden_patterns)
    -> GenerationService loads profile (full profile including hooks)
    -> GenerationService loads blacklist (correct column names + profile patterns)
    -> PromptBuilder receives full profile (injects hooks as writing examples)
    -> Prompt built (examples + anti-AI rules + formality description + rhythm description)
    -> GenerationService sends system + user as SEPARATE messages
    -> InferenceClient sends proper system/user message pair to OpenRouter
    -> LLM generates community-native content (style reference + system persona)
    -> Blacklist check (DB patterns) + AI-pattern detection (structural tells)
    -> Quality-gated post returned with violation count
  ```

fix: |
  5 fixes applied across 4 files:

  FIX 1: InferenceClient system/user message separation
    - Added system_prompt parameter to InferenceClient.call()
    - _call_openrouter now accepts messages list instead of single prompt
    - When system_prompt provided, sends proper system + user message pair
    - Backward compatible: existing callers without system_prompt still work

  FIX 2: GenerationService uses separate system/user messages
    - Removed combined_prompt concatenation
    - Now passes prompts["system"] as system_prompt, prompts["user"] as prompt
    - Fixed blacklist DB column names: forbidden_pattern (not regex_pattern), etc.
    - Added injection of community-detected forbidden_patterns from profile

  FIX 3: PromptBuilder comprehensive overhaul
    - Added ANTI_AI_RULES constant with 30+ anti-AI writing instructions
    - Added _format_community_examples() to inject top_success_hooks as writing style examples
    - Added _describe_formality() for human-readable formality descriptions
    - Added _describe_rhythm_from_profile() for natural rhythm descriptions
    - Rewrote system persona from "expert marketer" to "real Reddit user"
    - Rewrote archetype guidance with more specific anti-AI voice instructions
    - All prompts now include anti-AI rules, community examples, and qualitative style guidance

  FIX 4: AI-pattern detection in post-generation validation
    - Added detect_ai_patterns() function with 6 pattern categories
    - Detects: formal transitions, ChatGPT phrases, corporate buzzwords,
      bullet point lists, generic greetings, "So," discourse marker
    - Integrated into generation pipeline as quality gate
    - AI pattern count added to blacklist_violations score

  FIX 5: Blacklist DB column name correction
    - Changed query from "regex_pattern, category, pattern_description"
      to "forbidden_pattern, category, failure_type, confidence"
    - Added normalization layer to map DB columns to PromptBuilder format
    - Also injects detected_patterns from community_profiles.forbidden_patterns

verification: |
  - 25/25 blacklist validator tests pass (existing tests unchanged)
  - 35/35 ISC gating tests pass (no regressions)
  - PromptBuilder manual verification: 4/4 test cases pass
    - Generic prompt includes anti-AI rules
    - Profile prompt includes success hooks and anti-AI rules
    - Blacklist patterns correctly included
    - Constraints correctly included
  - AI pattern detection verification: 2/2 test cases pass
    - AI-heavy text: 9 patterns detected (transitions, buzzwords, lists, greetings)
    - Human-like text: 0 patterns detected (no false positives)
  - Structural verification: 7/7 checks pass
    - InferenceClient.call has system_prompt parameter
    - _call_openrouter has messages parameter
    - GenerationService passes system_prompt
    - combined_prompt removed
    - Blacklist query uses correct columns
    - Profile forbidden_patterns injected
    - AI pattern detection integrated
  - Pre-existing test failures (65) confirmed unrelated (monitoring, regex_filter, cost_tracker)

files_changed:
  - bc-rao-api/app/inference/client.py
  - bc-rao-api/app/generation/generation_service.py
  - bc-rao-api/app/generation/prompt_builder.py
  - bc-rao-api/app/generation/blacklist_validator.py
