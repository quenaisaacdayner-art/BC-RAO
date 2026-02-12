"""
Tests for cost tracking and budget enforcement.

Tests budget checks, zero cap edge case (BUG-A17 fix),
and usage recording to prevent plan limit overruns.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock
from app.inference.cost_tracker import CostTracker


@pytest.fixture
def mock_cost_caps():
    """Mock cost caps for different plans."""
    return {
        "trial": 1.0,
        "starter": 10.0,
        "growth": 50.0
    }


class TestBudgetChecking:
    """Test budget check logic."""

    @pytest.mark.asyncio
    @patch('app.inference.cost_tracker.get_supabase_client')
    @patch('app.inference.cost_tracker.COST_CAPS', {"trial": 1.0, "starter": 10.0, "growth": 50.0})
    async def test_under_budget_returns_true(self, mock_get_client, mock_supabase):
        """Budget check should return True when under cap."""
        # User has spent $0.50 of $1.00 trial cap
        mock_supabase.set_table_data("usage_tracking", [
            {"user_id": "user123", "cost_usd": 0.30, "created_at": datetime.utcnow().isoformat()},
            {"user_id": "user123", "cost_usd": 0.20, "created_at": datetime.utcnow().isoformat()}
        ])

        mock_get_client.return_value = mock_supabase

        tracker = CostTracker()
        can_proceed, remaining = await tracker.check_budget("user123", "trial")

        assert can_proceed is True
        assert remaining == 0.50

    @pytest.mark.asyncio
    @patch('app.inference.cost_tracker.get_supabase_client')
    @patch('app.inference.cost_tracker.COST_CAPS', {"trial": 1.0, "starter": 10.0, "growth": 50.0})
    async def test_over_budget_returns_false(self, mock_get_client, mock_supabase):
        """Budget check should return False when over cap."""
        # User has spent $1.50 of $1.00 trial cap
        mock_supabase.set_table_data("usage_tracking", [
            {"user_id": "user123", "cost_usd": 0.80, "created_at": datetime.utcnow().isoformat()},
            {"user_id": "user123", "cost_usd": 0.70, "created_at": datetime.utcnow().isoformat()}
        ])

        mock_get_client.return_value = mock_supabase

        tracker = CostTracker()
        can_proceed, remaining = await tracker.check_budget("user123", "trial")

        assert can_proceed is False
        assert remaining < 0

    @pytest.mark.asyncio
    @patch('app.inference.cost_tracker.get_supabase_client')
    @patch('app.inference.cost_tracker.COST_CAPS', {"trial": 1.0, "starter": 10.0, "growth": 50.0})
    async def test_exactly_at_budget_returns_false(self, mock_get_client, mock_supabase):
        """Budget check should return False when exactly at cap."""
        # User has spent exactly $1.00 of $1.00 trial cap
        mock_supabase.set_table_data("usage_tracking", [
            {"user_id": "user123", "cost_usd": 1.00, "created_at": datetime.utcnow().isoformat()}
        ])

        mock_get_client.return_value = mock_supabase

        tracker = CostTracker()
        can_proceed, remaining = await tracker.check_budget("user123", "trial")

        assert can_proceed is False
        assert remaining == 0.0

    @pytest.mark.asyncio
    @patch('app.inference.cost_tracker.get_supabase_client')
    @patch('app.inference.cost_tracker.COST_CAPS', {"trial": 1.0, "starter": 10.0, "growth": 50.0})
    async def test_zero_usage_returns_true(self, mock_get_client, mock_supabase):
        """Budget check with zero usage should return True."""
        # User has no usage records
        mock_supabase.set_table_data("usage_tracking", [])

        mock_get_client.return_value = mock_supabase

        tracker = CostTracker()
        can_proceed, remaining = await tracker.check_budget("user123", "trial")

        assert can_proceed is True
        assert remaining == 1.0  # Full trial cap remaining


class TestZeroCapEdgeCase:
    """Test BUG-A17 fix: zero cap should block all operations."""

    @pytest.mark.asyncio
    @patch('app.inference.cost_tracker.get_supabase_client')
    @patch('app.inference.cost_tracker.COST_CAPS', {"expired": 0.0})
    async def test_zero_cap_returns_false(self, mock_get_client, mock_supabase):
        """Zero cap should return False immediately (BUG-A17 fix)."""
        # Even with no usage, zero cap should block
        mock_supabase.set_table_data("usage_tracking", [])

        mock_get_client.return_value = mock_supabase

        tracker = CostTracker()
        can_proceed, remaining = await tracker.check_budget("user123", "expired")

        assert can_proceed is False
        assert remaining == 0.0

    @pytest.mark.asyncio
    @patch('app.inference.cost_tracker.get_supabase_client')
    @patch('app.inference.cost_tracker.COST_CAPS', {"expired": 0.0})
    async def test_zero_cap_with_usage_returns_false(self, mock_get_client, mock_supabase):
        """Zero cap with existing usage should also return False."""
        mock_supabase.set_table_data("usage_tracking", [
            {"user_id": "user123", "cost_usd": 0.50, "created_at": datetime.utcnow().isoformat()}
        ])

        mock_get_client.return_value = mock_supabase

        tracker = CostTracker()
        can_proceed, remaining = await tracker.check_budget("user123", "expired")

        assert can_proceed is False
        assert remaining == 0.0


class TestBillingCycleFiltering:
    """Test that budget checks only count current billing cycle."""

    @pytest.mark.asyncio
    @patch('app.inference.cost_tracker.get_supabase_client')
    @patch('app.inference.cost_tracker.COST_CAPS', {"trial": 1.0})
    async def test_only_current_month_counted(self, mock_get_client, mock_supabase):
        """Budget check should only count usage from current month."""
        now = datetime.utcnow()
        last_month = now - timedelta(days=35)

        # User spent $0.90 last month and $0.30 this month
        mock_supabase.set_table_data("usage_tracking", [
            {"user_id": "user123", "cost_usd": 0.90, "created_at": last_month.isoformat()},
            {"user_id": "user123", "cost_usd": 0.30, "created_at": now.isoformat()}
        ])

        mock_get_client.return_value = mock_supabase

        tracker = CostTracker()
        can_proceed, remaining = await tracker.check_budget("user123", "trial")

        # Should only count $0.30 from this month
        assert can_proceed is True
        assert remaining == pytest.approx(0.70, rel=0.01)

    @pytest.mark.asyncio
    @patch('app.inference.cost_tracker.get_supabase_client')
    @patch('app.inference.cost_tracker.COST_CAPS', {"trial": 1.0})
    async def test_billing_cycle_start_first_of_month(self, mock_get_client, mock_supabase):
        """Billing cycle should start on the 1st of the month."""
        # Mock current date as mid-month
        now = datetime(2024, 1, 15, 12, 0, 0)

        # Usage on Jan 1st should be counted
        jan_first = datetime(2024, 1, 1, 0, 0, 0)
        # Usage on Dec 31st should NOT be counted
        dec_last = datetime(2023, 12, 31, 23, 59, 59)

        mock_supabase.set_table_data("usage_tracking", [
            {"user_id": "user123", "cost_usd": 0.20, "created_at": jan_first.isoformat()},
            {"user_id": "user123", "cost_usd": 0.80, "created_at": dec_last.isoformat()}
        ])

        mock_get_client.return_value = mock_supabase

        tracker = CostTracker()

        with patch('app.inference.cost_tracker.datetime') as mock_datetime:
            mock_datetime.utcnow.return_value = now
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)

            can_proceed, remaining = await tracker.check_budget("user123", "trial")

        # Should only count $0.20 from Jan 1st
        assert can_proceed is True
        assert remaining == pytest.approx(0.80, rel=0.01)


class TestDifferentPlans:
    """Test budget checks across different plan tiers."""

    @pytest.mark.asyncio
    @patch('app.inference.cost_tracker.get_supabase_client')
    @patch('app.inference.cost_tracker.COST_CAPS', {"trial": 1.0, "starter": 10.0, "growth": 50.0})
    async def test_starter_plan_higher_cap(self, mock_get_client, mock_supabase):
        """Starter plan should have $10 cap."""
        mock_supabase.set_table_data("usage_tracking", [
            {"user_id": "user123", "cost_usd": 5.0, "created_at": datetime.utcnow().isoformat()}
        ])

        mock_get_client.return_value = mock_supabase

        tracker = CostTracker()
        can_proceed, remaining = await tracker.check_budget("user123", "starter")

        assert can_proceed is True
        assert remaining == 5.0

    @pytest.mark.asyncio
    @patch('app.inference.cost_tracker.get_supabase_client')
    @patch('app.inference.cost_tracker.COST_CAPS', {"trial": 1.0, "starter": 10.0, "growth": 50.0})
    async def test_growth_plan_highest_cap(self, mock_get_client, mock_supabase):
        """Growth plan should have $50 cap."""
        mock_supabase.set_table_data("usage_tracking", [
            {"user_id": "user123", "cost_usd": 30.0, "created_at": datetime.utcnow().isoformat()}
        ])

        mock_get_client.return_value = mock_supabase

        tracker = CostTracker()
        can_proceed, remaining = await tracker.check_budget("user123", "growth")

        assert can_proceed is True
        assert remaining == 20.0

    @pytest.mark.asyncio
    @patch('app.inference.cost_tracker.get_supabase_client')
    @patch('app.inference.cost_tracker.COST_CAPS', {"trial": 1.0, "starter": 10.0})
    async def test_unknown_plan_defaults_to_trial(self, mock_get_client, mock_supabase):
        """Unknown plan should default to trial cap."""
        mock_supabase.set_table_data("usage_tracking", [
            {"user_id": "user123", "cost_usd": 0.50, "created_at": datetime.utcnow().isoformat()}
        ])

        mock_get_client.return_value = mock_supabase

        tracker = CostTracker()
        can_proceed, remaining = await tracker.check_budget("user123", "nonexistent_plan")

        # Should use trial cap ($1.00)
        assert can_proceed is True
        assert remaining == 0.50


class TestUsageRecording:
    """Test usage recording functionality."""

    @pytest.mark.asyncio
    @patch('app.inference.cost_tracker.get_supabase_client')
    async def test_record_usage_with_campaign(self, mock_get_client, mock_supabase):
        """Should record usage with campaign_id."""
        mock_get_client.return_value = mock_supabase

        tracker = CostTracker()
        await tracker.record_usage(
            user_id="user123",
            action_type="generate",
            campaign_id="camp123",
            token_count=500,
            cost_usd=0.0075
        )

        # Verify insert was called (in real test, check mock.table().insert() call)

    @pytest.mark.asyncio
    @patch('app.inference.cost_tracker.get_supabase_client')
    async def test_record_usage_without_campaign(self, mock_get_client, mock_supabase):
        """Should record usage without campaign_id (optional)."""
        mock_get_client.return_value = mock_supabase

        tracker = CostTracker()
        await tracker.record_usage(
            user_id="user123",
            action_type="analyze",
            campaign_id=None,
            token_count=300,
            cost_usd=0.0045
        )

        # Should succeed without campaign_id


class TestUsageSummary:
    """Test usage summary generation."""

    @pytest.mark.asyncio
    @patch('app.inference.cost_tracker.get_supabase_client')
    @patch('app.inference.cost_tracker.COST_CAPS', {"trial": 1.0})
    async def test_usage_summary_breakdown_by_action(self, mock_get_client, mock_supabase):
        """Usage summary should break down costs by action type."""
        now = datetime.utcnow()

        mock_supabase.set_table_data("usage_tracking", [
            {"user_id": "user123", "action_type": "collect", "cost_usd": 0.10, "created_at": now.isoformat()},
            {"user_id": "user123", "action_type": "analyze", "cost_usd": 0.15, "created_at": now.isoformat()},
            {"user_id": "user123", "action_type": "generate", "cost_usd": 0.25, "created_at": now.isoformat()},
            {"user_id": "user123", "action_type": "generate", "cost_usd": 0.20, "created_at": now.isoformat()}
        ])
        mock_supabase.set_table_data("subscriptions", [
            {"user_id": "user123", "plan": "trial"}
        ])

        mock_get_client.return_value = mock_supabase

        tracker = CostTracker()
        summary = await tracker.get_usage_summary("user123")

        assert summary["total_cost"] == 0.70
        assert summary["action_breakdown"]["collect"] == 0.10
        assert summary["action_breakdown"]["analyze"] == 0.15
        assert summary["action_breakdown"]["generate"] == 0.45  # 0.25 + 0.20
        assert summary["remaining_budget"] == 0.30
        assert summary["plan_cap"] == 1.0

    @pytest.mark.asyncio
    @patch('app.inference.cost_tracker.get_supabase_client')
    @patch('app.inference.cost_tracker.COST_CAPS', {"trial": 1.0})
    async def test_usage_summary_no_subscription_defaults_trial(self, mock_get_client, mock_supabase):
        """Usage summary should default to trial if no subscription found."""
        mock_supabase.set_table_data("usage_tracking", [
            {"user_id": "user123", "action_type": "generate", "cost_usd": 0.50, "created_at": datetime.utcnow().isoformat()}
        ])
        mock_supabase.set_table_data("subscriptions", [])  # No subscription

        mock_get_client.return_value = mock_supabase

        tracker = CostTracker()
        summary = await tracker.get_usage_summary("user123")

        assert summary["plan_cap"] == 1.0  # Trial cap
        assert summary["remaining_budget"] == 0.50

    @pytest.mark.asyncio
    @patch('app.inference.cost_tracker.get_supabase_client')
    @patch('app.inference.cost_tracker.COST_CAPS', {"trial": 1.0})
    async def test_usage_summary_empty_usage(self, mock_get_client, mock_supabase):
        """Usage summary should handle zero usage."""
        mock_supabase.set_table_data("usage_tracking", [])
        mock_supabase.set_table_data("subscriptions", [
            {"user_id": "user123", "plan": "trial"}
        ])

        mock_get_client.return_value = mock_supabase

        tracker = CostTracker()
        summary = await tracker.get_usage_summary("user123")

        assert summary["total_cost"] == 0.0
        assert summary["action_breakdown"] == {}
        assert summary["remaining_budget"] == 1.0
        assert summary["plan_cap"] == 1.0


@pytest.mark.parametrize("spent,cap,expected_can_proceed", [
    (0.0, 1.0, True),
    (0.5, 1.0, True),
    (0.99, 1.0, True),
    (1.0, 1.0, False),
    (1.5, 1.0, False),
    (0.0, 0.0, False),  # BUG-A17: zero cap edge case
])
@pytest.mark.asyncio
async def test_budget_check_thresholds(spent, cap, expected_can_proceed, mock_supabase):
    """Test various budget threshold scenarios."""
    with patch('app.inference.cost_tracker.get_supabase_client') as mock_get_client:
        with patch('app.inference.cost_tracker.COST_CAPS', {"test_plan": cap}):
            mock_supabase.set_table_data("usage_tracking", [
                {"user_id": "user123", "cost_usd": spent, "created_at": datetime.utcnow().isoformat()}
            ])

            mock_get_client.return_value = mock_supabase

            tracker = CostTracker()
            can_proceed, remaining = await tracker.check_budget("user123", "test_plan")

            assert can_proceed is expected_can_proceed
            assert remaining == pytest.approx(cap - spent, rel=0.01)
