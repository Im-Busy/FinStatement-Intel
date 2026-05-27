"""Structure validator — hardcoded accounting identity and structural integrity checks."""

from __future__ import annotations

from src.config import ACCOUNTING_EQ_TOLERANCE, CF_RECONCILIATION_TOLERANCE
from src.models.period import Period, ValidationResult


def validate_balance_sheet(
    assets: float,
    liabilities: float,
    equity: float,
) -> ValidationResult:
    """Verify A = L + E with tolerance.

    Args:
        assets: Total assets.
        liabilities: Total liabilities.
        equity: Total shareholders' equity.

    Returns:
        ValidationResult with check details.
    """
    expected = liabilities + equity
    difference = assets - expected
    diff_pct = abs(difference) / max(abs(assets), 1.0)

    return ValidationResult(
        check_name="accounting_equation",
        holds=diff_pct < ACCOUNTING_EQ_TOLERANCE,
        expected=expected,
        actual=assets,
        difference=difference,
        diff_pct=round(diff_pct, 6),
        detail=(
            f"A ({assets:,.2f}) = L ({liabilities:,.2f}) + E ({equity:,.2f}) "
            f"→ diff {difference:,.2f} ({diff_pct:.4%})"
        ),
    )


def validate_cash_flow_reconciliation(
    operating_cf: float,
    investing_cf: float,
    financing_cf: float,
    net_change: float,
) -> ValidationResult:
    """Verify ΔCash = OCF + ICF + FCF.

    Args:
        operating_cf: Cash flow from operating activities.
        investing_cf: Cash flow from investing activities.
        financing_cf: Cash flow from financing activities.
        net_change: Net change in cash reported.

    Returns:
        ValidationResult with check details.
    """
    expected = operating_cf + investing_cf + financing_cf
    difference = net_change - expected
    diff_pct = abs(difference) / max(abs(net_change), 1.0)

    return ValidationResult(
        check_name="cash_flow_reconciliation",
        holds=diff_pct < CF_RECONCILIATION_TOLERANCE,
        expected=expected,
        actual=net_change,
        difference=difference,
        diff_pct=round(diff_pct, 6),
        detail=(
            f"ΔCash ({net_change:,.2f}) = OCF ({operating_cf:,.2f}) + "
            f"ICF ({investing_cf:,.2f}) + FCF ({financing_cf:,.2f}) "
            f"→ diff {difference:,.2f} ({diff_pct:.4%})"
        ),
    )


def validate_income_statement_arithmetic(
    revenue: float,
    cogs: float,
    gross_profit: float,
) -> ValidationResult:
    """Verify Gross Profit = Revenue - COGS.

    Args:
        revenue: Total revenue.
        cogs: Cost of goods sold.
        gross_profit: Reported gross profit.

    Returns:
        ValidationResult with check details.
    """
    expected = revenue - cogs
    difference = gross_profit - expected
    diff_pct = abs(difference) / max(abs(gross_profit), 1.0)

    return ValidationResult(
        check_name="income_statement_arithmetic",
        holds=diff_pct < ACCOUNTING_EQ_TOLERANCE,
        expected=expected,
        actual=gross_profit,
        difference=difference,
        diff_pct=round(diff_pct, 6),
        detail=(
            f"GP ({gross_profit:,.2f}) = Rev ({revenue:,.2f}) - "
            f"COGS ({cogs:,.2f}) → diff {difference:,.2f} ({diff_pct:.4%})"
        ),
    )


def validate_gross_profit_plausibility(
    revenue: float,
    gross_profit: float,
) -> ValidationResult:
    """Verify gross_profit is less than revenue (plausibility check).

    Args:
        revenue: Total revenue.
        gross_profit: Reported gross profit.

    Returns:
        ValidationResult — fails if gross_profit >= revenue.
    """
    holds = gross_profit < revenue
    detail = (
        f"GP ({gross_profit:,.2f}) vs Rev ({revenue:,.2f}) — "
        f"gross_profit is {gross_profit / revenue:.0%} of revenue"
    )
    if not holds:
        detail += " [IMPLAUSIBLE: gross_profit >= revenue]"

    return ValidationResult(
        check_name="gross_profit_plausibility",
        holds=holds,
        expected=revenue,
        actual=gross_profit,
        difference=gross_profit - revenue,
        diff_pct=round(abs(gross_profit - revenue) / max(abs(revenue), 1.0), 6),
        detail=detail,
    )


def run_all_validations(period: Period) -> list[ValidationResult]:
    """Run all applicable structural validations for a period.

    Args:
        period: Parsed Period with populated statements.

    Returns:
        List of ValidationResult objects.
    """
    results: list[ValidationResult] = []

    bs = period.balance_sheet
    if bs.total_assets and (bs.total_liabilities or bs.total_equity):
        results.append(
            validate_balance_sheet(bs.total_assets, bs.total_liabilities, bs.total_equity)
        )

    cfs = period.cash_flow_statement
    if cfs.net_change_cash:
        results.append(
            validate_cash_flow_reconciliation(
                cfs.operating_cf,
                cfs.investing_cf,
                cfs.financing_cf,
                cfs.net_change_cash,
            )
        )

    is_ = period.income_statement
    if is_.revenue and is_.cogs and is_.gross_profit:
        results.append(
            validate_income_statement_arithmetic(
                is_.revenue,
                is_.cogs,
                is_.gross_profit,
            )
        )
    if is_.revenue and is_.gross_profit and is_.gross_profit > 0:
        results.append(
            validate_gross_profit_plausibility(is_.revenue, is_.gross_profit)
        )

    return results
