"""
Tests for regex pre-filter - collection accuracy feature.

Tests post filtering based on relevance scoring, keyword matching,
and quality signals to reduce low-quality posts before AI processing.
"""
import pytest
from app.services.regex_filter import (
    filter_posts,
    select_top_for_classification,
    _calculate_relevance_score,
    _should_reject
)


class TestRelevanceScoring:
    """Test relevance score calculation."""

    def test_keyword_match_increases_score(self):
        """Posts matching keywords should get higher scores."""
        post_without = {
            "title": "Random post about nothing",
            "selftext": "This is just some random content.",
            "score": 10,
            "num_comments": 5
        }
        post_with = {
            "title": "Python programming question",
            "selftext": "I'm learning Python and need help.",
            "score": 10,
            "num_comments": 5
        }
        keywords = ["python", "programming"]

        score_without = _calculate_relevance_score(post_without, keywords)
        score_with = _calculate_relevance_score(post_with, keywords)

        assert score_with > score_without

    def test_multiple_keywords_boost_score(self):
        """More keyword matches should yield higher scores."""
        post_one_keyword = {
            "title": "Python question",
            "selftext": "Need help with something.",
            "score": 10,
            "num_comments": 5
        }
        post_multiple_keywords = {
            "title": "Python programming question",
            "selftext": "Learning Python programming.",
            "score": 10,
            "num_comments": 5
        }
        keywords = ["python", "programming"]

        score_one = _calculate_relevance_score(post_one_keyword, keywords)
        score_multiple = _calculate_relevance_score(post_multiple_keywords, keywords)

        assert score_multiple > score_one

    def test_personal_pronouns_boost_score(self):
        """Personal pronouns indicate engagement quality."""
        post_impersonal = {
            "title": "Discussion about Python",
            "selftext": "The language has many features.",
            "score": 10,
            "num_comments": 5
        }
        post_personal = {
            "title": "My Python journey",
            "selftext": "I've been learning Python and we built something.",
            "score": 10,
            "num_comments": 5
        }
        keywords = ["python"]

        score_impersonal = _calculate_relevance_score(post_impersonal, keywords)
        score_personal = _calculate_relevance_score(post_personal, keywords)

        assert score_personal > score_impersonal

    def test_questions_boost_score(self):
        """Question marks indicate engagement potential."""
        post_statement = {
            "title": "Python tips",
            "selftext": "Here are some Python tips.",
            "score": 10,
            "num_comments": 5
        }
        post_question = {
            "title": "Python help?",
            "selftext": "How do I do this in Python?",
            "score": 10,
            "num_comments": 5
        }
        keywords = ["python"]

        score_statement = _calculate_relevance_score(post_statement, keywords)
        score_question = _calculate_relevance_score(post_question, keywords)

        assert score_question > score_statement

    def test_emotional_language_boost_score(self):
        """Emotional language indicates authentic engagement."""
        post_neutral = {
            "title": "Python programming",
            "selftext": "Looking at Python code.",
            "score": 10,
            "num_comments": 5
        }
        post_emotional = {
            "title": "Frustrated with Python",
            "selftext": "I'm so excited but also confused and worried.",
            "score": 10,
            "num_comments": 5
        }
        keywords = ["python"]

        score_neutral = _calculate_relevance_score(post_neutral, keywords)
        score_emotional = _calculate_relevance_score(post_emotional, keywords)

        assert score_emotional > score_neutral

    def test_specific_numbers_boost_score(self):
        """Specific numbers/metrics indicate substantive content."""
        post_vague = {
            "title": "Python project",
            "selftext": "Working on a project.",
            "score": 10,
            "num_comments": 5
        }
        post_specific = {
            "title": "Python project",
            "selftext": "Spent 40 hours on this, got 500 users in 2 weeks.",
            "score": 10,
            "num_comments": 5
        }
        keywords = ["python"]

        score_vague = _calculate_relevance_score(post_vague, keywords)
        score_specific = _calculate_relevance_score(post_specific, keywords)

        assert score_specific > score_vague

    def test_long_posts_get_bonus(self):
        """Posts longer than 200 chars get length bonus."""
        post_short = {
            "title": "Python",
            "selftext": "Short post.",
            "score": 10,
            "num_comments": 5
        }
        post_long = {
            "title": "Python detailed question",
            "selftext": "A" * 250,  # Long text
            "score": 10,
            "num_comments": 5
        }
        keywords = ["python"]

        score_short = _calculate_relevance_score(post_short, keywords)
        score_long = _calculate_relevance_score(post_long, keywords)

        assert score_long > score_short

    def test_high_engagement_ratio_boosts_score(self):
        """High upvote-to-comment ratio indicates quality."""
        post_low_engagement = {
            "title": "Python",
            "selftext": "Python question",
            "score": 5,
            "num_comments": 10
        }
        post_high_engagement = {
            "title": "Python",
            "selftext": "Python question",
            "score": 100,
            "num_comments": 5
        }
        keywords = ["python"]

        score_low = _calculate_relevance_score(post_low_engagement, keywords)
        score_high = _calculate_relevance_score(post_high_engagement, keywords)

        assert score_high > score_low


class TestRejectionCriteria:
    """Test post rejection logic."""

    def test_very_short_posts_rejected(self):
        """Posts shorter than 50 characters should be rejected."""
        post = {
            "title": "Help",
            "selftext": "Need help."
        }
        assert _should_reject(post) is True

    def test_adequate_length_not_rejected(self):
        """Posts with adequate length should not be rejected for length."""
        post = {
            "title": "Python programming question about best practices",
            "selftext": "I've been working on a Python project and wondering about best practices."
        }
        assert _should_reject(post) is False

    def test_link_only_posts_rejected(self):
        """Posts that are just a link should be rejected."""
        post = {
            "title": "Check this",
            "selftext": "https://example.com/link"
        }
        assert _should_reject(post) is True

    def test_removed_posts_rejected(self):
        """Posts marked as [removed] should be rejected."""
        post = {
            "title": "Removed post",
            "selftext": "[removed]"
        }
        assert _should_reject(post) is True

    def test_deleted_posts_rejected(self):
        """Posts marked as [deleted] should be rejected."""
        post = {
            "title": "[deleted]",
            "selftext": "Some content"
        }
        assert _should_reject(post) is True

    def test_pure_promo_short_rejected(self):
        """Short posts with pure promotional language should be rejected."""
        post = {
            "title": "Check this out",
            "selftext": "Buy now and get 50% off! Click here!"
        }
        assert _should_reject(post) is True

    def test_promo_with_substance_not_rejected(self):
        """Longer posts with promotional language and substance not rejected."""
        post = {
            "title": "My experience building a tool",
            "selftext": "A" * 200 + " You can buy now if interested."
        }
        # Should not be rejected - has substance
        assert _should_reject(post) is False


class TestFilterPosts:
    """Test the main filter_posts function."""

    def test_empty_posts_returns_empty(self):
        """Filtering empty list should return empty list."""
        result = filter_posts([], ["python"])
        assert len(result) == 0

    def test_rejected_posts_removed(self):
        """Posts that should be rejected are filtered out."""
        posts = [
            {"title": "Good post", "selftext": "A" * 100, "score": 10, "num_comments": 5},
            {"title": "Bad", "selftext": "[removed]", "score": 1, "num_comments": 0}
        ]
        result = filter_posts(posts, ["python"])
        assert len(result) == 1
        assert result[0]["title"] == "Good post"

    def test_relevance_score_added(self):
        """Filtered posts should have relevance_score field added."""
        posts = [
            {"title": "Python question", "selftext": "A" * 100, "score": 10, "num_comments": 5}
        ]
        result = filter_posts(posts, ["python"])
        assert len(result) == 1
        assert "relevance_score" in result[0]
        assert isinstance(result[0]["relevance_score"], (int, float))

    def test_posts_sorted_by_relevance(self):
        """Posts should be sorted by relevance score (descending)."""
        posts = [
            {"title": "Low relevance", "selftext": "Some text", "score": 1, "num_comments": 1},
            {"title": "High relevance python programming", "selftext": "Python programming question?", "score": 100, "num_comments": 10},
            {"title": "Medium python", "selftext": "About python", "score": 10, "num_comments": 5}
        ]
        result = filter_posts(posts, ["python", "programming"])

        assert len(result) == 3
        # Scores should be in descending order
        scores = [p["relevance_score"] for p in result]
        assert scores == sorted(scores, reverse=True)

    def test_keyword_matching_case_insensitive(self):
        """Keyword matching should be case-insensitive."""
        posts = [
            {"title": "PYTHON question", "selftext": "About PYTHON", "score": 10, "num_comments": 5},
            {"title": "python question", "selftext": "About python", "score": 10, "num_comments": 5},
            {"title": "Python question", "selftext": "About Python", "score": 10, "num_comments": 5}
        ]
        keywords = ["python"]
        result = filter_posts(posts, keywords)

        # All should be kept and have similar scores
        assert len(result) == 3
        scores = [p["relevance_score"] for p in result]
        # All should have matched the keyword
        assert all(s > 0 for s in scores)

    def test_empty_keywords_still_filters(self):
        """Even with empty keywords, quality filtering should work."""
        posts = [
            {"title": "Good post", "selftext": "A" * 100 + " I need help?", "score": 10, "num_comments": 5},
            {"title": "Bad", "selftext": "[removed]", "score": 1, "num_comments": 0}
        ]
        result = filter_posts(posts, [])
        # Should remove rejected post
        assert len(result) == 1
        # Should still calculate relevance score (just without keyword bonus)
        assert "relevance_score" in result[0]


class TestSelectTopForClassification:
    """Test selecting top posts for LLM classification."""

    def test_empty_list_returns_empty(self):
        """Empty filtered list should return empty."""
        result = select_top_for_classification([], top_percent=0.1)
        assert len(result) == 0

    def test_top_percent_selection(self):
        """Should select correct percentage of posts."""
        posts = [
            {"id": i, "relevance_score": 10 - i} for i in range(100)
        ]
        result = select_top_for_classification(posts, top_percent=0.1)

        # Should select top 10%
        assert len(result) == 10
        # Should be the highest scoring ones
        assert all(p["relevance_score"] >= 9 for p in result)

    def test_minimum_one_post_selected(self):
        """Should select at least 1 post even if percentage rounds to 0."""
        posts = [
            {"id": 1, "relevance_score": 5.0}
        ]
        result = select_top_for_classification(posts, top_percent=0.01)

        # Should select at least 1
        assert len(result) == 1

    def test_already_sorted_posts(self):
        """Should work with already sorted posts from filter_posts."""
        posts = [
            {"id": 1, "relevance_score": 10.0},
            {"id": 2, "relevance_score": 8.0},
            {"id": 3, "relevance_score": 6.0},
            {"id": 4, "relevance_score": 4.0}
        ]
        result = select_top_for_classification(posts, top_percent=0.5)

        # Should select top 50% (2 posts)
        assert len(result) == 2
        assert result[0]["id"] == 1
        assert result[1]["id"] == 2

    def test_top_20_percent(self):
        """Test with different percentage."""
        posts = [{"id": i, "relevance_score": 10 - i} for i in range(50)]
        result = select_top_for_classification(posts, top_percent=0.2)

        # Should select top 20% (10 posts)
        assert len(result) == 10


class TestEndToEndFiltering:
    """Test complete filtering pipeline."""

    def test_realistic_filtering_scenario(self):
        """Test with realistic mix of good and bad posts."""
        posts = [
            # High quality, relevant
            {
                "id": "1",
                "title": "My Python journey",
                "selftext": "I've been learning Python for 6 months and built 3 projects. Here's what I learned...",
                "score": 50,
                "num_comments": 15
            },
            # Medium quality, relevant
            {
                "id": "2",
                "title": "Python question",
                "selftext": "How do I parse JSON in Python?",
                "score": 20,
                "num_comments": 5
            },
            # Low quality - too short
            {
                "id": "3",
                "title": "Help",
                "selftext": "Need help",
                "score": 1,
                "num_comments": 0
            },
            # Removed post
            {
                "id": "4",
                "title": "Removed",
                "selftext": "[removed]",
                "score": 0,
                "num_comments": 0
            },
            # Good quality, not relevant
            {
                "id": "5",
                "title": "JavaScript tips",
                "selftext": "I've been working with JavaScript and found these useful patterns...",
                "score": 30,
                "num_comments": 10
            }
        ]

        keywords = ["python"]
        filtered = filter_posts(posts, keywords)

        # Should remove short and removed posts
        assert len(filtered) == 3

        # Python posts should rank higher
        top_post_ids = [p["id"] for p in filtered[:2]]
        assert "1" in top_post_ids  # High quality Python post
        assert "2" in top_post_ids  # Medium quality Python post

        # All should have relevance scores
        assert all("relevance_score" in p for p in filtered)

    def test_80_percent_rejection_rate(self):
        """Filter should target ~80% rejection for quality focus."""
        # Create 100 posts with varying quality
        posts = []

        # 20 high quality posts
        for i in range(20):
            posts.append({
                "id": f"high_{i}",
                "title": f"Python programming question {i}",
                "selftext": "I've been working on a Python project " * 20 + "?",
                "score": 50 + i,
                "num_comments": 10 + i
            })

        # 80 low quality posts (short)
        for i in range(80):
            posts.append({
                "id": f"low_{i}",
                "title": "Short",
                "selftext": "Too short",
                "score": 1,
                "num_comments": 0
            })

        keywords = ["python", "programming"]
        filtered = filter_posts(posts, keywords)

        # Should keep only the 20 high quality posts
        assert len(filtered) == 20

        # Rejection rate should be ~80%
        rejection_rate = (100 - len(filtered)) / 100
        assert rejection_rate == 0.80


@pytest.mark.parametrize("keyword", ["python", "django", "flask", "fastapi"])
def test_keyword_variations(keyword):
    """Test filtering with different keywords."""
    posts = [
        {"title": f"{keyword} question", "selftext": f"About {keyword}", "score": 10, "num_comments": 5}
    ]
    result = filter_posts(posts, [keyword])

    assert len(result) == 1
    assert result[0]["relevance_score"] > 0
