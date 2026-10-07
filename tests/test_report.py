"""Journaled N3 benchmark report: five-run verification, frozen tables, rejections, CLI."""
from collections import namedtuple
import json
import shutil
import pytest
from n3_fixtures import benchmark_vintage
from alpha_lab import engine, provenance, report
from alpha_lab.__main__ import main
from alpha_lab.engine import RunConfig, Scenario, run_simulation
from alpha_lab.provenance import verify
from alpha_lab.report import BENCHMARKS, build_report, render_markdown
from test_engine_run import journal

START, END = '2008-12-31', '2009-03-31'
CLEAN = ('a' * 40, False, None)
Project = namedtuple('Project', 'root derived digest runs')


def simulate(root, derived, digest, name, config=None):
    return run_simulation(root, derived, name, config or RunConfig(START, END), expected_sha256=digest)


def build_project(root):
    mp = pytest.MonkeyPatch()
    mp.setattr(provenance, 'git_state', lambda r: CLEAN)
    try:
        derived, digest = benchmark_vintage(root)
        runs = {n: simulate(root, derived, digest, n) for n in BENCHMARKS}
    finally:
        mp.undo()
    return Project(root, derived, digest, runs)


@pytest.fixture(scope='module')
def template(tmp_path_factory):
    return build_project(tmp_path_factory.mktemp('template'))


@pytest.fixture(scope='module')
def twin(tmp_path_factory):
    return build_project(tmp_path_factory.mktemp('twin'))


def clone(source, dest, monkeypatch):
    """Private copy of a five-run project, with a clean git state."""
    shutil.copytree(source.root, dest)
    monkeypatch.setattr(provenance, 'git_state', lambda r: CLEAN)
    return Project(dest, dest / source.derived.relative_to(source.root), source.digest,
                   {n: dest / 'data/runs' / d.name for n, d in source.runs.items()})


@pytest.fixture
def project(template, tmp_path, monkeypatch, no_network):
    return clone(template, tmp_path / 'p', monkeypatch)


def make(p, names=BENCHMARKS, **kwargs):
    return build_report(p.root, [p.runs[n] for n in names], expected_sha256=p.digest, **kwargs)


def document_of(target):
    return json.loads((target / 'benchmarks.json').read_text(encoding='utf-8'))


def rewrite_journal(p, edit):
    path = p.root / 'experiments/EXPERIMENT_LOG.jsonl'
    rows = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]
    edit(rows)
    path.write_bytes(b''.join(provenance.canonical_bytes(r) for r in rows))


def edit_run(p, name, event, **changes):
    def edit(rows):
        for r in rows:
            if r['run_id'] == p.runs[name].name and r['event'] == event:
                r.update(changes)
    rewrite_journal(p, edit)


def reject(p, match, names=BENCHMARKS, runs=None):
    dirs = runs or [p.runs[n] for n in names]
    with pytest.raises(ValueError, match=match):
        build_report(p.root, dirs, expected_sha256=p.digest)
    assert [r['event'] for r in journal(p.root)][-2:] == ['started', 'failed']
    assert not (p.root / 'data/reports').exists()


def test_report_freezes_tables_without_run_ids(project):
    target = make(project)
    assert target.parent == project.root / 'data/reports'
    manifest = verify(target)
    assert set(manifest['files']) == {'benchmarks.json', 'benchmarks.md'}
    ids = [d.name for d in project.runs.values()] + [target.name]
    for name in manifest['files']:
        text = (target / name).read_text(encoding='utf-8')
        assert not any(i in text for i in ids) and 'data/' not in text and 'created_at' not in text
    document = document_of(target)
    assert list(document['benchmarks']) == list(BENCHMARKS)
    assert document['window'] == {'start_session': START, 'end_session': END}
    assert document['scenario'] == {'cost': Scenario().cost, 'lag': Scenario().lag, 'reserve': Scenario().reserve,
                                    'proxy_pay_days': Scenario().proxy_pay_days}
    assert document['initial_cash'] == RunConfig(START, END).initial_cash
    assert all(d['schema_version'] == 1 for d in document['benchmarks'].values())
    assert (target / 'benchmarks.md').read_text(encoding='utf-8') == render_markdown(document)
    meta = manifest['metadata']
    assert meta['run_id'] == target.name and 'environment' in meta
    assert meta['sources'] == [{'candidate': n, 'run_id': project.runs[n].name,
                                'manifest_sha256': provenance.sha256((project.runs[n] / 'manifest.json').read_bytes())}
                               for n in BENCHMARKS]
    started, completed = journal(project.root)[-2:]
    assert (started['event'], completed['event']) == ('started', 'completed')
    assert completed['purpose'] == 'N3 benchmark report' and completed['candidate_ids'] == list(BENCHMARKS)
    assert started['config'] == {'runs': [f'data/runs/{project.runs[n].name}' for n in BENCHMARKS],
                                 'expected_sha256': project.digest}
    assert completed['output_paths'] == [f'data/reports/{target.name}']
    assert completed['data_sha256'] == provenance.sha256((target / 'manifest.json').read_bytes())


def test_markdown_tables_and_formats(project):
    document = document_of(make(project))
    text = render_markdown(document)
    full = document['benchmarks']['B0']['periods']['full']
    assert '## full' in text and '| B0 |' in text and '| REF_SPY |' in text
    assert f"{full['total_return'] * 100:.2f}%" in text and f"{full['costs_usd']:.2f}" in text
    assert f"{full['utility']:.3f}" in text
    assert '## Annual total_return' in text and '## Groups' in text
    assert render_markdown(json.loads(json.dumps(document))) == text
    document['benchmarks']['B1']['periods']['full']['sharpe_bil'] = None
    assert 'n/a' in render_markdown(document)


def test_report_is_reproducible(project, twin, tmp_path, monkeypatch):
    first = verify(make(project))
    again = verify(make(project))
    other = verify(make(clone(twin, tmp_path / 'q', monkeypatch)))
    assert first['files'] == again['files'] == other['files']
    assert first['metadata']['run_id'] != again['metadata']['run_id']
    assert first['metadata']['sources'] != other['metadata']['sources']


def test_report_rejects_failed_run(project, monkeypatch):
    real = engine.nav
    with monkeypatch.context() as m:
        m.setattr(engine, 'nav', lambda account, closes: real(account, closes) + 1.0)
        bad = simulate(project.root, project.derived, project.digest, 'B1')
    assert journal(project.root)[-1]['event'] == 'invariants_failed'
    reject(project, 'completed', runs=[project.runs['B0'], bad, *(project.runs[n] for n in BENCHMARKS[2:])])


def test_report_rejects_duplicate_and_wrong_count(project):
    reject(project, 'exactly once', runs=[project.runs[n] for n in ('B0', 'B1', 'B1', 'B3', 'REF_SPY')])
    reject(project, 'exactly five', names=BENCHMARKS[:4])


def test_report_rejects_run_outside_data_runs(project, tmp_path):
    elsewhere = tmp_path / 'elsewhere'
    shutil.copytree(project.runs['B0'], elsewhere)
    reject(project, 'outside', runs=[elsewhere, *(project.runs[n] for n in BENCHMARKS[1:])])


def test_report_rejects_dirty_tree_and_missing_git_sha(project):
    edit_run(project, 'B2', 'started', dirty_tree=True)
    reject(project, 'dirty')
    edit_run(project, 'B2', 'started', dirty_tree=False, git_sha=None)
    reject(project, 'git_sha')


def test_report_rejects_missing_terminal_record(project):
    rewrite_journal(project, lambda rows: rows.__setitem__(
        slice(None), [r for r in rows if not (r['run_id'] == project.runs['B3'].name and r['event'] != 'started')]))
    reject(project, 'terminal')


def test_report_rejects_output_path_or_data_hash_mismatch(project):
    edit_run(project, 'B0', 'completed', output_paths=['data/runs/other'])
    reject(project, 'output_paths')
    edit_run(project, 'B0', 'completed', output_paths=[f'data/runs/{project.runs["B0"].name}'], data_sha256='0' * 64)
    reject(project, 'data_sha256')


def test_report_rejects_mismatched_scenario_window_or_version(project, monkeypatch):
    runs = [project.runs[n] for n in BENCHMARKS]
    other = simulate(project.root, project.derived, project.digest, 'B3',
                     RunConfig(START, END, scenario=Scenario(cost=0.002)))
    reject(project, 'scenario', runs=[*runs[:3], other, runs[4]])
    shorter = simulate(project.root, project.derived, project.digest, 'B3', RunConfig(START, '2009-03-30'))
    reject(project, 'end_session', runs=[*runs[:3], shorter, runs[4]])
    monkeypatch.setitem(engine.PROVIDERS, 'B0', engine.PROVIDERS['B0']._replace(version='2'))
    reject(project, 'version', runs=runs)


def test_report_rejects_other_vintage_hash(project):
    with pytest.raises(ValueError, match='manifest'):
        build_report(project.root, [project.runs[n] for n in BENCHMARKS], expected_sha256='0' * 64)
    assert [r['event'] for r in journal(project.root)][-2:] == ['started', 'failed']


def test_report_rejects_tampered_config(project):
    path = project.runs['B2'] / 'config.json'
    path.write_bytes(path.read_bytes().replace(b'"lag"', b'"lag2"', 1))
    with pytest.raises(ValueError):
        verify(project.runs['B2'])
    reject(project, 'invalid snapshot|mismatch')


def test_report_rejects_tampered_journal_config(project):
    def edit(rows):
        for r in rows:
            if r['run_id'] == project.runs['B1'].name and r['event'] == 'started':
                r['config']['scenario']['cost'] = 0.5
    rewrite_journal(project, edit)
    reject(project, 'config_sha256')


def test_common_periods_must_agree():
    with pytest.raises(ValueError, match='periods'):
        report.common_periods({'B0': {'periods': {'full': {}}}, 'B1': {'periods': {'full': {}, '2009': {}}}})


def test_cli_report(project, capsys):
    argv = ['report', '--runs', *(f'data/runs/{project.runs[n].name}' for n in BENCHMARKS),
            '--root', str(project.root), '--expected-sha256', project.digest]
    main(argv)
    printed = capsys.readouterr().out.strip()
    assert printed.startswith('data/reports/') and '\\' not in printed
    assert set(verify(project.root / printed)['files']) == {'benchmarks.json', 'benchmarks.md'}
    main([*argv, '--parent', 'x'])
    assert journal(project.root)[-1]['parent_attempt_id'] == 'x'
