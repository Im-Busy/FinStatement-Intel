"""Period and validation result data models."""

from dataclasses import dataclass, field

from src.models.enums import PeriodType
from src.models.statements import BalanceSheet, CashFlowStatement, IncomeStatement


@dataclass
class ValidationResult:
    check_name: str
    holds: bool
    expected: float = 0.0
    actual: float = 0.0
    difference: float = 0.0
    diff_pct: float = 0.0
    detail: str = ""


@dataclass
class Period:
    type: PeriodType
    fiscal_year: int
    end_date: str
    income_statement: IncomeStatement = field(default_factory=IncomeStatement)
    balance_sheet: BalanceSheet = field(default_factory=BalanceSheet)
    cash_flow_statement: CashFlowStatement = field(default_factory=CashFlowStatement)
    validation_results: list[ValidationResult] = field(default_factory=list)
    source: str = ""
    original_unit: str = ""
