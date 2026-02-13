---
status: diagnosed
trigger: "generic-ai-detectable-drafts — posts too generic/AI-detectable, 6 anti-patterns identified"
created: 2026-02-12T00:00:00Z
updated: 2026-02-12T01:00:00Z
---

## Current Focus

hypothesis: CONFIRMED — 6 root causes identified across the generation pipeline, each mapped to specific code locations
test: Full codebase analysis of all 12 generation-related files complete
expecting: N/A — diagnosis complete
next_action: Deliver comprehensive analysis with fix recommendations

## Symptoms

expected: Posts that sound like a frustrated/passionate human — starting with climax, raw technical details, abrupt endings, niche biases, stream-of-consciousness with digressions
actual: Posts follow AI-typical patterns — balanced intro-dev-conclusion, generic descriptions, tidy metrics, polite conclusions, perfect grammar, numbered lists with bold headers
errors: No runtime errors — quality/output issue
reproduction: Generate any draft — output consistently follows generic AI patterns
started: Since initial implementation of Phase 4 (Draft Generation)

## Eliminated

(none — all 6 hypothesized anti-patterns confirmed as present in codebase)

## Evidence

- timestamp: 2026-02-12T00:10:00Z
  checked: prompt_builder.py — ANTI_AI_RULES (lines 36-71)
  found: Rules are phrased as negations ("NEVER do X") rather than positive instructions with examples. LLMs follow positive instructions far better than negations. No concrete examples of what TO DO.
  implication: The anti-AI rules fight symptoms rather than reshaping generation behavior.

- timestamp: 2026-02-12T00:12:00Z
  checked: prompt_builder.py — _get_archetype_guidance() (lines 221-258)
  found: Journey archetype explicitly asks for "emotional arc: frustration -> searching -> discovery -> relief/progress" which is EXACTLY the symmetrical intro-body-conclusion structure. ProblemSolution asks for "90% pain / 10% solution" but still describes a conventional narrative arc. All three archetypes use bullet-point lists to describe structure, which the LLM mirrors.
  implication: Archetype guidance inadvertently encodes the symmetrical structure problem.

- timestamp: 2026-02-12T00:14:00Z
  checked: prompt_builder.py — build_prompt() user message (lines 168-170)
  found: User message is only 2 lines — "Write a {archetype} post for r/{subreddit} about: {user_context}". No specific narrative structure, no example of desired output, no anti-pattern injections in user message. All intelligence is in system prompt only.
  implication: User prompt provides no structural guidance to counteract LLM defaults.

- timestamp: 2026-02-12T00:16:00Z
  checked: prompt_builder.py — _format_community_examples() (lines 316-342)
  found: Only uses opening hooks (first lines). Does not show full post examples, mid-post style, endings, or the messy structural patterns of real posts. Limited to 5 examples, truncated to single lines.
  implication: Community examples are too shallow to teach full writing style.

- timestamp: 2026-02-12T00:18:00Z
  checked: blacklist_validator.py — AI_TELL_PATTERNS (lines 16-29)
  found: Only 6 detection patterns. Misses: symmetrical structure detection, "moral of the story" endings, perfect grammar patterns, neutral tone detection, generic descriptions, tidy metrics patterns. Detection is post-hoc and only logs warnings — does NOT trigger regeneration.
  implication: Post-generation quality gate is too weak and non-blocking.

- timestamp: 2026-02-12T00:20:00Z
  checked: generation_service.py — Step 6b (lines 201-209)
  found: AI pattern detection only logs warnings and adds to blacklist_violations count. Does NOT trigger automatic regeneration or filtering. The draft is stored as-is regardless of AI tells.
  implication: AI detection is informational only, not actionable.

- timestamp: 2026-02-12T00:22:00Z
  checked: inference/router.py — generate_draft config (line 14-19)
  found: Temperature is 0.7 for draft generation. This is moderate — produces relatively safe, predictable text. No top_p, frequency_penalty, or presence_penalty parameters.
  implication: Model parameters don't push for creative/unpredictable output.

- timestamp: 2026-02-12T00:24:00Z
  checked: prompt_builder.py — _format_style_guide() and _format_style_metrics()
  found: Style guide and metrics are injected as structured data sections in the system prompt. They describe community patterns but don't instruct the LLM to DEVIATE from its defaults. No instructions for imperfect syntax, stream-of-consciousness, or structural asymmetry.
  implication: Community DNA is presented as reference, not as actionable mutation instructions.

- timestamp: 2026-02-12T00:26:00Z
  checked: scorers.py — calculate_post_score() and vulnerability patterns
  found: Scoring only measures vulnerability (personal pronouns/emotions), rhythm adherence, formality match, jargon penalty, and link density. Does NOT score: structural asymmetry, ending quality, visceral specificity, bias presence, grammar imperfection, or burstiness.
  implication: Quality scoring doesn't measure the 6 anti-patterns, so the system can't optimize for them.

- timestamp: 2026-02-12T00:28:00Z
  checked: style_guide_generator.py — USER_PROMPT_TEMPLATE
  found: Style guide asks for "opening_guide" and "closing_guide" but not "structural patterns", "digression patterns", "imperfection patterns", or "bias vocabulary". The generated style guide is structurally conventional.
  implication: Style guide generation doesn't capture the messy human patterns needed.

- timestamp: 2026-02-12T00:30:00Z
  checked: isc_gating.py — constraints
  found: ISC constraints focus on promotional/authenticity safety but do NOT add structural diversity instructions. No constraint says "vary your post structure" or "avoid predictable patterns".
  implication: Gating system misses opportunity to inject structural diversity.

## Resolution

root_cause: 6 interconnected root causes (see detailed analysis in response)
fix: Multi-layer fix across prompt_builder.py, blacklist_validator.py, generation_service.py, scorers.py, inference/router.py, style_guide_generator.py, isc_gating.py
verification: Generate drafts and evaluate against 6 anti-pattern criteria + AI detection tools
files_changed: []
