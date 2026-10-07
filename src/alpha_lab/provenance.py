"""Immutable vintages and append-only run provenance."""
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path, PurePosixPath
import platform
import subprocess
import uuid


def canonical_bytes(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True,
                       separators=(',', ':'), allow_nan=False) + '\n').encode('utf-8')


def sha256(value):
    return hashlib.sha256(value).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def safe_name(name):
    p = PurePosixPath(name)
    if (not name or p.is_absolute() or '..' in p.parts or ':' in name
            or '\\' in name or str(p) != name
            or name in {'manifest.json', 'manifest.sha256'}):
        raise ValueError(f'unsafe/reserved snapshot path: {name}')
    return p


def freeze(root, files, metadata):
    root = Path(root)
    for name in files:
        safe_name(name)
    root.mkdir(parents=True, exist_ok=False)
    manifest = {'schema_version': 1, 'metadata': metadata, 'files': {}}
    for name, body in sorted(files.items()):
        dest = root / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        with dest.open('xb') as stream:
            stream.write(body)
        manifest['files'][name] = sha256(body)
    encoded = canonical_bytes(manifest)
    (root / 'manifest.json').write_bytes(encoded)
    (root / 'manifest.sha256').write_text(sha256(encoded) + '\n', encoding='ascii')
    return root


def verify(snapshot):
    snapshot = Path(snapshot)
    try:
        raw = (snapshot / 'manifest.json').read_bytes()
        if sha256(raw) != (snapshot / 'manifest.sha256').read_text().strip():
            raise ValueError('manifest hash mismatch')
        manifest = json.loads(raw)
        expected = set(manifest['files']) | {'manifest.json', 'manifest.sha256'}
        actual = {p.relative_to(snapshot).as_posix() for p in snapshot.rglob('*') if p.is_file()}
        if expected != actual:
            raise ValueError('snapshot file inventory mismatch')
        for name, digest in manifest['files'].items():
            safe_name(name)
            path = snapshot / name
            if not path.resolve().is_relative_to(snapshot.resolve()) or path.is_symlink():
                raise ValueError('snapshot path escapes root')
            if sha256(path.read_bytes()) != digest:
                raise ValueError(f'content hash mismatch: {name}')
        return manifest
    except (OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise ValueError(f'invalid snapshot: {exc}') from exc


def environment():
    packages = {d.metadata['Name']: d.version for d in importlib.metadata.distributions()}
    return {'python': platform.python_version(), 'platform': platform.platform(),
            'packages': dict(sorted(packages.items()))}


def git_state(root):
    def git(*args):
        return subprocess.run(['git', *args], cwd=root, capture_output=True, check=False).stdout
    head = git('rev-parse', '--verify', 'HEAD').decode().strip() or None
    status = git('status', '--porcelain', '-z')
    patch = git('diff', 'HEAD', '--binary') if head else b''
    untracked = git('ls-files', '--others', '--exclude-standard', '-z').split(b'\0')
    hashes = {}
    for name in untracked:
        if name:
            key = name.decode('utf-8')
            path = Path(root) / key
            if path.is_file():
                hashes[key] = sha256(path.read_bytes())
    return head, bool(status), sha256(patch + canonical_bytes(hashes)) if status else None


class Run:
    """Single-writer run journal. A crash leaves started for explicit recovery."""

    def __init__(self, root, purpose, config, parent=None, candidate_ids=None):
        self.root = Path(root)
        self.run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S') + '-' + uuid.uuid4().hex[:10]
        self.journal = self.root / 'experiments/EXPERIMENT_LOG.jsonl'
        self.journal.parent.mkdir(parents=True, exist_ok=True)
        env = environment()
        head, dirty, patch = git_state(self.root)
        self.base = dict(schema_version=1, run_id=self.run_id, attempt_id=self.run_id,
                         parent_attempt_id=parent, protocol_version='1.0', git_sha=head,
                         dirty_tree=dirty, dirty_patch_sha256=patch,
                         config_sha256=sha256(canonical_bytes(config)), data_sha256=None,
                         environment_manifest_sha256=sha256(canonical_bytes(env)), seed=None,
                         null_reasons={'seed': 'deterministic_data_pipeline', 'data_sha256': 'data_not_acquired',
                                       'git_sha': None if head else 'unborn_repository'},
                         purpose=purpose, candidate_ids=list(candidate_ids or []), universe=config.get('universe', []),
                         splits=config.get('splits', {}), output_paths=[], quality_warnings=[])
        self.done = False
        self.env = env
        self.config = config

    def emit(self, event, **fields):
        row = self.base | dict(event=event, status=event, created_at_utc=now()) | fields
        with self.journal.open('ab') as stream:
            stream.write(canonical_bytes(row))
            stream.flush()
            os.fsync(stream.fileno())

    def __enter__(self):
        self.emit('started', environment=self.env, config=self.config)
        return self

    def finish(self, status, outputs, data_hash, warnings):
        if self.done:
            raise ValueError('run already finished')
        self.base.update(data_sha256=data_hash, output_paths=outputs, quality_warnings=warnings)
        self.base['null_reasons']['data_sha256'] = None if data_hash else 'no_valid_snapshot'
        self.emit(status)
        self.done = True

    def __exit__(self, exc_type, exc, tb):
        if not self.done:
            self.emit('failed', error=f'{exc_type.__name__}: {exc}' if exc else 'finish not called')
        return False
