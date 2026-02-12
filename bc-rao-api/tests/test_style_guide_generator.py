"""Tests for LLM-based style guide generator."""

import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.analysis.style_guide_generator import (
    generate_style_guide,
    _parse_style_guide_json,
    _format_posts_for_prompt,
    _describe_formality_from_metrics,
    EMPTY_STYLE_GUIDE,
)


# Sample style metrics (output from style_extractor)
SAMPLE_METRICS = {
    "vocabulary": {
        "top_terms": ["build", "startup", "revenue", "user", "growth"],
        "top_noun_phrases": ["monthly revenue", "product market fit"],
        "oov_tokens": ["lol", "tbh", "ngl", "PMF"],
        "avg_word_length": 4.8,
        "stop_word_ratio": 0.42,
    },
    "structure": {
        "avg_paragraph_count": 3.2,
        "avg_paragraph_length_sentences": 2.8,
        "avg_post_word_count": 187,
        "post_word_count_std": 95,
        "question_sentence_ratio": 0.15,
        "imperative_ratio": 0.08,
    },
    "formatting": {
        "has_tldr_ratio": 0.15,
        "has_edit_ratio": 0.08,
        "has_links_ratio": 0.25,
        "has_code_blocks_ratio": 0.05,
        "avg_line_breaks": 4.5,
    },
}

SAMPLE_POSTS = [
    {"title": "Hit $5k MRR after 6 months", "raw_text": "Been building my SaaS for 6 months and finally hit $5k MRR. The journey was brutal."},
    {"title": "Churn is killing us", "raw_text": "Anyone else struggling with churn? We're at 8% monthly and it's killing our growth."},
    {"title": "Raised our seed round", "raw_text": "Just raised our seed round - $1.2M at $6M post. Took 4 months of pitching."},
]

VALID_STYLE_GUIDE_JSON = json.dumps({
    "voice_description": "Casual, self-deprecating, technically precise. Like experienced devs venting to peers.",
    "vocabulary_guide": {
        "use_these": ["lol", "tbh", "PMF", "ARR", "MRR"],
        "avoid_these": ["leverage", "optimize", "streamline"],
        "domain_terms": ["MRR", "churn", "CAC", "LTV"],
    },
    "opening_guide": "Jump straight into the problem. Most openings start with 'I' or action verb.",
    "closing_guide": "End with a question or just stop.",
    "formatting_rules": "2-3 sentence paragraphs. TL;DR common for long posts.",
    "emotional_tone": "Frustrated but humorous. Self-aware.",
    "taboo_patterns": "Never use corporate language. Never sound like a press release.",
})


class TestParseStyleGuideJson:
    """Test JSON parsing with various LLM output formats."""

    def test_valid_json(self):
        result = _parse_style_guide_json(VALID_STYLE_GUIDE_JSON)
        assert result["voice_description"] == "Casual, self-deprecating, technically precise. Like experienced devs venting to peers."
        assert "lol" in result["vocabulary_guide"]["use_these"]

    def test_json_with_code_fences(self):
        wrapped = f"```json\n{VALID_STYLE_GUIDE_JSON}\n```"
        result = _parse_style_guide_json(wrapped)
        assert result["voice_description"] != ""

    def test_json_with_surrounding_text(self):
        wrapped = f"Here is the analysis:\n{VALID_STYLE_GUIDE_JSON}\nHope this helps!"
        result = _parse_style_guide_json(wrapped)
        assert result["voice_description"] != ""

    def test_invalid_json_returns_empty(self):
        result = _parse_style_guide_json("This is not JSON at all")
        assert result == EMPTY_STYLE_GUIDE

    def test_partial_json_fills_defaults(self):
        partial = json.dumps({
            "voice_description": "Casual and fun",
            # Missing other keys
        })
        result = _parse_style_guide_json(partial)
        assert result["voice_description"] == "Casual and fun"
        assert result["vocabulary_guide"] == {"use_these": [], "avoid_these": [], "domain_terms": []}

    def test_wrong_types_handled(self):
        bad_types = json.dumps({
            "voice_description": 123,  # Should be string
            "vocabulary_guide": "not a dict",  # Should be dict
        })
        result = _parse_style_guide_json(bad_types)
        # Wrong types should fall back to defaults
        assert result["voice_description"] == ""  # int is not str
        assert result["vocabulary_guide"] == {"use_these": [], "avoid_these": [], "domain_terms": []}


class TestFormatPostsForPrompt:
    """Test post formatting for LLM prompt."""

    def test_formats_posts(self):
        result = _format_posts_for_prompt(SAMPLE_POSTS)
        assert "Post 1:" in result
        assert "Hit $5k MRR" in result
        assert "Post 3:" in result

    def test_truncates_long_posts(self):
        long_post = {"title": "Long", "raw_text": "x" * 1000}
        result = _format_posts_for_prompt([long_post])
        # Should be truncated to 500 chars
        assert len(result.split("\n")[1]) <= 500

    def test_respects_max_posts(self):
        many_posts = [{"title": f"Post {i}", "raw_text": f"Text {i}"} for i in range(20)]
        result = _format_posts_for_prompt(many_posts, max_posts=5)
        assert "Post 5:" in result
        assert "Post 6:" not in result

    def test_empty_posts(self):
        result = _format_posts_for_prompt([])
        assert result == ""


class TestDescribeFormalityFromMetrics:
    """Test formality description from metrics."""

    def test_very_casual(self):
        metrics = {"vocabulary": {"stop_word_ratio": 0.5}}
        result = _describe_formality_from_metrics(metrics)
        assert "casual" in result.lower()

    def test_formal(self):
        metrics = {"vocabulary": {"stop_word_ratio": 0.35}}
        result = _describe_formality_from_metrics(metrics)
        assert "formal" in result.lower()

    def test_empty_metrics(self):
        result = _describe_formality_from_metrics({})
        # Should return something reasonable with defaults
        assert isinstance(result, str)
        assert len(result) > 0


class TestGenerateStyleGuide:
    """Test the main generate_style_guide function."""

    @pytest.mark.asyncio
    async def test_empty_posts_returns_empty_guide(self):
        result = await generate_style_guide(
            subreddit="startups",
            top_posts=[],
            style_metrics=SAMPLE_METRICS,
            user_id="test-user",
            plan="trial",
            campaign_id="test-campaign",
        )
        assert result == EMPTY_STYLE_GUIDE

    @pytest.mark.asyncio
    @patch("app.analysis.style_guide_generator.InferenceClient")
    async def test_successful_generation(self, mock_client_class):
        """Test successful style guide generation with mocked LLM."""
        mock_instance = MagicMock()
        mock_instance.call = AsyncMock(return_value={
            "content": VALID_STYLE_GUIDE_JSON,
            "model_used": "anthropic/claude-3-haiku-20240307",
            "token_count": 4500,
            "cost_usd": 0.0023,
        })
        mock_client_class.return_value = mock_instance

        result = await generate_style_guide(
            subreddit="startups",
            top_posts=SAMPLE_POSTS,
            style_metrics=SAMPLE_METRICS,
            user_id="test-user",
            plan="trial",
            campaign_id="test-campaign",
        )

        assert result["voice_description"] != ""
        assert len(result["vocabulary_guide"]["use_these"]) > 0

        # Verify client was called with extract_patterns task
        mock_client_class.assert_called_once_with(task="extract_patterns")
        mock_instance.call.assert_called_once()

        # Verify system_prompt was passed
        call_kwargs = mock_instance.call.call_args
        assert "system_prompt" in call_kwargs.kwargs or len(call_kwargs.args) > 1

    @pytest.mark.asyncio
    @patch("app.analysis.style_guide_generator.InferenceClient")
    async def test_llm_failure_returns_empty_guide(self, mock_client_class):
        """Test graceful degradation on LLM failure."""
        mock_instance = MagicMock()
        mock_instance.call = AsyncMock(side_effect=Exception("API error"))
        mock_client_class.return_value = mock_instance

        result = await generate_style_guide(
            subreddit="startups",
            top_posts=SAMPLE_POSTS,
            style_metrics=SAMPLE_METRICS,
            user_id="test-user",
            plan="trial",
            campaign_id="test-campaign",
        )

        assert result == EMPTY_STYLE_GUIDE

    @pytest.mark.asyncio
    @patch("app.analysis.style_guide_generator.InferenceClient")
    async def test_malformed_llm_response(self, mock_client_class):
        """Test handling of invalid JSON from LLM."""
        mock_instance = MagicMock()
        mock_instance.call = AsyncMock(return_value={
            "content": "I apologize, but I cannot analyze these posts.",
            "model_used": "anthropic/claude-3-haiku-20240307",
            "token_count": 100,
            "cost_usd": 0.0001,
        })
        mock_client_class.return_value = mock_instance

        result = await generate_style_guide(
            subreddit="startups",
            top_posts=SAMPLE_POSTS,
            style_metrics=SAMPLE_METRICS,
            user_id="test-user",
            plan="trial",
            campaign_id="test-campaign",
        )

        # Should fall back to empty guide, not crash
        assert result == EMPTY_STYLE_GUIDE
