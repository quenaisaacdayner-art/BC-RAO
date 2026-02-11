"""
Collection service: Full pipeline orchestration for Reddit post collection.
Orchestrates: scrape -> filter -> classify -> store with partial failure handling.
"""
import asyncio
import json
from typing import Optional, Callable
from datetime import datetime
from uuid import UUID

from app.integrations.apify_client import scrape_subreddit
from app.services.regex_filter import filter_posts, select_top_for_classification
from app.inference.client import InferenceClient
from app.integrations.supabase_client import get_supabase_client
from app.models.raw_posts import (
    RawPostResponse,
    RawPostListResponse,
    CollectionProgress,
    CollectionResult
)
from app.utils.errors import AppError, ErrorCode


class CollectionService:
    """
    Service for orchestrating the full Reddit collection pipeline.
    Handles scraping, filtering, classification, and storage with deduplication.
    """

    def __init__(self):
        """Initialize collection service with Supabase client."""
        self.supabase = get_supabase_client()

    async def run_collection(
        self,
        campaign_id: str,
        user_id: str,
        plan: str,
        progress_callback: Optional[Callable[[CollectionProgress], None]] = None
    ) -> CollectionResult:
        """
        Run the full collection pipeline for a campaign.

        Pipeline steps:
        1. Fetch campaign details from database
        2. For each target subreddit:
           a. Scrape posts via Apify
           b. Filter posts via regex pre-filter
           c. Select top 10% for LLM classification
           d. Classify archetypes via InferenceClient
           e. Store posts in raw_posts table
        3. Return final counts and any errors

        Args:
            campaign_id: Campaign UUID
            user_id: User UUID (for ownership verification)
            plan: User plan tier (trial, starter, growth)
            progress_callback: Optional callback for progress updates

        Returns:
            CollectionResult with final counts and status

        Raises:
            AppError: NOT_FOUND if campaign doesn't exist or not owned by user
        """
        # Initialize counters
        scraped_total = 0
        filtered_total = 0
        classified_total = 0
        errors = []

        # Fetch campaign
        response = self.supabase.table("campaigns").select("*").eq("id", campaign_id).eq("user_id", user_id).execute()
        campaign = response.data[0] if response.data else None

        if not campaign:
            raise AppError(
                code=ErrorCode.RESOURCE_NOT_FOUND,
                message="Campaign not found or access denied",
                details={"campaign_id": campaign_id},
                status_code=404
            )
        target_subreddits = campaign.get("target_subreddits", [])
        keywords = campaign.get("keywords", [])

        if not target_subreddits:
            raise AppError(
                code=ErrorCode.VALIDATION_ERROR,
                message="Campaign has no target subreddits configured",
                details={"campaign_id": campaign_id},
                status_code=400
            )

        total_steps = len(target_subreddits)

        # Process each subreddit
        for step, subreddit in enumerate(target_subreddits, start=1):
            try:
                # Update progress: scraping
                if progress_callback:
                    progress_callback(CollectionProgress(
                        state="scraping",
                        scraped=scraped_total,
                        filtered=filtered_total,
                        classified=classified_total,
                        current_step=step,
                        total_steps=total_steps,
                        current_subreddit=subreddit,
                        errors=errors
                    ))

                # Step 1: Scrape posts (run in thread pool to avoid blocking event loop)
                scraped_posts = await asyncio.to_thread(
                    scrape_subreddit,
                    subreddit=subreddit,
                    keywords=keywords,
                    max_posts=100
                )
                scraped_total += len(scraped_posts)

                # Update progress: filtering
                if progress_callback:
                    progress_callback(CollectionProgress(
                        state="filtering",
                        scraped=scraped_total,
                        filtered=filtered_total,
                        classified=classified_total,
                        current_step=step,
                        total_steps=total_steps,
                        current_subreddit=subreddit,
                        errors=errors
                    ))

                # Step 2: Filter posts
                filtered_posts = filter_posts(scraped_posts, keywords)
                filtered_total += len(filtered_posts)

                # Step 3: Select top 10% for classification
                top_posts = select_top_for_classification(filtered_posts, top_percent=0.1)

                # Update progress: classifying
                if progress_callback:
                    progress_callback(CollectionProgress(
                        state="classifying",
                        scraped=scraped_total,
                        filtered=filtered_total,
                        classified=classified_total,
                        current_step=step,
                        total_steps=total_steps,
                        current_subreddit=subreddit,
                        errors=errors
                    ))

                # Step 4: Classify archetypes for top posts
                classified_posts = []
                for post in top_posts:
                    try:
                        classified_post = await self._classify_post(
                            post=post,
                            user_id=user_id,
                            plan=plan,
                            campaign_id=campaign_id
                        )
                        classified_posts.append(classified_post)
                        classified_total += 1
                    except Exception as e:
                        # Log classification error but continue
                        errors.append(f"Classification failed for post in {subreddit}: {str(e)}")
                        # Add post without classification
                        post['archetype'] = 'Unclassified'
                        post['success_score'] = 5.0
                        post['is_ai_processed'] = False
                        classified_posts.append(post)

                # Update progress: storing
                if progress_callback:
                    progress_callback(CollectionProgress(
                        state="storing",
                        scraped=scraped_total,
                        filtered=filtered_total,
                        classified=classified_total,
                        current_step=step,
                        total_steps=total_steps,
                        current_subreddit=subreddit,
                        errors=errors
                    ))

                # Step 5: Store all filtered posts (both classified and unclassified)
                # Combine classified posts with remaining filtered posts
                all_posts_to_store = classified_posts.copy()
                classified_ids = {p.get('id') for p in classified_posts}
                for post in filtered_posts:
                    if post.get('id') not in classified_ids:
                        post['archetype'] = 'Unclassified'
                        post['success_score'] = post.get('relevance_score', 5.0)
                        post['is_ai_processed'] = False
                        all_posts_to_store.append(post)

                await self._store_posts(
                    posts=all_posts_to_store,
                    campaign_id=campaign_id,
                    user_id=user_id,
                    subreddit=subreddit
                )

            except Exception as e:
                # Partial failure: log error and continue to next subreddit
                error_msg = f"Failed to process subreddit {subreddit}: {str(e)}"
                errors.append(error_msg)
                continue

        # Update progress: complete
        if progress_callback:
            progress_callback(CollectionProgress(
                state="complete",
                scraped=scraped_total,
                filtered=filtered_total,
                classified=classified_total,
                current_step=total_steps,
                total_steps=total_steps,
                errors=errors
            ))

        # Determine final status
        status = "partial" if errors else "complete"

        return CollectionResult(
            status=status,
            scraped=scraped_total,
            filtered=filtered_total,
            classified=classified_total,
            errors=errors
        )

    async def _classify_post(
        self,
        post: dict,
        user_id: str,
        plan: str,
        campaign_id: str
    ) -> dict:
        """
        Classify a single post's archetype and success score via LLM.

        Args:
            post: Reddit post dict
            user_id: User UUID
            plan: User plan tier
            campaign_id: Campaign UUID

        Returns:
            Post dict updated with archetype, success_score, and is_ai_processed=True
        """
        title = post.get('title', '')
        text = post.get('selftext', '') or post.get('raw_text', '')

        # Truncate text for prompt
        text_preview = text[:500] if text else ""

        # Build classification prompt
        prompt = f"""Classify this Reddit post into exactly one archetype: Journey (personal story/experience), ProblemSolution (asking for or providing solutions), or Feedback (opinions/reviews/recommendations).

Also score its success potential from 0-10 based on engagement signals (upvotes, comments, emotional language, specificity).

Post title: {title}
Post text: {text_preview}

Respond with JSON only:
{{"archetype": "Journey|ProblemSolution|Feedback", "success_score": 7.5}}"""

        try:
            # Call InferenceClient
            inference_client = InferenceClient("classify_archetype")
            result = await inference_client.call(
                prompt=prompt,
                user_id=user_id,
                plan=plan,
                campaign_id=campaign_id
            )

            # Parse JSON response
            content = result["content"]
            parsed = json.loads(content)

            archetype = parsed.get("archetype", "Unclassified")
            success_score = float(parsed.get("success_score", 5.0))

            # Validate archetype
            valid_archetypes = ["Journey", "ProblemSolution", "Feedback"]
            if archetype not in valid_archetypes:
                archetype = "Unclassified"

            # Update post
            post['archetype'] = archetype
            post['success_score'] = success_score
            post['is_ai_processed'] = True

        except json.JSONDecodeError:
            # Fallback on parse failure
            post['archetype'] = 'Unclassified'
            post['success_score'] = 5.0
            post['is_ai_processed'] = False
        except Exception:
            # Fallback on any error
            post['archetype'] = 'Unclassified'
            post['success_score'] = 5.0
            post['is_ai_processed'] = False

        return post

    async def _store_posts(
        self,
        posts: list[dict],
        campaign_id: str,
        user_id: str,
        subreddit: str
    ) -> int:
        """
        Store posts in raw_posts table with deduplication.

        Uses Supabase upsert with ON CONFLICT to handle duplicates.

        Args:
            posts: List of post dicts
            campaign_id: Campaign UUID
            user_id: User UUID
            subreddit: Subreddit name

        Returns:
            Count of posts processed (may include duplicates that were ignored)
        """
        if not posts:
            return 0

        # Map post fields to raw_posts schema
        rows = []
        for post in posts:
            row = {
                "campaign_id": campaign_id,
                "user_id": user_id,
                "subreddit": subreddit,
                "reddit_post_id": post.get("id", ""),
                "reddit_url": post.get("url") or post.get("permalink"),
                "author": post.get("author"),
                "author_karma": post.get("author_karma"),
                "title": post.get("title", ""),
                "raw_text": post.get("selftext", "") or post.get("raw_text", ""),
                "comment_count": post.get("num_comments", 0) or post.get("comment_count", 0),
                "upvote_ratio": post.get("upvote_ratio"),
                "archetype": post.get("archetype", "Unclassified"),
                "success_score": post.get("success_score"),
                "is_ai_processed": post.get("is_ai_processed", False),
                "reddit_created_at": None  # TODO: parse from created_utc if available
            }

            # Parse reddit_created_at if present
            if "created_utc" in post:
                try:
                    row["reddit_created_at"] = datetime.fromtimestamp(post["created_utc"]).isoformat()
                except:
                    pass

            rows.append(row)

        # Upsert with conflict resolution on (campaign_id, reddit_post_id)
        # Using ignore_duplicates to skip existing posts
        self.supabase.table("raw_posts").upsert(
            rows,
            on_conflict="campaign_id,reddit_post_id",
            ignore_duplicates=True
        ).execute()

        return len(rows)

    async def get_posts(
        self,
        campaign_id: str,
        user_id: str,
        archetype: Optional[str] = None,
        subreddit: Optional[str] = None,
        min_score: Optional[float] = None,
        max_score: Optional[float] = None,
        page: int = 1,
        per_page: int = 20
    ) -> RawPostListResponse:
        """
        Get paginated list of raw posts with optional filters.

        Args:
            campaign_id: Campaign UUID
            user_id: User UUID (for RLS)
            archetype: Filter by archetype (optional)
            subreddit: Filter by subreddit (optional)
            min_score: Minimum success_score (optional)
            max_score: Maximum success_score (optional)
            page: Page number (1-indexed)
            per_page: Items per page

        Returns:
            RawPostListResponse with posts, total, page, per_page
        """
        # Build query
        query = self.supabase.table("raw_posts").select("*", count="exact")
        query = query.eq("campaign_id", campaign_id)

        # Apply optional filters
        if archetype:
            query = query.eq("archetype", archetype)
        if subreddit:
            query = query.eq("subreddit", subreddit)
        if min_score is not None:
            query = query.gte("success_score", min_score)
        if max_score is not None:
            query = query.lte("success_score", max_score)

        # Apply ordering
        query = query.order("success_score", desc=True).order("collected_at", desc=True)

        # Apply pagination
        offset = (page - 1) * per_page
        query = query.range(offset, offset + per_page - 1)

        # Execute query
        response = query.execute()

        # Parse response
        posts = [RawPostResponse(**post) for post in response.data]
        total = response.count or 0

        return RawPostListResponse(
            posts=posts,
            total=total,
            page=page,
            per_page=per_page
        )

    async def get_post_detail(
        self,
        post_id: str,
        user_id: str
    ) -> RawPostResponse:
        """
        Get single post detail by ID.

        Args:
            post_id: Post UUID
            user_id: User UUID (for RLS verification)

        Returns:
            RawPostResponse

        Raises:
            AppError: NOT_FOUND if post doesn't exist or not owned by user
        """
        response = self.supabase.table("raw_posts").select("*").eq("id", post_id).execute()
        post = response.data[0] if response.data else None

        if not post:
            raise AppError(
                code=ErrorCode.RESOURCE_NOT_FOUND,
                message="Post not found",
                details={"post_id": post_id},
                status_code=404
            )

        return RawPostResponse(**post)

    async def get_collection_stats(
        self,
        campaign_id: str,
        user_id: str
    ) -> dict:
        """
        Get collection statistics for a campaign.

        Args:
            campaign_id: Campaign UUID
            user_id: User UUID (for RLS)

        Returns:
            Dict with stats:
            - total: Total post count
            - by_archetype: Count by archetype
            - by_subreddit: Count by subreddit
            - avg_success_score: Average success score
        """
        # Get all posts for this campaign
        response = self.supabase.table("raw_posts").select("archetype, subreddit, success_score").eq("campaign_id", campaign_id).execute()

        posts = response.data
        total = len(posts)

        if total == 0:
            return {
                "total": 0,
                "by_archetype": {},
                "by_subreddit": {},
                "avg_success_score": 0.0
            }

        # Count by archetype
        by_archetype = {}
        for post in posts:
            archetype = post.get("archetype", "Unclassified")
            by_archetype[archetype] = by_archetype.get(archetype, 0) + 1

        # Count by subreddit
        by_subreddit = {}
        for post in posts:
            subreddit = post.get("subreddit", "Unknown")
            by_subreddit[subreddit] = by_subreddit.get(subreddit, 0) + 1

        # Calculate average success score
        scores = [p.get("success_score") for p in posts if p.get("success_score") is not None]
        avg_success_score = sum(scores) / len(scores) if scores else 0.0

        return {
            "total": total,
            "by_archetype": by_archetype,
            "by_subreddit": by_subreddit,
            "avg_success_score": round(avg_success_score, 2)
        }
