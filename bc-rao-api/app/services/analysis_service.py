"""
Analysis service orchestrating NLP processing, scoring, and community profile creation.

Orchestrates the full analysis pipeline:
1. Fetch raw posts from Supabase
2. Group by subreddit
3. Run NLP analysis (formality, tone, rhythm)
4. Calculate post scores using vulnerability + rhythm + formality formula
5. Update raw_posts with NLP metadata and scores
6. Calculate ISC score for each subreddit
7. Extract forbidden patterns
8. Create/update community profiles

Progress tracking via optional callback for SSE streaming.
"""

import statistics
from typing import Optional, Callable, List, Dict, Any
from uuid import UUID

from app.integrations.supabase_client import get_supabase_client
from app.analysis.nlp_pipeline import analyze_posts_batch
from app.analysis.scorers import (
    calculate_post_score,
    calculate_isc_score,
)
from app.analysis.pattern_extractor import (
    extract_forbidden_patterns,
    check_post_penalties,
)
from app.models.analysis import (
    AnalysisResult,
    AnalysisProgress,
    CommunityProfileResponse,
    PostScoreBreakdown,
    BlacklistResponse,
    ForbiddenPatternEntry,
    isc_to_tier,
)
from app.utils.errors import AppError, ErrorCode


class AnalysisService:
    """Service for analyzing collected posts and creating community profiles."""

    def __init__(self):
        self.supabase = get_supabase_client()

    async def run_analysis(
        self,
        campaign_id: str,
        force_refresh: bool = False,
        progress_callback: Optional[Callable[[AnalysisProgress], None]] = None,
    ) -> AnalysisResult:
        """
        Run full analysis pipeline: NLP -> scoring -> profiling.

        Steps:
        1. Fetch raw posts for campaign
        2. Check if profiles already exist (skip if not force_refresh)
        3. Group posts by subreddit
        4. For each subreddit (if >= 10 posts):
           - Run NLP analysis
           - Calculate post scores
           - Update raw_posts with NLP metadata and scores
           - Calculate ISC score
           - Extract forbidden patterns
           - Create/update community profile

        Args:
            campaign_id: Campaign UUID
            force_refresh: If True, re-analyze even if profiles exist
            progress_callback: Optional callback for progress updates

        Returns:
            AnalysisResult with posts_analyzed, profiles_created, errors

        Raises:
            AppError: If campaign not found or no posts to analyze
        """
        errors = []
        posts_analyzed = 0
        profiles_created = 0

        # Fetch all raw posts for campaign
        response = self.supabase.table("raw_posts").select(
            "id, raw_text, subreddit, comment_count, upvote_ratio, archetype, success_score"
        ).eq("campaign_id", campaign_id).execute()

        posts = response.data

        if not posts:
            raise AppError(
                ErrorCode.RESOURCE_NOT_FOUND,
                "No posts found for campaign",
                {"campaign_id": campaign_id}
            )

        # Check if profiles already exist (unless force_refresh)
        if not force_refresh:
            existing_profiles = self.supabase.table("community_profiles").select("id").eq(
                "campaign_id", campaign_id
            ).execute()

            if existing_profiles.data:
                return AnalysisResult(
                    status="exists",
                    posts_analyzed=0,
                    profiles_created=len(existing_profiles.data),
                    errors=["Profiles already exist. Use force_refresh=True to re-analyze."]
                )

        # Group posts by subreddit
        posts_by_subreddit = {}
        for post in posts:
            subreddit = post["subreddit"]
            if subreddit not in posts_by_subreddit:
                posts_by_subreddit[subreddit] = []
            posts_by_subreddit[subreddit].append(post)

        total_posts = len(posts)
        processed_posts = 0

        # Process each subreddit
        for subreddit, subreddit_posts in posts_by_subreddit.items():
            try:
                # Skip subreddits with < 10 posts
                if len(subreddit_posts) < 10:
                    errors.append(
                        f"Insufficient data for r/{subreddit}: {len(subreddit_posts)} posts (need 10+)"
                    )
                    continue

                # Step 1: NLP analysis
                texts = [post["raw_text"] for post in subreddit_posts]
                nlp_results = analyze_posts_batch(texts)

                # Emit progress
                if progress_callback:
                    progress_callback(AnalysisProgress(
                        state="nlp_analysis",
                        current=processed_posts + len(subreddit_posts),
                        total=total_posts,
                        status=f"Analyzing posts for r/{subreddit}...",
                        current_step="nlp_analysis"
                    ))

                # Step 2: Calculate community averages for scoring
                community_avg = self._calculate_community_averages(nlp_results)

                # Step 3: Score each post and update database
                scored_posts = []
                for i, post in enumerate(subreddit_posts):
                    nlp_result = nlp_results[i]

                    # Prepare post data for scoring
                    post_data = {
                        "raw_text": post["raw_text"],
                        "formality_score": nlp_result.get("formality_score"),
                        "avg_sentence_length": nlp_result.get("avg_sentence_length"),
                        "sentence_length_std": nlp_result.get("sentence_length_std"),
                    }

                    # Calculate score
                    score_breakdown = calculate_post_score(post_data, community_avg)

                    # Merge NLP + scoring data for storage
                    rhythm_metadata = {
                        **nlp_result,
                        **score_breakdown,
                    }

                    # Update raw_posts with NLP metadata and total_score
                    self.supabase.table("raw_posts").update({
                        "rhythm_metadata": rhythm_metadata,
                        "success_score": score_breakdown["total_score"]
                    }).eq("id", post["id"]).execute()

                    # Store for ISC calculation
                    scored_posts.append({
                        **post,
                        **nlp_result,
                        **score_breakdown,
                    })

                    posts_analyzed += 1
                    processed_posts += 1

                # Emit progress
                if progress_callback:
                    progress_callback(AnalysisProgress(
                        state="scoring",
                        current=processed_posts,
                        total=total_posts,
                        status=f"Scoring posts for r/{subreddit}...",
                        current_step="scoring"
                    ))

                # Step 4: Calculate ISC score
                try:
                    isc_score = calculate_isc_score(scored_posts)
                except ValueError as e:
                    errors.append(f"ISC calculation failed for r/{subreddit}: {str(e)}")
                    continue

                # Step 5: Extract forbidden patterns
                forbidden_result = extract_forbidden_patterns(texts)

                # Step 6: Calculate profile statistics
                profile_data = self._build_community_profile(
                    campaign_id=campaign_id,
                    subreddit=subreddit,
                    isc_score=isc_score,
                    nlp_results=nlp_results,
                    scored_posts=scored_posts,
                    forbidden_patterns=forbidden_result,
                )

                # Step 7: Upsert community profile
                self.supabase.table("community_profiles").upsert(
                    profile_data,
                    on_conflict="campaign_id,subreddit"
                ).execute()

                profiles_created += 1

                # Emit progress
                if progress_callback:
                    progress_callback(AnalysisProgress(
                        state="profiling",
                        current=processed_posts,
                        total=total_posts,
                        status=f"Created profile for r/{subreddit}",
                        current_step="profiling"
                    ))

            except Exception as e:
                errors.append(f"Error analyzing r/{subreddit}: {str(e)}")
                continue

        return AnalysisResult(
            status="complete",
            posts_analyzed=posts_analyzed,
            profiles_created=profiles_created,
            errors=errors
        )

    def _calculate_community_averages(self, nlp_results: List[dict]) -> dict:
        """Calculate community-level averages for scoring."""
        valid_formality = [r["formality_score"] for r in nlp_results if r["formality_score"] is not None]
        valid_sentence_length = [r["avg_sentence_length"] for r in nlp_results if r["avg_sentence_length"] is not None]
        valid_sentence_std = [r["sentence_length_std"] for r in nlp_results if r["sentence_length_std"] is not None]

        return {
            "formality_level": statistics.mean(valid_formality) if valid_formality else None,
            "avg_sentence_length": statistics.mean(valid_sentence_length) if valid_sentence_length else None,
            "sentence_length_std": statistics.mean(valid_sentence_std) if valid_sentence_std else None,
        }

    def _build_community_profile(
        self,
        campaign_id: str,
        subreddit: str,
        isc_score: float,
        nlp_results: List[dict],
        scored_posts: List[dict],
        forbidden_patterns: dict,
    ) -> dict:
        """Build community profile dictionary for database insertion."""
        # Calculate dominant tone
        tones = [r["tone"] for r in nlp_results if r.get("tone")]
        tone_counts = {}
        for tone in tones:
            tone_counts[tone] = tone_counts.get(tone, 0) + 1
        dominant_tone = max(tone_counts, key=tone_counts.get) if tone_counts else "neutral"

        # Calculate formality level
        valid_formality = [r["formality_score"] for r in nlp_results if r["formality_score"] is not None]
        formality_level = statistics.mean(valid_formality) if valid_formality else None

        # Calculate avg sentence length
        valid_sentence_length = [r["avg_sentence_length"] for r in nlp_results if r["avg_sentence_length"] is not None]
        avg_sentence_length = statistics.mean(valid_sentence_length) if valid_sentence_length else None

        # Top 5 success hooks (first sentence of top 5 posts by score)
        top_posts = sorted(scored_posts, key=lambda p: p.get("total_score", 0), reverse=True)[:5]
        top_success_hooks = []
        for post in top_posts:
            text = post.get("raw_text", "")
            # Extract first sentence (up to first period, question mark, or exclamation)
            first_sentence = text.split('.')[0].split('?')[0].split('!')[0].strip()
            if first_sentence and len(first_sentence) > 10:
                top_success_hooks.append(first_sentence[:200])  # Limit to 200 chars

        # Archetype distribution
        archetype_dist = {}
        for post in scored_posts:
            archetype = post.get("archetype", "Unclassified")
            archetype_dist[archetype] = archetype_dist.get(archetype, 0) + 1

        return {
            "campaign_id": campaign_id,
            "subreddit": subreddit,
            "isc_score": isc_score,
            "avg_sentence_length": avg_sentence_length,
            "dominant_tone": dominant_tone,
            "formality_level": formality_level,
            "top_success_hooks": top_success_hooks,
            "forbidden_patterns": forbidden_patterns,
            "archetype_distribution": archetype_dist,
            "sample_size": len(scored_posts),
        }

    async def get_community_profile(self, campaign_id: str, subreddit: str) -> dict:
        """
        Fetch single community profile by campaign + subreddit.

        Args:
            campaign_id: Campaign UUID
            subreddit: Subreddit name

        Returns:
            Community profile dict with isc_tier computed

        Raises:
            AppError: If profile not found
        """
        response = self.supabase.table("community_profiles").select("*").eq(
            "campaign_id", campaign_id
        ).eq("subreddit", subreddit).execute()

        if not response.data:
            raise AppError(
                ErrorCode.RESOURCE_NOT_FOUND,
                f"Community profile not found for r/{subreddit}",
                {"campaign_id": campaign_id, "subreddit": subreddit}
            )

        profile = response.data[0]
        profile["isc_tier"] = isc_to_tier(profile["isc_score"])

        return profile

    async def get_community_profiles(self, campaign_id: str) -> List[dict]:
        """
        Fetch all community profiles for a campaign.

        Args:
            campaign_id: Campaign UUID

        Returns:
            List of community profile dicts with isc_tier computed
        """
        response = self.supabase.table("community_profiles").select("*").eq(
            "campaign_id", campaign_id
        ).execute()

        profiles = response.data

        for profile in profiles:
            profile["isc_tier"] = isc_to_tier(profile["isc_score"])

        return profiles

    async def get_scoring_breakdown(self, post_id: str) -> dict:
        """
        Get detailed scoring breakdown for a single post.

        Args:
            post_id: Post UUID

        Returns:
            PostScoreBreakdown dict with penalty phrases for inline highlighting

        Raises:
            AppError: If post not found
        """
        response = self.supabase.table("raw_posts").select(
            "id, raw_text, rhythm_metadata, subreddit, campaign_id"
        ).eq("id", post_id).execute()

        if not response.data:
            raise AppError(
                ErrorCode.RESOURCE_NOT_FOUND,
                "Post not found",
                {"post_id": post_id}
            )

        post = response.data[0]
        rhythm_metadata = post.get("rhythm_metadata") or {}

        # Get penalty phrases from pattern checker
        penalty_phrases = check_post_penalties(post["raw_text"])

        # Merge with jargon/link penalties from stored metadata
        stored_penalties = rhythm_metadata.get("penalty_phrases", [])
        penalty_phrases.extend(stored_penalties)

        return {
            "post_id": post_id,
            "vulnerability_weight": rhythm_metadata.get("vulnerability_weight", 0),
            "rhythm_adherence": rhythm_metadata.get("rhythm_adherence", 0),
            "formality_match": rhythm_metadata.get("formality_match", 0),
            "marketing_jargon_penalty": rhythm_metadata.get("marketing_jargon_penalty", 0),
            "link_density_penalty": rhythm_metadata.get("link_density_penalty", 0),
            "total_score": rhythm_metadata.get("total_score", 0),
            "penalty_phrases": penalty_phrases,
        }

    async def get_analyzed_posts(
        self,
        campaign_id: str,
        subreddit: Optional[str] = None,
        sort_by: str = "total_score",
        sort_dir: str = "desc",
        page: int = 1,
        per_page: int = 20,
    ) -> dict:
        """
        Fetch analyzed posts with filtering and sorting.

        Args:
            campaign_id: Campaign UUID
            subreddit: Optional subreddit filter
            sort_by: Sort field (total_score, vulnerability_weight, rhythm_adherence, etc.)
            sort_dir: Sort direction (asc, desc)
            page: Page number (1-indexed)
            per_page: Items per page

        Returns:
            Dict with posts, total, page, per_page
        """
        query = self.supabase.table("raw_posts").select(
            "id, title, raw_text, subreddit, archetype, success_score, rhythm_metadata, collected_at",
            count="exact"
        ).eq("campaign_id", campaign_id)

        if subreddit:
            query = query.eq("subreddit", subreddit)

        # Apply sorting - note: Supabase sorts by column names, not JSONB fields
        # For now, sort by success_score which mirrors rhythm_metadata->total_score
        if sort_by == "total_score":
            query = query.order("success_score", desc=(sort_dir == "desc"))
        else:
            query = query.order("success_score", desc=True)

        # Pagination
        offset = (page - 1) * per_page
        query = query.range(offset, offset + per_page - 1)

        response = query.execute()

        return {
            "posts": response.data,
            "total": response.count,
            "page": page,
            "per_page": per_page,
        }

    async def get_forbidden_patterns(
        self,
        campaign_id: str,
        subreddit: Optional[str] = None,
    ) -> dict:
        """
        Aggregate forbidden patterns from community profiles.

        Args:
            campaign_id: Campaign UUID
            subreddit: Optional subreddit filter

        Returns:
            BlacklistResponse dict with patterns, total, categories
        """
        query = self.supabase.table("community_profiles").select(
            "subreddit, forbidden_patterns"
        ).eq("campaign_id", campaign_id)

        if subreddit:
            query = query.eq("subreddit", subreddit)

        response = query.execute()
        profiles = response.data

        # Aggregate patterns
        patterns_by_category = {}
        all_patterns = []

        for profile in profiles:
            forbidden = profile.get("forbidden_patterns", {})
            detected = forbidden.get("detected_patterns", [])

            for pattern in detected:
                category = pattern["category"]
                if category not in patterns_by_category:
                    patterns_by_category[category] = 0
                patterns_by_category[category] += pattern["match_count"]

                all_patterns.append({
                    "category": category,
                    "pattern": pattern["pattern_description"],
                    "subreddit": profile["subreddit"],
                    "is_system": True,  # System-detected patterns
                    "count": pattern["match_count"],
                })

        # Fetch custom user patterns from syntax_blacklist table
        # Note: This table will be created in a future migration, for now skip gracefully
        try:
            custom_response = self.supabase.table("syntax_blacklist").select(
                "id, category, pattern, subreddit"
            ).eq("campaign_id", campaign_id).eq("is_system", False).execute()

            for custom in custom_response.data:
                all_patterns.append({
                    "category": custom["category"],
                    "pattern": custom["pattern"],
                    "subreddit": custom.get("subreddit"),
                    "is_system": False,
                    "count": 0,  # Custom patterns don't have match counts yet
                })

                category = custom["category"]
                patterns_by_category[category] = patterns_by_category.get(category, 0) + 1
        except Exception:
            # Table doesn't exist yet, skip gracefully
            pass

        return {
            "patterns": all_patterns,
            "total": len(all_patterns),
            "categories": patterns_by_category,
        }

    async def add_custom_pattern(
        self,
        campaign_id: str,
        user_id: str,
        category: str,
        pattern: str,
        subreddit: Optional[str] = None,
    ) -> dict:
        """
        Add custom forbidden pattern.

        Args:
            campaign_id: Campaign UUID
            user_id: User UUID
            category: Pattern category
            pattern: Regex pattern or text phrase
            subreddit: Optional subreddit scope

        Returns:
            Created pattern entry

        Raises:
            AppError: If campaign not found or access denied
        """
        # Validate campaign ownership
        campaign_response = self.supabase.table("campaigns").select("id").eq(
            "id", campaign_id
        ).eq("user_id", user_id).execute()

        if not campaign_response.data:
            raise AppError(
                ErrorCode.RESOURCE_NOT_FOUND,
                "Campaign not found or access denied",
                {"campaign_id": campaign_id}
            )

        # Insert custom pattern
        # Note: This table will be created in a future migration
        try:
            pattern_data = {
                "campaign_id": campaign_id,
                "category": category,
                "pattern": pattern,
                "subreddit": subreddit,
                "is_system": False,
                "source": "user",
            }

            response = self.supabase.table("syntax_blacklist").insert(pattern_data).execute()
            return response.data[0]
        except Exception as e:
            raise AppError(
                ErrorCode.DATABASE_ERROR,
                f"Failed to add custom pattern: {str(e)}",
                {"campaign_id": campaign_id}
            )
