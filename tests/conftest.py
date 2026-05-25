"""Shared test fixtures for the financial analysis pipeline."""

import json
from pathlib import Path

import pytest

from src.models.company import Company
from src.models.enums import (
    PeriodType,
    Severity,
)
from src.models.period import Period, ValidationResult
from src.models.ratios import (
    CashFlowQualityRatios,
    EfficiencyRatios,
    LiquidityRatios,
    ProfitabilityRatios,
    RatioPoint,
    SolvencyRatios,
)
from src.models.red_flag import RedFlag
from src.models.report_model import (
    AnalysisReport,
    CrossValidationResult,
    ExecutiveSummary,
    Scorecard,
)
from src.models.statements import BalanceSheet, CashFlowStatement, IncomeStatement


@pytest.fixture
def sample_company() -> Company:
    return Company(
        name="TestCo",
        ticker="TEST",
        cik="0001234567",
        fiscal_year_end="12-31",
        currency="USD",
        industry="Technology",
        exchange="XNAS",
    )


@pytest.fixture
def sample_apple_company() -> Company:
    return Company(
        name="Apple Inc.",
        ticker="AAPL",
        cik="0000320193",
        fiscal_year_end="09-30",
        currency="USD",
        industry="Technology",
        exchange="XNAS",
    )


@pytest.fixture
def sample_income_statement() -> IncomeStatement:
    return IncomeStatement(
        revenue=100000.0,
        cogs=60000.0,
        gross_profit=40000.0,
        operating_expenses=15000.0,
        rnd_expense=8000.0,
        sga_expense=7000.0,
        operating_income=25000.0,
        interest_expense=2000.0,
        interest_income=500.0,
        income_tax=4500.0,
        net_income=19000.0,
        eps_basic=3.80,
        eps_diluted=3.75,
        ebitda=30000.0,
    )


@pytest.fixture
def sample_balance_sheet() -> BalanceSheet:
    return BalanceSheet(
        total_assets=200000.0,
        current_assets=60000.0,
        cash_and_equivalents=25000.0,
        accounts_receivable=15000.0,
        inventory=8000.0,
        total_liabilities=120000.0,
        current_liabilities=35000.0,
        long_term_debt=50000.0,
        total_equity=80000.0,
        goodwill=10000.0,
        ppe_net=90000.0,
        accounts_payable=12000.0,
        short_term_debt=5000.0,
        accumulated_depreciation=30000.0,
    )


@pytest.fixture
def sample_cash_flow_statement() -> CashFlowStatement:
    return CashFlowStatement(
        operating_cf=28000.0,
        investing_cf=-12000.0,
        financing_cf=-8000.0,
        capex=-10000.0,
        depreciation_amortization=5000.0,
        net_change_cash=8000.0,
        dividends_paid=-4000.0,
        stock_issuance=0.0,
        debt_repayment=-2000.0,
        debt_issuance=0.0,
        fx_effect=-500.0,
    )


@pytest.fixture
def sample_period(
    sample_income_statement, sample_balance_sheet, sample_cash_flow_statement
) -> Period:
    return Period(
        type=PeriodType.ANNUAL,
        fiscal_year=2024,
        end_date="2024-12-31",
        income_statement=sample_income_statement,
        balance_sheet=sample_balance_sheet,
        cash_flow_statement=sample_cash_flow_statement,
        source="edgar-xbrl",
        original_unit="millions",
    )


def _make_period(
    year: int,
    revenue: float,
    net_income: float,
    operating_cf: float,
    current_assets: float,
    current_liabilities: float,
    total_assets: float,
    total_equity: float,
    total_liabilities: float,
    inventory: float,
    accounts_receivable: float,
    interest_expense: float,
    cogs: float,
) -> Period:
    gross_profit = revenue - cogs
    opex = gross_profit * 0.4
    operating_income = gross_profit - opex
    return Period(
        type=PeriodType.ANNUAL,
        fiscal_year=year,
        end_date=f"{year}-12-31",
        income_statement=IncomeStatement(
            revenue=revenue,
            cogs=cogs,
            gross_profit=gross_profit,
            operating_expenses=opex,
            operating_income=operating_income,
            interest_expense=interest_expense,
            net_income=net_income,
            ebitda=operating_income + 5000.0,
        ),
        balance_sheet=BalanceSheet(
            current_assets=current_assets,
            current_liabilities=current_liabilities,
            total_assets=total_assets,
            total_equity=total_equity,
            total_liabilities=total_liabilities,
            inventory=inventory,
            accounts_receivable=accounts_receivable,
            long_term_debt=total_liabilities - current_liabilities,
        ),
        cash_flow_statement=CashFlowStatement(
            operating_cf=operating_cf,
            capex=-5000.0,
            depreciation_amortization=5000.0,
            net_change_cash=operating_cf - 5000.0 - 8000.0,
        ),
        source="edgar-xbrl",
        original_unit="millions",
    )


@pytest.fixture
def sample_parsed_periods() -> list[Period]:
    """5 years of normalized financial data with a growth and then decline pattern."""
    return [
        _make_period(
            2020,
            80000,
            15000,
            25000,
            45000,
            25000,
            150000,
            65000,
            85000,
            6000,
            11000,
            1500,
            44000,
        ),
        _make_period(
            2021,
            88000,
            17000,
            27000,
            50000,
            28000,
            165000,
            72000,
            93000,
            6500,
            12000,
            1600,
            47500,
        ),
        _make_period(
            2022,
            95000,
            18500,
            29000,
            54000,
            30000,
            178000,
            78000,
            100000,
            7000,
            13500,
            1800,
            51000,
        ),
        _make_period(
            2023,
            98000,
            19000,
            28000,
            58000,
            33000,
            190000,
            80000,
            110000,
            7500,
            14500,
            1900,
            52000,
        ),
        _make_period(
            2024,
            95000,
            17500,
            26000,
            60000,
            35000,
            200000,
            80000,
            120000,
            8000,
            15000,
            2000,
            53000,
        ),
    ]


@pytest.fixture
def sample_ratios() -> dict:
    return {
        "profitability": ProfitabilityRatios(
            gross_margin=[RatioPoint("FY2024", 0.442)],
            operating_margin=[RatioPoint("FY2024", 0.202)],
            net_margin=[RatioPoint("FY2024", 0.184)],
            roa=[RatioPoint("FY2024", 0.087)],
            roe=[RatioPoint("FY2024", 0.219)],
            ebitda_margin=[RatioPoint("FY2024", 0.255)],
        ),
        "liquidity": LiquidityRatios(
            current_ratio=[RatioPoint("FY2024", 1.71)],
            quick_ratio=[RatioPoint("FY2024", 1.49)],
            working_capital=[RatioPoint("FY2024", 25000.0, "USD")],
            operating_cf_ratio=[RatioPoint("FY2024", 0.74)],
        ),
        "solvency": SolvencyRatios(
            debt_to_equity=[RatioPoint("FY2024", 1.50)],
            debt_to_assets=[RatioPoint("FY2024", 0.60)],
            interest_coverage=[RatioPoint("FY2024", 12.1)],
            lt_debt_to_equity=[RatioPoint("FY2024", 1.06)],
        ),
        "efficiency": EfficiencyRatios(
            asset_turnover=[RatioPoint("FY2024", 0.475)],
            receivables_turnover=[RatioPoint("FY2024", 6.33)],
            inventory_turnover=[RatioPoint("FY2024", 6.62)],
            days_sales_outstanding=[RatioPoint("FY2024", 57.6)],
        ),
        "cash_flow_quality": CashFlowQualityRatios(
            fcf=[RatioPoint("FY2024", 21000.0, "USD")],
            fcf_margin=[RatioPoint("FY2024", 0.221)],
            cf_to_ni=[RatioPoint("FY2024", 1.49)],
            fcf_to_ni=[RatioPoint("FY2024", 1.20)],
        ),
    }


@pytest.fixture
def sample_scorecard() -> Scorecard:
    return Scorecard(
        profitability=16,
        liquidity=14,
        solvency=12,
        efficiency=15,
        cash_flow_quality=17,
        total=74,
        assessment="Adequate",
    )


@pytest.fixture
def sample_red_flags() -> list[RedFlag]:
    return [
        RedFlag(
            type="excessive_leverage",
            severity=Severity.WARNING,
            description="D/E ratio 1.50 exceeds threshold",
            periods_affected=["FY2024", "FY2023"],
            current_value=1.50,
            threshold=1.0,
            historical_context="persistent since FY2022",
        ),
    ]


@pytest.fixture
def sample_analysis_report(sample_company, sample_scorecard, sample_red_flags) -> AnalysisReport:
    return AnalysisReport(
        company=sample_company,
        periods_analyzed="FY2020-FY2024",
        generated_at="2026-05-25T18:00:00Z",
        executive_summary=ExecutiveSummary(
            top_findings=[
                "Strong free cash flow generation",
                "D/E ratio elevated at 1.50",
            ],
            overall_assessment="Adequate",
        ),
        scorecard=sample_scorecard,
        detailed_findings={
            "income_statement": "Revenue grew over the period.",
            "balance_sheet": "Assets increased steadily.",
            "cash_flow_statement": "Operating CF remains strong.",
        },
        ratio_analysis="All ratios within acceptable ranges.",
        red_flags=sample_red_flags,
        strengths=["Strong FCF margin", "High earnings quality"],
        recommendations=["Monitor D/E ratio", "Review capex adequacy"],
        cross_validation=[
            CrossValidationResult(
                check_name="earnings_quality",
                result="PASS",
                detail="OCF/NI avg 1.30 over 5 years",
                periods_evaluated=5,
            ),
        ],
    )


@pytest.fixture
def apple_2020_2024_data():
    sample_path = Path("data/samples/aapl_2020_2024.json")
    return json.loads(sample_path.read_text())


@pytest.fixture
def validation_result_pass() -> ValidationResult:
    return ValidationResult(
        check_name="accounting_equation",
        holds=True,
        expected=200000.0,
        actual=200000.0,
        difference=0.0,
        diff_pct=0.0,
        detail="A = L + E holds.",
    )


@pytest.fixture
def validation_result_fail() -> ValidationResult:
    return ValidationResult(
        check_name="accounting_equation",
        holds=False,
        expected=200000.0,
        actual=195000.0,
        difference=5000.0,
        diff_pct=0.025,
        detail="A ≠ L + E. Difference: 5000.0.",
    )
