"""Unit and currency detection for financial data extraction.

Detects unit scale (thousands, millions, billions) and currency symbols
from financial text blocks and table headers.
"""

from __future__ import annotations

import re
from typing import Any

_UNIT_PATTERNS = [
    (
        re.compile(r"\(?in\s+(hundreds|thousands|millions|billions|trillions)", re.IGNORECASE),
        {
            "hundreds": ("hundreds", 100),
            "thousands": ("thousands", 1_000),
            "millions": ("millions", 1_000_000),
            "billions": ("billions", 1_000_000_000),
            "trillions": ("trillions", 1_000_000_000_000),
        },
    ),
    (
        re.compile(r"\$\s*(hundreds|thousands|millions|billions|trillions)", re.IGNORECASE),
        {
            "hundreds": ("hundreds", 100),
            "thousands": ("thousands", 1_000),
            "millions": ("millions", 1_000_000),
            "billions": ("billions", 1_000_000_000),
            "trillions": ("trillions", 1_000_000_000_000),
        },
    ),
    (
        re.compile(r"(百|千|万|亿|萬|億)"),
        {
            "百": ("hundreds", 100),
            "千": ("thousands", 1_000),
            "万": ("ten_thousands", 10_000),
            "萬": ("ten_thousands", 10_000),
            "亿": ("hundred_millions", 100_000_000),
            "億": ("hundred_millions", 100_000_000),
        },
    ),
]

_CURRENCY_PATTERNS = {
    re.compile(r"\$|USD|U\.S\.\s*Dollars?", re.IGNORECASE): "USD",
    re.compile(r"¥|JPY|Japanese\s*Yen", re.IGNORECASE): "JPY",
    re.compile(r"€|EUR|Euros?", re.IGNORECASE): "EUR",
    re.compile(r"£|GBP|British\s*Pounds?", re.IGNORECASE): "GBP",
    re.compile(r"CNY|RMB|Renminbi|元", re.IGNORECASE): "CNY",
    re.compile(r"HKD|HK\$", re.IGNORECASE): "HKD",
}

PARENTHETICAL_NEGATIVE_RE = re.compile(r"^\s*\(([\d,.]+)\)\s*$")
DASH_PATTERN = re.compile(r"^\s*[—–-]+\s*$")
NUMBER_CLEAN_RE = re.compile(r"[^\d.\-]")


def detect_unit(text_blocks: list[str]) -> tuple[str, str]:
    """Detect unit scale and currency from financial text blocks.

    Args:
        text_blocks: List of text strings to search (headers, footnotes, titles).

    Returns:
        Tuple of (unit_name, currency_code). Default: ("millions", "USD").
    """
    combined = "\n".join(text_blocks)

    unit_name = "actual"
    for pattern, mapping in _UNIT_PATTERNS:
        match = pattern.search(combined)
        if match:
            key = match.group(1).lower() if match.lastindex else match.group(0)
            if key in mapping:
                unit_name = mapping[key][0]
                break

    currency = "USD"
    for pattern, code in _CURRENCY_PATTERNS.items():
        if pattern.search(combined):
            currency = code
            break

    return unit_name, currency


def parse_value(value_str: Any, is_parenthetical_negative: bool = True) -> float:
    """Parse a financial value string or number into a float.

    Handles:
        - "1,234.5" → 1234.5
        - "(1,234.5)" → -1234.5 (if is_parenthetical_negative=True)
        - "—" / "-" / "–" → 0.0
        - Already numeric → float

    Args:
        value_str: The value to parse (string or number).
        is_parenthetical_negative: If True, values in parentheses are negative.

    Returns:
        Parsed float value.
    """
    if isinstance(value_str, (int, float)):
        return float(value_str)

    if not isinstance(value_str, str):
        return 0.0

    stripped = value_str.strip()

    if DASH_PATTERN.match(stripped):
        return 0.0

    if is_parenthetical_negative:
        pm = PARENTHETICAL_NEGATIVE_RE.match(stripped)
        if pm:
            cleaned = NUMBER_CLEAN_RE.sub("", pm.group(1))
            try:
                return -float(cleaned)
            except ValueError:
                return 0.0

    cleaned = NUMBER_CLEAN_RE.sub("", stripped)
    if not cleaned or cleaned in ("-", "."):
        return 0.0

    try:
        return float(cleaned)
    except ValueError:
        logger = __import__("logging").getLogger(__name__)
        logger.warning("Could not parse value: %r", value_str)
        return 0.0


def convert_unit(value: float, from_unit: str, to_unit: str = "millions") -> float:
    """Convert a value from one unit scale to another.

    Args:
        value: The numeric value.
        from_unit: Source unit (actual, thousands, millions, billions, trillions).
        to_unit: Target unit (default: millions).

    Returns:
        Converted float value.
    """
    unit_scale = {
        "actual": 0,
        "hundreds": 2,
        "thousands": 3,
        "ten_thousands": 4,
        "millions": 6,
        "hundred_millions": 8,
        "billions": 9,
        "trillions": 12,
    }
    from_exp = unit_scale.get(from_unit, 0)
    to_exp = unit_scale.get(to_unit, 6)
    multiplier = 10 ** (from_exp - to_exp)
    return value * multiplier
