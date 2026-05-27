"""Data extraction module — SEC EDGAR, 10-K XBRL instances, HTML, PDF, OCR, image, file routing."""

from src.extraction.external_searcher import find_and_download_financial_data
from src.extraction.extractor import extract_financial_data, extract_from_file
from src.extraction.filing_fetcher import fetch_10k_xbrl_facts, fetch_companyfacts_api
from src.extraction.source_router import route_source

__all__ = [
    "extract_financial_data",
    "extract_from_file",
    "fetch_10k_xbrl_facts",
    "fetch_companyfacts_api",
    "find_and_download_financial_data",
    "route_source",
]
