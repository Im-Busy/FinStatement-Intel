"""Generate sample data for MSFT, GOOGL, JPM via EDGAR."""
from src.extraction import extract_financial_data
import json

for ticker in ["MSFT", "GOOGL", "JPM"]:
    print(f"Extracting {ticker}...")
    result = extract_financial_data(ticker, periods=5, source="edgar")
    output_path = f"data/samples/{ticker.lower()}_2020_2024.json"
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)
    n_periods = len(result.get("periods", []))
    n_items = sum(
        len(p.get("statements", {}).get(k, {}).get("line_items", []))
        for p in result.get("periods", [])
        for k in ("IS", "BS", "CFS")
    )
    print(f"  -> {output_path} (status={result.get('status')}, periods={n_periods}, items={n_items})")
print("Done.")
