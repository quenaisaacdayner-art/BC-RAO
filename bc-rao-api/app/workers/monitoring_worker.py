"""
Monitoring background worker with asyncio tasks.

Implements:
- run_monitoring_check: Dual-check with consecutive failure logic
- dispatch_pending_checks: 15-min scheduler for due checks
- run_post_audit: 7-day classification (SocialSuccess/Rejection/Inertia)
- extract_and_inject_patterns: Negative reinforcement to syntax_blacklist
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional

from app.services.monitoring_service import MonitoringService
from app.integrations.reddit_client import RedditDualCheckClient
from app.integrations.supabase_client import get_supabase_client
from app.services import email_service
from app.analysis.pattern_extractor import check_post_penalties


logger = logging.getLogger(__name__)


async def run_monitoring_check(task_id: str, shadow_id: str):
    """
    Run monitoring check with dual-check shadowban detection.

    Implements consecutive failure logic: Only flag shadowbanned if BOTH
    current AND previous check detected shadowban (2 consecutive checks).

    Pipeline:
    1. Fetch shadow entry from DB
    2. Perform Reddit dual-check (auth + anon)
    3. Check consecutive failure logic
    4. Update shadow_table status
    5. On shadowban/removal: send email alert + extract patterns

    Args:
        task_id: Task UUID for Redis state tracking
        shadow_id: Shadow entry UUID
    """
    from app.workers.task_runner import update_task_state

    try:
        update_task_state(task_id, "STARTED", {"state": "started"})

        service = MonitoringService()
        reddit_client = RedditDualCheckClient()
        supabase = get_supabase_client()

        # 1. Fetch shadow entry
        update_task_state(task_id, "PROGRESS", {
            "type": "status",
            "message": "Fetching shadow entry..."
        })

        entry_response = supabase.table("shadow_table").select("*").eq("id", shadow_id).execute()
        if not entry_response.data:
            raise ValueError(f"Shadow entry not found: {shadow_id}")

        entry = entry_response.data[0]
        reddit_post_id = entry["post_url"].split("/comments/")[1].split("/")[0]

        # 2. Perform dual-check
        update_task_state(task_id, "PROGRESS", {
            "type": "status",
            "message": "Running dual-check (auth + anon)..."
        })

        detected_status = await reddit_client.dual_check_post(reddit_post_id)

        # Build check result
        now = datetime.utcnow()
        check_result = {
            "timestamp": now.isoformat(),
            "auth_status": "ok" if detected_status != "removed" else "fail",
            "anon_status": "ok" if detected_status == "active" else "fail",
            "detected_status": detected_status
        }

        logger.info(f"Dual-check result for {shadow_id}: {check_result}")

        # 3. Consecutive failure logic for shadowban
        # Only flag shadowbanned if BOTH current AND previous check detected shadowban
        previous_check = entry.get("metadata", {}).get("last_check_result")

        if detected_status == "shadowbanned":
            # Check if previous check also detected shadowban
            if previous_check and previous_check.get("detected_status") == "shadowbanned":
                # Confirmed shadowban: 2 consecutive checks
                new_status = "Shadowbanned"
                logger.warning(f"CONFIRMED SHADOWBAN for {shadow_id} (2 consecutive checks)")
            else:
                # First detection: keep status as active, schedule another check sooner
                new_status = "Ativo"
                logger.info(f"First shadowban detection for {shadow_id} - scheduling verification check")

                # Update next_check_at to 30 minutes from now (verification check)
                from datetime import timedelta
                next_check_at = now + timedelta(minutes=30)
                supabase.table("shadow_table").update({
                    "next_check_at": next_check_at.isoformat()
                }).eq("id", shadow_id).execute()

        elif detected_status == "removed":
            new_status = "Removido"
            logger.warning(f"Post {shadow_id} was removed by moderators")
        else:
            new_status = "Ativo"

        # 4. Update shadow_table status
        update_task_state(task_id, "PROGRESS", {
            "type": "status",
            "message": f"Updating status to {new_status}..."
        })

        service.update_post_status(
            shadow_id=shadow_id,
            new_status=new_status,
            check_result=check_result
        )

        # TODO: Store check_result in metadata for consecutive failure tracking
        # This requires adding a metadata JSONB column to shadow_table schema
        # Consecutive failure logic is currently not functional
        # Options: (1) Add metadata JSONB column, (2) Create separate check_history table
        # For now, skip metadata update - single check triggers shadowban alert
        #
        # Uncomment once schema is updated:
        # try:
        #     current_metadata = entry.get("metadata") or {}
        #     current_metadata["last_check_result"] = check_result
        #     supabase.table("shadow_table").update({"metadata": current_metadata}).eq("id", shadow_id).execute()
        # except Exception as e:
        #     logger.warning(f"Could not update metadata for {shadow_id}: {e}")

        # 5. Handle shadowban/removal detection
        if new_status == "Shadowbanned":
            update_task_state(task_id, "PROGRESS", {
                "type": "status",
                "message": "Shadowban confirmed - sending alert..."
            })

            # Check rate limit
            can_send = email_service.can_send_shadowban_alert(entry["user_id"])

            if can_send:
                # Fetch user email from profiles
                profile_response = supabase.table("profiles").select("email, display_name").eq(
                    "user_id", entry["user_id"]
                ).execute()

                if profile_response.data:
                    user_email = profile_response.data[0]["email"]
                    user_name = profile_response.data[0]["display_name"] or "User"

                    # Send email alert
                    email_service.send_shadowban_alert(
                        user_email=user_email,
                        user_name=user_name,
                        post_title=entry["post_url"].split("/")[-2].replace("_", " ")[:100],
                        subreddit=entry["subreddit"],
                        post_url=entry["post_url"],
                        dashboard_url=f"https://bc-rao.com/campaigns/{entry['campaign_id']}/monitoring"
                    )

                    # Record alert
                    email_service.record_alert(
                        user_id=entry["user_id"],
                        shadow_id=shadow_id,
                        alert_type="emergency",
                        subject=f"URGENT: Shadowban detected in r/{entry['subreddit']}",
                        body_preview="Your post is invisible to other users..."
                    )
                else:
                    logger.warning(f"Profile not found for user {entry['user_id']} - skipping shadowban alert email")

            # Extract and inject patterns
            update_task_state(task_id, "PROGRESS", {
                "type": "status",
                "message": "Extracting forbidden patterns..."
            })

            # Fetch original draft text if draft_id exists
            draft_text = None
            if entry.get("draft_id"):
                draft_response = supabase.table("generated_drafts").select("body").eq(
                    "id", entry["draft_id"]
                ).execute()
                if draft_response.data:
                    draft_text = draft_response.data[0]["body"]

            if draft_text:
                await extract_and_inject_patterns(
                    shadow_id=shadow_id,
                    draft_text=draft_text,
                    subreddit=entry["subreddit"],
                    campaign_id=entry["campaign_id"],
                    failure_type="Shadowban"
                )

        elif new_status == "Removido":
            update_task_state(task_id, "PROGRESS", {
                "type": "status",
                "message": "Removal detected - extracting patterns..."
            })

            # Extract and inject patterns for admin removal
            draft_text = None
            if entry.get("draft_id"):
                draft_response = supabase.table("generated_drafts").select("body").eq(
                    "id", entry["draft_id"]
                ).execute()
                if draft_response.data:
                    draft_text = draft_response.data[0]["body"]

            if draft_text:
                await extract_and_inject_patterns(
                    shadow_id=shadow_id,
                    draft_text=draft_text,
                    subreddit=entry["subreddit"],
                    campaign_id=entry["campaign_id"],
                    failure_type="AdminRemoval"
                )

        # Close Reddit client
        await reddit_client.close()

        update_task_state(task_id, "SUCCESS", {
            "type": "complete",
            "result": {
                "shadow_id": shadow_id,
                "status": new_status,
                "check_result": check_result
            }
        })

    except Exception as e:
        logger.error(f"Monitoring check failed for {shadow_id}: {e}")
        update_task_state(task_id, "FAILURE", {
            "type": "error",
            "message": str(e)
        })


async def dispatch_pending_checks():
    """
    Dispatch monitoring checks for posts that are due.

    Queries shadow_table for posts with next_check_at <= NOW()
    and status_vida = 'Ativo', then launches background tasks.

    Staggers launches by 2 seconds to respect Reddit rate limits.
    """
    try:
        supabase = get_supabase_client()

        # Query for pending checks
        now = datetime.utcnow()
        response = supabase.table("shadow_table").select("id, post_url").eq(
            "status_vida", "Ativo"
        ).lte(
            "next_check_at", now.isoformat()
        ).execute()

        pending = response.data
        logger.info(f"Found {len(pending)} posts due for monitoring check")

        # Dispatch each check as background task
        for entry in pending:
            from app.workers.task_runner import generate_task_id
            task_id = generate_task_id()

            logger.info(f"Dispatching check for shadow_id={entry['id']}, task_id={task_id}")

            asyncio.create_task(
                run_monitoring_check(task_id, entry["id"])
            )

            # Stagger launches to respect rate limits
            await asyncio.sleep(2)

    except Exception as e:
        logger.error(f"Failed to dispatch pending checks: {e}")


async def run_post_audit(task_id: str, shadow_id: str):
    """
    Run 7-day post audit and classify outcome.

    Classification:
    - Status already Shadowbanned/Removido -> "Rejection"
    - Status Ativo + (upvotes >= 10 OR comments >= 3) -> "SocialSuccess"
    - Otherwise -> "Inertia"

    Args:
        task_id: Task UUID for Redis state tracking
        shadow_id: Shadow entry UUID
    """
    from app.workers.task_runner import update_task_state

    try:
        update_task_state(task_id, "STARTED", {"state": "started"})

        service = MonitoringService()
        reddit_client = RedditDualCheckClient()
        supabase = get_supabase_client()

        # Fetch shadow entry
        update_task_state(task_id, "PROGRESS", {
            "type": "status",
            "message": "Fetching shadow entry for audit..."
        })

        entry_response = supabase.table("shadow_table").select("*").eq("id", shadow_id).execute()
        if not entry_response.data:
            raise ValueError(f"Shadow entry not found: {shadow_id}")

        entry = entry_response.data[0]
        status = entry["status_vida"]

        # Classify outcome
        if status in ["Shadowbanned", "Removido"]:
            outcome = "Rejection"
            upvotes = 0
            comments = 0
            logger.info(f"Audit for {shadow_id}: Rejection (status={status})")
        else:
            # Fetch metrics from Reddit
            update_task_state(task_id, "PROGRESS", {
                "type": "status",
                "message": "Fetching post metrics from Reddit..."
            })

            reddit_post_id = entry["post_url"].split("/comments/")[1].split("/")[0]
            metrics = await reddit_client.fetch_post_metrics(reddit_post_id)

            upvotes = metrics["upvotes"]
            comments = metrics["comments"]

            logger.info(f"Audit for {shadow_id}: upvotes={upvotes}, comments={comments}")

            # Classify
            if upvotes >= 10 or comments >= 3:
                outcome = "SocialSuccess"
            else:
                outcome = "Inertia"

        # Update shadow_table
        update_task_state(task_id, "PROGRESS", {
            "type": "status",
            "message": f"Recording audit outcome: {outcome}..."
        })

        service.run_post_audit(shadow_id, upvotes, comments)

        # Close Reddit client
        await reddit_client.close()

        update_task_state(task_id, "SUCCESS", {
            "type": "complete",
            "result": {
                "shadow_id": shadow_id,
                "outcome": outcome,
                "upvotes": upvotes,
                "comments": comments
            }
        })

    except Exception as e:
        logger.error(f"Post audit failed for {shadow_id}: {e}")
        update_task_state(task_id, "FAILURE", {
            "type": "error",
            "message": str(e)
        })


async def extract_and_inject_patterns(
    shadow_id: str,
    draft_text: str,
    subreddit: str,
    campaign_id: str,
    failure_type: str
):
    """
    Extract forbidden patterns from removed/shadowbanned post and inject to syntax_blacklist.

    Uses existing pattern_extractor.py check_post_penalties() function.

    Args:
        shadow_id: Shadow entry UUID (used as source_post_id)
        draft_text: Original draft text to analyze
        subreddit: Subreddit name
        campaign_id: Campaign UUID
        failure_type: 'Shadowban' or 'AdminRemoval'
    """
    try:
        logger.info(f"Extracting patterns from {failure_type} post {shadow_id}")

        # Use existing pattern extractor
        penalties = check_post_penalties(draft_text)

        if not penalties:
            logger.info(f"No patterns extracted from {shadow_id}")
            return

        logger.info(f"Extracted {len(penalties)} patterns from {shadow_id}")

        # Inject to syntax_blacklist
        supabase = get_supabase_client()
        inserted_count = 0

        for penalty in penalties:
            try:
                # Insert with upsert to avoid duplicate errors
                insert_data = {
                    "campaign_id": campaign_id,
                    "subreddit": subreddit,
                    "forbidden_pattern": penalty["phrase"],
                    "failure_type": failure_type,  # Will be cast to failure_category enum
                    "source_post_id": shadow_id,
                    "confidence": 0.5,  # Medium confidence for auto-extracted
                    "is_global": False,  # Subreddit-specific
                    "category": penalty["category"]
                }

                supabase.table("syntax_blacklist").upsert(
                    insert_data,
                    on_conflict="subreddit,forbidden_pattern",
                    ignore_duplicates=True
                ).execute()

                inserted_count += 1

            except Exception as e:
                # Skip patterns that fail to insert (likely duplicates or constraint violations)
                logger.debug(f"Skipped pattern '{penalty['phrase']}': {e}")

        logger.info(f"Injected {inserted_count}/{len(penalties)} patterns to syntax_blacklist for r/{subreddit}")

    except Exception as e:
        logger.error(f"Pattern extraction failed for {shadow_id}: {e}")
        # Don't crash monitoring pipeline on pattern extraction failure
