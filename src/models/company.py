"""Company data model."""

from dataclasses import dataclass


@dataclass
class Company:
    name: str
    ticker: str
    cik: str | None = None
    fiscal_year_end: str = ""
    currency: str = "USD"
    industry: str = ""
    exchange: str = ""
