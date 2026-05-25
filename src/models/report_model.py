"""Report data models — the final output of the pipeline."""

from dataclasses import dataclass, field

from src.models.company import Company
from src.models.red_flag import RedFlag


@dataclass
class Scorecard:
    profitability: int = 0
    liquidity: int = 0
    solvency: int = 0
    efficiency: int = 0
    cash_flow_quality: int = 0
    total: int = 0
    assessment: str = ""


@dataclass
class ExecutiveSummary:
    top_findings: list[str] = field(default_factory=list)
    overall_assessment: str = ""


@dataclass
class CrossValidationResult:
    check_name: str
    result: str
    detail: str
    periods_evaluated: int = 0


@dataclass
class AnalysisReport:
    company: Company
    periods_analyzed: str
    generated_at: str = ""
    executive_summary: ExecutiveSummary = field(default_factory=ExecutiveSummary)
    scorecard: Scorecard = field(default_factory=Scorecard)
    detailed_findings: dict[str, str] = field(default_factory=dict)
    ratio_analysis: str = ""
    red_flags: list[RedFlag] = field(default_factory=list)
    strengths: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    cross_validation: list[CrossValidationResult] = field(default_factory=list)
