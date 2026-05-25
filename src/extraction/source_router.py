"""Source router — auto-escalation L1→L2→L3→L4 with availability checks.

When source='auto', attempts extraction in priority order:
    L1 (EDGAR XBRL) → L2 (HTML) → L3 (PDF) → L4 (OCR)

Each level is tried; the first level returning a successful result is used.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)

HandlerFunc = Callable[[str, int], dict[str, Any]]

_ESCALATION_ORDER: list[str] = ["edgar", "html", "pdf", "ocr"]


def route_source(
    source: str,
    ticker: str,
    periods: int,
) -> dict[str, Any]:
    """Route extraction to the appropriate handler with auto-escalation.

    Args:
        source: Source preference ('edgar', 'html', 'pdf', 'ocr', or 'auto').
        ticker: Stock ticker symbol.
        periods: Number of fiscal periods to extract.

    Returns:
        Extraction result dict.
    """
    from src.extraction.extractor import SOURCE_HANDLERS
    from src.extraction.extractor import extract_financial_data as _extract

    if source == "auto":
        logger.info("Auto-escalation enabled for %s — trying L1→L2→L3→L4", ticker)
        warnings: list[str] = []
        for level_source in _ESCALATION_ORDER:
            logger.info("Trying %s extraction for %s", level_source, ticker)
            result = _extract(ticker, periods, source=level_source)

            if result.get("status") == "SUCCESS" and result.get("periods"):
                if warnings:
                    result.setdefault("warnings", [])
                    result["warnings"].extend(warnings)
                result.setdefault("metadata", {})["auto_escalated_from"] = level_source
                return result

            if result.get("status") == "WARNING":
                warnings.append(f"{level_source}: {result.get('message', 'no data')}")

            if result.get("status") == "ERROR":
                warnings.append(f"{level_source}: {result.get('message', 'extraction failed')}")

        return {
            "status": "ERROR",
            "message": f"All extraction methods failed for {ticker}",
            "company": {"name": ticker.upper(), "ticker": ticker.upper(), "fiscal_year_end": ""},
            "periods": [],
            "warnings": warnings,
        }

    handler_name = SOURCE_HANDLERS.get(source)
    if handler_name is None:
        return {
            "status": "ERROR",
            "message": f"Unknown source '{source}'. Valid sources: {list(SOURCE_HANDLERS)}, auto",
        }

    from src.extraction.extractor import (
        _extract_from_edgar,
        _extract_from_external,
        _extract_from_html,
        _extract_from_ocr,
        _extract_from_pdf,
    )

    handler_map: dict[str, HandlerFunc] = {
        "_extract_from_edgar": _extract_from_edgar,
        "_extract_from_html": _extract_from_html,
        "_extract_from_pdf": _extract_from_pdf,
        "_extract_from_ocr": _extract_from_ocr,
        "_extract_from_external": _extract_from_external,
    }

    handler = handler_map.get(handler_name)
    if handler is None:
        return {
            "status": "ERROR",
            "message": f"Source handler '{handler_name}' not found",
        }

    result = handler(ticker, periods)

    if "metadata" not in result:
        result["metadata"] = {
            "extraction_method": source,
            "periods_requested": periods,
            "periods_extracted": len(result.get("periods", [])),
        }
    if "warnings" not in result:
        result["warnings"] = []
    result.setdefault(
        "company", {"name": ticker.upper(), "ticker": ticker.upper(), "fiscal_year_end": ""}
    )

    return result
