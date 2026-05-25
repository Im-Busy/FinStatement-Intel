"""Scorecard builder — assembles 5-dimension health scorecard into report format."""

from __future__ import annotations

from typing import Any


def build_scorecard(scorecard: dict[str, Any]) -> dict[str, Any]:
    """Pass through scorecard data into report format.

    Args:
        scorecard: Dict from analyzer with profitability, liquidity, etc.

    Returns:
        Same scorecard dict for report output.
    """
    return {
        "profitability": scorecard.get("profitability", 0),
        "liquidity": scorecard.get("liquidity", 0),
        "solvency": scorecard.get("solvency", 0),
        "efficiency": scorecard.get("efficiency", 0),
        "cash_flow_quality": scorecard.get("cash_flow_quality", 0),
        "total": scorecard.get("total", 0),
        "assessment": scorecard.get("assessment", ""),
    }
