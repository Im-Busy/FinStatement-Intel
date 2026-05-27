# Blueprint: Multi-Format Financial Statement Extraction & Analysis

Date: 2026-05-27

---

## 1. Vision

A single entry point that accepts **any input format** (ticker symbol, PDF, image, DOCX, XLSX, URL) and produces a **complete financial analysis** through the existing 4-agent pipeline (extractor → parser → analyzer → reporter).

```
Input (any format) → File Router → Format Extractor → Structured JSON → Parser → Analyzer → Reporter → Output
```

---

## 2. Input Formats — Desired

| Format | Examples | Priority |
|--------|----------|----------|
| **Ticker symbol** | `AAPL`, `MSFT` | ✅ Exists (EDGAR L1-L4) |
| **Text PDF (local)** | 10-K download, annual report | 🔴 Missing |
| **Scanned PDF (local)** | Photocopied annual reports | 🔴 Missing (OCR pipe exists but not file-triggered) |
| **Image file** | JPG/PNG screenshot of Excel financials | 🔴 Missing |
| **DOCX / Word** | Financial statements in Word format | 🔴 Missing |
| **XLSX / Excel** | Financial model exports | 🔴 Missing |
| **URL (SEC filing)** | Direct link to 10-K HTML/PDF | 🔴 Missing |

---

## 3. Architecture

### 3.1 New Entry Point: `extract_from_file()`

A universal file extraction function that auto-detects format and routes to the correct handler.

```python
def extract_from_file(
    path: str | Path,
    ticker: str | None = None,
    periods: int = 5,
) -> dict[str, Any]:
    """
    Extract financial data from any supported file format.

    Auto-detects:
    - File type (PDF, image, DOCX, XLSX, plain text)
    - Whether PDF is text-based or scanned
    - Statement types present (CFS, IS, BS)
    - Currency and unit scale

    Returns standard extraction JSON with status, periods, warnings.
    """
```

### 3.2 New Module: `src/extraction/file_router.py`

```
file_router.py
  ├── detect_file_type(path) → FileType enum (PDF_SCANNED, PDF_TEXT, IMAGE, DOCX, XLSX, CSV, UNKNOWN)
  ├── extract_from_file(path, ...) → standard extraction JSON
  └── _route_to_extractor(file_type, path, ...) → calls appropriate extractor
```

### 3.3 Vision Backend System (OCR + Multimodal LLM)

Users can choose between **local OCR** (free, offline) and **cloud multimodal LLMs** (higher accuracy, needs API key).

```
┌─────────────────────────────────────────────────────┐
│                  VisionBackend                       │
│                                                      │
│  ┌──────────┐  ┌─────────────────┐  ┌────────────┐  │
│  │  LOCAL   │  │ OPENAI_COMPATIBLE│  │  ANTHROPIC │  │
│  │          │  │                 │  │            │  │
│  │PaddleOCR │  │ OpenAI          │  │ Claude 3.5 │  │
│  │Tesseract │  │ OpenRouter      │  │ Sonnet     │  │
│  │(no key)  │  │ Ollama (vision) │  │            │  │
│  │          │  │ vLLM            │  │            │  │
│  │          │  │ DeepSeek        │  │            │  │
│  └──────────┘  └─────────────────┘  └────────────┘  │
│                                                      │
│  Config via env vars or --vision-backend CLI flag:   │
│    VISION_BACKEND=openai_compatible                   │
│    VISION_API_KEY=sk-...                              │
│    VISION_BASE_URL=https://openrouter.ai/api/v1       │
│    VISION_MODEL=openai/gpt-4o                         │
└─────────────────────────────────────────────────────┘
```

**Backend selection priority:**
1. CLI flag `--vision-backend local|openai|anthropic`
2. Env var `VISION_BACKEND`
3. Default: `local` (no API key needed)

**For cloud backends, the multimodal LLM receives:**
- Base64-encoded image/page
- A prompt: *"You are a financial statement extraction system. Extract all line items with their values from this image. Identify whether it's an Income Statement, Balance Sheet, or Cash Flow Statement. Detect the period, currency, and unit scale. Return JSON."*
- A response schema matching the standard extraction JSON

### 3.4 New Modules

| Module | New/Refactor | Purpose |
|--------|:-----------:|---------|
| `vision_backend.py` | New | `VisionBackend` enum, API config loading, backend selection |
| `vision_llm_extractor.py` | New | Sends base64 images to multimodal LLMs, parses structured JSON response |
| `image_extractor.py` | New | Extracts images: delegates to either local OCR or vision LLM based on config |
| `docx_extractor.py` | New | python-docx → table extraction → line items |
| `xlsx_extractor.py` | New | openpyxl → sheet scanning → line items |
| `file_router.py` | New | File type detection + routing to correct extractor |
| `ocr_extractor.py` | Refactor | Accept direct file path, support vision LLM fallback |
| `extractor.py` | Refactor | Add `extract_from_file()` as public API |
| `config.py` | New/Update | Vision backend config, API key loading from env |

### 3.5 Vision LLM Extraction Flow

```
Image file (JPG/PNG)
       │
       ▼
┌──────────────────┐
│  file_router.py  │  detect_file_type() → IMAGE
└──────────────────┘
       │
       ▼
┌──────────────────────┐
│ image_extractor.py   │
│                      │
│  if backend == LOCAL:│
│    → PaddleOCR       │
│    → tesseract       │
│    → _extract_line_  │
│      items_from_text │
│                      │
│  if backend == CLOUD:│
│    → encode to b64   │
│    → send to LLM     │
│    → parse JSON      │
│    → convert to      │
│      standard format │
└──────────────────────┘
       │
       ▼
  Standard extraction JSON
  (feeds into parser → analyzer → reporter)
```

**Prompt template for multimodal LLMs:**

```
You are a financial statement data extraction system. Analyze this image and extract ALL line items with their financial values.

1. Identify statement type: Income Statement, Balance Sheet, or Cash Flow Statement
2. Identify the reporting period (e.g., "FY2024", "Q3 2024")
3. Detect the unit scale (actual, thousands, millions, billions)
4. Extract every visible line item and its numerical value
5. Flag any ambiguous or unclear items

Return ONLY valid JSON in this exact schema:
{
  "statement_type": "IS|BS|CFS",
  "period": "FY2024",
  "unit": "millions",
  "currency": "USD",
  "line_items": [
    {"label": "Revenue", "value": 383285.0, "needs_review": false},
    ...
  ]
}
```

### 3.6 Config Loading

```python
# src/config.py or similar
import os
from dataclasses import dataclass, field
from enum import Enum

class VisionBackend(Enum):
    LOCAL = "local"
    OPENAI_COMPATIBLE = "openai_compatible"
    ANTHROPIC = "anthropic"

@dataclass
class VisionConfig:
    backend: VisionBackend = VisionBackend.LOCAL
    api_key: str = ""
    base_url: str = "https://api.openai.com/v1"
    model: str = "gpt-4o"
    max_tokens: int = 4096
    temperature: float = 0.0

    @classmethod
    def from_env(cls) -> "VisionConfig":
        backend_str = os.getenv("VISION_BACKEND", "local")
        return cls(
            backend=VisionBackend(backend_str),
            api_key=os.getenv("VISION_API_KEY", os.getenv("OPENAI_API_KEY", "")),
            base_url=os.getenv("VISION_BASE_URL", os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")),
            model=os.getenv("VISION_MODEL", "gpt-4o"),
            max_tokens=int(os.getenv("VISION_MAX_TOKENS", "4096")),
            temperature=float(os.getenv("VISION_TEMPERATURE", "0.0")),
        )
```

Key design decisions:
- `OPENAI_API_KEY` env var works as fallback (most users will already have this set)
- OpenRouter uses the same OpenAI-compatible endpoint with a different `base_url`
- Anthropic uses a separate API path with its own SDK (or raw HTTP)
- Default is `local` so the tool works out of the box without any API key

### 3.5 Unified Output Contract

All extractors produce the same JSON structure (already defined in `.kilo/agent/extractor.md`):

```json
{
  "status": "SUCCESS",
  "company": {"name": "", "ticker": "", "fiscal_year_end": ""},
  "periods": [{
    "type": "annual",
    "end_date": "YYYY-MM-DD",
    "statements": {
      "CFS": {"source": "", "unit": "", "line_items": [{"label": "", "value": 0.0}]},
      "IS":  {"source": "", "unit": "", "line_items": []},
      "BS":  {"source": "", "unit": "", "line_items": []}
    }
  }]
}
```

---

## 4. Desired Functionality Checklist

### 4.1 File Input
- [ ] Accept local file path or `Path` object
- [ ] Accept a file-like object (bytes/BytesIO) for API usage
- [ ] Accept a URL pointing to a filing document
- [ ] Accept a ticker symbol (existing — no change)

### 4.2 File Type Detection
- [ ] Detect by extension (`.pdf`, `.png`, `.jpg`, `.docx`, `.xlsx`, `.csv`)
- [ ] Detect by magic bytes (fallback for misnamed files)
- [ ] Detect PDF type: text-based vs scanned (text yield check, existing in OCR)
- [ ] Detect image type: photo of printed document vs screenshot of screen

### 4.3 Multi-Format Extraction
- [ ] Text PDF → coordinate-clustered text extraction + camelot tables (L3, exists)
- [ ] Scanned PDF → per-page OCR → line items (L4, exists but only EDGAR-triggered)
- [ ] Image file → OCR → line items (NEW)
- [ ] DOCX file → table and paragraph extraction → line items (NEW)
- [ ] XLSX file → sheet analysis → line items (NEW)
- [ ] All paths converge to standard extraction JSON

### 4.4 Quality Checks (Per Extractor)
- [ ] Word count / text yield threshold for OCR fallback (< 20 words → OCR)
- [ ] Confidence scoring per extracted value
- [ ] Flag ambiguous line items with `needs_review: true`
- [ ] Record source page/row references for audit trail

### 4.5 Error Handling & Fallback
- [ ] If PyMuPDF fails → try pdfplumber
- [ ] If tesseract not installed → try PaddleOCR
- [ ] If OCR fails entirely → return `WARNING` with partial data
- [ ] Graceful degradation: partial extraction better than none

### 4.6 Integration with Existing Pipeline
- [ ] `extract_from_file()` output feeds directly into parser (JSON stdin pattern)
- [ ] `main.py` updated to accept `--file <path>` flag
- [ ] `/extract` slash command updated to accept file paths
- [ ] All 4 agents (extractor, parser, analyzer, reporter) work unchanged

---

## 5. Non-Goals (Out of Scope)

- Real-time camera capture of financial documents
- Handwriting recognition for hand-annotated financials
- Multi-language financial statement support (English-only for now)
- Live streaming data feeds (Bloomberg, Reuters)
- Tax form extraction (W-2, 1099)
- Cross-company comparison in a single run

---

## 6. Updated Tool Choices (with Vision LLM requirement)

| Gap | Primary Path | Fallback / Enhancement |
|-----|-------------|----------------------|
| **Image file → CFS/IS/BS** | `vision_llm_extractor.py` using user's multimodal LLM (OpenRouter, OpenAI, Anthropic) | Local PaddleOCR → `_extract_line_items_from_text()` |
| **Scanned PDF → CFS/IS/BS** | Refactored `ocr_extractor.py` + vision LLM per page | Local PaddleOCR per page |
| **DOCX → text/tables** | New `docx_extractor.py` with `python-docx` | — |
| **XLSX → structured data** | New `xlsx_extractor.py` with `openpyxl` | — |
| **Text PDF (local file)** | Refactored `extract_from_pdf()` — accept direct path | — |
| **Ticker → EDGAR** | Existing L1-L4 pipeline (unchanged) | — |

### New Dependencies

```toml
[project.optional-dependencies]
vision = [
    "openai>=1.0.0",        # OpenAI-compatible API calls (OpenRouter, etc.)
    "anthropic>=0.30.0",    # Anthropic API (optional, can use OpenAI-compat path)
]
docx = [
    "python-docx>=1.0.0",
]
xlsx = [
    "openpyxl>=3.0.0",
]
ocr = [
    "paddleocr>=2.0.0",
    "pytesseract>=0.3.0",
    "Pillow>=10.0.0",
]
```
