"""File router — detect file type and route to appropriate extractor.

Handles:
    - PDF (text-based): PyMuPDF + camelot
    - PDF (scanned): OCR (tesseract/PaddleOCR) + vision LLM fallback
    - Image (PNG, JPG, etc.): vision LLM or local OCR
    - DOCX: python-docx table extraction
    - XLSX: openpyxl sheet scanning
    - Ticker string: EDGAR pipeline (existing)
    - URL: download then route
"""

from __future__ import annotations

import logging
from enum import Enum, auto
from pathlib import Path
from typing import Any

from src.extraction.vision_backend import VisionConfig

logger = logging.getLogger(__name__)


class FileType(Enum):
    PDF_TEXT = auto()
    PDF_SCANNED = auto()
    IMAGE = auto()
    DOCX = auto()
    XLSX = auto()
    CSV = auto()
    UNKNOWN = auto()


_PDF_MAGIC = b"%PDF"
_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".tif", ".webp"}
_DOCX_EXTENSIONS = {".docx", ".doc"}
_XLSX_EXTENSIONS = {".xlsx", ".xls"}
_CSV_EXTENSIONS = {".csv", ".tsv"}


def detect_file_type(path: str | Path) -> FileType:
    """Detect the type of a file by extension and magic bytes.

    Args:
        path: File path to analyze.

    Returns:
        FileType enum value.
    """
    p = Path(path)

    if not p.exists():
        return FileType.UNKNOWN

    suffix = p.suffix.lower()

    if suffix in _IMAGE_EXTENSIONS:
        return FileType.IMAGE

    if suffix in _DOCX_EXTENSIONS:
        return FileType.DOCX

    if suffix in _XLSX_EXTENSIONS:
        return FileType.XLSX

    if suffix in _CSV_EXTENSIONS:
        return FileType.CSV

    if suffix == ".pdf" or _is_pdf_by_magic(p):
        return _classify_pdf(p)

    return FileType.UNKNOWN


def _is_pdf_by_magic(path: Path) -> bool:
    """Check if a file is a PDF by reading its magic bytes."""
    try:
        return path.read_bytes()[:4] == _PDF_MAGIC
    except OSError:
        return False


def _classify_pdf(path: Path) -> FileType:
    """Classify a PDF as text-based or scanned by checking text yield on the first page."""
    try:
        import fitz
    except ImportError:
        return FileType.PDF_TEXT

    try:
        doc = fitz.open(str(path))
        if len(doc) == 0:
            doc.close()
            return FileType.UNKNOWN
        page = doc[0]
        text = page.get_text()
        doc.close()
        word_count = len(text.split())
        if word_count < 20:
            return FileType.PDF_SCANNED
        return FileType.PDF_TEXT
    except Exception:
        return FileType.PDF_TEXT


def extract_from_file(
    path: str | Path,
    ticker: str | None = None,
    periods: int = 5,
    config: VisionConfig | None = None,
) -> dict[str, Any]:
    """Extract financial data from any supported file format.

    Auto-detects file type and routes to the correct extractor.

    Args:
        path: Path to the file (PDF, image, DOCX, XLSX).
        ticker: Optional company ticker for metadata.
        periods: Number of fiscal periods to extract (for PDF).
        config: VisionConfig for cloud LLM backends.

    Returns:
        Standard extraction result dict with status, periods, warnings.
    """
    p = Path(path)
    if not p.exists():
        return {
            "status": "ERROR",
            "message": f"File not found: {path}",
            "company": _empty_company(ticker),
            "periods": [],
            "warnings": [],
        }

    file_type = detect_file_type(p)
    ticker_str = ticker or ""
    logger.info("File %s detected as %s", p.name, file_type.name)

    if config is None:
        config = VisionConfig.from_env()

    if file_type == FileType.PDF_TEXT:
        from src.extraction.pdf_extractor import extract_from_pdf as extract_pdf

        result = extract_pdf(str(p), ticker_str)
        if result:
            return result
        return _empty_error(f"PDF text extraction failed for {p.name}", ticker)

    if file_type == FileType.PDF_SCANNED:
        from src.extraction.ocr_extractor import extract_with_ocr

        result = extract_with_ocr(str(p), ticker_str)
        if result:
            return result
        return _empty_error(f"OCR extraction failed for {p.name}", ticker)

    if file_type == FileType.IMAGE:
        from src.extraction.image_extractor import extract_from_image

        return extract_from_image(str(p), ticker_str, config)

    if file_type == FileType.DOCX:
        try:
            from src.extraction.docx_extractor import extract_from_docx
        except ImportError:
            return _empty_error("DOCX extraction not available: python-docx not installed", ticker)
        return extract_from_docx(str(p), ticker_str)

    if file_type == FileType.XLSX:
        try:
            from src.extraction.xlsx_extractor import extract_from_xlsx
        except ImportError:
            return _empty_error("XLSX extraction not available: openpyxl not installed", ticker)
        return extract_from_xlsx(str(p), ticker_str)

    return {
        "status": "ERROR",
        "message": f"Unsupported or unrecognized file type: {p.suffix}",
        "company": _empty_company(ticker),
        "periods": [],
        "warnings": [],
    }


def _empty_company(ticker: str | None) -> dict[str, str]:
    t = (ticker or "").upper()
    return {"name": t, "ticker": t, "fiscal_year_end": ""}


def _empty_error(message: str, ticker: str | None) -> dict[str, Any]:
    return {
        "status": "ERROR",
        "message": message,
        "company": _empty_company(ticker),
        "periods": [],
        "warnings": [],
    }
