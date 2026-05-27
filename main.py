"""Financial statement analysis entry point.

Provides CLI access to the 4-agent pipeline:
    extractor -> parser -> analyzer -> reporter

Usage:
    uv run main.py analyze AAPL --periods 5
    uv run main.py analyze AAPL --format markdown --output aapl_report.md
    uv run main.py extract MSFT --source edgar
    uv run main.py extract MSFT --save-sample
    uv run main.py parse output/extracted_data.json
    uv run main.py ratio output/parsed_data.json
    uv run main.py report output/analyzed_data.json --format html

    # File-based extraction (any format):
    uv run main.py analyze --file statement.pdf --ticker AAPL
    uv run main.py extract --file screenshot.png --vision-backend openai_compatible
    uv run main.py extract --file report.docx --ticker MSFT
"""

import argparse
import json
import sys
from pathlib import Path

from src.analysis import analyze_financial_data
from src.extraction import extract_financial_data, extract_from_file
from src.parsing import parse_financial_data
from src.reporting import generate_report
from src.reporting.html_renderer import render_html
from src.reporting.json_serializer import render_json
from src.reporting.markdown_renderer import render_markdown

OUTPUT_FORMATS = ("json", "markdown", "html")
SAMPLES_DIR = Path("data/samples")


def _render_report(report: dict, fmt: str) -> str:
    """Render a report dict in the requested format.

    Args:
        report: The 'report' key from generate_report output.
        fmt: One of 'json', 'markdown', 'html'.

    Returns:
        Rendered string.
    """
    if fmt == "markdown":
        return render_markdown(report)
    if fmt == "html":
        return render_html(report)
    return render_json(report)


def _output_result(result: dict, fmt: str, output: str | None) -> None:
    """Render and optionally save the result to a file.

    Args:
        result: The reporter output dict with 'status' and 'report' keys.
        fmt: Output format.
        output: Optional file path to save to.
    """
    inner = result.get("report", result)
    rendered = _render_report(inner, fmt)

    if output:
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(rendered, encoding="utf-8")
        print(f"Report saved to {path.resolve()}")
    else:
        print(rendered)


def _save_sample(raw_data: dict, ticker: str) -> None:
    """Save extracted raw data as a sample for offline use.

    Args:
        raw_data: Raw extraction output.
        ticker: Company ticker symbol.
    """
    periods = raw_data.get("periods", [])
    if not periods:
        print("No period data to save as sample")
        return

    years = sorted({p.get("fiscal_year", 0) for p in periods})
    min_year, max_year = min(years), max(years)
    filename = f"{ticker.lower()}_{min_year}_{max_year}.json"
    filepath = SAMPLES_DIR / filename

    SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
    filepath.write_text(json.dumps(raw_data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Sample saved to {filepath.resolve()}")


def cmd_analyze(args: argparse.Namespace) -> None:
    """Run the full pipeline: extract -> parse -> analyze -> report."""
    if args.file:
        raw_data = _extract_from_file(args)
    else:
        print(f"Analyzing {args.ticker} ({args.periods} periods, source: {args.source})...")
        raw_data = extract_financial_data(args.ticker, periods=args.periods, source=args.source)

    if raw_data["status"] == "ERROR":
        print(json.dumps(raw_data, indent=2))
        sys.exit(1)

    parsed_data = parse_financial_data(raw_data)
    if parsed_data["status"] == "ERROR":
        print(json.dumps(parsed_data, indent=2))
        sys.exit(1)

    analyzed_data = analyze_financial_data(parsed_data)
    if analyzed_data["status"] == "ERROR":
        print(json.dumps(analyzed_data, indent=2))
        sys.exit(1)

    report = generate_report(analyzed_data)
    _output_result(report, args.format, args.output)


def cmd_extract(args: argparse.Namespace) -> None:
    """Run extraction only."""
    if args.file:
        result = _extract_from_file(args)
    else:
        result = extract_financial_data(args.ticker, periods=args.periods, source=args.source)

    if args.save_sample and result["status"] != "ERROR":
        _save_sample(result, args.ticker or result.get("company", {}).get("ticker", "unknown"))
    else:
        print(json.dumps(result, indent=2))


def _extract_from_file(args: argparse.Namespace) -> dict:
    """Extract financial data from a local file using auto-detection."""
    file_type = Path(args.file).suffix
    ticker = args.ticker or ""
    print(f"Extracting from {args.file} ({file_type})...")
    return extract_from_file(
        args.file,
        ticker=ticker,
        periods=args.periods,
        vision_backend=args.vision_backend,
    )


def cmd_parse(args: argparse.Namespace) -> None:
    """Run parsing only."""
    raw_data = json.loads(Path(args.input_file).read_text())
    result = parse_financial_data(raw_data)
    print(json.dumps(result, indent=2))


def cmd_ratio(args: argparse.Namespace) -> None:
    """Run analysis only."""
    parsed_data = json.loads(Path(args.input_file).read_text())
    result = analyze_financial_data(parsed_data)
    print(json.dumps(result, indent=2))


def cmd_report(args: argparse.Namespace) -> None:
    """Run reporting only."""
    analyzed_data = json.loads(Path(args.input_file).read_text())
    result = generate_report(analyzed_data)
    _output_result(result, args.format, args.output)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Financial Statement Analysis Pipeline",
        prog="reading-cfs-is-bs",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze_parser = subparsers.add_parser("analyze", help="Run full analysis pipeline")
    analyze_parser.add_argument("ticker", nargs="?", help="Stock ticker symbol")
    analyze_parser.add_argument("--file", "-f", help="Local file path (PDF, image, DOCX, XLSX)")
    analyze_parser.add_argument("--periods", type=int, default=5, help="Number of periods")
    analyze_parser.add_argument("--source", default="edgar", help="Data source (for ticker mode)")
    analyze_parser.add_argument("--vision-backend", help="Vision backend: local, openai_compatible, anthropic")
    analyze_parser.add_argument(
        "--format", choices=OUTPUT_FORMATS, default="json", help="Report output format"
    )
    analyze_parser.add_argument("--output", "-o", help="Save report to file")
    analyze_parser.set_defaults(func=cmd_analyze)

    extract_parser = subparsers.add_parser("extract", help="Extract raw financial data")
    extract_parser.add_argument("ticker", nargs="?", help="Stock ticker symbol")
    extract_parser.add_argument("--file", "-f", help="Local file path (PDF, image, DOCX, XLSX)")
    extract_parser.add_argument("--periods", type=int, default=5, help="Number of periods")
    extract_parser.add_argument("--source", default="edgar", help="Data source (for ticker mode)")
    extract_parser.add_argument("--vision-backend", help="Vision backend: local, openai_compatible, anthropic")
    extract_parser.add_argument(
        "--save-sample",
        action="store_true",
        help="Save extracted data as sample for offline use",
    )
    extract_parser.set_defaults(func=cmd_extract)

    parse_parser = subparsers.add_parser("parse", help="Parse raw data into structured statements")
    parse_parser.add_argument("input_file", help="JSON file from extraction")
    parse_parser.set_defaults(func=cmd_parse)

    ratio_parser = subparsers.add_parser("ratio", help="Compute financial ratios")
    ratio_parser.add_argument("input_file", help="JSON file from parsing")
    ratio_parser.set_defaults(func=cmd_ratio)

    report_parser = subparsers.add_parser("report", help="Generate analysis report")
    report_parser.add_argument("input_file", help="JSON file from analysis")
    report_parser.add_argument(
        "--format", choices=OUTPUT_FORMATS, default="json", help="Report output format"
    )
    report_parser.add_argument("--output", "-o", help="Save report to file")
    report_parser.set_defaults(func=cmd_report)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
