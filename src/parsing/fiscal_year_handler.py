"""Fiscal year handler — parse, sort, label, and detect fiscal year periods."""

from __future__ import annotations

import re
from datetime import date, datetime

from src.models.enums import PeriodType


def parse_end_date(date_str: str) -> date | None:
    """Parse various end-date formats into a date object.

    Args:
        date_str: Date string (e.g., "2024-09-30", "09/30/2024", "2024-09-30T00:00:00").

    Returns:
        datetime.date or None if unparseable.
    """
    if not date_str:
        return None

    formats = [
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%m/%d/%Y",
        "%d/%m/%Y",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y%m%d",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip()[:10], fmt).date()
        except ValueError:
            continue

    return None


def sort_periods_chronologically(
    periods: list[dict],
    reverse: bool = True,
) -> list[dict]:
    """Sort periods by end_date.

    Args:
        periods: List of period dicts with an "end_date" key.
        reverse: True for descending (most recent first).

    Returns:
        Sorted list of periods.
    """

    def _sort_key(p: dict) -> str:
        return p.get("end_date", "")

    return sorted(periods, key=_sort_key, reverse=reverse)


def generate_period_label(
    fiscal_year: int,
    period_type: PeriodType,
    quarter: int | None = None,
) -> str:
    """Generate a standard period label.

    Args:
        fiscal_year: Fiscal year (YYYY).
        period_type: ANNUAL or QUARTERLY.
        quarter: Quarter number (1-4) for quarterly periods.

    Returns:
        Period label string (e.g., "FY2024", "Q1 FY2024").
    """
    if period_type == PeriodType.QUARTERLY and quarter is not None:
        return f"Q{quarter} FY{fiscal_year}"
    return f"FY{fiscal_year}"


def detect_fiscal_year_end(periods: list[dict]) -> str:
    """Detect fiscal year end month/day from period data.

    Args:
        periods: List of period dicts with "end_date" keys.

    Returns:
        Fiscal year end in "MM-DD" format (e.g., "09-30", "12-31").
    """
    month_counts: dict[str, int] = {}

    for p in periods:
        end_date = p.get("end_date", "")
        if not end_date:
            continue
        match = re.match(r"(\d{4})[-/](\d{2})[-/](\d{2})", end_date)
        if match:
            fy_end = f"{match.group(2)}-{match.group(3)}"
            month_counts[fy_end] = month_counts.get(fy_end, 0) + 1

    if not month_counts:
        return "12-31"

    return max(month_counts, key=lambda k: month_counts[k])
