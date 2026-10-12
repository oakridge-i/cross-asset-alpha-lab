# Cross-Asset Alpha Lab - Makefile
# Common commands for development and research tasks

.PHONY: help install test clean lint format check-env
.PHONY: replay-vintage run-benchmarks
.PHONY: viz-equity viz-compare viz-risk
.PHONY: n6-dry-run n6-cost-grid

# Default target
help:
	@echo "Cross-Asset Alpha Lab - Available Commands"
	@echo "=========================================="
	@echo ""
	@echo "Setup and Environment:"
	@echo "  make install          Create venv and install dependencies"
	@echo "  make check-env        Verify Python version and environment"
	@echo "  make clean            Remove cache and temporary files"
	@echo ""
	@echo "Testing:"
	@echo "  make test             Run full test suite"
	@echo "  make test-fast        Run tests without slow fixtures"
	@echo "  make lint             Check code style (if ruff installed)"
	@echo ""
	@echo "Data and Replay:"
	@echo "  make replay-vintage   Replay approved vintage (requires local data)"
	@echo ""
	@echo "Visualization:"
	@echo "  make viz-equity RUN=<run_id>           Generate equity curve"
	@echo "  make viz-compare RUNS='<id1> <id2>'    Compare strategies"
	@echo "  make viz-risk RUN=<run_id>             Risk analysis chart"
	@echo ""
	@echo "N6 Scenario Runner:"
	@echo "  make n6-dry-run PROVIDER=H1_252_3      Dry run N6 scenarios"
	@echo "  make n6-cost-grid PROVIDER=H1_252_3    Run cost grid (0/10/20/50 bps)"
	@echo "  make n6-full-grid PROVIDER=all         Run full cost x lag grid"
	@echo ""
	@echo "Examples:"
	@echo "  make viz-equity RUN=20261010T090737-2d652c2127"
	@echo "  make n6-cost-grid PROVIDER=H1_252_3"

# Environment setup
install:
	py -3.14 -m venv .venv
	.venv\Scripts\python -m pip install --upgrade pip
	.venv\Scripts\python -m pip install -r requirements.lock
	@echo "Environment created. Activate with: .venv\Scripts\activate"

check-env:
	@py -3.14 --version || (echo "ERROR: Python 3.14 not found" && exit 1)
	@echo "Python 3.14 found"
	@if exist .venv\Scripts\python.exe (echo "Virtual environment exists") else (echo "Run 'make install' first" && exit 1)

# Testing
test: check-env
	set PYTHONPATH=src && .venv\Scripts\python -m pytest -q -p no:cacheprovider --basetemp=%TEMP%\alpha-lab-pytest

test-fast: check-env
	set PYTHONPATH=src && .venv\Scripts\python -m pytest -q -p no:cacheprovider -m "not slow" --basetemp=%TEMP%\alpha-lab-pytest

lint:
	@if exist .venv\Scripts\ruff.exe (.venv\Scripts\ruff check src tests) else (echo "ruff not installed, skipping")

format:
	@if exist .venv\Scripts\black.exe (.venv\Scripts\black src tests) else (echo "black not installed, skipping")

# Cleanup
clean:
	@if exist .pytest_cache rmdir /s /q .pytest_cache
	@if exist .venv\Lib\site-packages\alpha_lab.egg-info rmdir /s /q .venv\Lib\site-packages\alpha_lab.egg-info
	@for /r %%i in (__pycache__) do @if exist "%%i" rmdir /s /q "%%i"
	@echo "Cleaned cache and temporary files"

# Data operations
replay-vintage: check-env
	@if not exist data\derived\20261006T172442-80ef993493 (echo "ERROR: Approved vintage not found in data/derived/" && exit 1)
	set PYTHONPATH=src && .venv\Scripts\python -m alpha_lab replay data\derived\20261006T172442-80ef993493 --root . --parent 20261006T172442-80ef993493

# Visualization (requires run directories)
viz-equity: check-env
	@if "$(RUN)"=="" (echo "ERROR: RUN variable required. Usage: make viz-equity RUN=<run_id>" && exit 1)
	@if not exist data\runs\$(RUN) (echo "ERROR: Run directory not found: data\runs\$(RUN)" && exit 1)
	.venv\Scripts\python scripts\visualization\equity_curves.py data\runs\$(RUN) --output charts\$(RUN)_equity.png
	@echo "Chart saved to charts\$(RUN)_equity.png"

viz-compare: check-env
	@if "$(RUNS)"=="" (echo "ERROR: RUNS variable required. Usage: make viz-compare RUNS='<id1> <id2>'" && exit 1)
	.venv\Scripts\python scripts\visualization\comparison_plots.py $(RUNS) --output charts\comparison.png
	@echo "Chart saved to charts\comparison.png"

viz-risk: check-env
	@if "$(RUN)"=="" (echo "ERROR: RUN variable required. Usage: make viz-risk RUN=<run_id>" && exit 1)
	@if not exist data\runs\$(RUN) (echo "ERROR: Run directory not found: data\runs\$(RUN)" && exit 1)
	.venv\Scripts\python scripts\visualization\risk_charts.py data\runs\$(RUN) --output charts\$(RUN)_risk.png
	@echo "Chart saved to charts\$(RUN)_risk.png"

# N6 scenario runner
n6-dry-run: check-env
	@if "$(PROVIDER)"=="" (echo "ERROR: PROVIDER variable required. Usage: make n6-dry-run PROVIDER=H1_252_3" && exit 1)
	set PYTHONPATH=src && .venv\Scripts\python scripts\n6_runner.py --root . --provider $(PROVIDER) --scenarios cost_grid --dry-run

n6-cost-grid: check-env
	@if "$(PROVIDER)"=="" (echo "ERROR: PROVIDER variable required. Usage: make n6-cost-grid PROVIDER=H1_252_3" && exit 1)
	set PYTHONPATH=src && .venv\Scripts\python scripts\n6_runner.py --root . --provider $(PROVIDER) --scenarios cost_grid

n6-lag-grid: check-env
	@if "$(PROVIDER)"=="" (echo "ERROR: PROVIDER variable required" && exit 1)
	set PYTHONPATH=src && .venv\Scripts\python scripts\n6_runner.py --root . --provider $(PROVIDER) --scenarios lag_grid

n6-full-grid: check-env
	@if "$(PROVIDER)"=="" (echo "ERROR: PROVIDER variable required" && exit 1)
	set PYTHONPATH=src && .venv\Scripts\python scripts\n6_runner.py --root . --provider $(PROVIDER) --scenarios full_grid
	@echo "WARNING: Full grid runs all cost x lag combinations (8 runs per provider)"
