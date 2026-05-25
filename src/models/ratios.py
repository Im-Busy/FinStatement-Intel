"""Financial ratio data models — 5 categories, 22 ratios."""

from dataclasses import dataclass, field


@dataclass
class RatioPoint:
    period: str
    value: float
    unit: str = ""


@dataclass
class ProfitabilityRatios:
    gross_margin: list[RatioPoint] = field(default_factory=list)
    operating_margin: list[RatioPoint] = field(default_factory=list)
    net_margin: list[RatioPoint] = field(default_factory=list)
    roa: list[RatioPoint] = field(default_factory=list)
    roe: list[RatioPoint] = field(default_factory=list)
    ebitda_margin: list[RatioPoint] = field(default_factory=list)


@dataclass
class LiquidityRatios:
    current_ratio: list[RatioPoint] = field(default_factory=list)
    quick_ratio: list[RatioPoint] = field(default_factory=list)
    working_capital: list[RatioPoint] = field(default_factory=list)
    operating_cf_ratio: list[RatioPoint] = field(default_factory=list)


@dataclass
class SolvencyRatios:
    debt_to_equity: list[RatioPoint] = field(default_factory=list)
    debt_to_assets: list[RatioPoint] = field(default_factory=list)
    interest_coverage: list[RatioPoint] = field(default_factory=list)
    lt_debt_to_equity: list[RatioPoint] = field(default_factory=list)


@dataclass
class EfficiencyRatios:
    asset_turnover: list[RatioPoint] = field(default_factory=list)
    receivables_turnover: list[RatioPoint] = field(default_factory=list)
    inventory_turnover: list[RatioPoint] = field(default_factory=list)
    days_sales_outstanding: list[RatioPoint] = field(default_factory=list)


@dataclass
class CashFlowQualityRatios:
    fcf: list[RatioPoint] = field(default_factory=list)
    fcf_margin: list[RatioPoint] = field(default_factory=list)
    cf_to_ni: list[RatioPoint] = field(default_factory=list)
    fcf_to_ni: list[RatioPoint] = field(default_factory=list)
