"""Vision LLM extractor — sends images to multimodal LLMs for financial statement extraction.

Supports:
    - OpenAI-compatible endpoints (OpenAI, OpenRouter, Ollama, vLLM, DeepSeek)
    - Anthropic native API

The LLM receives a base64-encoded image and a specialized prompt asking it to
extract all line items with values, identify statement type, period, and unit.
"""

from __future__ import annotations

import base64
import json
import logging
from pathlib import Path
from typing import Any

from src.extraction.line_item_extractor import build_line_item, clean_label
from src.extraction.vision_backend import VisionBackend, VisionConfig

logger = logging.getLogger(__name__)

_VISION_SYSTEM_PROMPT = """You are a financial statement data extraction system. Your task is to analyze images of financial statements and extract structured data.

Rules:
1. Identify the statement type: Income Statement (IS), Balance Sheet (BS), or Cash Flow Statement (CFS).
2. Identify the reporting period (e.g. "FY2024", "Q3 2024", "Year Ended Dec 31, 2024").
3. Detect the unit scale: actual, thousands, millions, or billions.
4. Detect the currency (USD, EUR, GBP, JPY, CNY, HKD, etc.).
5. Extract EVERY visible line item with its numerical value.
6. Line items with parenthetical values like (1,234) are negative.
7. Do NOT invent or guess values. Only extract what is visible.
8. If a value is unclear or ambiguous, set needs_review=true for that item.

Return ONLY a valid JSON object using this EXACT schema:
{
  "statement_type": "IS",
  "period": "FY2024",
  "unit": "millions",
  "currency": "USD",
  "line_items": [
    {"label": "Revenue", "value": 383285.0, "needs_review": false}
  ]
}"""


def _encode_image(image_path: str | Path) -> tuple[str, str]:
    """Encode an image file to base64 data URL.

    Args:
        image_path: Path to image file (PNG, JPG, etc.).

    Returns:
        Tuple of (mime_type, base64_data_url).
    """
    path = Path(image_path)
    suffix = path.suffix.lower()

    mime_map = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".bmp": "image/bmp",
        ".tiff": "image/tiff",
        ".tif": "image/tiff",
        ".webp": "image/webp",
    }
    mime_type = mime_map.get(suffix, "image/png")

    data = path.read_bytes()
    encoded = base64.b64encode(data).decode("utf-8")
    data_url = f"data:{mime_type};base64,{encoded}"

    return mime_type, data_url


def _extract_via_openai(
    image_data_url: str,
    config: VisionConfig,
    extra_prompt: str = "",
) -> dict[str, Any]:
    """Send image to an OpenAI-compatible multimodal endpoint.

    Works with: OpenAI, OpenRouter, Ollama, vLLM, DeepSeek — anything
    that speaks the /v1/chat/completions protocol.
    """
    try:
        from openai import OpenAI
    except ImportError:
        return {
            "status": "ERROR",
            "message": "openai package not installed. Install with: uv add openai",
        }

    client = OpenAI(base_url=config.base_url, api_key=config.api_key)
    user_prompt = _VISION_SYSTEM_PROMPT
    if extra_prompt:
        user_prompt = f"{_VISION_SYSTEM_PROMPT}\n\nAdditional context: {extra_prompt}"

    response = client.chat.completions.create(
        model=config.model,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_prompt},
                    {"type": "image_url", "image_url": {"url": image_data_url}},
                ],
            }
        ],
        max_tokens=config.max_tokens,
        temperature=config.temperature,
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content
    if not content:
        return {"status": "ERROR", "message": "Empty response from vision LLM"}

    return _parse_llm_response(content)


def _extract_via_anthropic(
    image_path: str | Path,
    config: VisionConfig,
    extra_prompt: str = "",
) -> dict[str, Any]:
    """Send image to Anthropic's native API.

    Uses Anthropic's image content block format with base64 source.
    """
    mime_type, base64_data = _encode_raw_base64(image_path)

    try:
        from anthropic import Anthropic
    except ImportError:
        return {
            "status": "ERROR",
            "message": "anthropic package not installed. Install with: uv add anthropic",
        }

    client = Anthropic(api_key=config.api_key)
    user_prompt = _VISION_SYSTEM_PROMPT
    if extra_prompt:
        user_prompt = f"{_VISION_SYSTEM_PROMPT}\n\nAdditional context: {extra_prompt}"

    response = client.messages.create(
        model=config.model,
        max_tokens=config.max_tokens,
        temperature=config.temperature,
        system="You are a financial data extraction system. Return ONLY valid JSON.",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": mime_type,
                            "data": base64_data,
                        },
                    },
                    {"type": "text", "text": user_prompt},
                ],
            }
        ],
    )

    content = ""
    for block in response.content:
        if hasattr(block, "text"):
            content += block.text

    if not content:
        return {"status": "ERROR", "message": "Empty response from Anthropic vision"}

    return _parse_llm_response(content)


def _encode_raw_base64(image_path: str | Path) -> tuple[str, str]:
    """Encode image as raw base64 string (without data URL prefix).

    Args:
        image_path: Path to image file.

    Returns:
        Tuple of (mime_type, base64_string).
    """
    path = Path(image_path)
    suffix = path.suffix.lower()
    mime_map = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".bmp": "image/bmp",
        ".tiff": "image/tiff",
        ".tif": "image/tiff",
        ".webp": "image/webp",
    }
    mime_type = mime_map.get(suffix, "image/png")
    data = path.read_bytes()
    return mime_type, base64.b64encode(data).decode("utf-8")


def _parse_llm_response(content: str) -> dict[str, Any]:
    """Parse the LLM's JSON response, extracting the structured data.

    Handles markdown code fences (```json ... ```) and bare JSON.
    """
    cleaned = content.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        cleaned = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
        cleaned = cleaned.strip()

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        import re

        match = re.search(r"\{[\s\S]*\}", cleaned)
        if match:
            try:
                data = json.loads(match.group(0))
            except json.JSONDecodeError:
                return {"status": "ERROR", "message": "Failed to parse LLM response as JSON"}
        else:
            return {"status": "ERROR", "message": "No JSON found in LLM response"}

    if not isinstance(data, dict):
        return {"status": "ERROR", "message": "LLM returned non-object JSON"}

    line_items = data.get("line_items", [])
    if isinstance(line_items, list) and line_items and isinstance(line_items[0], dict):
        return data

    return {"status": "ERROR", "message": "No line_items array found in LLM response"}


def _llm_result_to_extraction_format(
    llm_data: dict[str, Any],
    ticker: str = "",
    source_path: str = "",
) -> dict[str, Any]:
    """Convert raw LLM extraction data to the standard extraction JSON format."""
    stmt_type = llm_data.get("statement_type", "BS").upper()
    if stmt_type not in ("IS", "BS", "CFS"):
        stmt_type = "BS"

    unit = llm_data.get("unit", "millions")
    currency = llm_data.get("currency", "USD")
    period = llm_data.get("period", "")

    line_items: list[dict[str, Any]] = []
    for item in llm_data.get("line_items", []):
        label = item.get("label", "")
        value = item.get("value", 0.0)
        needs_review = item.get("needs_review", False)

        if not label:
            continue

        try:
            value = float(value)
        except (TypeError, ValueError):
            value = 0.0
            needs_review = True

        line_items.append(
            build_line_item(clean_label(label), value, needs_review=needs_review)
        )

    statements = {
        "IS": {"unit": unit, "line_items": []},
        "BS": {"unit": unit, "line_items": []},
        "CFS": {"unit": unit, "line_items": []},
    }
    statements[stmt_type]["line_items"] = line_items

    period_entry = {
        "type": "annual",
        "fiscal_year": 0,
        "end_date": period if period else "",
        "source": f"vision-llm:{source_path}",
        "statements": statements,
    }

    return {
        "status": "SUCCESS",
        "company": {
            "name": ticker.upper() if ticker else "UNKNOWN",
            "ticker": ticker.upper() if ticker else "",
            "fiscal_year_end": "",
            "currency": currency,
        },
        "periods": [period_entry],
        "warnings": [],
        "metadata": {
            "extraction_method": "vision-llm",
            "vision_statement_type": stmt_type,
        },
    }


def extract_image_with_llm(
    image_path: str | Path,
    config: VisionConfig | None = None,
    ticker: str = "",
    extra_prompt: str = "",
) -> dict[str, Any]:
    """Extract financial statement data from an image using a multimodal LLM.

    Args:
        image_path: Path to the image file (PNG, JPG, etc.).
        config: VisionConfig instance. If None, loaded from env.
        ticker: Optional company ticker symbol for metadata.
        extra_prompt: Optional additional context for the LLM prompt.

    Returns:
        Standard extraction result dict.
    """
    if config is None:
        config = VisionConfig.from_env()

    issues = config.validate()
    if issues:
        return {"status": "ERROR", "message": "; ".join(issues)}

    image_path = Path(image_path)
    if not image_path.exists():
        return {"status": "ERROR", "message": f"File not found: {image_path}"}

    logger.info("Extracting from %s via %s (%s)", image_path, config.backend.value, config.model)

    try:
        if config.backend == VisionBackend.ANTHROPIC:
            llm_data = _extract_via_anthropic(image_path, config, extra_prompt)
        else:
            _, data_url = _encode_image(image_path)
            llm_data = _extract_via_openai(data_url, config, extra_prompt)
    except Exception as e:
        logger.exception("Vision LLM extraction failed")
        return {"status": "ERROR", "message": str(e)}

    if llm_data.get("status") == "ERROR":
        return llm_data

    return _llm_result_to_extraction_format(
        llm_data,
        ticker=ticker,
        source_path=str(image_path),
    )


def extract_pdf_page_with_llm(
    image_bytes: bytes,
    mime_type: str = "image/png",
    config: VisionConfig | None = None,
    extra_prompt: str = "",
) -> dict[str, Any]:
    """Extract financial data from a PDF page rendered as an image.

    Args:
        image_bytes: Raw image bytes (rendered PDF page).
        mime_type: MIME type of the image.
        config: VisionConfig instance.
        extra_prompt: Optional additional context.

    Returns:
        Raw LLM extraction data dict (NOT converted to standard format).
    """
    if config is None:
        config = VisionConfig.from_env()

    issues = config.validate()
    if issues:
        return {"status": "ERROR", "message": "; ".join(issues)}

    encoded = base64.b64encode(image_bytes).decode("utf-8")
    data_url = f"data:{mime_type};base64,{encoded}"

    try:
        if config.backend == VisionBackend.ANTHROPIC:
            raw_base64 = base64.b64encode(image_bytes).decode("utf-8")
            return _extract_via_anthropic_raw(raw_base64, mime_type, config, extra_prompt)

        return _extract_via_openai(data_url, config, extra_prompt)
    except Exception as e:
        logger.exception("Vision LLM page extraction failed")
        return {"status": "ERROR", "message": str(e)}


def _extract_via_anthropic_raw(
    base64_data: str,
    mime_type: str,
    config: VisionConfig,
    extra_prompt: str = "",
) -> dict[str, Any]:
    """Send raw base64 image to Anthropic API."""
    try:
        from anthropic import Anthropic
    except ImportError:
        return {
            "status": "ERROR",
            "message": "anthropic package not installed. Install with: uv add anthropic",
        }

    client = Anthropic(api_key=config.api_key)
    user_prompt = _VISION_SYSTEM_PROMPT
    if extra_prompt:
        user_prompt = f"{_VISION_SYSTEM_PROMPT}\n\nAdditional context: {extra_prompt}"

    response = client.messages.create(
        model=config.model,
        max_tokens=config.max_tokens,
        temperature=config.temperature,
        system="You are a financial data extraction system. Return ONLY valid JSON.",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": mime_type,
                            "data": base64_data,
                        },
                    },
                    {"type": "text", "text": user_prompt},
                ],
            }
        ],
    )

    content = ""
    for block in response.content:
        if hasattr(block, "text"):
            content += block.text

    if not content:
        return {"status": "ERROR", "message": "Empty response from Anthropic vision"}

    return _parse_llm_response(content)
