"""Line item data models for raw financial data."""

from dataclasses import dataclass

from src.models.enums import MappingConfidence, StatementType


@dataclass
class LineItem:
    label: str
    value: float
    needs_review: bool = False
    standard_key: str | None = None
    mapping_confidence: MappingConfidence | None = None
    original_unit: str = ""
    original_value: float | None = None
    xbrl_concept: str | None = None


@dataclass
class UnmappedItem:
    original_label: str
    value: float
    statement_type: StatementType
