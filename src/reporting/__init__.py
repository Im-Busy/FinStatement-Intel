"""Report generation module — executive summary, scorecard, findings, renderers."""

from src.reporting.html_renderer import render_html
from src.reporting.json_serializer import render_json
from src.reporting.markdown_renderer import render_markdown
from src.reporting.reporter import generate_report

__all__ = ["generate_report", "render_html", "render_json", "render_markdown"]
