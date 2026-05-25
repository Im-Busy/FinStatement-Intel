"""Enum types for financial statement analysis."""

from enum import Enum


class StatementType(Enum):
    INCOME_STATEMENT = "income_statement"
    BALANCE_SHEET = "balance_sheet"
    CASH_FLOW_STATEMENT = "cash_flow_statement"


class PeriodType(Enum):
    ANNUAL = "annual"
    QUARTERLY = "quarterly"


class Severity(Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class Assessment(Enum):
    STRONG = "Strong"
    ADEQUATE = "Adequate"
    CONCERNING = "Concerning"
    CRITICAL = "Critical"


class PipelineStatus(Enum):
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    ERROR = "ERROR"


class AccountingStandard(Enum):
    US_GAAP = "US GAAP"
    IFRS = "IFRS"
    CN_GAAP = "China GAAP"


class ExtractionSource(Enum):
    EDGAR_XBRL = "edgar-xbrl"
    HTML = "html"
    PDF = "pdf"
    OCR = "ocr"


class MappingConfidence(Enum):
    EXACT = "exact"
    FUZZY = "fuzzy"
    LOW = "low"
    UNMAPPED = "unmapped"


class TrendDirection(Enum):
    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"
    MIXED = "mixed"
