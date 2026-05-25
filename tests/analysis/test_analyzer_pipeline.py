"""Integration tests for the full analyzer pipeline."""

from src.analysis.analyzer import analyze_financial_data


class TestAnalyzeFinancialData:
    def _make_period(self, year, rev, ni, ocf):
        return {
            "fiscal_year": year,
            "statements": {
                "income_statement": {
                    "revenue": rev,
                    "gross_profit": rev * 0.4,
                    "operating_income": rev * 0.25,
                    "net_income": ni,
                    "ebitda": rev * 0.3,
                    "cogs": rev * 0.6,
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
                    "short_term_debt": 5000,
                    "accumulated_depreciation": 30000,
                },
                "cash_flow_statement": {
                    "operating_cf": ocf,
                    "capex": -10000,
                    "depreciation_amortization": 5000,
                },
            },
        }

    def test_success(self):
        data = {
            "company": {"name": "TestCo", "ticker": "TEST"},
            "periods": [
                self._make_period(2022, 100000, 19000, 28000),
                self._make_period(2023, 105000, 20000, 29000),
                self._make_period(2024, 110000, 21000, 30000),
            ],
        }
        result = analyze_financial_data(data)
        assert result["status"] == "SUCCESS"
        assert result["periods_analyzed"] == 3
        assert "ratios" in result
        assert "trends" in result
        assert "red_flags" in result
        assert "cross_validation" in result
        assert "anomalies" in result
        assert "scorecard" in result

    def test_warning_status_propagated(self):
        data = {
            "company": {"name": "TestCo", "ticker": "TEST"},
            "status": "WARNING",
            "periods": [self._make_period(2024, 100000, 19000, 28000)],
        }
        result = analyze_financial_data(data)
        assert result["status"] == "WARNING"

    def test_empty_periods(self):
        data = {"company": {"name": "TestCo"}, "periods": []}
        result = analyze_financial_data(data)
        assert result["status"] == "WARNING"
        assert result["periods_analyzed"] == 0

    def test_ratios_serialized(self):
        data = {
            "company": {"name": "TestCo", "ticker": "TEST"},
            "periods": [self._make_period(2024, 100000, 19000, 28000)],
        }
        result = analyze_financial_data(data)
        ratios = result["ratios"]
        gm = ratios["profitability"]["gross_margin"]
        assert isinstance(gm, list)
        assert "period" in gm[0]
        assert "value" in gm[0]
        assert "unit" in gm[0]

    def test_trends_serialized(self):
        data = {
            "company": {"name": "TestCo", "ticker": "TEST"},
            "periods": [
                self._make_period(2023, 100000, 19000, 28000),
                self._make_period(2024, 110000, 21000, 30000),
            ],
        }
        result = analyze_financial_data(data)
        assert "revenue_yoy_growth" in result["trends"]
        assert "revenue_cagr_3yr" in result["trends"]
        assert "margin_trend" in result["trends"]

    def test_cross_validation_serialized(self):
        data = {
            "company": {"name": "TestCo", "ticker": "TEST"},
            "periods": [
                self._make_period(2023, 100000, 19000, 28000),
                self._make_period(2024, 110000, 21000, 30000),
            ],
        }
        result = analyze_financial_data(data)
        assert len(result["cross_validation"]) == 5
        cv = result["cross_validation"][0]
        assert "check_name" in cv
        assert "result" in cv

    def test_red_flags_serialized(self):
        data = {
            "company": {"name": "TestCo", "ticker": "TEST"},
            "periods": [
                self._make_period(2023, 100000, 19000, 28000),
                self._make_period(2024, 110000, 21000, 30000),
            ],
        }
        result = analyze_financial_data(data)
        for flag in result["red_flags"]:
            assert "type" in flag
            assert "severity" in flag
            assert "description" in flag

    def test_scorecard_fields(self):
        data = {
            "company": {"name": "TestCo", "ticker": "TEST"},
            "periods": [self._make_period(2024, 100000, 19000, 28000)],
        }
        result = analyze_financial_data(data)
        sc = result["scorecard"]
        assert "profitability" in sc
        assert "liquidity" in sc
        assert "solvency" in sc
        assert "efficiency" in sc
        assert "cash_flow_quality" in sc
        assert "total" in sc
        assert "assessment" in sc
        assert 0 <= sc["total"] <= 100

    def test_analysis_period(self):
        data = {
            "company": {"name": "TestCo", "ticker": "TEST"},
            "periods": [
                self._make_period(2020, 80000, 15000, 25000),
                self._make_period(2021, 88000, 17000, 27000),
                self._make_period(2022, 95000, 18500, 29000),
                self._make_period(2023, 98000, 19000, 28000),
                self._make_period(2024, 95000, 17500, 26000),
            ],
        }
        result = analyze_financial_data(data)
        assert "FY2020" in result["analysis_period"]
        assert "FY2024" in result["analysis_period"]
