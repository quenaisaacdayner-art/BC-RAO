"""
Regex pre-filter for post quality scoring.
Removes ~80% of low-quality posts before AI processing using compiled patterns.
"""
import re
from typing import Optional


# Pre-compiled regex patterns at module level for performance
# Positive patterns (signals to KEEP)
PERSONAL_PRONOUNS = re.compile(r'\b(?:I|my|we|our|me)\b', re.IGNORECASE)
QUESTION_MARKS = re.compile(r'\?')
EMOTIONAL_LANGUAGE = re.compile(
    r'\b(?:frustrated|excited|helped|struggle|amazing|terrible|love|hate|worried|confused|grateful)\b',
    re.IGNORECASE
)
SPECIFIC_NUMBERS = re.compile(r'\b\d+(?:\.\d+)?(?:%|k|m|x|times|days|weeks|months|years)\b', re.IGNORECASE)
STORYTELLING_MARKERS = re.compile(
    r'\b(?:then|after|finally|realized|discovered|tried|started|ended|turned out)\b',
    re.IGNORECASE
)

# Negative patterns (signals to REJECT)
LINK_ONLY = re.compile(r'^https?://[^\s]+$')
BOT_MARKERS = re.compile(r'\[(?:removed|deleted)\]', re.IGNORECASE)
PURE_PROMO = re.compile(
    r'\b(?:buy now|use code|limited time|click here|get \d+% off|act now|order now)\b',
    re.IGNORECASE
)


def _calculate_relevance_score(post: dict, campaign_keywords: list[str]) -> float:
    """
    Calculate relevance score (0-10) for a single post.

    Scoring factors:
    - Keyword matches: +2 per keyword (max +6)
    - Personal pronouns: +1
    - Questions: +0.5
    - Emotional language: +1
    - Specific numbers: +0.5
    - Storytelling markers: +1
    - Post length bonus: +1 if > 200 chars
    - Engagement ratio: upvotes/comments normalized (max +2)

    Args:
        post: Reddit post dict
        campaign_keywords: List of target keywords

    Returns:
        Relevance score from 0-10
    """
    score = 0.0

    # Get post text fields
    title = post.get('title', '')
    text = post.get('selftext', '') or post.get('raw_text', '')
    combined_text = f"{title} {text}"

    # Keyword matches (max +6)
    keyword_matches = sum(
        1 for keyword in campaign_keywords
        if keyword.lower() in combined_text.lower()
    )
    score += min(keyword_matches * 2, 6)

    # Positive pattern matches
    if PERSONAL_PRONOUNS.search(combined_text):
        score += 1
    if QUESTION_MARKS.search(combined_text):
        score += 0.5
    if EMOTIONAL_LANGUAGE.search(combined_text):
        score += 1
    if SPECIFIC_NUMBERS.search(combined_text):
        score += 0.5
    if STORYTELLING_MARKERS.search(combined_text):
        score += 1

    # Post length bonus
    if len(combined_text) > 200:
        score += 1

    # Engagement ratio (upvotes per comment)
    upvotes = post.get('score', 0) or post.get('upvotes', 0) or 0
    comments = post.get('num_comments', 0) or post.get('comment_count', 0) or 1
    engagement_ratio = upvotes / max(comments, 1)
    # Normalize to 0-2 range (assuming 20+ ratio is excellent)
    score += min(engagement_ratio / 10, 2)

    return min(score, 10.0)


def _should_reject(post: dict) -> bool:
    """
    Check if post should be immediately rejected based on negative patterns.

    Rejection criteria:
    - Link-only posts (no meaningful text)
    - Very short posts (< 50 chars)
    - Bot/automated markers ([removed], [deleted])
    - Pure promotional language without story

    Args:
        post: Reddit post dict

    Returns:
        True if post should be rejected
    """
    title = post.get('title', '')
    text = post.get('selftext', '') or post.get('raw_text', '')
    combined_text = f"{title} {text}".strip()

    # Too short
    if len(combined_text) < 50:
        return True

    # Link-only post
    if LINK_ONLY.match(combined_text):
        return True

    # Bot markers
    if BOT_MARKERS.search(combined_text):
        return True

    # Pure promotional without substance
    if PURE_PROMO.search(combined_text) and len(combined_text) < 150:
        return True

    return False


def filter_posts(posts: list[dict], campaign_keywords: list[str]) -> list[dict]:
    """
    Filter and score Reddit posts based on relevance and quality.

    Targets ~80% rejection rate to focus on highest-quality posts.

    Args:
        posts: List of raw Reddit post dicts
        campaign_keywords: List of campaign keywords for relevance scoring

    Returns:
        Filtered list of posts sorted by relevance_score (descending)
        Each post has added 'relevance_score' field
    """
    filtered = []

    for post in posts:
        # Skip posts that match rejection patterns
        if _should_reject(post):
            continue

        # Calculate relevance score
        score = _calculate_relevance_score(post, campaign_keywords)

        # Add score to post
        post['relevance_score'] = score
        filtered.append(post)

    # Sort by relevance score descending
    filtered.sort(key=lambda p: p['relevance_score'], reverse=True)

    return filtered


def select_top_for_classification(
    filtered_posts: list[dict],
    top_percent: float = 0.1
) -> list[dict]:
    """
    Select top N% of filtered posts for LLM classification.

    Args:
        filtered_posts: Already filtered and scored posts
        top_percent: Percentage to select (0.1 = top 10%)

    Returns:
        List of top posts by relevance_score
    """
    if not filtered_posts:
        return []

    # Calculate how many posts to select
    count = max(1, int(len(filtered_posts) * top_percent))

    # Return top N posts (already sorted by relevance_score)
    return filtered_posts[:count]
