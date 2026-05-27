"""Cross-statement validator — 5 checks across CFS/IS/BS."""

from __future__ import annotations

from typing import Any

from src.models.report_model import CrossValidationResult


def validate_earnings_quality(
    ocf_series: list[float],
    ni_series: list[float],
) -> CrossValidationResult:
    """Check: average Operating CF >= average Net Income (earnings quality)."""
    if not ocf_series or not ni_series:
        return CrossValidationResult("earnings_quality", "FAIL", "Insufficient data")
    avg_ocf = sum(ocf_series) / len(ocf_series)
    avg_ni = sum(ni_series) / len(ni_series)
    result = "PASS" if avg_ocf >= avg_ni else "WARN"
    return CrossValidationResult(
        check_name="earnings_quality",
        result=result,
        detail=f"Avg OCF {avg_ocf:,.0f} vs Avg NI {avg_ni:,.0f} over {len(ocf_series)} years",
        periods_evaluated=len(ocf_series),
    )


def _valid_pairs(
    series_a: list[float],
    series_b: list[float],
) -> tuple[list[float], list[float]]:
    """Filter both series to indices where both values are non-zero."""
    paired = [(a, b) for a, b in zip(series_a, series_b) if abs(a) > 0 and abs(b) > 0]
    if not paired:
        return [], []
    return [p[0] for p in paired], [p[1] for p in paired]


def validate_revenue_quality(
    ar_series: list[float],
    revenue_series: list[float],
) -> CrossValidationResult:
    """Check: AR growth <= Revenue growth (revenue quality)."""
    ar_f, rev_f = _valid_pairs(ar_series, revenue_series)
    if len(ar_f) < 2:
        return CrossValidationResult("revenue_quality", "FAIL", "Insufficient data")
    ar_growth = (ar_f[-1] - ar_f[0]) / abs(ar_f[0])
    rev_growth = (rev_f[-1] - rev_f[0]) / abs(rev_f[0])
    result = "PASS" if ar_growth <= rev_growth else "WARN"
    return CrossValidationResult(
        check_name="revenue_quality",
        result=result,
        detail=f"AR growth {ar_growth:.1%} vs Revenue growth {rev_growth:.1%}",
        periods_evaluated=len(ar_f),
    )


def validate_demand_health(
    inventory_series: list[float],
    revenue_series: list[float],
) -> CrossValidationResult:
    """Check: Inventory growth <= Revenue growth (demand health)."""
    inv_f, rev_f = _valid_pairs(inventory_series, revenue_series)
    if len(inv_f) < 2:
        return CrossValidationResult("demand_health", "FAIL", "Insufficient data")
    inv_growth = (inv_f[-1] - inv_f[0]) / abs(inv_f[0])
    rev_growth = (rev_f[-1] - rev_f[0]) / abs(rev_f[0])
    result = "PASS" if inv_growth <= rev_growth else "WARN"
    return CrossValidationResult(
        check_name="demand_health",
        result=result,
        detail=f"Inventory growth {inv_growth:.1%} vs Revenue growth {rev_growth:.1%}",
        periods_evaluated=len(inv_f),
    )


def validate_depreciation_consistency(
    acc_dep_series: list[float],
    dep_exp_series: list[float],
) -> CrossValidationResult:
    """Check: change in Accumulated Depreciation ≈ Depreciation Expense."""
    if len(acc_dep_series) < 2:
        return CrossValidationResult("depreciation_consistency", "FAIL", "Insufficient data")
    delta_acc_dep = acc_dep_series[-1] - acc_dep_series[0]
    if not dep_exp_series:
        return CrossValidationResult(
            "depreciation_consistency", "WARN", "No depreciation expense data"
        )
    avg_dep = sum(dep_exp_series) / len(dep_exp_series)
    if abs(avg_dep) < 1:
        return CrossValidationResult("depreciation_consistency", "PASS", "Negligible depreciation")
    ratio = abs(delta_acc_dep) / abs(avg_dep)
    result = "PASS" if 0.7 <= ratio <= 1.3 else "WARN"
    return CrossValidationResult(
        check_name="depreciation_consistency",
        result=result,
        detail=f"deltaAccDep {delta_acc_dep:,.0f} vs Avg DepExp {avg_dep:,.0f} (ratio: {ratio:.2f})",
        periods_evaluated=len(acc_dep_series),
    )


def validate_interest_consistency(
    interest_expense: float,
    total_debt: float,
    market_rate: float = 0.05,
    periods_with_debt: int = 0,
) -> CrossValidationResult:
    """Check: Interest Expense ≈ Total Debt × Market Rate."""
    if total_debt <= 0 or interest_expense <= 0:
        return CrossValidationResult(
            "interest_consistency", "PASS", "No debt interest to validate",
            periods_evaluated=periods_with_debt,
        )
    implied_rate = interest_expense / total_debt
    result = "PASS" if abs(implied_rate - market_rate) < 0.03 else "WARN"
    return CrossValidationResult(
        check_name="interest_consistency",
        result=result,
        detail=f"Implied rate {implied_rate:.1%} vs market ~{market_rate:.1%}",
        periods_evaluated=periods_with_debt,
    )


def run_cross_validation(
    periods: list[dict[str, Any]],
) -> list[CrossValidationResult]:
    """Run all 5 cross-statement checks."""
    ocf_series: list[float] = []
    ni_series: list[float] = []
    ar_series: list[float] = []
    revenue_series: list[float] = []
    inventory_series: list[float] = []
    acc_dep_series: list[float] = []
    dep_exp_series: list[float] = []

    for p in periods:
        stmts = p.get("statements", {})
        is_ = stmts.get("income_statement", {})
        bs = stmts.get("balance_sheet", {})
        cfs = stmts.get("cash_flow_statement", {})

        ocf_series.append(cfs.get("operating_cf", 0))
        ni_series.append(is_.get("net_income", 0))
        ar_series.append(bs.get("accounts_receivable", 0))
        revenue_series.append(is_.get("revenue", 0))
        inventory_series.append(bs.get("inventory", 0))
        acc_dep_series.append(bs.get("accumulated_depreciation", 0))
        dep_exp_series.append(cfs.get("depreciation_amortization", 0))

    last_is = periods[-1].get("statements", {}).get("income_statement", {}) if periods else {}
    last_bs = periods[-1].get("statements", {}).get("balance_sheet", {}) if periods else {}
    total_debt = last_bs.get("long_term_debt", 0) + last_bs.get("short_term_debt", 0)
    debt_periods = sum(
        1 for p in periods
        if p.get("statements", {}).get("balance_sheet", {}).get("long_term_debt", 0) > 0
        or p.get("statements", {}).get("balance_sheet", {}).get("short_term_debt", 0) > 0
    )

    return [
        validate_earnings_quality(ocf_series, ni_series),
        validate_revenue_quality(ar_series, revenue_series),
        validate_demand_health(inventory_series, revenue_series),
        validate_depreciation_consistency(acc_dep_series, dep_exp_series),
        validate_interest_consistency(
            last_is.get("interest_expense", 0), total_debt, periods_with_debt=debt_periods
        ),
    ]
