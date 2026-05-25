"""Tests for subtotal calculator — derived field computation."""

from src.models.statements import BalanceSheet, CashFlowStatement, IncomeStatement
from src.parsing.subtotal_calculator import compute_derived_fields


class TestComputeDerivedFields:
    def test_gross_profit(self):
        is_ = IncomeStatement(revenue=100000, cogs=60000)
        bs = BalanceSheet()
        cfs = CashFlowStatement()
        computed = compute_derived_fields(is_, bs, cfs)
        assert "gross_profit" in computed
        assert computed["gross_profit"] == 40000.0
        assert is_.gross_profit == 40000.0

    def test_ebitda(self):
        is_ = IncomeStatement(operating_income=25000)
        cfs = CashFlowStatement(depreciation_amortization=5000)
        bs = BalanceSheet()
        computed = compute_derived_fields(is_, bs, cfs)
        assert "ebitda" in computed
        assert computed["ebitda"] == 30000.0
        assert is_.ebitda == 30000.0

    def test_working_capital(self):
        bs = BalanceSheet(current_assets=60000, current_liabilities=35000)
        is_ = IncomeStatement()
        cfs = CashFlowStatement()
        computed = compute_derived_fields(is_, bs, cfs)
        assert "working_capital" in computed
        assert computed["working_capital"] == 25000.0

    def test_net_change_cash(self):
        cfs = CashFlowStatement(operating_cf=28000, investing_cf=-12000, financing_cf=-8000)
        is_ = IncomeStatement()
        bs = BalanceSheet()
        computed = compute_derived_fields(is_, bs, cfs)
        assert "net_change_cash" in computed
        assert computed["net_change_cash"] == 8000.0

    def test_does_not_overwrite_existing(self):
        is_ = IncomeStatement(revenue=100000, cogs=60000, gross_profit=50000)
        bs = BalanceSheet()
        cfs = CashFlowStatement()
        compute_derived_fields(is_, bs, cfs)
        assert is_.gross_profit == 50000.0

    def test_no_data(self):
        computed = compute_derived_fields(IncomeStatement(), BalanceSheet(), CashFlowStatement())
        assert len(computed) == 0
