# Command: /analyze

Runs the full financial statement analysis pipeline for a company.

## Pipeline
extractor → parser → analyzer → reporter

## Usage
```
/analyze <ticker> [--periods <N>] [--source <edgar|pdf|html>]
```

## Parameters
- `ticker` — Stock ticker symbol (required)
- `--periods N` — Number of fiscal years to analyze (default: 5)
- `--source` — Data source preference (default: edgar)

## Example
```
/analyze AAPL --periods 5
/analyze MSFT --source pdf --periods 3
```

## Output
A financial statement analysis report with:
1. Executive summary with overall assessment
2. Financial health scorecard (0-100)
3. Detailed ratio analysis across profitability, liquidity, solvency, efficiency, cash flow quality
4. Red flags with severity ratings
5. Strengths and recommendations
