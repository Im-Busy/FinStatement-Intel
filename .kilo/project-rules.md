# Project Rules: reading-CFS-IS-BS

## Financial Statement Analysis Guardrails

### Data Integrity
- NEVER confuse cumulative vs. period-specific figures. Cash flow and income statement items are typically period-specific; balance sheet items are point-in-time.
- ALWAYS verify the accounting equation: Assets = Liabilities + Shareholders' Equity. If it doesn't balance, flag the discrepancy.
- Handle fiscal year variations — not all companies use calendar year reporting.
- Validate currency units (thousands, millions, billions) and normalize before comparison.
- For cross-company analysis: confirm consistent accounting standards (GAAP vs. IFRS).

### Statement-Specific Rules

#### Cash Flow Statement (CFS)
- Verify that net change in cash = operating + investing + financing cash flows.
- Operating cash flow should reconcile with net income via non-cash adjustments.
- Free Cash Flow (FCF) = Operating CF − Capital Expenditures.
- Watch for one-time items inflating operating cash flow (e.g., legal settlements, asset sales).
- Quality check: sustained negative operating CF is a red flag regardless of net income.

#### Income Statement (IS)
- Distinguish between GAAP and non-GAAP (adjusted) earnings.
- Revenue recognition timing can distort period comparisons — note any policy changes.
- EBIT vs. EBITDA: understand what's excluded (depreciation, amortization).
- Watch for "other income/expense" line items that may be recurring despite labeling.
- Gross margin trends are leading indicators of competitive position.

#### Balance Sheet (BS)
- Current Ratio = Current Assets / Current Liabilities. Below 1.0 is a liquidity red flag.
- Debt-to-Equity = Total Liabilities / Shareholders' Equity. Industry-specific thresholds apply.
- Goodwill impairment can signal overpayment for acquisitions.
- Off-balance-sheet items (operating leases, contingent liabilities) require footnote review.
- Working capital = Current Assets − Current Liabilities. Negative trend signals cash strain.

### Cross-Statement Analysis
- Cash flow from operations should generally exceed net income over long periods (quality of earnings check).
- Revenue growth vs. receivables growth: if receivables grow faster, earnings quality may be declining.
- Inventory buildup without corresponding revenue growth signals demand problems.
- Depreciation on BS vs. IS: accumulated depreciation should increase roughly by depreciation expense.
- Interest expense on IS should reconcile with debt levels on BS and prevailing interest rates.

## Pipeline Architecture — 4-Agent Convention

Inspired by pdf-to-markdown-batch-6tools, this project uses a pipeline agent pattern:

| Agent | File | Purpose |
|-------|------|---------|
| **extractor** | `.kilo/agent/extractor.md` | Extracts financial data from source (PDF, HTML, EDGAR, API) |
| **parser** | `.kilo/agent/parser.md` | Parses raw data into structured financial statements |
| **analyzer** | `.kilo/agent/analyzer.md` | Computes ratios, trends, quality checks, anomalies |
| **reporter** | `.kilo/agent/reporter.md` | Generates analysis report with findings, red flags, recommendations |

### Agent Output Format
- Each agent produces JSON to stdout (consumed by next agent).
- All agent output includes `status` field: `SUCCESS | ERROR | WARNING`.
- Agent failures are scoped — one failure doesn't kill the entire pipeline.

## Data Source Escalation Pattern

When extracting financial data, escalate progressively:
1. **L1: Direct API** — SEC EDGAR XBRL, company IR API, financial data providers
2. **L2: Structured Web** — HTML tables from SEC filings, financial websites
3. **L3: Document Parsing** — PDF annual reports, 10-K, 10-Q (use pdf-to-markdown tooling)
4. **L4: OCR** — Scanned documents (last resort, highest error rate)

Never jump to L4 first — it wastes resources and introduces OCR errors.

## Financial Analysis Anti-Rationalization Guardrails

The following excuses are INVALID:

| Rationalization | Reality |
|----------------|---------|
| "The trend is clear despite messy data" | Garbage in, garbage out. Validate data quality first. |
| "This ratio is close enough" | Financial ratios have specific definitions. 0.1 difference in debt/equity can change the story entirely. |
| "I'll just use net income as a proxy for cash flow" | Accrual accounting can mask severe cash problems. Always analyze cash flow separately. |
| "One year of data is enough to see the trend" | Minimum 3-5 years for meaningful trend analysis. Single-year snapshots are misleading. |
| "The company is profitable so it's healthy" | Profit ≠ cash. Enron was "profitable" until it wasn't. |
| "I can skip the footnotes" | Footnotes contain material information — off-balance-sheet items, accounting policy changes, contingencies. |
| "Industry averages are good enough for comparison" | Peer group selection is critical. Averages can be skewed by outliers. |
| "The audit opinion is clean" | A clean audit opinion means GAAP compliance, not business quality. |
