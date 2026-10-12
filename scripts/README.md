# Automation Tools

This directory contains automation and utility scripts for the research project.

## Structure

```
scripts/
├── visualization/          # Chart and plot generation
│   ├── equity_curves.py    # Equity curves and drawdowns
│   ├── comparison_plots.py # Multi-strategy comparison
│   ├── risk_charts.py      # Risk metrics visualization
│   └── README.md           # Visualization documentation
├── n6_runner.py            # N6 scenario automation
└── README.md               # This file
```

## Quick Start

### Visualization

```powershell
# Generate equity curve
python scripts/visualization/equity_curves.py data/runs/<run_id> --output charts/equity.png

# Compare strategies
python scripts/visualization/comparison_plots.py data/runs/<id1> data/runs/<id2> --output charts/compare.png

# Risk analysis
python scripts/visualization/risk_charts.py data/runs/<run_id> --output charts/risk.png
```

### N6 Scenario Runner

```powershell
# Dry run to preview commands
python scripts/n6_runner.py --root . --provider H1_252_3 --scenarios cost_grid --dry-run

# Run cost grid (0/10/20/50 bps)
python scripts/n6_runner.py --root . --provider H1_252_3 --scenarios cost_grid

# Run all hypothesis providers
python scripts/n6_runner.py --root . --provider all --scenarios full_grid
```

## Requirements

Visualization requires:
```
matplotlib
pandas
numpy
```

Install with:
```powershell
pip install matplotlib pandas numpy
```

## Usage with Makefile

If you have `make` installed:

```powershell
# Visualization
make viz-equity RUN=20261010T090737-2d652c2127
make viz-compare RUNS="data/runs/<id1> data/runs/<id2>"
make viz-risk RUN=20261010T090737-2d652c2127

# N6 scenarios
make n6-dry-run PROVIDER=H1_252_3
make n6-cost-grid PROVIDER=H1_252_3
make n6-full-grid PROVIDER=all
```

## Notes

- All visualizations work with frozen run data
- N6 runner appends to `experiments/EXPERIMENT_LOG.jsonl`
- Results are saved to `outputs/n6_results.json`
- Charts are saved to `charts/` by default
- All scripts support `--help` for full options

## Integration with Research Workflow

1. **After N5**: Use visualization to analyze walk-forward results
2. **For N6**: Use n6_runner.py to automate scenario grid
3. **For reports**: Generate charts for inclusion in research documents

See `AGENTS_QUICKREF.md` for integration with agent workflows.
