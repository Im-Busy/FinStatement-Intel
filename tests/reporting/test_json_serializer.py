"""Tests for JSON serializer."""

import json

from src.reporting.json_serializer import render_json


class TestRenderJson:
    def test_renders_valid_json(self):
        data = {"status": "SUCCESS", "report": {"company": {"ticker": "TEST"}}}
        result = render_json(data)
        parsed = json.loads(result)
        assert parsed["status"] == "SUCCESS"
        assert parsed["report"]["company"]["ticker"] == "TEST"

    def test_custom_indent(self):
        data = {"key": "value"}
        result = render_json(data, indent=4)
        assert "    " in result

    def test_unicode_handling(self):
        data = {"note": "caf"}
        result = render_json(data)
        parsed = json.loads(result)
        assert parsed["note"] == "caf"

    def test_empty(self):
        result = render_json({})
        assert result == "{}"
