# Financial Statement Stress Test Skill

## Purpose

Systematically stress-test the 4-agent financial analysis pipeline (extractor → parser → analyzer → reporter) with real-world SEC EDGAR data, edge cases, and boundary conditions. Identifies bugs, data quality gaps, and scoring accuracy issues.

## When to Use

Run this after any pipeline code change, after adding new sample data, or when investigating scoring anomalies.

Triggers:
- "stress test the pipeline"
- "run edge case tests"
- "validate pipeline robustness"
- "why is the score so low for [ticker]?"
- "stress test with [ticker] data"

## Test Categories

### 1. Full Pipeline on Real Sample Data

Run all 4 sample companies (AAPL, MSFT, GOOGL, JPM) through the complete pipeline. Verify:
- All status fields propagate correctly (SUCCESS → SUCCESS → SUCCESS)
- Scorecards are computed for all companies
- Red flags are detected per company-specific data
- Cross-validation runs all 5 checks
- All 3 output formats (JSON, Markdown, HTML) render valid output

Expected: pipeline completes for all 4 companies without crashes.

### 2. Edge Case Injection

Test input robustness. Each edge case should produce a scorecard (not crash):

| Edge Case | What it Tests |
|-----------|---------------|
| All zero values | Division-by-zero handling, default values |
| Negative equity + negative OCF | Sign-aware ratio computation |
| Extreme values (1e15 scale) | Float overflow, scaling |
| Missing fields (partial statements) | Graceful degradation with available data |
| Empty periods | Early return path |
| Unbalanced balance sheet (A != L+E) | Structure validation flagging |
| Non-numeric/garbage values (None, NaN, inf) | Input sanitization |
| Multi-year extreme swings (100x volatility) | Anomaly detection saturation |
| Negative gross profit (COGS > revenue) | Plausibility checks |

### 3. Throughput

Process the largest sample 50 times sequentially. Verify sub-50ms average pipeline time.

### 4. Output Format Validation

Generate all 3 formats for all 4 companies. Verify:
- JSON is valid and parseable
- HTML contains `<html>`, `<style>`, `<body>` tags
- Markdown has at least one `# ` header

## Bug Knowledge Base

When running stress tests, be aware of these known failure modes:

| ID | Bug | Symptom | Root Cause |
|----|-----|---------|------------|
| 1 | Empty period crash | KeyError on `scorecard` | Analyzer early return missing structured fields |
| 2 | Garbage data crash | TypeError in unit_normalizer | Non-numeric values (None, NaN, str) multiply by scale factor |
| 3 | Interest consistency always 0 periods | `periods_evaluated: 0` in all CV output | Function uses scalar inputs, default arg never overridden |
| 4 | Duplicate fiscal years | Two periods with same FY in parsed output | Parser doesn't deduplicate periods |
| 5 | Anomaly metric name missing | `metric` field empty in anomaly output | Field named `item` not `metric` in detector |
| 6 | gross_profit > revenue | Impossible GP data passes silently | No plausibility check; COGS-missing GP skips IS arithmetic check |

## Pipeline Flow

```
Raw data (JSON)
  → parser.parse_financial_data()
    → unit_normalizer.normalize_period() [BUG 2 here]
    → label_mapper.map_all_line_items()
    → _populate_dataclass()
    → subtotal_calculator.compute_derived_fields() [BUG 6 relevant]
    → structure_validator.run_all_validations()
  → analyzer.analyze_financial_data() [BUG 1 here]
    → ratio_calculator.compute_all_ratios()
    → trend_analyzer.analyze_trends()
    → red_flag_detector.detect_all_red_flags()
    → cross_validator.run_cross_validation() [BUG 3 here]
    → anomaly_detector.detect_anomalies() [BUG 5 here]
    → scorer.compute_scorecard()
  → reporter.generate_report()
```

## Quick Run

```bash
# Full pipeline on all 4 sample companies
uv run python -c "
import sys; sys.path.insert(0, '.')
import json
from src.parsing.parser import parse_financial_data
from src.analysis.analyzer import analyze_financial_data
from src.reporting.reporter import generate_report

for ticker in ['aapl', 'msft', 'googl', 'jpm']:
    with open(f'data/samples/{ticker}_2020_2024.json') as f:
        raw = json.load(f)
    p = parse_financial_data(raw)
    a = analyze_financial_data(p)
    r = generate_report(a)
    sc = a.get('scorecard', {})
    flags = len(a.get('red_flags', []))
    print(f'{ticker.upper()}: {sc.get(\"total\",\"?\")}/100 {sc.get(\"assessment\",\"?\")} | {flags} flags | {a[\"status\"]}')
"
```

## Scoring Interpretation

Scores from real SEC data must be interpreted cautiously:

- **Score < 40 for known-profitable companies** (AAPL, MSFT): likely data mapping gaps — the XBRL concept mappings don't cover all SEC filing variants. Check which fields are MISSING, especially ocf, capex, depreciation.
- **Key indicators to trust**: cross-validation results (earnings quality is reliable), anomaly counts for extreme years, red flag presence for the matched fields.
- **Key indicators to distrust**: overall score when >2 fields are missing per statement, efficiency scores when all 0, liquidity scores when current_assets/liabilities are 0.
