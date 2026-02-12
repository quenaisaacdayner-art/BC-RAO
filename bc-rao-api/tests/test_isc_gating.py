"""
Tests for ISC gating logic - the most critical safety feature.

ISC gating prevents risky content from being posted to high-sensitivity
communities by enforcing archetype restrictions and link policies.
"""
import pytest
from app.generation.isc_gating import validate_generation_request


class TestISCGatingBasics:
    """Test basic ISC gating rules for established accounts."""

    def test_low_isc_allows_all_archetypes(self):
        """ISC <= 7.5 should allow all archetypes."""
        result = validate_generation_request(
            subreddit="python",
            archetype="Journey",
            account_status="Established",
            isc_score=5.0
        )
        assert result["allowed"] is True
        assert result["forced_archetype"] is None
        assert result["reason"] is None

    def test_high_isc_blocks_journey(self):
        """ISC > 7.5 should block Journey archetype and force Feedback."""
        result = validate_generation_request(
            subreddit="antiwork",
            archetype="Journey",
            account_status="Established",
            isc_score=8.5
        )
        assert result["allowed"] is False
        assert result["forced_archetype"] == "Feedback"
        assert "ISC 8.5 > 7.5" in result["reason"]
        assert "Only Feedback archetype allowed" in result["reason"]

    def test_high_isc_blocks_problemsolution(self):
        """ISC > 7.5 should block ProblemSolution archetype and force Feedback."""
        result = validate_generation_request(
            subreddit="depression",
            archetype="ProblemSolution",
            account_status="Established",
            isc_score=9.0
        )
        assert result["allowed"] is False
        assert result["forced_archetype"] == "Feedback"
        assert "ISC 9.0 > 7.5" in result["reason"]

    def test_high_isc_allows_feedback(self):
        """ISC > 7.5 should allow Feedback archetype."""
        result = validate_generation_request(
            subreddit="antiwork",
            archetype="Feedback",
            account_status="Established",
            isc_score=8.5
        )
        assert result["allowed"] is True
        assert result["forced_archetype"] is None
        assert result["reason"] is None

    def test_isc_exactly_7_5_allows_all(self):
        """ISC exactly 7.5 (boundary case) should allow all archetypes."""
        result = validate_generation_request(
            subreddit="python",
            archetype="Journey",
            account_status="Established",
            isc_score=7.5
        )
        assert result["allowed"] is True
        assert result["forced_archetype"] is None


class TestISCGatingConstraints:
    """Test that ISC gating adds appropriate constraints to generation."""

    def test_high_isc_forces_zero_links(self):
        """ISC > 7.5 should enforce ZERO links constraint."""
        result = validate_generation_request(
            subreddit="antiwork",
            archetype="Feedback",
            account_status="Established",
            isc_score=8.5
        )
        assert result["allowed"] is True
        # Check for zero links constraint
        zero_links = any("ZERO links" in c for c in result["constraints"])
        assert zero_links is True

    def test_high_isc_requires_vulnerability(self):
        """ISC > 7.5 should require maximum vulnerability."""
        result = validate_generation_request(
            subreddit="depression",
            archetype="Feedback",
            account_status="Established",
            isc_score=9.0
        )
        vulnerability_constraint = any(
            "vulnerability" in c.lower() for c in result["constraints"]
        )
        assert vulnerability_constraint is True

    def test_low_isc_standard_constraints(self):
        """ISC <= 3.0 should add low sensitivity note."""
        result = validate_generation_request(
            subreddit="entrepreneur",
            archetype="ProblemSolution",
            account_status="Established",
            isc_score=2.5
        )
        low_sensitivity = any(
            "low sensitivity" in c.lower() for c in result["constraints"]
        )
        assert low_sensitivity is True

    def test_medium_isc_elevated_sensitivity(self):
        """ISC > 5.0 (but <= 7.5) should note elevated sensitivity."""
        result = validate_generation_request(
            subreddit="python",
            archetype="Journey",
            account_status="Established",
            isc_score=6.5
        )
        elevated = any(
            "elevated sensitivity" in c.lower() for c in result["constraints"]
        )
        assert elevated is True


class TestNewAccountWarmup:
    """Test warm-up mode for new accounts."""

    def test_new_account_forces_feedback(self):
        """New accounts must use Feedback archetype only."""
        result = validate_generation_request(
            subreddit="python",
            archetype="Journey",
            account_status="New",
            isc_score=5.0
        )
        assert result["allowed"] is False
        assert result["forced_archetype"] == "Feedback"
        assert "warm-up mode" in result["reason"]

    def test_new_account_feedback_allowed(self):
        """New accounts can use Feedback archetype."""
        result = validate_generation_request(
            subreddit="python",
            archetype="Feedback",
            account_status="New",
            isc_score=5.0
        )
        assert result["allowed"] is True
        assert result["forced_archetype"] is None

    def test_new_account_zero_links_enforced(self):
        """New accounts must have ZERO links."""
        result = validate_generation_request(
            subreddit="python",
            archetype="Feedback",
            account_status="New",
            isc_score=5.0
        )
        zero_links = any("ZERO links" in c for c in result["constraints"])
        assert zero_links is True

    def test_new_account_vulnerability_required(self):
        """New accounts must show maximum vulnerability."""
        result = validate_generation_request(
            subreddit="python",
            archetype="Feedback",
            account_status="New",
            isc_score=5.0
        )
        vulnerability = any(
            "vulnerability" in c.lower() and "maximum" in c.lower()
            for c in result["constraints"]
        )
        assert vulnerability is True

    def test_new_account_warmup_marker(self):
        """New accounts should have warm-up mode marker in constraints."""
        result = validate_generation_request(
            subreddit="python",
            archetype="Feedback",
            account_status="New",
            isc_score=5.0
        )
        warmup = any("warm-up mode" in c.lower() for c in result["constraints"])
        assert warmup is True


class TestArchetypeConstraints:
    """Test archetype-specific constraints are applied."""

    def test_problemsolution_90_10_ratio(self):
        """ProblemSolution archetype should enforce 90% pain / 10% solution."""
        result = validate_generation_request(
            subreddit="python",
            archetype="ProblemSolution",
            account_status="Established",
            isc_score=5.0
        )
        ratio_constraint = any(
            "90% pain / 10% solution" in c for c in result["constraints"]
        )
        assert ratio_constraint is True

    def test_problemsolution_no_greetings(self):
        """ProblemSolution should prohibit greetings."""
        result = validate_generation_request(
            subreddit="python",
            archetype="ProblemSolution",
            account_status="Established",
            isc_score=5.0
        )
        no_greetings = any("NO greetings" in c for c in result["constraints"])
        assert no_greetings is True

    def test_journey_requires_metrics(self):
        """Journey archetype should require concrete numbers and metrics."""
        result = validate_generation_request(
            subreddit="python",
            archetype="Journey",
            account_status="Established",
            isc_score=5.0
        )
        metrics = any(
            "numbers and metrics" in c.lower() for c in result["constraints"]
        )
        assert metrics is True

    def test_journey_technical_diary_style(self):
        """Journey archetype should use technical diary style."""
        result = validate_generation_request(
            subreddit="python",
            archetype="Journey",
            account_status="Established",
            isc_score=5.0
        )
        diary_style = any(
            "technical diary" in c.lower() for c in result["constraints"]
        )
        assert diary_style is True

    def test_feedback_inverts_authority(self):
        """Feedback archetype should invert authority pattern."""
        result = validate_generation_request(
            subreddit="python",
            archetype="Feedback",
            account_status="Established",
            isc_score=5.0
        )
        invert_authority = any(
            "invert authority" in c.lower() for c in result["constraints"]
        )
        assert invert_authority is True

    def test_feedback_controlled_imperfection(self):
        """Feedback archetype should show controlled imperfection."""
        result = validate_generation_request(
            subreddit="python",
            archetype="Feedback",
            account_status="Established",
            isc_score=5.0
        )
        imperfection = any(
            "controlled imperfection" in c.lower() for c in result["constraints"]
        )
        assert imperfection is True


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_isc_boundary_7_5_vs_7_6(self):
        """Test the exact boundary between allowed and blocked."""
        # 7.5 should allow
        result_allowed = validate_generation_request(
            subreddit="python",
            archetype="Journey",
            account_status="Established",
            isc_score=7.5
        )
        assert result_allowed["allowed"] is True

        # 7.6 should block
        result_blocked = validate_generation_request(
            subreddit="antiwork",
            archetype="Journey",
            account_status="Established",
            isc_score=7.6
        )
        assert result_blocked["allowed"] is False
        assert result_blocked["forced_archetype"] == "Feedback"

    def test_isc_score_maximum(self):
        """Test with maximum ISC score (10.0)."""
        result = validate_generation_request(
            subreddit="depression",
            archetype="Journey",
            account_status="Established",
            isc_score=10.0
        )
        assert result["allowed"] is False
        assert result["forced_archetype"] == "Feedback"
        assert "ISC 10.0 > 7.5" in result["reason"]

    def test_isc_score_minimum(self):
        """Test with minimum ISC score (1.0)."""
        result = validate_generation_request(
            subreddit="entrepreneur",
            archetype="ProblemSolution",
            account_status="Established",
            isc_score=1.0
        )
        assert result["allowed"] is True
        # Should have low sensitivity note
        low_sensitivity = any(
            "low sensitivity" in c.lower() for c in result["constraints"]
        )
        assert low_sensitivity is True

    def test_warming_up_status_standard_rules(self):
        """WarmingUp status should follow standard ISC rules (not New rules)."""
        result = validate_generation_request(
            subreddit="python",
            archetype="Journey",
            account_status="WarmingUp",
            isc_score=5.0
        )
        assert result["allowed"] is True
        assert result["forced_archetype"] is None
        # Should NOT have warm-up mode constraint
        warmup = any("warm-up mode" in c.lower() for c in result["constraints"])
        assert warmup is False

    def test_established_high_isc_combination(self):
        """Established account + high ISC should still enforce restrictions."""
        result = validate_generation_request(
            subreddit="antiwork",
            archetype="Journey",
            account_status="Established",
            isc_score=9.0
        )
        assert result["allowed"] is False
        assert result["forced_archetype"] == "Feedback"
        # Account status doesn't override ISC restrictions


@pytest.mark.parametrize("archetype", ["Journey", "ProblemSolution", "Feedback"])
def test_all_archetypes_low_isc(archetype):
    """All archetypes should be allowed with low ISC."""
    result = validate_generation_request(
        subreddit="python",
        archetype=archetype,
        account_status="Established",
        isc_score=5.0
    )
    assert result["allowed"] is True
    assert result["forced_archetype"] is None


@pytest.mark.parametrize("archetype", ["Journey", "ProblemSolution"])
def test_risky_archetypes_blocked_high_isc(archetype):
    """Journey and ProblemSolution should be blocked with high ISC."""
    result = validate_generation_request(
        subreddit="antiwork",
        archetype=archetype,
        account_status="Established",
        isc_score=8.5
    )
    assert result["allowed"] is False
    assert result["forced_archetype"] == "Feedback"


@pytest.mark.parametrize("isc_score", [8.0, 8.5, 9.0, 9.5, 10.0])
def test_high_isc_values_all_block_risky(isc_score):
    """All ISC values > 7.5 should block risky archetypes."""
    result = validate_generation_request(
        subreddit="sensitive_sub",
        archetype="Journey",
        account_status="Established",
        isc_score=isc_score
    )
    assert result["allowed"] is False
    assert result["forced_archetype"] == "Feedback"
