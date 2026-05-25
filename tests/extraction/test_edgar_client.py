"""Tests for SEC EDGAR API client — CIK lookup, facts, submissions."""

from unittest.mock import MagicMock, patch

import pytest

from src.extraction.edgar_client import (
    get_annual_filings,
    get_cik,
    get_company_facts,
    get_submissions,
)

SAMPLE_COMPANY_TICKERS = {
    "0": {"cik_str": 0, "ticker": "UNKNOWN", "title": "Unknown Co"},
    "1": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."},
    "2": {"cik_str": 789019, "ticker": "MSFT", "title": "Microsoft Corp"},
}


SAMPLE_FACTS = {
    "cik": 320193,
    "entityName": "Apple Inc.",
    "facts": {
        "us-gaap": {
            "Revenues": {
                "label": "Revenues",
                "units": {
                    "USD": [
                        {
                            "fy": 2024,
                            "fp": "FY",
                            "end": "2024-09-30",
                            "val": 391035000000,
                            "form": "10-K",
                        },
                        {
                            "fy": 2023,
                            "fp": "FY",
                            "end": "2023-09-30",
                            "val": 383285000000,
                            "form": "10-K",
                        },
                    ]
                },
            },
            "Assets": {
                "label": "Assets",
                "units": {
                    "USD": [
                        {
                            "fy": 2024,
                            "fp": "FY",
                            "end": "2024-09-30",
                            "val": 364980000000,
                            "form": "10-K",
                        },
                    ]
                },
            },
        }
    },
}


SAMPLE_SUBMISSIONS = {
    "filings": {
        "recent": {
            "form": ["10-K", "10-Q", "10-K", "8-K"],
            "accessionNumber": [
                "0000320193-24-000123",
                "0000320193-24-000089",
                "0000320193-23-000106",
                "0000320193-24-000150",
            ],
            "filingDate": ["2024-11-01", "2024-07-30", "2023-11-02", "2024-05-01"],
            "reportDate": ["2024-09-30", "2024-06-30", "2023-09-30", "2024-04-01"],
            "primaryDocument": [
                "aapl-20240930.htm",
                "aapl-20240630.htm",
                "aapl-20230930.htm",
                "aapl-20240401.htm",
            ],
        }
    }
}


class TestGetCik:
    def test_get_cik_success(self):
        with patch("src.extraction.edgar_client._get_session") as mock_session:
            mock_resp = MagicMock()
            mock_resp.json.return_value = SAMPLE_COMPANY_TICKERS
            mock_resp.raise_for_status.return_value = None
            mock_session.return_value.get.return_value = mock_resp

            result = get_cik("AAPL")
            assert result == "0000320193"

    def test_get_cik_case_insensitive(self):
        with patch("src.extraction.edgar_client._get_session") as mock_session:
            mock_resp = MagicMock()
            mock_resp.json.return_value = SAMPLE_COMPANY_TICKERS
            mock_resp.raise_for_status.return_value = None
            mock_session.return_value.get.return_value = mock_resp

            result = get_cik("aapl")
            assert result == "0000320193"

    def test_get_cik_not_found(self):
        with patch("src.extraction.edgar_client._get_session") as mock_session:
            mock_resp = MagicMock()
            mock_resp.json.return_value = SAMPLE_COMPANY_TICKERS
            mock_resp.raise_for_status.return_value = None
            mock_session.return_value.get.return_value = mock_resp

            with pytest.raises(ValueError, match="not found"):
                get_cik("ZZZZ")


class TestGetCompanyFacts:
    def test_get_company_facts_success(self):
        with patch("src.extraction.edgar_client._get_session") as mock_session:
            mock_resp = MagicMock()
            mock_resp.json.return_value = SAMPLE_FACTS
            mock_resp.raise_for_status.return_value = None
            mock_session.return_value.get.return_value = mock_resp

            result = get_company_facts("0000320193")
            assert result["entityName"] == "Apple Inc."
            assert "Revenues" in result["facts"]["us-gaap"]


class TestGetSubmissions:
    def test_get_submissions_success(self):
        with patch("src.extraction.edgar_client._get_session") as mock_session:
            mock_resp = MagicMock()
            mock_resp.json.return_value = SAMPLE_SUBMISSIONS
            mock_resp.raise_for_status.return_value = None
            mock_session.return_value.get.return_value = mock_resp

            result = get_submissions("0000320193")
            assert "filings" in result


class TestGetAnnualFilings:
    def test_filters_10k_correctly(self):
        filings = get_annual_filings(SAMPLE_SUBMISSIONS, form_type="10-K", limit=5)
        assert len(filings) == 2
        assert all(f["form_type"] == "10-K" for f in filings)
        assert filings[0]["accession_number"] == "0000320193-24-000123"
