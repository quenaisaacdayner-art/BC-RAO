"""
Usage service for FastAPI endpoints.
Provides high-level interface for checking limits and retrieving usage stats.
"""
from app.inference.cost_tracker import CostTracker
from app.inference.router import COST_CAPS


class UsageService:
    """
    Service layer for usage tracking operations.
    Wraps CostTracker for use in FastAPI route handlers.
    """

    def __init__(self):
        self.cost_tracker = CostTracker()

    async def get_usage_for_user(self, user_id: str) -> dict:
        """
        Get usage summary for user.

        Args:
            user_id: User UUID

        Returns:
            dict with usage statistics
        """
        return await self.cost_tracker.get_usage_summary(user_id)

    async def check_action_limit(self, user_id: str, action_type: str, plan: str) -> bool:
        """
        Check if user can perform action based on plan limits.

        Args:
            user_id: User UUID
            action_type: Action type (collect, analyze, generate, monitor_register)
            plan: Plan name (trial, starter, growth)

        Returns:
            bool: True if action is allowed
        """
        can_proceed, remaining = await self.cost_tracker.check_budget(user_id, plan)
        return can_proceed
