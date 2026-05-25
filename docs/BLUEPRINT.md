# reading-CFS-IS-BS — Complete System Blueprint

> **Last updated:** 2026-05-25
> **Blueprint scope:** All 4 pipeline phases + final product architecture + data flow + models + tests + CLI

---

## Table of Contents

1. [Final Product Vision](#1-final-product-vision)
2. [System Architecture Overview](#2-system-architecture-overview)
3. [Phase 1: Extraction — Architecture](#3-phase-1-extraction--architecture)
4. [Phase 2: Parsing — Architecture](#4-phase-2-parsing--architecture)
5. [Phase 3: Analysis — Architecture](#5-phase-3-analysis--architecture)
6. [Phase 4: Reporting — Architecture](#6-phase-4-reporting--architecture)
7. [Data Models (Complete)](#7-data-models-complete)
8. [Pipeline Orchestration](#8-pipeline-orchestration)
9. [CLI & Slash Commands](#9-cli--slash-commands)
10. [Testing Strategy](#10-testing-strategy)
11. [Configuration & Extensibility](#11-configuration--extensibility)

---

## 1. Final Product Vision

### 1.1 What the System Does

A **local-first, CLI-driven financial statement analysis pipeline** that:

1. **Ingests** a company ticker and data source preference
2. **Extracts** raw financial data from SEC EDGAR XBRL, HTML filings, PDF annual reports (10-K/10-Q), or scans
3. **Parses** raw line items into standardized, structured financial statements with unit normalization
4. **Analyzes** the data — computes 20+ ratios across 5 categories, detects red flags, identifies trends
5. **Reports** — generates a scored, structured analysis with executive summary, scorecard, and recommendations

### 1.2 Final Product Capability Matrix

| Capability | Detail |
|-----------|--------|
| **Statements covered** | CFS, IS, BS — all three, cross-validated |
| **Data sources** | SEC EDGAR XBRL (L1), HTML tables (L2), PDF parsing (L3), OCR (L4) |
| **Periods analyzed** | 3-10 fiscal years (configurable) |
| **Ratios computed** | 22 ratios across profitability, liquidity, solvency, efficiency, cash flow quality |
| **Red flags detected** | 12 pattern-based red flags with severity ratings |
| **Trend analysis** | YoY growth, 3-year/5-year CAGR, margin trend direction |
| **Cross-statement validation** | Earnings quality, revenue quality, demand health, depreciation consistency, interest consistency |
| **Health scorecard** | 0-100 composite score across 5 dimensions |
| **Output formats** | JSON (machine), Markdown (readable), HTML (shareable) |
| **Accounting standards** | GAAP and IFRS awareness with configurable mapping |
| **Unit handling** | Auto-detect (thousands/millions/billions), normalize to millions |
| **Fiscal year** | Auto-detect or configurable fiscal year end |
| **Audit trail** | Every transformation logged with source references |
| **Pipeline resilience** | Agent failures scoped — one failure doesn't kill the pipeline |

### 1.3 Non-Goals (Deferred to v2+)

- Real-time streaming data (quarterly updates)
- Vector DB + RAG for footnote semantic search
- Multi-agent orchestration (LangGraph/CrewAI)
- Web UI / Streamlit dashboard
- PostgreSQL storage layer
- Peer/industry comparison database
- Active learning / fine-tuning loop

---

## 2. System Architecture Overview

### 2.1 Pipeline Data Flow

```
┌─────────┐     ┌─────────┐     ┌──────────┐     ┌──────────┐
│ Extract │────▶│  Parse  │────▶│ Analyze  │────▶│  Report  │
│ (L1-L4) │     │+Mapping │     │+Ratios   │     │+Scorecard│
└─────────┘     └─────────┘     └──────────┘     └──────────┘
     │               │                │                │
     ▼               ▼                ▼                ▼
extracted.json  parsed.json     analyzed.json     report.json
                                         │              │
                                         ▼              ▼
                                   report.md       report.html
```

### 2.2 Directory Structure (Complete)

```
reading-CFS-IS-BS/
├── .kilo/
│   ├── global-rules.md              # Behavioral, git, uv, coding conventions
│   ├── project-rules.md             # Financial analysis guardrails, pipeline architecture
│   ├── project-loop.md              # DEEPEN/BROADEN/PIVOT/CONCLUDE framework
│   ├── agent/                       # Pipeline agent definitions (prompts for AI agents)
│   │   ├── extractor.md
│   │   ├── parser.md
│   │   ├── analyzer.md
│   │   └── reporter.md
│   ├── command/                     # Slash command definitions
│   │   ├── analyze.md
│   │   ├── extract.md
│   │   ├── parse.md
│   │   ├── ratio.md
│   │   └── report.md
│   └── skills/                      # Project-local skills (empty, using shared skills/)
├── src/
│   ├── __init__.py
│   ├── config.py                    # Global config: defaults, paths, constants
│   ├── models/                      # Data models — the backbone of the system
│   │   ├── __init__.py
│   │   ├── enums.py                 # StatementType, PeriodType, Severity, Assessment, Status
│   │   ├── company.py               # Company dataclass
│   │   ├── line_item.py             # LineItem, UnmappedItem dataclasses
│   │   ├── statements.py            # IncomeStatement, BalanceSheet, CashFlowStatement
│   │   ├── period.py                # Period dataclass aggregating all statements
│   │   ├── ratios.py                # All ratio dataclasses (5 categories)
│   │   ├── red_flag.py              # RedFlag dataclass
│   │   ├── report_model.py          # Report dataclass (output model)
│   │   └── validation.py            # Validation result dataclasses
│   ├── extraction/                  # Phase 1: Data extraction
│   │   ├── __init__.py
│   │   ├── extractor.py             # Main orchestrator — route to source handler
│   │   ├── edgar_client.py          # SEC EDGAR XBRL API client (L1)
│   │   ├── edgar_xbrl_parser.py     # XBRL XML → raw line items parser
│   │   ├── html_extractor.py        # HTML table scraper (L2)
│   │   ├── pdf_extractor.py         # PDF parsing with PyMuPDF (L3)
│   │   ├── ocr_extractor.py         # OCR via PaddleOCR/Tesseract (L4)
│   │   ├── line_item_extractor.py   # Common line item extraction logic
│   │   ├── source_router.py         # Router: classify source → select extraction method
│   │   └── unit_detector.py         # Detect currency and unit scale from text
│   ├── parsing/                     # Phase 2: Data parsing & normalization
│   │   ├── __init__.py
│   │   ├── parser.py                # Main orchestrator
│   │   ├── label_mapper.py          # Label → standard name mapping engine
│   │   ├── mapping_dictionary.py    # Configurable mapping dictionaries (GAAP, IFRS, CN)
│   │   ├── unit_normalizer.py       # Convert all values to consistent unit
│   │   ├── structure_validator.py   # A=L+E, ΔCash reconciliation, subtotal checks
│   │   ├── subtotal_calculator.py   # Compute derived fields (gross profit, working capital, etc.)
│   │   └── fiscal_year_handler.py   # Detect/normalize fiscal year periods
│   ├── analysis/                    # Phase 3: Ratio computation & analysis
│   │   ├── __init__.py
│   │   ├── analyzer.py              # Main orchestrator
│   │   ├── ratio_calculator.py      # Compute all 22 ratios
│   │   ├── profitability.py         # Gross/Op/Net margin, ROA, ROE, EBITDA margin
│   │   ├── liquidity.py             # Current, Quick, Operating CF ratio, Working Capital
│   │   ├── solvency.py              # D/E, D/A, Interest Coverage, LT D/E
│   │   ├── efficiency.py            # Asset/Receivables/Inventory Turnover, DSO
│   │   ├── cash_flow_quality.py     # FCF, FCF Margin, CF-to-NI, FCF-to-NI
│   │   ├── trend_analyzer.py        # YoY growth, CAGR, margin trend direction
│   │   ├── red_flag_detector.py     # 12 pattern-based red flag checks
│   │   ├── cross_validator.py       # Cross-statement validation (5 checks)
│   │   ├── anomaly_detector.py      # >20% YoY volatility detection
│   │   └── scorer.py                # 0-100 financial health scorecard
│   └── reporting/                   # Phase 4: Report generation
│       ├── __init__.py
│       ├── reporter.py              # Main orchestrator
│       ├── executive_summary.py     # Top findings + overall assessment
│       ├── scorecard_builder.py     # 5-dimension scorecard assembly
│       ├── findings_section.py      # Per-statement detailed findings
│       ├── ratio_section.py         # Ratio analysis with benchmarks
│       ├── red_flags_section.py     # Ranked red flags with context
│       ├── strengths_section.py     # Positive indicators
│       ├── recommendations.py       # Actionable recommendations
│       ├── markdown_renderer.py     # Markdown output
│       ├── html_renderer.py         # HTML output
│       └── json_serializer.py       # JSON serialization
├── tests/
│   ├── __init__.py
│   ├── conftest.py                  # Shared fixtures (mock company data, test periods)
│   ├── extraction/
│   │   ├── test_edgar_client.py
│   │   ├── test_edgar_xbrl_parser.py
│   │   ├── test_html_extractor.py
│   │   ├── test_pdf_extractor.py
│   │   ├── test_ocr_extractor.py
│   │   ├── test_source_router.py
│   │   ├── test_unit_detector.py
│   │   └── test_extractor_pipeline.py
│   ├── parsing/
│   │   ├── test_label_mapper.py
│   │   ├── test_unit_normalizer.py
│   │   ├── test_structure_validator.py
│   │   ├── test_subtotal_calculator.py
│   │   ├── test_fiscal_year_handler.py
│   │   └── test_parser_pipeline.py
│   ├── analysis/
│   │   ├── test_profitability.py
│   │   ├── test_liquidity.py
│   │   ├── test_solvency.py
│   │   ├── test_efficiency.py
│   │   ├── test_cash_flow_quality.py
│   │   ├── test_trend_analyzer.py
│   │   ├── test_red_flag_detector.py
│   │   ├── test_cross_validator.py
│   │   ├── test_anomaly_detector.py
│   │   ├── test_scorer.py
│   │   └── test_analyzer_pipeline.py
│   ├── reporting/
│   │   ├── test_executive_summary.py
│   │   ├── test_scorecard_builder.py
│   │   ├── test_markdown_renderer.py
│   │   ├── test_html_renderer.py
│   │   └── test_reporter_pipeline.py
│   ├── models/
│   │   └── test_models.py
│   └── integration/
│       ├── test_apple_sample.py     # Full pipeline with known AAPL data
│       ├── test_msft_sample.py      # Full pipeline with known MSFT data
│       └── test_edge_cases.py       # Negative equity, missing data, single year, etc.
├── data/                            # Sample data and fixtures
│   ├── samples/                     # Known-good financial data for testing
│   │   ├── aapl_2020_2024.json
│   │   └── msft_2020_2024.json
│   └── mapping/                     # Label mapping dictionaries
│       ├── gaap_us.json
│       ├── ifrs_eu.json
│       └── cn_accounting.json
├── skills/
│   └── financial-statement-analysis/
│       └── SKILL.md                 # The core skill definition
├── docs/
│   ├── BLUEPRINT.md                 # This file
│   ├── IMPLEMENTATION_PLAN.md       # Step-by-step implementation plan
│   └── tech-stack-insights.md       # 125 insights from reference documents
├── pyproject.toml
├── main.py                          # CLI entry point
├── kilo.json                        # Kilo agent config
├── AGENTS.md                        # Project-specific AI agent guide
└── README.md
```

### 2.3 Dependency Graph (Import Map)

```
main.py
  └── src/
      ├── extraction/  (no internal deps except models)
      ├── parsing/     (depends on models, can consume extraction output)
      ├── analysis/    (depends on models, consumes parsing output)
      └── reporting/   (depends on models, consumes analysis output)

src/models/  ← All modules depend on models (zero internal deps)
```

### 2.4 Technology Stack

| Category | Choice | Rationale |
|----------|--------|-----------|
| **Language** | Python 3.13+ | Required by project config |
| **Package mgmt** | uv (astral.sh) | Mandatory per global rules |
| **Data models** | Pydantic v2+ | Already in deps; validation + serialization |
| **HTTP client** | requests | Already in deps; EDGAR API calls |
| **XML parsing** | lxml | XBRL XML parsing (add via uv) |
| **PDF extraction** | PyMuPDF (fitz) | Best performance for text PDFs (per insight #3, #10) |
| **HTML parsing** | BeautifulSoup4 + lxml | SEC filing HTML tables |
| **OCR fallback** | PaddleOCR or pytesseract | L4 extraction (add only when needed) |
| **Testing** | pytest >= 8.0 | Already in dev deps |
| **Linting** | ruff >= 0.1 | Already in dev deps |
| **Logging** | stdlib logging | No external dep needed |
| **Env vars** | python-dotenv | Already in deps |

---

## 3. Phase 1: Extraction — Architecture

### 3.1 Purpose

Take a ticker + source preference → produce `extracted.json` with raw line items for CFS, IS, BS across N periods.

### 3.2 Sub-Modules

#### 3.2.1 `source_router.py` — Source Classification & Routing

**Responsibility:** Given a source string (`edgar`, `html`, `pdf`, `ocr`), determine the appropriate extraction handler. If source is `auto` or unavailable, attempt L1→L2→L3→L4 escalation.

**Input:** `source: str`, `ticker: str`
**Output:** Handler function reference + metadata dict

**Key logic:**
- `edgar` → `edgar_client.py` + `edgar_xbrl_parser.py`
- `html` → `html_extractor.py`
- `pdf` → `pdf_extractor.py`
- `ocr` → `ocr_extractor.py`
- `auto` → try L1, fall to L2 on failure, etc.

#### 3.2.2 `edgar_client.py` — SEC EDGAR API Client

**Responsibility:** Fetch company submissions, locate 10-K/10-Q filings, download XBRL data.

**API endpoints used:**
- `https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type=10-K`
- Company facts: `https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json`
- Submission files: `https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/`

**Key functions:**
- `get_cik(ticker)` → CIK number
- `get_company_facts(cik)` → XBRL facts JSON
- `get_filing_list(cik, form_type, limit)` → list of filing accessions
- `download_xbrl_instance(accession_url)` → XBRL XML

**User-Agent header:** Required by SEC; must include company name + email

**Rate limiting:** 10 requests/second (SEC requirement)

#### 3.2.3 `edgar_xbrl_parser.py` — XBRL → Raw Line Items

**Responsibility:** Parse SEC XBRL JSON (companyfacts API) into raw line items grouped by statement type.

**Key logic:**
- Map XBRL concepts to statement category (CFS/IS/BS) using concept prefixes
- Handle `us-gaap` namespace (primary) and `dei` (document info)
- Extract `fy` (fiscal year) frame data for annual periods
- Handle quarterly (`Q1`, `Q2`, `Q3`, `Q4`) if requested
- Each fact has: label, value, unit, fiscal year, fiscal period
- Sort periods by fiscal year, take last N

**XBRL concept to statement mapping (example):**
- `us-gaap:Revenues` → IS
- `us-gaap:Assets` → BS
- `us-gaap:NetCashProvidedByUsedInOperatingActivities` → CFS

See full concept mapping in `mapping_dictionary.py`.

#### 3.2.4 `html_extractor.py` — HTML Table Extraction

**Responsibility:** Scrape financial statement HTML tables from SEC filing documents or financial websites.

**Key logic:**
- Locate filing document URL (10-K HTML version)
- Parse HTML with BeautifulSoup
- Identify statement tables by surrounding text/headers
- Extract table rows → line item labels + values
- Handle multi-year comparison tables (columns = years)
- Detect colspan/rowspan and normalize

#### 3.2.5 `pdf_extractor.py` — PDF Text Extraction

**Responsibility:** Extract financial tables from PDF annual reports using PyMuPDF.

**Key logic:**
- Open PDF with `fitz.open()`
- Extract text blocks with coordinates (x0, y0, x1, y1)
- **Coordinate clustering** (per insight #30): group text by Y (rows) and X (columns)
- Detect table boundaries by section header keywords
- Handle borderless tables via coordinate alignment
- Detect cross-page tables via "continued"/"续表" keywords (per insight #17)
- Merge cross-page tables: strip repeated headers, append rows (per insight #18)
- Handle "double table" scenario: IS + CFS on same page (per insight #21)
- Split dual tables by row-label semantic clustering (per insight #27)

**Section header keywords for splitting:**
- CFS: "Operating Activities", "Investing Activities", "Financing Activities" (per insight #23)
- IS: "Revenue", "Cost of Sales", "Cost of Revenue" (per insight #24)
- BS: "Current Assets", "Non-Current Assets", "Total Assets"

#### 3.2.6 `ocr_extractor.py` — OCR Fallback (L4)

**Responsibility:** Extract text from scanned/image-based PDFs when PyMuPDF text extraction fails.

**Key logic:**
- Convert PDF page to image
- Run PaddleOCR or Tesseract
- Post-process OCR text into structured line items
- Apply same coordinate clustering as PDF extractor

**Confidence score mechanism (per insight #4):**
- Only trigger OCR per-page when structural integrity score < threshold
- Not whole-document OCR fallback

#### 3.2.7 `unit_detector.py` — Currency & Unit Detection

**Responsibility:** Detect currency and unit scale from document text.

**Key logic:**
- Regex patterns for unit declarations:
  - `(in thousands)` → thousands
  - `(in millions)` → millions
  - `(in billions)` → billions
  - `($)` / `(¥)` / `(€)` → currency detection (per insight #39)
- Check table headers, footnotes, document header
- Default: assume millions if undetected

#### 3.2.8 `line_item_extractor.py` — Common Extraction Logic

**Responsibility:** Shared utilities for extracting line items from any source.

**Key functions:**
- `clean_label(label)` → strip whitespace, normalize unicode
- `parse_value(value_str)` → "1,234.5" → 1234.5, handle parentheses for negatives
- `detect_negative(value_str)` → "(123)" → -123
- `extract_period_info(text)` → detect fiscal year from surrounding text
- `build_line_item(label, value, needs_review)` → LineItem dict

### 3.3 Extraction Output Format

```json
{
  "status": "SUCCESS",
  "company": {
    "name": "Apple Inc.",
    "ticker": "AAPL",
    "cik": "0000320193",
    "fiscal_year_end": "09-30",
    "currency": "USD"
  },
  "periods": [
    {
      "type": "annual",
      "fiscal_year": 2024,
      "end_date": "2024-09-30",
      "source": "sec-edgar-xbrl",
      "statements": {
        "CFS": {
          "unit": "millions",
          "line_items": [
            {"label": "Net Income", "value": 93736.0, "needs_review": false},
            {"label": "Depreciation and Amortization", "value": 11500.0, "needs_review": false}
          ]
        },
        "IS": {
          "unit": "millions",
          "line_items": [...]
        },
        "BS": {
          "unit": "millions",
          "line_items": [...]
        }
      }
    }
  ],
  "warnings": [],
  "metadata": {
    "extraction_method": "edgar-xbrl",
    "extraction_timestamp": "2026-05-25T18:00:00Z",
    "periods_requested": 5,
    "periods_extracted": 5
  }
}
```

---

## 4. Phase 2: Parsing — Architecture

### 4.1 Purpose

Take extracted raw line items → produce `parsed.json` with standardized line items, unit normalization, and structural validation.

### 4.2 Sub-Modules

#### 4.2.1 `label_mapper.py` — Label Normalization Engine

**Responsibility:** Map company-specific label strings to canonical standard keys.

**Approach (per insight #34-43):**
1. **Exact match** against mapping dictionary first (fast)
2. **Fuzzy match** using Levenshtein distance / token sort ratio (fallback)
3. **Embedding similarity** using sentence-transformers (future/deferred)
4. **LLM fallback** for truly unmappable labels (future/deferred)

**Key functions:**
- `load_mapping_dictionary(accounting_standard)` → dict
- `map_label(label, mapping_dict)` → (standard_key, confidence)
- `get_unmapped_items(line_items, mapping_dict)` → list of unmapped items

**Confidence levels:**
- `exact` — exact match in dictionary
- `fuzzy` — fuzzy match > 0.85 similarity
- `low` — fuzzy match 0.6-0.85
- `unmapped` — no match found

#### 4.2.2 `mapping_dictionary.py` — Configurable Mapping Dictionaries

**Responsibility:** Store and load mapping dictionaries for different accounting standards.

**Files (in `data/mapping/`):**

```json
// gaap_us.json (extract)
{
  "standard": "US GAAP",
  "mappings": {
    "CFS": {
      "NetCashProvidedByUsedInOperatingActivities": "operating_cf",
      "PaymentsToAcquirePropertyPlantAndEquipment": "capex",
      "DepreciationDepletionAndAmortization": "depreciation_amortization",
      "NetIncomeLoss": "net_income",
      "PaymentsOfDividends": "dividends_paid",
      "ProceedsFromIssuanceOfCommonStock": "stock_issuance",
      "RepaymentsOfLongTermDebt": "debt_repayment",
      "ProceedsFromIssuanceOfLongTermDebt": "debt_issuance",
      "EffectOfExchangeRateOnCash": "fx_effect"
    },
    "IS": {
      "Revenues": "revenue",
      "CostOfGoodsAndServicesSold": "cogs",
      "OperatingExpenses": "operating_expenses",
      "ResearchAndDevelopmentExpense": "rnd_expense",
      "SellingGeneralAndAdministrativeExpense": "sga_expense",
      "OperatingIncomeLoss": "operating_income",
      "InterestExpense": "interest_expense",
      "InterestIncomeExpenseNonoperatingNet": "interest_income",
      "IncomeTaxExpenseBenefit": "income_tax",
      "NetIncomeLoss": "net_income",
      "EarningsPerShareBasic": "eps_basic",
      "EarningsPerShareDiluted": "eps_diluted",
      "GrossProfit": "gross_profit"
    },
    "BS": {
      "Assets": "total_assets",
      "AssetsCurrent": "current_assets",
      "CashAndCashEquivalentsAtCarryingValue": "cash_and_equivalents",
      "AccountsReceivableNetCurrent": "accounts_receivable",
      "InventoryNet": "inventory",
      "Liabilities": "total_liabilities",
      "LiabilitiesCurrent": "current_liabilities",
      "LongTermDebtNoncurrent": "long_term_debt",
      "StockholdersEquity": "total_equity",
      "Goodwill": "goodwill",
      "PropertyPlantAndEquipmentNet": "ppe_net",
      "AccountsPayableCurrent": "accounts_payable",
      "ShortTermBorrowings": "short_term_debt",
      "AccumulatedDepreciationDepletionAndAmortizationPropertyPlantAndEquipment": "accumulated_depreciation"
    }
  }
}
```

**Common label aliases (language-independent, per insight #43):**
```
"总營收" / "Revenue" / "Sales" / "Turnover" / "Top line" → revenue
"淨利潤" / "Net Profit" / "Net Income" / "Net Earnings" / "Profit attributable to shareholders" / "Bottom line" → net_income
"總資產" / "Total Assets" / "Assets" → total_assets
"營業現金流" / "Operating Cash Flow" / "Cash from Operations" → operating_cf
"營業成本" / "Cost of Goods Sold" / "Cost of Sales" / "Cost of Revenue" → cogs
```

#### 4.2.3 `unit_normalizer.py` — Unit & Currency Normalization

**Responsibility:** Convert all values to a consistent unit (millions) and detect currency.

**Key functions:**
- `detect_unit(line_items_text, headers)` → ("millions", "USD")
- `convert_to_millions(value, from_unit)` → normalized float
- `normalize_period(period_data, target_unit="millions")` → normalized period

**Conversion table:**
| From | Multiplier |
|------|-----------|
| actual | × 1,000,000 → divide by 1,000,000 |
| thousands | × 1,000 → divide by 1,000 |
| millions | × 1 (no change) |
| billions | × 1,000 (multiply by 1,000) |

**Important:** Store original value + unit alongside normalized value (per insight #44).

#### 4.2.4 `structure_validator.py` — Structural Integrity Checks

**Responsibility:** Validate that the parsed data satisfies accounting identities.

**Validation checks (per insight #58-63):**

1. **Balance Sheet Balance:** `|total_assets - (total_liabilities + total_equity)| / total_assets < 0.001` (tolerance ±0.1%)
2. **Cash Flow Reconciliation:** `|net_change_cash - (operating_cf + investing_cf + financing_cf)| / |net_change_cash| < 0.005`
3. **Income Statement Arithmetic:** `gross_profit ≈ revenue - cogs`
4. **Net Income Delta:** `net_income ≈ operating_income - interest_expense + interest_income - income_tax`
5. **Current/Non-Current Sum:** `current_assets ≤ total_assets`

**Key functions:**
- `validate_balance_sheet(bs_data)` → ValidationResult
- `validate_cash_flow(cfs_data)` → ValidationResult
- `validate_income_statement(is_data)` → ValidationResult
- `run_all_validations(period)` → list of ValidationResult

**All checks are hardcoded — never let LLM guess financial logic (per insight #63).**

#### 4.2.5 `subtotal_calculator.py` — Derived Field Computation

**Responsibility:** Compute derived/subtotal line items that weren't explicitly in the raw data.

**Key computations:**
- `gross_profit = revenue - cogs`
- `operating_income = gross_profit - operating_expenses` (if not present)
- `total_current_assets = cash + ar + inventory + other_ca` (if components exist)
- `working_capital = current_assets - current_liabilities`
- `invested_capital = total_equity + long_term_debt`
- `ebitda = operating_income + depreciation_amortization`
- `fcf = operating_cf - capex`

#### 4.2.6 `fiscal_year_handler.py` — Fiscal Year Period Handling

**Responsibility:** Detect, validate, and normalize fiscal year periods.

**Key logic:**
- Parse end_date strings → datetime objects
- Sort periods chronologically
- Fill gaps in period sequence (mark as missing)
- Handle companies with non-calendar fiscal years (e.g., AAPL ends Sep 30)
- Generate period labels: "FY2024", "FY2023", "Q1 2024", etc.

### 4.3 Parsing Output Format

```json
{
  "status": "SUCCESS",
  "company": {"name": "Apple Inc.", "ticker": "AAPL", "fiscal_year_end": "09-30"},
  "accounting_standard": "US GAAP",
  "unit": "millions",
  "currency": "USD",
  "periods": [
    {
      "type": "annual",
      "fiscal_year": 2024,
      "end_date": "2024-09-30",
      "statements": {
        "income_statement": {
          "revenue": 391035.0,
          "cogs": 210352.0,
          "gross_profit": 180683.0,
          "operating_expenses": 57612.0,
          "rnd_expense": 31370.0,
          "sga_expense": 26242.0,
          "operating_income": 123071.0,
          "interest_expense": 4032.0,
          "interest_income": 4063.0,
          "income_tax": 29749.0,
          "net_income": 93736.0,
          "eps_basic": 6.11,
          "eps_diluted": 6.08,
          "ebitda": 134571.0,
          "unmapped": []
        },
        "balance_sheet": {
          "total_assets": 364980.0,
          "current_assets": 152987.0,
          "cash_and_equivalents": 65171.0,
          "accounts_receivable": 33410.0,
          "inventory": 7286.0,
          "total_liabilities": 308030.0,
          "current_liabilities": 176392.0,
          "long_term_debt": 85750.0,
          "total_equity": 56950.0,
          "goodwill": 0.0,
          "ppe_net": 45680.0,
          "accounts_payable": 68960.0,
          "short_term_debt": 9967.0,
          "accumulated_depreciation": 72500.0,
          "unmapped": []
        },
        "cash_flow_statement": {
          "operating_cf": 118254.0,
          "investing_cf": -2936.0,
          "financing_cf": -121983.0,
          "capex": -9447.0,
          "depreciation_amortization": 11500.0,
          "net_change_cash": -6665.0,
          "dividends_paid": -15234.0,
          "stock_issuance": 0.0,
          "debt_repayment": -9950.0,
          "debt_issuance": 0.0,
          "fx_effect": 0.0,
          "unmapped": []
        }
      },
      "validation": {
        "accounting_equation": {
          "holds": true,
          "difference": 0.0,
          "diff_pct": 0.0
        },
        "cash_flow_reconciliation": {
          "holds": true,
          "expected": -6665.0,
          "actual": -6665.0
        },
        "income_statement_arithmetic": {
          "holds": true
        },
        "warnings": []
      }
    }
  ],
  "mapping_stats": {
    "total_items": 85,
    "mapped_exact": 72,
    "mapped_fuzzy": 10,
    "unmapped": 3
  }
}
```

---

## 5. Phase 3: Analysis — Architecture

### 5.1 Purpose

Take parsed structured statements → produce `analyzed.json` with computed ratios, trends, red flags, and cross-statement validation.

### 5.2 Sub-Modules

#### 5.2.1 `ratio_calculator.py` — Orchestrator

Runs all ratio computations across 5 categories and collects results.

#### 5.2.2 `profitability.py` — Profitability Ratios

| Ratio | Formula | Unit |
|-------|---------|------|
| Gross Margin | gross_profit / revenue | % |
| Operating Margin | operating_income / revenue | % |
| Net Margin | net_income / revenue | % |
| ROA | net_income / total_assets | % |
| ROE | net_income / total_equity | % |
| EBITDA Margin | ebitda / revenue | % |

**Edge cases:**
- Revenue = 0 → skip ratio, log warning
- Negative equity → ROE is meaningless, flag
- Negative operating income → margins are negative, flag

#### 5.2.3 `liquidity.py` — Liquidity Ratios

| Ratio | Formula | Unit |
|-------|---------|------|
| Current Ratio | current_assets / current_liabilities | ratio |
| Quick Ratio | (current_assets - inventory) / current_liabilities | ratio |
| Working Capital | current_assets - current_liabilities | currency |
| Operating CF Ratio | operating_cf / current_liabilities | ratio |

**Red flag thresholds:**
- Current Ratio < 1.0 → liquidity risk
- Quick Ratio < 0.5 → severe liquidity concern
- Negative Working Capital → cash strain
- Operating CF Ratio < 0 → cannot cover short-term obligations from operations

#### 5.2.4 `solvency.py` — Solvency Ratios

| Ratio | Formula | Unit |
|-------|---------|------|
| Debt-to-Equity | total_liabilities / total_equity | ratio |
| Debt-to-Assets | total_liabilities / total_assets | % |
| Interest Coverage | operating_income / interest_expense | ratio |
| LT Debt-to-Equity | long_term_debt / total_equity | ratio |

**Red flag thresholds:**
- D/E > 2.0 (configurable by industry) → excessive leverage
- Interest Coverage < 1.5 → debt service concern
- Interest Coverage < 1.0 → cannot cover interest from operations

#### 5.2.5 `efficiency.py` — Efficiency Ratios

| Ratio | Formula | Unit |
|-------|---------|------|
| Asset Turnover | revenue / total_assets | ratio |
| Receivables Turnover | revenue / accounts_receivable | ratio |
| Inventory Turnover | cogs / inventory | ratio |
| Days Sales Outstanding | 365 / receivables_turnover | days |

**Edge cases:**
- AR = 0 → skip receivables turnover, log
- Inventory = 0 → skip inventory turnover, log

#### 5.2.6 `cash_flow_quality.py` — Cash Flow Quality Indicators

| Ratio | Formula | Unit |
|-------|---------|------|
| Free Cash Flow | operating_cf - abs(capex) | currency |
| FCF Margin | fcf / revenue | % |
| CF-to-NI | operating_cf / net_income | ratio |
| FCF-to-NI | fcf / net_income | ratio |

**Red flag thresholds:**
- CF/NI < 0.5 → earnings quality concern
- Negative FCF → cash burn
- CF/NI < 1.0 for 3+ consecutive years → sustained earnings quality issue

#### 5.2.7 `trend_analyzer.py` — Trend Analysis

**Computes:**
- **YoY growth rates:** `(value_t - value_{t-1}) / |value_{t-1}|` for all major line items
- **CAGR:** `(value_end / value_start)^(1/years) - 1` for 3-year and 5-year
- **Margin trend direction:** Compare most recent 2 periods to prior 3
  - `improving` — margins expanding each year
  - `stable` — margins within ±1% band
  - `declining` — margins contracting each year
  - `mixed` — no clear pattern

**Key functions:**
- `compute_yoy_growth(values)` → list of growth rates
- `compute_cagr(values, periods)` → CAGR float
- `classify_margin_trend(margins)` → "improving" | "stable" | "declining" | "mixed"
- `detect_acceleration(growth_rates)` → "accelerating" | "decelerating" | "stable"

#### 5.2.8 `red_flag_detector.py` — Red Flag Detection

**12 red flags ranked by severity:**

| # | Red Flag | Condition | Severity |
|---|----------|-----------|----------|
| 1 | Earnings quality concern | CF-to-NI < 0.5 | critical |
| 2 | Liquidity crisis risk | Current Ratio < 1.0 | critical |
| 3 | Excessive leverage | D/E > configurable industry threshold | warning |
| 4 | Sustained negative op CF | Operating CF < 0 for 3+ consecutive periods | critical |
| 5 | Aggressive revenue recognition | AR growth > Revenue growth (2+ periods) | warning |
| 6 | Demand problem | Inventory growth > Revenue growth | warning |
| 7 | Acquisition risk | Goodwill > 50% of equity | warning |
| 8 | Debt service concern | Interest Coverage < 1.5 | warning |
| 9 | Cannot cover interest | Interest Coverage < 1.0 | critical |
| 10 | Negative equity | Total Equity < 0 | critical |
| 11 | Sustained margin decline | Margins declining 3+ consecutive periods | warning |
| 12 | Cash burn | Negative FCF for 3+ consecutive periods | warning |

**Key functions:**
- `detect_all(parsed_data, ratios)` → list of RedFlag
- `evaluate_severity(flag_type, value, context)` → Severity
- `flag_earnings_quality(cf_to_ni_series)` → RedFlag or None
- `flag_liquidity_crisis(current_ratios)` → RedFlag or None
- ... (one function per flag for testability)

#### 5.2.9 `cross_validator.py` — Cross-Statement Validation

**5 cross-statement checks:**

| # | Check | What It Reveals |
|---|-------|----------------|
| 1 | Operating CF > Net Income (long-term avg) | Quality of earnings |
| 2 | AR growth ≤ Revenue growth | Revenue quality |
| 3 | Inventory growth ≤ Revenue growth | Demand health |
| 4 | ΔAccumulated Depreciation ≈ Depreciation Expense | Depreciation consistency |
| 5 | Interest Expense ≈ Debt × Market Rate | Interest consistency |

**Output per check:** `{check_name, result: "PASS"|"WARN"|"FAIL", detail, periods_evaluated}`

#### 5.2.10 `anomaly_detector.py` — Anomaly Detection

Detect year-over-year volatility > 20% without apparent explanation (per insight #91).

**Key functions:**
- `detect_volatility_spikes(values, threshold=0.2)` → list of anomaly dicts
- `flag_unexplained_change(current, previous, threshold=0.2)` → Anomaly or None

#### 5.2.11 `scorer.py` — Financial Health Scorecard (0-100)

**5 dimensions, each 0-20 points:**

**Profitability (20 pts):**
| Sub-component | Max Points | Scoring |
|---------------|-----------|---------|
| Gross margin trend | 5 | Stable/improving: 5, slight decline: 3, sharp decline: 0 |
| Operating margin trend | 5 | Same scale |
| Net margin trend | 5 | Same scale |
| ROE level | 5 | >15%: 5, >10%: 3, >5%: 1, <5%: 0 |

**Liquidity (20 pts):**
| Sub-component | Max Points | Scoring |
|---------------|-----------|---------|
| Current ratio | 7 | >2.0: 7, >1.5: 5, >1.0: 3, <1.0: 0 |
| Quick ratio | 5 | >1.0: 5, >0.5: 3, <0.5: 0 |
| Operating CF ratio | 4 | >0.5: 4, >0.2: 2, <0.2: 0 |
| Working capital trend | 4 | Stable/improving: 4, declining: 2, negative: 0 |

**Solvency (20 pts):**
| Sub-component | Max Points | Scoring |
|---------------|-----------|---------|
| D/E ratio | 8 | <0.5: 8, <1.0: 6, <2.0: 3, >2.0: 0 |
| Interest coverage | 8 | >10: 8, >5: 6, >2: 3, <1.5: 1, <1.0: 0 |
| Debt maturity profile | 4 | From notes (deferred: default 2) |

**Efficiency (20 pts):**
| Sub-component | Max Points | Scoring |
|---------------|-----------|---------|
| Asset turnover trend | 6 | Improving: 6, stable: 4, declining: 2 |
| DSO trend | 5 | Declining: 5, stable: 3, increasing: 1 |
| Inventory turnover trend | 5 | Improving: 5, stable: 3, declining: 1 |
| Operating cycle trend | 4 | Improving: 4, stable: 2, worsening: 0 |

**Cash Flow Quality (20 pts):**
| Sub-component | Max Points | Scoring |
|---------------|-----------|---------|
| CF/NI ratio (avg) | 6 | >1.5: 6, >1.0: 4, >0.5: 2, <0.5: 0 |
| FCF margin trend | 6 | Improving: 6, stable: 4, declining: 2 |
| FCF sustainability | 4 | Positive 5 years: 4, positive 3 years: 2, negative: 0 |
| Capex/revenue trend | 4 | Consistent: 4, erratic: 2, declining: 0 |

### 5.3 Analysis Output Format

```json
{
  "status": "SUCCESS",
  "company": {"name": "Apple Inc.", "ticker": "AAPL"},
  "periods_analyzed": 5,
  "analysis_period": "FY2020-FY2024",
  "ratios": {
    "profitability": {
      "gross_margin": [
        {"period": "FY2024", "value": 0.462},
        {"period": "FY2023", "value": 0.443}
      ],
      "operating_margin": [...] ,
      "net_margin": [...],
      "roa": [...],
      "roe": [...],
      "ebitda_margin": [...]
    },
    "liquidity": {
      "current_ratio": [...],
      "quick_ratio": [...],
      "working_capital": [...],
      "operating_cf_ratio": [...]
    },
    "solvency": {
      "debt_to_equity": [...],
      "debt_to_assets": [...],
      "interest_coverage": [...],
      "lt_debt_to_equity": [...]
    },
    "efficiency": {
      "asset_turnover": [...],
      "receivables_turnover": [...],
      "inventory_turnover": [...],
      "days_sales_outstanding": [...]
    },
    "cash_flow_quality": {
      "fcf": [...],
      "fcf_margin": [...],
      "cf_to_ni": [...],
      "fcf_to_ni": [...]
    }
  },
  "trends": {
    "revenue_yoy_growth": [
      {"period": "FY2024", "value": -0.018}
    ],
    "net_income_yoy_growth": [...],
    "operating_cf_yoy_growth": [...],
    "fcf_yoy_growth": [...],
    "revenue_cagr_3yr": 0.054,
    "revenue_cagr_5yr": 0.072,
    "margin_trend": "stable"
  },
  "cross_validation": {
    "earnings_quality": {"result": "PASS", "detail": "OCF/NI avg 1.26 over 5 years"},
    "revenue_quality": {"result": "PASS", "detail": "AR growth 2.1% vs Revenue growth 5.4%"},
    "demand_health": {"result": "PASS", "detail": "Inventory growth -3.2% vs Revenue growth 5.4%"},
    "depreciation_consistency": {"result": "PASS", "detail": "ΔAccDep $11.2B ≈ DepExp $11.5B"},
    "interest_consistency": {"result": "PASS", "detail": "Implied rate 4.7% vs market ~5%"}
  },
  "red_flags": [
    {
      "type": "excessive_leverage",
      "severity": "warning",
      "description": "D/E ratio of 5.41 exceeds 2.0 threshold. However, Apple's D/E is inflated by share buybacks reducing equity — review net debt position.",
      "periods_affected": ["FY2024", "FY2023", "FY2022"],
      "current_value": 5.41,
      "threshold": 2.0
    }
  ],
  "anomalies": [],
  "scorecard": {
    "profitability": 18,
    "liquidity": 12,
    "solvency": 10,
    "efficiency": 16,
    "cash_flow_quality": 18,
    "total": 74,
    "assessment": "Adequate"
  }
}
```

---

## 6. Phase 4: Reporting — Architecture

### 6.1 Purpose

Take analyzed data → produce a readable report in JSON (machine), Markdown (readable), and HTML (shareable) formats.

### 6.2 Report Structure (7 Sections)

1. **Executive Summary** — Top 3 findings + overall assessment
2. **Financial Health Scorecard** — 5 dimensions with scores
3. **Detailed Findings** — Per-statement analysis (IS, BS, CFS)
4. **Ratio Analysis** — All ratios with trends and interpretation
5. **Red Flags & Risks** — Ranked by materiality
6. **Strengths** — What the company does well
7. **Recommendations** — Actionable next steps

### 6.3 Sub-Modules

#### 6.3.1 `executive_summary.py`

**Logic:**
- Select top 3 most material findings:
  - Most severe red flag (critical > warning > info)
  - Largest ratio deviation from norm
  - Most significant trend direction change
- Determine overall assessment from scorecard total:
  - 80-100 → "Strong"
  - 60-79 → "Adequate"
  - 40-59 → "Concerning"
  - 0-39 → "Critical"

#### 6.3.2 `scorecard_builder.py`

Assembles the 5-dimension 0-100 scorecard with per-dimension breakdown and assessment level.

#### 6.3.3 `findings_section.py`

For each statement (IS, BS, CFS):
- Key line items with YoY changes
- 3-5 year trend narrative
- Significant one-time items or anomalies
- Footnotes requiring attention (from `needs_review` flags)

#### 6.3.4 `ratio_section.py`

For each ratio category:
- Current value + trend direction
- Interpretation text
- Any warnings about edge cases

#### 6.3.5 `red_flags_section.py`

Red flags ranked by severity (critical first), each with:
- Type, severity, description
- Historical context: is this new or persistent?
- Mitigation context (if available)

#### 6.3.6 `strengths_section.py`

Positive indicators:
- Ratios in healthy ranges
- Improving trends
- Cross-validation passes
- Competitive advantages evident in statements

#### 6.3.7 `recommendations.py`

Actionable next steps:
- Areas requiring deeper investigation
- Watch items for next reporting period
- Peer comparison suggestions

#### 6.3.8 `markdown_renderer.py`

Converts the report JSON into a well-formatted Markdown document with tables, headers, and formatting.

#### 6.3.9 `html_renderer.py`

Converts the report JSON into a standalone HTML document with basic CSS styling.

### 6.4 Report Output Format

```json
{
  "status": "SUCCESS",
  "report": {
    "company": {"name": "Apple Inc.", "ticker": "AAPL"},
    "periods_analyzed": "FY2020-FY2024",
    "generated_at": "2026-05-25T18:00:00Z",
    "executive_summary": {
      "top_findings": [
        "Strong free cash flow generation with FCF margin averaging 27.7% over 5 years",
        "D/E ratio elevated at 5.41 due to aggressive share buybacks — net debt position is more relevant",
        "Revenue growth decelerating with -1.8% YoY in FY2024 — monitor for structural slowdown"
      ],
      "overall_assessment": "Adequate"
    },
    "scorecard": {
      "profitability": 18,
      "liquidity": 12,
      "solvency": 10,
      "efficiency": 16,
      "cash_flow_quality": 18,
      "total": 74,
      "assessment": "Adequate"
    },
    "detailed_findings": {
      "income_statement": "Revenue declined 1.8% YoY to $391B. Gross margin improved to 46.2% (from 44.3%). Net income declined 3.4% to $93.7B. R&D spending increased to 8.0% of revenue.",
      "balance_sheet": "Total assets $365B. Cash position $65B (down from $73B). Negative working capital of -$23B indicates efficient cash conversion cycle. D/E inflated by buybacks — net debt per share is $12.45.",
      "cash_flow_statement": "Operating CF of $118B remains strong (CF/NI of 1.26). FCF of $109B after $9.4B capex. $122B returned to shareholders via buybacks and dividends."
    },
    "ratio_analysis": "Gross margin of 46.2% is excellent and improving. Operating margin of 31.5% indicates strong pricing power. CF/NI of 1.26 confirms high earnings quality. D/E of 5.41 is misleading — review net debt/EBITDA instead.",
    "red_flags": [
      {
        "type": "excessive_leverage",
        "severity": "warning",
        "description": "D/E ratio 5.41 exceeds threshold but is primarily driven by share buybacks reducing equity. Net cash position suggests this is not a solvency concern.",
        "periods_affected": ["FY2024", "FY2023", "FY2022"]
      },
      {
        "type": "revenue_decline",
        "severity": "warning",
        "description": "Revenue declined 1.8% YoY. Monitor next quarter for confirmation of trend reversal or structural slowdown.",
        "periods_affected": ["FY2024"]
      }
    ],
    "strengths": [
      "Industry-leading gross margins (46.2%) indicating strong pricing power and brand value",
      "Exceptional free cash flow generation ($109B FCF, 27.7% FCF margin)",
      "High earnings quality (CF/NI ratio consistently >1.0 over full analysis period)",
      "Efficient working capital management with negative cash conversion cycle"
    ],
    "recommendations": [
      "Monitor revenue growth trajectory — two consecutive quarters of decline warrants deeper analysis of product mix",
      "Review net debt/EBITDA rather than D/E for leverage assessment given buyback impact",
      "Track Services revenue growth as key margin driver (likely higher margin than hardware)",
      "Evaluate capex adequacy — 2.4% of revenue may be low for a tech hardware company",
      "Compare against peer group (MSFT, GOOGL, AMZN) for relative valuation context"
    ]
  }
}
```

---

## 7. Data Models (Complete)

### 7.1 `enums.py`

```python
from enum import Enum

class StatementType(Enum):
    INCOME_STATEMENT = "income_statement"
    BALANCE_SHEET = "balance_sheet"
    CASH_FLOW_STATEMENT = "cash_flow_statement"

class PeriodType(Enum):
    ANNUAL = "annual"
    QUARTERLY = "quarterly"

class Severity(Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"

class Assessment(Enum):
    STRONG = "Strong"
    ADEQUATE = "Adequate"
    CONCERNING = "Concerning"
    CRITICAL = "Critical"

class PipelineStatus(Enum):
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    ERROR = "ERROR"

class AccountingStandard(Enum):
    US_GAAP = "US GAAP"
    IFRS = "IFRS"
    CN_GAAP = "China GAAP"

class ExtractionSource(Enum):
    EDGAR_XBRL = "edgar-xbrl"
    HTML = "html"
    PDF = "pdf"
    OCR = "ocr"

class MappingConfidence(Enum):
    EXACT = "exact"
    FUZZY = "fuzzy"
    LOW = "low"
    UNMAPPED = "unmapped"

class TrendDirection(Enum):
    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"
    MIXED = "mixed"
```

### 7.2 `company.py`

```python
@dataclass
class Company:
    name: str
    ticker: str
    cik: str | None = None
    fiscal_year_end: str = ""       # "09-30"
    currency: str = "USD"
    industry: str = ""
    exchange: str = ""
```

### 7.3 `line_item.py`

```python
@dataclass
class LineItem:
    label: str                      # Original label from source
    value: float
    needs_review: bool = False
    standard_key: str | None = None  # Mapped standard key
    mapping_confidence: MappingConfidence | None = None
    original_unit: str = ""         # "thousands", "millions", etc.
    original_value: float | None = None
    xbrl_concept: str | None = None # XBRL concept name if applicable

@dataclass
class UnmappedItem:
    original_label: str
    value: float
    statement_type: StatementType
```

### 7.4 `statements.py`

```python
@dataclass
class IncomeStatement:
    revenue: float = 0.0
    cogs: float = 0.0
    gross_profit: float = 0.0
    operating_expenses: float = 0.0
    rnd_expense: float = 0.0
    sga_expense: float = 0.0
    operating_income: float = 0.0
    interest_expense: float = 0.0
    interest_income: float = 0.0
    income_tax: float = 0.0
    net_income: float = 0.0
    eps_basic: float = 0.0
    eps_diluted: float = 0.0
    ebitda: float = 0.0
    unmapped: list[UnmappedItem] = field(default_factory=list)

@dataclass
class BalanceSheet:
    total_assets: float = 0.0
    current_assets: float = 0.0
    cash_and_equivalents: float = 0.0
    accounts_receivable: float = 0.0
    inventory: float = 0.0
    total_liabilities: float = 0.0
    current_liabilities: float = 0.0
    long_term_debt: float = 0.0
    total_equity: float = 0.0
    goodwill: float = 0.0
    ppe_net: float = 0.0
    accounts_payable: float = 0.0
    short_term_debt: float = 0.0
    accumulated_depreciation: float = 0.0
    unmapped: list[UnmappedItem] = field(default_factory=list)

@dataclass
class CashFlowStatement:
    operating_cf: float = 0.0
    investing_cf: float = 0.0
    financing_cf: float = 0.0
    capex: float = 0.0
    depreciation_amortization: float = 0.0
    net_change_cash: float = 0.0
    dividends_paid: float = 0.0
    stock_issuance: float = 0.0
    debt_repayment: float = 0.0
    debt_issuance: float = 0.0
    fx_effect: float = 0.0
    unmapped: list[UnmappedItem] = field(default_factory=list)
```

### 7.5 `period.py`

```python
@dataclass
class ValidationResult:
    check_name: str
    holds: bool
    expected: float = 0.0
    actual: float = 0.0
    difference: float = 0.0
    diff_pct: float = 0.0
    detail: str = ""

@dataclass
class Period:
    type: PeriodType
    fiscal_year: int
    end_date: str
    income_statement: IncomeStatement = field(default_factory=IncomeStatement)
    balance_sheet: BalanceSheet = field(default_factory=BalanceSheet)
    cash_flow_statement: CashFlowStatement = field(default_factory=CashFlowStatement)
    validation_results: list[ValidationResult] = field(default_factory=list)
    source: str = ""
    original_unit: str = ""
```

### 7.6 `ratios.py`

```python
@dataclass
class RatioPoint:
    period: str
    value: float
    unit: str = ""  # "%", "ratio", "days", "USD"

@dataclass
class ProfitabilityRatios:
    gross_margin: list[RatioPoint] = field(default_factory=list)
    operating_margin: list[RatioPoint] = field(default_factory=list)
    net_margin: list[RatioPoint] = field(default_factory=list)
    roa: list[RatioPoint] = field(default_factory=list)
    roe: list[RatioPoint] = field(default_factory=list)
    ebitda_margin: list[RatioPoint] = field(default_factory=list)

@dataclass
class LiquidityRatios:
    current_ratio: list[RatioPoint] = field(default_factory=list)
    quick_ratio: list[RatioPoint] = field(default_factory=list)
    working_capital: list[RatioPoint] = field(default_factory=list)
    operating_cf_ratio: list[RatioPoint] = field(default_factory=list)

@dataclass
class SolvencyRatios:
    debt_to_equity: list[RatioPoint] = field(default_factory=list)
    debt_to_assets: list[RatioPoint] = field(default_factory=list)
    interest_coverage: list[RatioPoint] = field(default_factory=list)
    lt_debt_to_equity: list[RatioPoint] = field(default_factory=list)

@dataclass
class EfficiencyRatios:
    asset_turnover: list[RatioPoint] = field(default_factory=list)
    receivables_turnover: list[RatioPoint] = field(default_factory=list)
    inventory_turnover: list[RatioPoint] = field(default_factory=list)
    days_sales_outstanding: list[RatioPoint] = field(default_factory=list)

@dataclass
class CashFlowQualityRatios:
    fcf: list[RatioPoint] = field(default_factory=list)
    fcf_margin: list[RatioPoint] = field(default_factory=list)
    cf_to_ni: list[RatioPoint] = field(default_factory=list)
    fcf_to_ni: list[RatioPoint] = field(default_factory=list)
```

### 7.7 `red_flag.py`

```python
@dataclass
class RedFlag:
    type: str                       # e.g., "earnings_quality_concern"
    severity: Severity
    description: str
    periods_affected: list[str]
    current_value: float | None = None
    threshold: float | None = None
    historical_context: str = ""    # "new in FY2024" or "persistent since FY2021"
```

### 7.8 `report_model.py`

```python
@dataclass
class Scorecard:
    profitability: int = 0   # 0-20
    liquidity: int = 0       # 0-20
    solvency: int = 0        # 0-20
    efficiency: int = 0      # 0-20
    cash_flow_quality: int = 0  # 0-20
    total: int = 0           # 0-100
    assessment: str = ""     # Strong|Adequate|Concerning|Critical

@dataclass
class ExecutiveSummary:
    top_findings: list[str] = field(default_factory=list)
    overall_assessment: str = ""

@dataclass
class CrossValidationResult:
    check_name: str
    result: str               # PASS|WARN|FAIL
    detail: str
    periods_evaluated: int = 0

@dataclass
class Report:
    company: Company
    periods_analyzed: str
    generated_at: str = ""
    executive_summary: ExecutiveSummary = field(default_factory=ExecutiveSummary)
    scorecard: Scorecard = field(default_factory=Scorecard)
    detailed_findings: dict[str, str] = field(default_factory=dict)
    ratio_analysis: str = ""
    red_flags: list[RedFlag] = field(default_factory=list)
    strengths: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    cross_validation: list[CrossValidationResult] = field(default_factory=list)
```

---

## 8. Pipeline Orchestration

### 8.1 Main Pipeline Function

```python
def run_pipeline(ticker: str, periods: int = 5, source: str = "edgar") -> PipelineResult:
    """Run the complete extract→parse→analyze→report pipeline."""
    # 1. Extract
    raw_data = extract_financial_data(ticker, periods=periods, source=source)
    if raw_data["status"] == "ERROR":
        return PipelineResult(status="ERROR", phase="extraction", error=raw_data)

    # 2. Parse
    parsed_data = parse_financial_data(raw_data)
    if parsed_data["status"] == "ERROR":
        return PipelineResult(status="ERROR", phase="parsing", error=parsed_data)

    # 3. Analyze
    analyzed_data = analyze_financial_data(parsed_data)
    if analyzed_data["status"] == "ERROR":
        return PipelineResult(status="ERROR", phase="analysis", error=analyzed_data)

    # 4. Report
    report = generate_report(analyzed_data)
    return PipelineResult(status="SUCCESS", result=report)
```

### 8.2 Error Handling Strategy

- Each agent returns `status` in its output: `SUCCESS`, `WARNING`, or `ERROR`
- `ERROR` at any phase stops the pipeline and reports which phase failed
- `WARNING` at any phase continues but carries the warning forward
- Extraction warnings (missing data) → parser attempts best-effort mapping
- Parser warnings (unmapped items) → analyzer skips affected ratios
- Analyzer warnings (incomplete ratios) → reporter notes data limitations

### 8.3 Pipeline Config

```python
@dataclass
class PipelineConfig:
    ticker: str
    periods: int = 5
    source: str = "edgar"
    output_dir: Path = Path("output")
    save_intermediate: bool = True  # Save extracted.json, parsed.json, etc.
    output_format: str = "json"     # json, markdown, html
    accounting_standard: str = "auto"  # auto-detect or "us-gaap", "ifrs"
    target_currency: str = "USD"
    target_unit: str = "millions"
```

---

## 9. CLI & Slash Commands

### 9.1 CLI Commands (main.py)

| Command | Description | Pipeline Phase |
|---------|-------------|---------------|
| `analyze <ticker>` | Full pipeline | extract → parse → analyze → report |
| `extract <ticker>` | Extraction only | extract |
| `parse <file>` | Parsing only | parse |
| `ratio <file>` | Analysis only | analyze |
| `report <file>` | Reporting only | report |

**Options for all commands:**
- `--periods N` (default: 5)
- `--source <edgar|html|pdf|ocr>` (default: edgar)
- `--output-dir <dir>` (default: output/)
- `--format <json|markdown|html>` (default: json, report command only)
- `--accounting <us-gaap|ifrs|auto>` (default: auto)

### 9.2 Slash Commands (AI Agent)

| Command | Agent Pipeline | Usage |
|---------|---------------|-------|
| `/analyze` | extractor → parser → analyzer → reporter | `/analyze AAPL --periods 5` |
| `/extract` | extractor only | `/extract MSFT --source edgar` |
| `/parse` | parser only | `/parse output/extracted.json` |
| `/ratio` | analyzer only | `/ratio output/parsed.json` |
| `/report` | reporter only | `/report output/analyzed.json --format markdown` |

---

## 10. Testing Strategy

### 10.1 Test Pyramid

```
        ┌─────────┐
        │   E2E   │  3 tests: full pipeline with known AAPL/MSFT/edge-case data
        │   (3)   │
       ┌┴─────────┴┐
       │Integration│  8 tests: cross-module (extract→parse, parse→analyze, etc.)
       │    (8)    │
      ┌┴───────────┴┐
      │    Unit     │  ~50 tests: one per module/function
      │   (~50)     │
      └─────────────┘
```

### 10.2 Unit Test Coverage Target

Every public function must have:
1. **Happy path** — normal input → expected output
2. **Edge case** — zero values, missing data, negative equity, division by zero
3. **Error case** — invalid input, malformed data
4. **Boundary** — exactly at threshold (e.g., D/E = 2.0, Current Ratio = 1.0)

### 10.3 Test Fixtures

```python
# conftest.py — shared fixtures

@pytest.fixture
def sample_company():
    return Company(name="TestCo", ticker="TEST", fiscal_year_end="12-31")

@pytest.fixture
def sample_parsed_periods():
    """5 years of normalized financial data for testing."""
    return [...]  # List of Period dataclasses with known values

@pytest.fixture
def sample_ratios():
    """Pre-computed ratio data for testing reporter."""
    return {...}  # Full ratio dictionary

@pytest.fixture
def apple_2020_2024_data():
    """Real AAPL data for integration tests."""
    return json.loads(Path("data/samples/aapl_2020_2024.json").read_text())
```

### 10.4 Integration Test Scenarios

| Test | What It Validates |
|------|------------------|
| `test_apple_pipeline` | Full pipeline produces valid report for AAPL |
| `test_msft_pipeline` | Full pipeline produces valid report for MSFT |
| `test_missing_data_graceful` | Missing BS data → parser warns, analyzer skips BS ratios |
| `test_negative_equity` | Negative equity → D/E flagged, ROE skipped |
| `test_single_year` | Only 1 year of data → skip trends, log warning |
| `test_zero_revenue` | Zero revenue → skip margin ratios, log warning |
| `test_extract_parse_roundtrip` | extraction output → parser accept/reject |
| `test_parse_analyze_roundtrip` | parsed output → analyzer accept/reject |

---

## 11. Configuration & Extensibility

### 11.1 Mapping Dictionary Extension

To add a new accounting standard (e.g., Japan GAAP):

1. Create `data/mapping/jp_gaap.json`
2. Add mappings for CFS, IS, BS line item labels → standard keys
3. Register in `mapping_dictionary.py::STANDARDS`
4. Use via `--accounting jp-gaap` flag

### 11.2 Ratio Extension

To add a new ratio:

1. Add computation function in appropriate `src/analysis/<category>.py`
2. Add field to corresponding Ratio dataclass in `src/models/ratios.py`
3. Register in `ratio_calculator.py::COMPUTED_RATIOS` dict
4. Add tests in `tests/analysis/test_<category>.py`
5. Add interpretation logic in `src/reporting/ratio_section.py`

### 11.3 Red Flag Extension

To add a new red flag:

1. Add detection function in `src/analysis/red_flag_detector.py`
2. Register in `red_flag_detector.py::RED_FLAG_CHECKS` list
3. Add test in `tests/analysis/test_red_flag_detector.py`
4. Add description template in `src/reporting/red_flags_section.py`

### 11.4 Output Format Extension

To add a new output format (e.g., PDF):

1. Create `src/reporting/pdf_renderer.py`
2. Implement `render_pdf(report: Report, output_path: Path) -> Path`
3. Register in `src/reporting/reporter.py::RENDERERS`
4. Add `--format pdf` option to CLI

---

## Appendix A: XBRL Concept → Statement Mapping (Partial)

This is the core mapping from SEC EDGAR XBRL concepts to our standard keys. The full mapping lives in `data/mapping/gaap_us.json`.

| XBRL Concept | Standard Key | Statement |
|-------------|-------------|-----------|
| `Revenues` | `revenue` | IS |
| `CostOfGoodsAndServicesSold` | `cogs` | IS |
| `OperatingIncomeLoss` | `operating_income` | IS |
| `NetIncomeLoss` | `net_income` | IS / CFS |
| `EarningsPerShareBasic` | `eps_basic` | IS |
| `Assets` | `total_assets` | BS |
| `AssetsCurrent` | `current_assets` | BS |
| `Liabilities` | `total_liabilities` | BS |
| `LiabilitiesCurrent` | `current_liabilities` | BS |
| `StockholdersEquity` | `total_equity` | BS |
| `NetCashProvidedByUsedInOperatingActivities` | `operating_cf` | CFS |
| `NetCashProvidedByUsedInInvestingActivities` | `investing_cf` | CFS |
| `NetCashProvidedByUsedInFinancingActivities` | `financing_cf` | CFS |
| `PaymentsToAcquirePropertyPlantAndEquipment` | `capex` | CFS |
| `DepreciationDepletionAndAmortization` | `depreciation_amortization` | CFS |
| `CashAndCashEquivalentsAtCarryingValue` | `cash_and_equivalents` | BS |
| `AccountsReceivableNetCurrent` | `accounts_receivable` | BS |
| `InventoryNet` | `inventory` | BS |
| `Goodwill` | `goodwill` | BS |
| `LongTermDebtNoncurrent` | `long_term_debt` | BS |

## Appendix B: Formula Reference Card

### Profitability
```
GM  = GP / Rev          GP = Rev - COGS
OM  = OI / Rev          OI = GP - OpEx
NM  = NI / Rev
ROA = NI / TA
ROE = NI / TE
EBITDAM = EBITDA / Rev   EBITDA = OI + D&A
```

### Liquidity
```
CR  = CA / CL
QR  = (CA - Inv) / CL
WC  = CA - CL
OCFR = OCF / CL
```

### Solvency
```
D/E = TL / TE
D/A = TL / TA
IC  = OI / IntExp
LTD/E = LTD / TE
```

### Efficiency
```
AT  = Rev / TA
RT  = Rev / AR
IT  = COGS / Inv
DSO = 365 / RT
```

### Cash Flow Quality
```
FCF = OCF - |CapEx|
FCFM = FCF / Rev
CF/NI = OCF / NI
FCF/NI = FCF / NI
```

### Cross-Statement
```
ΔCash = OCF + ICF + FCF
A = L + E (identity)
ΔAccDep ≈ DepExp (consistency)
IntExp ≈ Debt × Rate (reasonability)
```
