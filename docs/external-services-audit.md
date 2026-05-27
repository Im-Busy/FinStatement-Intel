# External Services Audit — Financial Statement Extraction

Date: 2026-05-27

---

## 1. Financial Statement-Specific Extractors (CFS/IS/BS)

### willamhou/fin-doc-parser
- **URL**: https://github.com/willamhou/fin-doc-parser
- **Stars**: 18 | **Updated**: March 2026 | **License**: MIT
- **Input formats**: PDF, **image (PNG/JPG)**, Excel
- **Output**: Structured JSON with `balance_sheet`, `income_statement`, `cash_flow`
- **Doc types**: 11 types including `financial_statement`, bank_statement, audit_report, financial_notes, MD&A
- **OCR**: Pluggable — PaddleOCR (local, free), Prismer (GPU service), or text-only
- **LLM**: Pluggable — DeepSeek, OpenAI, or any OpenAI-compatible API (Ollama, vLLM)
- **Auto-detection**: `detect_file_type()` for format auto-detection
- **Key code**:
  ```python
  result = parse("screenshot.png", doc_type="financial_statement")
  bs = result["data"]["balance_sheet"]
  bs["total_assets"]  # direct key access
  ```
- **Note**: Chinese-origin but works with English documents. Local PaddleOCR means no external service required for OCR.

### cartographer-filings
- **URL**: https://pypi.org/project/cartographer-filings/ | https://github.com/Horsmann/sharepoint-to-text
- **Input**: PDF annual reports, quarterly filings, regulatory docs
- **Output**: Structured markdown + **classified sections** — Income Statement, Balance Sheet, Cash Flow, MD&A, Risk Factors, numbered Notes
- **Key modules**:
  - `enhance` — reconstructs tables from space-stacked cells, normalizes negative numbers `(1,234)` → `-1,234`, strips repeated page headers/footers, promotes bold runs to headings
  - `parser` — classifies sections (IS, BS, CF, MD&A, Risk, Audit), detects numbered notes, extracts metadata across 9 languages
  - `vision` — opt-in image-heavy page processing via Qwen-VL (SiliconFlow API)
- **Jurisdictions**: 10+ — SEC 10-Ks, ESEF annual reports, HKEX filings
- **Output schema**:
  ```json
  {
    "markdown": "...",
    "metadata": {"company": "...", "currency": "...", "fiscal_year": 2024, "standard": "US-GAAP"},
    "sections": {
      "income_statement": "...",
      "balance_sheet": "...",
      "cash_flow": "...",
      "mda": "...",
      "risk": "...",
      "audit": "..."
    },
    "notes": [{"note_number": 1, "title": "...", "content": "...", "v5_type": "..."}],
    "stats": {"pages": 120, "sections_found": 6, "notes_count": 22}
  }
  ```

### lazyaccountant/FinTable
- **URL**: https://github.com/lazyaccountant/FinTable
- **Input**: PDF annual reports
- **Output**: CSV files for SOFP (Balance Sheet), SOPL (Income Statement), SOCF (Cash Flow)
- **Method**: Regex patterns + keyword matching (customizable keyword lists per company type)
- **API**: Python class `AnnualReport(path).report("SOFP")` + CustomTkinter GUI
- **Limitation**: PDF only, no image/scan support, accuracy depends on PDF structure quality

### EstevanFisk/LLM_Spreads_Financial_Data_Extraction
- **URL**: https://github.com/EstevanFisk/LLM_Spreads_Financial_Data_Extraction
- **Input**: PDF (10-K, 10-Q, Earnings reports)
- **Output**: Structured institutional-grade JSON
- **Pipeline**: Docling (layout-aware parsing) → Gemini 2.5 Flash → multi-agent verification
- **Agents**: Security Agent (injection/PII detection) → Financial Agent (extraction) → Verification Agent (senior editor review)
- **Deployment**: Streamlit UI + Modal serverless
- **Limitation**: Requires Gemini API key, PDF only, no image input

### marutijhawar/Financial-Pipeline
- **URL**: https://github.com/marutijhawar/Financial-Pipeline-
- **Input**: CSV, Excel, PDF
- **Output**: `list[pd.DataFrame]` with metadata (source_file, sheet_name, is_pdf_derived flag)
- **KPIs**: Burn rate, runway, CAC, LTV (startup-focused)
- **Note**: PDF output flagged as semi-structured requiring manual verification

---

## 2. General-Purpose Document Parsers (DOCX Support)

### mdextract / satadeep3927/docparser
- **URL**: https://github.com/satadeep3927/docparser | PyPI: `mdextract`
- **Input**: PDF, **DOCX**, XLSX, CSV
- **Output**: Clean Markdown string (heading-preserving, GFM tables)
- **Strength**: Zero-config, returns a string, auto-detects from extension
- **DOCX handling**: Preserves Word heading styles (Heading 1-6, Title), list items, merged table cells
- **PDF**: Detects tables and headings by font size, Tesseract OCR for scanned pages
- **Code**:
  ```python
  import mdextract
  text = mdextract.parse_file("report.docx")  # → Markdown string
  ```

### ispras/dedoc
- **URL**: https://github.com/ispras/dedoc
- **Stars**: 680+ | **License**: Apache 2.0
- **Input**: DOC/DOCX, ODT, XLS/XLSX, CSV, TXT, JSON, **images (PNG/JPG)**, ZIP/RAR, PDF, HTML
- **Output**: Unified tree structure (headings, lists, tables, text formatting, metadata)
- **Table extraction**: Contour analysis for complex multi-page tables with explicit borders from DOCX, PDF, HTML, CSV, and images
- **DOCX**: Uses python-docx + BeautifulSoup for inner XML analysis
- **Images**: OCR via Tesseract
- **Maturity**: Most established general-purpose option, ISPRAS-backed research project

### NanoNets/docstrange
- **URL**: https://github.com/NanoNets/docstrange
- **Input**: PDF, **DOCX**, PPTX, XLSX, images, URL
- **Output**: Markdown, JSON (schema-driven), HTML, CSV
- **Key feature**: Structured extraction with JSON schema — provide a schema, get typed output
- **OCR**: Built-in advanced OCR
- **Note**: General-purpose, no financial-statement-specific models

### officemd (ThomAub)
- **URL**: https://github.com/ThomAub/officemd | PyPI: `officemd`
- **Input**: **DOCX**, XLSX, CSV, PPTX, PDF
- **Output**: Markdown, JSON IR, Docling-compatible JSON
- **Note**: Rust core with Python bindings, fast. No OCR.

---

## 3. Multimodal LLM Providers (Vision/OCR via API)

Rather than wrap a third-party library like `fin-doc-parser`, users can bring their own API key. Multimodal models with strong vision capabilities read financial tables directly from images/screenshots.

| Provider | Models | API Path | Cost | Notes |
|----------|--------|----------|------|-------|
| **OpenRouter** | GPT-4o, Claude 3.5 Sonnet, Gemini 2.5 Flash, Qwen-VL-Max | `https://openrouter.ai/api/v1` (OpenAI-compat) | Pay-per-token | One API key → access to all models. Best flexibility. |
| **OpenAI** | GPT-4o, GPT-4o-mini | `https://api.openai.com/v1` | Pay-per-token | Strong vision, well-structured JSON output |
| **Anthropic** | Claude 3.5 Sonnet, Claude 3 Opus | `https://api.anthropic.com` | Pay-per-token | Excellent at table understanding, long context |
| **Google** | Gemini 2.5 Flash, Gemini 1.5 Pro | Gemini SDK | Pay-per-token / free tier | Very fast, good table extraction |
| **Ollama (local)** | LLaVA, BakLLaVA, Minicpm-v | `http://localhost:11434/v1` (OpenAI-compat) | Free | Fully local, no API key, quality depends on model |

All accessible through the same `VisionBackend` config — user just sets `base_url` and `api_key`.

### Why not `fin-doc-parser` or other wrappers?

- Users already have API keys (OpenRouter, OpenAI) — no need to add another abstraction
- Direct API calls give full control over model selection and cost
- Our prompt is specifically tailored to CFS/IS/BS extraction
- Avoids dependency on an external SDK that may change

---

## 4. Summary Matrix

| Service | PDF | Image | DOCX | CFS/IS/BS Output | OCR (local) | Notes |
|---------|:---:|:-----:|:----:|:----------------:|:-----------:|-------|
| **fin-doc-parser** | ✔️ | ✔️ | ❌ | ✔️ structured JSON | PaddleOCR | Best existing image→financial library |
| **cartographer-filings** | ✔️ | ❌ | ❌ | ✔️ classified sections | Qwen-VL (cloud) | Best section classifier |
| **FinTable** | ✔️ | ❌ | ❌ | ✔️ CSV | ❌ | SOFP/SOPL/SOCF specific |
| **LLM_Spreads** | ✔️ | ❌ | ❌ | ✔️ JSON | ❌ | Requires Gemini API |
| **mdextract** | ✔️ | ❌ | ✔️ | ❌ general markdown | Tesseract | Best DOCX→Markdown |
| **dedoc** | ✔️ | ✔️ | ✔️ | ❌ generic tree | Tesseract | Most mature multi-format |
| **docstrange** | ✔️ | ✔️ | ✔️ | ❌ schema JSON | Built-in | Schema-driven extraction |
| **Multimodal LLM (BYO key)** | ✔️* | ✔️ | ❌ | ✔️ structured JSON | ❌ (cloud) | User's own API key → GPT-4o / Claude / Gemini |

---

## 4. Current Project Capability Gap

| Input Format | Currently Supported? | Gap |
|-------------|:-------------------:|-----|
| Ticker → EDGAR API | ✔️ L1 | None |
| Ticker → EDGAR XBRL | ✔️ L1.5 | None |
| Ticker → EDGAR HTML | ✔️ L2 | None |
| Ticker → EDGAR PDF | ✔️ L3 (PyMuPDF + camelot) | None |
| Ticker → EDGAR scanned PDF | ✔️ L4 (tesseract/PaddleOCR) | None |
| **Local PDF file** | ❌ | No direct `extract_from_local_file(path)` |
| **Image file (JPG/PNG)** | ❌ | No image extraction path exists |
| **Image screenshot (Excel screenshot)** | ❌ | Same as above |
| **Scanned PDF (local file)** | ❌ | L4 pipeline exists but only EDGAR-triggered |
| **DOCX / Word file** | ❌ | No DOCX extractor exists |
| **XLSX / Excel file** | ❌ | No Excel extractor exists |
