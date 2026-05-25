"""Red flags section — formats red flags with historical context and rankings."""

from __future__ import annotations

from typing import Any


def build_red_flags_section(red_flags: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Format and rank red flags by severity.

    Returns:
        Sorted list of red flag dicts with contextualized descriptions.
    """
    severity_order = {"critical": 0, "warning": 1, "info": 2}
    sorted_flags = sorted(red_flags, key=lambda f: severity_order.get(f.get("severity", "info"), 2))

    result: list[dict[str, Any]] = []
    for flag in sorted_flags:
        context = flag.get("historical_context", "")
        if not context:
            periods = flag.get("periods_affected", [])
            if len(periods) > 2:
                context = f"persistent since {periods[0]}"
            elif len(periods) == 1:
                context = f"new in {periods[0]}"
            else:
                context = "ongoing"

        result.append(
            {
                "type": flag.get("type", ""),
                "severity": flag.get("severity", ""),
                "description": flag.get("description", ""),
                "periods_affected": flag.get("periods_affected", []),
                "current_value": flag.get("current_value"),
                "threshold": flag.get("threshold"),
                "historical_context": context,
            }
        )

    return result
