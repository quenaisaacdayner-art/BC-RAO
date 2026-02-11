"""
Forbidden pattern detection and categorization.

Detects promotional content, self-referential patterns, link spam,
low-effort posts, and other patterns that communities typically reject.
"""

import re

# Pattern categories with compiled regex patterns
PATTERN_CATEGORIES = {
    "Promotional": [
        re.compile(r'\baffiliate\s+link\b', re.IGNORECASE),
        re.compile(r'\bdiscount\s+code\b', re.IGNORECASE),
        re.compile(r'\bcoupon\b', re.IGNORECASE),
        re.compile(r'\bpromo\s+code\b', re.IGNORECASE),
        re.compile(r'\bcheck\s+out\s+my\b', re.IGNORECASE),
        re.compile(r'\bI\s+made\s+a\b', re.IGNORECASE),
        re.compile(r'\bspecial\s+offer\b', re.IGNORECASE),
        re.compile(r'\blimited\s+time\b', re.IGNORECASE),
        re.compile(r'\bfree\s+trial\b', re.IGNORECASE),
        re.compile(r'\bsign\s+up\s+(now|today)\b', re.IGNORECASE),
    ],
    "Self-referential": [
        re.compile(r'\bmy\s+product\b', re.IGNORECASE),
        re.compile(r'\bmy\s+tool\b', re.IGNORECASE),
        re.compile(r'\bI\s+built\b', re.IGNORECASE),
        re.compile(r'\bmy\s+startup\b', re.IGNORECASE),
        re.compile(r'\bmy\s+company\b', re.IGNORECASE),
        re.compile(r'\bmy\s+app\b', re.IGNORECASE),
        re.compile(r'\bmy\s+service\b', re.IGNORECASE),
        re.compile(r'\bour\s+platform\b', re.IGNORECASE),
        re.compile(r'\bmy\s+business\b', re.IGNORECASE),
    ],
    "Link patterns": [
        re.compile(r'bit\.ly/', re.IGNORECASE),
        re.compile(r'tinyurl\.com/', re.IGNORECASE),
        re.compile(r'goo\.gl/', re.IGNORECASE),
        re.compile(r'\?utm_', re.IGNORECASE),  # UTM parameters
        re.compile(r'\?ref=', re.IGNORECASE),  # Referral links
        re.compile(r'amazon\.com/.*?/ref=', re.IGNORECASE),  # Amazon affiliate
        re.compile(r'https?://\S+\s+https?://\S+', re.IGNORECASE),  # Multiple URLs
    ],
    "Low-effort": [
        re.compile(r'^.{0,49}$', re.MULTILINE),  # Very short posts (< 50 chars total)
        re.compile(r'\bthoughts\?$', re.IGNORECASE),
        re.compile(r'\bany\s+feedback\?$', re.IGNORECASE),
        re.compile(r'\bwhat\s+do\s+you\s+think\?$', re.IGNORECASE),
        re.compile(r'^(here|this|it)\s+(is|are)\s+', re.IGNORECASE),  # Generic intro
    ],
    "Spam indicators": [
        re.compile(r'[!]{3,}'),  # Excessive exclamation
        re.compile(r'[A-Z\s]{20,}'),  # ALL CAPS sections
        re.compile(r'(.{10,}?)\1{2,}'),  # Repetitive phrases (3+ times)
        re.compile(r'^.{500,}$(?!\n)', re.MULTILINE),  # Wall of text (500+ chars no paragraphs)
        re.compile(r'[\U0001F300-\U0001F9FF]{5,}'),  # Excessive emojis (5+)
    ],
    "Off-topic": [
        re.compile(r'\b(click\s+here|clickbait)\b', re.IGNORECASE),
        re.compile(r'\byou\s+won\'t\s+believe\b', re.IGNORECASE),
        re.compile(r'\bshocking\b', re.IGNORECASE),
    ],
}


def extract_forbidden_patterns(texts: list[str]) -> dict:
    """
    Scan texts for forbidden patterns and categorize them.

    Args:
        texts: List of post texts to analyze

    Returns:
        Dict with:
        - by_category: {category: count} - posts matching each category
        - detected_patterns: List of {category, pattern_description, match_count, severity}
    """
    if not texts:
        return {
            "by_category": {},
            "detected_patterns": [],
        }

    # Track matches per category
    category_matches = {category: 0 for category in PATTERN_CATEGORIES}
    pattern_details = []

    total_posts = len(texts)

    for category, patterns in PATTERN_CATEGORIES.items():
        matched_posts = set()

        for pattern in patterns:
            matches_in_posts = 0

            for i, text in enumerate(texts):
                if pattern.search(text):
                    matches_in_posts += 1
                    matched_posts.add(i)

            if matches_in_posts > 0:
                # Calculate severity based on percentage of posts
                percentage = (matches_in_posts / total_posts) * 100

                if percentage > 20:
                    severity = "high"
                elif percentage >= 10:
                    severity = "medium"
                else:
                    severity = "low"

                pattern_details.append({
                    "category": category,
                    "pattern_description": pattern.pattern[:50],  # First 50 chars of regex
                    "match_count": matches_in_posts,
                    "severity": severity,
                })

        category_matches[category] = len(matched_posts)

    # Sort pattern details by match count (descending)
    pattern_details.sort(key=lambda x: x["match_count"], reverse=True)

    return {
        "by_category": category_matches,
        "detected_patterns": pattern_details,
    }


def check_post_penalties(text: str) -> list[dict]:
    """
    Check single post for penalty-triggering patterns.

    Args:
        text: Post text to check

    Returns:
        List of {phrase, severity, category} dicts for inline highlighting
    """
    if not text:
        return []

    penalties = []
    seen_phrases = set()

    for category, patterns in PATTERN_CATEGORIES.items():
        for pattern in patterns:
            for match in pattern.finditer(text):
                # Extract actual matched text (not the regex pattern)
                phrase = match.group(0)

                # Avoid duplicates
                if phrase.lower() not in seen_phrases:
                    seen_phrases.add(phrase.lower())

                    # Assign severity based on category
                    if category in ["Promotional", "Spam indicators"]:
                        severity = "high"
                    elif category in ["Self-referential", "Link patterns"]:
                        severity = "medium"
                    else:
                        severity = "low"

                    penalties.append({
                        "phrase": phrase,
                        "severity": severity,
                        "category": category,
                    })

    return penalties
