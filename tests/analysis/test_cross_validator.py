"""Tests for cross-statement validator."""

from src.analysis.cross_validator import (
    run_cross_validation,
    validate_demand_health,
    validate_depreciation_consistency,
    validate_earnings_quality,
    validate_interest_consistency,
    validate_revenue_quality,
)


class TestValidateEarningsQuality:
    def test_pass(self):
        result = validate_earnings_quality([300, 310, 320], [280, 290, 310])
        assert result.result == "PASS"

    def test_warn(self):
        result = validate_earnings_quality([250, 260, 270], [280, 290, 310])
        assert result.result == "WARN"

    def test_insufficient_data(self):
        result = validate_earnings_quality([], [100])
        assert result.result == "FAIL"


class TestValidateRevenueQuality:
    def test_pass(self):
        result = validate_revenue_quality([100, 110, 120], [1000, 1200, 1400])
        assert result.result == "PASS"

    def test_warn(self):
        result = validate_revenue_quality([100, 150, 200], [1000, 1050, 1100])
        assert result.result == "WARN"

    def test_insufficient_data(self):
        result = validate_revenue_quality([100], [1000])
        assert result.result == "FAIL"


class TestValidateDemandHealth:
    def test_pass(self):
        result = validate_demand_health([100, 110, 120], [1000, 1200, 1400])
        assert result.result == "PASS"

    def test_warn(self):
        result = validate_demand_health([100, 150, 200], [1000, 1050, 1100])
        assert result.result == "WARN"

    def test_insufficient_data(self):
        result = validate_demand_health([100], [1000])
        assert result.result == "FAIL"


class TestValidateDepreciationConsistency:
    def test_pass(self):
        result = validate_depreciation_consistency([100, 110], [10])
        assert result.result == "PASS"

    def test_warn(self):
        result = validate_depreciation_consistency([100, 110, 500], [9, 10, 11])
        assert result.result == "WARN"

    def test_insufficient_data(self):
        result = validate_depreciation_consistency([100], [10])
        assert result.result == "FAIL"


class TestValidateInterestConsistency:
    def test_pass(self):
        result = validate_interest_consistency(5000, 100000)
        assert result.result == "PASS"

    def test_warn(self):
        result = validate_interest_consistency(10000, 10000)
        assert result.result == "WARN"

    def test_no_debt(self):
        result = validate_interest_consistency(0, 0)
        assert result.result == "PASS"


class TestRunCrossValidation:
    def test_runs_all_checks(self):
        periods = [
            {
                "fiscal_year": 2023,
                "statements": {
                    "income_statement": {
                        "revenue": 1000,
                        "net_income": 100,
                        "interest_expense": 10,
                    },
                    "balance_sheet": {
                        "accounts_receivable": 100,
                        "inventory": 200,
                        "accumulated_depreciation": 500,
                        "long_term_debt": 1000,
                        "short_term_debt": 200,
                    },
                    "cash_flow_statement": {
                        "operating_cf": 150,
                        "depreciation_amortization": 50,
                    },
                },
            },
            {
                "fiscal_year": 2024,
                "statements": {
                    "income_statement": {
                        "revenue": 1100,
                        "net_income": 110,
                        "interest_expense": 12,
                    },
                    "balance_sheet": {
                        "accounts_receivable": 110,
                        "inventory": 220,
                        "accumulated_depreciation": 600,
                        "long_term_debt": 1200,
                        "short_term_debt": 300,
                    },
                    "cash_flow_statement": {
                        "operating_cf": 160,
                        "depreciation_amortization": 60,
                    },
                },
            },
        ]
        result = run_cross_validation(periods)
        assert len(result) == 5
        names = {v.check_name for v in result}
        assert "earnings_quality" in names
        assert "revenue_quality" in names
        assert "demand_health" in names
        assert "depreciation_consistency" in names
        assert "interest_consistency" in names

    def test_empty_periods(self):
        result = run_cross_validation([])
        assert len(result) == 5
