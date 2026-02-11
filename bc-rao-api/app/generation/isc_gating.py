"""
ISC gating logic and account status decision tree.

Implements the 5-branch decision tree from system spec Section 14:
1. New accounts: Warm-up mode (Feedback only, no links, max vulnerability)
2. High ISC (> 7.5): Block risky archetypes, force Feedback with zero links
3. ProblemSolution: 90% pain / 10% solution, no greetings, product mention only in last 10%
4. Journey: Technical diary style, milestones with numbers, metrics required
5. Feedback: Invert authority, ask community to find flaws, controlled imperfection
"""

from typing import Optional


def validate_generation_request(
    subreddit: str,
    archetype: str,
    account_status: str,
    isc_score: float
) -> dict:
    """
    Validate generation request against ISC gating rules and account status decision tree.

    Args:
        subreddit: Target subreddit name
        archetype: Requested archetype (Journey, ProblemSolution, Feedback)
        account_status: Account status (New, WarmingUp, Established)
        isc_score: Community ISC score (1.0 to 10.0)

    Returns:
        dict with:
            - allowed (bool): Whether generation is allowed
            - forced_archetype (Optional[str]): Forced archetype if request blocked
            - constraints (list[str]): Generation constraints to inject into prompt
            - reason (Optional[str]): Reason if blocked

    Examples:
        >>> validate_generation_request("python", "Journey", "New", 5.0)
        {"allowed": False, "forced_archetype": "Feedback", "constraints": [...], "reason": "..."}

        >>> validate_generation_request("python", "Feedback", "Established", 8.5)
        {"allowed": True, "forced_archetype": None, "constraints": [...], "reason": None}
    """
    constraints = []
    forced_archetype = None
    reason = None
    allowed = True

    # Branch 1: New accounts = warm-up mode
    if account_status == "New":
        if archetype != "Feedback":
            allowed = False
            forced_archetype = "Feedback"
            reason = "New accounts must use Feedback archetype (warm-up mode)"

        constraints.extend([
            "Account is NEW - warm-up mode active",
            "Maximum vulnerability required (use 'I', 'my', 'me' extensively)",
            "ZERO links allowed - no URLs of any kind",
            "No product pitch - focus entirely on asking for help",
            "Maximum formality: 0.9 (very casual and personal)",
            "Share struggles and uncertainties openly",
        ])
        return {
            "allowed": allowed,
            "forced_archetype": forced_archetype,
            "constraints": constraints,
            "reason": reason
        }

    # Branch 2: High ISC (> 7.5) = extreme sensitivity
    if isc_score > 7.5:
        if archetype in ["ProblemSolution", "Journey"]:
            allowed = False
            forced_archetype = "Feedback"
            reason = f"ISC {isc_score:.1f} > 7.5: Only Feedback archetype allowed for high-sensitivity communities"

        constraints.extend([
            f"Community has VERY HIGH sensitivity (ISC {isc_score:.1f}/10)",
            "Maximum vulnerability required (emotions, personal pronouns, questions)",
            "ZERO links allowed - no URLs of any kind",
            "Minimize all promotional language",
            "Focus on authenticity over polish",
            "Show genuine uncertainty and ask for community guidance",
        ])
        return {
            "allowed": allowed,
            "forced_archetype": forced_archetype,
            "constraints": constraints,
            "reason": reason
        }

    # Branch 3: ProblemSolution archetype rules
    if archetype == "ProblemSolution":
        constraints.extend([
            "ProblemSolution archetype: 90% pain / 10% solution ratio",
            "NO greetings (avoid 'Hi everyone', 'Hey folks', etc.)",
            "Product mention ONLY in final 10% of post",
            "Focus first 2-3 paragraphs entirely on the problem",
            "Explain why existing solutions fail",
            "Keep solution description brief and matter-of-fact",
            "Avoid marketing language entirely in problem section",
        ])

    # Branch 4: Journey archetype rules
    elif archetype == "Journey":
        constraints.extend([
            "Journey archetype: Technical diary style",
            "Include specific milestones with dates or timeframes",
            "Use concrete numbers and metrics (users, iterations, hours spent)",
            "Show the discovery process, not just the outcome",
            "Mention setbacks and failed attempts",
            "Product mention should emerge naturally from the story",
            "Write in past tense for completed milestones, present for current status",
        ])

    # Branch 5: Feedback archetype rules
    elif archetype == "Feedback":
        constraints.extend([
            "Feedback archetype: Invert authority pattern",
            "Ask community to find flaws and problems",
            "Show controlled imperfection (mention what you're unsure about)",
            "Frame yourself as student, community as teacher",
            "Ask specific questions about concerns or decisions",
            "Acknowledge limitations of your approach",
            "Invite critique, not just praise",
        ])

    # ISC-based general constraints
    if isc_score > 5.0:
        constraints.append(f"Community has elevated sensitivity (ISC {isc_score:.1f}/10) - increase authenticity")

    if isc_score <= 3.0:
        constraints.append(f"Community has low sensitivity (ISC {isc_score:.1f}/10) - standard promotional language acceptable")

    return {
        "allowed": allowed,
        "forced_archetype": forced_archetype,
        "constraints": constraints,
        "reason": reason
    }
