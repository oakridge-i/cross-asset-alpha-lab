"""N5 evaluation, part 1: verification of the thirteen N5 runs (spec 7.1 items 1-5, D025 items 12, 16 and 17) on a
miniature synthetic campaign, with one rejection per rule and value-free messages."""
from collections import namedtuple
import csv
import io
import json
import math
import re
import shutil
import pytest
from n3_fixtures import benchmark_vintage
from alpha_lab import engine, evaluation, provenance, report
from alpha_lab.engine import RunConfig, run_simulation
from alpha_lab.market import load_market
from alpha_lab.metrics import PERIODS, WF_PERIODS
from test_engine_run import journal
from test_report import CLEAN, SRC_TREE, edit_run, refreeze, rewrite_journal

FRAMES = {'start': '2007-12-03', 'end': '2014-03-31'}
FULL = ('2008-12-31', '2014-02-28')
WF = ('2013-12-31', '2014-02-28')
KEYS = ('B0', 'B1', 'B2', 'B3', 'REF_SPY', 'H1_252_3', 'H1_252_4', 'H1_126_3', 'H1_126_4', 'H2_4of6', 'H2_5of6',
        'P_A1', 'H1_252_3_WF')
BENCHMARKS = KEYS[:5]
CONFIGURATIONS = KEYS[5:11]
PROVIDER = {**{k: k for k in KEYS[:12]}, 'H1_252_3_WF': 'H1_252_3'}
WINDOW = {**{k: FULL for k in KEYS[:11]}, 'P_A1': WF, 'H1_252_3_WF': WF}
REAL_REFERENCES = {'B0': '20261007T180004-12aae80084', 'B1': '20261007T180018-b6c98bd0aa',
                   'B2': '20261007T180026-dffe07154c', 'B3': '20261007T180033-bba99392df',
                   'REF_SPY': '20261007T180039-be7dd8f43a', 'H1_252_3': '20261008T192727-e5e184b7db',
                   'H1_252_4': '20261008T192731-0f8d083cb0', 'H1_126_3': '20261008T192734-866ab4b3d7',
                   'H1_126_4': '20261008T192737-45e578bd7c', 'H2_4of6': '20261008T192740-f8be1b1ad3',
                   'H2_5of6': '20261008T192745-708215766a'}
OTHER_TREE = 'c' * 40
OTHER_SHA = 'd' * 40
Campaign = namedtuple('Campaign', 'root derived digest runs refs')
# A float-looking token: digits with a decimal point or an exponent.
FLOAT = re.compile(r'[0-9]*\.[0-9]+|[0-9]+\.[0-9]*|[0-9]+[eE][-+]?[0-9]+')
HEX = re.compile(r'[0-9a-f]{16,}')


def build_campaign(root):
    """Thirteen stage-5 runs and eleven reference runs (stage None) of the same code on one synthetic vintage."""
    mp = pytest.MonkeyPatch()
    mp.setattr(provenance, 'git_state', lambda r: CLEAN)
    mp.setattr(report, 'src_tree', lambda r, sha: SRC_TREE)
    try:
        derived, digest = benchmark_vintage(root, **FRAMES)
        runs = {k: run_simulation(root, derived, PROVIDER[k], RunConfig(*WINDOW[k]), expected_sha256=digest,
                                  stage=5) for k in KEYS}
        refs = {k: run_simulation(root, derived, k, RunConfig(*FULL), expected_sha256=digest).name
                for k in KEYS[:11]}
    finally:
        mp.undo()
    return Campaign(root, derived, digest, runs, refs)


@pytest.fixture(scope='module')
def template(tmp_path_factory):
    return build_campaign(tmp_path_factory.mktemp('campaign'))


def synthetic_windows(monkeypatch):
    monkeypatch.setattr(evaluation, 'FULL_WINDOW', FULL)
    monkeypatch.setattr(evaluation, 'WF_WINDOW', WF)


@pytest.fixture
def shared(template, monkeypatch, no_network):
    """The module campaign itself, for tests that do not modify it."""
    synthetic_windows(monkeypatch)
    monkeypatch.setattr(report, 'src_tree', lambda r, sha: SRC_TREE)
    return template


@pytest.fixture
def campaign(template, tmp_path, monkeypatch, no_network):
    """A private copy of the campaign, for tests that tamper with it."""
    synthetic_windows(monkeypatch)
    dest = tmp_path / 'c'
    shutil.copytree(template.root, dest)
    monkeypatch.setattr(provenance, 'git_state', lambda r: CLEAN)
    monkeypatch.setattr(report, 'src_tree', lambda r, sha: OTHER_TREE if sha == OTHER_SHA else SRC_TREE)
    return Campaign(dest, dest / template.derived.relative_to(template.root), template.digest,
                    {k: dest / 'data/runs' / d.name for k, d in template.runs.items()}, template.refs)


def dirs(c, replace=None):
    return [(replace or {}).get(k, c.runs[k]) for k in KEYS]


def base_of(c):
    first = next(r for r in journal(c.root) if r.get('run_id') == c.runs['B0'].name)
    return {'git_sha': CLEAN[0], 'environment_manifest_sha256': first['environment_manifest_sha256']}


def verify_all(c, runs=None, references=None, base=None):
    return evaluation.verified_n5_runs(c.root, dirs(c) if runs is None else runs, c.digest, base or base_of(c),
                                       references=c.refs if references is None else references)


def value_free(c, message, values=()):
    """No tampered value, hash or float-looking token once run ids, labels, period names and file names are removed."""
    for value in values:
        assert str(value) not in message, message
    text = message
    names = [*(d.name for d in c.runs.values()), *c.refs.values(), *KEYS, *(p for p, _, _ in PERIODS + WF_PERIODS)]
    for name in sorted(names, key=len, reverse=True):
        text = text.replace(name, ' ')
    assert not FLOAT.search(text), message
    assert not HEX.search(text), message


def reject(c, item, where, runs=None, references=None, values=(), base=None):
    with pytest.raises(ValueError) as info:
        verify_all(c, runs, references, base)
    message = str(info.value)
    assert message.startswith(f'item {item}'), message
    assert where in message, message
    value_free(c, message, values)
    assert info.value.__cause__ is None and (info.value.__context__ is None or info.value.__suppress_context__), message
    return message


def edit_config(c, label, **changes):
    """Edit config.json and the journaled config of a run consistently; the run is re-frozen."""
    path = c.runs[label] / 'config.json'
    config = {**json.loads(path.read_bytes()), **changes}
    refreeze(c, label, {'config.json': provenance.canonical_bytes(config)})

    def edit(rows):
        for r in rows:
            if r['run_id'] == c.runs[label].name and r['event'] == 'started':
                r['config'] = {**r['config'], **changes}
                r['config_sha256'] = provenance.sha256(provenance.canonical_bytes(r['config']))
    rewrite_journal(c, edit)


def edit_json(c, label, name, edit):
    document = json.loads((c.runs[label] / name).read_bytes())
    edit(document)
    refreeze(c, label, {name: provenance.canonical_bytes(document)})


# --- constants -----------------------------------------------------------------------------------------------------

def test_constants():
    assert evaluation.KEYS == KEYS
    assert evaluation.REFERENCES == REAL_REFERENCES
    assert evaluation.FULL_WINDOW == ('2008-12-31', '2022-12-30')
    assert evaluation.WF_WINDOW == ('2013-12-31', '2022-12-30')
    assert evaluation.METRICS_TOLERANCE == 1e-7
    assert evaluation.Run._fields == ('path', 'manifest', 'config', 'metrics')


# --- acceptance ----------------------------------------------------------------------------------------------------

def test_accepts_a_complete_consistent_set(shared):
    before = (shared.root / 'experiments/EXPERIMENT_LOG.jsonl').read_bytes()
    runs = verify_all(shared)
    assert list(runs) == list(KEYS)
    for label, run in runs.items():
        assert run.path == shared.runs[label].resolve()
        assert run.manifest == provenance.verify(shared.runs[label])
        assert run.config == json.loads((shared.runs[label] / 'config.json').read_bytes())
        assert run.metrics == json.loads((shared.runs[label] / 'metrics.json').read_bytes())
        assert run.config['provider']['name'] == PROVIDER[label]
        assert (run.config['start_session'], run.config['end_session']) == WINDOW[label]
    assert (shared.root / 'experiments/EXPERIMENT_LOG.jsonl').read_bytes() == before
    # The order of the directories does not matter.
    assert list(verify_all(shared, runs=list(reversed(dirs(shared))))) == list(KEYS)


def test_accepts_metrics_within_the_tolerance(campaign):
    def nudge(document):
        document['periods']['full']['utility'] += 5e-8
        document['periods']['2014']['total_return'] -= 5e-8
    edit_json(campaign, 'B2', 'metrics.json', nudge)
    # B2 metrics.json now differs from its N3 reference, so the identity check is given a matching reference.
    refs = {**campaign.refs, 'B2': campaign.runs['B2'].name}
    assert list(verify_all(campaign, references=refs)) == list(KEYS)


# --- item 1 --------------------------------------------------------------------------------------------------------

def test_rejects_a_missing_or_duplicated_run(campaign):
    reject(campaign, 1, 'H2_5of6', runs=[campaign.runs[k] for k in KEYS if k != 'H2_5of6'])
    reject(campaign, 1, 'H1_252_3_WF', runs=[campaign.runs[k] for k in KEYS if k != 'H1_252_3_WF'])
    reject(campaign, 1, 'B2', runs=[*dirs(campaign), campaign.runs['B2']])
    # A second H1_252_3 run over the full window replaces the walk-forward comparator.
    reject(campaign, 1, 'H1_252_3', runs=dirs(campaign, {'H1_252_3_WF': campaign.runs['H1_252_3']}))


def test_rejects_a_run_of_another_kind_or_outside_data_runs(campaign, tmp_path):
    # An N4 hypothesis run (nine files) where an N5 hypothesis run (ten files) is required.
    n4 = campaign.root / 'data/runs' / campaign.refs['H1_126_4']
    reject(campaign, 1, n4.name, runs=dirs(campaign, {'H1_126_4': n4}))
    elsewhere = tmp_path / 'elsewhere'
    shutil.copytree(campaign.runs['B0'], elsewhere)
    reject(campaign, 1, 'elsewhere', runs=dirs(campaign, {'B0': elsewhere}))


def test_rejects_a_modified_shared_file(campaign):
    path = campaign.runs['B1'] / 'weights.csv'
    body = bytearray(path.read_bytes())
    body[-2] = ord('7') if body[-2] != ord('7') else ord('8')
    path.write_bytes(bytes(body))
    with pytest.raises(ValueError):
        provenance.verify(campaign.runs['B1'])
    reject(campaign, 1, campaign.runs['B1'].name)


# --- item 2 --------------------------------------------------------------------------------------------------------

def test_rejects_a_dirty_or_not_completed_journal_record(campaign):
    edit_run(campaign, 'H1_252_4', 'started', dirty_tree=True)
    reject(campaign, 2, 'H1_252_4')
    edit_run(campaign, 'H1_252_4', 'started', dirty_tree=False)
    edit_run(campaign, 'H1_252_4', 'completed', git_sha=None)
    reject(campaign, 2, 'H1_252_4')
    edit_run(campaign, 'H1_252_4', 'completed', git_sha=CLEAN[0])

    def fail(rows):
        for r in rows:
            if r['run_id'] == campaign.runs['H1_252_4'].name and r['event'] == 'completed':
                r.update(event='invariants_failed', status='invariants_failed')
    rewrite_journal(campaign, fail)
    message = reject(campaign, 2, 'H1_252_4')
    assert 'invariants_failed' not in message and 'not completed' in message


def test_rejects_a_missing_terminal_record_or_output_mismatch(campaign):
    edit_run(campaign, 'P_A1', 'completed', output_paths=['data/runs/other'])
    reject(campaign, 2, 'P_A1')
    rewrite_journal(campaign, lambda rows: rows.__setitem__(
        slice(None), [r for r in rows if not (r['run_id'] == campaign.runs['P_A1'].name and r['event'] != 'started')]))
    reject(campaign, 2, 'P_A1')


def test_rejects_a_wrong_purpose(campaign):
    # The N3 reference run of B3 has the same nine files as the N5 run, but the N3 purpose.
    n3 = campaign.root / 'data/runs' / campaign.refs['B3']
    reject(campaign, 2, 'B3', runs=dirs(campaign, {'B3': n3}))
    edit_run(campaign, 'H1_126_3', 'started', purpose='N4 hypothesis run')
    reject(campaign, 2, 'H1_126_3')
    edit_run(campaign, 'H1_126_3', 'started', purpose='N5 hypothesis run')
    edit_run(campaign, 'H1_126_3', 'completed', purpose='N4 hypothesis run')
    reject(campaign, 2, 'H1_126_3')
    edit_run(campaign, 'H1_126_3', 'completed', purpose='N5 hypothesis run')
    edit_run(campaign, 'P_A1', 'started', candidate_ids=['H1_252_3'])
    reject(campaign, 2, 'P_A1')


# --- item 3 --------------------------------------------------------------------------------------------------------

def test_rejects_runs_on_different_source_trees(campaign):
    edit_run(campaign, 'H2_4of6', 'started', git_sha=OTHER_SHA)
    edit_run(campaign, 'H2_4of6', 'completed', git_sha=OTHER_SHA)
    message = reject(campaign, 3, 'H2_4of6', values=(OTHER_SHA, OTHER_TREE, SRC_TREE))
    assert 'src tree' in message
    # The report commit itself on another tree rejects the first run checked.
    edit_run(campaign, 'H2_4of6', 'started', git_sha=CLEAN[0])
    edit_run(campaign, 'H2_4of6', 'completed', git_sha=CLEAN[0])
    reject(campaign, 3, 'B0', base={**base_of(campaign), 'git_sha': OTHER_SHA}, values=(OTHER_SHA,))


def test_rejects_an_unresolvable_git_sha_without_its_value(campaign, monkeypatch):
    def tree(root, sha):
        if sha == OTHER_SHA:
            raise ValueError(f'cannot resolve the src tree of {sha}')
        return SRC_TREE
    monkeypatch.setattr(report, 'src_tree', tree)
    edit_run(campaign, 'B1', 'started', git_sha=OTHER_SHA)
    edit_run(campaign, 'B1', 'completed', git_sha=OTHER_SHA)
    reject(campaign, 3, 'B1', values=(OTHER_SHA,))


def test_rejects_a_different_environment(campaign):
    edit_run(campaign, 'REF_SPY', 'started', environment_manifest_sha256='e' * 64)
    reject(campaign, 3, 'REF_SPY', values=('e' * 64,))


# --- item 4 --------------------------------------------------------------------------------------------------------

def test_rejects_wrong_windows(campaign):
    # A configuration run over the walk-forward window.
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(provenance, 'git_state', lambda r: CLEAN)
        short = run_simulation(campaign.root, campaign.derived, 'H1_126_3', RunConfig(*WF),
                               expected_sha256=campaign.digest, stage=5)
    reject(campaign, 4, 'H1_126_3', runs=dirs(campaign, {'H1_126_3': short}))
    # The policy run with the 2008 window.
    edit_config(campaign, 'P_A1', start_session=FULL[0])
    message = reject(campaign, 4, 'P_A1')
    assert 'start_session' in message


def test_rejects_a_wrong_scenario_cash_vintage_or_provider(campaign):
    edit_config(campaign, 'B0', initial_cash=100001.0)
    reject(campaign, 4, 'B0', values=('100001',))
    edit_config(campaign, 'B0', initial_cash=100000.0, scenario={'cost': 0.002, 'lag': 1, 'reserve': 0.01,
                                                                  'proxy_pay_days': 10})
    reject(campaign, 4, 'B0', values=('0.002',))
    edit_config(campaign, 'B0', scenario={'cost': 0.001, 'lag': 1, 'reserve': 0.01, 'proxy_pay_days': 10})
    assert list(verify_all(campaign, references={**campaign.refs, 'B0': campaign.runs['B0'].name})) == list(KEYS)
    with pytest.raises(ValueError) as info:
        evaluation.verified_n5_runs(campaign.root, dirs(campaign), '0' * 64, base_of(campaign),
                                    references=campaign.refs)
    assert str(info.value).startswith('item 4') and campaign.digest not in str(info.value)
    provider = journal_config(campaign, 'H2_5of6')['provider']
    edit_config(campaign, 'H2_5of6', provider={**provider, 'parameters': {**provider['parameters'], 'h': 4}})
    reject(campaign, 4, 'H2_5of6')


def journal_config(c, label):
    return next(r for r in journal(c.root) if r['run_id'] == c.runs[label].name and r['event'] == 'started')['config']


def test_rejects_a_provider_version_that_is_not_current(campaign, monkeypatch):
    monkeypatch.setitem(engine.PROVIDERS, 'H1_252_4', engine.PROVIDERS['H1_252_4']._replace(version='2'))
    reject(campaign, 4, 'H1_252_4')


@pytest.mark.parametrize('edit', [lambda d: d['costs'].update(passed=False), lambda d: d.update(passed=False),
                                  lambda d: d['nav_identity'].update(passed=1), lambda d: d.pop('cash_flow')])
def test_rejects_a_failed_invariant(campaign, edit):
    edit_json(campaign, 'H1_252_3_WF', 'invariants.json', edit)
    reject(campaign, 4, 'H1_252_3_WF')


# --- item 5 --------------------------------------------------------------------------------------------------------

def test_rejects_a_shared_file_that_differs_from_its_reference(campaign):
    text = (campaign.runs['H1_126_4'] / 'weights.csv').read_text(encoding='utf-8')
    rows = list(csv.reader(io.StringIO(text)))
    rows[1][1] = '0.25' if rows[1][1] != '0.25' else '0.24'
    out = io.StringIO()
    csv.writer(out, lineterminator='\n').writerows(rows)
    refreeze(campaign, 'H1_126_4', {'weights.csv': out.getvalue().encode()})
    message = reject(campaign, 5, 'H1_126_4')
    assert 'weights.csv' in message


def test_rejects_a_benchmark_metrics_file_that_differs_from_its_reference(campaign):
    edit_json(campaign, 'B1', 'metrics.json', lambda d: d['periods']['full'].update(decisions=0))
    message = reject(campaign, 5, 'B1')
    assert 'metrics.json' in message


def test_rejects_a_missing_or_mismatched_reference(campaign):
    reject(campaign, 5, 'H1_252_4', references={k: v for k, v in campaign.refs.items() if k != 'H1_252_4'})
    shutil.rmtree(campaign.root / 'data/runs' / campaign.refs['H2_4of6'])
    reject(campaign, 5, 'H2_4of6')
    # A reference of another configuration does not match file by file.
    reject(campaign, 5, 'H2_4of6', references={**campaign.refs, 'H2_4of6': campaign.refs['H2_5of6']})
    # A reference with a broken manifest fails, it is not skipped.
    ref = campaign.root / 'data/runs' / campaign.refs['H1_252_3']
    (ref / 'daily.csv').write_bytes((ref / 'daily.csv').read_bytes() + b'\n')
    reject(campaign, 5, 'H1_252_3')


@pytest.mark.parametrize('label, period, key, delta', [('H2_4of6', 'full', 'utility', 2e-7),
                                                       ('P_A1', 'walk_forward', 'utility', -2e-7),
                                                       ('H1_252_3_WF', '2014', 'total_return', 2e-7),
                                                       ('B3', '2009', 'total_return', -1e-6)])
def test_rejects_metrics_that_disagree_with_daily_csv(campaign, label, period, key, delta):
    original = json.loads((campaign.runs[label] / 'metrics.json').read_bytes())['periods'][period][key]
    tampered = original + delta
    edit_json(campaign, label, 'metrics.json', lambda d: d['periods'][period].update({key: tampered}))
    # A benchmark metrics.json is shared with its N3 reference, so the identity check gets a matching reference.
    refs = {**campaign.refs, label: campaign.runs[label].name} if label in BENCHMARKS else campaign.refs
    message = reject(campaign, 5, label, references=refs, values=(repr(tampered), repr(original)))
    assert period in message and key in message


def test_rejects_malformed_or_incomplete_metrics_without_values(campaign):
    edit_json(campaign, 'H1_252_3_WF', 'metrics.json', lambda d: d['periods']['2014'].update(utility='0.1234567'))
    reject(campaign, 5, 'H1_252_3_WF', values=('0.1234567',))
    edit_json(campaign, 'H1_252_3_WF', 'metrics.json', lambda d: d['periods'].pop('2014'))
    reject(campaign, 5, 'H1_252_3_WF')
    edit_json(campaign, 'P_A1', 'metrics.json', lambda d: d['periods'].update(full=d['periods']['walk_forward']))
    reject(campaign, 5, 'P_A1')


def test_rejects_a_malformed_daily_csv_without_its_text(campaign):
    path = campaign.runs['P_A1'] / 'daily.csv'
    lines = path.read_text(encoding='utf-8').split('\n')
    header = lines[0].split(',')
    fields = lines[3].split(',')
    fields[header.index('nav')] = '1x2.5'
    lines[3] = ','.join(fields)
    refreeze(campaign, 'P_A1', {'daily.csv': '\n'.join(lines).encode()})
    reject(campaign, 5, 'P_A1', values=('1x2.5',))


def test_recomputation_matches_an_independent_reference(shared):
    """The recomputed utility of one period equals a direct loop over daily.csv and the vintage closes."""
    market = load_market(shared.root, shared.derived, shared.digest)
    with (shared.runs['H1_252_3_WF'] / 'daily.csv').open(newline='', encoding='utf-8') as stream:
        daily = [(r['session'], float(r['nav'])) for r in csv.DictReader(stream)]
    close, dividend, ratio = market.close['BIL'], market.dividend['BIL'], market.split_ratio['BIL']
    excess = []
    for (_, before), (session, after) in zip(daily, daily[1:]):
        if not '2014-01-01' <= session <= '2014-12-31':
            continue
        prev = market.sessions[market.sessions.index(session) - 1]
        bil = ratio[session] * (close[session] + dividend[session]) / close[prev] - 1
        excess.append(after / before - 1 - bil)
    n = len(excess)
    mean = sum(excess) / n
    var = sum((x - mean) ** 2 for x in excess) / (n - 1)
    expected = 252 * mean - 1.5 * 252 * var
    stored = json.loads((shared.runs['H1_252_3_WF'] / 'metrics.json').read_bytes())['periods']['2014']['utility']
    assert math.isclose(evaluation.recomputed(market, daily_rows(shared, 'H1_252_3_WF'), '2014-01-01',
                                              '2014-12-31')['utility'], expected, rel_tol=0, abs_tol=1e-12)
    assert abs(stored - expected) <= 1e-7


def daily_rows(c, label):
    with (c.runs[label] / 'daily.csv').open(newline='', encoding='utf-8') as stream:
        return [(r['session'], float(r['nav'])) for r in csv.DictReader(stream)]
