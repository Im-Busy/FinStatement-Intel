"""Subtotal calculator — computes derived financial fields not in raw data."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from src.models.statements import BalanceSheet, CashFlowStatement, IncomeStatement

COMPUTED_FIELDS: list[tuple[str, Callable, str]] = [
    (
        "gross_profit",
        lambda is_: round(is_.revenue - is_.cogs, 2) if is_.revenue and is_.cogs else 0.0,
        "income_statement",
    ),
    (
        "ebitda",
        lambda is_, cfs: (
            round(is_.operating_income + cfs.depreciation_amortization, 2)
            if is_.operating_income and cfs.depreciation_amortization
            else 0.0
        ),
        "cross",
    ),
    (
        "working_capital",
        lambda bs: (
            round(bs.current_assets - bs.current_liabilities, 2)
            if bs.current_assets and bs.current_liabilities
            else 0.0
        ),
        "balance_sheet",
    ),
    (
        "net_change_cash",
        lambda cfs: (
            round(cfs.operating_cf + cfs.investing_cf + cfs.financing_cf, 2)
            if any([cfs.operating_cf, cfs.investing_cf, cfs.financing_cf])
            else 0.0
        ),
        "cash_flow_statement",
    ),
    (
        "fcf",
        lambda cfs: (
            round(cfs.operating_cf - abs(cfs.capex), 2) if cfs.operating_cf and cfs.capex else 0.0
        ),
        "cash_flow_statement",
    ),
]


def set_if_zero(target: object, attr: str, value: float) -> None:
    """Set attribute on object only if it is currently 0.0."""
    current = getattr(target, attr, None)
    if current is not None and current == 0.0:
        setattr(target, attr, value)


def compute_derived_fields(
    income_statement: IncomeStatement,
    balance_sheet: BalanceSheet,
    cash_flow_statement: CashFlowStatement,
) -> dict[str, Any]:
    """Compute derived/subtotal fields not explicitly in raw data.

    Only fills in fields that are currently 0.0 — never overwrites existing data.

    Args:
        income_statement: Parsed income statement.
        balance_sheet: Parsed balance sheet.
        cash_flow_statement: Parsed cash flow statement.

    Returns:
        Dict with computed field names and values.
    """
    computed: dict[str, Any] = {}

    for field_name, compute_fn, scope in COMPUTED_FIELDS:
        try:
            if scope == "income_statement":
                value = compute_fn(income_statement)
            elif scope == "balance_sheet":
                value = compute_fn(balance_sheet)
            elif scope == "cash_flow_statement":
                value = compute_fn(cash_flow_statement)
            elif scope == "cross":
                value = compute_fn(income_statement, cash_flow_statement)
            else:
                continue

            if value != 0.0:
                computed[field_name] = value

                if field_name == "gross_profit":
                    set_if_zero(income_statement, "gross_profit", value)
                elif field_name == "ebitda":
                    set_if_zero(income_statement, "ebitda", value)
                elif field_name == "net_change_cash":
                    set_if_zero(cash_flow_statement, "net_change_cash", value)
                elif field_name == "fcf":
                    pass
                elif field_name == "working_capital":
                    pass
        except Exception:
            continue

    return computed
