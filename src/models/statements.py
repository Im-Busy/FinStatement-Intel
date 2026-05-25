"""Structured financial statement data models."""

from dataclasses import dataclass, field

from src.models.line_item import UnmappedItem


@dataclass
class IncomeStatement:
    revenue: float = 0.0
    cogs: float = 0.0
    gross_profit: float = 0.0
    operating_expenses: float = 0.0
    rnd_expense: float = 0.0
    sga_expense: float = 0.0
    operating_income: float = 0.0
    interest_expense: float = 0.0
    interest_income: float = 0.0
    income_tax: float = 0.0
    net_income: float = 0.0
    eps_basic: float = 0.0
    eps_diluted: float = 0.0
    ebitda: float = 0.0
    unmapped: list[UnmappedItem] = field(default_factory=list)


@dataclass
class BalanceSheet:
    total_assets: float = 0.0
    current_assets: float = 0.0
    cash_and_equivalents: float = 0.0
    accounts_receivable: float = 0.0
    inventory: float = 0.0
    total_liabilities: float = 0.0
    current_liabilities: float = 0.0
    long_term_debt: float = 0.0
    total_equity: float = 0.0
    goodwill: float = 0.0
    ppe_net: float = 0.0
    accounts_payable: float = 0.0
    short_term_debt: float = 0.0
    accumulated_depreciation: float = 0.0
    unmapped: list[UnmappedItem] = field(default_factory=list)


@dataclass
class CashFlowStatement:
    operating_cf: float = 0.0
    investing_cf: float = 0.0
    financing_cf: float = 0.0
    capex: float = 0.0
    depreciation_amortization: float = 0.0
    net_change_cash: float = 0.0
    dividends_paid: float = 0.0
    stock_issuance: float = 0.0
    debt_repayment: float = 0.0
    debt_issuance: float = 0.0
    fx_effect: float = 0.0
    net_income: float = 0.0
    unmapped: list[UnmappedItem] = field(default_factory=list)
