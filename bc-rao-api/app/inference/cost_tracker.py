"""
Cost tracking and budget enforcement for inference operations.
Prevents plan limit overruns by checking usage before each LLM call.
"""
from typing import Optional
from datetime import datetime, timedelta
from app.integrations.supabase_client import get_supabase_client
from app.inference.router import COST_CAPS


class CostTracker:
    """
    Tracks LLM usage costs and enforces plan caps.
    Queries usage_tracking table for real-time budget checking.
    """

    def __init__(self):
        self.supabase = get_supabase_client()

    async def check_budget(self, user_id: str, plan: str) -> tuple[bool, float]:
        """
        Check if user has budget remaining for this billing cycle.

        Args:
            user_id: User UUID
            plan: Plan name (trial, starter, growth)

        Returns:
            tuple[can_proceed: bool, remaining_budget: float]
        """
        # Get plan cap
        cap = COST_CAPS.get(plan, COST_CAPS["trial"])

        # Calculate billing cycle start (first day of current month)
        now = datetime.utcnow()
        billing_start = datetime(now.year, now.month, 1)

        # Query total spend in current billing cycle
        result = self.supabase.table("usage_tracking") \
            .select("cost_usd") \
            .eq("user_id", user_id) \
            .gte("created_at", billing_start.isoformat()) \
            .execute()

        # Calculate total cost
        total_cost = sum(row["cost_usd"] for row in result.data)
        remaining = cap - total_cost

        return (remaining > 0, remaining)

    async def record_usage(
        self,
        user_id: str,
        action_type: str,
        campaign_id: Optional[str],
        token_count: int,
        cost_usd: float
    ) -> None:
        """
        Record usage event in usage_tracking table.

        Args:
            user_id: User UUID
            action_type: One of: collect, analyze, generate, monitor_register
            campaign_id: Campaign UUID (optional)
            token_count: Number of tokens used
            cost_usd: Cost in USD
        """
        data = {
            "user_id": user_id,
            "action_type": action_type,
            "token_count": token_count,
            "cost_usd": cost_usd,
        }

        if campaign_id:
            data["campaign_id"] = campaign_id

        self.supabase.table("usage_tracking").insert(data).execute()

    async def get_usage_summary(self, user_id: str) -> dict:
        """
        Get usage summary for user in current billing cycle.

        Args:
            user_id: User UUID

        Returns:
            dict with total_cost, action_breakdown, remaining_budget
        """
        # Calculate billing cycle start
        now = datetime.utcnow()
        billing_start = datetime(now.year, now.month, 1)

        # Query all usage in current cycle
        result = self.supabase.table("usage_tracking") \
            .select("action_type, cost_usd") \
            .eq("user_id", user_id) \
            .gte("created_at", billing_start.isoformat()) \
            .execute()

        # Calculate breakdown
        total_cost = 0.0
        breakdown = {}

        for row in result.data:
            action = row["action_type"]
            cost = row["cost_usd"]
            total_cost += cost
            breakdown[action] = breakdown.get(action, 0.0) + cost

        # Get user's plan (assume trial if not found)
        user_result = self.supabase.table("subscriptions") \
            .select("plan") \
            .eq("user_id", user_id) \
            .maybe_single() \
            .execute()

        plan = user_result.data.get("plan", "trial") if user_result.data else "trial"
        cap = COST_CAPS.get(plan, COST_CAPS["trial"])
        remaining = cap - total_cost

        return {
            "total_cost": total_cost,
            "action_breakdown": breakdown,
            "remaining_budget": remaining,
            "plan_cap": cap,
        }
