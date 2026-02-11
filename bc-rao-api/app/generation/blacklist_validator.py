"""
Post-generation blacklist validation.

Validates generated drafts against regex forbidden patterns from the database.
Provides utilities for link density, sentence length, and jargon checking.
"""

import re
from typing import List, Dict
from app.models.draft import BlacklistCheckResult, BlacklistViolation


def validate_draft(draft_text: str, forbidden_patterns: List[Dict]) -> BlacklistCheckResult:
    """
    Validate draft text against forbidden regex patterns.

    Args:
        draft_text: Generated draft body text
        forbidden_patterns: List of pattern dicts with keys:
            - regex_pattern (str): Regex pattern to match
            - category (str): Pattern category (e.g., "Promotional", "Spam")
            - pattern_description (str): Human-readable description

    Returns:
        BlacklistCheckResult with passed=True if zero violations, else passed=False with details

    Examples:
        >>> patterns = [{"regex_pattern": r"\bclick here\b", "category": "Promotional", "pattern_description": "Click here CTA"}]
        >>> validate_draft("Check out my site!", patterns)
        BlacklistCheckResult(passed=True, violations=[])

        >>> validate_draft("Click here to see more!", patterns)
        BlacklistCheckResult(passed=False, violations=[...])
    """
    violations = []

    for pattern_entry in forbidden_patterns:
        try:
            regex_pattern = pattern_entry.get("regex_pattern", "")
            category = pattern_entry.get("category", "Unknown")
            description = pattern_entry.get("pattern_description", "Unknown pattern")

            # Compile pattern with case-insensitive flag
            compiled_pattern = re.compile(regex_pattern, re.IGNORECASE)

            # Find all matches
            matches = compiled_pattern.finditer(draft_text)

            for match in matches:
                matched_text = match.group(0)
                violations.append(
                    BlacklistViolation(
                        pattern=regex_pattern,
                        category=category,
                        matched_text=matched_text
                    )
                )

        except re.error:
            # Invalid regex pattern - skip but don't fail validation
            continue

    return BlacklistCheckResult(
        passed=len(violations) == 0,
        violations=violations
    )


def calculate_link_density(text: str) -> float:
    """
    Calculate link density as URLs per paragraph.

    Args:
        text: Post text

    Returns:
        Average number of URLs per paragraph (0.0 to N)

    Examples:
        >>> calculate_link_density("Paragraph 1.\\n\\nParagraph 2 https://example.com")
        0.5
    """
    # Split by double newlines to get paragraphs
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    if not paragraphs:
        return 0.0

    # Count URLs using regex
    url_pattern = re.compile(
        r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    )

    total_urls = len(url_pattern.findall(text))

    return total_urls / len(paragraphs)


def check_sentence_length(text: str, max_avg: float = 25.0) -> bool:
    """
    Check if average sentence length is within community norm.

    Args:
        text: Post text
        max_avg: Maximum acceptable average sentence length (default: 25 words)

    Returns:
        True if within norm, False if exceeds max_avg

    Examples:
        >>> check_sentence_length("Short sentence. Another one.", max_avg=25.0)
        True

        >>> long_text = "This is a very long sentence with many words that exceeds the typical community norm."
        >>> check_sentence_length(long_text, max_avg=5.0)
        False
    """
    # Split into sentences using period, question mark, exclamation
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]

    if not sentences:
        return True

    # Count words per sentence
    word_counts = [len(s.split()) for s in sentences]

    # Calculate average
    avg_length = sum(word_counts) / len(word_counts)

    return avg_length <= max_avg


def scan_jargon(text: str, jargon_list: List[str]) -> List[str]:
    """
    Scan text for marketing jargon terms.

    Args:
        text: Post text
        jargon_list: List of jargon terms to detect (case-insensitive)

    Returns:
        List of jargon terms found in text

    Examples:
        >>> scan_jargon("Our revolutionary solution disrupts the market", ["revolutionary", "disrupt", "synergy"])
        ["revolutionary", "disrupt"]
    """
    found_jargon = []

    text_lower = text.lower()

    for jargon_term in jargon_list:
        # Use word boundaries to avoid false positives
        pattern = r'\b' + re.escape(jargon_term.lower()) + r'\b'

        if re.search(pattern, text_lower):
            found_jargon.append(jargon_term)

    return found_jargon
