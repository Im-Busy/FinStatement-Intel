"""Recommendations section — generates actionable next steps based on analysis."""

from __future__ import annotations

from typing import Any


def build_recommendations(
    ratios: dict[str, Any],
    red_flags: list[dict[str, Any]],
    scorecard: dict[str, Any],
) -> list[str]:
    """Generate actionable recommendations based on analysis findings.

    Returns:
        List of recommendation strings.
    """
    recs: list[str] = []

    criticals = [f for f in red_flags if f.get("severity") == "critical"]
    warnings = [f for f in red_flags if f.get("severity") == "warning"]

    for flag in criticals:
        flag_type = flag.get("type", "")
        if flag_type == "earnings_quality_concern":
            recs.append(
                "Investigate cash flow to net income divergence — review accruals and non-cash items"
            )
        elif flag_type == "liquidity_crisis_risk":
            recs.append("Review working capital management and near-term debt maturities")
        elif flag_type == "sustained_negative_ocf":
            recs.append(
                "Evaluate core business viability — sustained negative operating CF is unsustainable"
            )
        elif flag_type == "cannot_cover_interest":
            recs.append(
                "Restructure debt or improve operational efficiency before liquidity crisis"
            )
        elif flag_type == "negative_equity":
            recs.append(
                "Assess solvency risk and potential need for restructuring or capital raise"
            )

    for flag in warnings:
        flag_type = flag.get("type", "")
        if flag_type == "excessive_leverage":
            recs.append(
                "Monitor debt levels — consider net debt position rather than gross D/E ratio"
            )
        elif flag_type == "demand_problem":
            recs.append("Investigate inventory buildup — potential demand weakness or overstocking")
        elif flag_type == "acquisition_risk":
            recs.append(
                "Review goodwill for potential impairment and acquisition integration progress"
            )

    total = scorecard.get("total", 0)
    if total < 40:
        recs.append(
            "Conduct comprehensive financial review — multiple critical and warning indicators present"
        )
    elif total < 60:
        recs.append(
            "Implement monitoring dashboard for key metrics — several areas require attention"
        )
    elif len(warnings) > 2:
        recs.append("Set up quarterly review process for warning indicators")

    if not recs:
        recs.append("Monitor revenue growth trajectory for signs of structural change")
        recs.append("Maintain current financial discipline and capital allocation strategy")
        recs.append("Consider peer comparison to benchmark against industry leaders")

    return recs
