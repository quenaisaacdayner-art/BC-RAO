---
phase: 03
plan: 01
subsystem: pattern-engine
tags: [nlp, spacy, scoring, pattern-detection, isc, vulnerability-analysis]
requires: [02-01, 02-02, 02-03]
provides: [nlp-pipeline, post-scoring, isc-calculation, pattern-extraction]
affects: [03-02, 03-03, 03-04]
tech-stack:
  added: [spacy>=3.8.0, textstat>=0.7.12, vaderSentiment>=3.3.2, en_core_web_md]
  patterns: [spacy-custom-components, compiled-regex-patterns, batch-processing]
key-files:
  created:
    - bc-rao-api/app/analysis/__init__.py
    - bc-rao-api/app/analysis/nlp_pipeline.py
    - bc-rao-api/app/analysis/scorers.py
    - bc-rao-api/app/analysis/pattern_extractor.py
    - bc-rao-api/app/models/analysis.py
  modified:
    - bc-rao-api/pyproject.toml
key-decisions:
  - decision: "SpaCy pipeline with 3 custom components (formality, tone, rhythm)"
    rationale: "Modular components allow independent metric calculation, custom Doc extensions enable clean API"
  - decision: "Disable NER in SpaCy model loading"
    rationale: "Named entity recognition not needed for post analysis, saves memory"
  - decision: "textstat.set_lang('en') at module level"
    rationale: "Per research pitfall 6, prevents language detection on each call"
  - decision: "Vulnerability score based on personal pronouns + emotions + storytelling"
    rationale: "Authentic posts use 'I/my/we' language and share personal experiences"
  - decision: "Weighted scoring formula with penalties"
    rationale: "Total = (vulnerability*0.25 + rhythm*0.25 + formality*0.2) - (jargon*0.15 + links*0.15)"
  - decision: "ISC requires minimum 10 posts"
    rationale: "Statistical validity - quartile analysis needs sufficient sample size"
  - decision: "6 pattern categories for forbidden detection"
    rationale: "Covers all major rejection signals: promotional, self-referential, links, low-effort, spam, off-topic"
  - decision: "Compiled regex patterns at module level"
    rationale: "Performance optimization - patterns compiled once, reused for all posts"
duration: 6.5 minutes
completed: 2026-02-11
---

# Phase 03 Plan 01: SpaCy NLP Pipeline + Scoring + Pattern Detection Summary

**One-liner:** SpaCy pipeline with custom formality/tone/rhythm components, vulnerability-based post scoring (0-10), ISC community sensitivity calculation, and 6-category forbidden pattern detection—all local, zero API cost.

## Performance

**Execution time:** 6.5 minutes
**Commits:** 2 (atomic per task)
**Files created:** 5
**Dependencies installed:** spacy, textstat, vaderSentiment, en_core_web_md model

## Accomplishments

### NLP Pipeline Architecture

✅ **Custom SpaCy components registered via @Language.component:**
- `formality_scorer`: Averages Flesch-Kincaid grade + Gunning FOG (handles <20 char edge case)
- `tone_classifier`: VADER sentiment (compound >= 0.05 = positive, <= -0.05 = negative, else neutral)
- `rhythm_analyzer`: Sentence length avg/std + vocabulary complexity (type-token ratio)

✅ **Doc extensions for clean metric access:**
- formality_score, tone, tone_compound, avg_sentence_length, sentence_length_std, vocabulary_complexity, num_sentences

✅ **Batch processing function:**
- `analyze_posts_batch(texts, batch_size=100)` uses nlp.pipe() for efficiency
- Never uses n_process inside workers (avoids deadlock per research)
- Handles empty/None texts gracefully with default values

### Scoring Algorithms

✅ **5-factor post scoring:**
1. **Vulnerability weight (0-10):** Personal pronouns, emotions, questions, storytelling signals
2. **Rhythm adherence (0-10):** Sentence length pattern match vs community avg ± std dev
3. **Formality match (0-10):** Post formality vs community formality (10 - abs(diff) * 2)
4. **Marketing jargon penalty (0-10):** 16 patterns (synergy, leverage, paradigm, disrupt, game-changer, growth hack, etc.)
5. **Link density penalty (0-10):** URL count (0=0, 1=3, 2=6, 3+=9)

✅ **Total score formula:**
```
total = (vulnerability*0.25 + rhythm*0.25 + formality*0.2) - (jargon*0.15 + links*0.15)
```
Clamped 0-10, returns penalty_phrases for inline highlighting.

✅ **ISC (Intrinsic Sensitivity Coefficient) calculator:**
- Measures community sensitivity to marketing (1.0-10.0 scale)
- 4 factors: jargon_sensitivity (30%), link_sensitivity (20%), vulnerability_preference (30%), depth_correlation (20%)
- Compares top quartile vs bottom quartile posts
- Requires minimum 10 posts, raises ValueError otherwise

### Pattern Detection

✅ **6 forbidden pattern categories:**
1. **Promotional:** Affiliate links, discount codes, "check out my", limited time offers
2. **Self-referential:** "My product/tool/startup", "I built", company name drops
3. **Link patterns:** URL shorteners (bit.ly, tinyurl), UTM params, Amazon affiliate, multiple URLs
4. **Low-effort:** <50 char posts, "thoughts?", generic intros
5. **Spam indicators:** Excessive !, ALL CAPS, repetitive phrases, wall-of-text, emoji spam
6. **Off-topic:** Clickbait, "you won't believe", shocking

✅ **Pattern extraction functions:**
- `extract_forbidden_patterns(texts)`: Batch analysis, returns by_category counts + detected_patterns with severity
- `check_post_penalties(text)`: Per-post check, returns matched phrases for inline highlighting
- Severity classification: high (>20% posts), medium (10-20%), low (<10%)

### Pydantic Models

✅ **Complete API response models:**
- `NLPResult`: Single post NLP metrics
- `PostScoreBreakdown`: Detailed scoring with penalty phrases
- `CommunityProfileResponse`: ISC score + tier + behavioral patterns
- `CommunityProfileListResponse`: Profile list wrapper
- `AnalysisProgress`: Real-time SSE progress tracking
- `AnalysisResult`: Job completion summary
- `ForbiddenPatternEntry`: Single pattern with category + system/user flag
- `BlacklistResponse`: Grouped patterns by category
- `isc_to_tier()` helper: Maps score to "Low/Moderate/High/Very High Sensitivity"

## Task Commits

| Task | Commit | Summary |
|------|--------|---------|
| 1 | fd2362d | SpaCy NLP pipeline with 3 custom components + Pydantic models |
| 2 | bbcb85a | Post success scoring + ISC calculator + forbidden pattern extractor |

## Files Created/Modified

**Created:**
- `bc-rao-api/app/analysis/__init__.py` (6 lines) - Package init with docstring
- `bc-rao-api/app/analysis/nlp_pipeline.py` (202 lines) - SpaCy pipeline with custom components
- `bc-rao-api/app/analysis/scorers.py` (395 lines) - Post scoring + ISC calculation
- `bc-rao-api/app/analysis/pattern_extractor.py` (197 lines) - 6-category pattern detection
- `bc-rao-api/app/models/analysis.py` (105 lines) - Pydantic models for all analysis responses

**Modified:**
- `bc-rao-api/pyproject.toml` - Added spacy, textstat, vaderSentiment dependencies

**Total:** 905 lines of production code

## Decisions Made

1. **SpaCy en_core_web_md model:** Medium model provides good accuracy/performance tradeoff. NER disabled saves memory (not needed for post analysis).

2. **Custom Doc extensions over dict returns:** SpaCy's Doc.set_extension pattern provides cleaner API than manual dict passing between components.

3. **Vulnerability scoring as authenticity proxy:** Personal pronouns (I/my/we), emotional markers, questions, and storytelling signals reliably identify authentic vs promotional content.

4. **Weighted formula balances positive/negative factors:** 25% vulnerability + 25% rhythm + 20% formality provides base score. Jargon and link penalties subtract 15% each, ensuring promotional content can't score high even with perfect rhythm.

5. **ISC quartile comparison methodology:** Comparing top 25% vs bottom 25% posts isolates community preferences. Jargon/link ratios between quartiles reveal sensitivity patterns.

6. **Compiled regex patterns at module level:** One-time compilation cost, reused for all posts. Significant performance gain vs re-compiling per call.

7. **Pattern categories cover rejection signals:** Research showed communities reject promotional, self-referential, link spam, low-effort, and spam patterns. All 6 categories implemented.

8. **Severity classification by percentage:** >20% = high, 10-20% = medium, <10% = low provides actionable feedback (high severity = community-wide pattern).

9. **Minimum 10 posts for ISC:** Statistical validity requirement. Quartile analysis on <10 posts produces unreliable results.

10. **Zero external API dependencies:** All processing via SpaCy/textstat/VADER = zero API cost. Critical for scaling to thousands of posts per campaign.

## Deviations from Plan

None - plan executed exactly as written.

All must_haves verified:
- ✅ SpaCy pipeline processes post text and extracts formality, tone, sentence length, vocabulary complexity
- ✅ Scoring functions calculate ISC, vulnerability weight, rhythm adherence, marketing jargon penalty, link density penalty
- ✅ Pattern extractor detects forbidden patterns and categorizes into Promotional, Self-referential, Link patterns, etc.
- ✅ All NLP runs locally with zero external API cost
- ✅ All artifact paths created with minimum line counts exceeded
- ✅ All key_links patterns present (SpaCy decorators, imports)

## Issues Encountered

**Issue 1: Missing SpaCy dependencies**
- **Context:** Initial import failed with ModuleNotFoundError
- **Resolution:** Installed spacy, textstat, vaderSentiment via pip, then downloaded en_core_web_md model
- **Impact:** No blocker, standard setup requirement

No other issues encountered. All verification commands passed:
- NLP pipeline and models import successfully
- Pipeline processes sample text and returns valid metrics
- Post scoring calculates all 5 factors + total score
- Pattern extractor detects promotional/link/jargon patterns

## Next Phase Readiness

**Phase 03 Plan 02 prerequisites:**

✅ **Ready to build:**
- Analysis service can now orchestrate NLP pipeline via analyze_posts_batch()
- Post scoring ready for batch processing via calculate_post_score()
- ISC calculation ready for community profiling via calculate_isc_score()
- Pattern extraction ready for blacklist detection via extract_forbidden_patterns()

**Integration points:**
- Plan 02 will create AnalysisService that calls these modules
- Celery task will use analyze_posts_batch() for background processing
- Database models will store ISC scores, post scores, forbidden patterns
- API endpoints will return Pydantic models from this plan

**No blockers.** All computational core functions complete and tested.

---

## Self-Check: PASSED

✅ Created files verified:
- bc-rao-api/app/analysis/__init__.py exists
- bc-rao-api/app/analysis/nlp_pipeline.py exists

✅ Commits verified:
- fd2362d exists in git log
- bbcb85a exists in git log
