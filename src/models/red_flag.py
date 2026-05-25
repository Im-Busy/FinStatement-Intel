"""Red flag detection data model."""

from dataclasses import dataclass, field

from src.models.enums import Severity


@dataclass
class RedFlag:
    type: str
    severity: Severity
    description: str
    periods_affected: list[str] = field(default_factory=list)
    current_value: float | None = None
    threshold: float | None = None
    historical_context: str = ""
