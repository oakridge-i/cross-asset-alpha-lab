"""Usage: python -m alpha_lab {acquire,evidence,audit,replay,reconcile,corrections} [snapshot] [evidence]
--root PROJECT; python -m alpha_lab simulate DERIVED --provider NAME --start DATE --end DATE
[--cost C --lag L --reserve R --proxy-days D --expected-sha256 HASH] --root PROJECT [--parent ATTEMPT]."""
import argparse
import json
from pathlib import Path
from .corrections import corrections_run
from .engine import PROVIDERS, RunConfig, Scenario, run_simulation
from .evidence import fetch_evidence
from .market import VINTAGE_MANIFEST_SHA256
from .pipeline import acquire_snapshot, audit_snapshot, replay_snapshot
from .reconcile import reconcile


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['acquire', 'evidence', 'audit', 'replay', 'reconcile', 'corrections',
                                            'simulate'])
    parser.add_argument('snapshot', nargs='?')
    parser.add_argument('evidence', nargs='?')
    parser.add_argument('--root', type=Path, default=Path('.'))
    parser.add_argument('--parent')
    parser.add_argument('--payable', type=Path)
    parser.add_argument('--corrections', type=Path)
    base = Scenario()
    parser.add_argument('--provider', choices=sorted(PROVIDERS))
    parser.add_argument('--start')
    parser.add_argument('--end')
    parser.add_argument('--cost', type=float, default=base.cost)
    parser.add_argument('--lag', type=int, default=base.lag)
    parser.add_argument('--reserve', type=float, default=base.reserve)
    parser.add_argument('--proxy-days', type=int, default=base.proxy_pay_days)
    parser.add_argument('--expected-sha256', default=VINTAGE_MANIFEST_SHA256)
    args = parser.parse_args(argv)
    root = args.root.resolve()
    if args.command == 'acquire':
        # Config and payable files are read inside the pipeline so unreadable inputs are journaled.
        print(acquire_snapshot(root, Path('configs/n1.json'), args.parent))
    elif args.command == 'evidence':
        print(fetch_evidence(root, Path('configs/n1_evidence.json'), args.parent))
    elif args.command == 'corrections':
        if not args.snapshot:
            parser.error('reconciliation snapshot required for corrections')
        print(corrections_run(root, root / args.snapshot, args.parent))
    elif args.command == 'simulate':
        if not (args.snapshot and args.provider and args.start and args.end):
            parser.error('derived snapshot, --provider, --start and --end required for simulate')
        scenario = Scenario(cost=args.cost, lag=args.lag, reserve=args.reserve, proxy_pay_days=args.proxy_days)
        config = RunConfig(args.start, args.end, scenario=scenario)
        print(run_simulation(root, root / args.snapshot, args.provider, config, args.parent, args.expected_sha256))
    else:
        if not args.snapshot:
            parser.error('snapshot required for audit/replay/reconcile')
        snapshot = root / args.snapshot
        if args.command == 'audit':
            # --payable and --corrections resolve against --root, like the snapshot paths.
            print(audit_snapshot(root, snapshot, args.parent, args.payable or {}, args.corrections or {}))
        elif args.command == 'reconcile':
            if not args.evidence:
                parser.error('evidence snapshot required for reconcile')
            print(reconcile(root, snapshot, root / args.evidence, args.parent, args.corrections or {}))
        else:
            print(json.dumps({'replay_equal':replay_snapshot(root,snapshot,args.parent)}))


if __name__ == '__main__':
    main()
