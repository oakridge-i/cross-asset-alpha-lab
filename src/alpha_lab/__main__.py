"""Usage: python -m alpha_lab {acquire,audit,replay} [snapshot] --root PROJECT."""
import argparse
import json
from pathlib import Path
from .pipeline import acquire_snapshot, audit_snapshot, replay_snapshot


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['acquire','audit','replay'])
    parser.add_argument('snapshot', nargs='?')
    parser.add_argument('--root', type=Path, default=Path('.'))
    parser.add_argument('--parent')
    parser.add_argument('--payable', type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    if args.command == 'acquire':
        print(acquire_snapshot(root, json.loads((root/'configs/n1.json').read_bytes()), args.parent))
    else:
        if not args.snapshot:
            parser.error('snapshot required for audit/replay')
        snapshot = root / args.snapshot
        if args.command == 'audit':
            payable = json.loads(args.payable.read_bytes()) if args.payable else {}
            print(audit_snapshot(root, snapshot, args.parent, payable))
        else:
            print(json.dumps({'replay_equal':replay_snapshot(root,snapshot,args.parent)}))


if __name__ == '__main__':
    main()
