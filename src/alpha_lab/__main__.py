"""Usage: python -m alpha_lab {acquire,evidence,audit,replay,reconcile,corrections} [snapshot] [evidence]
--root PROJECT; python -m alpha_lab simulate DERIVED --provider NAME --start DATE --end DATE
[--cost C --lag L --reserve R --proxy-days D --expected-sha256 HASH] --root PROJECT [--parent ATTEMPT];
python -m alpha_lab {report,hypothesis-report} --runs DIR [DIR ...] --root PROJECT [--parent ATTEMPT]
[--expected-sha256 HASH].
Exit codes: 0 completed; 3 simulate finished with failed invariants or audit with failed QA; 1 exception; 2 usage."""
import argparse
import json
import sys
from pathlib import Path
from .corrections import corrections_run
from .engine import PROVIDERS, RunConfig, Scenario, run_simulation
from .evidence import fetch_evidence
from .hypothesis_report import build_hypothesis_report
from .market import VINTAGE_MANIFEST_SHA256
from .pipeline import acquire_snapshot, audit_snapshot, project_path, replay_snapshot
from .reconcile import reconcile
from .report import build_report

EXIT_CHECKS_FAILED = 3


def main(argv=None):
    # A console that cannot encode a path must not turn a finished run into a traceback.
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(errors='backslashreplace')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['acquire', 'evidence', 'audit', 'replay', 'reconcile', 'corrections',
                                            'simulate', 'report', 'hypothesis-report'])
    parser.add_argument('snapshot', nargs='?')
    parser.add_argument('evidence', nargs='?')
    parser.add_argument('--runs', nargs='+')
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
    elif args.command == 'report':
        if not args.runs:
            parser.error('--runs required for report')
        print(project_path(root, build_report(root, [Path(r) for r in args.runs], args.parent, args.expected_sha256)))
    elif args.command == 'hypothesis-report':
        if not args.runs:
            parser.error('--runs required for hypothesis-report')
        print(project_path(root, build_hypothesis_report(root, [Path(r) for r in args.runs], args.parent,
                                                         args.expected_sha256)))
    elif args.command == 'simulate':
        if not (args.snapshot and args.provider and args.start and args.end):
            parser.error('derived snapshot, --provider, --start and --end required for simulate')
        scenario = Scenario(cost=args.cost, lag=args.lag, reserve=args.reserve, proxy_pay_days=args.proxy_days)
        config = RunConfig(args.start, args.end, scenario=scenario)
        run_dir = run_simulation(root, root / args.snapshot, args.provider, config, args.parent, args.expected_sha256)
        print(project_path(root, run_dir))
        if not json.loads((run_dir / 'invariants.json').read_bytes())['passed']:
            raise SystemExit(EXIT_CHECKS_FAILED)
    else:
        if not args.snapshot:
            parser.error('snapshot required for audit/replay/reconcile')
        snapshot = root / args.snapshot
        if args.command == 'audit':
            # --payable and --corrections resolve against --root, like the snapshot paths.
            derived = audit_snapshot(root, snapshot, args.parent, args.payable or {}, args.corrections or {})
            print(derived)
            if not json.loads((Path(derived) / 'quality.json').read_bytes())['technical_pass']:
                raise SystemExit(EXIT_CHECKS_FAILED)
        elif args.command == 'reconcile':
            if not args.evidence:
                parser.error('evidence snapshot required for reconcile')
            print(reconcile(root, snapshot, root / args.evidence, args.parent, args.corrections or {}))
        else:
            print(json.dumps({'replay_equal':replay_snapshot(root,snapshot,args.parent)}))


if __name__ == '__main__':
    main()
