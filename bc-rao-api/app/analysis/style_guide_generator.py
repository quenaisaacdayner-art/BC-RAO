"""
LLM-based style guide generator for community writing fingerprints.

Sends top-performing posts + SpaCy structural metrics to Haiku via the
existing `extract_patterns` task slot to produce a natural-language
community writing style guide.

Cost: ~$0.003 per subreddit (Haiku at $0.0005/1K tokens).
"""

import json
import logging
from typing import List, Dict, Any, Optional

from app.inference.client import InferenceClient
from app.utils.errors import AppError

logger = logging.getLogger(__name__)

# Default empty style guide returned on failure
EMPTY_STYLE_GUIDE: Dict[str, Any] = {
    "voice_description": "",
    "vocabulary_guide": {"use_these": [], "avoid_these": [], "domain_terms": []},
    "opening_guide": "",
    "closing_guide": "",
    "formatting_rules": "",
    "emotional_tone": "",
    "taboo_patterns": "",
}

SYSTEM_PROMPT = """You are a sociolinguistic analyst specializing in online community communication patterns.
Analyze the provided Reddit posts and metrics to produce a precise community writing style guide.
Your analysis must be specific and actionable - avoid vague descriptions.
Use only concrete observations from the provided data.
Output valid JSON only, no markdown fences, no explanation."""

USER_PROMPT_TEMPLATE = """Analyze these top-performing posts from r/{subreddit} and produce a writing style guide.

## Community Metrics (from automated analysis)
- Average sentence length: {avg_sentence_length} words
- Formality level: {formality_desc}
- Dominant tone: {dominant_tone}
- Common terms: {top_terms}
- Common phrases: {top_noun_phrases}
- Detected slang/jargon: {oov_tokens}
- Question frequency: {question_ratio}% of sentences
- Typical post length: ~{avg_word_count} words
- TL;DR usage: {tldr_ratio}%

## Top Posts (highest community engagement)

{posts_block}

## Required Output (JSON)
Return EXACTLY this JSON structure:
{{
  "voice_description": "2-3 sentence description of HOW this community writes - their personality, energy, expertise level",
  "vocabulary_guide": {{
    "use_these": ["5-15 community-specific terms, slang, abbreviations to use naturally"],
    "avoid_these": ["5-10 terms that would sound out of place or corporate"],
    "domain_terms": ["5-15 technical/domain terms this community commonly uses"]
  }},
  "opening_guide": "How posts typically start, with 2-3 example patterns from the data",
  "closing_guide": "How posts typically end, with 2-3 example patterns from the data",
  "formatting_rules": "Paragraph length, line breaks, formatting conventions observed",
  "emotional_tone": "The emotional register and energy level of this community",
  "taboo_patterns": "What would immediately mark a post as outsider/corporate/AI-generated in this community"
}}"""


async def generate_style_guide(
    subreddit: str,
    top_posts: List[Dict[str, str]],
    style_metrics: Dict[str, Any],
    user_id: str,
    plan: str,
    campaign_id: str,
) -> Dict[str, Any]:
    """
    Generate a natural-language style guide for a subreddit using LLM analysis.

    Sends top-performing posts + SpaCy structural metrics to Haiku to produce
    an actionable writing style guide. The style guide is structured for direct
    injection into generation prompts via PromptBuilder._format_style_guide().

    Args:
        subreddit: Target subreddit name
        top_posts: Top 10-15 posts with "title" and "raw_text" keys
        style_metrics: Output from extract_community_style() (SpaCy data)
        user_id: User UUID for cost tracking
        plan: User plan (trial, starter, growth)
        campaign_id: Campaign UUID

    Returns:
        Style guide dict with voice_description, vocabulary_guide, etc.
        Returns EMPTY_STYLE_GUIDE on any failure (graceful degradation).
    """
    if not top_posts:
        logger.warning(f"No posts provided for style guide generation for r/{subreddit}")
        return EMPTY_STYLE_GUIDE.copy()

    # Build posts block (truncate each post to 500 chars)
    posts_block = _format_posts_for_prompt(top_posts)

    # Extract metrics for prompt
    vocab = style_metrics.get("vocabulary", {})
    structure = style_metrics.get("structure", {})
    formatting = style_metrics.get("formatting", {})

    # Describe formality from metrics
    formality_desc = _describe_formality_from_metrics(style_metrics)

    user_prompt = USER_PROMPT_TEMPLATE.format(
        subreddit=subreddit,
        avg_sentence_length=structure.get("avg_post_word_count", "unknown"),
        formality_desc=formality_desc,
        dominant_tone="mixed",  # Will be enriched from profile in caller
        top_terms=", ".join(vocab.get("top_terms", [])[:15]),
        top_noun_phrases=", ".join(vocab.get("top_noun_phrases", [])[:10]),
        oov_tokens=", ".join(vocab.get("oov_tokens", [])[:10]) or "none detected",
        question_ratio=round(structure.get("question_sentence_ratio", 0) * 100, 1),
        avg_word_count=structure.get("avg_post_word_count", "unknown"),
        tldr_ratio=round(formatting.get("has_tldr_ratio", 0) * 100, 1),
        posts_block=posts_block,
    )

    # Call LLM via existing extract_patterns task slot
    try:
        client = InferenceClient(task="extract_patterns")
        result = await client.call(
            prompt=user_prompt,
            system_prompt=SYSTEM_PROMPT,
            user_id=user_id,
            plan=plan,
            campaign_id=campaign_id,
        )

        content = result["content"].strip()
        style_guide = _parse_style_guide_json(content)

        logger.info(
            f"Style guide generated for r/{subreddit}: "
            f"{result['token_count']} tokens, ${result['cost_usd']:.4f}"
        )

        return style_guide

    except AppError as e:
        # Budget exceeded or inference failed - graceful degradation
        logger.warning(f"Style guide generation failed for r/{subreddit}: {e.message}")
        return EMPTY_STYLE_GUIDE.copy()
    except Exception as e:
        logger.error(f"Unexpected error generating style guide for r/{subreddit}: {e}")
        return EMPTY_STYLE_GUIDE.copy()


def _format_posts_for_prompt(posts: List[Dict[str, str]], max_posts: int = 12) -> str:
    """Format top posts for LLM prompt, truncating each to 500 chars."""
    lines = []
    for i, post in enumerate(posts[:max_posts], 1):
        title = post.get("title", "Untitled")
        text = post.get("raw_text", "")[:500]
        lines.append(f'Post {i}: "{title}"\n{text}\n')
    return "\n".join(lines)


def _describe_formality_from_metrics(style_metrics: Dict[str, Any]) -> str:
    """Derive a formality description from SpaCy metrics."""
    vocab = style_metrics.get("vocabulary", {})
    stop_ratio = vocab.get("stop_word_ratio", 0.4)

    if stop_ratio > 0.48:
        return "Very casual (high stop-word ratio indicates informal writing)"
    elif stop_ratio > 0.43:
        return "Casual conversational"
    elif stop_ratio > 0.38:
        return "Moderate formality"
    else:
        return "Formal/technical (low stop-word ratio)"


def _parse_style_guide_json(content: str) -> Dict[str, Any]:
    """
    Parse LLM response as JSON style guide.

    Handles common LLM output issues: markdown code fences, extra text
    before/after JSON, etc.
    """
    # Strip markdown code fences if present
    content = content.strip()
    if content.startswith("```"):
        # Remove opening fence (with optional language tag)
        first_newline = content.index("\n")
        content = content[first_newline + 1:]
    if content.endswith("```"):
        content = content[:-3]
    content = content.strip()

    # Try direct JSON parse
    try:
        parsed = json.loads(content)
        return _validate_style_guide(parsed)
    except json.JSONDecodeError:
        pass

    # Try extracting JSON from surrounding text
    try:
        start = content.index("{")
        end = content.rindex("}") + 1
        parsed = json.loads(content[start:end])
        return _validate_style_guide(parsed)
    except (ValueError, json.JSONDecodeError):
        logger.warning(f"Failed to parse style guide JSON. Raw content: {content[:200]}")
        return EMPTY_STYLE_GUIDE.copy()


def _validate_style_guide(parsed: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure all expected keys exist with correct types."""
    result = EMPTY_STYLE_GUIDE.copy()

    # String fields
    for key in ["voice_description", "opening_guide", "closing_guide",
                 "formatting_rules", "emotional_tone", "taboo_patterns"]:
        if key in parsed and isinstance(parsed[key], str):
            result[key] = parsed[key]

    # Vocabulary guide (nested dict with lists)
    if "vocabulary_guide" in parsed and isinstance(parsed["vocabulary_guide"], dict):
        vg = parsed["vocabulary_guide"]
        result["vocabulary_guide"] = {
            "use_these": vg.get("use_these", []) if isinstance(vg.get("use_these"), list) else [],
            "avoid_these": vg.get("avoid_these", []) if isinstance(vg.get("avoid_these"), list) else [],
            "domain_terms": vg.get("domain_terms", []) if isinstance(vg.get("domain_terms"), list) else [],
        }

    return result
