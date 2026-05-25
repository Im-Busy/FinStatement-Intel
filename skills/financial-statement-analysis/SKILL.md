# Financial Statement Analysis Skill

## When to Use This Skill
Use this skill when the user wants to:
- Analyze a company's Cash Flow Statement (CFS), Income Statement (IS), and/or Balance Sheet (BS)
- Compute financial ratios and assess financial health
- Detect financial red flags and quality issues
- Perform cross-statement validation and trend analysis
- Generate a comprehensive financial analysis report

Triggers:
- "Analyze [company] financial statements"
- "How healthy is [company] financially?"
- "Check [company] cash flow quality"
- "Run financial ratios on [company]"
- Any mention of CFS, IS, BS, financial statement analysis

## Core Philosophy

Financial statement analysis requires **cross-statement validation**. Never analyze a single statement in isolation. The three statements form a closed system — changes in one must have consequential effects on the others.

### The Three Statements
1. **Income Statement (IS)** — Revenue, expenses, profit over a period. Accrual-based.
2. **Balance Sheet (BS)** — Assets, liabilities, equity at a point in time. Snapshot.
3. **Cash Flow Statement (CFS)** — Cash inflows/outflows over a period. The "truth" statement.

### The Accounting Identity
```
Assets = Liabilities + Shareholders' Equity
```
Every analysis must verify this identity holds. If it doesn't, flag the discrepancy — it indicates data quality issues.

## Analysis Workflow

### Phase 1: Data Acquisition
1. Identify company (ticker, fiscal year end)
2. Source financial statements (EDGAR XBRL preferred, then HTML, PDF)
3. Extract raw line items preserving original labels
4. Record metadata: period type, currency, unit scale, fiscal year end

### Phase 2: Data Parsing & Normalization
1. Map company-specific labels to standardized names
2. Convert all values to consistent unit (millions default)
3. Verify structural integrity:
   - Balance sheet balances (A = L + E)
   - Cash flow reconciles (ΔCash = Operating + Investing + Financing)
   - Subtotal arithmetic checks
4. Flag unmapped line items and discrepancies

### Phase 3: Ratio Computation
Compute ratios across 5 categories:

#### Profitability
| Ratio | Formula | What It Tells You |
|-------|---------|-------------------|
| Gross Margin | Gross Profit / Revenue | Pricing power, production efficiency |
| Operating Margin | Operating Income / Revenue | Core business profitability |
| Net Margin | Net Income / Revenue | Bottom-line efficiency |
| ROA | Net Income / Total Assets | Asset utilization efficiency |
| ROE | Net Income / Total Equity | Return to shareholders |
| EBITDA Margin | EBITDA / Revenue | Cash-generating ability |

#### Liquidity
| Ratio | Formula | What It Tells You |
|-------|---------|-------------------|
| Current Ratio | Current Assets / Current Liabilities | Short-term bill-paying ability |
| Quick Ratio | (CA - Inventory) / CL | Liquidity without inventory |
| Operating CF Ratio | Operating CF / Current Liabilities | Cash coverage of short-term obligations |

#### Solvency
| Ratio | Formula | What It Tells You |
|-------|---------|-------------------|
| Debt-to-Equity | Total Liabilities / Total Equity | Financial leverage |
| Debt-to-Assets | Total Liabilities / Total Assets | Asset financing mix |
| Interest Coverage | Operating Income / Interest Expense | Ability to service debt |

#### Efficiency
| Ratio | Formula | What It Tells You |
|-------|---------|-------------------|
| Asset Turnover | Revenue / Total Assets | Revenue per dollar of assets |
| Receivables Turnover | Revenue / A/R | Collection efficiency |
| Inventory Turnover | COGS / Inventory | Inventory management |
| Days Sales Outstanding | 365 / Receivables Turnover | Average collection period |

#### Cash Flow Quality
| Ratio | Formula | What It Tells You |
|-------|---------|-------------------|
| Free Cash Flow | Operating CF - Capex | Discretionary cash |
| FCF Margin | FCF / Revenue | Cash conversion efficiency |
| CF-to-NI | Operating CF / Net Income | Earnings quality (>1.0 preferred) |
| FCF-to-NI | FCF / Net Income | Sustainable earnings power |

### Phase 4: Trend Analysis
- Compute YoY growth rates for: revenue, net income, operating CF, FCF
- Calculate 3-year and 5-year CAGR where data allows
- Evaluate margin trend direction: improving, stable, declining
- Identify acceleration/deceleration patterns

### Phase 5: Red Flag Detection
Check for these patterns (each is a concern, multiple together is alarming):

| Red Flag | Threshold | What It Means |
|----------|-----------|---------------|
| CF-to-NI < 0.5 | Operating CF less than half of net income | Earnings quality problem |
| Current Ratio < 1.0 | Current liabilities exceed current assets | Liquidity crisis risk |
| D/E > industry threshold | Leverage exceeds industry norms | Financial distress risk |
| Negative Operating CF (3+ years) | Sustained cash burn | Business model problem |
| Receivables growth > Revenue growth | Customers paying slower | Aggressive revenue recognition |
| Inventory growth > Revenue growth | Products not selling | Demand problem |
| Goodwill > 50% of equity | Over-reliance on acquisitions | Impairment risk |
| Interest Coverage < 1.5 | Barely covering interest payments | Debt service risk |
| Sustained margin decline (3+ years) | Competitive erosion | Structural problem |

### Phase 6: Cross-Statement Validation
1. **Earnings Quality**: Operating CF should generally exceed Net Income over long periods
2. **Revenue Quality**: Receivables growth should not exceed revenue growth
3. **Demand Health**: Inventory growth should not exceed revenue growth
4. **Depreciation Consistency**: ΔAccumulated Depreciation should approximate Depreciation Expense
5. **Interest Consistency**: Interest Expense should reconcile with debt levels and market rates

### Phase 7: Report Generation
Produce a structured report with:
1. Executive Summary (top 3 findings + overall assessment)
2. Financial Health Scorecard (0-100 across 5 dimensions)
3. Detailed statement analysis (IS, BS, CFS)
4. Ratio analysis with trend
5. Red flags ranked by materiality
6. Strengths and competitive advantages
7. Recommendations and watch items

## Scoring Methodology

### Financial Health Scorecard (0-100)
Each dimension scored 0-20:

**Profitability (20 pts)**
- Gross margin trend: 0-5
- Operating margin trend: 0-5
- Net margin vs. industry: 0-5
- ROE level and trend: 0-5

**Liquidity (20 pts)**
- Current ratio level: 0-7
- Quick ratio level: 0-5
- Operating CF ratio: 0-4
- Working capital trend: 0-4

**Solvency (20 pts)**
- D/E vs. industry: 0-8
- Interest coverage: 0-8
- Debt maturity profile: 0-4 (from footnotes)

**Efficiency (20 pts)**
- Asset turnover trend: 0-6
- DSO trend: 0-5
- Inventory turnover: 0-5
- Operating cycle trend: 0-4

**Cash Flow Quality (20 pts)**
- CF/NI ratio: 0-6
- FCF margin trend: 0-6
- FCF sustainability: 0-4
- Capex/revenue trend: 0-4

### Overall Assessment
- 80-100: **Strong** — Healthy across dimensions, well-managed
- 60-79: **Adequate** — Generally sound, monitor specific areas
- 40-59: **Concerning** — Multiple yellow flags, increased risk
- 0-39: **Critical** — Severe issues requiring immediate attention

## Guardrails — Anti-Rationalization

NEVER accept these excuses:

| Excuse | Reality |
|--------|---------|
| "The trend is clear despite messy data" | Validate data quality first. Garbage in, garbage out. |
| "One year is enough" | Minimum 3-5 years for meaningful trend analysis. |
| "The company is profitable so it's healthy" | Profit ≠ cash. Enron was "profitable." |
| "I can skip the footnotes" | Footnotes contain material information. |
| "Net income proxies for cash flow" | Accrual accounting can mask severe cash problems. |
| "Industry averages are good enough" | Peer group selection is critical; averages hide outliers. |
| "The audit opinion is clean" | Clean audit = GAAP compliance, not business quality. |

## Data Source Escalation

When extracting financial data, escalate progressively:
1. **L1: SEC EDGAR XBRL API** — Machine-readable, structured, most reliable
2. **L2: HTML tables** from SEC filings or financial websites
3. **L3: PDF parsing** — Annual reports, 10-K, 10-Q
4. **L4: OCR** — Scanned documents only (highest error rate)

Never jump to L4 first.

## Statement-Specific Rules

### Cash Flow Statement
- Verify: ΔCash = Operating CF + Investing CF + Financing CF
- FCF = Operating CF - Capex
- Watch for one-time items inflating operating CF
- Sustained negative operating CF is a critical red flag

### Income Statement
- Distinguish GAAP vs. non-GAAP earnings
- Revenue recognition timing changes require scrutiny
- EBIT vs. EBITDA: understand what's excluded
- Gross margin trends are leading indicators of competitive position

### Balance Sheet
- Verify A = L + E identity
- Current Ratio < 1.0 triggers liquidity concern
- Goodwill impairment signals overpayment on acquisitions
- Off-balance-sheet items require footnote review

### Key Patterns
- Assets = Current Assets + Non-Current Assets
- Total Assets = Total Current Assets + LT Assets
- Operating Income = Gross Profit - Operating Expenses

## Output
Provide a comprehensive financial analysis with the Financial Health Scorecard, ratio breakdowns by category, red flags ranked by severity, trend analysis across periods, and actionable recommendations.
