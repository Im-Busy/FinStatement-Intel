"""Executive summary generator — selects top findings and overall assessment."""

from __future__ import annotations

from typing import Any


def generate_executive_summary(
    analyzed_data: dict[str, Any],
) -> dict[str, Any]:
    """Generate executive summary with top 3 findings and overall assessment.

    Args:
        analyzed_data: Analyzed data dict with ratios, red_flags, scorecard, trends.

    Returns:
        Dict with top_findings list and overall_assessment string.
    """
    findings: list[str] = []

    red_flags = analyzed_data.get("red_flags", [])
    scorecard = analyzed_data.get("scorecard", {})
    trends = analyzed_data.get("trends", {})
    ratios = analyzed_data.get("ratios", {})

    for flag in red_flags:
        if flag.get("severity") == "critical" and len(findings) < 3:
            findings.append(flag.get("description", "Critical red flag detected"))

    if not findings:
        cf_to_ni = ratios.get("cash_flow_quality", {}).get("cf_to_ni", [])
        if cf_to_ni:
            avg_cf_ni = sum(p["value"] for p in cf_to_ni) / len(cf_to_ni)
            if avg_cf_ni > 1.2:
                findings.append(f"Strong earnings quality: average CF/NI of {avg_cf_ni:.2f}")
            elif avg_cf_ni < 0.8:
                findings.append(f"Earnings quality concern: average CF/NI of {avg_cf_ni:.2f}")

        rev_growth = trends.get("revenue_yoy_growth", [])
        if rev_growth:
            latest = rev_growth[-1]["value"] if rev_growth else 0
            if latest > 0.05:
                findings.append(f"Strong revenue growth: {latest:.1%} YoY")
            elif latest < -0.05:
                findings.append(f"Revenue declining: {latest:.1%} YoY")

    for flag in red_flags:
        if flag.get("severity") == "warning" and len(findings) < 3:
            findings.append(flag.get("description", "Warning flag detected"))

    if len(findings) < 3:
        total = scorecard.get("total", 0)
        if total >= 80:
            findings.append("Overall strong financial health across all dimensions")
        elif total >= 60:
            findings.append("Overall adequate financial health with some areas to monitor")
        elif total >= 40:
            findings.append("Concerning financial health requiring closer attention")
        else:
            findings.append("Critical financial health issues requiring immediate action")

    findings = findings[:3]

    assessment = scorecard.get("assessment", "Not analyzed")

    return {
        "top_findings": findings,
        "overall_assessment": assessment,
    }
