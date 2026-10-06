"""Usage: python -m alpha_lab {acquire,evidence,audit,replay,reconcile,corrections} [snapshot] [evidence]
--root PROJECT."""
import argparse
import json
from pathlib import Path
from .corrections import corrections_run
from .evidence import fetch_evidence
from .pipeline import acquire_snapshot, audit_snapshot, replay_snapshot
from .reconcile import reconcile


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['acquire', 'evidence', 'audit', 'replay', 'reconcile', 'corrections'])
    parser.add_argument('snapshot', nargs='?')
    parser.add_argument('evidence', nargs='?')
    parser.add_argument('--root', type=Path, default=Path('.'))
    parser.add_argument('--parent')
    parser.add_argument('--payable', type=Path)
    parser.add_argument('--corrections', type=Path)
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
