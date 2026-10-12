"""Risk and attribution visualizations.

Usage:
    python scripts/visualization/risk_charts.py data/runs/<run_id> --output charts/risk.png
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


def load_metrics(run_dir: Path) -> dict:
    """Load metrics.json if available."""
    metrics_path = run_dir / "metrics.json"
    if not metrics_path.exists():
        raise FileNotFoundError(f"metrics.json not found in {run_dir}")
    return json.loads(metrics_path.read_text())


def load_decisions(run_dir: Path) -> pd.DataFrame:
    """Load decisions.csv."""
    decisions_csv = run_dir / "decisions.csv"
    if not decisions_csv.exists():
        raise FileNotFoundError(f"decisions.csv not found in {run_dir}")
    
    df = pd.read_csv(decisions_csv)
    df['decision_session'] = pd.to_datetime(df['decision_session'])
    return df


def plot_risk_metrics(run_dir: Path, output: Path = None, show: bool = False):
    """Create risk analysis charts."""
    metrics = load_metrics(run_dir)
    decisions = load_decisions(run_dir)
    
    # Extract provider name
    manifest_path = run_dir / "manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        provider = manifest.get('config', {}).get('provider', 'Unknown')
    else:
        provider = run_dir.name
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(f'Risk Analysis: {provider}', fontsize=14, fontweight='bold')
    
    # 1. Turnover over time
    if 'turnover' in decisions.columns:
        axes[0, 0].plot(decisions['decision_session'], decisions['turnover'], 
                       linewidth=1.2, color='#F18F01', marker='o', markersize=3)
        axes[0, 0].set_ylabel('One-way Turnover', fontsize=10)
        axes[0, 0].set_title('Turnover Over Time', fontsize=11)
        axes[0, 0].grid(True, alpha=0.3)
    
    # 2. Cash allocation over time
    if 'usd' in decisions.columns:
        axes[0, 1].fill_between(decisions['decision_session'], decisions['usd'], 
                                alpha=0.6, color='#2E86AB')
        axes[0, 1].set_ylabel('Cash Weight', fontsize=10)
        axes[0, 1].set_title('Cash Allocation Over Time', fontsize=11)
        axes[0, 1].grid(True, alpha=0.3)
    
    # 3. Period metrics (if available)
    if 'periods' in metrics and metrics['periods']:
        periods = list(metrics['periods'].keys())
        vols = [metrics['periods'][p]['volatility_annual'] for p in periods if 'volatility_annual' in metrics['periods'][p]]
        
        if vols:
            axes[1, 0].bar(range(len(vols)), vols, color='#A23B72', alpha=0.7)
            axes[1, 0].set_ylabel('Annualized Volatility', fontsize=10)
            axes[1, 0].set_title('Volatility by Period', fontsize=11)
            axes[1, 0].set_xticks(range(len(periods)))
            axes[1, 0].set_xticklabels(periods, rotation=45, ha='right', fontsize=8)
            axes[1, 0].axhline(y=0.10, color='red', linestyle='--', linewidth=1, alpha=0.5, label='10% target')
            axes[1, 0].legend(fontsize=8)
            axes[1, 0].grid(True, alpha=0.3, axis='y')
    
    # 4. Summary statistics (text)
    axes[1, 1].axis('off')
    summary_text = f"Summary Statistics\n{'-' * 30}\n"
    
    if 'periods' in metrics and 'full' in metrics['periods']:
        full = metrics['periods']['full']
        summary_text += f"CAGR: {full.get('cagr_annual', 'N/A'):.4f}\n" if isinstance(full.get('cagr_annual'), (int, float)) else "CAGR: N/A\n"
        summary_text += f"Volatility: {full.get('volatility_annual', 'N/A'):.4f}\n" if isinstance(full.get('volatility_annual'), (int, float)) else "Volatility: N/A\n"
        summary_text += f"Sharpe: {full.get('sharpe_bil', 'N/A'):.4f}\n" if isinstance(full.get('sharpe_bil'), (int, float)) else "Sharpe: N/A\n"
        summary_text += f"Max DD: {full.get('max_drawdown', 'N/A'):.4f}\n" if isinstance(full.get('max_drawdown'), (int, float)) else "Max DD: N/A\n"
        summary_text += f"Decisions: {full.get('decisions', 'N/A')}\n"
        summary_text += f"Mean Turnover: {full.get('turnover_annual', 'N/A'):.4f}\n" if isinstance(full.get('turnover_annual'), (int, float)) else "Mean Turnover: N/A\n"
        summary_text += f"Cost Ratio: {full.get('cost_ratio', 'N/A'):.6f}\n" if isinstance(full.get('cost_ratio'), (int, float)) else "Cost Ratio: N/A\n"
    
    axes[1, 1].text(0.1, 0.5, summary_text, fontsize=10, family='monospace',
                   verticalalignment='center', transform=axes[1, 1].transAxes)
    
    plt.tight_layout()
    
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output, dpi=150, bbox_inches='tight')
        print(f"Risk chart saved to {output}")
    
    if show:
        plt.show()
    
    plt.close()


def main():
    parser = argparse.ArgumentParser(description="Generate risk analysis charts")
    parser.add_argument('run_dir', type=Path, help='Path to run directory')
    parser.add_argument('--output', type=Path, help='Output file path')
    parser.add_argument('--show', action='store_true', help='Display chart interactively')
    
    args = parser.parse_args()
    
    if not args.run_dir.exists():
        print(f"Error: Run directory not found: {args.run_dir}")
        return 1
    
    try:
        plot_risk_metrics(args.run_dir, args.output, args.show)
        return 0
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
