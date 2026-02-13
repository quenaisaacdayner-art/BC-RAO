"""
Generation service orchestrating the full draft generation pipeline.

Pipeline flow:
1. Load community profile from Supabase
2. Load syntax blacklist patterns
3. Run ISC gating validation
4. Build prompt via PromptBuilder
5. Call InferenceClient for LLM generation
6. Post-process: blacklist validation
7. Score draft (vulnerability + rhythm match)
8. Store in generated_drafts table
9. Return DraftResponse
"""

import logging
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from app.integrations.supabase_client import get_supabase_client
from app.inference.client import InferenceClient
from app.generation.prompt_builder import PromptBuilder
from app.generation.isc_gating import validate_generation_request
from app.generation.blacklist_validator import validate_draft, detect_ai_patterns
from app.analysis.nlp_pipeline import analyze_posts_batch
from app.analysis.scorers import calculate_post_score
from app.models.draft import (
    GenerateDraftRequest,
    DraftResponse,
    DraftListResponse,
    UpdateDraftRequest,
    RegenerateDraftRequest,
)
from app.utils.errors import AppError, ErrorCode

logger = logging.getLogger(__name__)


class GenerationService:
    """Service for generating, scoring, and managing drafts."""

    def __init__(self):
        self.supabase = get_supabase_client()
        self.prompt_builder = PromptBuilder()

    async def generate_draft(
        self,
        campaign_id: str,
        user_id: str,
        plan: str,
        request: GenerateDraftRequest,
    ) -> DraftResponse:
        """
        Generate a new draft using the full pipeline.

        Pipeline:
        1. Load community profile
        2. Load blacklist patterns
        3. ISC gating validation
        4. Build prompt
        5. LLM generation
        6. Blacklist validation
        7. NLP scoring
        8. Store draft
        9. Return response

        Args:
            campaign_id: Campaign UUID
            user_id: User UUID
            plan: User plan (trial, starter, growth)
            request: GenerateDraftRequest with subreddit, archetype, context, account_status

        Returns:
            DraftResponse with generated draft and scores

        Raises:
            AppError: If ISC gating blocks request or generation fails
        """
        # Step 1: Load community profile (optional - gracefully handle absence)
        profile = None
        isc_score = 5.0  # Default for generic prompts

        try:
            profile_response = self.supabase.table("community_profiles").select("*").eq(
                "campaign_id", campaign_id
            ).eq("subreddit", request.subreddit).execute()

            if profile_response.data:
                profile = profile_response.data[0]
                isc_score = profile.get("isc_score", 5.0)
            else:
                logger.warning(
                    f"No community profile found for r/{request.subreddit} in campaign {campaign_id}. Using generic defaults."
                )
        except Exception as e:
            logger.error(f"Error loading community profile: {e}")
            # Continue with generic defaults

        # Step 2: Load syntax blacklist patterns
        # Query uses actual DB column names from migrations 001+002:
        # forbidden_pattern (text), category (text), failure_type (enum), confidence (float)
        blacklist_patterns = []
        try:
            blacklist_response = self.supabase.table("syntax_blacklist").select(
                "forbidden_pattern, category, failure_type, confidence"
            ).eq("campaign_id", campaign_id).eq("subreddit", request.subreddit).execute()

            # Normalize column names for PromptBuilder compatibility
            blacklist_patterns = [
                {
                    "regex_pattern": p.get("forbidden_pattern", ""),
                    "category": p.get("category", p.get("failure_type", "Other")),
                    "pattern_description": p.get("forbidden_pattern", ""),
                }
                for p in blacklist_response.data
            ]
        except Exception as e:
            logger.error(f"Error loading blacklist patterns: {e}")
            # Continue without blacklist

        # Also inject community-detected forbidden patterns from profile
        if profile and profile.get("forbidden_patterns"):
            forbidden = profile.get("forbidden_patterns", {})
            detected = forbidden.get("detected_patterns", [])
            for pattern in detected:
                blacklist_patterns.append({
                    "regex_pattern": pattern.get("pattern_description", ""),
                    "category": pattern.get("category", "Community-detected"),
                    "pattern_description": pattern.get("pattern_description", ""),
                })

        # Step 3: ISC gating validation
        gating_result = validate_generation_request(
            subreddit=request.subreddit,
            archetype=request.archetype,
            account_status=request.account_status,
            isc_score=isc_score,
        )

        if not gating_result["allowed"]:
            raise AppError(
                code=ErrorCode.VALIDATION_ERROR,
                message=gating_result["reason"],
                details={
                    "forced_archetype": gating_result["forced_archetype"],
                    "constraints": gating_result["constraints"],
                },
                status_code=400
            )

        # Step 4: Build prompt
        prompts = self.prompt_builder.build_prompt(
            subreddit=request.subreddit,
            archetype=request.archetype,
            user_context=request.context or "",
            profile=profile,
            blacklist_patterns=blacklist_patterns,
            constraints=gating_result["constraints"],
        )

        # Step 5: LLM generation via InferenceClient
        inference_client = InferenceClient(task="generate_draft")

        # Send system and user prompts as separate messages for proper
        # persona adherence and instruction following via Chat Completions API
        try:
            inference_result = await inference_client.call(
                prompt=prompts["user"],
                system_prompt=prompts["system"],
                user_id=user_id,
                plan=plan,
                campaign_id=campaign_id,
            )

            generated_text = inference_result["content"]
            model_used = inference_result["model_used"]
            token_count = inference_result["token_count"]
            token_cost_usd = inference_result["cost_usd"]

        except AppError as e:
            # Re-raise AppError (budget limits, inference failures)
            raise
        except Exception as e:
            raise AppError(
                code=ErrorCode.INFERENCE_FAILED,
                message=f"Draft generation failed: {str(e)}",
                details={"subreddit": request.subreddit, "archetype": request.archetype},
                status_code=503
            )

        # Step 6: Post-generation blacklist validation
        blacklist_check = validate_draft(generated_text, blacklist_patterns)
        blacklist_violations = len(blacklist_check.violations)

        if blacklist_violations > 0:
            logger.warning(
                f"Generated draft has {blacklist_violations} blacklist violations for r/{request.subreddit}"
            )

        # Step 6b: AI-pattern detection (quality gate for humanization)
        ai_patterns = detect_ai_patterns(generated_text)
        if ai_patterns:
            ai_categories = [p["category"] for p in ai_patterns]
            logger.warning(
                f"Generated draft has {len(ai_patterns)} AI-tell patterns for r/{request.subreddit}: {ai_categories}"
            )
            # Count AI patterns as additional blacklist violations for scoring
            blacklist_violations += len(ai_patterns)

        # Step 7: Calculate scores via NLP pipeline
        try:
            # Run NLP analysis on generated text
            nlp_results = analyze_posts_batch([generated_text])
            nlp_result = nlp_results[0] if nlp_results else {}

            # Get community averages for scoring (if profile exists)
            community_avg = {}
            if profile:
                community_avg = {
                    "avg_sentence_length": profile.get("avg_sentence_length"),
                    "formality_level": profile.get("formality_level"),
                }

            # Calculate post score
            post_data = {
                "raw_text": generated_text,
                "formality_score": nlp_result.get("formality_score"),
                "avg_sentence_length": nlp_result.get("avg_sentence_length"),
                "sentence_length_std": nlp_result.get("sentence_length_std"),
            }

            score_breakdown = calculate_post_score(post_data, community_avg)

            vulnerability_score = score_breakdown["vulnerability_weight"]
            rhythm_match_score = score_breakdown["rhythm_adherence"]

        except Exception as e:
            logger.error(f"Error scoring generated draft: {e}")
            # Use default scores if scoring fails
            vulnerability_score = 5.0
            rhythm_match_score = 5.0

        # Step 8: Store draft in generated_drafts table
        # Auto-generate title from first line of body (DB requires NOT NULL)
        first_line = generated_text.strip().split("\n")[0].strip()
        auto_title = first_line[:80] + ("..." if len(first_line) > 80 else "")

        draft_data = {
            "campaign_id": campaign_id,
            "user_id": user_id,
            "subreddit": request.subreddit,
            "archetype": request.archetype,
            "title": auto_title,
            "body": generated_text,
            "vulnerability_score": vulnerability_score,
            "rhythm_match_score": rhythm_match_score,
            "blacklist_violations": blacklist_violations,
            "model_used": model_used,
            "token_count": token_count,
            "token_cost_usd": token_cost_usd,
            "generation_params": {
                "account_status": request.account_status,
                "user_context": request.context,
                "isc_score": isc_score,
                "constraints": gating_result["constraints"],
                **({"structural_template": prompts["metadata"]["structural_template"],
                    "ending_style": prompts["metadata"]["ending_style"]}
                   if prompts.get("metadata") else {}),
            },
            "status": "generated",
        }

        try:
            insert_response = self.supabase.table("generated_drafts").insert(draft_data).execute()
            stored_draft = insert_response.data[0]
        except Exception as e:
            raise AppError(
                code=ErrorCode.INTERNAL_ERROR,
                message=f"Failed to store generated draft: {str(e)}",
                details={"campaign_id": campaign_id},
                status_code=500
            )

        # Step 9: Return DraftResponse
        return DraftResponse(
            id=stored_draft["id"],
            campaign_id=stored_draft["campaign_id"],
            subreddit=stored_draft["subreddit"],
            archetype=stored_draft["archetype"],
            title=stored_draft.get("title"),
            body=stored_draft["body"],
            vulnerability_score=stored_draft["vulnerability_score"],
            rhythm_match_score=stored_draft["rhythm_match_score"],
            blacklist_violations=stored_draft["blacklist_violations"],
            model_used=stored_draft["model_used"],
            token_count=stored_draft["token_count"],
            token_cost_usd=stored_draft["token_cost_usd"],
            generation_params=stored_draft["generation_params"],
            status=stored_draft["status"],
            user_edits=stored_draft.get("user_edits"),
            created_at=stored_draft["created_at"],
            updated_at=stored_draft["updated_at"],
        )

    async def get_drafts(
        self,
        campaign_id: str,
        user_id: str,
        status: Optional[str] = None,
        subreddit: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> DraftListResponse:
        """
        Get drafts for a campaign with optional filtering.

        Args:
            campaign_id: Campaign UUID
            user_id: User UUID
            status: Optional status filter (generated, edited, approved, posted, discarded)
            subreddit: Optional subreddit filter
            limit: Max results to return
            offset: Pagination offset

        Returns:
            DraftListResponse with drafts and total count
        """
        query = self.supabase.table("generated_drafts").select(
            "*", count="exact"
        ).eq("campaign_id", campaign_id).eq("user_id", user_id)

        if status:
            # Support comma-separated status values (e.g. "generated,edited")
            statuses = [s.strip() for s in status.split(",")]
            if len(statuses) > 1:
                query = query.in_("status", statuses)
            else:
                query = query.eq("status", status)

        if subreddit:
            query = query.eq("subreddit", subreddit)

        query = query.order("created_at", desc=True).range(offset, offset + limit - 1)

        response = query.execute()

        drafts = [
            DraftResponse(
                id=d["id"],
                campaign_id=d["campaign_id"],
                subreddit=d["subreddit"],
                archetype=d["archetype"],
                title=d.get("title"),
                body=d["body"],
                vulnerability_score=d["vulnerability_score"],
                rhythm_match_score=d["rhythm_match_score"],
                blacklist_violations=d["blacklist_violations"],
                model_used=d["model_used"],
                token_count=d["token_count"],
                token_cost_usd=d["token_cost_usd"],
                generation_params=d["generation_params"],
                status=d["status"],
                user_edits=d.get("user_edits"),
                created_at=d["created_at"],
                updated_at=d["updated_at"],
            )
            for d in response.data
        ]

        return DraftListResponse(drafts=drafts, total=response.count)

    async def update_draft(
        self,
        draft_id: str,
        user_id: str,
        update: UpdateDraftRequest,
    ) -> DraftResponse:
        """
        Update draft status or user edits.

        Args:
            draft_id: Draft UUID
            user_id: User UUID
            update: UpdateDraftRequest with status and/or user_edits

        Returns:
            Updated DraftResponse

        Raises:
            AppError: If draft not found or access denied
        """
        # Verify ownership
        draft_response = self.supabase.table("generated_drafts").select("*").eq(
            "id", draft_id
        ).eq("user_id", user_id).execute()

        if not draft_response.data:
            raise AppError(
                code=ErrorCode.RESOURCE_NOT_FOUND,
                message="Draft not found or access denied",
                details={"draft_id": draft_id},
                status_code=404
            )

        # Build update data
        update_data = {}
        if update.status:
            update_data["status"] = update.status
        if update.user_edits is not None:
            update_data["user_edits"] = update.user_edits

        if not update_data:
            # No changes, return existing draft
            return DraftResponse(**draft_response.data[0])

        # Update draft
        update_response = self.supabase.table("generated_drafts").update(
            update_data
        ).eq("id", draft_id).execute()

        updated_draft = update_response.data[0]

        return DraftResponse(
            id=updated_draft["id"],
            campaign_id=updated_draft["campaign_id"],
            subreddit=updated_draft["subreddit"],
            archetype=updated_draft["archetype"],
            title=updated_draft.get("title"),
            body=updated_draft["body"],
            vulnerability_score=updated_draft["vulnerability_score"],
            rhythm_match_score=updated_draft["rhythm_match_score"],
            blacklist_violations=updated_draft["blacklist_violations"],
            model_used=updated_draft["model_used"],
            token_count=updated_draft["token_count"],
            token_cost_usd=updated_draft["token_cost_usd"],
            generation_params=updated_draft["generation_params"],
            status=updated_draft["status"],
            user_edits=updated_draft.get("user_edits"),
            created_at=updated_draft["created_at"],
            updated_at=updated_draft["updated_at"],
        )

    async def regenerate_draft(
        self,
        draft_id: str,
        user_id: str,
        plan: str,
        feedback: Optional[str] = None,
    ) -> DraftResponse:
        """
        Regenerate a draft with optional user feedback.

        Loads original draft parameters and appends feedback to context.

        Args:
            draft_id: Original draft UUID
            user_id: User UUID
            plan: User plan
            feedback: Optional user feedback to incorporate

        Returns:
            New DraftResponse with regenerated content

        Raises:
            AppError: If original draft not found
        """
        # Load original draft
        draft_response = self.supabase.table("generated_drafts").select("*").eq(
            "id", draft_id
        ).eq("user_id", user_id).execute()

        if not draft_response.data:
            raise AppError(
                code=ErrorCode.RESOURCE_NOT_FOUND,
                message="Original draft not found",
                details={"draft_id": draft_id},
                status_code=404
            )

        original_draft = draft_response.data[0]

        # Build new request with original params + feedback
        original_context = original_draft["generation_params"].get("user_context", "")
        new_context = original_context

        if feedback:
            new_context = f"{original_context}\n\nUser feedback: {feedback}"

        regenerate_request = GenerateDraftRequest(
            subreddit=original_draft["subreddit"],
            archetype=original_draft["archetype"],
            context=new_context,
            account_status=original_draft["generation_params"].get("account_status", "Established"),
        )

        # Generate new draft
        return await self.generate_draft(
            campaign_id=original_draft["campaign_id"],
            user_id=user_id,
            plan=plan,
            request=regenerate_request,
        )

    async def delete_draft(self, draft_id: str, user_id: str) -> None:
        """
        Delete a draft.

        Args:
            draft_id: Draft UUID
            user_id: User UUID

        Raises:
            AppError: If draft not found or access denied
        """
        # Verify ownership
        draft_response = self.supabase.table("generated_drafts").select("id").eq(
            "id", draft_id
        ).eq("user_id", user_id).execute()

        if not draft_response.data:
            raise AppError(
                code=ErrorCode.RESOURCE_NOT_FOUND,
                message="Draft not found or access denied",
                details={"draft_id": draft_id},
                status_code=404
            )

        # Delete draft
        self.supabase.table("generated_drafts").delete().eq("id", draft_id).execute()
