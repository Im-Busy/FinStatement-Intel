"""Tests for structure validator — A=L+E, ΔCash, IS arithmetic."""

from src.parsing.structure_validator import (
    validate_balance_sheet,
    validate_cash_flow_reconciliation,
    validate_income_statement_arithmetic,
)


class TestBalanceSheet:
    def test_balanced(self):
        result = validate_balance_sheet(200000, 120000, 80000)
        assert result.holds is True
        assert result.diff_pct == 0.0

    def test_unbalanced(self):
        result = validate_balance_sheet(200000, 120000, 70000)
        assert result.holds is False

    def test_within_tolerance(self):
        result = validate_balance_sheet(200000, 120000, 79900)
        assert result.holds is True

    def test_zero_assets(self):
        result = validate_balance_sheet(0, 100000, 100000)
        assert result.holds is False


class TestCashFlowReconciliation:
    def test_reconciles(self):
        result = validate_cash_flow_reconciliation(100000, -20000, -70000, 10000)
        assert result.holds is True

    def test_mismatch(self):
        result = validate_cash_flow_reconciliation(100000, -20000, -70000, 20000)
        assert result.holds is False


class TestIncomeStatementArithmetic:
    def test_correct(self):
        result = validate_income_statement_arithmetic(100000, 60000, 40000)
        assert result.holds is True

    def test_incorrect(self):
        result = validate_income_statement_arithmetic(100000, 60000, 30000)
        assert result.holds is False
