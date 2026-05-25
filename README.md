# reading-CFS-IS-BS

**Automated financial statement analysis pipeline** — analyze Cash Flow Statements, Income Statements, and Balance Sheets with ratio computation, trend analysis, red flag detection, and cross-statement validation.

## Features

- **4-level extraction pipeline** — SEC EDGAR XBRL API → HTML tables → PDF parsing → OCR fallback
- **22 financial ratios** across profitability, liquidity, solvency, efficiency, and cash flow quality
- **12 red flag pattern detectors** with severity ratings (critical/warning/info)
- **5 cross-statement validation checks** (earnings quality, revenue quality, demand health, depreciation consistency, interest consistency)
- **0-100 financial health scorecard** across 5 dimensions
- **Multi-format output** — JSON (machine), Markdown (readable), HTML (shareable)
- **Configurable accounting standards** (US GAAP, IFRS) and period ranges (3-10 fiscal years)

## Quick Start

```bash
# Install dependencies
uv sync

# Analyze a company (full pipeline)
uv run main.py analyze AAPL --periods 5

# Extract raw data only
uv run main.py extract MSFT --source edgar

# Parse extracted data
uv run main.py parse output/extracted_data.json

# Compute ratios
uv run main.py ratio output/parsed_data.json

# Generate report
uv run main.py report output/analyzed_data.json
```

## Data Sources (L1-L4)

| Level | Source | Status |
|-------|--------|--------|
| L1 | SEC EDGAR XBRL API + 10-K instances | Implemented |
| L2 | HTML table extraction | Implemented |
| L3 | PDF parsing (PyMuPDF) | Implemented |
| L4 | OCR fallback (Tesseract/PaddleOCR) | Implemented |

## Pipeline Architecture

```
extractor → parser → analyzer → reporter
     ↓           ↓          ↓           ↓
raw data   structured  ratios +    report
           statements  red flags   (JSON/MD/HTML)
```

## Project Structure

```
src/
├── extraction/    # Data extraction (EDGAR, HTML, PDF, OCR)
├── parsing/       # Label mapping, unit normalization, validation
├── analysis/      # Ratios, trends, red flags, scoring
├── reporting/     # Report generation (JSON, Markdown, HTML)
└── models/        # Financial dataclasses and enums

tests/             # 368+ tests across all modules
data/              # Sample data and mapping dictionaries
skills/            # AI skill definitions
```

## Development

```bash
# Run tests
uv run pytest

# Lint
uv run ruff check src/ tests/

# Type check (future)
uv run pyright src/
```

## Technology Stack

- Python 3.13+
- PyMuPDF (PDF extraction)
- BeautifulSoup4 + lxml (HTML parsing)
- requests (SEC EDGAR API)
- pytest + ruff (testing & linting)

## License

MIT
