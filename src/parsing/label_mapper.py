"""Label mapping engine — maps raw financial labels to canonical standard keys.

Uses exact match first, then fuzzy matching via SequenceMatcher, then label alias lookup.
"""

from __future__ import annotations

import json
import logging
from difflib import SequenceMatcher

from src.config import FUZZY_MATCH_THRESHOLD, MAPPING_DIR
from src.models.enums import MappingConfidence, StatementType
from src.models.line_item import LineItem, UnmappedItem

logger = logging.getLogger(__name__)

_CACHED_MAPPINGS: dict[str, dict] = {}


def load_mapping_dictionary(standard: str = "us-gaap") -> dict:
    """Load mapping dictionary for an accounting standard.

    Args:
        standard: Standard key (default: "us-gaap"; also "ifrs", "cn-gaap").

    Returns:
        Dict with statement_mappings and label_aliases.
    """
    if standard in _CACHED_MAPPINGS:
        return _CACHED_MAPPINGS[standard]

    filename_map = {
        "us-gaap": "gaap_us.json",
        "ifrs": "ifrs_eu.json",
        "cn-gaap": "cn_accounting.json",
    }
    filename = filename_map.get(standard, "gaap_us.json")
    path = MAPPING_DIR / filename

    if not path.exists():
        logger.warning("Mapping file %s not found, using gaap_us.json fallback", path)
        path = MAPPING_DIR / "gaap_us.json"

    if not path.exists():
        logger.error("No mapping dictionary found at %s", path)
        return {"statement_mappings": {}, "label_aliases": {}}

    with path.open("r", encoding="utf-8") as f:
        mapping = json.load(f)

    _CACHED_MAPPINGS[standard] = mapping
    return mapping


def _stmt_type_to_key(stmt_type: StatementType) -> str:
    return {
        StatementType.INCOME_STATEMENT: "IS",
        StatementType.BALANCE_SHEET: "BS",
        StatementType.CASH_FLOW_STATEMENT: "CFS",
    }[stmt_type]


def fuzzy_match(
    label: str,
    candidates: list[str],
    threshold: float = FUZZY_MATCH_THRESHOLD,
) -> str | None:
    """Find best fuzzy match above threshold.

    Args:
        label: The label to match.
        candidates: List of candidate strings to compare against.
        threshold: Minimum similarity ratio (0.0 to 1.0).

    Returns:
        Best matching candidate string or None.
    """
    label_lower = label.lower()
    best_score = 0.0
    best_match: str | None = None

    for candidate in candidates:
        score = SequenceMatcher(None, label_lower, candidate.lower()).ratio()
        if score > best_score:
            best_score = score
            best_match = candidate

    if best_score >= threshold and best_match is not None:
        return best_match
    return None


def map_line_item(
    label: str,
    statement_type: StatementType,
    mapping: dict,
) -> tuple[str | None, MappingConfidence]:
    """Map a raw label to a standard key.

    Tries exact match → label aliases → fuzzy match on aliases → unmapped.

    Args:
        label: Raw label string from source.
        statement_type: Which statement this line item belongs to.
        mapping: Loaded mapping dictionary.

    Returns:
        Tuple of (standard_key, confidence). Key is None if unmapped.
    """
    stmt_key = _stmt_type_to_key(statement_type)
    stmt_mappings = mapping.get("statement_mappings", {}).get(stmt_key, {})
    label_aliases = mapping.get("label_aliases", {})

    label_clean = label.strip()
    if not label_clean:
        return None, MappingConfidence.UNMAPPED

    if label_clean in stmt_mappings:
        return stmt_mappings[label_clean], MappingConfidence.EXACT

    for std_key, aliases in label_aliases.items():
        for alias in aliases:
            if label_clean.lower() == alias.lower():
                return std_key, MappingConfidence.EXACT

    for std_key, aliases in label_aliases.items():
        match = fuzzy_match(label_clean, aliases)
        if match is not None:
            score = SequenceMatcher(None, label_clean.lower(), match.lower()).ratio()
            confidence = (
                MappingConfidence.FUZZY if score >= FUZZY_MATCH_THRESHOLD else MappingConfidence.LOW
            )
            return std_key, confidence

    stmt_concept_names = list(stmt_mappings.keys())
    match = fuzzy_match(label_clean, stmt_concept_names)
    if match is not None:
        return stmt_mappings[match], MappingConfidence.LOW

    return None, MappingConfidence.UNMAPPED


def map_all_line_items(
    line_items: list[dict],
    statement_type: StatementType,
    mapping: dict,
) -> list[LineItem]:
    """Map all line items in a statement.

    Args:
        line_items: Raw line items from extraction output.
        statement_type: Statement type for these items.
        mapping: Loaded mapping dictionary.

    Returns:
        List of LineItem dataclass instances.
    """
    result: list[LineItem] = []
    for item in line_items:
        label = item.get("label", "")
        value = item.get("value", 0.0)
        needs_review = item.get("needs_review", False)
        xbrl_concept = item.get("xbrl_concept")

        std_key, confidence = map_line_item(label, statement_type, mapping)

        result.append(
            LineItem(
                label=label,
                value=value,
                needs_review=needs_review or confidence == MappingConfidence.UNMAPPED,
                standard_key=std_key,
                mapping_confidence=confidence,
                xbrl_concept=xbrl_concept,
            )
        )

    return result


def get_unmapped_items(line_items: list[LineItem]) -> list[UnmappedItem]:
    """Get list of items that couldn't be mapped.

    Args:
        line_items: List of mapped LineItem objects.

    Returns:
        List of UnmappedItem for unmapped entries.
    """
    unmapped: list[UnmappedItem] = []
    stmt_types = list(StatementType)
    idx = 0

    for li in line_items:
        if li.standard_key is None or li.mapping_confidence == MappingConfidence.UNMAPPED:
            stmt_type = (
                stmt_types[idx % len(stmt_types)] if stmt_types else StatementType.INCOME_STATEMENT
            )
            unmapped.append(
                UnmappedItem(
                    original_label=li.label,
                    value=li.value,
                    statement_type=stmt_type,
                )
            )
        idx += 1

    return unmapped
