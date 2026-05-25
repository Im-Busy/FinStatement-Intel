"""Verify all data models instantiate correctly."""

from src.models.company import Company
from src.models.enums import (
    MappingConfidence,
    PeriodType,
    PipelineStatus,
    Severity,
    StatementType,
)
from src.models.line_item import LineItem, UnmappedItem
from src.models.period import Period, ValidationResult
from src.models.ratios import RatioPoint
from src.models.red_flag import RedFlag
from src.models.report_model import (
    AnalysisReport,
    ExecutiveSummary,
    Scorecard,
)
from src.models.statements import BalanceSheet, CashFlowStatement, IncomeStatement
from src.models.validation import PipelineResult


class TestEnums:
    def test_statement_types(self):
        assert StatementType.INCOME_STATEMENT.value == "income_statement"
        assert StatementType.BALANCE_SHEET.value == "balance_sheet"
        assert StatementType.CASH_FLOW_STATEMENT.value == "cash_flow_statement"

    def test_pipeline_status(self):
        assert PipelineStatus.SUCCESS.value == "SUCCESS"
        assert PipelineStatus.WARNING.value == "WARNING"
        assert PipelineStatus.ERROR.value == "ERROR"

    def test_mapping_confidence(self):
        assert MappingConfidence.EXACT.value == "exact"
        assert MappingConfidence.FUZZY.value == "fuzzy"
        assert MappingConfidence.LOW.value == "low"
        assert MappingConfidence.UNMAPPED.value == "unmapped"


class TestCompany:
    def test_defaults(self):
        c = Company(name="Test", ticker="TST")
        assert c.name == "Test"
        assert c.ticker == "TST"
        assert c.cik is None
        assert c.currency == "USD"
        assert c.industry == ""

    def test_full_fields(self):
        c = Company(
            name="Apple Inc.",
            ticker="AAPL",
            cik="0000320193",
            fiscal_year_end="09-30",
            industry="Technology",
            exchange="XNAS",
        )
        assert c.cik == "0000320193"
        assert c.fiscal_year_end == "09-30"


class TestLineItem:
    def test_basic(self):
        li = LineItem(label="Revenue", value=100000.0)
        assert li.label == "Revenue"
        assert li.value == 100000.0
        assert not li.needs_review

    def test_with_mapping(self):
        li = LineItem(
            label="Revenues",
            value=95000.0,
            standard_key="revenue",
            mapping_confidence=MappingConfidence.EXACT,
            original_unit="millions",
            original_value=95000.0,
            xbrl_concept="us-gaap:Revenues",
        )
        assert li.standard_key == "revenue"
        assert li.mapping_confidence == MappingConfidence.EXACT

    def test_unmapped_item(self):
        ui = UnmappedItem(
            original_label="Other weird revenue",
            value=500.0,
            statement_type=StatementType.INCOME_STATEMENT,
        )
        assert ui.original_label == "Other weird revenue"
        assert ui.value == 500.0


class TestStatements:
    def test_income_statement_defaults(self):
        is_ = IncomeStatement()
        assert is_.revenue == 0.0
        assert is_.net_income == 0.0
        assert is_.unmapped == []

    def test_balance_sheet_defaults(self):
        bs = BalanceSheet()
        assert bs.total_assets == 0.0
        assert bs.total_equity == 0.0

    def test_cash_flow_statement_defaults(self):
        cfs = CashFlowStatement()
        assert cfs.operating_cf == 0.0
        assert cfs.capex == 0.0

    def test_income_statement_with_values(self):
        is_ = IncomeStatement(revenue=100000.0, net_income=19000.0)
        assert is_.revenue == 100000.0
        assert is_.net_income == 19000.0


class TestPeriod:
    def test_default_period(self):
        p = Period(type=PeriodType.ANNUAL, fiscal_year=2024, end_date="2024-12-31")
        assert p.fiscal_year == 2024
        assert p.type == PeriodType.ANNUAL
        assert isinstance(p.income_statement, IncomeStatement)
        assert isinstance(p.balance_sheet, BalanceSheet)
        assert isinstance(p.cash_flow_statement, CashFlowStatement)

    def test_validation_result(self):
        vr = ValidationResult(
            check_name="accounting_equation",
            holds=True,
            expected=200000.0,
            actual=200000.0,
            detail="A = L + E",
        )
        assert vr.holds is True
        assert vr.difference == 0.0


class TestRatios:
    def test_ratio_point(self):
        rp = RatioPoint(period="FY2024", value=0.462, unit="%")
        assert rp.period == "FY2024"
        assert rp.value == 0.462
        assert rp.unit == "%"


class TestRedFlag:
    def test_basic(self):
        rf = RedFlag(
            type="earnings_quality_concern",
            severity=Severity.CRITICAL,
            description="CF/NI < 0.5",
            periods_affected=["FY2024"],
            current_value=0.4,
            threshold=0.5,
        )
        assert rf.severity == Severity.CRITICAL
        assert rf.current_value == 0.4


class TestReportModel:
    def test_scorecard(self):
        sc = Scorecard(profitability=16, total=74, assessment="Adequate")
        assert sc.total == 74
        assert sc.assessment == "Adequate"

    def test_analysis_report(self, sample_company):
        r = AnalysisReport(company=sample_company, periods_analyzed="FY2020-FY2024")
        assert r.company.ticker == "TEST"
        assert r.periods_analyzed == "FY2020-FY2024"
        assert isinstance(r.executive_summary, ExecutiveSummary)
        assert isinstance(r.scorecard, Scorecard)


class TestPipelineResult:
    def test_success(self):
        pr = PipelineResult(status=PipelineStatus.SUCCESS, phase="analysis", result={"key": "val"})
        assert pr.status == PipelineStatus.SUCCESS
        assert pr.phase == "analysis"

    def test_error(self):
        pr = PipelineResult(status=PipelineStatus.ERROR, phase="extraction", error={"msg": "fail"})
        assert pr.status == PipelineStatus.ERROR
