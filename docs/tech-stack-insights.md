# Financial Statement Extraction System — Tech Stack & Architecture Insights

> Extracted from analysis of two reference documents regarding a production financial report information extraction system.
> **Date:** 2026-05-25

---

## A. Architecture & Tech Stack

| # | Insight | Source |
|---|---------|--------|
| 1 | Hybrid approach: PyMuPDF (rule-based) + Pandas + SQL + LLM (Function Call) | Doc1 §1 |
| 2 | Rule-based extraction is fast and accurate for standard tables; LLM handles logic and query | Doc1 §1 |
| 3 | PyMuPDF (fitz) preferred over OCR for text-based PDFs — faster | Doc1 §1 |
| 4 | "Confidence Score" mechanism — low structural integrity triggers OCR fallback per-page (not whole document) | Doc1 §1 |
| 5 | OCR fallback options: PaddleOCR, AWS Textract | Doc1 §1 |
| 6 | Streamlit + Plotly for frontend/charting | Doc1 §1 |
| 7 | PostgreSQL recommended over MySQL for complex JSON/time-series handling | Doc1 §1 |
| 8 | 7-layer system architecture: Ingestion → Extraction → Normalization → Mapping → Storage → Query → Viz → Audit | Doc2 Arch |
| 9 | **Router Agent** classifies each page/table into `clean` / `borderless` / `cross-page` / `scanned` using heuristics + small classifier model | Doc2 §1.1 |
| 10 | Route: clean→PyMuPDF, complex→VLM, scanned→OCR+Layout | Doc2 §1.1 |
| 11 | Additional extraction tools beyond PyMuPDF: Camelot, Tabula-py, pdfplumber, Unstructured, Marker, LayoutParser, Nougat, Donut, Qwen2-VL, Llama-3.2-Vision, Tesseract, DocTR | Doc2 §Tech |
| 12 | Agent frameworks: LangGraph, CrewAI, LlamaIndex, AutoGen | Doc2 §Tech |
| 13 | LLM backends: GPT-4o, Claude-3.5, Qwen-Max, self-hosted vLLM | Doc2 §Tech |
| 14 | Validation libraries: Great Expectations, Pandera, custom accounting rule engine | Doc2 §Tech |
| 15 | Monitoring: LangSmith, Arize Phoenix, Prometheus, GitHub Actions | Doc2 §Tech |

---

## B. Cross-Page & Split-Table Logic

| # | Insight | Source |
|---|---------|--------|
| 16 | Balance sheets often span multiple pages | Doc1 §2A |
| 17 | "Continued" keyword detection on Page 2+ headers | Doc1 §2A |
| 18 | `merge_cross_page_tables(pages)` function needed | Doc1 §2A |
| 19 | Strip repeated headers, append data rows to previous page's DataFrame | Doc1 §2A |
| 20 | "Double Table Cross-Page" scenario: Page 1 ends Table A, Page 2 starts Table B — use vertical gap analysis to split | Doc1 §2A |
| 21 | Income Statement + Cash Flow Statement often on same page, look like one table | Doc1 §2B |
| 22 | "Splitter" logic based on section header keywords | Doc1 §2B |
| 23 | Cash Flow section keywords: "Operating Activities," "Investing Activities," "Financing Activities" | Doc1 §2B |
| 24 | Income section keywords: "Revenue," "Cost of Sales" | Doc1 §2B |
| 25 | Row indentation change or full-width blank row = table separator | Doc1 §2B |
| 26 | Continuation detection via Regex + LLM: "续表", "continued", "(cont'd)", repeated header rows | Doc2 §1.2 |
| 27 | Dual-table split using row-label semantic clustering (e.g., "Current Assets" vs "Non-Current Assets") | Doc2 §1.2 |
| 28 | Header Inheritance: cache last known headers, align columns by width/position + semantic similarity for continuation pages | Doc2 §1.2 |

---

## C. Missing Borders & Visual Ambiguity

| # | Insight | Source |
|---|---------|--------|
| 29 | Some reports use only horizontal lines or no lines at all | Doc1 §2C |
| 30 | **Coordinate Clustering**: group text blocks by Y-coordinate (rows) and X-coordinate (columns) when no lines detected | Doc1 §2C |
| 31 | If coordinate alignment is messy → pass page image to Vision LLM (GPT-4o) | Doc1 §2C |
| 32 | Vision LLM prompt: "Extract this financial table into JSON format, preserving row/column structure" | Doc1 §2C |
| 33 | Context capture: titles, footnotes, accounting policies need multi-modal OCR + LLM chunking | Doc2 §1.1 |

---

## D. Data Normalization & Semantic Mapping

| # | Insight | Source |
|---|---------|--------|
| 34 | Different companies use different names for same line item | Doc1 §3 |
| 35 | Examples: "Net Profit" / "Profit Attributable to Shareholders of the Parent" / "Net Income" — all the same | Doc1 §3 |
| 36 | **Master Schema** with standard keys: `revenue`, `net_profit`, `total_assets`, `operating_cash_flow` | Doc1 §3 |
| 37 | **LLM Mapping Function**: pass extracted row headers to LLM, map to standard schema, mark misses as 'custom_item' | Doc1 §3 |
| 38 | This enables cross-company comparison queries | Doc1 §3 |
| 39 | **Unit detection**: parse "(in thousands)", "(millions)", ¥, $, € from OCR/regex | Both docs |
| 40 | **Unit normalization**: detect unit note at table top, convert all values to base unit (actual currency) before storage | Doc1 §3 |
| 41 | Map to canonical taxonomy (IFRS/GAAP/XBRL) | Doc2 §1.3 |
| 42 | Use **embedding similarity + LLM fallback** for fuzzy matching of line items | Doc2 §1.3 |
| 43 | Example canonical mapping: 總營收 / Revenue / Sales → `revenue` | Doc2 §1.3 |
| 44 | Store **raw + normalized** values side by side | Doc2 Pitfalls |
| 45 | Store raw extracted JSON + normalized DB rows → enables reprocessing without re-OCR | Doc2 Pro Tips |
| 46 | Create golden dataset of 50+ annual reports with ground-truth tables for benchmarking | Doc2 Pro Tips |

---

## E. Database Schema Design

| # | Insight | Source |
|---|---------|--------|
| 47 | Do NOT store one table per year | Doc1 §4 |
| 48 | **Long Format (Tidy Data)** — rows not columns for time | Doc1 §4 |
| 49 | Base schema fields: company_id, fiscal_year, statement_type (enum: balance_sheet/income_stmt/cash_flow), line_item_key, line_item_original_name, value, currency, unit | Doc1 §4 |
| 50 | Advanced schema includes: companies (id, ticker, name, exchange, currency) | Doc2 §2.1 |
| 51 | reports table: id, company_id, fiscal_year, period_end, report_type, audit_opinion | Doc2 §2.1 |
| 52 | statements table: id, report_id, statement_type | Doc2 §2.1 |
| 53 | line_items table: id, statement_id, label, canonical_tag, value, period, unit, **confidence_score** | Doc2 §2.1 |
| 54 | footnotes table: report_id, section, text_embedding (for RAG) | Doc2 §2.1 |
| 55 | restatements table: line_item_id, original_value, adjusted_value, reason (track corrections over time) | Doc2 §2.1 |
| 56 | **Hybrid storage**: Relational DB (structured time-series) + Vector DB (pgvector/Milvus/Weaviate) for footnotes, MD&A, accounting policies, line-item synonyms | Doc2 §2.2 |
| 57 | Redis caching layer for frequent queries (5-year ratios, peer comparisons) | Doc2 §2.2 |

---

## F. Accounting Validation

| # | Insight | Source |
|---|---------|--------|
| 58 | **Validation Agent** runs post-ingestion | Doc2 §2.3 |
| 59 | Balance Sheet check: Assets == Liabilities + Equity (tolerance ±0.1% for rounding) | Doc2 §2.3 |
| 60 | Cash Flow check: Net Cash from Operations + Investing + Financing == ΔCash | Doc2 §2.3 |
| 61 | Income Stmt check: Gross Profit = Revenue − COGS, Net Income = Pre-tax − Tax | Doc2 §2.3 |
| 62 | Flag violations → auto-retry extraction or trigger human audit | Doc2 §2.3 |
| 63 | Hardcode accounting formulas — never let LLM "guess" financial logic | Doc2 §3.2 |
| 64 | LLM should only be used for translation, reasoning, and narrative, not numerical computation | Doc2 §3.2 |

---

## G. Agentic Query & Function Calling

| # | Insight | Source |
|---|---------|--------|
| 65 | 5-agent orchestration: Query Understanding → Schema Mapper → Execution → Insight → Visualization | Doc2 §3.1 |
| 66 | Agent 1: Query Understanding — parse NL → intent + entities + time range, handle synonyms ("bottom line" → net_income) | Doc2 §3.1 |
| 67 | Agent 2: Schema Mapper — map NL terms to DB columns/canonical tags, few-shot prompting + validation loop | Doc2 §3.1 |
| 68 | Agent 3: Execution — generate safe SQL/Python via Function Calling or Text-to-SQL, enforce read-only, use parameterized queries | Doc2 §3.1 |
| 69 | Agent 4: Insight — compute YoY/CAGR, margins, liquidity ratios, cash conversion cycle, generate narrative + chart spec | Doc2 §3.1 |
| 70 | Agent 5: Visualization — render Plotly/Streamlit components, export PDF/Excel with audit trail | Doc2 §3.1 |
| 71 | Function tools for LLM: `get_financial_metric(company, metric, years)` | Doc1 §5 |
| 72 | `calculate_ratio(metric_a, metric_b, company, year)` — perform calculations the LLM shouldn't do directly | Doc1 §5 |
| 73 | `generate_trend_analysis(data_json)` — LLM analyzes retrieved numbers, generates narrative summary | Doc1 §5 |
| 74 | Strict JSON Schema for LLM output: `{ "query": "...", "params": {}, "tool": "text_to_sql" }` | Doc2 §3.2 |
| 75 | **Self-Correction Loop**: SQL fails → retry with schema reflection + error feedback from DB | Doc2 §3.2 |
| 76 | RAG injection: relevant footnotes/accounting policies added to LLM context for qualitative questions | Doc2 §3.2 |
| 77 | Use `pydantic` models for all agent inputs/outputs — enforces structure, reduces hallucination | Doc2 Pro Tips |
| 78 | `dry_run` mode: validate SQL/Python syntax before execution | Doc2 Pro Tips |
| 79 | `explain` endpoint: LLM returns step-by-step reasoning + source page numbers for every insight | Doc2 Pro Tips |
| 80 | **Agent infinite loop guard**: max-retry limits, schema reflection timeout, fallback to human queue | Doc2 Pitfalls |
| 81 | Log all prompts, outputs, tool calls; implement rate limiting + cost tracking per extraction | Doc2 §5.2 |
| 82 | Model governance: version tracking of prompts, extraction methodology changes, pipeline upgrades | Doc2 §5.2 |

---

## H. Precomputed Analytics & Query Patterns

| # | Insight | Source |
|---|---------|--------|
| 83 | Precompute ratios on ingestion for sub-second retrieval: liquidity, profitability, leverage, cash flow | Doc2 §4.1 |
| 84 | Liquidity metrics: Current Ratio, Quick Ratio | Doc2 §4.1 |
| 85 | Profitability metrics: Gross/Operating/Net Margin, ROE, ROA | Doc2 §4.1 |
| 86 | Leverage metrics: Debt/Equity, Interest Coverage | Doc2 §4.1 |
| 87 | Cash Flow metrics: OCF/Sales, FCF Conversion, CapEx/Depreciation | Doc2 §4.1 |
| 88 | Time Series queries: "Plot 5-year OCF trend with recession markers" | Doc2 §4.2 |
| 89 | Cross-Statement queries: "How did working capital changes affect cash flow?" | Doc2 §4.2 |
| 90 | Peer Benchmarking: "Compare net margin vs industry median" | Doc2 §4.2 |
| 91 | Anomaly Detection: "Flag items with >20% YoY volatility without footnote explanation" | Doc2 §4.2 |
| 92 | Confidence score per line item based on: extraction method, validation pass, LLM consensus | Doc2 §5.1 |
| 93 | Dashboard: highlight low-confidence cells, one-click correction → feeds back to fine-tuning dataset | Doc2 §5.1 |

---

## I. Pitfalls & Guardrails

| # | Insight | Source |
|---|---------|--------|
| 94 | **LLM hallucination of financial values** — NEVER trust raw LLM output for numbers; LLM only for schema mapping, reasoning, narrative | Doc2 Pitfalls |
| 95 | Cross-page merging alignment breaks → column-width heuristics + semantic header matching + VLM fallback | Doc2 Pitfalls |
| 96 | Currency/unit mismatch causes ratio errors → detect early, normalize to base unit, store raw+normalized | Doc2 Pitfalls |
| 97 | Footnotes contain critical accounting changes → RAG index them, inject context for qualitative questions | Doc2 Pitfalls |
| 98 | High inference cost for VLM/OCR → Router agent prioritizes cheap methods, cache outputs, batch processing | Doc2 Pitfalls |
| 99 | Keep audit trail: log all transformations, support XBRL/iXBRL where available for regulatory alignment | Doc2 §5.2 |
| 100 | Version restatements — track original_value → adjusted_value → reason | Doc2 §2.1 |
| 101 | Encrypt PII/confidential reports, use row-level security in DB | Doc2 §5.2 |

---

## J. Implementation Roadmap

| # | Insight | Source |
|---|---------|--------|
| 102 | Phase 1 (Wk 1-2): Build PDF router + PyMuPDF extractor for clean tables + accounting equation validator | Doc2 Roadmap |
| 103 | Phase 2 (Wk 3-4): Integrate OCR + LayoutParser for borderless/scanned pages + unit/currency normalization | Doc2 Roadmap |
| 104 | Phase 7 (ongoing): Active learning loop — fine-tune OCR/VLM on corrected samples, expand taxonomy coverage | Doc2 Roadmap |
| 105 | Full 7-week phased rollout from PyMuPDF basics to full multi-agent system | Doc2 Roadmap |

---

## K. Doc1-Unique Insights (Not in Doc2)

| # | Insight |
|---|---------|
| 106 | **Coordinate Clustering** technique for no-border tables (named explicitly, not in Doc2) |
| 107 | **Single-page multi-table implicit merge** (IS + CFS same page) — Doc1 more explicit about detection |
| 108 | Section header keywords for Cash Flow: "Operating Activities," "Investing Activities," "Financing Activities" |
| 109 | Section header keywords for Income: "Revenue," "Cost of Sales" |
| 110 | 5-phase mental model: Extract → Clean → Normalize → Store → Query (simpler than Doc2's 7 layers) |

---

## L. Doc2-Unique Insights (Not in Doc1)

| # | Insight |
|---|---------|
| 111 | Router Agent as formal architectural component with classifier model |
| 112 | Vector DB for semantic search over footnotes, MD&A, policies |
| 113 | Validation Agent with accounting equation checks |
| 114 | Self-Correction Loop for SQL queries |
| 115 | 5-agent orchestration (Query Understanding, Schema Mapper, Execution, Insight, Visualization) |
| 116 | Footnotes table with text_embedding column for RAG |
| 117 | Restatements table for version tracking |
| 118 | Confidence scoring strategy: extraction method × validation pass × LLM consensus |
| 119 | Precomputed OCF/Sales, FCF Conversion, CapEx/Depreciation |
| 120 | Anomaly detection: >20% YoY volatility without footnote explanation |
| 121 | `dry_run` mode + `explain` endpoint + `pydantic` models |
| 122 | Human-in-the-loop audit interface for low-confidence corrections |
| 123 | Model governance: log prompts/outputs/tool calls + cost tracking per extraction |
| 124 | Security: encrypt PII, row-level DB security, XBRL/iXBRL support |
| 125 | Caching layer (Redis) for frequent queries |

---

## Synthesis: Key Architectural Decisions

### What both documents agree on
1. **PyMuPDF first, OCR second** — never pay OCR cost for clean text PDFs
2. **LLM for mapping/narrative, NOT for numbers** — hardcoded accounting validation
3. **Long-format DB schema** — not one table per year
4. **Unit normalization before storage** — detect and convert (in thousands/millions)
5. **Cross-statement validation** — Assets = Liabilities + Equity, ΔCash reconciliation
6. **Semantic line-item mapping** — standardize company-specific labels

### Where Doc2 extends Doc1
- Adds multi-agent orchestration (LangGraph/CrewAI)
- Adds Vector DB + RAG for footnotes and qualitative context
- Adds confidence scoring and human-in-the-loop audit
- Adds precomputed metrics layer for sub-second retrieval
- Adds model governance, security, and monitoring

### Where Doc1 is stronger
- More specific table-splitting heuristics (coordinate clustering, section keywords)
- Explicit IS+CFS same-page merge detection
- Simpler 5-phase mental model easier to implement incrementally

### Recommended synthesis for this project
1. **Start with Doc1's pipeline** — PyMuPDF + coordinate clustering + section-header splitting
2. **Adopt Doc2's Router Agent** — classify pages before choosing extraction method
3. **Adopt Doc2's validation** — accounting equation checks post-extraction
4. **Adopt Doc2's schema** — companies/reports/statements/line_items with confidence_score
5. **Defer** Vector DB and full 5-agent orchestration until core extraction is reliable
6. **Implement** the 125 insights as a checklist during architecture design
