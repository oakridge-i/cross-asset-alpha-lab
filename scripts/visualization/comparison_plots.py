"""Compare multiple strategies side-by-side.

Usage:
    python scripts/visualization/comparison_plots.py data/runs/<id1> data/runs/<id2> --output charts/comparison.png
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


def load_run_data(run_dir: Path) -> tuple[str, pd.DataFrame]:
    """Load run data and return (provider_name, daily_df)."""
    manifest_path = run_dir / "manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        provider = manifest.get('config', {}).get('provider', run_dir.name)
    else:
        provider = run_dir.name
    
    daily_csv = run_dir / "daily.csv"
    if not daily_csv.exists():
        raise FileNotFoundError(f"daily.csv not found in {run_dir}")
    
    df = pd.read_csv(daily_csv)
    df['session'] = pd.to_datetime(df['session'])
    df.set_index('session', inplace=True)
    
    return provider, df


def normalize_nav(nav_series: pd.Series, base: float = 100.0) -> pd.Series:
    """Normalize NAV to start at base value."""
    return nav_series / nav_series.iloc[0] * base


def plot_comparison(run_dirs: list[Path], output: Path = None, show: bool = False):
    """Create comparison chart of multiple strategies."""
    fig, axes = plt.subplots(2, 1, figsize=(14, 10), sharex=True)
    
    colors = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#6A994E', '#BC4B51']
    
    all_data = []
    for i, run_dir in enumerate(run_dirs):
        try:
            provider, df = load_run_data(run_dir)
            all_data.append((provider, df))
        except Exception as e:
            print(f"Warning: Skipping {run_dir}: {e}")
    
    if not all_data:
        print("Error: No valid run data found")
        return 1
    
    # Equity curves (normalized to 100)
    for i, (provider, df) in enumerate(all_data):
        normalized = normalize_nav(df['nav'], base=100.0)
        color = colors[i % len(colors)]
        axes[0].plot(df.index, normalized, label=provider, linewidth=1.5, color=color, alpha=0.8)
    
    axes[0].set_ylabel('Normalized NAV (base=100)', fontsize=11)
    axes[0].set_title('Strategy Comparison: Normalized Equity Curves', fontsize=13, fontweight='bold')
    axes[0].legend(loc='best', fontsize=9)
    axes[0].grid(True, alpha=0.3, linestyle='--')
    axes[0].axhline(y=100, color='gray', linestyle='--', linewidth=0.8, alpha=0.5)
    
    # Drawdowns
    for i, (provider, df) in enumerate(all_data):
        cummax = df['nav'].cummax()
        drawdown = (df['nav'] - cummax) / cummax * 100
        color = colors[i % len(colors)]
        axes[1].plot(df.index, drawdown, label=provider, linewidth=1.2, color=color, alpha=0.7)
    
    axes[1].set_ylabel('Drawdown (%)', fontsize=11)
    axes[1].set_xlabel('Date', fontsize=11)
    axes[1].legend(loc='best', fontsize=9)
    axes[1].grid(True, alpha=0.3, linestyle='--')
    
    plt.tight_layout()
    
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output, dpi=150, bbox_inches='tight')
        print(f"Comparison chart saved to {output}")
    
    if show:
        plt.show()
    
    plt.close()
    return 0


def main():
    parser = argparse.ArgumentParser(description="Compare multiple strategies")
    parser.add_argument('run_dirs', nargs='+', type=Path, help='Run directories to compare')
    parser.add_argument('--output', type=Path, help='Output file path')
    parser.add_argument('--show', action='store_true', help='Display chart interactively')
    
    args = parser.parse_args()
    
    return plot_comparison(args.run_dirs, args.output, args.show)


if __name__ == '__main__':
    sys.exit(main())
