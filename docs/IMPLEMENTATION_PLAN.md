# reading-CFS-IS-BS — Implementation Plan

> **Last updated:** 2026-05-25
> **Target:** Fully functional 4-agent pipeline (extract→parse→analyze→report) for US-listed companies via SEC EDGAR

---

## Table of Contents

1. [Roadmap Overview](#1-roadmap-overview)
2. [Phase 0: Foundation](#2-phase-0-foundation)
3. [Phase 1: Extraction (L1 — SEC EDGAR XBRL)](#3-phase-1-extraction-l1--sec-edgar-xbrl)
4. [Phase 2: Parsing & Normalization](#4-phase-2-parsing--normalization)
5. [Phase 3: Analysis Engine](#5-phase-3-analysis-engine)
6. [Phase 4: Report Generation](#6-phase-4-report-generation)
7. [Phase 5: Integration & Polish](#7-phase-5-integration--polish)
8. [Phase 6: Advanced Extraction (L2-L4)](#8-phase-6-advanced-extraction-l2-l4-future)
9. [Phase 7: Hardening & Production](#9-phase-7-hardening--production-future)

---

## 1. Roadmap Overview

```
Phase 0: Foundation (models, config, test infra)
    │
Phase 1: Extraction — SEC EDGAR XBRL (L1 only)
    │
Phase 2: Parsing — label mapping, unit norm, validation
    │
Phase 3: Analysis — 22 ratios, trends, red flags, scoring
    │
Phase 4: Reporting — JSON, Markdown, HTML output
    │
Phase 5: Integration — full pipeline tests, CLI polish
    │
Phase 6: Advanced Extraction — L2 HTML, L3 PDF, L4 OCR (future)
    │
Phase 7: Hardening — error recovery, logging, docs (future)
```

**MVP scope (Phases 0-5):** Full pipeline working for US companies via SEC EDGAR XBRL (L1).  
**Deferred (Phases 6-7):** HTML/PDF/OCR extraction, advanced hardening.

---

## 2. Phase 0: Foundation

**Goal:** Establish data models, project config, test infrastructure, and dependency baseline. Everything subsequent phases build on.

### Step 0.1 — Install Dependencies

```bash
# Already in pyproject.toml: requests, pydantic, python-dotenv, pytest, ruff
uv sync
uv add lxml          # XBRL XML parsing
uv add beautifulsoup4 # HTML parsing (future L2)
```

**Verification:** `uv run pytest` runs (0 tests but no import errors).

**Estimated files:** 0 new, 1 modified (`pyproject.toml`)

### Step 0.2 — Create `src/config.py`

Module-level constants and configuration defaults:

```python
# src/config.py
DEFAULT_PERIODS = 5
DEFAULT_SOURCE = "edgar"
DEFAULT_UNIT = "millions"
DEFAULT_CURRENCY = "USD"
OUTPUT_DIR = Path("output")
DATA_DIR = Path("data")
MAPPING_DIR = DATA_DIR / "mapping"
SAMPLES_DIR = DATA_DIR / "samples"
SEC_BASE_URL = "https://data.sec.gov/api"
SEC_SUBMISSIONS_URL = "https://data.sec.gov/submissions"
SEC_USER_AGENT = "reading-cfs-is-bs/0.1.0 (contact@example.com)"  # Override via env
ACCOUNTING_EQ_TOLERANCE = 0.001
CF_RECONCILIATION_TOLERANCE = 0.005
VOLATILITY_THRESHOLD = 0.20
```

**Verification:** `uv run -c "from src.config import DEFAULT_PERIODS; print(DEFAULT_PERIODS)"`

**Estimated files:** 1 new

### Step 0.3 — Create Data Models (`src/models/`)

| File | Contents |
|------|----------|
| `enums.py` | 9 enum classes: StatementType, PeriodType, Severity, Assessment, PipelineStatus, AccountingStandard, ExtractionSource, MappingConfidence, TrendDirection |
| `company.py` | Company dataclass |
| `line_item.py` | LineItem, UnmappedItem dataclasses |
| `statements.py` | IncomeStatement, BalanceSheet, CashFlowStatement dataclasses |
| `period.py` | Period, ValidationResult dataclasses |
| `ratios.py` | RatioPoint, ProfitabilityRatios, LiquidityRatios, SolvencyRatios, EfficiencyRatios, CashFlowQualityRatios |
| `red_flag.py` | RedFlag dataclass |
| `report_model.py` | Scorecard, ExecutiveSummary, CrossValidationResult, Report dataclasses |

**Important:** All models use `dataclasses` with `field(default_factory=...)` for list/dict defaults. Pydantic v2 models added later when we need validation on deserialization.

**Verification:** `uv run -c "from src.models import Company, IncomeStatement, Period, RedFlag; print('OK')"`

**Estimated files:** 9 new

### Step 0.4 — Create `src/models/__init__.py` with Re-exports

```python
from src.models.enums import (...)
from src.models.company import Company
from src.models.line_item import LineItem, UnmappedItem
from src.models.statements import IncomeStatement, BalanceSheet, CashFlowStatement
from src.models.period import Period, ValidationResult
from src.models.ratios import (...)
from src.models.red_flag import RedFlag
from src.models.report_model import Scorecard, ExecutiveSummary, CrossValidationResult, Report
```

**Verification:** All models importable from `src.models`

**Estimated files:** 0 new, 1 modified

### Step 0.5 — Create Test Structure & Fixtures

```bash
mkdir -p tests/extraction tests/parsing tests/analysis tests/reporting tests/models tests/integration
```

**Create `tests/conftest.py`** with shared fixtures:
- `sample_company` — Company(name="TestCo", ticker="TEST", fiscal_year_end="12-31")
- `sample_parsed_periods` — 5 years of Period objects with known values
- `sample_income_statement` — IncomeStatement with known values
- `sample_balance_sheet` — BalanceSheet with known values
- `sample_cash_flow_statement` — CashFlowStatement with known values
- `sample_ratios` — Pre-computed ratio dictionary

**Create `tests/models/test_models.py`** — verify all dataclasses instantiate correctly.

**Verification:** `uv run pytest tests/models/test_models.py -v` passes

**Estimated files:** 12 new (1 conftest, 1 test_models, 10 test stubs)

### Step 0.6 — Create Sample Data

Create `data/samples/aapl_2020_2024.json` with real or sufficiently realistic AAPL data:
- 5 years of IS, BS, CFS data
- Known values from public filings
- Used for integration tests

**Verification:** File is valid JSON, parsable by `json.load()`

**Estimated files:** 1 new

### Step 0.7 — Create `validate.py` Script for Pre-commit Quality

```bash
# Add to pyproject.toml scripts section
[tool.ruff]
line-length = 100
target-version = "py313"

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
```

**Verification:** `uv run ruff check src/` and `uv run pytest` run without issues

**Estimated files:** 0 new, 1 modified

**Phase 0 completion check:**
- [ ] All models importable: `uv run -c "from src.models import *"`
- [ ] Ruff passes: `uv run ruff check src/`
- [ ] Test infrastructure works: `uv run pytest tests/ -v`
- [ ] Config loads: `uv run -c "from src.config import *; print(DEFAULT_SOURCE)"`

---

## 3. Phase 1: Extraction (L1 — SEC EDGAR XBRL)

**Goal:** Given a ticker, fetch financial data from SEC EDGAR and produce structured raw line items.

### Step 1.1 — Create SEC EDGAR API Client (`src/extraction/edgar_client.py`)

**Functions to implement:**

```python
def get_cik(ticker: str) -> str:
    """Map ticker to CIK via SEC company_tickers.json."""
    # Fetch https://www.sec.gov/files/company_tickers.json
    # Convert dict → find by ticker → return CIK with leading zeros (10 digits)

def get_company_facts(cik: str) -> dict:
    """Fetch XBRL company facts from SEC API."""
    # GET https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json
    # Required: User-Agent header with company name + email
    # Rate limit: 10 req/sec (add time.sleep(0.1))

def get_submissions(cik: str) -> dict:
    """Fetch company submissions (filing history)."""
    # GET https://data.sec.gov/submissions/CIK{cik}.json

def get_annual_filings(submissions: dict, form_type: str = "10-K", limit: int = 10) -> list[dict]:
    """Extract annual 10-K filing metadata from submissions."""
    # Parse submissions["filings"]["recent"] for form_type matches
    # Return list of {accession_number, filing_date, report_date, primary_document}

def download_filing_document(cik: str, accession_number: str, document: str) -> str:
    """Download a specific filing document (HTML/XML)."""
    # Construct URL: https://www.sec.gov/Archives/edgar/data/{cik}/{accession_no_clean}/{document}
    # Return raw text content
```

**User-Agent requirement (SEC regulation):**
- Format: `OrganizationName ContactEmail`
- Must be in env var `SEC_USER_AGENT` or config
- Requests without it will be rate-limited/blocked

**Rate limiting:**
- SEC requires ≤ 10 requests/second
- Add `time.sleep(0.1)` between requests
- Use a session with appropriate headers

**Verification:**
```bash
uv run -c "from src.extraction.edgar_client import get_cik; print(get_cik('AAPL'))"
# Expected: 0000320193
```

**Estimated files:** 1 new

### Step 1.2 — Create XBRL Parser (`src/extraction/edgar_xbrl_parser.py`)

**Functions to implement:**

```python
def parse_company_facts(facts: dict, periods: int = 5) -> dict:
    """Parse SEC companyfacts JSON into raw line items grouped by statement and year."""
    # 1. Identify all us-gaap concepts in facts["facts"]["us-gaap"]
    # 2. For each concept, filter to annual ("fy") frame data
    # 3. Group by fiscal year, take last N periods
    # 4. Classify each concept into CFS/IS/BS using XBRL_CONCEPT_TO_STATEMENT mapping

XBRL_CONCEPT_TO_STATEMENT = {
    # IS concepts
    "Revenues": "IS",
    "CostOfGoodsAndServicesSold": "IS",
    "OperatingIncomeLoss": "IS",
    "NetIncomeLoss": "IS",
    # BS concepts
    "Assets": "BS",
    "AssetsCurrent": "BS",
    "Liabilities": "BS",
    "StockholdersEquity": "BS",
    # CFS concepts
    "NetCashProvidedByUsedInOperatingActivities": "CFS",
    "NetCashProvidedByUsedInInvestingActivities": "CFS",
    "NetCashProvidedByUsedInFinancingActivities": "CFS",
    # ... (full list from BLUEPRINT.md Appendix A)
}

def extract_fact_values(fact_data: dict, periods: int) -> list[dict]:
    """Extract annual values from an XBRL fact."""
    # For "units" → "USD" → filter to "fy" form entries
    # Sort by fiscal year, take last N
    # Each entry: {fiscal_year, end_date, value, unit}

def classify_concept(concept_name: str) -> StatementType | None:
    """Classify an XBRL concept into a statement type."""
    # Look up in XBRL_CONCEPT_TO_STATEMENT mapping
    # Return StatementType or None if unknown
```

**Verification:**
```bash
uv run -c "
from src.extraction.edgar_client import get_cik, get_company_facts
from src.extraction.edgar_xbrl_parser import parse_company_facts
cik = get_cik('AAPL')
facts = get_company_facts(cik)
data = parse_company_facts(facts, periods=3)
print(f'Periods: {len(data[\"periods\"])}, IS items: {len(data[\"periods\"][0][\"IS\"])}')
"
```

**Estimated files:** 1 new

### Step 1.3 — Create Main Extractor (`src/extraction/extractor.py` — rewrite)

Replace stub with real implementation:

```python
def extract_financial_data(ticker: str, periods: int = 5, source: str = "edgar") -> dict:
    """Extract raw financial data for a company from SEC EDGAR."""
    # 1. Validate ticker → uppercase, check length
    # 2. Route to source handler (currently only "edgar")
    # 3. If edgar: get_cik → get_company_facts → parse_company_facts
    # 4. Build output JSON per extractor agent spec
    # 5. Handle errors: ticker not found, API errors, no data
```

**Error handling:**
- Ticker not found → `{"status": "ERROR", "message": "Ticker 'XXXX' not found on SEC EDGAR"}`
- API error → `{"status": "ERROR", "message": "SEC API error: {details}"}`
- No data → `{"status": "WARNING", "message": "No financial data found for periods"}`
- Partial data → `{"status": "WARNING", "message": "Only X of 3 statements found"}`

**Verification:**
```bash
uv run main.py extract AAPL --periods 3
# Should output valid extracted JSON with 3 periods, IS/BS/CFS data
```

**Estimated files:** 0 new, 1 modified

### Step 1.4 — Create Unit Detector (`src/extraction/unit_detector.py`)

```python
def detect_unit(text_blocks: list[str]) -> tuple[str, str]:
    """Detect unit scale and currency from financial text blocks."""
    # Unit patterns: "(in thousands)", "(in millions)", "(in billions)"
    # Currency patterns: "$", "USD", "¥", "€", "GBP"
    # Default: ("millions", "USD")

def parse_value(value_str: str, is_parenthetical_negative: bool = True) -> float:
    """Parse a financial value string into a float."""
    # Handle: "1,234.5" → 1234.5, "(1,234.5)" → -1234.5, "—" → 0.0
```

**Verification:** Unit tests for edge cases

**Estimated files:** 1 new

### Step 1.5 — Write Extraction Tests (`tests/extraction/`)

| Test File | What It Tests |
|-----------|--------------|
| `test_edgar_client.py` | CIK lookup, facts fetch, submission fetch (mock SEC API) |
| `test_edgar_xbrl_parser.py` | Concept classification, fact extraction, period grouping |
| `test_unit_detector.py` | Unit detection, value parsing edge cases |
| `test_extractor_pipeline.py` | Full extraction → output JSON structure validation |

**Mocking strategy:**
- Mock `requests.get` to return sample SEC API responses
- Use `tests/conftest.py` fixtures for known-good XBRL facts JSON
- Test error paths: ticker not found, API timeout, empty facts

**Verification:** `uv run pytest tests/extraction/ -v` all pass

**Estimated files:** 4 new

**Phase 1 completion check:**
- [ ] `uv run main.py extract AAPL --periods 3` outputs valid JSON
- [ ] Output matches extractor agent JSON schema
- [ ] Error cases handled gracefully
- [ ] All extraction tests pass

---

## 4. Phase 2: Parsing & Normalization

**Goal:** Take raw extracted line items → produce standardized, validated financial statements.

### Step 2.1 — Create Mapping Dictionary Data Files

Create `data/mapping/gaap_us.json` — full US GAAP XBRL concept → standard key mapping.

**Must include ALL concepts from BLUEPRINT.md Appendix A** plus additional common ones.

**Structure:**
```json
{
  "standard": "US GAAP",
  "source": "SEC XBRL",
  "statement_mappings": {
    "IS": {
      "Revenues": "revenue",
      "CostOfGoodsAndServicesSold": "cogs",
      "...": "..."
    },
    "BS": { "...": "..." },
    "CFS": { "...": "..." }
  },
  "label_aliases": {
    "revenue": ["revenue", "sales", "turnover", "top line", "net sales", "total revenue"],
    "cogs": ["cost of goods sold", "cost of sales", "cost of revenue"],
    "net_income": ["net income", "net earnings", "net profit", "profit attributable to shareholders", "bottom line"],
    "...": "..."
  }
}
```

**Estimated files:** 1 new

### Step 2.2 — Create Label Mapper (`src/parsing/label_mapper.py`)

```python
def load_mapping_dictionary(standard: str = "us-gaap") -> dict:
    """Load mapping dictionary for an accounting standard."""

def map_line_item(label: str, statement_type: StatementType, mapping: dict) -> tuple[str | None, MappingConfidence]:
    """Map a raw label to a standard key."""
    # 1. Exact match against statement_mappings[statement_type]
    # 2. Fuzzy match using difflib.SequenceMatcher (threshold 0.85)
    # 3. Check label_aliases for common alternate names
    # 4. Return (standard_key, confidence)

def map_all_line_items(line_items: list[dict], statement_type: StatementType, mapping: dict) -> list[LineItem]:
    """Map all line items in a statement."""

def get_unmapped_items(line_items: list[LineItem]) -> list[UnmappedItem]:
    """Get list of items that couldn't be mapped."""

def fuzzy_match(label: str, candidates: list[str], threshold: float = 0.85) -> str | None:
    """Find best fuzzy match above threshold."""
```

**Verification:** Unit tests with known XBRL labels and edge cases

**Estimated files:** 1 new

### Step 2.3 — Create Unit Normalizer (`src/parsing/unit_normalizer.py`)

```python
def normalize_value(value: float, from_unit: str, to_unit: str = "millions") -> float:
    """Convert value between unit scales."""
    # thousands → millions: value / 1000
    # millions → millions: value (no change)
    # billions → millions: value * 1000
    # actual → millions: value / 1_000_000

def normalize_period(period: dict, target_unit: str = "millions") -> dict:
    """Normalize all values in a period to target unit."""
    # Record original_unit + original_value before normalizing
```

**Verification:** Unit tests for all conversions

**Estimated files:** 1 new

### Step 2.4 — Create Structure Validator (`src/parsing/structure_validator.py`)

```python
def validate_balance_sheet(assets: float, liabilities: float, equity: float) -> ValidationResult:
    """Verify A = L + E with tolerance (±0.1%)."""
    # |(assets - (liabilities + equity)) / assets| < 0.001

def validate_cash_flow_reconciliation(operating_cf: float, investing_cf: float, financing_cf: float, net_change: float) -> ValidationResult:
    """Verify ΔCash = OCF + ICF + FCF."""
    # |net_change - sum| / max(|net_change|, 1) < 0.005

def validate_income_statement_arithmetic(revenue: float, cogs: float, gross_profit: float) -> ValidationResult:
    """Verify GP = Rev - COGS."""

def run_all_validations(period: Period) -> list[ValidationResult]:
    """Run all applicable validations for a period."""
```

**Important:** All checks are hardcoded arithmetic — never use LLM for financial validation (per insight #63).

**Verification:** Unit tests with balanced and deliberately unbalanced data

**Estimated files:** 1 new

### Step 2.5 — Create Subtotal Calculator (`src/parsing/subtotal_calculator.py`)

```python
def compute_derived_fields(period: Period) -> Period:
    """Compute derived/subtotal fields not in raw data."""
    # gross_profit = revenue - cogs (if not present)
    # ebitda = operating_income + depreciation_amortization
    # working_capital = current_assets - current_liabilities
    # Annotate computed fields so they're traceable

COMPUTED_FIELDS = {
    "gross_profit": lambda is_: is_.revenue - is_.cogs,
    "ebitda": lambda is_, cfs: is_.operating_income + cfs.depreciation_amortization,
}
```

**Verification:** Unit tests with complete and incomplete data

**Estimated files:** 1 new

### Step 2.6 — Create Fiscal Year Handler (`src/parsing/fiscal_year_handler.py`)

```python
def parse_end_date(date_str: str) -> date:
    """Parse various end-date formats → date object."""

def sort_periods_chronologically(periods: list) -> list:
    """Sort periods by end_date ascending."""

def generate_period_label(fiscal_year: int, period_type: PeriodType, quarter: int | None = None) -> str:
    """Generate standard period label: FY2024, Q1 2024, etc."""

def detect_fiscal_year_end(periods: list) -> str:
    """Detect fiscal year end month/day from period data."""
```

**Estimated files:** 1 new

### Step 2.7 — Create Main Parser (`src/parsing/parser.py` — rewrite)

Replace stub with real implementation:

```python
def parse_financial_data(raw_data: dict) -> dict:
    """Parse extracted raw data into structured financial statements."""
    # 1. Load mapping dictionary based on detected standard
    # 2. For each period:
    #    a. Detect/apply unit normalization
    #    b. Map each line item via label_mapper
    #    c. Build IncomeStatement, BalanceSheet, CashFlowStatement objects
    #    d. Compute derived fields (subtotals)
    #    e. Run structure validations
    # 3. Generate mapping statistics
    # 4. Return parsed JSON output
```

**Verification:** `uv run main.py parse output/extracted_aapl.json`

**Estimated files:** 0 new, 1 modified

### Step 2.8 — Write Parsing Tests (`tests/parsing/`)

| Test File | What It Tests |
|-----------|--------------|
| `test_label_mapper.py` | Exact match, fuzzy match, unmapped, edge cases |
| `test_unit_normalizer.py` | All unit conversions, edge cases |
| `test_structure_validator.py` | A=L+E, ΔCash, IS arithmetic, tolerances |
| `test_subtotal_calculator.py` | Derived field computation |
| `test_fiscal_year_handler.py` | Date parsing, sorting, labeling |
| `test_parser_pipeline.py` | Full extract→parse roundtrip |

**Verification:** `uv run pytest tests/parsing/ -v` all pass

**Estimated files:** 6 new

**Phase 2 completion check:**
- [ ] `uv run main.py parse output/extracted_aapl.json` outputs valid parsed JSON
- [ ] Validation checks run and report correctly
- [ ] Unmapped items tracked in `unmapped` list
- [ ] Mapping statistics present
- [ ] All parsing tests pass

---

## 5. Phase 3: Analysis Engine

**Goal:** Compute all 22 ratios, detect red flags, analyze trends, produce a scored health assessment.

### Step 5.1 — Create Profitability Ratios (`src/analysis/profitability.py`)

```python
def compute_gross_margin(gross_profit: float, revenue: float) -> float | None:
    """Gross Margin = Gross Profit / Revenue. Returns None if revenue is 0."""

def compute_operating_margin(operating_income: float, revenue: float) -> float | None:

def compute_net_margin(net_income: float, revenue: float) -> float | None:

def compute_roa(net_income: float, total_assets: float) -> float | None:

def compute_roe(net_income: float, total_equity: float) -> float | None:

def compute_ebitda_margin(ebitda: float, revenue: float) -> float | None:

def compute_all_profitability(period: Period) -> ProfitabilityRatios:
    """Compute all profitability ratios for a period."""
```

**Handle edge cases:**
- Division by zero → return None, log warning
- Negative equity → ROE returns None with warning
- Negative margins → still compute but flag in trends

**Estimated files:** 1 new

### Step 5.2 — Create Liquidity Ratios (`src/analysis/liquidity.py`)

```python
def compute_current_ratio(current_assets: float, current_liabilities: float) -> float | None:
def compute_quick_ratio(current_assets: float, inventory: float, current_liabilities: float) -> float | None:
def compute_working_capital(current_assets: float, current_liabilities: float) -> float:
def compute_operating_cf_ratio(operating_cf: float, current_liabilities: float) -> float | None:
def compute_all_liquidity(period: Period) -> LiquidityRatios:
```

**Estimated files:** 1 new

### Step 5.3 — Create Solvency Ratios (`src/analysis/solvency.py`)

```python
def compute_debt_to_equity(total_liabilities: float, total_equity: float) -> float | None:
def compute_debt_to_assets(total_liabilities: float, total_assets: float) -> float | None:
def compute_interest_coverage(operating_income: float, interest_expense: float) -> float | None:
def compute_lt_debt_to_equity(long_term_debt: float, total_equity: float) -> float | None:
def compute_all_solvency(period: Period) -> SolvencyRatios:
```

**Handle:** zero/negative equity → None for D/E, zero interest expense → None for coverage

**Estimated files:** 1 new

### Step 5.4 — Create Efficiency Ratios (`src/analysis/efficiency.py`)

```python
def compute_asset_turnover(revenue: float, total_assets: float) -> float | None:
def compute_receivables_turnover(revenue: float, accounts_receivable: float) -> float | None:
def compute_inventory_turnover(cogs: float, inventory: float) -> float | None:
def compute_days_sales_outstanding(receivables_turnover: float | None) -> float | None:
def compute_all_efficiency(period: Period) -> EfficiencyRatios:
```

**Estimated files:** 1 new

### Step 5.5 — Create Cash Flow Quality Ratios (`src/analysis/cash_flow_quality.py`)

```python
def compute_fcf(operating_cf: float, capex: float) -> float:
    """FCF = Operating CF - |CapEx| (capEx is stored as negative)"""

def compute_fcf_margin(fcf: float, revenue: float) -> float | None:
def compute_cf_to_ni(operating_cf: float, net_income: float) -> float | None:
def compute_fcf_to_ni(fcf: float, net_income: float) -> float | None:
def compute_all_cash_flow_quality(period: Period) -> CashFlowQualityRatios:
```

**Estimated files:** 1 new

### Step 5.6 — Create Ratio Calculator Orchestrator (`src/analysis/ratio_calculator.py`)

```python
def compute_all_ratios(periods: list[Period]) -> dict:
    """Compute all 22 ratios for all periods."""
    # 1. For each period, compute each of 5 categories
    # 2. Aggregate into RatioPoint lists
    # 3. Handle missing/None ratios gracefully
    # Returns dict with profitability/liquidity/solvency/efficiency/cash_flow_quality
```

**Estimated files:** 1 new

### Step 5.7 — Create Trend Analyzer (`src/analysis/trend_analyzer.py`)

```python
def compute_yoy_growth(values: list[float], periods: list[str]) -> list[RatioPoint]:
    """Compute YoY growth: (V_t - V_{t-1}) / |V_{t-1}|."""

def compute_cagr(start_value: float, end_value: float, num_years: int) -> float | None:
    """CAGR = (end/start)^(1/years) - 1."""

def classify_margin_trend(margins: list[float]) -> TrendDirection:
    """Classify margin direction over period range."""
    # Compare last 2 periods to prior 3
    # improving: margins increasing each year
    # stable: within ±1% band
    # declining: margins decreasing each year
    # mixed: no clear pattern

def analyze_trends(parsed_data: dict, ratios: dict) -> dict:
    """Run all trend analyses."""
```

**Estimated files:** 1 new

### Step 5.8 — Create Red Flag Detector (`src/analysis/red_flag_detector.py`)

```python
# 12 detection functions, one per red flag type

def detect_earnings_quality_concern(cf_to_ni_series: list[float | None]) -> RedFlag | None:
    """Flag if CF/NI < 0.5 in any period."""

def detect_liquidity_crisis(current_ratios: list[float | None]) -> RedFlag | None:
    """Flag if Current Ratio < 1.0 in any period."""

def detect_excessive_leverage(de_ratios: list[float | None], threshold: float = 2.0) -> RedFlag | None:
    """Flag if D/E > threshold."""

def detect_sustained_negative_ocf(ocf_values: list[float]) -> RedFlag | None:
    """Flag if Operating CF < 0 for 3+ consecutive periods."""

def detect_aggressive_revenue_recognition(ar_growth: list[float], rev_growth: list[float]) -> RedFlag | None:
    """Flag if AR growth > Revenue growth for 2+ periods."""

def detect_demand_problem(inventory_growth: list[float], rev_growth: list[float]) -> RedFlag | None:
    """Flag if Inventory growth > Revenue growth."""

def detect_acquisition_risk(goodwill: float, equity: float) -> RedFlag | None:
    """Flag if Goodwill > 50% of Equity."""

def detect_debt_service_concern(interest_coverage: list[float | None]) -> RedFlag | None:
    """Flag if Interest Coverage < 1.5."""

def detect_cannot_cover_interest(interest_coverage: list[float | None]) -> RedFlag | None:
    """Flag if Interest Coverage < 1.0."""

def detect_negative_equity(equity_values: list[float]) -> RedFlag | None:
    """Flag if Total Equity < 0."""

def detect_sustained_margin_decline(margin_series: dict[str, list[float]]) -> RedFlag | None:
    """Flag if 3+ consecutive years of declining margins."""

def detect_cash_burn(fcf_values: list[float]) -> RedFlag | None:
    """Flag if negative FCF for 3+ consecutive periods."""

def detect_all_red_flags(periods: list[Period], ratios: dict) -> list[RedFlag]:
    """Run all 12 red flag checks."""
```

**Severity rules:**
- `critical`: CF/NI < 0.5, Current Ratio < 1.0, negative equity, sustained negative OCF, Interest Coverage < 1.0
- `warning`: D/E > threshold, AR/receivables concern, inventory buildup, goodwill > 50%, Interest Coverage < 1.5, sustained margin decline, cash burn

**Estimated files:** 1 new

### Step 5.9 — Create Cross-Statement Validator (`src/analysis/cross_validator.py`)

```python
def validate_earnings_quality(ocf_series: list[float], ni_series: list[float]) -> CrossValidationResult:
    """Check: avg OCF > avg NI over period range."""

def validate_revenue_quality(ar_growth: list[float], rev_growth: list[float]) -> CrossValidationResult:
    """Check: AR growth ≤ Revenue growth."""

def validate_demand_health(inventory_growth: list[float], rev_growth: list[float]) -> CrossValidationResult:
    """Check: Inventory growth ≤ Revenue growth."""

def validate_depreciation_consistency(acc_dep_series: list[float], dep_exp_series: list[float]) -> CrossValidationResult:
    """Check: ΔAccDep ≈ DepExp."""

def validate_interest_consistency(interest_exp: float, total_debt: float, market_rate: float = 0.05) -> CrossValidationResult:
    """Check: Interest Expense ≈ Debt × Market Rate."""

def run_cross_validation(periods: list[Period], ratios: dict) -> list[CrossValidationResult]:
    """Run all 5 cross-statement checks."""
```

**Estimated files:** 1 new

### Step 5.10 — Create Anomaly Detector (`src/analysis/anomaly_detector.py`)

```python
def detect_volatility_spikes(values: list[float], periods: list[str], threshold: float = 0.20) -> list[dict]:
    """Detect YoY changes > threshold."""
    # Flag items with >20% YoY volatility
    # Return [{item, period, prev_value, curr_value, change_pct}]

def detect_anomalies(periods: list[Period]) -> list[dict]:
    """Run anomaly detection on all line items."""
```

**Estimated files:** 1 new

### Step 5.11 — Create Scorer (`src/analysis/scorer.py`)

Implement the 5-dimension, 0-100 scoring system per BLUEPRINT.md §5.2.11.

```python
def score_profitability(ratios: ProfitabilityRatios) -> int:
    """Score profitability 0-20."""
    # Gross margin trend: 0-5
    # Operating margin trend: 0-5
    # Net margin trend: 0-5
    # ROE level: 0-5

def score_liquidity(ratios: LiquidityRatios) -> int:
    """Score liquidity 0-20."""

def score_solvency(ratios: SolvencyRatios) -> int:
    """Score solvency 0-20."""

def score_efficiency(ratios: EfficiencyRatios) -> int:
    """Score efficiency 0-20."""

def score_cash_flow_quality(ratios: CashFlowQualityRatios) -> int:
    """Score cash flow quality 0-20."""

def compute_scorecard(ratios: dict) -> Scorecard:
    """Compute full 5-dimension scorecard."""
    # total = sum of all dimensions
    # assessment from total:
    #   80-100: Strong
    #   60-79: Adequate
    #   40-59: Concerning
    #   0-39: Critical
```

**Estimated files:** 1 new

### Step 5.12 — Create Main Analyzer (`src/analysis/analyzer.py` — rewrite)

```python
def analyze_financial_data(parsed_data: dict) -> dict:
    """Run complete financial analysis pipeline."""
    # 1. Deserialize periods from parsed_data
    # 2. Compute all ratios
    # 3. Analyze trends
    # 4. Detect red flags
    # 5. Run cross-validation
    # 6. Detect anomalies
    # 7. Compute scorecard
    # 8. Return analyzed JSON
```

**Verification:** `uv run main.py ratio output/parsed_aapl.json`

**Estimated files:** 0 new, 1 modified

### Step 5.13 — Write Analysis Tests (`tests/analysis/`)

| Test File | What It Tests |
|-----------|--------------|
| `test_profitability.py` | Each ratio with known inputs, edge cases (zero rev, neg equity) |
| `test_liquidity.py` | CR, QR, WC, OCFR with edge cases |
| `test_solvency.py` | D/E, D/A, IC with zero/negative equity, zero interest |
| `test_efficiency.py` | Turnover ratios, DSO with zero AR/inventory |
| `test_cash_flow_quality.py` | FCF, margins with negative OCF |
| `test_trend_analyzer.py` | YoY growth, CAGR, margin trend classification |
| `test_red_flag_detector.py` | Each of 12 flags at boundary conditions |
| `test_cross_validator.py` | Each of 5 cross-checks |
| `test_anomaly_detector.py` | Volatility detection at threshold boundary |
| `test_scorer.py` | Each dimension scoring, total assessment boundary tests |
| `test_analyzer_pipeline.py` | Full parse→analyze roundtrip |

**Verification:** `uv run pytest tests/analysis/ -v` all pass

**Estimated files:** 11 new

**Phase 3 completion check:**
- [ ] All 22 ratios compute correctly with known data
- [ ] Ratio computation handles edge cases (division by zero, negative values)
- [ ] All 12 red flags detect correctly at boundary conditions
- [ ] Scorecard produces correct 0-100 score with known inputs
- [ ] `uv run main.py ratio output/parsed_aapl.json` outputs valid analyzed JSON
- [ ] All analysis tests pass

---

## 6. Phase 4: Report Generation

**Goal:** Produce readable, structured analysis reports in JSON, Markdown, and HTML formats.

### Step 6.1 — Create Executive Summary (`src/reporting/executive_summary.py`)

```python
def select_top_findings(analysis: dict) -> list[str]:
    """Select top 3 most material findings."""
    # Priority: most severe red flag > largest ratio deviation > strongest trend

def determine_assessment(scorecard_total: int) -> str:
    """Map score to assessment label."""
    # 80-100: Strong, 60-79: Adequate, 40-59: Concerning, 0-39: Critical

def build_executive_summary(analysis: dict) -> ExecutiveSummary:
    """Build executive summary from analysis data."""
```

**Estimated files:** 1 new

### Step 6.2 — Create Scorecard Builder (`src/reporting/scorecard_builder.py`)

```python
def build_scorecard_section(analysis: dict) -> Scorecard:
    """Format scorecard data for report."""
    # Just pass through from analysis scorecard
```

**Estimated files:** 1 new

### Step 6.3 — Create Findings Section (`src/reporting/findings_section.py`)

```python
def build_income_statement_findings(periods: list[dict]) -> str:
    """Generate IS narrative: revenue trend, margins, key items."""

def build_balance_sheet_findings(periods: list[dict]) -> str:
    """Generate BS narrative: assets, liabilities, equity structure."""

def build_cash_flow_findings(periods: list[dict]) -> str:
    """Generate CFS narrative: OCF trend, FCF, financing activities."""

def build_detailed_findings(parsed_data: dict, analysis: dict) -> dict[str, str]:
    """Build all three statement narratives."""
```

**Estimated files:** 1 new

### Step 6.4 — Create Ratio Section (`src/reporting/ratio_section.py`)

```python
def build_ratio_analysis(analysis: dict) -> str:
    """Generate ratio analysis narrative across all 5 categories."""
    # For each ratio: current value, trend, interpretation
    # Highlight ratios outside healthy ranges
    # Note any data limitations
```

**Estimated files:** 1 new

### Step 6.5 — Create Red Flags Section (`src/reporting/red_flags_section.py`)

```python
def rank_red_flags(flags: list[dict]) -> list[dict]:
    """Sort red flags: critical first, then by number of periods affected."""

def build_red_flags_section(analysis: dict) -> list[dict]:
    """Format ranked red flags with context."""
```

**Estimated files:** 1 new

### Step 6.6 — Create Strengths Section (`src/reporting/strengths_section.py`)

```python
def identify_strengths(analysis: dict, periods: list[dict]) -> list[str]:
    """Identify positive financial indicators."""
    # Ratios in healthy range, improving trends, validated cross-checks
    # Rules-based: no LLM guessing
```

**Estimated files:** 1 new

### Step 6.7 — Create Recommendations (`src/reporting/recommendations.py`)

```python
def generate_recommendations(analysis: dict, red_flags: list[dict]) -> list[str]:
    """Generate actionable recommendations."""
    # Based on red flag types, ratio weaknesses, trend concerns
    # Template-based with parameter substitution
```

**Estimated files:** 1 new

### Step 6.8 — Create Markdown Renderer (`src/reporting/markdown_renderer.py`)

```python
def render_markdown(report: Report) -> str:
    """Render report as Markdown string."""
    # Section headers (##), tables for ratios and scorecard, bullet lists for findings
    # Format:
    #   # Financial Analysis: {ticker}
    #   ## Executive Summary
    #   ## Financial Health Scorecard
    #   | Dimension | Score |
    #   ## Detailed Findings
    #   ## Ratio Analysis
    #   ## Red Flags & Risks
    #   ## Strengths
    #   ## Recommendations
```

**Estimated files:** 1 new

### Step 6.9 — Create HTML Renderer (`src/reporting/html_renderer.py`)

```python
def render_html(report: Report) -> str:
    """Render report as standalone HTML document."""
    # Basic CSS: clean typography, table styling, color-coded scorecard
    # Self-contained (no external deps)
```

**Estimated files:** 1 new

### Step 6.10 — Create Main Reporter (`src/reporting/reporter.py` — rewrite)

```python
def generate_report(analyzed_data: dict, output_format: str = "json") -> dict:
    """Generate analysis report from analyzed data."""
    # 1. Build Report object from analyzed_data
    # 2. Build each section
    # 3. Format output based on --format flag (json, markdown, html)
    # 4. If markdown/html, write to file, return path reference
```

**Verification:** `uv run main.py report output/analyzed_aapl.json --format markdown`

**Estimated files:** 0 new, 1 modified

### Step 6.11 — Write Reporting Tests (`tests/reporting/`)

| Test File | What It Tests |
|-----------|--------------|
| `test_executive_summary.py` | Top findings selection, assessment mapping |
| `test_scorecard_builder.py` | Scorecard assembly |
| `test_markdown_renderer.py` | Output structure, table formatting |
| `test_html_renderer.py` | Output structure, valid HTML |
| `test_reporter_pipeline.py` | Full analyze→report roundtrip |

**Verification:** `uv run pytest tests/reporting/ -v` all pass

**Estimated files:** 5 new

**Phase 4 completion check:**
- [ ] Report generates in all 3 formats (JSON, Markdown, HTML)
- [ ] Markdown output is readable and well-structured
- [ ] HTML output is valid and self-contained
- [ ] All report sections present and populated
- [ ] `uv run main.py report output/analyzed_aapl.json --format markdown` outputs clean markdown

---

## 7. Phase 5: Integration & Polish

**Goal:** End-to-end pipeline validation, CLI polish, integration tests, documentation.

### Step 7.1 — Full Pipeline Integration Test

Create `tests/integration/test_apple_sample.py`:

```python
def test_full_pipeline_aapl():
    """Run full extract→parse→analyze→report pipeline on AAPL."""
    # 1. Extract AAPL data from SEC EDGAR (or mock if offline)
    # 2. Parse into structured statements
    # 3. Analyze ratios, trends, red flags
    # 4. Generate report
    # 5. Assert: status == SUCCESS (or WARNING)
    # 6. Assert: periods_analyzed == 5
    # 7. Assert: ratios computed for all categories
    # 8. Assert: report has all 7 sections
```

**Integration test scenarios:**

| Test | Description |
|------|-------------|
| `test_apple_pipeline` | Full pipeline with real/mocked AAPL data |
| `test_edge_cases_pipeline` | Negative equity, missing data, single year |
| `test_missing_statement` | Company with only IS data (no BS/CFS) |

**Estimated files:** 3 new

### Step 7.2 — CLI Polish (`main.py`)

- Add `--output` flag to specify output file path
- Add `--output-dir` flag
- Add `--save-intermediate` flag to save extracted/parsed/analyzed JSON
- Add `--accounting` flag to specify accounting standard
- Add `--verbose` / `-v` flag for debug logging
- Add `--quiet` / `-q` flag to suppress non-error output
- Add version command: `uv run main.py --version`

**Estimated files:** 0 new, 1 modified

### Step 7.3 — Environment & User-Agent Setup

- Add `.env.example` with `SEC_USER_AGENT` template
- Document SEC EDGAR API requirements in README
- Load `.env` in `main.py` startup via `python-dotenv`
- Validate User-Agent header before making SEC API calls

**Estimated files:** 1 new (`.env.example`), 1 modified (`main.py`)

### Step 7.4 — Add Logging Configuration

```python
# src/logging_config.py
def setup_logging(verbose: bool = False) -> None:
    """Configure logging for the pipeline."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
```

**Estimated files:** 1 new

### Step 7.5 — Update `pyproject.toml` Entry Points

```toml
[project.scripts]
cfs-is-bs = "main:main"

[project.urls]
Repository = "https://github.com/user/reading-CFS-IS-BS"
```

**Estimated files:** 0 new, 1 modified

### Step 7.6 — Document the Skill Loading Pattern

Ensure `skills/financial-statement-analysis/SKILL.md` is up to date with final ratio definitions, scoring methodology, and guardrails.

**Estimated files:** 0 new, 1 modified

### Step 7.7 — Run Full Test Suite

```bash
uv run ruff check src/ tests/
uv run pytest tests/ -v --tb=short
```

**Phase 5 completion check:**
- [ ] `uv run main.py analyze AAPL --periods 5` completes successfully
- [ ] All integration tests pass
- [ ] CLI error messages are clear and actionable
- [ ] `uv run ruff check` passes with no errors
- [ ] `uv run pytest` passes with >80% coverage on src/analysis/ and src/parsing/

---

## 8. Phase 6: Advanced Extraction (L2-L4) — FUTURE

**Goal:** Extend beyond SEC EDGAR XBRL to support HTML tables, PDF parsing, and OCR fallback.

### Step 8.1 — HTML Extractor (`src/extraction/html_extractor.py`)

- Parse SEC filing HTML documents with BeautifulSoup
- Locate financial statement tables via surrounding text headers
- Handle multi-year comparison tables (columns = years)
- Extract row labels + cell values

### Step 8.2 — PDF Extractor (`src/extraction/pdf_extractor.py`)

- PyMuPDF-based text extraction
- Coordinate clustering for borderless tables
- Cross-page table merge (continued/new-page detection)
- IS+CFS same-page splitting
- Section header keyword detection

### Step 8.3 — OCR Extractor (`src/extraction/ocr_extractor.py`)

- PaddleOCR integration (add dependency)
- Image-to-text for scanned documents
- Confidence score per page
- Only triggered when text extraction fails

### Step 8.4 — Source Router (`src/extraction/source_router.py`)

- Route `source` parameter to correct handler
- Auto-escalation: L1 (fail) → L2 (fail) → L3 (fail) → L4
- Track escalation path in metadata for audit

### Step 8.5 — Line Item Extractor Common Logic (`src/extraction/line_item_extractor.py`)

- `clean_label()` — strip whitespace, normalize unicode
- `parse_value()` — handle parentheses, commas, "—" dashes
- Shared across L1-L4 extractors

---

## 9. Phase 7: Hardening & Production — FUTURE

### Step 9.1 — Error Recovery & Retry

- Retry SEC API calls with exponential backoff
- Cache CIK lookups to avoid repeat API calls
- Save intermediate results so partial pipeline can resume

### Step 9.2 — Audit Trail

- Log all transformations with timestamps
- Store original values alongside normalized values
- Generate extraction→report traceability map

### Step 9.3 — Additional Output Formats

- PDF report via WeasyPrint or similar
- Excel export via openpyxl

### Step 9.4 — International Support

- IFRS mapping dictionary (`data/mapping/ifrs_eu.json`)
- China GAAP mapping dictionary (`data/mapping/cn_accounting.json`)
- Multi-currency support with exchange rate conversion
- Non-English label detection and mapping

### Step 9.5 — Performance Optimization

- Async SEC API calls for multi-year extraction
- Caching layer for API responses
- Parallel period processing in analysis phase

---

## Appendix A: File Creation Sequence

Files listed in creation order with dependencies:

| Order | File | Phase | Depends On |
|-------|------|-------|-----------|
| 1 | `src/config.py` | 0 | — |
| 2 | `src/models/enums.py` | 0 | — |
| 3 | `src/models/company.py` | 0 | enums |
| 4 | `src/models/line_item.py` | 0 | enums |
| 5 | `src/models/statements.py` | 0 | line_item |
| 6 | `src/models/period.py` | 0 | statements, enums |
| 7 | `src/models/ratios.py` | 0 | — |
| 8 | `src/models/red_flag.py` | 0 | enums |
| 9 | `src/models/report_model.py` | 0 | company, red_flag |
| 10 | `src/models/__init__.py` | 0 | all models |
| 11 | `tests/conftest.py` | 0 | models |
| 12 | `tests/models/test_models.py` | 0 | models |
| 13 | `data/samples/aapl_2020_2024.json` | 0 | — |
| 14 | `src/extraction/edgar_client.py` | 1 | config |
| 15 | `src/extraction/edgar_xbrl_parser.py` | 1 | models, edgar_client |
| 16 | `src/extraction/unit_detector.py` | 1 | — |
| 17 | `src/extraction/extractor.py` | 1 | edgar_client, edgar_xbrl_parser |
| 18 | `tests/extraction/test_edgar_client.py` | 1 | edgar_client |
| 19 | `tests/extraction/test_edgar_xbrl_parser.py` | 1 | edgar_xbrl_parser |
| 20 | `tests/extraction/test_unit_detector.py` | 1 | unit_detector |
| 21 | `tests/extraction/test_extractor_pipeline.py` | 1 | extractor |
| 22 | `data/mapping/gaap_us.json` | 2 | — |
| 23 | `src/parsing/label_mapper.py` | 2 | models |
| 24 | `src/parsing/unit_normalizer.py` | 2 | — |
| 25 | `src/parsing/structure_validator.py` | 2 | models |
| 26 | `src/parsing/subtotal_calculator.py` | 2 | models |
| 27 | `src/parsing/fiscal_year_handler.py` | 2 | models |
| 28 | `src/parsing/parser.py` | 2 | all parsing modules |
| 29 | `tests/parsing/test_label_mapper.py` | 2 | label_mapper |
| 30 | `tests/parsing/test_unit_normalizer.py` | 2 | unit_normalizer |
| 31 | `tests/parsing/test_structure_validator.py` | 2 | structure_validator |
| 32 | `tests/parsing/test_subtotal_calculator.py` | 2 | subtotal_calculator |
| 33 | `tests/parsing/test_fiscal_year_handler.py` | 2 | fiscal_year_handler |
| 34 | `tests/parsing/test_parser_pipeline.py` | 2 | parser |
| 35 | `src/analysis/profitability.py` | 3 | models |
| 36 | `src/analysis/liquidity.py` | 3 | models |
| 37 | `src/analysis/solvency.py` | 3 | models |
| 38 | `src/analysis/efficiency.py` | 3 | models |
| 39 | `src/analysis/cash_flow_quality.py` | 3 | models |
| 40 | `src/analysis/ratio_calculator.py` | 3 | all ratio modules |
| 41 | `src/analysis/trend_analyzer.py` | 3 | models |
| 42 | `src/analysis/red_flag_detector.py` | 3 | models |
| 43 | `src/analysis/cross_validator.py` | 3 | models |
| 44 | `src/analysis/anomaly_detector.py` | 3 | models |
| 45 | `src/analysis/scorer.py` | 3 | models |
| 46 | `src/analysis/analyzer.py` | 3 | all analysis modules |
| 47 | `tests/analysis/test_profitability.py` | 3 | profitability |
| 48 | `tests/analysis/test_liquidity.py` | 3 | liquidity |
| 49 | `tests/analysis/test_solvency.py` | 3 | solvency |
| 50 | `tests/analysis/test_efficiency.py` | 3 | efficiency |
| 51 | `tests/analysis/test_cash_flow_quality.py` | 3 | cash_flow_quality |
| 52 | `tests/analysis/test_trend_analyzer.py` | 3 | trend_analyzer |
| 53 | `tests/analysis/test_red_flag_detector.py` | 3 | red_flag_detector |
| 54 | `tests/analysis/test_cross_validator.py` | 3 | cross_validator |
| 55 | `tests/analysis/test_anomaly_detector.py` | 3 | anomaly_detector |
| 56 | `tests/analysis/test_scorer.py` | 3 | scorer |
| 57 | `tests/analysis/test_analyzer_pipeline.py` | 3 | analyzer |
| 58 | `src/reporting/executive_summary.py` | 4 | models |
| 59 | `src/reporting/scorecard_builder.py` | 4 | models |
| 60 | `src/reporting/findings_section.py` | 4 | models |
| 61 | `src/reporting/ratio_section.py` | 4 | models |
| 62 | `src/reporting/red_flags_section.py` | 4 | models |
| 63 | `src/reporting/strengths_section.py` | 4 | models |
| 64 | `src/reporting/recommendations.py` | 4 | models |
| 65 | `src/reporting/markdown_renderer.py` | 4 | models |
| 66 | `src/reporting/html_renderer.py` | 4 | models |
| 67 | `src/reporting/reporter.py` | 4 | all reporting modules |
| 68 | `tests/reporting/test_executive_summary.py` | 4 | executive_summary |
| 69 | `tests/reporting/test_scorecard_builder.py` | 4 | scorecard_builder |
| 70 | `tests/reporting/test_markdown_renderer.py` | 4 | markdown_renderer |
| 71 | `tests/reporting/test_html_renderer.py` | 4 | html_renderer |
| 72 | `tests/reporting/test_reporter_pipeline.py` | 4 | reporter |
| 73 | `tests/integration/test_apple_sample.py` | 5 | all phases |
| 74 | `tests/integration/test_edge_cases.py` | 5 | all phases |
| 75 | `src/logging_config.py` | 5 | — |
| 76 | `.env.example` | 5 | — |

**Total new files: 76** (including 34 test files)

## Appendix B: Quick Start Commands

```bash
# Install dependencies
uv sync

# Run tests
uv run pytest tests/ -v

# Lint
uv run ruff check src/ tests/

# Extract financial data
uv run main.py extract AAPL --periods 5

# Run full pipeline
uv run main.py analyze AAPL --periods 5 --output report.md --format markdown

# Parse previously extracted data
uv run main.py parse output/extracted_aapl.json

# Compute ratios
uv run main.py ratio output/parsed_aapl.json

# Generate report
uv run main.py report output/analyzed_aapl.json --format markdown
```

## Appendix C: Testing Checklist per Phase

### Phase 0 (Foundation)
- [ ] All models instantiate without errors
- [ ] Enum values are correct
- [ ] Dataclass field types are correct
- [ ] Model serialization/deserialization roundtrips

### Phase 1 (Extraction)
- [ ] CIK lookup works for known tickers (AAPL, MSFT, GOOGL)
- [ ] CIK lookup returns error for invalid tickers
- [ ] Company facts fetch returns expected structure
- [ ] XBRL parser extracts all 3 statements
- [ ] Periods are correctly counted and ordered
- [ ] Rate limiting is respected
- [ ] User-Agent header is properly set

### Phase 2 (Parsing)
- [ ] Exact label mapping works for all GAAP concepts
- [ ] Fuzzy matching works for close variations
- [ ] Unmapped labels are tracked
- [ ] Unit normalization is correct for all scales
- [ ] A=L+E validation catches mismatches
- [ ] ΔCash validation catches mismatches
- [ ] Derived fields are correctly computed
- [ ] Fiscal years are detected and sorted

### Phase 3 (Analysis)
- [ ] All 22 ratios compute with known inputs
- [ ] Division by zero produces None (not crash)
- [ ] Negative equity handled for ROE, D/E
- [ ] Each of 12 red flags fires at boundary
- [ ] Each of 5 cross-checks validates correctly
- [ ] Trend direction classification is correct
- [ ] Scorecard produces correct totals
- [ ] Assessment labels match score ranges

### Phase 4 (Reporting)
- [ ] Executive summary selects correct top 3 findings
- [ ] Scorecard table is correctly populated
- [ ] Each statement finding section is present
- [ ] Ratio section covers all 5 categories
- [ ] Red flags are ranked by severity
- [ ] Strengths are identified from positive indicators
- [ ] Recommendations are actionable
- [ ] Markdown output is well-formatted
- [ ] HTML output is valid and self-contained

### Phase 5 (Integration)
- [ ] Full pipeline runs AAPL without errors
- [ ] Pipeline handles missing data gracefully
- [ ] CLI flags work as documented
- [ ] Output files are created in correct locations
- [ ] Logging shows appropriate detail levels
- [ ] All integration tests pass
