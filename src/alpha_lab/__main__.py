"""Usage: python -m alpha_lab {acquire,evidence,audit,replay,reconcile} [snapshot] [evidence] --root PROJECT."""
import argparse
import json
from pathlib import Path
from .evidence import fetch_evidence
from .pipeline import acquire_snapshot, audit_snapshot, replay_snapshot
from .reconcile import reconcile


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['acquire', 'evidence', 'audit', 'replay', 'reconcile'])
    parser.add_argument('snapshot', nargs='?')
    parser.add_argument('evidence', nargs='?')
    parser.add_argument('--root', type=Path, default=Path('.'))
    parser.add_argument('--parent')
    parser.add_argument('--payable', type=Path)
    args = parser.parse_args(argv)
    root = args.root.resolve()
    if args.command == 'acquire':
        print(acquire_snapshot(root, json.loads((root/'configs/n1.json').read_bytes()), args.parent))
    elif args.command == 'evidence':
        print(fetch_evidence(root, json.loads((root/'configs/n1_evidence.json').read_bytes()), args.parent))
    else:
        if not args.snapshot:
            parser.error('snapshot required for audit/replay/reconcile')
        snapshot = root / args.snapshot
        if args.command == 'audit':
            payable = json.loads(args.payable.read_bytes()) if args.payable else {}
            print(audit_snapshot(root, snapshot, args.parent, payable))
        elif args.command == 'reconcile':
            if not args.evidence:
                parser.error('evidence snapshot required for reconcile')
            print(reconcile(root, snapshot, root / args.evidence, args.parent))
        else:
            print(json.dumps({'replay_equal':replay_snapshot(root,snapshot,args.parent)}))


if __name__ == '__main__':
    main()
