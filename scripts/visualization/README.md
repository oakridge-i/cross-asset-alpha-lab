# Visualization Tools

Generate charts and plots from research runs.

## Requirements

```powershell
pip install matplotlib pandas numpy
```

## Usage

### 1. Equity Curves and Drawdown

```powershell
python scripts/visualization/equity_curves.py data/runs/<run_id> --output charts/equity.png
python scripts/visualization/equity_curves.py data/runs/<run_id> --show
```

### 2. Strategy Comparison

Compare multiple strategies side-by-side:

```powershell
python scripts/visualization/comparison_plots.py data/runs/<id1> data/runs/<id2> data/runs/<id3> --output charts/comparison.png
```

### 3. Risk Analysis

Risk metrics, turnover, and cash allocation:

```powershell
python scripts/visualization/risk_charts.py data/runs/<run_id> --output charts/risk.png
```

## Examples

```powershell
# Generate equity curve for B3 benchmark
python scripts/visualization/equity_curves.py data/runs/20261007T180033-bba99392df --output charts/b3_equity.png

# Compare all H1 configurations
python scripts/visualization/comparison_plots.py data/runs/20261010T090737-2d652c2127 data/runs/20261010T090745-899d5a7136 data/runs/20261010T090752-9bd003f35b data/runs/20261010T090800-f78d0ee07b --output charts/h1_comparison.png

# Risk analysis for P_A1
python scripts/visualization/risk_charts.py data/runs/20261010T090831-aeca348964 --output charts/pa1_risk.png
```

## Output

All charts are saved as PNG files with 150 DPI resolution. Use `--show` flag for interactive display.

## Notes

- Requires `daily.csv` in run directory
- `metrics.json` required for risk charts
- `decisions.csv` required for turnover/cash allocation
- Charts use research-appropriate color palette
- All visualizations are reproducible from frozen run data
