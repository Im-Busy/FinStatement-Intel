"""Image extraction — extract financial statements from image files (PNG, JPG, etc.).

Routes to either:
    - Vision LLM (OpenAI-compatible / Anthropic) if configured
    - Local OCR (PaddleOCR / tesseract) otherwise
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from src.extraction.unit_detector import detect_unit
from src.extraction.vision_backend import VisionBackend, VisionConfig
from src.extraction.vision_llm_extractor import extract_image_with_llm

logger = logging.getLogger(__name__)

_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".tif", ".webp"}


def _extract_with_local_ocr(image_path: str | Path, ticker: str = "") -> dict[str, Any] | None:
    """Extract text from image using local OCR, then parse into line items."""
    path = Path(image_path)
    if not path.exists():
        return None

    all_text: list[str] = []

    tesseract_text = _try_tesseract(path)
    if tesseract_text:
        all_text.append(tesseract_text)

    paddleocr_text = _try_paddleocr(path)
    if paddleocr_text:
        all_text.append(paddleocr_text)

    if not all_text:
        return None

    full_text = "\n".join(all_text)
    statements = _extract_line_items_from_text(full_text)
    total_items = sum(len(items) for items in statements.values())
    if total_items == 0:
        return None

    unit_name, currency = detect_unit(all_text)

    period = {
        "type": "annual",
        "fiscal_year": 0,
        "end_date": "",
        "source": f"image-ocr:{path.name}",
        "statements": {
            "IS": {"unit": unit_name, "line_items": statements.get("IS", [])},
            "BS": {"unit": unit_name, "line_items": statements.get("BS", [])},
            "CFS": {"unit": unit_name, "line_items": statements.get("CFS", [])},
        },
    }

    return {
        "status": "SUCCESS",
        "company": {
            "name": ticker.upper() if ticker else "UNKNOWN",
            "ticker": ticker.upper() if ticker else "",
            "fiscal_year_end": "",
            "currency": currency,
        },
        "periods": [period],
        "warnings": [],
        "metadata": {
            "extraction_method": "image-ocr",
            "extraction_timestamp": "",
            "periods_requested": 1,
            "periods_extracted": 1,
        },
    }


def _try_tesseract(image_path: Path) -> str:
    """Try tesseract OCR on an image file."""
    try:
        import pytesseract
        from PIL import Image
    except ImportError:
        return ""

    try:
        img = Image.open(image_path)
        return pytesseract.image_to_string(img, lang="eng")
    except Exception as e:
        logger.debug("Tesseract failed for %s: %s", image_path, e)
        return ""


def _try_paddleocr(image_path: Path) -> str:
    """Try PaddleOCR on an image file."""
    try:
        from paddleocr import PaddleOCR
    except ImportError:
        return ""

    try:
        ocr = PaddleOCR(lang="en", show_log=False)
        result = ocr.ocr(str(image_path))
        if not result or not result[0]:
            return ""
        lines = [line[1][0] for group in result for line in group if line and len(line) > 1]
        return "\n".join(lines)
    except Exception as e:
        logger.debug("PaddleOCR failed for %s: %s", image_path, e)
        return ""


def extract_from_image(
    image_path: str | Path,
    ticker: str = "",
    config: VisionConfig | None = None,
) -> dict[str, Any]:
    """Extract financial statement data from an image file.

    Priority:
        1. Vision LLM (if configured with API key)
        2. Local OCR (PaddleOCR, then tesseract)

    Args:
        image_path: Path to PNG, JPG, or other image file.
        ticker: Optional company ticker for metadata.
        config: VisionConfig. If None, loaded from env.

    Returns:
        Standard extraction result dict with status, periods, warnings.
    """
    if config is None:
        config = VisionConfig.from_env()

    path = Path(image_path)
    if not path.exists():
        return {
            "status": "ERROR",
            "message": f"File not found: {image_path}",
            "company": {"name": ticker.upper(), "ticker": ticker.upper(), "fiscal_year_end": ""},
            "periods": [],
            "warnings": [],
        }

    suffix = path.suffix.lower()
    if suffix not in _IMAGE_EXTENSIONS:
        return {
            "status": "ERROR",
            "message": f"Unsupported image format: {suffix}. Supported: {_IMAGE_EXTENSIONS}",
            "company": {"name": ticker.upper(), "ticker": ticker.upper(), "fiscal_year_end": ""},
            "periods": [],
            "warnings": [],
        }

    if config.backend != VisionBackend.LOCAL and config.api_key:
        logger.info("Using vision LLM backend: %s", config.backend.value)
        result = extract_image_with_llm(path, config, ticker=ticker)
        if result.get("status") == "SUCCESS" and result.get("periods"):
            return result
        logger.warning("Vision LLM failed, falling back to local OCR: %s", result.get("message"))
        result["warnings"] = result.get("warnings", [])
        result["warnings"].append("Vision LLM failed, fell back to local OCR")

    result = _extract_with_local_ocr(path, ticker)
    if result:
        return result

    return {
        "status": "ERROR",
        "message": f"Failed to extract any financial data from {image_path}",
        "company": {"name": ticker.upper(), "ticker": ticker.upper(), "fiscal_year_end": ""},
        "periods": [],
        "warnings": ["Both vision LLM and local OCR extraction failed"],
    }


def _extract_line_items_from_text(text: str) -> dict[str, list[dict[str, Any]]]:
    """Import wrapper for existing OCR module's parser."""
    from src.extraction.ocr_extractor import _extract_line_items_from_text as _fn

    return _fn(text)
