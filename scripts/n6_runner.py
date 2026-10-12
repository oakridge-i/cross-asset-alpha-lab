"""N6 Scenario Runner - Automated execution of cost/delay scenarios.

This script automates the N6 robustness campaign as specified in RESEARCH_PROTOCOL.md section 12.

Usage:
    python scripts/n6_runner.py --root . --provider H1_252_3 --scenarios cost_grid
    python scripts/n6_runner.py --root . --provider all --scenarios full_grid --dry-run

Scenarios:
    - cost_grid: 0/10/20/50 bps with lag=1
    - lag_grid: lag 1/2 with cost=10 bps
    - full_grid: all cost × lag combinations
    - leave_one_out: exclude each asset class
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
        """Execute one simulation run."""
        cmd = [
            sys.executable, '-m', 'alpha_lab', 'simulate',
            str(self.vintage),
            '--provider', provider,
            '--start', start,
            '--end', end,
            '--cost', str(cost),
            '--lag', str(lag),
            '--reserve', str(reserve),
            '--proxy-days', str(proxy_days),
            '--stage', '5',
            '--root', str(self.root)
        ]
        
        if parent:
            cmd.extend(['--parent', parent])
        
        scenario_id = f"{provider}_c{int(cost*10000)}bp_lag{lag}_proxy{proxy_days}"
        
        print(f"\n{'[DRY RUN] ' if self.dry_run else ''}Running: {scenario_id}")
        print(f"Command: {' '.join(cmd)}")
        
        if self.dry_run:
            return {
                'scenario_id': scenario_id,
                'provider': provider,
                'cost': cost,
                'lag': lag,
                'proxy_days': proxy_days,
                'status': 'dry_run',
                'run_id': 'DRY_RUN'
            }
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, 
                                  env={'PYTHONPATH': 'src', **subprocess.os.environ})
            run_id = result.stdout.strip().split('/')[-1] if '/' in result.stdout else result.stdout.strip()
            
            return {
                'scenario_id': scenario_id,
                'provider': provider,
                'cost': cost,
                'lag': lag,
                'proxy_days': proxy_days,
                'status': 'completed',
                'run_id': run_id,
                'timestamp': datetime.utcnow().isoformat()
            }
        except subprocess.CalledProcessError as e:
            print(f"ERROR: {e}")
            print(f"STDERR: {e.stderr}")
            return {
                'scenario_id': scenario_id,
                'provider': provider,
                'cost': cost,
                'lag': lag,
                'proxy_days': proxy_days,
                'status': 'failed',
                'error': str(e)
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
                'failed': len([r for r in self.results if r['status'] == 'failed']),
                'results': self.results
            }, f, indent=2)
        print(f"\nResults saved to {output}")


def main():
    parser = argparse.ArgumentParser(description="N6 Scenario Runner")
    parser.add_argument('--root', type=Path, required=True, help='Project root directory')
    parser.add_argument('--vintage', type=Path, 
                       default=Path('data/derived/20261006T172442-80ef993493'),
                       help='Data vintage path')
    parser.add_argument('--provider', required=True, 
                       help='Provider name or "all" for all hypothesis providers')
    parser.add_argument('--scenarios', required=True,
                       choices=['cost_grid', 'lag_grid', 'full_grid'],
                       help='Which scenario grid to run')
    parser.add_argument('--start', default='2008-12-31', help='Start date')
    parser.add_argument('--end', default='2022-12-30', help='End date')
    parser.add_argument('--output', type=Path, 
                       default=Path('outputs/n6_results.json'),
                       help='Output JSON file')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Print commands without executing')
    
    args = parser.parse_args()
    
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
    
    print(f"N6 Scenario Runner")
    print(f"{'=' * 60}")
    print(f"Providers: {', '.join(providers)}")
    print(f"Scenarios: {args.scenarios}")
    print(f"Window: {args.start} to {args.end}")
    print(f"Dry run: {args.dry_run}")
    print(f"{'=' * 60}\n")
    
    # Run scenarios
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
    print(f"\n{'=' * 60}")
    print(f"Summary:")
    print(f"Total runs: {len(runner.results)}")
    print(f"Completed: {len([r for r in runner.results if r['status'] == 'completed'])}")
    print(f"Failed: {len([r for r in runner.results if r['status'] == 'failed'])}")
    print(f"{'=' * 60}")
    
    # Exit with error code if any failed
    if any(r['status'] == 'failed' for r in runner.results):
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
