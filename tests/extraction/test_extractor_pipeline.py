"""Tests for the extraction pipeline orchestrator."""

from unittest.mock import patch

from src.extraction.extractor import extract_financial_data


class TestExtractFinancialData:
    def test_unknown_source(self):
        result = extract_financial_data("AAPL", source="unknown")
        assert result["status"] == "ERROR"
        assert "Unknown source" in result["message"]

    @patch("src.extraction.extractor.get_cik")
    @patch("src.extraction.extractor.get_company_facts")
    @patch("src.extraction.extractor.parse_company_facts")
    def test_edgar_extraction_success(self, mock_parse, mock_facts, mock_cik):
        mock_cik.return_value = "0000320193"
        mock_facts.return_value = {"facts": {"us-gaap": {"Revenues": {}}}}
        mock_parse.return_value = {
            "status": "SUCCESS",
            "company": {"name": "Apple Inc.", "ticker": "AAPL"},
            "periods": [
                {
                    "type": "annual",
                    "fiscal_year": 2024,
                    "end_date": "2024-09-30",
                    "source": "sec-edgar-xbrl",
                    "statements": {"IS": {}, "BS": {}, "CFS": {}},
                }
            ],
        }

        result = extract_financial_data("AAPL", periods=3, source="edgar")
        assert result["status"] == "SUCCESS"
        assert result["company"]["ticker"] == "AAPL"

    @patch("src.extraction.extractor.get_cik")
    def test_ticker_not_found(self, mock_cik):
        mock_cik.side_effect = ValueError("Ticker 'ZZZZ' not found")

        result = extract_financial_data("ZZZZ", source="edgar")
        assert result["status"] == "ERROR"
        assert "not found" in result["message"]

    @patch("src.extraction.edgar_client.get_cik")
    def test_html_source_error_on_unknown_ticker(self, mock_cik):
        mock_cik.side_effect = ValueError("Ticker 'ZZZZ' not found")
        result = extract_financial_data("ZZZZ", source="html")
        assert result["status"] == "ERROR"
        assert "not found" in result["message"]

    @patch("src.extraction.edgar_client.get_cik")
    @patch("src.extraction.edgar_client.get_submissions")
    @patch("src.extraction.edgar_client.get_annual_filings")
    def test_html_source_no_filings(self, mock_filings, mock_submissions, mock_cik):
        mock_cik.return_value = "0000320193"
        mock_submissions.return_value = {
            "filings": {"recent": {"form": [], "accessionNumber": [], "primaryDocument": []}}
        }
        mock_filings.return_value = []
        result = extract_financial_data("AAPL", source="html")
        assert result["status"] == "WARNING"

    @patch("src.extraction.edgar_client.get_cik")
    def test_pdf_source_error_on_unknown_ticker(self, mock_cik):
        mock_cik.side_effect = ValueError("Ticker 'ZZZZ' not found")
        result = extract_financial_data("ZZZZ", source="pdf")
        assert result["status"] == "ERROR"

    @patch("src.extraction.edgar_client.get_cik")
    def test_ocr_source_error_on_unknown_ticker(self, mock_cik):
        mock_cik.side_effect = ValueError("Ticker 'ZZZZ' not found")
        result = extract_financial_data("ZZZZ", source="ocr")
        assert result["status"] == "ERROR"
