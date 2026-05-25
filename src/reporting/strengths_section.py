"""Strengths section — identifies positive indicators from analysis."""

from __future__ import annotations

from typing import Any


def build_strengths(ratios: dict[str, Any], cross_validation: list[dict[str, Any]]) -> list[str]:
    """Identify positive financial indicators.

    Returns:
        List of strength statements.
    """
    strengths: list[str] = []

    gm = ratios.get("profitability", {}).get("gross_margin", [])
    if gm and gm[-1]["value"] > 0.4:
        strengths.append(
            f"Industry-leading gross margins ({gm[-1]['value']:.1%}) indicating strong pricing power"
        )

    cf_ni = ratios.get("cash_flow_quality", {}).get("cf_to_ni", [])
    if cf_ni:
        all_above = all(p["value"] >= 1.0 for p in cf_ni)
        if all_above:
            strengths.append("High earnings quality (CF/NI ratio consistently ≥ 1.0)")

    fcf = ratios.get("cash_flow_quality", {}).get("fcf_margin", [])
    if fcf and fcf[-1]["value"] > 0.15:
        strengths.append(f"Strong free cash flow generation ({fcf[-1]['value']:.1%} FCF margin)")

    cr = ratios.get("liquidity", {}).get("current_ratio", [])
    if cr and cr[-1]["value"] > 2.0:
        strengths.append("Excellent short-term liquidity position")

    ic = ratios.get("solvency", {}).get("interest_coverage", [])
    if ic and ic[-1]["value"] > 10:
        strengths.append("Very strong debt service capacity")

    for cv in cross_validation:
        if cv["result"] == "PASS":
            if cv["check_name"] == "revenue_quality":
                strengths.append(
                    "Revenue quality confirmed — AR growth in line with revenue growth"
                )
            elif cv["check_name"] == "demand_health":
                strengths.append(
                    "Healthy demand indicators — inventory growth aligned with revenue"
                )
            elif cv["check_name"] == "earnings_quality":
                strengths.append(
                    "Earnings quality validated — operating cash flow exceeds net income"
                )

    return strengths or ["Insufficient data to identify specific strengths"]
