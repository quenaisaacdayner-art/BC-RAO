"""
Post success scoring and ISC (Intrinsic Sensitivity Coefficient) calculator.

Calculates how well a post matches community behavioral patterns and
quantifies community sensitivity to marketing content.
"""

import re
from typing import Optional

# Compiled regex patterns for vulnerability detection
VULNERABILITY_PATTERNS = [
    re.compile(r'\b(I|my|me|we|our|us)\b', re.IGNORECASE),  # Personal pronouns
    re.compile(r'[?]'),  # Questions (engagement signal)
    re.compile(r'\b(struggled|frustrated|confused|worried|concerned)\b', re.IGNORECASE),  # Emotional markers
    re.compile(r'\b(story|journey|experience|learned|realized)\b', re.IGNORECASE),  # Storytelling signals
]

# Compiled patterns for marketing jargon
JARGON_PATTERNS = [
    re.compile(r'\bsynerg\w*\b', re.IGNORECASE),
    re.compile(r'\bleverage\b', re.IGNORECASE),
    re.compile(r'\bparadigm\b', re.IGNORECASE),
    re.compile(r'\bdisrupt\w*\b', re.IGNORECASE),
    re.compile(r'\binnovate\w*\b', re.IGNORECASE),
    re.compile(r'\bgame-changer\b', re.IGNORECASE),
    re.compile(r'\bthought leader\b', re.IGNORECASE),
    re.compile(r'\bbest-in-class\b', re.IGNORECASE),
    re.compile(r'\breach out\b', re.IGNORECASE),
    re.compile(r'\bcircle back\b', re.IGNORECASE),
    re.compile(r'\btouch base\b', re.IGNORECASE),
    re.compile(r'\brevolutionary\b', re.IGNORECASE),
    re.compile(r'\bcutting-edge\b', re.IGNORECASE),
    re.compile(r'\bscalable\b', re.IGNORECASE),
    re.compile(r'\bROI\b'),
    re.compile(r'\bgrowth hack\w*\b', re.IGNORECASE),
]

# URL detection pattern
URL_PATTERN = re.compile(r'https?://\S+|www\.\S+', re.IGNORECASE)


def calculate_vulnerability_weight(text: str) -> float:
    """
    Calculate vulnerability/authenticity score based on personal language.

    Higher score = more vulnerable/authentic (uses "I", emotions, questions, storytelling).

    Args:
        text: Post text to analyze

    Returns:
        Score from 0-10 (10 = highly vulnerable/authentic)
    """
    if not text:
        return 0.0

    matches = 0
    for pattern in VULNERABILITY_PATTERNS:
        matches += len(pattern.findall(text))

    # Scale: 0 matches = 0, 1-3 = 3, 4-6 = 5, 7-10 = 7, 10+ = 9-10
    if matches == 0:
        score = 0.0
    elif matches <= 3:
        score = 3.0
    elif matches <= 6:
        score = 5.0
    elif matches <= 10:
        score = 7.0
    else:
        score = min(10.0, 7.0 + (matches - 10) * 0.3)

    return round(score, 2)


def calculate_rhythm_adherence(
    post_avg_length: Optional[float],
    post_length_std: Optional[float],
    community_avg_length: Optional[float],
    community_length_std: Optional[float] = None,
) -> float:
    """
    Calculate how closely post's rhythm matches community patterns.

    Args:
        post_avg_length: Average sentence length in post
        post_length_std: Standard deviation of sentence lengths in post
        community_avg_length: Community's average sentence length
        community_length_std: Community's sentence length std dev (optional)

    Returns:
        Score from 0-10 (10 = perfect rhythm match)
    """
    if post_avg_length is None or community_avg_length is None:
        return 5.0  # Neutral score if data missing

    # Primary factor: difference in average sentence length
    avg_diff = abs(post_avg_length - community_avg_length)
    score = max(0.0, 10.0 - avg_diff)

    # Secondary factor: std dev similarity (if available)
    if post_length_std is not None and community_length_std is not None:
        std_diff = abs(post_length_std - community_length_std)
        std_penalty = min(2.0, std_diff * 0.5)
        score -= std_penalty

    return max(0.0, min(10.0, round(score, 2)))


def calculate_formality_match(
    post_formality: Optional[float],
    community_formality: Optional[float],
) -> float:
    """
    Calculate how closely post's formality matches community.

    Args:
        post_formality: Post's formality score
        community_formality: Community's average formality

    Returns:
        Score from 0-10 (10 = perfect formality match)
    """
    if post_formality is None or community_formality is None:
        return 5.0  # Neutral score if data missing

    diff = abs(post_formality - community_formality)
    score = max(0.0, 10.0 - (diff * 2.0))

    return round(score, 2)


def calculate_marketing_jargon_penalty(text: str) -> tuple[float, list[dict]]:
    """
    Detect marketing jargon and calculate penalty.

    Args:
        text: Post text to analyze

    Returns:
        Tuple of (penalty_score, penalty_phrases)
        - penalty_score: 0-10 (higher = worse, more jargon)
        - penalty_phrases: List of {phrase, severity, category} dicts
    """
    if not text:
        return 0.0, []

    matches = []
    seen_phrases = set()

    for pattern in JARGON_PATTERNS:
        for match in pattern.finditer(text):
            phrase = match.group(0)
            if phrase.lower() not in seen_phrases:
                seen_phrases.add(phrase.lower())
                matches.append(phrase)

    num_matches = len(matches)

    # Calculate penalty: 0 = none, 1 = 3, 2 = 5, 3 = 8, 4+ = 9-10
    if num_matches == 0:
        penalty = 0.0
        severity = "none"
    elif num_matches == 1:
        penalty = 3.0
        severity = "low"
    elif num_matches == 2:
        penalty = 5.0
        severity = "medium"
    elif num_matches == 3:
        penalty = 8.0
        severity = "high"
    else:
        penalty = min(10.0, 8.0 + (num_matches - 3) * 0.5)
        severity = "high"

    penalty_phrases = [
        {"phrase": phrase, "severity": severity, "category": "Promotional"}
        for phrase in matches
    ]

    return round(penalty, 2), penalty_phrases


def calculate_link_density_penalty(text: str) -> tuple[float, list[dict]]:
    """
    Calculate penalty based on link density.

    Args:
        text: Post text to analyze

    Returns:
        Tuple of (penalty_score, penalty_phrases)
        - penalty_score: 0-10 (higher = worse, more links)
        - penalty_phrases: List of {phrase, severity, category} dicts
    """
    if not text:
        return 0.0, []

    links = URL_PATTERN.findall(text)
    num_links = len(links)

    # Calculate penalty: 0 links = 0, 1 = 3, 2 = 6, 3+ = 9
    if num_links == 0:
        penalty = 0.0
        severity = "none"
    elif num_links == 1:
        penalty = 3.0
        severity = "low"
    elif num_links == 2:
        penalty = 6.0
        severity = "medium"
    else:
        penalty = 9.0
        severity = "high"

    penalty_phrases = [
        {"phrase": link, "severity": severity, "category": "Link patterns"}
        for link in links
    ]

    return round(penalty, 2), penalty_phrases


def calculate_post_score(post_data: dict, community_avg: dict) -> dict:
    """
    Calculate comprehensive post success score.

    Args:
        post_data: Post's NLP results + engagement data
            Required keys: raw_text
            Optional: formality_score, avg_sentence_length, sentence_length_std
        community_avg: Community average profile
            Optional: avg_sentence_length, sentence_length_std, formality_level

    Returns:
        Dict with:
        - vulnerability_weight (0-10)
        - rhythm_adherence (0-10)
        - formality_match (0-10)
        - marketing_jargon_penalty (0-10, higher = worse)
        - link_density_penalty (0-10, higher = worse)
        - total_score (0-10)
        - penalty_phrases (list of dicts)
    """
    text = post_data.get("raw_text", "")

    # Calculate positive factors
    vulnerability = calculate_vulnerability_weight(text)
    rhythm = calculate_rhythm_adherence(
        post_data.get("avg_sentence_length"),
        post_data.get("sentence_length_std"),
        community_avg.get("avg_sentence_length"),
        community_avg.get("sentence_length_std"),
    )
    formality = calculate_formality_match(
        post_data.get("formality_score"),
        community_avg.get("formality_level"),
    )

    # Calculate penalties
    jargon_penalty, jargon_phrases = calculate_marketing_jargon_penalty(text)
    link_penalty, link_phrases = calculate_link_density_penalty(text)

    # Combined penalty phrases
    penalty_phrases = jargon_phrases + link_phrases

    # Total score formula
    total = (
        vulnerability * 0.25
        + rhythm * 0.25
        + formality * 0.2
        - jargon_penalty * 0.15
        - link_penalty * 0.15
    )

    # Clamp to 0-10
    total = max(0.0, min(10.0, total))

    return {
        "vulnerability_weight": vulnerability,
        "rhythm_adherence": rhythm,
        "formality_match": formality,
        "marketing_jargon_penalty": jargon_penalty,
        "link_density_penalty": link_penalty,
        "total_score": round(total, 2),
        "penalty_phrases": penalty_phrases,
    }


def calculate_isc_score(posts_data: list[dict]) -> float:
    """
    Calculate ISC (Intrinsic Sensitivity Coefficient) for a community.

    Measures how sensitive a community is to marketing content on a scale of 1.0-10.0.
    Higher score = more sensitive to promotional/jargon/link content.

    Args:
        posts_data: List of post dicts with NLP + engagement data
            Each dict should have: raw_text, formality_score, avg_sentence_length,
            vulnerability_weight (calculated), total_score (calculated)

    Returns:
        ISC score (1.0 to 10.0)

    Raises:
        ValueError: If less than 10 posts (insufficient data)
    """
    if len(posts_data) < 10:
        raise ValueError(f"Insufficient data: need at least 10 posts, got {len(posts_data)}")

    # Sort posts by total_score
    sorted_posts = sorted(posts_data, key=lambda p: p.get("total_score", 0), reverse=True)

    # Split into top 25% and bottom 25%
    top_quartile_size = max(1, len(sorted_posts) // 4)
    top_posts = sorted_posts[:top_quartile_size]
    bottom_posts = sorted_posts[-top_quartile_size:]

    # Factor 1: Jargon sensitivity (0-10)
    top_jargon = sum(1 for p in top_posts if calculate_marketing_jargon_penalty(p.get("raw_text", ""))[0] > 0)
    bottom_jargon = sum(1 for p in bottom_posts if calculate_marketing_jargon_penalty(p.get("raw_text", ""))[0] > 0)

    if bottom_jargon > 0:
        jargon_ratio = top_jargon / bottom_jargon
        jargon_sensitivity = max(0.0, min(10.0, 10.0 - (jargon_ratio * 5.0)))
    else:
        jargon_sensitivity = 5.0  # Default if no jargon in bottom quartile

    # Factor 2: Link sensitivity (0-10)
    top_links = sum(1 for p in top_posts if calculate_link_density_penalty(p.get("raw_text", ""))[0] > 0)
    bottom_links = sum(1 for p in bottom_posts if calculate_link_density_penalty(p.get("raw_text", ""))[0] > 0)

    if bottom_links > 0:
        link_ratio = top_links / bottom_links
        link_sensitivity = max(0.0, min(10.0, 10.0 - (link_ratio * 5.0)))
    else:
        link_sensitivity = 5.0  # Default if no links in bottom quartile

    # Factor 3: Vulnerability preference (0-10)
    top_vulnerability = sum(p.get("vulnerability_weight", 0) for p in top_posts) / len(top_posts)
    bottom_vulnerability = sum(p.get("vulnerability_weight", 0) for p in bottom_posts) / len(bottom_posts)

    vulnerability_diff = top_vulnerability - bottom_vulnerability
    vulnerability_preference = max(0.0, min(10.0, 5.0 + vulnerability_diff))

    # Factor 4: Depth correlation (0-10)
    # Check if higher comment count correlates with authenticity
    posts_with_comments = [p for p in posts_data if p.get("comment_count", 0) > 0]

    if len(posts_with_comments) >= 5:
        # Sort by comment count
        by_comments = sorted(posts_with_comments, key=lambda p: p.get("comment_count", 0), reverse=True)
        top_discussed = by_comments[:len(by_comments) // 4] if len(by_comments) >= 4 else by_comments[:2]

        # Calculate average authenticity (formality_match + vulnerability) of top-discussed
        authenticity_scores = [
            (p.get("formality_match", 5) + p.get("vulnerability_weight", 0)) / 2
            for p in top_discussed
        ]
        avg_authenticity = sum(authenticity_scores) / len(authenticity_scores)

        # Higher authenticity in top-discussed = higher depth correlation
        depth_correlation = max(0.0, min(10.0, avg_authenticity))
    else:
        depth_correlation = 5.0  # Default if insufficient comment data

    # Weighted average
    isc = (
        jargon_sensitivity * 0.3
        + link_sensitivity * 0.2
        + vulnerability_preference * 0.3
        + depth_correlation * 0.2
    )

    # Ensure range is 1.0-10.0
    isc = max(1.0, min(10.0, isc))

    return round(isc, 1)
