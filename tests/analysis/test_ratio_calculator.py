"""Tests for ratio calculator orchestrator (compute_all_ratios)."""

from src.analysis.ratio_calculator import compute_all_ratios


class TestComputeAllRatios:
    def _make_period(self, year, **overrides):
        base = {
            "fiscal_year": year,
            "statements": {
                "income_statement": {
                    "revenue": 100000,
                    "gross_profit": 40000,
                    "operating_income": 25000,
                    "net_income": 19000,
                    "ebitda": 30000,
                    "cogs": 60000,
                    "interest_expense": 2000,
                },
                "balance_sheet": {
                    "current_assets": 60000,
                    "current_liabilities": 35000,
                    "total_assets": 200000,
                    "total_equity": 80000,
                    "total_liabilities": 120000,
                    "inventory": 8000,
                    "accounts_receivable": 15000,
                    "long_term_debt": 50000,
                    "goodwill": 10000,
                },
                "cash_flow_statement": {
                    "operating_cf": 28000,
                    "capex": -10000,
                    "depreciation_amortization": 5000,
                },
            },
        }
        for key, value in overrides.items():
            parts = key.split(".", 1)
            if len(parts) == 2:
                stmt_key, field = parts
                base["statements"][stmt_key][field] = value
        return base

    def test_single_period(self):
        periods = [self._make_period(2024)]
        result = compute_all_ratios(periods)
        assert len(result["profitability"]["gross_margin"]) == 1
        assert result["profitability"]["gross_margin"][0].value == 0.4

    def test_multiple_periods(self):
        periods = [
            self._make_period(2023, **{"income_statement.revenue": 95000}),
            self._make_period(2024),
        ]
        result = compute_all_ratios(periods)
        assert len(result["profitability"]["gross_margin"]) == 2
        assert len(result["liquidity"]["current_ratio"]) == 2
        assert len(result["solvency"]["debt_to_equity"]) == 2
        assert len(result["efficiency"]["asset_turnover"]) == 2
        assert len(result["cash_flow_quality"]["fcf"]) == 2

    def test_all_categories_present(self):
        result = compute_all_ratios([self._make_period(2024)])
        assert set(result.keys()) == {
            "profitability",
            "liquidity",
            "solvency",
            "efficiency",
            "cash_flow_quality",
        }

    def test_profitability_ratios(self):
        result = compute_all_ratios([self._make_period(2024)])
        p = result["profitability"]
        assert len(p) == 6
        assert p["gross_margin"][0].unit == "%"
        assert p["roe"][0].unit == "%"
        assert p["ebitda_margin"][0].unit == "%"

    def test_liquidity_ratios(self):
        result = compute_all_ratios([self._make_period(2024)])
        lq = result["liquidity"]
        assert len(lq) == 4
        assert lq["working_capital"][0].unit == "USD"
        assert lq["current_ratio"][0].unit == "ratio"

    def test_solvency_ratios(self):
        result = compute_all_ratios([self._make_period(2024)])
        sv = result["solvency"]
        assert len(sv) == 4
        assert sv["interest_coverage"][0].unit == "ratio"

    def test_efficiency_ratios(self):
        result = compute_all_ratios([self._make_period(2024)])
        ef = result["efficiency"]
        assert len(ef) == 4
        assert ef["days_sales_outstanding"][0].unit == "days"

    def test_cash_flow_quality_ratios(self):
        result = compute_all_ratios([self._make_period(2024)])
        cf = result["cash_flow_quality"]
        assert len(cf) == 4
        assert cf["fcf"][0].unit == "USD"
        assert cf["fcf"][0].value == 18000.0

    def test_zero_denominators(self):
        periods = [self._make_period(2024, **{"balance_sheet.total_equity": 0})]
        result = compute_all_ratios(periods)
        assert result["profitability"]["roe"][0].value == 0.0
        assert result["solvency"]["debt_to_equity"][0].value == 0.0

    def test_empty_periods(self):
        result = compute_all_ratios([])
        assert len(result["profitability"]["gross_margin"]) == 0

    def test_period_missing_fields(self):
        periods = [
            {
                "fiscal_year": 2024,
                "statements": {
                    "income_statement": {},
                    "balance_sheet": {},
                    "cash_flow_statement": {},
                },
            }
        ]
        result = compute_all_ratios(periods)
        assert result["cash_flow_quality"]["fcf"][0].value == 0.0
