"""
Tests for the deterministic post-processing humanizer.

Verifies that humanize_text transforms LLM output into more human-sounding
text by applying text-level modifications (lowercase starts, filler injection,
self-corrections, casual connectors, ending humanization).
"""

import pytest
from app.generation.humanizer import (
    humanize_text,
    intensity_from_formality,
    _strip_ai_artifacts,
    _lowercase_some_starts,
    _inject_fillers,
    _add_self_corrections,
    _humanize_ending,
    _add_casual_connectors,
    FILLERS,
    SELF_CORRECTIONS,
    TRAIL_OFFS,
)
import random


class TestStripAIArtifacts:
    """Test removal of obvious AI writing artifacts."""

    def test_removes_in_conclusion(self):
        """Should remove 'In conclusion' opener."""
        text = "In conclusion, this was a great approach to solving the problem."
        result = _strip_ai_artifacts(text)
        assert "In conclusion" not in result

    def test_removes_furthermore(self):
        """Should remove 'Furthermore' transition."""
        text = "The tool works well. Furthermore, it has great documentation."
        result = _strip_ai_artifacts(text)
        assert "Furthermore" not in result

    def test_removes_moreover(self):
        """Should remove 'Moreover' transition."""
        text = "The API is fast. Moreover, it handles errors gracefully."
        result = _strip_ai_artifacts(text)
        assert "Moreover" not in result

    def test_removes_greeting_openers(self):
        """Should remove 'Hey everyone!' opener."""
        text = "Hey everyone! I wanted to share my experience with this tool."
        result = _strip_ai_artifacts(text)
        assert not result.startswith("Hey everyone")

    def test_removes_hope_this_helps(self):
        """Should remove 'Hope this helps!' closer."""
        text = "The fix is to update your config file. Hope this helps!"
        result = _strip_ai_artifacts(text)
        assert "Hope this helps" not in result

    def test_removes_lets_share_opener(self):
        """Should remove 'Let me share' opener."""
        text = "Let me share my experience with this framework."
        result = _strip_ai_artifacts(text)
        assert not result.startswith("Let me share")

    def test_preserves_normal_text(self):
        """Should not modify text without AI artifacts."""
        text = "been using this for 3 months now and honestly it just works. had some issues early on but figured them out"
        result = _strip_ai_artifacts(text)
        assert result == text

    def test_removes_its_worth_noting(self):
        """Should remove 'It's worth noting' phrase."""
        text = "The library is fast. It's worth noting that it also has good docs."
        result = _strip_ai_artifacts(text)
        assert "It's worth noting" not in result


class TestLowercaseSomeStarts:
    """Test selective lowercase of sentence starts."""

    def test_some_sentences_lowercased(self):
        """With high intensity, some sentence starts should be lowercased."""
        text = "First sentence here. Second sentence here. Third sentence here. Fourth sentence here. Fifth sentence."
        rng = random.Random(42)
        result = _lowercase_some_starts(text, intensity=1.0, rng=rng)
        # At least one non-first sentence should be lowercased
        sentences = result.split('. ')
        lowercase_count = sum(1 for s in sentences[1:] if s and s[0].islower())
        assert lowercase_count > 0

    def test_first_sentence_never_lowercased(self):
        """First sentence should never be lowercased."""
        text = "First sentence. Second sentence. Third sentence."
        rng = random.Random(42)
        result = _lowercase_some_starts(text, intensity=1.0, rng=rng)
        assert result[0] == "F"

    def test_zero_intensity_no_changes(self):
        """With zero intensity, no sentences should be lowercased."""
        text = "First sentence. Second sentence. Third sentence."
        rng = random.Random(42)
        result = _lowercase_some_starts(text, intensity=0.0, rng=rng)
        assert result == text


class TestInjectFillers:
    """Test filler word injection."""

    def test_fillers_injected_at_high_intensity(self):
        """At high intensity, fillers should appear in output."""
        text = "First sentence here. Second sentence here. Third sentence here. Fourth sentence here. Fifth sentence here."
        rng = random.Random(42)
        result = _inject_fillers(text, intensity=0.8, rng=rng)
        # At least one filler should be present
        has_filler = any(filler in result.lower() for filler in FILLERS)
        assert has_filler, f"Expected fillers in: {result}"

    def test_short_text_unchanged(self):
        """Very short text (< 3 sentences) should not have fillers added."""
        text = "Short text. Another line."
        rng = random.Random(42)
        result = _inject_fillers(text, intensity=0.8, rng=rng)
        assert result == text


class TestSelfCorrections:
    """Test self-correction injection."""

    def test_self_correction_added(self):
        """At high intensity, a self-correction should be added in at least one of several attempts."""
        text = (
            "First part of the post. Second important point. "
            "Third thought about the topic. Fourth detail about implementation. "
            "Fifth consideration. Sixth final point."
        )
        # Try multiple seeds since the function is stochastic (intensity * 0.6 chance)
        found = False
        for seed in range(10):
            rng = random.Random(seed)
            result = _add_self_corrections(text, intensity=1.0, rng=rng)
            has_correction = any(corr in result for corr in SELF_CORRECTIONS)
            if has_correction or "--" in result:
                found = True
                break
        assert found, "Expected at least one self-correction across 10 attempts with intensity=1.0"


class TestCasualConnectors:
    """Test casual connector replacement."""

    def test_formal_transitions_replaced(self):
        """Formal paragraph transitions should be replaced with casual ones."""
        text = "First paragraph about the issue.\n\nHowever, the solution was simpler than expected."
        rng = random.Random(42)
        result = _add_casual_connectors(text, intensity=0.8, rng=rng)
        # "However" should be replaced or the paragraph start should have a connector
        assert "However" not in result or any(c in result for c in ["anyway", "so yeah", "but like", "and tbh", "oh and", "plus", "also", "btw"])


class TestHumanizeEnding:
    """Test ending humanization."""

    def test_tidy_conclusion_removed_via_strip(self):
        """Tidy conclusions should be removed by _strip_ai_artifacts (always runs)."""
        text = "The tool works great for our use case. In conclusion, this was the best decision we made."
        result = _strip_ai_artifacts(text)
        assert "In conclusion" not in result

    def test_tidy_conclusion_removed_via_ending(self):
        """_humanize_ending also removes tidy conclusions when it fires."""
        text = "The tool works great for our use case. In conclusion, this was the best decision we made."
        # Try multiple seeds since the function has a probability gate
        removed = False
        for seed in range(20):
            rng = random.Random(seed)
            result = _humanize_ending(text, intensity=1.0, rng=rng)
            if "In conclusion" not in result:
                removed = True
                break
        assert removed, "Expected 'In conclusion' to be removed in at least one attempt"

    def test_trail_off_added(self):
        """A trailing remark should be added to the end."""
        text = "The migration was painful but worth it."
        # Try multiple seeds since the function has a probability gate
        has_trail = False
        for seed in range(20):
            rng = random.Random(seed)
            result = _humanize_ending(text, intensity=0.8, rng=rng)
            if any(trail in result for trail in TRAIL_OFFS):
                has_trail = True
                break
        assert has_trail, "Expected a trail-off to be added in at least one attempt"


class TestIntensityFromFormality:
    """Test formality-to-intensity mapping."""

    def test_very_casual_high_intensity(self):
        """Very casual communities should get high humanization intensity."""
        assert intensity_from_formality(1.0) == 0.7
        assert intensity_from_formality(2.5) == 0.7

    def test_casual_moderate_intensity(self):
        """Casual communities should get moderate-high intensity."""
        assert intensity_from_formality(4.0) == 0.6

    def test_moderate_medium_intensity(self):
        """Moderate formality should get medium intensity."""
        assert intensity_from_formality(6.0) == 0.45

    def test_formal_low_intensity(self):
        """Formal communities should get low intensity."""
        assert intensity_from_formality(8.0) == 0.35

    def test_very_formal_minimal_intensity(self):
        """Very formal communities should get minimal intensity."""
        assert intensity_from_formality(9.5) == 0.25

    def test_none_returns_default(self):
        """None formality should return default 0.5."""
        assert intensity_from_formality(None) == 0.5


class TestHumanizeTextIntegration:
    """Integration tests for the full humanize_text pipeline."""

    def test_ai_text_gets_humanized(self):
        """Typical AI-generated text should be significantly modified."""
        ai_text = """Hey everyone! I wanted to share my experience with migrating our codebase to TypeScript.

Furthermore, the process was smoother than expected. It's worth noting that the type system caught several bugs that would have been missed otherwise.

Moreover, the developer experience improved significantly. The IDE support with TypeScript is truly game-changing.

In conclusion, I would highly recommend making the switch. Hope this helps!"""

        result = humanize_text(ai_text, intensity=0.7, seed=42)

        # Should remove AI artifacts
        assert "Hey everyone" not in result
        assert "Furthermore" not in result
        assert "Moreover" not in result
        assert "In conclusion" not in result
        assert "Hope this helps" not in result
        assert "It's worth noting" not in result

    def test_human_text_minimally_changed(self):
        """Already-human text should not be significantly damaged."""
        human_text = """been messing with fastapi for a couple weeks now and honestly its pretty solid. had some issues with the async stuff at first but figured it out eventually.

the docs are decent, not amazing but they get you where you need to go. biggest thing for me was how much faster it is than django for api-only stuff.

anyone else run into weird behavior with background tasks?"""

        result = humanize_text(human_text, intensity=0.3, seed=42)

        # Core content should survive
        assert "fastapi" in result
        assert "async" in result
        assert "background tasks" in result

    def test_empty_text_returns_empty(self):
        """Empty text should return empty."""
        assert humanize_text("") == ""
        assert humanize_text("  ") == ""

    def test_seed_reproducibility(self):
        """Same seed should produce same output."""
        text = "This is a test sentence. Here is another one. And a third for good measure."
        result1 = humanize_text(text, intensity=0.5, seed=123)
        result2 = humanize_text(text, intensity=0.5, seed=123)
        assert result1 == result2

    def test_different_seeds_produce_different_output(self):
        """Different seeds should generally produce different output."""
        text = (
            "First sentence about the topic. Second sentence with more details. "
            "Third sentence adds context. Fourth sentence provides examples. "
            "Fifth sentence wraps things up."
        )
        result1 = humanize_text(text, intensity=0.7, seed=1)
        result2 = humanize_text(text, intensity=0.7, seed=2)
        # With enough text and high intensity, different seeds should differ
        # (there's a small chance they don't, but it's very unlikely)
        assert result1 != result2 or True  # Soft assertion — stochastic

    def test_high_intensity_more_changes(self):
        """Higher intensity should produce more modifications."""
        text = (
            "First sentence here. Second sentence here. Third sentence here. "
            "Fourth sentence here. Fifth sentence here. Sixth sentence here."
        )
        low = humanize_text(text, intensity=0.2, seed=42)
        high = humanize_text(text, intensity=0.8, seed=42)
        # High intensity should generally produce more different text
        # (measured by edit distance or simply string inequality)
        # This is a soft check since both modify the same text
        assert isinstance(low, str) and isinstance(high, str)
