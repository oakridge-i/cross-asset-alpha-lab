# Automation Tools - Implementation Notes

## Created: December 2024

This feature branch adds three automation components to support N6 and visualization needs.

## Components

### 1. Visualization Module (`scripts/visualization/`)

**Purpose**: Generate research-quality charts from run results

**Files**:
- `equity_curves.py` - Equity curve and drawdown plots
- `comparison_plots.py` - Side-by-side strategy comparison
- `risk_charts.py` - Risk metrics, turnover, cash allocation
- `README.md` - Usage documentation

**Dependencies**: `matplotlib`, `pandas`, `numpy` (optional, for visualization only)

**Key features**:
- Works with frozen run data (daily.csv, metrics.json, decisions.csv)
- Research-appropriate color palette
- High DPI output (150 dpi)
- Interactive mode (`--show`) and file output (`--output`)
- Provider name extraction from manifest.json

**Example usage**:
```powershell
python scripts/visualization/equity_curves.py data/runs/20261010T090737-2d652c2127 --output charts/h1_252_3.png
```

### 2. N6 Scenario Runner (`scripts/n6_runner.py`)

**Purpose**: Automate RESEARCH_PROTOCOL.md section 12 scenario grid

**Scenarios**:
- `cost_grid`: 0/10/20/50 bps with lag=1 (4 runs per provider)
- `lag_grid`: lag 1/2 with cost=10 bps (2 runs per provider)
- `full_grid`: all cost × lag combinations (8 runs per provider)

**Key features**:
- Dry-run mode for command preview
- Progress tracking and error handling
- JSON output with results summary
- Appends to experiment journal
- Supports single provider or `--provider all`

**Example usage**:
```powershell
# Preview commands
python scripts/n6_runner.py --root . --provider H1_252_3 --scenarios cost_grid --dry-run

# Execute
python scripts/n6_runner.py --root . --provider H1_252_3 --scenarios cost_grid
```

### 3. Makefile (`Makefile`)

**Purpose**: Centralized command shortcuts for Windows

**Targets**:
- `make install` - Create venv and install dependencies
- `make test` - Run full test suite
- `make replay-vintage` - Replay approved vintage
- `make viz-equity RUN=<id>` - Generate equity curve
- `make viz-compare RUNS='<id1> <id2>'` - Compare strategies
- `make viz-risk RUN=<id>` - Risk analysis
- `make n6-dry-run PROVIDER=<name>` - Preview N6 scenarios
- `make n6-cost-grid PROVIDER=<name>` - Run cost grid
- `make n6-full-grid PROVIDER=<name>` - Run full grid

**Note**: Windows Makefile syntax (using `%TEMP%`, `set`, `rmdir /s /q`, etc.)

**Example usage**:
```powershell
make viz-equity RUN=20261010T090737-2d652c2127
make n6-cost-grid PROVIDER=H1_252_3
```

## Testing

Added `tests/test_automation_scripts.py`:
- Import verification
- N6 scenario definitions validation
- Dry-run mode testing
- Skips visualization tests if matplotlib not installed

Run with:
```powershell
pytest tests/test_automation_scripts.py -v
```

## Integration with Existing Project

**No changes to**:
- Core source code (`src/alpha_lab/`)
- Research protocol or decisions
- Frozen N3/N4/N5 results
- Experiment journal format

**Extends**:
- `scripts/` directory (new)
- Test suite (new test file)
- Root Makefile (new)

## Documentation

- `scripts/README.md` - Overview of all scripts
- `scripts/visualization/README.md` - Visualization usage
- `Makefile` - Inline help with `make help`

## Future Enhancements

Possible additions (not in this PR):
- Leave-one-out asset class scenarios
- Proxy payment delay scenarios (0/10/30 days)
- Automated report generation from scenario results
- Dashboard for interactive exploration (Streamlit/Dash)

## Verification

Before merge:
- [ ] All tests pass: `pytest tests/test_automation_scripts.py`
- [ ] No changes to frozen code paths
- [ ] Documentation complete
- [ ] Example commands verified
- [ ] Dry-run mode tested

## Usage After Merge

1. **For visualization** (requires pip install matplotlib pandas numpy):
   ```powershell
   make viz-equity RUN=<run_id>
   ```

2. **For N6 automation**:
   ```powershell
   make n6-cost-grid PROVIDER=H1_252_3
   ```

3. **Check available commands**:
   ```powershell
   make help
   ```
