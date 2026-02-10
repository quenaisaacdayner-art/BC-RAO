"""
Apify client wrapper for Reddit scraping.
Uses Apify SDK to execute Reddit scraper actor and return post data.
"""
from typing import Optional
from apify_client import ApifyClient
from app.config import settings
from app.utils.errors import AppError, ErrorCode


def scrape_subreddit(
    subreddit: str,
    keywords: list[str],
    max_posts: int = 100
) -> list[dict]:
    """
    Scrape Reddit posts from a subreddit using Apify Reddit scraper actor.

    Args:
        subreddit: Target subreddit name (without r/)
        keywords: List of search terms to filter posts
        max_posts: Maximum number of posts to scrape (default 100)

    Returns:
        List of raw post dictionaries with fields:
        - id (reddit post ID)
        - url (reddit permalink)
        - author
        - title
        - selftext (post body)
        - subreddit
        - created_utc
        - num_comments
        - score (upvotes)
        - upvote_ratio

    Raises:
        AppError: APIFY_ERROR if API token not configured or scraping fails
    """
    # Check API token
    if not settings.APIFY_API_TOKEN:
        raise AppError(
            code=ErrorCode.APIFY_ERROR,
            message="Apify API token not configured",
            details={"env_var": "APIFY_API_TOKEN"},
            status_code=500
        )

    if not settings.APIFY_REDDIT_ACTOR_ID:
        raise AppError(
            code=ErrorCode.APIFY_ERROR,
            message="Apify Reddit actor ID not configured",
            details={"env_var": "APIFY_REDDIT_ACTOR_ID"},
            status_code=500
        )

    try:
        # Initialize Apify client
        client = ApifyClient(settings.APIFY_API_TOKEN)

        # Prepare actor input
        actor_input = {
            "subreddits": [subreddit],
            "searchTerms": keywords,
            "maxPosts": max_posts,
            "sort": "hot",
            "timeFilter": "month"
        }

        # Run the actor and wait for it to finish
        run = client.actor(settings.APIFY_REDDIT_ACTOR_ID).call(run_input=actor_input)

        # Fetch results from the default dataset
        dataset_items = client.dataset(run["defaultDatasetId"]).list_items()

        return dataset_items.items

    except Exception as e:
        raise AppError(
            code=ErrorCode.APIFY_ERROR,
            message=f"Failed to scrape subreddit: {subreddit}",
            details={
                "subreddit": subreddit,
                "error": str(e)
            },
            status_code=503
        )
