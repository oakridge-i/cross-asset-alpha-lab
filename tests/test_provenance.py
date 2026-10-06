"""Catch overwritten vintages, tampered files and unrecorded failed attempts."""
import json
import subprocess
import pytest
from alpha_lab import provenance as p


def test_canonical_order_and_reject_nan():
    assert p.canonical_bytes({'b': 2, 'a': 1}) == b'{"a":1,"b":2}\n'
    with pytest.raises(ValueError):
        p.canonical_bytes({'bad': float('nan')})


def test_freeze_verify_and_refuse_overwrite(tmp_path):
    target = tmp_path / 'vintage'
    p.freeze(target, {'raw/a.json': b'abc'}, {'source': 'synthetic'})
    manifest = p.verify(target)
    assert manifest['files']['raw/a.json'] == 'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'
    with pytest.raises(FileExistsError):
        p.freeze(target, {'raw/a.json': b'changed'}, {})
    assert (target / 'raw/a.json').read_bytes() == b'abc'


@pytest.mark.parametrize('mutation', ['alter', 'missing', 'extra', 'manifest'])
def test_verify_rejects_tampering(tmp_path, mutation):
    p.freeze(tmp_path / 's', {'a': b'abc'}, {})
    s = tmp_path / 's'
    if mutation == 'alter':
        (s / 'a').write_bytes(b'abd')
    elif mutation == 'missing':
        (s / 'a').unlink()
    elif mutation == 'extra':
        (s / 'extra').write_bytes(b'x')
    else:
        (s / 'manifest.json').write_bytes(b'{}')
    with pytest.raises(ValueError):
        p.verify(s)


@pytest.mark.parametrize('name', ['../escape', '/absolute', 'C:/escape', 'a\\b', 'manifest.json', 'manifest.sha256'])
def test_freeze_rejects_unsafe_or_reserved_names(tmp_path, name):
    with pytest.raises(ValueError):
        p.freeze(tmp_path / 's', {name: b'x'}, {})
    assert not (tmp_path / 'escape').exists()


@pytest.fixture
def repo(tmp_path):
    subprocess.run(['git', 'init', '-q', str(tmp_path)], check=True)
    (tmp_path / 'untracked.py').write_text('original')
    return tmp_path


def test_run_logs_success_and_untracked_code_hash(repo):
    with p.Run(repo, 'synthetic', {'universe': ['TEST'], 'splits': {}}, None) as run:
        run.finish('completed', ['output.json'], 'abc', [])
    rows = [json.loads(x) for x in (repo / 'experiments/EXPERIMENT_LOG.jsonl').read_text().splitlines()]
    assert [x['event'] for x in rows] == ['started', 'completed']
    assert rows[0]['run_id'] == rows[1]['run_id']
    assert rows[0]['dirty_tree'] is True
    assert rows[0]['dirty_patch_sha256']
    assert rows[0]['data_sha256'] is None
    assert rows[1]['data_sha256'] == 'abc'
    assert rows[1]['environment_manifest_sha256']
    assert rows[1]['candidate_ids'] == []


def test_run_keeps_failure_and_links_retry(repo):
    with pytest.raises(RuntimeError):
        with p.Run(repo, 'synthetic', {}, None) as run:
            first = run.run_id
            raise RuntimeError('broken fixture')
    with p.Run(repo, 'synthetic', {}, first):
        pass
    rows = [json.loads(x) for x in (repo / 'experiments/EXPERIMENT_LOG.jsonl').read_text().splitlines()]
    assert [x['event'] for x in rows] == ['started', 'failed', 'started', 'failed']
    assert rows[-1]['parent_attempt_id'] == first
    assert 'broken fixture' in rows[1]['error']
    assert 'finish' in rows[-1]['error']
