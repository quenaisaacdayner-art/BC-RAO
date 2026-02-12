"""
Reddit dual-check client for shadowban detection.

Uses httpx for lightweight HTTP requests to Reddit's public JSON endpoints.
Performs authenticated + anonymous checks to detect shadowbanned posts.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Literal

import httpx

from app.config import settings


logger = logging.getLogger(__name__)


class RedditDualCheckClient:
    """
    Reddit client that performs dual-check (auth + anon) for shadowban detection.

    Uses Reddit's OAuth2 client credentials flow for authenticated requests
    and public JSON endpoints for anonymous requests.
    """

    def __init__(self):
        """Initialize Reddit dual-check client with OAuth credentials."""
        self.client_id = settings.REDDIT_CLIENT_ID
        self.client_secret = settings.REDDIT_CLIENT_SECRET

        # OAuth token cache
        self._access_token: str | None = None
        self._token_expires_at: datetime | None = None

        # HTTP clients (will be created on first use)
        self._auth_client: httpx.AsyncClient | None = None
        self._anon_client: httpx.AsyncClient | None = None

    async def _get_auth_client(self) -> httpx.AsyncClient:
        """Get or create authenticated HTTP client."""
        if self._auth_client is None:
            self._auth_client = httpx.AsyncClient(
                headers={
                    "User-Agent": "BC-RAO/1.0 (monitoring)"
                },
                timeout=30.0
            )
        return self._auth_client

    async def _get_anon_client(self) -> httpx.AsyncClient:
        """Get or create anonymous HTTP client."""
        if self._anon_client is None:
            self._anon_client = httpx.AsyncClient(
                headers={
                    "User-Agent": "Mozilla/5.0 (compatible; BC-RAO-Monitor/1.0)"
                },
                timeout=30.0
            )
        return self._anon_client

    async def get_oauth_token(self) -> str:
        """
        Get OAuth access token via client credentials grant.

        Caches token for 3500 seconds (expires at 3600).

        Returns:
            Access token string

        Raises:
            httpx.HTTPError: If token request fails
        """
        # Return cached token if still valid
        if self._access_token and self._token_expires_at:
            if datetime.utcnow() < self._token_expires_at:
                return self._access_token

        # Request new token
        logger.info("Requesting new Reddit OAuth token")

        auth = (self.client_id, self.client_secret)
        data = {"grant_type": "client_credentials"}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://www.reddit.com/api/v1/access_token",
                    auth=auth,
                    data=data,
                    headers={"User-Agent": "BC-RAO/1.0 (monitoring)"}
                )
                response.raise_for_status()

            token_data = response.json()
            self._access_token = token_data["access_token"]
            # Cache for 3500 seconds (expires at 3600, leave 100s buffer)
            self._token_expires_at = datetime.utcnow() + timedelta(seconds=3500)

            logger.info("Reddit OAuth token obtained successfully")
            return self._access_token
        except httpx.HTTPError as e:
            logger.error(f"Reddit OAuth token fetch failed: {e}")
            raise Exception(f"Failed to authenticate with Reddit API: {e}")

    async def dual_check_post(self, reddit_post_id: str) -> Literal["active", "removed", "shadowbanned"]:
        """
        Perform dual-check (auth + anon) to detect post status.

        Detection logic:
        - Both auth and anon see post → "active"
        - Auth sees post, anon doesn't → "shadowbanned"
        - Auth doesn't see post → "removed"
        - Both fail → "removed"

        Args:
            reddit_post_id: Reddit post ID (without t3_ prefix)

        Returns:
            Status: "active", "removed", or "shadowbanned"

        Raises:
            httpx.HTTPError: On network/API errors (caller should retry)
        """
        logger.info(f"Starting dual-check for post {reddit_post_id}")

        # 1. Authenticated check
        auth_ok = False
        try:
            token = await self.get_oauth_token()
            auth_client = await self._get_auth_client()

            auth_response = await auth_client.get(
                f"https://oauth.reddit.com/api/info?id=t3_{reddit_post_id}",
                headers={"Authorization": f"Bearer {token}"}
            )
            auth_response.raise_for_status()

            auth_data = auth_response.json()
            if auth_data.get("data", {}).get("children"):
                post_data = auth_data["data"]["children"][0]["data"]
                # Check if post is not removed
                removed_by = post_data.get("removed_by_category")
                auth_ok = removed_by is None
                logger.info(f"Auth check: {'OK' if auth_ok else 'FAIL'} (removed_by_category={removed_by})")
            else:
                logger.info("Auth check: FAIL (no post data)")

        except Exception as e:
            logger.error(f"Auth check failed: {e}")
            # Don't raise - continue to anon check

        # Rate limit awareness: sleep 2s between checks
        await asyncio.sleep(2)

        # 2. Anonymous check
        anon_ok = False
        try:
            anon_client = await self._get_anon_client()

            anon_response = await anon_client.get(
                f"https://www.reddit.com/comments/{reddit_post_id}.json"
            )
            anon_response.raise_for_status()

            anon_data = anon_response.json()
            if anon_data and len(anon_data) > 0:
                post_listing = anon_data[0].get("data", {}).get("children", [])
                if post_listing:
                    post_data = post_listing[0]["data"]
                    selftext = post_data.get("selftext", "")
                    # Check if post is not [removed]
                    anon_ok = "[removed]" not in selftext and selftext != "[removed]"
                    logger.info(f"Anon check: {'OK' if anon_ok else 'FAIL'} (selftext={selftext[:50]})")
                else:
                    logger.info("Anon check: FAIL (no post listing)")
            else:
                logger.info("Anon check: FAIL (empty response)")

        except Exception as e:
            logger.error(f"Anon check failed: {e}")
            # Don't raise - continue to determination

        # 3. Determine status
        if auth_ok and anon_ok:
            status = "active"
        elif auth_ok and not anon_ok:
            status = "shadowbanned"
        else:
            status = "removed"

        logger.info(f"Dual-check result for {reddit_post_id}: {status} (auth={auth_ok}, anon={anon_ok})")
        return status

    async def fetch_post_metrics(self, reddit_post_id: str) -> dict:
        """
        Fetch post metrics (upvotes, comments) for 7-day audit.

        Args:
            reddit_post_id: Reddit post ID (without t3_ prefix)

        Returns:
            Dict with 'upvotes' and 'comments' keys

        Raises:
            httpx.HTTPError: On network/API errors
        """
        logger.info(f"Fetching metrics for post {reddit_post_id}")

        token = await self.get_oauth_token()
        auth_client = await self._get_auth_client()

        response = await auth_client.get(
            f"https://oauth.reddit.com/api/info?id=t3_{reddit_post_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        response.raise_for_status()

        data = response.json()
        if not data.get("data", {}).get("children"):
            logger.warning(f"No metrics data found for post {reddit_post_id}")
            return {"upvotes": 0, "comments": 0}

        post_data = data["data"]["children"][0]["data"]
        upvotes = post_data.get("ups", 0)
        comments = post_data.get("num_comments", 0)

        logger.info(f"Post {reddit_post_id} metrics: upvotes={upvotes}, comments={comments}")
        return {"upvotes": upvotes, "comments": comments}

    async def close(self):
        """Close HTTP clients."""
        if self._auth_client:
            await self._auth_client.aclose()
        if self._anon_client:
            await self._anon_client.aclose()
