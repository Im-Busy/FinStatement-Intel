"""OCR extraction (L4) — last-resort text extraction from scanned/image-based PDFs.

Converts PDF pages to images and runs OCR to recover financial statement text.
Only triggered per-page when PyMuPDF text extraction yield is below threshold.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from src.extraction.line_item_extractor import build_line_item, clean_label
from src.extraction.unit_detector import detect_unit, parse_value

logger = logging.getLogger(__name__)


def _try_pdf_text_extraction(pdf_path: str, page_num: int) -> str:
    """Try PyMuPDF text extraction first for a single page."""
    try:
        import fitz
    except ImportError:
        return ""
    try:
        doc = fitz.open(pdf_path)
        if page_num >= len(doc):
            doc.close()
            return ""
        page = doc[page_num]
        text = page.get_text()
        doc.close()
        return text
    except Exception:
        return ""


def _ocr_page_with_tesseract(pdf_path: str, page_num: int) -> str:
    """OCR a single page using pytesseract.

    Falls back to empty string if pytesseract or PIL is not available.
    """
    try:
        import fitz
        import pytesseract
        from PIL import Image
    except ImportError:
        logger.info("OCR dependencies not available — install pytesseract and Pillow")
        return ""

    try:
        doc = fitz.open(pdf_path)
        if page_num >= len(doc):
            doc.close()
            return ""
        page = doc[page_num]
        pix = page.get_pixmap(dpi=200)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        text = pytesseract.image_to_string(img, lang="eng")
        doc.close()
        return text
    except Exception as e:
        logger.warning("OCR failed for page %d: %s", page_num, e)
        return ""


def _ocr_page_with_paddleocr(pdf_path: str, page_num: int) -> str:
    """OCR a single page using PaddleOCR."""
    try:
        import fitz
        from paddleocr import PaddleOCR
        from PIL import Image
    except ImportError:
        logger.info("PaddleOCR not available — install with: uv add paddleocr")
        return ""

    try:
        doc = fitz.open(pdf_path)
        if page_num >= len(doc):
            doc.close()
            return ""
        page = doc[page_num]
        pix = page.get_pixmap(dpi=200)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        img_path = Path(pdf_path).parent / f"_ocr_temp_page_{page_num}.png"
        img.save(img_path)

        ocr = PaddleOCR(lang="en", show_log=False)
        result = ocr.ocr(str(img_path))
        img_path.unlink(missing_ok=True)
        doc.close()

        if not result or not result[0]:
            return ""

        lines = [line[1][0] for group in result for line in group if line and len(line) > 1]
        return "\n".join(lines)
    except Exception as e:
        logger.warning("PaddleOCR failed for page %d: %s", page_num, e)
        return ""


def _extract_line_items_from_text(text: str) -> dict[str, list[dict[str, Any]]]:
    """Parse OCR text into line items using heuristic patterns.

    Looks for patterns like:
        "Label Name  $1,234"
        "Label Name  (567)"
        "Label Name  1,234"
    """
    import re

    statements: dict[str, list[dict[str, Any]]] = {"IS": [], "BS": [], "CFS": []}

    amount_line_re = re.compile(r"^(.{3,80}?)\s+(?:\$?\s*\(?[\d,]+\.?\d*\)?)\s*$")

    lines = text.split("\n")
    for line in lines:
        stripped = line.strip()
        if not stripped or len(stripped) < 10:
            continue
        match = amount_line_re.match(stripped)
        if not match:
            continue

        label = match.group(1).strip()
        label_clean = clean_label(label)
        if not label_clean:
            continue

        parts = stripped.rsplit(None, 1)
        if len(parts) < 2:
            continue

        value_text = parts[1]
        value_str = value_text.replace("$", "").replace(",", "").strip()
        try:
            value = parse_value(value_str)
        except (ValueError, TypeError):
            continue

        lower = label_clean.lower()

        if any(
            kw in lower
            for kw in [
                "revenue",
                "sales",
                "cost of",
                "gross",
                "operating",
                "income tax",
                "interest",
                "eps",
                "earnings per",
                "net income",
                "profit",
                "r&d",
                "research",
                "selling",
                "general",
                "administrative",
            ]
        ):
            statements["IS"].append(build_line_item(label_clean, value))

        elif any(
            kw in lower
            for kw in [
                "assets",
                "liabilities",
                "equity",
                "cash",
                "receivable",
                "inventory",
                "payable",
                "debt",
                "goodwill",
                "property",
                "accumulated",
            ]
        ):
            statements["BS"].append(build_line_item(label_clean, value))

        elif any(
            kw in lower
            for kw in [
                "operating activ",
                "investing activ",
                "financing activ",
                "depreciation",
                "amortization",
                "stock-based",
                "capex",
                "capital expenditure",
                "dividend",
                "repurchase",
                "proceeds",
                "repayment",
                "free cash",
            ]
        ):
            statements["CFS"].append(build_line_item(label_clean, value))

        else:
            statements["BS"].append(build_line_item(label_clean, value))

    return statements


def extract_with_ocr(
    pdf_path: str,
    ticker: str,
    engine: str = "tesseract",
    pages: list[int] | None = None,
) -> dict[str, Any] | None:
    """Extract financial data from PDF using OCR.

    Args:
        pdf_path: Path to the PDF file.
        ticker: Stock ticker symbol.
        engine: OCR engine to use ('tesseract' or 'paddleocr').
        pages: Optional list of page indices to OCR.

    Returns:
        Extraction result dict or None on failure.
    """
    try:
        import fitz
    except ImportError:
        return {
            "status": "ERROR",
            "message": "PyMuPDF not installed. Install with: uv add PyMuPDF",
            "company": {"name": ticker.upper(), "ticker": ticker.upper()},
            "periods": [],
            "warnings": ["PDF library unavailable for OCR preprocessing"],
        }

    try:
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        doc.close()
    except Exception as e:
        return {
            "status": "ERROR",
            "message": f"Failed to open PDF: {e}",
            "company": {"name": ticker.upper(), "ticker": ticker.upper()},
            "periods": [],
            "warnings": [],
        }

    target_pages = pages if pages else list(range(total_pages))
    all_text_parts: list[str] = []

    for page_num in target_pages:
        text = _try_pdf_text_extraction(pdf_path, page_num)
        word_count = len(text.split())
        if word_count < 20:
            logger.info("Page %d has low text yield (%d words), running OCR", page_num, word_count)
            if engine == "paddleocr":
                ocr_text = _ocr_page_with_paddleocr(pdf_path, page_num)
            else:
                ocr_text = _ocr_page_with_tesseract(pdf_path, page_num)
            text = ocr_text if ocr_text else text

        if text:
            all_text_parts.append(text)

    if not all_text_parts:
        logger.warning("No text extracted from PDF %s", pdf_path)
        return None

    full_text = "\n".join(all_text_parts)
    statements = _extract_line_items_from_text(full_text)

    total_items = sum(len(items) for items in statements.values())
    if total_items == 0:
        return None

    unit_name, currency = detect_unit(all_text_parts)

    period = {
        "type": "annual",
        "fiscal_year": 0,
        "end_date": "",
        "source": "ocr-extraction",
        "statements": {
            "IS": {"unit": unit_name, "line_items": statements.get("IS", [])},
            "BS": {"unit": unit_name, "line_items": statements.get("BS", [])},
            "CFS": {"unit": unit_name, "line_items": statements.get("CFS", [])},
        },
    }

    return {
        "status": "SUCCESS",
        "company": {
            "name": ticker.upper(),
            "ticker": ticker.upper(),
            "fiscal_year_end": "",
            "currency": currency,
        },
        "periods": [period],
        "warnings": [],
        "metadata": {
            "extraction_method": f"ocr-{engine}",
            "extraction_timestamp": "",
            "periods_requested": 1,
            "periods_extracted": 1,
        },
    }
