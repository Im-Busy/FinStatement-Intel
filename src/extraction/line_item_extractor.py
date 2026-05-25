"""Common line item extraction utilities shared across extraction sources."""

from __future__ import annotations

import re
from typing import Any


def clean_label(label: str) -> str:
    """Normalize a financial line item label string.

    Args:
        label: Raw label from source document.

    Returns:
        Stripped, whitespace-normalized label string.
    """
    return " ".join(label.strip().split())


def detect_negative(value_str: str) -> bool:
    """Check if a value string indicates a negative number.

    Args:
        value_str: Raw value string.

    Returns:
        True if the value appears negative.
    """
    stripped = value_str.strip()
    return bool(re.match(r"^\s*\(", stripped)) and stripped.endswith(")")


def extract_period_info(text: str) -> dict[str, Any]:
    """Attempt to extract fiscal year / period info from surrounding text.

    Args:
        text: Text block that may contain period information.

    Returns:
        Dict with optional keys: fiscal_year, end_date, period_type.
    """
    info: dict[str, Any] = {}

    fy_match = re.search(r"(?:FY|Fiscal Year)[^\d]*(\d{4})", text, re.IGNORECASE)
    if fy_match:
        info["fiscal_year"] = int(fy_match.group(1))

    date_match = re.search(r"(\d{4}[-/]\d{2}[-/]\d{2}|\d{2}[-/]\d{2}[-/]\d{4})", text)
    if date_match:
        info["end_date"] = date_match.group(1)

    if re.search(r"quarter|Q[1-4]|3\s*months?", text, re.IGNORECASE):
        info["period_type"] = "quarterly"
    elif re.search(r"annual|12\s*months?|year\s*ended", text, re.IGNORECASE):
        info["period_type"] = "annual"

    return info


def build_line_item(
    label: str,
    value: float,
    needs_review: bool = False,
    xbrl_concept: str | None = None,
) -> dict[str, Any]:
    """Create a standardized line item dict for extraction output.

    Args:
        label: Raw label text.
        value: Parsed numeric value.
        needs_review: Flag for items requiring manual review.
        xbrl_concept: XBRL concept name if from XBRL source.

    Returns:
        Standardized line item dict.
    """
    return {
        "label": clean_label(label),
        "value": value,
        "needs_review": needs_review,
        "xbrl_concept": xbrl_concept,
    }
