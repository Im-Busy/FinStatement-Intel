"""Validation data models for pipeline integrity checks."""

from dataclasses import dataclass, field

from src.models.enums import PipelineStatus


@dataclass
class PipelineResult:
    status: PipelineStatus
    phase: str = ""
    result: dict | None = None
    error: dict | None = None
    warnings: list[str] = field(default_factory=list)
