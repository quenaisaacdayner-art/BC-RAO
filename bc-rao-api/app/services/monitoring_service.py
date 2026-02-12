"""
Monitoring service: Core monitoring operations for shadow_table management.

Handles post registration, status updates, audit classification, and dashboard stats.
"""

from datetime import datetime, timedelta
from uuid import UUID
from typing import Optional

from app.integrations.supabase_client import get_supabase_client
from app.models.monitoring import (
    RegisterPostResponse,
    ShadowEntry,
    MonitoringDashboardStats,
    parse_reddit_url
)


class MonitoringService:
    """
    Service for monitoring registered posts and tracking lifecycle status.
    """

    def __init__(self):
        """Initialize monitoring service with Supabase client."""
        self.supabase = get_supabase_client()

    def register_post(
        self,
        user_id: str,
        campaign_id: str,
        post_url: str
    ) -> RegisterPostResponse:
        """
        Register a new post for monitoring in shadow_table.

        Args:
            user_id: User UUID
            campaign_id: Campaign UUID
            post_url: Full Reddit post URL

        Returns:
            RegisterPostResponse with registration details

        Raises:
            ValueError: If URL is invalid or post already registered
        """
        # 1. Validate URL and extract subreddit + post_id
        parsed = parse_reddit_url(post_url)
        if not parsed:
            raise ValueError(f"Invalid Reddit URL format: {post_url}")

        subreddit = parsed["subreddit"]
        reddit_post_id = parsed["post_id"]

        # 2. Check if post already registered for this user
        existing = self.supabase.table("shadow_table").select("id").eq("post_url", post_url).eq("user_id", user_id).execute()
        if existing.data:
            raise ValueError(f"Post already registered: {post_url}")

        # 3. Infer draft mapping: query generated_drafts for most recent approved/posted draft
        # matching subreddit + user_id within 24 hours
        cutoff = datetime.utcnow() - timedelta(hours=24)
        draft_response = self.supabase.table("generated_drafts").select("id").eq(
            "user_id", user_id
        ).eq(
            "campaign_id", campaign_id
        ).eq(
            "subreddit", subreddit
        ).in_(
            "status", ["approved", "posted"]
        ).gte(
            "created_at", cutoff.isoformat()
        ).order(
            "created_at", desc=True
        ).limit(1).execute()

        draft_id = draft_response.data[0]["id"] if draft_response.data else None

        # 4. Get current ISC for campaign+subreddit from community_profiles table
        profile_response = self.supabase.table("community_profiles").select("isc_score").eq(
            "campaign_id", campaign_id
        ).eq(
            "subreddit", subreddit
        ).execute()

        # Default ISC if profile doesn't exist
        isc_at_post = profile_response.data[0]["isc_score"] if profile_response.data else 5.0

        # 5. Determine check_interval based on user's account_status from shadow_table history
        # Account status is derived from post history, not stored in profiles/subscriptions
        # For first-time users, default to "Established" (4h interval)
        account_status = "Established"
        check_interval_hours = 4

        recent_posts = self.supabase.table("shadow_table").select("account_status").eq(
            "user_id", user_id
        ).order("created_at", desc=True).limit(1).execute()

        if recent_posts.data:
            account_status = recent_posts.data[0].get("account_status", "Established")
            # Set check_interval based on account_status
            if account_status == "New":
                check_interval_hours = 1
            else:
                check_interval_hours = 4

        # 6. Insert into shadow_table
        now = datetime.utcnow()
        next_check_at = now + timedelta(hours=check_interval_hours)
        audit_due_at = now + timedelta(days=7)

        insert_data = {
            "draft_id": str(draft_id) if draft_id else None,
            "campaign_id": str(campaign_id),
            "user_id": str(user_id),
            "post_url": post_url,
            "subreddit": subreddit,
            "status_vida": "Ativo",
            "conversational_depth": 0,
            "isc_at_post": isc_at_post,
            "account_status": account_status,
            "check_interval_hours": check_interval_hours,
            "total_checks": 0,
            "last_check_at": now.isoformat(),
            "submitted_at": now.isoformat(),
            "audit_due_at": audit_due_at.isoformat()
        }

        result = self.supabase.table("shadow_table").insert(insert_data).execute()
        created_row = result.data[0]

        # 7. Return RegisterPostResponse
        return RegisterPostResponse(
            id=created_row["id"],
            post_url=post_url,
            subreddit=subreddit,
            reddit_post_id=reddit_post_id,
            status=created_row["status_vida"],
            isc_at_post=isc_at_post,
            check_interval_hours=check_interval_hours,
            next_check_at=next_check_at,
            created_at=created_row["created_at"]
        )

    def get_monitored_posts(
        self,
        user_id: str,
        campaign_id: str,
        status: Optional[str] = None
    ) -> list[ShadowEntry]:
        """
        Get list of monitored posts for a campaign.

        Args:
            user_id: User UUID
            campaign_id: Campaign UUID
            status: Optional status_vida filter

        Returns:
            List of ShadowEntry objects
        """
        query = self.supabase.table("shadow_table").select("*").eq(
            "user_id", user_id
        ).eq(
            "campaign_id", campaign_id
        )

        if status:
            query = query.eq("status_vida", status)

        query = query.order("submitted_at", desc=True)

        response = query.execute()
        return [ShadowEntry(**row) for row in response.data]

    def get_shadow_entry(self, shadow_id: str, user_id: str) -> ShadowEntry:
        """
        Get single shadow_table entry by ID.

        Args:
            shadow_id: Shadow entry UUID
            user_id: User UUID (for tenant isolation)

        Returns:
            ShadowEntry

        Raises:
            ValueError: If entry not found or user_id doesn't match
        """
        response = self.supabase.table("shadow_table").select("*").eq("id", shadow_id).execute()

        if not response.data:
            raise ValueError(f"Shadow entry not found: {shadow_id}")

        entry = response.data[0]
        if entry["user_id"] != user_id:
            raise ValueError(f"Access denied: shadow entry {shadow_id} does not belong to user {user_id}")

        return ShadowEntry(**entry)

    def get_dashboard_stats(
        self,
        user_id: str,
        campaign_id: str
    ) -> MonitoringDashboardStats:
        """
        Get monitoring dashboard statistics for a campaign.

        Args:
            user_id: User UUID
            campaign_id: Campaign UUID

        Returns:
            MonitoringDashboardStats with counts and recent alerts
        """
        # Get all shadow entries for this campaign
        response = self.supabase.table("shadow_table").select("status_vida").eq(
            "user_id", user_id
        ).eq(
            "campaign_id", campaign_id
        ).execute()

        entries = response.data
        total_count = len(entries)

        # Count by status
        active_count = sum(1 for e in entries if e["status_vida"] == "Ativo")
        removed_count = sum(1 for e in entries if e["status_vida"] == "Removido")
        shadowbanned_count = sum(1 for e in entries if e["status_vida"] == "Shadowbanned")

        # Calculate success rate (active posts / total)
        success_rate = (active_count / total_count * 100) if total_count > 0 else 0.0

        # Fetch recent alerts from email_alerts table (last 5)
        alerts_response = self.supabase.table("email_alerts").select(
            "id, alert_type, subject, sent_at"
        ).eq(
            "user_id", user_id
        ).order(
            "sent_at", desc=True
        ).limit(5).execute()

        recent_alerts = [
            {
                "id": str(alert["id"]),
                "type": alert["alert_type"],
                "subject": alert["subject"],
                "sent_at": alert["sent_at"]
            }
            for alert in alerts_response.data
        ]

        return MonitoringDashboardStats(
            active_count=active_count,
            removed_count=removed_count,
            shadowbanned_count=shadowbanned_count,
            total_count=total_count,
            success_rate=round(success_rate, 2),
            recent_alerts=recent_alerts
        )

    def update_post_status(
        self,
        shadow_id: str,
        new_status: str,
        check_result: Optional[dict] = None
    ) -> None:
        """
        Update shadow_table entry status and check metadata.

        Args:
            shadow_id: Shadow entry UUID
            new_status: New status_vida value
            check_result: Optional check result dict to append to metadata
        """
        # Fetch current entry to increment total_checks and get check_interval_hours
        current = self.supabase.table("shadow_table").select("total_checks, check_interval_hours").eq("id", shadow_id).execute()
        if not current.data:
            raise ValueError(f"Shadow entry not found: {shadow_id}")

        total_checks = current.data[0]["total_checks"] + 1
        check_interval_hours = current.data[0].get("check_interval_hours", 4)

        # Calculate next check time
        from datetime import timedelta
        next_check = datetime.utcnow() + timedelta(hours=check_interval_hours)

        update_data = {
            "status_vida": new_status,
            "total_checks": total_checks,
            "last_check_at": datetime.utcnow().isoformat(),
            "last_check_status": 200,  # HTTP status code placeholder
            "next_check_at": next_check.isoformat()
        }

        # TODO: Append check_result to JSONB metadata field if schema updated in future
        # For now, check_result is logged but not persisted to database

        self.supabase.table("shadow_table").update(update_data).eq("id", shadow_id).execute()

    def run_post_audit(
        self,
        shadow_id: str,
        upvotes: int = 0,
        comments: int = 0
    ) -> str:
        """
        Run 7-day audit and classify outcome.

        Classification rules:
        - Shadowbanned or Removido -> "Rejection"
        - Ativo + (upvotes >= 10 OR comments >= 3) -> "SocialSuccess"
        - Otherwise -> "Inertia"

        Args:
            shadow_id: Shadow entry UUID
            upvotes: Current upvote count
            comments: Current comment count

        Returns:
            Outcome string: "SocialSuccess", "Rejection", or "Inertia"
        """
        # Fetch current entry
        response = self.supabase.table("shadow_table").select("status_vida").eq("id", shadow_id).execute()
        if not response.data:
            raise ValueError(f"Shadow entry not found: {shadow_id}")

        status = response.data[0]["status_vida"]

        # Classify outcome
        if status in ["Shadowbanned", "Removido"]:
            outcome = "Rejection"
        elif status == "Ativo" and (upvotes >= 10 or comments >= 3):
            outcome = "SocialSuccess"
        else:
            outcome = "Inertia"

        # Update shadow_table with audit result
        now = datetime.utcnow()
        self.supabase.table("shadow_table").update({
            "audit_result": outcome,
            "audit_completed_at": now.isoformat(),
            "status_vida": "Auditado"  # Mark as audited
        }).eq("id", shadow_id).execute()

        return outcome
