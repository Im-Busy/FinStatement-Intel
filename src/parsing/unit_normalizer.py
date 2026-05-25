"""Unit normalizer — converts financial values to a consistent unit scale and currency."""

from __future__ import annotations

import logging

from src.config import DEFAULT_UNIT

logger = logging.getLogger(__name__)

UNIT_SCALE: dict[str, int] = {
    "actual": 0,
    "hundreds": 2,
    "thousands": 3,
    "ten_thousands": 4,
    "millions": 6,
    "hundred_millions": 8,
    "billions": 9,
    "trillions": 12,
}


def normalize_value(
    value: float,
    from_unit: str,
    to_unit: str = DEFAULT_UNIT,
) -> float:
    """Convert value between unit scales.

    Args:
        value: The numeric value to convert.
        from_unit: Source unit (actual, thousands, millions, billions).
        to_unit: Target unit (default: millions).

    Returns:
        Converted float value.
    """
    from_exp = UNIT_SCALE.get(from_unit.lower(), 0)
    to_exp = UNIT_SCALE.get(to_unit.lower(), 6)
    multiplier = 10 ** (from_exp - to_exp)
    return value * multiplier


def detect_unit_from_period(period: dict, default_unit: str = DEFAULT_UNIT) -> str:
    """Detect unit from a period's raw data.

    Args:
        period: Raw period dict from extraction.
        default_unit: Fallback unit if undetectable.

    Returns:
        Detected unit name.
    """
    statements = period.get("statements", {})
    for stmt_key in ("IS", "BS", "CFS"):
        unit = statements.get(stmt_key, {}).get("unit", "")
        if not unit:
            continue
        unit_lower = unit.lower()
        if unit_lower in UNIT_SCALE:
            return unit_lower
        if unit_lower in ("usd", "eur", "jpy", "gbp", "cny", "hkd"):
            return "actual"
        return "actual"

    logger.debug("Could not detect unit from period, defaulting to %s", default_unit)
    return default_unit


def normalize_statement_line_items(
    line_items: list[dict],
    from_unit: str,
    to_unit: str = DEFAULT_UNIT,
) -> list[dict]:
    """Normalize all values in a statement's line items.

    Args:
        line_items: Raw line items list.
        from_unit: Source unit.
        to_unit: Target unit.

    Returns:
        Normalized line items with original_value preserved.
    """
    result: list[dict] = []
    for item in line_items:
        orig_val = item.get("value", 0.0)
        normalized_val = normalize_value(orig_val, from_unit, to_unit)
        result.append(
            {
                **item,
                "value": normalized_val,
                "original_value": orig_val,
                "original_unit": from_unit,
            }
        )
    return result


def normalize_period(
    period: dict,
    target_unit: str = DEFAULT_UNIT,
) -> dict:
    """Normalize all values in a period to the target unit.

    Args:
        period: Raw period dict.
        target_unit: Target unit scale.

    Returns:
        Normalized period dict.
    """
    from_unit = detect_unit_from_period(period)

    statements = period.get("statements", {})
    normalized_statements: dict[str, dict] = {}

    for stmt_key in ("IS", "BS", "CFS"):
        stmt = statements.get(stmt_key, {})
        items = stmt.get("line_items", [])
        normalized_statements[stmt_key] = {
            "unit": target_unit,
            "line_items": normalize_statement_line_items(items, from_unit, target_unit),
            "original_unit": from_unit,
        }

    return {
        **period,
        "statements": normalized_statements,
        "unit": target_unit,
        "original_unit": from_unit,
    }
