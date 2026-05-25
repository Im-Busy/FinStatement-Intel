# Command: /extract

Extracts raw financial data from a source without parsing or analysis.

## Usage
```
/extract <ticker> [--source <edgar|pdf|html>] [--periods <N>]
```

## Parameters
- `ticker` — Stock ticker symbol (required)
- `--source` — Data source (default: edgar)
- `--periods N` — Number of periods (default: 5)

## Output
Raw extracted JSON with all line items from CFS, IS, BS.
