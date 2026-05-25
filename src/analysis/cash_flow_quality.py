"""Cash flow quality indicators — FCF, FCF margin, CF-to-NI, FCF-to-NI."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def compute_fcf(operating_cf: float, capex: float) -> float:
    """FCF = Operating CF - |CapEx|. CapEx is stored as negative."""
    return round(operating_cf - abs(capex), 2)


def compute_fcf_margin(fcf: float, revenue: float) -> float | None:
    """FCF Margin = FCF / Revenue."""
    if revenue == 0:
        return None
    return round(fcf / revenue, 4)


def compute_cf_to_ni(operating_cf: float, net_income: float) -> float | None:
    """CF-to-NI = Operating CF / Net Income."""
    if net_income == 0:
        return None
    return round(operating_cf / net_income, 4)


def compute_fcf_to_ni(fcf: float, net_income: float) -> float | None:
    """FCF-to-NI = FCF / Net Income."""
    if net_income == 0:
        return None
    return round(fcf / net_income, 4)
