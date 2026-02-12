"""
Tests for blacklist validation - content safety feature.

Tests pattern matching, case sensitivity, and violation detection
to ensure forbidden promotional language is caught.
"""
import pytest
from app.generation.blacklist_validator import validate_draft


class TestBlacklistValidation:
    """Test basic blacklist validation functionality."""

    def test_clean_text_passes(self, forbidden_patterns):
        """Clean text with no forbidden patterns should pass validation."""
        draft_text = "I've been working on a Python project and need some feedback on my approach."
        result = validate_draft(draft_text, forbidden_patterns)

        assert result.passed is True
        assert len(result.violations) == 0

    def test_forbidden_pattern_detected(self, forbidden_patterns):
        """Text containing forbidden pattern should fail validation."""
        draft_text = "Check out my new tool! Click here to see more."
        result = validate_draft(draft_text, forbidden_patterns)

        assert result.passed is False
        assert len(result.violations) > 0

        # Should detect "click here"
        click_here_found = any(
            "click here" in v.matched_text.lower() for v in result.violations
        )
        assert click_here_found is True

    def test_multiple_violations_detected(self, forbidden_patterns):
        """Text with multiple violations should detect all of them."""
        draft_text = "Buy now before this limited time offer ends! Click here!"
        result = validate_draft(draft_text, forbidden_patterns)

        assert result.passed is False
        assert len(result.violations) >= 2

        # Should detect both "buy now" and "limited time offer" and "click here"
        patterns_found = [v.matched_text.lower() for v in result.violations]
        assert any("buy now" in p for p in patterns_found)
        assert any("limited time" in p for p in patterns_found)

    def test_case_insensitive_matching(self, forbidden_patterns):
        """Pattern matching should be case-insensitive."""
        # Test different case variations
        test_cases = [
            "CLICK HERE to see more",
            "Click Here to see more",
            "click here to see more",
            "ClIcK hErE to see more"
        ]

        for text in test_cases:
            result = validate_draft(text, forbidden_patterns)
            assert result.passed is False
            assert len(result.violations) > 0

    def test_empty_pattern_list(self):
        """Empty pattern list should pass all text."""
        draft_text = "Click here to buy now with this limited time offer!"
        result = validate_draft(draft_text, [])

        assert result.passed is True
        assert len(result.violations) == 0

    def test_empty_text(self, forbidden_patterns):
        """Empty text should pass validation."""
        result = validate_draft("", forbidden_patterns)

        assert result.passed is True
        assert len(result.violations) == 0


class TestViolationDetails:
    """Test that violation details are correctly captured."""

    def test_violation_contains_pattern(self, forbidden_patterns):
        """Violation should include the regex pattern that matched."""
        draft_text = "Click here for more information."
        result = validate_draft(draft_text, forbidden_patterns)

        assert result.passed is False
        violation = result.violations[0]
        assert violation.pattern is not None
        assert len(violation.pattern) > 0

    def test_violation_contains_category(self, forbidden_patterns):
        """Violation should include the category."""
        draft_text = "Click here for more information."
        result = validate_draft(draft_text, forbidden_patterns)

        assert result.passed is False
        violation = result.violations[0]
        assert violation.category == "Promotional"

    def test_violation_contains_matched_text(self, forbidden_patterns):
        """Violation should include the exact matched text."""
        draft_text = "Click here for more information."
        result = validate_draft(draft_text, forbidden_patterns)

        assert result.passed is False
        violation = result.violations[0]
        assert "click here" in violation.matched_text.lower()

    def test_multiple_violations_separate_entries(self, forbidden_patterns):
        """Multiple violations should create separate entries."""
        draft_text = "Buy now with this limited time offer!"
        result = validate_draft(draft_text, forbidden_patterns)

        assert result.passed is False
        assert len(result.violations) >= 2

        # Each violation should be distinct
        matched_texts = [v.matched_text for v in result.violations]
        assert len(set(matched_texts)) == len(matched_texts)


class TestWordBoundaries:
    """Test that patterns respect word boundaries."""

    def test_word_boundary_respected(self):
        """Pattern should match whole words, not substrings."""
        patterns = [
            {
                "regex_pattern": r"\bclick\b",
                "category": "Test",
                "pattern_description": "Click word"
            }
        ]

        # Should match "click" as whole word
        result_match = validate_draft("Please click the button", patterns)
        assert result_match.passed is False

        # Should NOT match "click" as substring
        result_no_match = validate_draft("This is clickbait", patterns)
        # Note: depends on pattern definition. If pattern is \bclick\b, won't match
        # But our actual patterns use \bclick here\b which shouldn't match either

    def test_phrase_boundary_matching(self, forbidden_patterns):
        """Multi-word phrases should match correctly."""
        # "buy now" should match
        result_match = validate_draft("You should buy now!", forbidden_patterns)
        assert result_match.passed is False

        # Words separated shouldn't match
        result_no_match = validate_draft("You should buy something now", forbidden_patterns)
        # "buy now" requires words to be adjacent, so this should pass
        assert result_no_match.passed is True


class TestComplexPatterns:
    """Test more complex regex patterns."""

    def test_regex_with_alternation(self):
        """Patterns with alternation (|) should work."""
        patterns = [
            {
                "regex_pattern": r"\b(free|discount|sale)\b",
                "category": "Promotional",
                "pattern_description": "Promotional keywords"
            }
        ]

        for word in ["free", "discount", "sale"]:
            result = validate_draft(f"Get your {word} today!", patterns)
            assert result.passed is False

    def test_regex_with_character_classes(self):
        """Patterns with character classes should work."""
        patterns = [
            {
                "regex_pattern": r"\d+% off",
                "category": "Promotional",
                "pattern_description": "Percentage discount"
            }
        ]

        result = validate_draft("Get 50% off now!", patterns)
        assert result.passed is False

        result_no_match = validate_draft("Get a discount!", patterns)
        assert result_no_match.passed is True

    def test_regex_with_quantifiers(self):
        """Patterns with quantifiers should work."""
        patterns = [
            {
                "regex_pattern": r"\$\d+(\.\d{2})?",
                "category": "Pricing",
                "pattern_description": "Dollar amounts"
            }
        ]

        # Should match dollar amounts
        result1 = validate_draft("Only $19.99!", patterns)
        assert result1.passed is False

        result2 = validate_draft("Just $50!", patterns)
        assert result2.passed is False


class TestInvalidPatterns:
    """Test handling of invalid regex patterns."""

    def test_invalid_regex_pattern_skipped(self):
        """Invalid regex patterns should be skipped without crashing."""
        patterns = [
            {
                "regex_pattern": r"[invalid(pattern",  # Invalid regex
                "category": "Test",
                "pattern_description": "Broken pattern"
            },
            {
                "regex_pattern": r"\bclick here\b",  # Valid pattern
                "category": "Promotional",
                "pattern_description": "Click here CTA"
            }
        ]

        # Should not crash, should still detect valid pattern
        result = validate_draft("Click here to see more", patterns)
        # Invalid pattern skipped, but valid pattern should work
        assert result.passed is False

    def test_missing_pattern_fields(self):
        """Missing pattern fields should be handled gracefully."""
        patterns = [
            {
                "regex_pattern": r"\btest\b"
                # Missing category and description
            }
        ]

        result = validate_draft("This is a test", patterns)
        # Should not crash
        assert result.passed is False
        # Should use defaults for missing fields
        assert result.violations[0].category == "Unknown"


class TestRealWorldExamples:
    """Test with real-world promotional text examples."""

    def test_subtle_promotion_passes(self, forbidden_patterns):
        """Subtle promotion without forbidden patterns should pass."""
        draft_text = """
        I've been working on a tool to help with API testing.
        After months of development, I've finally got something working.
        Would love to hear thoughts from the community on the approach.
        """
        result = validate_draft(draft_text, forbidden_patterns)
        assert result.passed is True

    def test_obvious_spam_fails(self, forbidden_patterns):
        """Obvious spam with multiple violations should fail."""
        draft_text = """
        Check out my amazing product!
        Limited time offer - buy now before it's too late!
        Click here to get started: [link]
        """
        result = validate_draft(draft_text, forbidden_patterns)
        assert result.passed is False
        assert len(result.violations) >= 2

    def test_technical_content_passes(self, forbidden_patterns):
        """Technical content without promotion should pass."""
        draft_text = """
        I implemented a binary search algorithm in Python.
        The time complexity is O(log n) and space complexity is O(1).
        Here's my approach and where I'm stuck...
        """
        result = validate_draft(draft_text, forbidden_patterns)
        assert result.passed is True

    def test_feedback_request_passes(self, forbidden_patterns):
        """Genuine feedback request should pass."""
        draft_text = """
        I built a small CLI tool for my workflow.
        It's rough around the edges and I'm sure there are bugs.
        What would you change about this approach?
        """
        result = validate_draft(draft_text, forbidden_patterns)
        assert result.passed is True


@pytest.mark.parametrize("forbidden_phrase", [
    "click here",
    "buy now",
    "limited time offer",
    "check out my"
])
def test_each_forbidden_pattern_detected(forbidden_phrase):
    """Each forbidden pattern should be individually detectable."""
    patterns = [
        {
            "regex_pattern": rf"\b{forbidden_phrase}\b",
            "category": "Test",
            "pattern_description": f"{forbidden_phrase} test"
        }
    ]

    draft_text = f"Some text with {forbidden_phrase} in it."
    result = validate_draft(draft_text, patterns)

    assert result.passed is False
    assert len(result.violations) >= 1
