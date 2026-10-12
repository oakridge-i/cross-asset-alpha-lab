"""Generate equity curves and drawdown charts from run results.

Usage:
    python scripts/visualization/equity_curves.py data/runs/<run_id> --output charts/equity.png
    python scripts/visualization/equity_curves.py data/runs/<run_id> --show
"""
import argparse
import json
from pathlib import Path
import sys

try:
    import matplotlib.pyplot as plt
    import pandas as pd
    import numpy as np
except ImportError as e:
    print(f"Error: Missing required package: {e.name}")
    print("Install with: pip install matplotlib pandas numpy")
    sys.exit(1)


def load_daily_data(run_dir: Path) -> pd.DataFrame:
    """Load daily.csv from a run directory."""
    daily_csv = run_dir / "daily.csv"
    if not daily_csv.exists():
        raise FileNotFoundError(f"daily.csv not found in {run_dir}")
    
    df = pd.read_csv(daily_csv)
    df['session'] = pd.to_datetime(df['session'])
    df.set_index('session', inplace=True)
    return df


def calculate_drawdown(nav_series: pd.Series) -> pd.Series:
    """Calculate drawdown from NAV series."""
    cummax = nav_series.cummax()
    drawdown = (nav_series - cummax) / cummax
    return drawdown


def plot_equity_and_drawdown(df: pd.DataFrame, title: str, output: Path = None, show: bool = False):
    """Create a two-panel chart: equity curve and drawdown."""
    fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
    
    # Equity curve
    axes[0].plot(df.index, df['nav'], linewidth=1.5, color='#2E86AB')
    axes[0].set_ylabel('NAV (USD)', fontsize=11)
    axes[0].set_title(title, fontsize=13, fontweight='bold')
    axes[0].grid(True, alpha=0.3, linestyle='--')
    axes[0].axhline(y=100000, color='gray', linestyle='--', linewidth=0.8, alpha=0.5)
    
    # Drawdown
    drawdown = calculate_drawdown(df['nav'])
    axes[1].fill_between(df.index, drawdown * 100, 0, color='#A23B72', alpha=0.6)
    axes[1].set_ylabel('Drawdown (%)', fontsize=11)
    axes[1].set_xlabel('Date', fontsize=11)
    axes[1].grid(True, alpha=0.3, linestyle='--')
    
    plt.tight_layout()
    
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output, dpi=150, bbox_inches='tight')
        print(f"Chart saved to {output}")
    
    if show:
        plt.show()
    
    plt.close()


def main():
    parser = argparse.ArgumentParser(description="Generate equity curve and drawdown chart")
    parser.add_argument('run_dir', type=Path, help='Path to run directory (e.g., data/runs/<run_id>)')
    parser.add_argument('--output', type=Path, help='Output file path (e.g., charts/equity.png)')
    parser.add_argument('--show', action='store_true', help='Display chart interactively')
    parser.add_argument('--title', help='Chart title (defaults to run config name)')
    
    args = parser.parse_args()
    
    if not args.run_dir.exists():
        print(f"Error: Run directory not found: {args.run_dir}")
        return 1
    
    # Load manifest to get provider name
    manifest_path = args.run_dir / "manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        provider = manifest.get('config', {}).get('provider', 'Unknown')
    else:
        provider = args.run_dir.name
    
    title = args.title or f"Equity Curve: {provider}"
    
    try:
        df = load_daily_data(args.run_dir)
        plot_equity_and_drawdown(df, title, args.output, args.show)
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
