"""N6 Scenario Runner - Automated execution of cost/delay scenarios.

WARNING: This is a template/prototype for N6 execution.
It requires:
- N6 specification and design document approval (not yet finalized)
- Protocol version frozen in RESEARCH_PROTOCOL.md
- D026+ decisions recorded in DECISIONS.md
- Code freeze at N6 start

DO NOT run on real data without the above. This runner will be enabled
after N6 specification is complete.

Usage (when enabled):
    python scripts/n6_runner.py --root . --provider H1_252_3 --scenarios cost_grid
    python scripts/n6_runner.py --root . --provider all --scenarios full_grid --dry-run

Scenarios:
    - cost_grid: 0/10/20/50 bps with lag=1
    - lag_grid: lag 1/2 with cost=10 bps
    - full_grid: all cost × lag combinations
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict


# Protocol section 12 scenarios
COST_SCENARIOS = [0.0, 0.001, 0.002, 0.005]  # 0, 10, 20, 50 bps per side
LAG_SCENARIOS = [1, 2]  # 1 or 2 sessions
PROXY_SCENARIOS = [0, 10, 30]  # calendar days

# Asset class groups for leave-one-out (RESEARCH_PROTOCOL.md section 2)
ASSET_CLASSES = {
    'equity': ['SPY', 'EFA', 'EEM'],
    'treasury': ['IEF', 'TLT'],
    'credit': ['LQD', 'HYG'],
    'real': ['GLD', 'DBC']
}

# Available providers
HYPOTHESIS_PROVIDERS = ['H1_252_3', 'H1_252_4', 'H1_126_3', 'H1_126_4', 'H2_4of6', 'H2_5of6']
POLICY_PROVIDERS = ['P_A1']
ALL_PROVIDERS = HYPOTHESIS_PROVIDERS + POLICY_PROVIDERS


class N6Runner:
    def __init__(self, root: Path, vintage: Path, dry_run: bool = False):
        self.root = root.resolve()
        self.vintage = vintage
        self.dry_run = dry_run
        self.results = []
        
    def run_simulation(self, provider: str, start: str, end: str, cost: float, lag: int, 
                      reserve: float = 0.01, proxy_days: int = 10, parent: str = None) -> Dict:
        """Execute one simulation run.
        
        Note: This method requires N6 specification and code freeze to be finalized.
        Currently only supports dry-run mode for demonstration.
        """
        if not self.dry_run:
            raise RuntimeError(
                "N6 runner is not yet enabled for real execution.\n"
                "Waiting for N6 specification completion and code freeze."
            )
        
        scenario_id = f"{provider}_c{int(cost*10000)}bp_lag{lag}_proxy{proxy_days}"
        
        print(f"[DRY RUN] {scenario_id}")
        print(f"  Provider: {provider}")
        print(f"  Cost: {cost} ({int(cost*10000)} bps)")
        print(f"  Lag: {lag} sessions")
        print(f"  Proxy: {proxy_days} calendar days")
        
        return {
            'scenario_id': scenario_id,
            'provider': provider,
            'cost': cost,
            'lag': lag,
            'proxy_days': proxy_days,
            'status': 'dry_run',
            'run_id': 'DRY_RUN_N6_NOT_ACTIVE'
        }
    
    def run_cost_grid(self, provider: str, start: str, end: str) -> List[Dict]:
        """Run all cost scenarios with lag=1."""
        results = []
        for cost in COST_SCENARIOS:
            result = self.run_simulation(provider, start, end, cost, lag=1)
            results.append(result)
            self.results.append(result)
        return results
    
    def run_lag_grid(self, provider: str, start: str, end: str) -> List[Dict]:
        """Run lag scenarios with cost=10bps."""
        results = []
        for lag in LAG_SCENARIOS:
            result = self.run_simulation(provider, start, end, cost=0.001, lag=lag)
            results.append(result)
            self.results.append(result)
        return results
    
    def run_full_grid(self, provider: str, start: str, end: str) -> List[Dict]:
        """Run full cost × lag grid."""
        results = []
        for cost in COST_SCENARIOS:
            for lag in LAG_SCENARIOS:
                result = self.run_simulation(provider, start, end, cost, lag)
                results.append(result)
                self.results.append(result)
        return results
    
    def save_results(self, output: Path):
        """Save results to JSON."""
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open('w') as f:
            json.dump({
                'timestamp': datetime.utcnow().isoformat(),
                'total_runs': len(self.results),
                'completed': len([r for r in self.results if r['status'] == 'completed']),
                'dry_runs': len([r for r in self.results if r['status'] == 'dry_run']),
                'status': 'N6 not yet active - dry-run mode only',
                'results': self.results
            }, f, indent=2)
        print(f"\nResults saved to {output}")


def main():
    parser = argparse.ArgumentParser(
        description="N6 Scenario Runner (dry-run only, awaiting N6 specification)"
    )
    parser.add_argument('--root', type=Path, required=True, help='Project root directory')
    parser.add_argument('--vintage', type=Path, 
                       default=Path('data/derived/20261006T172442-80ef993493'),
                       help='Data vintage path')
    parser.add_argument('--provider', required=True, 
                       help='Provider name or "all" for all hypothesis providers')
    parser.add_argument('--scenarios', required=True,
                       choices=['cost_grid', 'lag_grid', 'full_grid'],
                       help='Which scenario grid to preview')
    parser.add_argument('--start', default='2008-12-31', help='Start date')
    parser.add_argument('--end', default='2022-12-30', help='End date')
    parser.add_argument('--output', type=Path, 
                       default=Path('outputs/n6_results.json'),
                       help='Output JSON file')
    parser.add_argument('--dry-run', action='store_true', default=True,
                       help='Preview mode (always dry-run until N6 is active)')
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("N6 Scenario Runner - DRY RUN MODE")
    print("=" * 70)
    print("\nWARNING: N6 is not yet active.")
    print("This tool is in preview/dry-run mode only.\n")
    print("To enable N6 execution, the following must be complete:")
    print("  1. N6 specification document (docs/superpowers/specs/2026-10-XX-n6-*.md)")
    print("  2. D0XX decisions in DECISIONS.md with all interpretations")
    print("  3. Code freeze at start of N6 campaign")
    print("  4. Update this runner to remove the RuntimeError check\n")
    
    runner = N6Runner(args.root, args.vintage, args.dry_run)
    
    # Determine which providers to run
    if args.provider == 'all':
        providers = HYPOTHESIS_PROVIDERS
    elif args.provider in ALL_PROVIDERS:
        providers = [args.provider]
    else:
        print(f"Error: Unknown provider '{args.provider}'")
        print(f"Available: {', '.join(ALL_PROVIDERS)}, or 'all'")
        return 1
    
    print(f"Providers: {', '.join(providers)}")
    print(f"Scenarios: {args.scenarios}")
    print(f"Window: {args.start} to {args.end}")
    print("-" * 70 + "\n")
    
    # Run scenarios (dry-run only)
    try:
        for provider in providers:
            print(f"\nProvider: {provider}")
            print("-" * 40)
            
            if args.scenarios == 'cost_grid':
                runner.run_cost_grid(provider, args.start, args.end)
            elif args.scenarios == 'lag_grid':
                runner.run_lag_grid(provider, args.start, args.end)
            elif args.scenarios == 'full_grid':
                runner.run_full_grid(provider, args.start, args.end)
        
        # Save results
        runner.save_results(args.output)
        
        # Summary
        print(f"\n{'=' * 70}")
        print(f"Dry-run preview complete. No actual runs were executed.")
        print(f"Total scenarios previewed: {len(runner.results)}")
        print(f"{'=' * 70}\n")
        
        return 0
    
    except RuntimeError as e:
        print(f"\nError: {e}\n")
        return 1


if __name__ == '__main__':
    sys.exit(main())
