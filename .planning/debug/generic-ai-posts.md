---
status: investigating
trigger: "GAP 6 deep investigation - NLP pipeline extracts only numerical metrics, no qualitative style data"
created: 2026-02-12T02:30:00Z
updated: 2026-02-12T03:30:00Z
---

## Current Focus

hypothesis: The NLP pipeline and analysis service extract only 7 numerical/categorical fields. SpaCy's en_core_web_md model provides POS tagging, dependency parsing, lemmatization, and word vectors that are completely unused. An LLM-based "style guide generator" using the existing `extract_patterns` task slot is the highest-impact enhancement.
test: Code audit complete - mapping all extracted vs available vs needed data
expecting: Design document with full enhancement roadmap
next_action: N/A - investigation and design complete (documented below)

## Symptoms

expected: NLP pipeline should extract qualitative style fingerprints (common phrases, slang, vocabulary, opening patterns, punctuation habits, formatting conventions) that feed into generation prompts.
actual: NLP pipeline extracts only 7 numerical/categorical fields. PromptBuilder receives abstract numbers like "formality: 6.2/10" with zero concrete examples of community writing style.
errors: No runtime errors - the pipeline works correctly for what it does. The gap is in what it DOES NOT do.
reproduction: Run analysis on any subreddit - the community_profiles table will contain only numerical aggregates and top_success_hooks (first sentences of top 5 posts). No vocabulary lists, no slang extraction, no formatting conventions, no style fingerprints.
started: Architectural limitation since Phase 3 implementation.

## Eliminated

(No hypotheses eliminated - this is an investigation/design session, not a bug hunt)

## Evidence

- timestamp: 2026-02-12T02:35:00Z
  checked: NLP Pipeline - complete field inventory (nlp_pipeline.py)
  found: |
    The pipeline extracts EXACTLY 7 fields per post:
    1. formality_score (float) - Flesch-Kincaid + Gunning FOG average
    2. tone (str) - "positive" / "negative" / "neutral" via VADER
    3. tone_compound (float) - VADER compound score (-1.0 to 1.0)
    4. avg_sentence_length (float) - tokens per sentence
    5. sentence_length_std (float) - standard deviation of sentence lengths
    6. vocabulary_complexity (float) - type-token ratio (unique lemmas / total tokens)
    7. num_sentences (int) - count of sentences

    ZERO qualitative fields. No text extraction of any kind.
  implication: |
    The pipeline produces only abstract numbers. These numbers tell you
    "this community uses ~15 word sentences at formality 6.2" but give you
    ZERO examples of HOW they actually write.

- timestamp: 2026-02-12T02:40:00Z
  checked: SpaCy en_core_web_md capabilities (UNUSED by current pipeline)
  found: |
    The loaded SpaCy model (en_core_web_md) provides these capabilities
    that the pipeline DOES NOT USE:

    USED (partially):
    - Sentence segmentation (doc.sents) -> used for length counts only
    - Lemmatization (token.lemma_) -> used for type-token ratio only
    - is_alpha token filter -> used for vocabulary_complexity only

    COMPLETELY UNUSED:
    - POS tagging (token.pos_, token.tag_) -> Part-of-speech tags
      Could extract: sentence structure patterns, question frequency,
      adjective/adverb density, noun phrase patterns
    - Dependency parsing (token.dep_, token.head) -> Syntactic structure
      Could extract: sentence complexity, subordinate clause frequency,
      writing maturity indicators
    - Word vectors (token.vector, doc.similarity()) -> 300d word embeddings
      Could extract: semantic clustering of vocabulary, topic coherence,
      vocabulary similarity between posts
    - Named Entity Recognition -> DISABLED in current config (line 28)
      Could be re-enabled for: brand mention detection, location patterns
    - Noun chunks (doc.noun_chunks) -> Multi-word noun phrases
      Could extract: common topic phrases, jargon terms, domain vocabulary
    - Token attributes: token.is_stop, token.is_punct, token.shape_
      Could extract: punctuation patterns, stop word ratio, word shape patterns
  implication: |
    We are paying the computational cost of loading a 91MB SpaCy model with
    300d word vectors but only using ~10% of its capabilities. Significant
    qualitative extraction is possible WITHOUT any additional cost or API calls.

- timestamp: 2026-02-12T02:45:00Z
  checked: Analysis Service - what qualitative data IS extracted (analysis_service.py)
  found: |
    The _build_community_profile() method (lines 260-312) extracts:

    QUALITATIVE DATA ALREADY EXTRACTED:
    1. top_success_hooks: First sentence of top 5 posts by score (list[str])
       - Extraction: text.split('.')[0] up to 200 chars
       - Stored in: community_profiles.top_success_hooks (JSONB)
       - USED in prompt: YES (after GAP 5 fix)

    2. forbidden_patterns: Pattern extractor results (dict)
       - Contains: by_category counts + detected_patterns list
       - Stored in: community_profiles.forbidden_patterns (JSONB)
       - USED in prompt: YES (after GAP 3/5 fix)

    3. archetype_distribution: Count of posts per archetype (dict)
       - Stored in: community_profiles.archetype_distribution (JSONB)
       - USED in prompt: NO (available but not consumed by PromptBuilder)

    QUALITATIVE DATA NOT EXTRACTED:
    - Common vocabulary / frequently used terms
    - Slang and abbreviations
    - Opening/closing patterns beyond first sentence
    - Punctuation habits (emoji usage, exclamation frequency)
    - Formatting conventions (paragraph length, use of edits, TL;DR)
    - Common sentence structures
    - Question patterns
    - Community-specific jargon
  implication: |
    The existing qualitative extraction is minimal - only first sentences
    of top posts. The forbidden_patterns is detection-focused (what NOT to do)
    not style-focused (HOW to write).

- timestamp: 2026-02-12T02:50:00Z
  checked: Pattern Extractor - what it analyzes (pattern_extractor.py)
  found: |
    extract_forbidden_patterns() scans for 6 NEGATIVE pattern categories:
    - Promotional (10 patterns)
    - Self-referential (9 patterns)
    - Link patterns (7 patterns)
    - Low-effort (5 patterns)
    - Spam indicators (5 patterns)
    - Off-topic (3 patterns)

    All patterns are hardcoded regex. Results are counts + severity.

    ZERO POSITIVE pattern extraction:
    - Does NOT extract "what works" patterns
    - Does NOT extract community writing style patterns
    - Does NOT identify common phrases/vocabulary in successful posts
  implication: |
    The pattern extractor is exclusively negative (what to avoid).
    There is no "positive pattern extractor" that identifies what
    makes community writing distinctive. This is a fundamental gap.

- timestamp: 2026-02-12T02:55:00Z
  checked: Scorers module - what it calculates (scorers.py)
  found: |
    5 scoring functions, ALL producing numerical outputs:
    1. calculate_vulnerability_weight() -> 0-10 score
    2. calculate_rhythm_adherence() -> 0-10 score
    3. calculate_formality_match() -> 0-10 score
    4. calculate_marketing_jargon_penalty() -> 0-10 penalty + phrase list
    5. calculate_link_density_penalty() -> 0-10 penalty + link list

    ISC calculation: Weighted average of 4 numerical factors.

    The ONLY textual data extracted is jargon/link phrases for penalty
    highlighting. No positive style data extraction.
  implication: |
    Scorers are designed for scoring, not for style extraction.
    They can't be repurposed for qualitative data.

- timestamp: 2026-02-12T03:00:00Z
  checked: Community profiles DB schema (001_initial_schema.sql, lines 118-134)
  found: |
    community_profiles table columns:
    - id (UUID PK)
    - campaign_id (UUID FK)
    - subreddit (TEXT)
    - isc_score (FLOAT)
    - avg_sentence_length (FLOAT)
    - dominant_tone (TEXT)
    - formality_level (FLOAT)
    - top_success_hooks (JSONB DEFAULT '[]')
    - forbidden_patterns (JSONB DEFAULT '[]')
    - archetype_distribution (JSONB DEFAULT '{}')
    - sample_size (INT)
    - last_analyzed_at (TIMESTAMPTZ)
    - created_at, updated_at (TIMESTAMPTZ)

    JSONB columns can store arbitrary data without schema migration.
    Adding a new JSONB column `style_guide` would require migration 003.
  implication: |
    Two storage approaches are viable:
    A) Pack new data into existing JSONB columns (no migration)
    B) Add new `style_guide` JSONB column (clean, requires migration 003)
    Option B is strongly preferred for clarity and queryability.

- timestamp: 2026-02-12T03:05:00Z
  checked: Inference Router - extract_patterns task config (router.py)
  found: |
    MODEL_ROUTING already has an `extract_patterns` task:
    {
      "model": "anthropic/claude-3-haiku-20240307",
      "max_tokens": 1000,
      "temperature": 0.2,
      "fallback": "google/gemini-flash-1.5"
    }

    This task is NOT CURRENTLY USED anywhere in the codebase.
    It was defined in the spec but never implemented.

    Cost: Haiku = $0.0005/1K tokens
    For 10-20 posts at ~200 words each = ~4K input tokens + ~1K output = ~5K tokens
    Cost per subreddit: ~$0.0025 (less than half a cent)

    For comparison:
    - generate_draft uses Sonnet 4 at $0.015/1K = 30x more expensive
    - A single draft generation costs ~$0.045 (9K tokens estimated)
    - Style analysis adds < 6% to the cost of generating ONE draft
  implication: |
    The LLM-based approach is EXTREMELY cheap. Using Haiku for style
    extraction costs a fraction of a cent per subreddit. The infrastructure
    (InferenceClient, cost tracking, budget enforcement) already exists.
    The extract_patterns task slot was designed for exactly this purpose.

- timestamp: 2026-02-12T03:10:00Z
  checked: PromptBuilder - what qualitative data it CAN consume (prompt_builder.py)
  found: |
    Current PromptBuilder consumes from profile:
    - isc_score -> ISC tier + rules
    - formality_level -> _describe_formality() natural language
    - avg_sentence_length -> _describe_rhythm_from_profile() natural language
    - dominant_tone -> mood label
    - top_success_hooks -> _format_community_examples() real post openings
    - blacklist_patterns -> _format_blacklist() forbidden patterns

    PromptBuilder already has the ARCHITECTURE to consume rich data.
    It has dedicated formatter methods for each data type.
    Adding a new `_format_style_guide()` method is straightforward.

    The system prompt template (lines 132-161) has clear section structure:
    ## Community DNA, ## Community Examples, ## Anti-AI Rules, ## Archetype,
    ## Constraints, ## Forbidden Patterns, ## ISC Rules, ## Output Rules

    A new section "## Community Writing Style Guide" would fit naturally
    between Community Examples and Anti-AI Rules.
  implication: |
    PromptBuilder is already designed for extensibility. The new style
    guide data just needs a formatter method and insertion into the template.

- timestamp: 2026-02-12T03:15:00Z
  checked: Raw post data available for analysis (collection_service.py, raw_posts schema)
  found: |
    Raw posts stored in DB contain:
    - raw_text (TEXT NOT NULL) -> full post body
    - title (TEXT NOT NULL) -> post title
    - comment_count (INT) -> engagement metric
    - upvote_ratio (FLOAT) -> quality signal
    - archetype (ENUM) -> post type
    - success_score (FLOAT) -> composite quality score
    - rhythm_metadata (JSONB) -> NLP results stored per post

    For style analysis, we have access to:
    - Full text of ALL collected posts (typically 50-100 per subreddit)
    - Quality scores to identify top-performing posts
    - Archetype labels to analyze style per archetype

    The data richness is there - we just need to extract style from it.
  implication: |
    No new data collection needed. The raw_posts table already contains
    everything needed for both SpaCy-based and LLM-based style extraction.

## Resolution

root_cause: |
  GAP 6 ROOT CAUSE: The NLP pipeline was designed exclusively for NUMERICAL
  SCORING, not for QUALITATIVE STYLE EXTRACTION. This is an architectural
  limitation, not a bug.

  The pipeline processes text through SpaCy and produces 7 numbers.
  These numbers are consumed by scorers to produce more numbers.
  These numbers are aggregated into community profiles with averages.
  At no point does any component extract WHAT THE COMMUNITY ACTUALLY
  WRITES - their vocabulary, phrases, formatting habits, or structural patterns.

  The result: PromptBuilder tells the LLM "formality is 6.2/10" but never
  shows it "here's how r/python actually writes." The top_success_hooks
  (GAP 5 fix) partially addresses this with 5 example openings, but 5
  truncated first sentences are insufficient to capture a community's
  full writing fingerprint.

fix: |
  NOT IMPLEMENTED - DESIGN ONLY (per user instruction)

  See "Enhancement Design" section below for full design document.

verification: |
  N/A - investigation and design session only.

files_changed: []

---

# GAP 6 DEEP INVESTIGATION: Enhancement Design Document

## 1. CURRENT STATE MAP

### 1.1 What the NLP Pipeline Currently Extracts (Per Post)

| # | Field | Type | Source | Used By |
|---|-------|------|--------|---------|
| 1 | formality_score | float | Flesch-Kincaid + Gunning FOG | Scorer -> community_profiles.formality_level |
| 2 | tone | str | VADER sentiment (pos/neg/neutral) | community_profiles.dominant_tone |
| 3 | tone_compound | float | VADER compound (-1.0 to 1.0) | Stored in rhythm_metadata only |
| 4 | avg_sentence_length | float | Token count / sentence count | Scorer -> community_profiles.avg_sentence_length |
| 5 | sentence_length_std | float | Stdev of sentence lengths | Scorer (rhythm_adherence) |
| 6 | vocabulary_complexity | float | Type-token ratio (unique/total) | Stored in rhythm_metadata only |
| 7 | num_sentences | int | Sentence count | Stored in rhythm_metadata only |

### 1.2 What Analysis Service Adds (Per Subreddit Profile)

| # | Field | Source | Used by PromptBuilder? |
|---|-------|--------|----------------------|
| 1 | isc_score | ISC calculator (4-factor weighted) | YES |
| 2 | avg_sentence_length | Mean of post averages | YES |
| 3 | dominant_tone | Mode of VADER tone labels | YES |
| 4 | formality_level | Mean of post formality scores | YES |
| 5 | top_success_hooks | First sentence of top 5 posts | YES (after GAP 5 fix) |
| 6 | forbidden_patterns | Pattern extractor results | YES (after GAP 3/5 fix) |
| 7 | archetype_distribution | Count by archetype | NO (available, unused) |
| 8 | sample_size | Post count | NO |

### 1.3 What SpaCy en_core_web_md Provides But Is UNUSED

| Capability | SpaCy API | Potential Extraction |
|-----------|-----------|---------------------|
| POS tagging | `token.pos_`, `token.tag_` | Adjective density, question frequency, imperative frequency |
| Dependency parsing | `token.dep_`, `token.head` | Sentence complexity, subordination depth |
| Word vectors | `token.vector` (300d) | Vocabulary clustering, semantic similarity |
| Noun chunks | `doc.noun_chunks` | Domain jargon, common topic phrases |
| Stop words | `token.is_stop` | Stop word ratio (casual vs formal indicator) |
| Punctuation | `token.is_punct`, `token.text` | Emoji frequency, exclamation patterns, ellipsis use |
| Token shape | `token.shape_` | Capitalization patterns, abbreviation patterns |

## 2. WHAT QUALITATIVE DATA IS MISSING

### 2.1 Critical Missing Data (Directly Impacts Generation Quality)

| # | Missing Data | Impact | Extraction Method |
|---|-------------|--------|------------------|
| 1 | **Common vocabulary / frequent terms** | LLM can't match community vocabulary | SpaCy: lemma frequency + noun chunks |
| 2 | **Slang and abbreviations** | Posts sound formal instead of native | SpaCy: OOV tokens + shape analysis; LLM: explicit extraction |
| 3 | **Opening patterns** (beyond first sentence) | LLM uses generic openings | LLM: analyze first 2-3 sentences of top posts |
| 4 | **Formatting conventions** | Wrong paragraph length, missing TL;DR | Regex + heuristic: paragraph count, avg paragraph length, TL;DR presence |
| 5 | **Community-specific jargon** | Generic technical language instead of domain terms | SpaCy: noun chunks with high tf-idf; LLM: explicit extraction |

### 2.2 High-Value Missing Data (Significant Quality Improvement)

| # | Missing Data | Impact | Extraction Method |
|---|-------------|--------|------------------|
| 6 | **Sentence structure patterns** | Uniform sentence complexity | SpaCy: POS n-grams, dependency tree depth distribution |
| 7 | **Punctuation habits** | Missing community-specific punctuation style | SpaCy: punctuation token frequency, emoji/emoticon count |
| 8 | **Emotional tone patterns** | Flat emotional register | LLM: nuanced tone description beyond pos/neg/neutral |
| 9 | **Closing patterns** | AI-style neat conclusions | LLM: analyze last 2-3 sentences of top posts |
| 10 | **Question patterns** | Generic questions vs community-style questions | SpaCy: POS analysis of interrogative sentences |

### 2.3 Nice-to-Have Missing Data (Polish)

| # | Missing Data | Impact | Extraction Method |
|---|-------------|--------|------------------|
| 11 | **Post length distribution** | Over/under-writing for community norms | Heuristic: word count statistics |
| 12 | **Edit/update patterns** | Missing "EDIT:" culture | Regex: "EDIT:", "UPDATE:", "ETA:" frequency |
| 13 | **Paragraph structure** | Wrong information density | Heuristic: sentences per paragraph distribution |
| 14 | **Link usage norms** | Including/excluding links inappropriately | Regex: URL frequency and placement |
| 15 | **Humor/sarcasm indicators** | Missing tonal nuance | LLM: only reliable extractor for this |

## 3. ENHANCEMENT DESIGN: HYBRID APPROACH (SpaCy + LLM)

### 3.1 Architecture Decision: SpaCy vs LLM vs Hybrid

| Approach | Strengths | Weaknesses | Cost |
|----------|-----------|------------|------|
| **SpaCy-only** | Free, fast, deterministic, no API dependency | Can't extract semantic meaning, can't describe style in natural language, limited to structural patterns | $0 |
| **LLM-only** | Rich qualitative extraction, natural language output, can identify nuance | Costs tokens, non-deterministic, slower, requires prompt engineering | ~$0.003/subreddit |
| **Hybrid (RECOMMENDED)** | SpaCy extracts structural patterns (free); LLM synthesizes into style guide (cheap) | Slightly more complex pipeline | ~$0.003/subreddit |

**RECOMMENDATION: Hybrid approach.**

Rationale:
- SpaCy extracts FREE structural data that grounds the LLM analysis
- LLM synthesizes raw data + example posts into a coherent "style guide"
- The `extract_patterns` task slot already exists in router.py with Haiku ($0.0005/1K)
- Total cost per subreddit analysis: < $0.003 (less than 6% of one draft generation)
- Infrastructure already exists: InferenceClient, CostTracker, budget enforcement

### 3.2 Phase A: SpaCy Qualitative Extractor (FREE - No API Costs)

**New file: `bc-rao-api/app/analysis/style_extractor.py`**

Extracts structural style fingerprints using EXISTING SpaCy capabilities:

```
Function: extract_community_style(texts: list[str], top_texts: list[str]) -> dict

Input:
  - texts: ALL post texts for the subreddit
  - top_texts: Top 10-20 posts by success_score (for positive pattern emphasis)

Output dict:
{
  "vocabulary": {
    "top_terms": ["term1", "term2", ...],        # Top 30 non-stop lemmas by frequency
    "top_noun_phrases": ["phrase1", "phrase2"], # Top 20 noun chunks by frequency
    "oov_tokens": ["slang1", "abbrev1", ...],   # Out-of-vocabulary = likely slang/jargon
    "avg_word_length": 4.8,
    "stop_word_ratio": 0.42,                    # Higher = more casual
  },
  "structure": {
    "avg_paragraph_count": 3.2,
    "avg_paragraph_length_sentences": 2.8,
    "avg_post_word_count": 187,
    "post_word_count_std": 95,
    "question_sentence_ratio": 0.15,            # % sentences that are questions
    "imperative_ratio": 0.08,                   # % sentences starting with verbs
  },
  "punctuation": {
    "exclamation_per_post": 1.2,
    "question_mark_per_post": 0.8,
    "ellipsis_per_post": 0.3,                   # "..." usage
    "emoji_per_post": 0.1,
    "parenthetical_per_post": 0.5,              # () usage
  },
  "formatting": {
    "has_tldr_ratio": 0.15,                     # % posts with TL;DR
    "has_edit_ratio": 0.08,                     # % posts with EDIT:
    "has_links_ratio": 0.25,                    # % posts containing URLs
    "has_code_blocks_ratio": 0.05,              # % posts with ``` or indented code
    "avg_line_breaks": 4.5,                     # Line breaks per post
  },
  "openings": {
    "top_opening_patterns": [                    # First 3-5 words of top posts
      {"pattern": "I've been ...", "count": 5},
      {"pattern": "So I ...", "count": 3},
    ],
  },
}
```

**Implementation approach:**
- New SpaCy pipeline component `style_analyzer` OR standalone function
- Uses existing `nlp` model instance (no additional model loading)
- Processes same texts already being processed (minimal overhead)
- Integrates into `AnalysisService.run_analysis()` after NLP batch processing

**SpaCy features used:**
- `doc.noun_chunks` -> top_noun_phrases
- `token.lemma_` frequency -> top_terms
- `token.is_oov` (out of vocabulary) -> oov_tokens (slang/jargon detection)
- `token.is_stop` ratio -> formality indicator
- `token.pos_ == "PUNCT"` + `token.text` -> punctuation analysis
- `sent.root.pos_` -> question/imperative detection
- Regex on raw text -> formatting conventions (TL;DR, EDIT, code blocks)

### 3.3 Phase B: LLM Style Guide Generator (< $0.003/subreddit)

**New file: `bc-rao-api/app/analysis/style_guide_generator.py`**

Uses the existing `extract_patterns` InferenceClient task to synthesize a
natural-language style guide from raw posts + SpaCy metrics.

```
Function: generate_style_guide(
    subreddit: str,
    top_posts: list[dict],        # Top 10-15 posts with title + raw_text
    style_metrics: dict,           # Output from Phase A SpaCy extraction
    user_id: str,
    plan: str,
    campaign_id: str,
) -> dict

Output dict:
{
  "voice_description": "Casual, self-deprecating, technically precise. Community members write like experienced developers venting to peers. Frequent use of 'lol', 'tbh', rhetorical questions.",

  "vocabulary_guide": {
    "use_these": ["lol", "tbh", "ngl", "IIRC", "TIL"],
    "avoid_these": ["leverage", "utilize", "streamline"],
    "domain_terms": ["type hints", "decorator", "f-string", "list comp"],
  },

  "opening_guide": "Jump straight into the problem or discovery. Most popular openings start with 'I' or an action verb. Never greet the community. Example patterns: 'I just spent 3 hours...', 'Finally figured out why...', 'Anyone else annoyed by...'",

  "closing_guide": "End with a question, an open thought, or just stop. Never summarize. Common endings: asking for others' experience, sharing next steps, trailing off with '...'",

  "formatting_rules": "Keep paragraphs to 2-3 sentences. Use line breaks between thoughts. Code examples are expected and appreciated. TL;DR is common for longer posts.",

  "emotional_tone": "Frustrated but humorous. Self-aware. Mix of genuine technical passion and mild exasperation. Enthusiasm is acceptable when sharing genuine discoveries.",

  "taboo_patterns": "Never use corporate language. Never sound like a press release. Avoid exclamation marks for emphasis - let the content speak. Never use 'game-changer' or similar marketing words."
}
```

**LLM Prompt Design (system + user messages):**

System:
```
You are a sociolinguistic analyst specializing in online community communication patterns.
Analyze the provided Reddit posts and metrics to produce a precise community writing style guide.
Your analysis must be specific and actionable - avoid vague descriptions.
Output JSON only.
```

User:
```
Analyze these top-performing posts from r/{subreddit} and produce a writing style guide.

## Community Metrics (from automated analysis)
- Average sentence length: {avg_sentence_length} words
- Formality level: {formality_desc}
- Dominant tone: {dominant_tone}
- Common terms: {top_terms}
- Common phrases: {top_noun_phrases}
- Detected slang/jargon: {oov_tokens}
- Question frequency: {question_ratio}%
- Post length: ~{avg_word_count} words
- TL;DR usage: {tldr_ratio}%

## Top Posts (highest community engagement)

Post 1: "{title_1}"
{text_1[:500]}

Post 2: "{title_2}"
{text_2[:500]}

[... up to 10-15 posts, truncated at 500 chars each]

## Required Output (JSON)
{
  "voice_description": "2-3 sentence description of HOW this community writes",
  "vocabulary_guide": {
    "use_these": ["5-15 community-specific terms, slang, abbreviations"],
    "avoid_these": ["5-10 terms that would sound out of place"],
    "domain_terms": ["5-15 technical/domain terms this community uses"]
  },
  "opening_guide": "How posts typically start (with 2-3 example patterns)",
  "closing_guide": "How posts typically end (with 2-3 example patterns)",
  "formatting_rules": "Paragraph length, line breaks, code blocks, lists usage",
  "emotional_tone": "Emotional register and energy level",
  "taboo_patterns": "What would immediately mark a post as outsider/AI"
}
```

**Token estimate:**
- System prompt: ~80 tokens
- User prompt with 10 posts at 500 chars: ~4,000 tokens
- Output: ~500 tokens
- Total: ~4,580 tokens
- Cost at Haiku rates ($0.0005/1K): ~$0.0023 per subreddit

### 3.4 Phase C: Schema Changes

**New migration: `migrations/003_community_style_guide.sql`**

```sql
-- Add style_guide JSONB column to community_profiles
ALTER TABLE community_profiles
    ADD COLUMN IF NOT EXISTS style_guide JSONB DEFAULT '{}';

-- Add style_metrics JSONB column for SpaCy structural data
ALTER TABLE community_profiles
    ADD COLUMN IF NOT EXISTS style_metrics JSONB DEFAULT '{}';

-- Comment for documentation
COMMENT ON COLUMN community_profiles.style_guide IS
    'LLM-generated natural language style guide for the community (voice, vocabulary, formatting)';

COMMENT ON COLUMN community_profiles.style_metrics IS
    'SpaCy-extracted structural style metrics (vocabulary frequency, punctuation habits, formatting conventions)';
```

Two new JSONB columns:
- `style_metrics` -> SpaCy structural data (Phase A output)
- `style_guide` -> LLM natural language guide (Phase B output)

Why two columns instead of one:
- `style_metrics` is deterministic, free to recompute, useful for frontend display
- `style_guide` is LLM-generated, costs tokens, is the actual prompt injection data
- Separation allows re-running SpaCy analysis without re-running LLM extraction
- Frontend can display style_metrics directly (charts, stats) while style_guide is for backend

### 3.5 Phase D: PromptBuilder Integration

**Modified file: `bc-rao-api/app/generation/prompt_builder.py`**

New method: `_format_style_guide(style_guide: dict) -> str`

```
## Community Writing Style Guide for r/{subreddit}

VOICE: {voice_description}

VOCABULARY:
- Use naturally: {use_these joined}
- Never use: {avoid_these joined}
- Domain terms to know: {domain_terms joined}

OPENINGS: {opening_guide}

CLOSINGS: {closing_guide}

FORMATTING: {formatting_rules}

EMOTIONAL REGISTER: {emotional_tone}

TABOO (instant detection as outsider): {taboo_patterns}
```

Inserted into system prompt between "## How This Community Actually Writes" and
"## CRITICAL: Anti-AI Writing Rules". This positions the style guide as contextual
grounding before the restrictive rules.

### 3.6 Phase E: Analysis Service Integration

**Modified file: `bc-rao-api/app/services/analysis_service.py`**

In `run_analysis()`, add steps between current Step 5 (forbidden patterns) and
Step 6 (build profile):

```
# Step 5.1: Extract structural style metrics (SpaCy - FREE)
top_scored = sorted(scored_posts, key=lambda p: p.get("total_score", 0), reverse=True)
top_texts = [p["raw_text"] for p in top_scored[:20]]
style_metrics = extract_community_style(texts, top_texts)

# Step 5.2: Generate LLM style guide (Haiku - ~$0.003)
style_guide = await generate_style_guide(
    subreddit=subreddit,
    top_posts=[{"title": p.get("title", ""), "raw_text": p["raw_text"]} for p in top_scored[:15]],
    style_metrics=style_metrics,
    user_id=user_id,          # Need to pass through from campaign
    plan=plan,                 # Need to pass through
    campaign_id=campaign_id,
)
```

**Note:** `run_analysis()` currently doesn't receive `user_id` or `plan` parameters.
These need to be added to the method signature and passed from the route handler.
This is necessary for InferenceClient budget tracking.

### 3.7 Generation Service Integration

**Modified file: `bc-rao-api/app/generation/generation_service.py`**

In `generate_draft()`, Step 1 already loads `profile = profile_response.data[0]`.
The `style_guide` will be available as `profile.get("style_guide", {})`.

PromptBuilder.build_prompt() already receives the full profile dict.
It needs to read `profile.get("style_guide", {})` and call `_format_style_guide()`.

No changes needed to GenerationService beyond what PromptBuilder handles.

## 4. COST ANALYSIS

### 4.1 Per-Subreddit Analysis Cost

| Component | Cost | Notes |
|-----------|------|-------|
| SpaCy style extraction | $0.000 | Local processing, no API |
| LLM style guide (Haiku) | ~$0.003 | ~4.5K tokens at $0.0005/1K |
| **Total per subreddit** | **~$0.003** | |

### 4.2 Impact on User Budgets

| Plan | Monthly Cap | Style Analysis Cost (5 subreddits) | % of Budget |
|------|------------|-------------------------------------|-------------|
| Trial | $5.00 | $0.015 | 0.3% |
| Starter | $15.00 | $0.015 | 0.1% |
| Growth | $40.00 | $0.015 | 0.04% |

Style analysis is negligible relative to budget caps.

### 4.3 Comparison to Draft Generation

- One draft generation: ~$0.045 (Sonnet 4, ~3K tokens)
- Style analysis for 5 subreddits: ~$0.015
- Style analysis pays for itself if it prevents even ONE regeneration
  (regeneration cost = $0.045, style analysis = $0.015)

## 5. TRADEOFFS: SpaCy-Only vs LLM-Only vs Hybrid

### 5.1 SpaCy-Only (Phase A only)

**Pros:**
- Zero ongoing cost
- Deterministic results
- Fast processing
- No API dependency

**Cons:**
- Cannot describe writing "voice" in natural language
- Cannot identify semantic patterns (humor, sarcasm, expertise level)
- Output is structured data, not prose the LLM can directly absorb
- Cannot compare posts to identify what makes top posts distinctive
- Limited to syntactic patterns (POS, frequency, structure)

**Verdict:** Useful as foundation but insufficient alone. Numbers like
"exclamation_per_post: 1.2" don't teach the LLM HOW to write.

### 5.2 LLM-Only (Phase B only, no SpaCy grounding)

**Pros:**
- Rich natural language output
- Can identify nuanced patterns (humor, expertise, community norms)
- Direct prompt-ready output

**Cons:**
- Non-deterministic (different runs may produce different guides)
- Without structural grounding, may hallucinate patterns
- Costs tokens every time (even if re-analyzing same data)
- Slower (API round-trip)
- Can't produce precise statistical metrics

**Verdict:** Powerful but unreliable without grounding data.

### 5.3 Hybrid (RECOMMENDED)

**Pros:**
- SpaCy provides FREE structural grounding (prevents LLM hallucination)
- LLM synthesizes into actionable natural language (prompt-ready)
- Best of both: precision of NLP + nuance of LLM
- SpaCy metrics available for frontend display (charts, stats)
- LLM guide available for prompt injection
- Fault-tolerant: if LLM fails, SpaCy data still improves prompts

**Cons:**
- More complex pipeline (two steps)
- Slightly more code to maintain

**Verdict:** The added complexity is minimal. The quality improvement is substantial.

## 6. PRIORITIZED IMPLEMENTATION ROADMAP

### Wave 1: SpaCy Style Extractor (FREE, no API cost, no migration)
**Complexity: Medium | Impact: High | Files: 2 modified, 1 new**

| Step | File | Change | Complexity |
|------|------|--------|-----------|
| 1.1 | NEW: `bc-rao-api/app/analysis/style_extractor.py` | Create style_extractor module with `extract_community_style()` function | Medium |
| 1.2 | `bc-rao-api/app/services/analysis_service.py` | Import and call `extract_community_style()` in `run_analysis()`, pass results to `_build_community_profile()` | Low |
| 1.3 | `bc-rao-api/app/services/analysis_service.py` | Update `_build_community_profile()` to include style_metrics in profile dict | Low |
| 1.4 | Tests for style_extractor | Unit tests with sample Reddit-like texts | Medium |

**Deliverable:** Community profiles now contain `style_metrics` with vocabulary, structure, punctuation, and formatting data. Stored in existing JSONB columns (no migration needed if packed into `forbidden_patterns` or similar -- but cleaner with migration).

### Wave 2: Schema Migration + PromptBuilder Basic Integration
**Complexity: Low | Impact: Medium | Files: 2 modified, 1 new**

| Step | File | Change | Complexity |
|------|------|--------|-----------|
| 2.1 | NEW: `migrations/003_community_style_guide.sql` | Add `style_guide` and `style_metrics` JSONB columns | Low |
| 2.2 | `bc-rao-api/app/generation/prompt_builder.py` | Add `_format_style_metrics()` method that converts SpaCy metrics to natural language for prompt | Medium |
| 2.3 | `bc-rao-api/app/generation/prompt_builder.py` | Inject style metrics section into system prompt template | Low |
| 2.4 | Tests for PromptBuilder style formatting | Verify style metrics appear in generated prompts | Low |

**Deliverable:** Even without LLM style guide, prompts now include "Top vocabulary: ..., Formatting: ..., Punctuation style: ..." from SpaCy data.

### Wave 3: LLM Style Guide Generator
**Complexity: Medium | Impact: Very High | Files: 2 modified, 1 new**

| Step | File | Change | Complexity |
|------|------|--------|-----------|
| 3.1 | NEW: `bc-rao-api/app/analysis/style_guide_generator.py` | Create module with `generate_style_guide()` async function, prompt design, JSON parsing | Medium-High |
| 3.2 | `bc-rao-api/app/services/analysis_service.py` | Add `user_id` and `plan` params to `run_analysis()`, call `generate_style_guide()` after SpaCy extraction | Medium |
| 3.3 | `bc-rao-api/app/services/analysis_service.py` | Update `_build_community_profile()` to include `style_guide` in profile dict | Low |
| 3.4 | `bc-rao-api/app/generation/prompt_builder.py` | Add `_format_style_guide()` method, inject into system prompt | Medium |
| 3.5 | Tests for style_guide_generator | Mock InferenceClient, verify prompt structure and JSON parsing | Medium |

**Deliverable:** Full hybrid pipeline. Community profiles contain both structural metrics and LLM-generated natural language style guide. PromptBuilder injects the style guide into every generation prompt.

### Wave 4: End-to-End Verification + Tuning
**Complexity: Medium | Impact: High | Files: 0 new**

| Step | Description | Complexity |
|------|-------------|-----------|
| 4.1 | Generate drafts for 3-5 different subreddits with style guides | Medium |
| 4.2 | Compare output quality: with style guide vs without | Medium |
| 4.3 | Tune LLM style guide prompt based on output quality | Low-Medium |
| 4.4 | Verify AI-pattern detection doesn't flag style-guided posts | Low |
| 4.5 | Verify budget tracking includes style analysis costs | Low |

### Dependency Graph

```
Wave 1 (SpaCy extractor) ─────> Wave 2 (Schema + basic integration)
                                          │
                                          v
                                 Wave 3 (LLM style guide)
                                          │
                                          v
                                 Wave 4 (Verification + tuning)
```

Wave 1 and Wave 2 can be partially parallelized (schema migration is independent
of SpaCy extractor). Wave 3 depends on both being complete.

## 7. FILE INVENTORY (Complete Change List)

### New Files (3)

| File | Purpose | Wave |
|------|---------|------|
| `bc-rao-api/app/analysis/style_extractor.py` | SpaCy qualitative extraction | 1 |
| `bc-rao-api/app/analysis/style_guide_generator.py` | LLM style guide synthesis | 3 |
| `migrations/003_community_style_guide.sql` | Schema migration for new columns | 2 |

### Modified Files (3)

| File | Changes | Wave |
|------|---------|------|
| `bc-rao-api/app/services/analysis_service.py` | Add style extraction + LLM guide calls to pipeline, add user_id/plan params | 1, 3 |
| `bc-rao-api/app/generation/prompt_builder.py` | Add _format_style_metrics() and _format_style_guide() methods | 2, 3 |
| `bc-rao-api/app/inference/router.py` | Possibly adjust extract_patterns max_tokens if needed | 3 |

### Test Files (2-3 new)

| File | Tests | Wave |
|------|-------|------|
| `bc-rao-api/tests/test_style_extractor.py` | SpaCy extraction with sample texts | 1 |
| `bc-rao-api/tests/test_style_guide_generator.py` | LLM prompt structure + JSON parsing | 3 |
| `bc-rao-api/tests/test_prompt_builder_style.py` | Style data injection into prompts | 2, 3 |

## 8. RISK ASSESSMENT

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| LLM style guide returns invalid JSON | Medium | Low | JSON parsing with fallback to empty dict |
| SpaCy `is_oov` misidentifies common words as slang | Medium | Low | Filter by frequency threshold (>2 occurrences) |
| Style guide makes prompts too long (token limit) | Low | Medium | Truncate style guide to 500 tokens, prioritize vocabulary + voice |
| Style analysis significantly slows analysis pipeline | Low | Low | SpaCy adds <1s, LLM adds ~2-3s (acceptable) |
| LLM hallucinates community patterns | Medium | Medium | SpaCy grounding data prevents this; include "based on these specific examples" anchoring |
| Budget impact on trial users | Low | Low | $0.003/subreddit is negligible vs $5 cap |
| `run_analysis()` signature change breaks callers | Medium | Medium | Add user_id/plan as Optional with defaults |

## 9. OPEN QUESTIONS FOR USER

1. **Should style analysis be mandatory or opt-in?**
   - Mandatory: Every `run_analysis()` call includes style extraction
   - Opt-in: New parameter `include_style_guide=True`
   - Recommendation: Mandatory (cost is negligible, quality improvement is significant)

2. **Should the frontend display style metrics?**
   - If yes, `style_metrics` needs to be included in the API response for community profiles
   - This affects frontend design but not backend implementation

3. **Should style guide be cached per subreddit globally or per campaign?**
   - Currently: community_profiles are per campaign (same subreddit analyzed differently for different campaigns)
   - If cached globally: one analysis serves all campaigns (cheaper but less personalized)
   - Recommendation: Keep per-campaign (matches existing architecture)

4. **Implementation priority relative to other work?**
   - This can be implemented as a standalone phase
   - Wave 1 (SpaCy only) provides immediate value at zero cost
   - Wave 3 (LLM guide) provides maximum value at minimal cost
