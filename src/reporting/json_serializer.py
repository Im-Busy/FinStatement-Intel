"""JSON serializer — converts report data to formatted JSON string."""

from __future__ import annotations

import json
from typing import Any


def render_json(report_data: dict[str, Any], indent: int = 2) -> str:
    """Render the analysis report as a formatted JSON string.

    Args:
        report_data: Complete report JSON from the reporter.
        indent: JSON indentation level.

    Returns:
        Formatted JSON string.
    """
    return json.dumps(report_data, indent=indent, ensure_ascii=False)
