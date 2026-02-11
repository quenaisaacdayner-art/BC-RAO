"""
Apify client wrapper for Reddit scraping.
Uses Apify SDK to execute Reddit scraper actor and return post data.
"""
import logging
from apify_client import ApifyClient
from app.config import settings
from app.utils.errors import AppError, ErrorCode

logger = logging.getLogger(__name__)


def scrape_subreddit(
    subreddit: str,
    keywords: list[str],
    max_posts: int = 100
) -> list[dict]:
    """
    Scrape Reddit posts from a subreddit using Apify Reddit Scraper Lite.

    Uses the `startUrls` input format for subreddit browsing, or `searches`
    with `searchCommunityName` when keywords are provided.

    Args:
        subreddit: Target subreddit name (without r/)
        keywords: List of search terms to filter posts
        max_posts: Maximum number of posts to scrape (default 100)

    Returns:
        List of raw post dictionaries from Apify dataset.
        Fields vary by actor but typically include:
        - id, url, title, body/selftext, author, subreddit,
          createdAt/created_utc, numberOfComments/num_comments,
          score/upVotes, upvoteRatio

    Raises:
        AppError: APIFY_ERROR if API token not configured or scraping fails
    """
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
        client = ApifyClient(settings.APIFY_API_TOKEN)

        # Build actor input compatible with Reddit Scraper Lite
        # If keywords exist, use search mode within the subreddit
        # Otherwise, browse the subreddit directly
        if keywords:
            actor_input = {
                "searches": keywords,
                "searchCommunityName": subreddit,
                "searchPosts": True,
                "searchComments": False,
                "maxItems": max_posts,
                "sort": "relevance",
                "time": "month",
            }
        else:
            actor_input = {
                "startUrls": [{"url": f"https://www.reddit.com/r/{subreddit}/"}],
                "maxItems": max_posts,
                "sort": "hot",
                "time": "month",
            }

        logger.info(f"Scraping r/{subreddit} with {'search' if keywords else 'browse'} mode, max {max_posts} posts")

        # Run the actor and wait for it to finish
        run = client.actor(settings.APIFY_REDDIT_ACTOR_ID).call(run_input=actor_input)

        # Fetch results from the default dataset
        dataset_items = client.dataset(run["defaultDatasetId"]).list_items()
        items = dataset_items.items

        # Normalize field names for downstream compatibility
        normalized = []
        for item in items:
            normalized.append(_normalize_post(item, subreddit))

        logger.info(f"Scraped {len(normalized)} posts from r/{subreddit}")
        return normalized

    except AppError:
        raise
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


def _normalize_post(item: dict, fallback_subreddit: str) -> dict:
    """
    Normalize Apify actor output to consistent field names.
    Different actors use different field names, so we map them here.
    """
    return {
        "id": item.get("id") or item.get("postId") or "",
        "url": item.get("url") or item.get("permalink") or "",
        "author": item.get("author") or item.get("username") or "",
        "author_karma": item.get("authorKarma") or item.get("author_karma"),
        "title": item.get("title") or "",
        "selftext": item.get("body") or item.get("selftext") or item.get("text") or "",
        "raw_text": item.get("body") or item.get("selftext") or item.get("text") or "",
        "subreddit": item.get("communityName") or item.get("subreddit") or fallback_subreddit,
        "created_utc": item.get("createdAt") or item.get("created_utc"),
        "num_comments": item.get("numberOfComments") or item.get("num_comments") or 0,
        "score": item.get("upVotes") or item.get("score") or 0,
        "upvote_ratio": item.get("upvoteRatio") or item.get("upvote_ratio"),
        "permalink": item.get("url") or item.get("permalink") or "",
    }
