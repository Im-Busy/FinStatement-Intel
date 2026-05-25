"""End-to-end integration tests for the full pipeline."""

from unittest.mock import patch

from src.analysis import analyze_financial_data
from src.extraction import extract_financial_data
from src.parsing import parse_financial_data
from src.reporting import generate_report


class TestFullPipeline:
    """Test the complete extract -> parse -> analyze -> report pipeline."""

    @patch("src.extraction.edgar_client.get_cik")
    @patch("src.extraction.edgar_client.get_submissions")
    @patch("src.extraction.edgar_client.get_annual_filings")
    @patch("src.extraction.html_extractor.extract_from_html_filing")
    def test_pipeline_warning_data_flows(self, mock_html, mock_filings, mock_submissions, mock_cik):
        """HTML extraction with no usable data returns WARNING — pipeline handles it."""
        mock_cik.return_value = "0000000000"
        mock_submissions.return_value = {
            "filings": {"recent": {"form": [], "accessionNumber": [], "primaryDocument": []}}
        }
        mock_filings.return_value = []
        raw = extract_financial_data("TEST", periods=1, source="html")
        assert raw["company"]["ticker"] == "TEST"

        parsed = parse_financial_data(raw)
        assert parsed["status"] == "WARNING"

        analyzed = analyze_financial_data(parsed)
        assert analyzed["status"] == "WARNING"

        report = generate_report(analyzed)
        assert report["status"] == "SUCCESS"

    def test_pipeline_edgar_with_fake_ticker(self):
        """EDGAR extraction with unknown ticker returns ERROR, pipeline handles it."""
        raw = extract_financial_data("ZZZZUNKNOWN", periods=1, source="edgar")
        assert raw["status"] == "ERROR"

    def test_pipeline_unknown_source(self):
        raw = extract_financial_data("TEST", periods=1, source="invalid_source")
        assert raw["status"] == "ERROR"

    def test_pipeline_report_error_data(self):
        report = generate_report({"status": "ERROR"})
        assert report["status"] == "ERROR"


class TestCrossComponent:
    """Test data flow between specific pipeline components."""

    @patch("src.extraction.edgar_client.get_cik")
    @patch("src.extraction.edgar_client.get_submissions")
    @patch("src.extraction.edgar_client.get_annual_filings")
    def test_parser_handles_empty_periods(self, mock_filings, mock_submissions, mock_cik):
        mock_cik.return_value = "0000000000"
        mock_submissions.return_value = {
            "filings": {"recent": {"form": [], "accessionNumber": [], "primaryDocument": []}}
        }
        mock_filings.return_value = []
        raw = extract_financial_data("TEST", periods=1, source="html")
        parsed = parse_financial_data(raw)
        assert "periods" in parsed
        assert len(parsed["periods"]) == 0

    @patch("src.extraction.edgar_client.get_cik")
    @patch("src.extraction.edgar_client.get_submissions")
    @patch("src.extraction.edgar_client.get_annual_filings")
    def test_analyzer_handles_empty_periods(self, mock_filings, mock_submissions, mock_cik):
        mock_cik.return_value = "0000000000"
        mock_submissions.return_value = {
            "filings": {"recent": {"form": [], "accessionNumber": [], "primaryDocument": []}}
        }
        mock_filings.return_value = []
        raw = extract_financial_data("TEST", periods=1, source="html")
        parsed = parse_financial_data(raw)
        analyzed = analyze_financial_data(parsed)
        assert analyzed["status"] == "WARNING"
        assert analyzed["periods_analyzed"] == 0
