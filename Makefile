# Cross-Asset Alpha Lab - Makefile
# Windows-compatible targets with fallback support for Git Bash
# Note: Some targets may not work under Git Bash (sh interpreter)
# For full compatibility, run under native Windows cmd.exe with make installed

.PHONY: help install test clean check-env
.PHONY: replay-vintage
.PHONY: viz-equity viz-compare viz-risk
.PHONY: n6-dry-run

# Default target
help:
	@echo Cross-Asset Alpha Lab - Available Commands
	@echo ==========================================
	@echo.
	@echo Setup and Environment:
	@echo   make install          Create venv and install dependencies
	@echo   make check-env        Verify Python version and environment
	@echo   make test             Run full test suite
	@echo   make clean            Remove cache and temporary files
	@echo.
	@echo Data and Replay:
	@echo   make replay-vintage   Replay approved vintage (requires local data)
	@echo.
	@echo Visualization (requires matplotlib, pandas, numpy):
	@echo   make viz-equity RUN=^<run_id^>        Generate equity curve
	@echo   make viz-compare RUNS=^'^<id1^> ^<id2^>^'  Compare strategies
	@echo   make viz-risk RUN=^<run_id^>          Risk analysis chart
	@echo.
	@echo N6 Scenario Runner (preview mode):
	@echo   make n6-dry-run PROVIDER=H1_252_3    Preview N6 cost scenarios
	@echo.
	@echo Notes:
	@echo   - Visualization targets require matplotlib to be installed
	@echo   - N6 runner currently operates in dry-run preview mode only
	@echo   - See Makefile comments for Git Bash compatibility notes

# Environment setup
install:
	py -3.14 -m venv .venv
	.venv\Scripts\python -m pip install --upgrade pip
	.venv\Scripts\python -m pip install -r requirements.lock
	@echo Environment created. Activate with: .venv\Scripts\activate

check-env:
	@py -3.14 --version > nul 2>&1 || (echo ERROR: Python 3.14 not found && exit 1)
	@echo Python 3.14 found
	@if exist .venv\Scripts\python.exe (echo Virtual environment exists) else (echo Run 'make install' first && exit 1)

# Testing
test: check-env
	set PYTHONPATH=src && .venv\Scripts\python -m pytest -q -p no:cacheprovider --basetemp=%TEMP%\alpha-lab-pytest

# Cleanup
clean:
	@for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d" 2>nul
	@if exist .pytest_cache rmdir /s /q .pytest_cache 2>nul
	@echo Cleaned cache and temporary files

# Data operations (WARNING: may not work under Git Bash)
# For Git Bash compatibility, check the path syntax and use sh commands
replay-vintage: check-env
	@if not exist data\derived\20261006T172442-80ef993493 (echo ERROR: Approved vintage not found && exit 1)
	set PYTHONPATH=src && .venv\Scripts\python -m alpha_lab replay data\derived\20261006T172442-80ef993493 --root . --parent 20261006T172442-80ef993493

# Visualization targets
viz-equity: check-env
	@if "$(RUN)"=="" (echo ERROR: RUN variable required. Usage: make viz-equity RUN=^<run_id^> && exit 1)
	@if not exist data\runs\$(RUN) (echo ERROR: Run directory not found: data\runs\$(RUN) && exit 1)
	.venv\Scripts\python scripts\visualization\equity_curves.py data\runs\$(RUN) --output charts\$(RUN)_equity.png
	@echo Chart saved to charts\$(RUN)_equity.png

viz-compare: check-env
	@if "$(RUNS)"=="" (echo ERROR: RUNS variable required. Usage: make viz-compare RUNS=^"^<id1^> ^<id2^>^" && exit 1)
	.venv\Scripts\python scripts\visualization\comparison_plots.py $(RUNS) --output charts\comparison.png
	@echo Chart saved to charts\comparison.png

viz-risk: check-env
	@if "$(RUN)"=="" (echo ERROR: RUN variable required. Usage: make viz-risk RUN=^<run_id^> && exit 1)
	@if not exist data\runs\$(RUN) (echo ERROR: Run directory not found: data\runs\$(RUN) && exit 1)
	.venv\Scripts\python scripts\visualization\risk_charts.py data\runs\$(RUN) --output charts\$(RUN)_risk.png
	@echo Chart saved to charts\$(RUN)_risk.png

# N6 scenario runner (preview mode)
n6-dry-run: check-env
	@if "$(PROVIDER)"=="" (echo ERROR: PROVIDER variable required. Usage: make n6-dry-run PROVIDER=H1_252_3 && exit 1)
	set PYTHONPATH=src && .venv\Scripts\python scripts\n6_runner.py --root . --provider $(PROVIDER) --scenarios cost_grid --dry-run
