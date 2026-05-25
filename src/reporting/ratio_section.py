"""Ratio analysis section — interpret computed ratios with trend context."""

from __future__ import annotations

from typing import Any


def _last_valid(points: list[dict]) -> dict | None:
    for p in reversed(points):
        if abs(p.get("value", 0)) > 0.0001:
            return p
    return points[0] if points else None


def build_ratio_analysis(ratios: dict[str, Any], trends: dict[str, Any]) -> str:
    """Build ratio analysis narrative with trend insights.

    Returns:
        Multi-paragraph ratio analysis text.
    """
    parts: list[str] = []

    gm = ratios.get("profitability", {}).get("gross_margin", [])
    om = ratios.get("profitability", {}).get("operating_margin", [])
    cf_ni = ratios.get("cash_flow_quality", {}).get("cf_to_ni", [])
    de = ratios.get("solvency", {}).get("debt_to_equity", [])
    cr = ratios.get("liquidity", {}).get("current_ratio", [])
    ic = ratios.get("solvency", {}).get("interest_coverage", [])

    if gm and len(gm) >= 2:
        lv = _last_valid(gm)
        first_valid = next((p for p in gm if abs(p["value"]) > 0.0001), gm[0])
        trend = "improving" if lv["value"] > first_valid["value"] else "declining"
        parts.append(f"Gross margin of {lv['value']:.1%} is {trend} over the analysis period. ")

    if om:
        lv = _last_valid(om)
        if lv:
            parts.append(
                f"Operating margin of {lv['value']:.1%} indicates "
                f"{'strong' if lv['value'] > 0.15 else 'moderate'} pricing power. "
            )

    if cf_ni:
        lv = _last_valid(cf_ni)
        if lv:
            val = lv["value"]
            parts.append(
                f"CF-to-NI ratio of {val:.2f} confirms "
                f"{'high' if val > 1.0 else 'moderate' if val > 0.7 else 'questionable'} earnings quality. "
            )

    if de:
        lv = _last_valid(de)
        if lv:
            parts.append(f"D/E ratio of {lv['value']:.2f}. ")

    if cr:
        lv = _last_valid(cr)
        if lv:
            val = lv["value"]
            parts.append(
                f"Current ratio of {val:.2f} indicates "
                f"{'strong' if val > 2.0 else 'adequate' if val > 1.0 else 'weak'} short-term liquidity. "
            )

    if ic:
        lv = _last_valid(ic)
        if lv:
            val = lv["value"]
            parts.append(
                f"Interest coverage of {val:.1f}x "
                f"{'comfortably covers' if val > 5 else 'adequately covers' if val > 2 else 'barely covers'} "
                f"debt obligations. "
            )

    return "".join(parts) if parts else "Ratio analysis data not available."
