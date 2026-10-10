"""N5 evaluation on a miniature synthetic campaign: verification of the thirteen N5 runs (spec 7.1 items 1-5, D025 items
12, 16 and 17) with one rejection per rule and value-free messages; the selection-log checks (item 6), the comparisons,
annual differences and regressions against independent NumPy computations, the document whitelist, the journal, the
withheld computation errors and the command (spec 7.2-7.4, 8.3)."""
from collections import namedtuple
import csv
import io
import json
import math
import re
import shutil
import socket
import traceback
import numpy as np
import pandas as pd
import pytest
from n3_fixtures import benchmark_vintage
from alpha_lab import engine, evaluation, inference, provenance, report
from alpha_lab.adaptive import CANDIDATES, validation_segment
from alpha_lab.engine import RunConfig, run_simulation
from alpha_lab.features import xnys_month_end
from alpha_lab.market import load_market
from alpha_lab.metrics import PERIODS, WF_PERIODS
from alpha_lab.portfolio import GROUPS
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


# === Part 2: selection-log checks (spec 7.1 item 6), comparisons, regressions, document and command =================

PRIMARY = (('H1_252_3', 'B3'), ('H1_252_4', 'B3'), ('H1_126_3', 'B3'), ('H1_126_4', 'B3'), ('H2_4of6', 'H1_252_3'),
           ('H2_5of6', 'H1_252_3'))
SUPPLEMENTARY = (('H2_4of6', 'B3'), ('H2_5of6', 'B3'), ('H2_4of6', 'B2'), ('H2_5of6', 'B2'))
DOCUMENT_KEYS = ('window', 'scenario', 'initial_cash', 'manifest_sha256', 'provider_versions', 'metrics', 'comparisons',
                 'annual_differences', 'regressions', 'selection', 'disclosures')
MINI_YEARS = (2014,)
TIMESTAMP = re.compile(r'[0-9]{8}T[0-9]{6}')
WITHHELD = 'ValueError in the evaluation; message withheld under the N5 viewing procedure'


def test_part2_constants():
    assert evaluation.PRIMARY == PRIMARY
    assert evaluation.SUPPLEMENTARY == SUPPLEMENTARY
    assert evaluation.POLICY_COMPARISON == ('P_A1', 'H1_252_3_WF')
    assert evaluation.REPLICATES == 10000 and evaluation.SEED == 20261006
    assert evaluation.LENGTHS == (21, 63, 126) and evaluation.PRIMARY_LENGTH == 63
    assert evaluation.MINIMUM_EFFECT == 0.01
    assert evaluation.SELECTION_YEARS == tuple(range(2014, 2023))
    assert evaluation.WALK_FORWARD == ('2014-01-01', '2022-12-31')
    assert evaluation.DOCUMENT_KEYS == DOCUMENT_KEYS
    assert evaluation.REPORT_PURPOSE == 'N5 evaluation report'
    assert evaluation.REGRESSION_COMPARATOR == {'H1_252_3': 'B3', 'H1_252_4': 'B3', 'H1_126_3': 'B3', 'H1_126_4': 'B3',
                                                'H2_4of6': 'H1_252_3', 'H2_5of6': 'H1_252_3', 'P_A1': 'H1_252_3_WF'}
    assert len(evaluation.DISCLOSURES) == 9 and all(isinstance(s, str) and s for s in evaluation.DISCLOSURES)


# --- item 6: the selection log ------------------------------------------------------------------------------------

def policy_log(c):
    return json.loads((c.runs['P_A1'] / 'selection.json').read_bytes())


def reject_log(c, runs, log, where, values=()):
    with pytest.raises(ValueError) as info:
        evaluation.check_selection_log(log, runs)
    message = str(info.value)
    assert message.startswith('item 6'), message
    assert where in message, message
    value_free(c, message, values)
    for name in CANDIDATES:
        # The message never names a configuration, which would disclose a selection.
        assert name not in message, message
    assert info.value.__cause__ is None and (info.value.__context__ is None or info.value.__suppress_context__), message
    return message


def test_selection_log_accepts_the_campaign_log_and_a_fallback_with_a_warning(shared, monkeypatch):
    monkeypatch.setattr(evaluation, 'SELECTION_YEARS', MINI_YEARS)
    runs = verify_all(shared)
    log = policy_log(shared)
    assert [e['year'] for e in log] == [2014]
    assert evaluation.check_selection_log(log, runs) is None
    # A fallback entry (a utility is not finite) with its warning is accepted when the chosen is H1_252_3.
    assert log[0]['chosen'] == 'H1_252_3', 'the miniature selection is expected to be H1_252_3'
    entry = {**log[0], 'utility': {**log[0]['utility'], 'H1_126_4': None}, 'best_utility': None, 'close_set': [],
             'fallback': True, 'warning': 'non-finite utility for H1_126_4; fallback to H1_252_3'}
    assert evaluation.check_selection_log([entry], runs) is None


def test_selection_log_requires_the_nine_walk_forward_years(shared):
    runs = verify_all(shared)
    reject_log(shared, runs, policy_log(shared), 'P_A1')


def test_selection_log_rejections(shared, monkeypatch):
    monkeypatch.setattr(evaluation, 'SELECTION_YEARS', MINI_YEARS)
    runs = verify_all(shared)
    log = policy_log(shared)
    entry = log[0]
    u = entry['utility']
    start, end = validation_segment(2014)
    assert (entry['segment_start'], entry['segment_end'], entry['selection_date']) == (start, end, end)
    where = 'P_A1 selection year 2014'
    # Wrong segment date.
    reject_log(shared, runs, [{**entry, 'segment_start': '2011-12-29'}], where)
    reject_log(shared, runs, [{**entry, 'selection_date': '2013-12-30'}], where)
    # best_utility is not the maximum of the logged utilities.
    lowered = entry['best_utility'] - 0.5
    reject_log(shared, runs, [{**entry, 'best_utility': lowered}], where, values=(repr(lowered),))
    # A missing close-set member: a candidate outside the close set is moved inside the tolerance.
    outside = [c for c in CANDIDATES if c not in entry['close_set']]
    assert outside, 'the miniature log has a full close set'
    near = {**u, outside[-1]: entry['best_utility'] - 0.0005}
    reject_log(shared, runs, [{**entry, 'utility': near}], where)
    reject_log(shared, runs, [{**entry, 'close_set': entry['close_set'][:-1]}], where)
    # A chosen configuration that is not the first member of the close set in the preference order.
    other = next(c for c in CANDIDATES if c != entry['chosen'])
    message = reject_log(shared, runs, [{**entry, 'chosen': other}], where)
    assert 'first member' in message
    # A fallback without a warning.
    fallback = {**entry, 'utility': {**u, 'H1_126_4': None}, 'best_utility': None, 'close_set': [],
                'chosen': 'H1_252_3', 'fallback': True, 'warning': None}
    message = reject_log(shared, runs, [fallback], where)
    assert 'warning' in message
    reject_log(shared, runs, [{**fallback, 'warning': ''}], where)
    # A fallback whose chosen is not H1_252_3, and a non-finite utility without the fallback flag.
    reject_log(shared, runs, [{**fallback, 'warning': 'w', 'chosen': 'H1_126_3'}], where)
    reject_log(shared, runs, [{**entry, 'utility': {**u, 'H1_252_4': None}}], where)
    # Utility keys that are not the four candidates, a malformed entry, a wrong year and a repeated year.
    reject_log(shared, runs, [{**entry, 'utility': {k: v for k, v in u.items() if k != 'H1_126_4'}}], where)
    reject_log(shared, runs, [{k: v for k, v in entry.items() if k != 'warning'}], where)
    reject_log(shared, runs, [{**entry, 'year': 2015}], 'P_A1')
    reject_log(shared, runs, [entry, entry], 'P_A1')


def edit_csv(c, label, name, edit):
    text = (c.runs[label] / name).read_text(encoding='utf-8')
    rows = list(csv.reader(io.StringIO(text)))
    edit(rows)
    out = io.StringIO()
    csv.writer(out, lineterminator='\n').writerows(rows)
    refreeze(c, label, {name: out.getvalue().encode()})


def test_selection_log_rejects_a_year_mapping_or_weights_that_do_not_match(campaign, monkeypatch):
    monkeypatch.setattr(evaluation, 'SELECTION_YEARS', MINI_YEARS)
    log = policy_log(campaign)

    # A selection year in the signal rows that differs from the year of the decision's execution session.
    def year(rows):
        at = rows[0].index('selection_year')
        for row in rows[1:]:
            if row[0] == '2014-01-31':
                row[at] = '2015'
    edit_csv(campaign, 'P_A1', 'signals.csv', year)
    message = reject_log(campaign, verify_all(campaign), log, 'P_A1 decision 2014-01-31')
    assert 'selection_year' in message

    def restore(rows):
        at = rows[0].index('selection_year')
        for row in rows[1:]:
            row[at] = '2014'
    edit_csv(campaign, 'P_A1', 'signals.csv', restore)
    assert evaluation.check_selection_log(log, verify_all(campaign)) is None

    # Weights of a decision that do not match the chosen configuration's weights at that decision.
    def weights(rows):
        rows[1][1] = '0.123' if rows[1][1] != '0.123' else '0.124'
    edit_csv(campaign, 'P_A1', 'weights.csv', weights)
    message = reject_log(campaign, verify_all(campaign), log, 'P_A1 decision 2013-12-31', values=('0.123', '0.124'))
    assert 'weights.csv' in message


def test_selection_log_rejects_signal_rows_that_differ_from_the_chosen_configuration(campaign, monkeypatch):
    monkeypatch.setattr(evaluation, 'SELECTION_YEARS', MINI_YEARS)
    log = policy_log(campaign)

    def score(rows):
        rows[2][rows[0].index('score')] = '9.87654321'
    edit_csv(campaign, 'P_A1', 'signals.csv', score)
    message = reject_log(campaign, verify_all(campaign), log, 'P_A1 decision 2013-12-31', values=('9.87654321',))
    assert 'signal rows' in message


# --- the report ----------------------------------------------------------------------------------------------------

Built = namedtuple('Built', 'c target document markdown second')


def refuse_network(*args, **kwargs):
    raise AssertionError('test tried network access')


def patch_report(mp, c):
    """The miniature windows, references and selection years, a clean tree and one src tree."""
    mp.setattr(evaluation, 'FULL_WINDOW', FULL)
    mp.setattr(evaluation, 'WF_WINDOW', WF)
    mp.setattr(evaluation, 'REFERENCES', c.refs)
    mp.setattr(evaluation, 'SELECTION_YEARS', MINI_YEARS)
    mp.setattr(provenance, 'git_state', lambda r: CLEAN)
    mp.setattr(report, 'src_tree', lambda r, sha: SRC_TREE)


@pytest.fixture(scope='module')
def built(template, tmp_path_factory):
    """Two evaluation reports on one private copy of the campaign."""
    dest = tmp_path_factory.mktemp('built') / 'c'
    shutil.copytree(template.root, dest)
    c = Campaign(dest, dest / template.derived.relative_to(template.root), template.digest,
                 {k: dest / 'data/runs' / d.name for k, d in template.runs.items()}, template.refs)
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(socket.socket, 'connect', refuse_network)
        mp.setattr(socket, 'create_connection', refuse_network)
        patch_report(mp, c)
        first = evaluation.build_evaluation(c.root, dirs(c), expected_sha256=c.digest)
        second = evaluation.build_evaluation(c.root, dirs(c), expected_sha256=c.digest)
    document = json.loads((first / 'evaluation.json').read_bytes())
    return Built(c, first, document, (first / 'evaluation.md').read_text(encoding='utf-8'), second)


def independent_series(c, label):
    """(sessions, r, r_BIL) of the walk-forward period, from daily.csv and the vintage closes with NumPy."""
    market = load_market(c.root, c.derived, c.digest)
    rows = daily_rows(c, label)
    sessions = [s for s, _ in rows]
    nav = np.array([v for _, v in rows])
    r = nav[1:] / nav[:-1] - 1
    position = np.array([market.sessions.index(s) for s in sessions[1:]])
    close = market.close['BIL'].to_numpy()
    dividend = market.dividend['BIL'].to_numpy()
    ratio = market.split_ratio['BIL'].to_numpy()
    bil = ratio[position] * (close[position] + dividend[position]) / close[position - 1] - 1
    keep = np.array(['2014-01-01' <= s <= '2022-12-31' for s in sessions[1:]])
    return [s for s, k in zip(sessions[1:], keep) if k], r[keep], bil[keep]


def u_of(e):
    return 252 * np.mean(e) - 1.5 * 252 * np.var(e, ddof=1)


def entries(document, group):
    return {(e['candidate'], e['comparator']): e for e in document['comparisons'][group]}


def same_interval(have, expected):
    return (math.isclose(have['ci_low'], expected['ci_low'], rel_tol=0, abs_tol=1e-12)
            and math.isclose(have['ci_high'], expected['ci_high'], rel_tol=0, abs_tol=1e-12))


def test_comparison_values_against_an_independent_computation(built):
    c, document = built.c, built.document
    primary = entries(document, 'primary')
    supplementary = entries(document, 'supplementary')
    assert list(primary) == list(PRIMARY) and list(supplementary) == list(SUPPLEMENTARY)
    for candidate, comparator in (('H1_126_3', 'B3'), ('H2_5of6', 'H1_252_3'), ('H2_4of6', 'B2')):
        sc, rc, bil = independent_series(c, candidate)
        sk, rk, bil_k = independent_series(c, comparator)
        assert sc == sk and np.array_equal(bil, bil_k) and sc[0] == '2014-01-02' and sc[-1] == WF[1]
        delta = u_of(rc - bil) - u_of(rk - bil)
        mean_diff = 252 * (np.mean(rc - bil) - np.mean(rk - bil))
        entry = {**primary, **supplementary}[(candidate, comparator)]
        assert math.isclose(entry['delta_u'], delta, rel_tol=0, abs_tol=1e-12)
        assert math.isclose(entry['mean_excess_difference'], mean_diff, rel_tol=0, abs_tol=1e-12)
        assert entry['meets_minimum_effect'] == {'delta_u_at_least_minimum': bool(delta >= 0.01),
                                                 'mean_excess_difference_positive': bool(mean_diff > 0)}
        for length in (21, 63, 126):
            expected = inference.paired_bootstrap(rc, rk, bil, length, replicates=10000, seed=20261006)
            assert same_interval(entry['intervals'][str(length)], expected)
            assert entry['p_values'][str(length)] == expected['p']
    holm = inference.holm({f'{a} vs {b}': primary[(a, b)]['p_values']['63'] for a, b in PRIMARY})
    assert [primary[p]['holm_p'] for p in PRIMARY] == [holm[f'{a} vs {b}'] for a, b in PRIMARY]
    assert all('holm_p' not in e for e in supplementary.values())
    assert document['comparisons']['method'] == {'replicates': 10000, 'seed': 20261006, 'lengths': [21, 63, 126],
                                                 'primary_length': 63, 'holm_family_length': 63}


def test_policy_comparison_has_intervals_and_no_p_values(built):
    c, document = built.c, built.document
    [entry] = document['comparisons']['policy']
    assert (entry['candidate'], entry['comparator']) == ('P_A1', 'H1_252_3_WF')
    assert 'p_values' not in entry and 'holm_p' not in entry
    assert 'conditional on the realized selections' in entry['note']
    assert set(entry['intervals']) == {'21', '63', '126'}
    sc, rc, bil = independent_series(c, 'P_A1')
    sk, rk, _ = independent_series(c, 'H1_252_3_WF')
    # Both series start at 2014-01-02, based on the start session 2013-12-31.
    assert sc == sk and sc[0] == '2014-01-02'
    assert math.isclose(entry['delta_u'], u_of(rc - bil) - u_of(rk - bil), rel_tol=0, abs_tol=1e-12)
    assert same_interval(entry['intervals']['63'], inference.paired_bootstrap(rc, rk, bil, 63))


def test_annual_differences(built):
    c, document = built.c, built.document
    groups = document['annual_differences']
    assert [(e['candidate'], e['comparator']) for e in groups['primary']] == list(PRIMARY)
    assert [(e['candidate'], e['comparator']) for e in groups['supplementary']] == list(SUPPLEMENTARY)
    assert [(e['candidate'], e['comparator']) for e in groups['policy']] == [('P_A1', 'H1_252_3_WF')]
    for group, (candidate, comparator) in (('primary', ('H1_252_4', 'B3')), ('policy', ('P_A1', 'H1_252_3_WF'))):
        _, rc, _ = independent_series(c, candidate)
        _, rk, _ = independent_series(c, comparator)
        total = float(np.sum(rc - rk))
        entry = next(e for e in groups[group] if (e['candidate'], e['comparator']) == (candidate, comparator))
        assert list(entry['years']) == ['2014']
        assert math.isclose(entry['years']['2014'], total, rel_tol=0, abs_tol=1e-15)
        assert entry['positive_years'] == int(total > 0)
        assert entry['largest_positive_share'] == (1.0 if total > 0 else None)
    # Several years: sums 0.03, -0.01 and 0.01 give two positive years and a largest share of 0.75.
    sessions = ['2014-01-02', '2014-06-02', '2015-01-02', '2016-01-04', '2016-02-01']
    out = evaluation.annual_differences(sessions, np.array([0.02, 0.01, 0.0, 0.004, 0.006]),
                                        np.array([0.0, 0.0, 0.01, 0.0, 0.0]))
    assert list(out['years']) == ['2014', '2015', '2016'] and out['positive_years'] == 2
    assert [round(v, 12) for v in out['years'].values()] == [0.03, -0.01, 0.01]
    assert math.isclose(out['largest_positive_share'], 0.75, rel_tol=1e-12)
    none = evaluation.annual_differences(sessions[:1], np.array([0.0]), np.array([0.01]))
    assert none['positive_years'] == 0 and none['largest_positive_share'] is None


def test_regression_section_gates_short_samples(built):
    regressions = built.document['regressions']['candidates']
    assert list(regressions) == sorted(['H1_252_3', 'H1_252_4', 'H1_126_3', 'H1_126_4', 'H2_4of6', 'H2_5of6', 'P_A1'])
    for label, block in regressions.items():
        assert block['comparator'] == evaluation.REGRESSION_COMPARATOR[label]
        for model, k in (('model_a', 2), ('model_b', 5)):
            fit = block[model]
            # Two complete months (January and February 2014) in the miniature window: fewer than 36.
            assert fit['months'] == 2 and fit['k'] == k and fit['reason'] == 'months'
            assert fit['coefficients'] is None and fit['standard_errors'] is None
            assert fit['alpha'] is None and fit['se'] is None and fit['ci_low'] is None and fit['ci_high'] is None
        assert block['model_a']['regressors'] == ['intercept', block['comparator']]
        assert block['model_b']['regressors'] == ['intercept', *GROUPS]


def nw_reference(Z, u, lag):
    """Newey-West covariance by explicit loops, Bartlett weights and the factor n / (n - k)."""
    n, k = Z.shape
    meat = np.zeros((k, k))
    for t in range(n):
        meat += u[t] ** 2 * np.outer(Z[t], Z[t])
    for ell in range(1, lag + 1):
        w = 1 - ell / (lag + 1)
        for t in range(ell, n):
            g = u[t] * u[t - ell] * np.outer(Z[t], Z[t - ell])
            meat += w * (g + g.T)
    bread = np.linalg.inv(Z.T @ Z)
    return bread @ meat @ bread * n / (n - k)


def test_regression_block_against_an_independent_fit():
    rng = np.random.default_rng(5)
    X = rng.normal(0, 0.03, size=(48, 2))
    y = 0.002 + X @ np.array([0.5, -0.2]) + rng.normal(0, 0.01, 48)
    block = evaluation.regression_block(['a', 'b'], y, X)
    Z = np.column_stack([np.ones(48), X])
    coef = np.linalg.lstsq(Z, y, rcond=None)[0]
    se = np.sqrt(np.diag(nw_reference(Z, y - Z @ coef, 3)))
    assert block['regressors'] == ['intercept', 'a', 'b'] and block['months'] == 48 and block['k'] == 3
    assert block['rank'] == 3 and block['reason'] is None and math.isfinite(block['cond'])
    assert np.allclose(block['coefficients'], coef, rtol=0, atol=1e-12)
    assert np.allclose(block['standard_errors'], se, rtol=1e-9, atol=0)
    assert math.isclose(block['alpha'], 12 * coef[0], rel_tol=1e-12)
    assert math.isclose(block['se'], 12 * se[0], rel_tol=1e-9)
    assert math.isclose(block['ci_low'], 12 * coef[0] - 1.96 * 12 * se[0], rel_tol=1e-9)
    assert math.isclose(block['ci_high'], 12 * coef[0] + 1.96 * 12 * se[0], rel_tol=1e-9)
    # A duplicated regressor makes the design rank deficient: no alpha, the reason is reported.
    deficient = evaluation.regression_block(['a', 'a2'], y, np.column_stack([X[:, 0], X[:, 0]]))
    assert deficient['reason'] == 'rank' and deficient['alpha'] is None and deficient['coefficients'] is None
    assert deficient['cond'] is None or deficient['cond'] > 1e8


def test_document_has_only_whitelisted_keys_and_no_identifiers(built):
    c, document = built.c, built.document
    assert list(json.loads((built.target / 'evaluation.json').read_bytes())) == sorted(DOCUMENT_KEYS)
    assert set(provenance.verify(built.target)['files']) == {'evaluation.json', 'evaluation.md'}
    assert sorted(document['metrics']) == sorted(KEYS)
    for label in KEYS:
        assert document['metrics'][label] == json.loads((c.runs[label] / 'metrics.json').read_bytes())
    assert document['selection'] == policy_log(c)
    assert document['disclosures'] == list(evaluation.DISCLOSURES)
    assert document['provider_versions'] == {k: engine.PROVIDERS[PROVIDER[k]].version for k in KEYS}
    assert document['scenario'] == evaluation.SCENARIO and document['initial_cash'] == 100000.0
    assert document['manifest_sha256'] == c.digest
    texts = [(built.target / 'evaluation.json').read_text(encoding='utf-8'), built.markdown]
    ids = [*(d.name for d in c.runs.values()), *c.refs.values(), built.target.name, built.second.name]
    for text in texts:
        for value in ids:
            assert value not in text
        assert not TIMESTAMP.search(text)
        assert str(c.root) not in text and c.root.as_posix() not in text
        assert 'data/runs' not in text and 'data/reports' not in text and 'data\\' not in text
    metadata = provenance.verify(built.target)['metadata']
    assert [s['candidate'] for s in metadata['sources']] == list(KEYS)
    assert [s['run_id'] for s in metadata['sources']] == [c.runs[k].name for k in KEYS]
    assert all(s['manifest_sha256'] == provenance.sha256((c.runs[s['candidate']] / 'manifest.json').read_bytes())
               for s in metadata['sources'])
    assert metadata['run_id'] == built.target.name


def test_whitelist_is_enforced_before_freezing():
    document = {k: None for k in DOCUMENT_KEYS}
    assert evaluation.enforce_whitelist(document, b'{}', b'', ['abc']) is None
    with pytest.raises(ValueError, match='whitelist'):
        evaluation.enforce_whitelist({**document, 'run_id': 'x'}, b'{}', b'', ['abc'])
    with pytest.raises(ValueError, match='run id or a path'):
        evaluation.enforce_whitelist(document, b'{"a":"abc"}', b'', ['abc'])
    with pytest.raises(ValueError, match='run id or a path'):
        evaluation.enforce_whitelist(document, b'{}', b'| abc |', ['abc'])


def test_report_is_deterministic_and_journaled(built):
    c = built.c
    assert provenance.verify(built.target)['files'] == provenance.verify(built.second)['files']
    assert built.markdown == evaluation.render_markdown(built.document)
    for heading in ('T1', 'T2', 'T3', 'T4', 'T5', 'T6'):
        assert f'## {heading}' in built.markdown
    rows = [r for r in journal(c.root) if r['purpose'] == 'N5 evaluation report']
    for target in (built.target, built.second):
        mine = [r for r in rows if r['run_id'] == target.name]
        assert [r['event'] for r in mine] == ['started', 'completed']
        assert all(r['candidate_ids'] == list(KEYS) for r in mine)
        assert mine[1]['output_paths'] == [f'data/reports/{target.name}']
        assert mine[1]['data_sha256'] == provenance.sha256((target / 'manifest.json').read_bytes())
        # The paired bootstrap seed is the report's seed (D025 item 8), in the started and the terminal record.
        assert all(r['seed'] == 20261006 and r['null_reasons']['seed'] is None for r in mine)
    policy = [r for r in journal(c.root) if r['purpose'] == 'N5 policy run']
    assert policy and all(r['seed'] == 20261007 and r['null_reasons']['seed'] is None for r in policy)
    others = [r for r in journal(c.root) if r['purpose'] not in ('N5 evaluation report', 'N5 policy run')]
    assert others and all(r['seed'] is None and r['null_reasons']['seed'] == 'deterministic_data_pipeline'
                          for r in others)


def test_render_markdown_shows_gated_values_and_the_disclosures(built):
    text = evaluation.render_markdown(built.document)
    assert 'n/a' in text and 'months' in text
    for sentence in evaluation.DISCLOSURES:
        assert sentence in text


@pytest.fixture
def reportable(campaign, monkeypatch):
    patch_report(monkeypatch, campaign)
    return campaign


def evaluate_argv(c):
    return ['evaluate', '--runs', *(f'data/runs/{c.runs[k].name}' for k in KEYS), '--root', str(c.root),
            '--expected-sha256', c.digest]


def test_evaluation_errors_are_value_free(reportable, monkeypatch, capsys):
    from alpha_lab.__main__ import main
    c = reportable

    def boom(*args, **kwargs):
        raise ValueError('nav 12345.67')
    monkeypatch.setattr(inference, 'paired_bootstrap', boom)
    with pytest.raises(RuntimeError) as info:
        main(evaluate_argv(c))
    assert str(info.value) == WITHHELD
    assert info.value.__cause__ is None and info.value.__suppress_context__
    assert '12345.67' not in ''.join(traceback.format_exception(info.value))
    captured = capsys.readouterr()
    assert '12345.67' not in captured.out + captured.err
    last = journal(c.root)[-1]
    assert last['event'] == 'failed' and last['purpose'] == 'N5 evaluation report'
    assert last['error'] == f'RuntimeError: {WITHHELD}' and '12345.67' not in json.dumps(last)
    reports = c.root / 'data/reports'
    assert not reports.exists() or not any(reports.iterdir())


def test_verification_errors_keep_their_rule_and_run(reportable):
    c = reportable
    with pytest.raises(ValueError) as info:
        evaluation.build_evaluation(c.root, [c.runs[k] for k in KEYS if k != 'B1'], expected_sha256=c.digest)
    assert str(info.value).startswith('item 1, B1')
    assert journal(c.root)[-1]['event'] == 'failed'
    # The default selection years require nine log entries: item 6 rejects the miniature log.
    monkeypatch_years = pytest.MonkeyPatch()
    monkeypatch_years.setattr(evaluation, 'SELECTION_YEARS', tuple(range(2014, 2023)))
    try:
        with pytest.raises(ValueError) as info:
            evaluation.build_evaluation(c.root, dirs(c), expected_sha256=c.digest)
    finally:
        monkeypatch_years.undo()
    assert str(info.value).startswith('item 6, P_A1')


def test_cli_evaluate_prints_the_report_directory(reportable, capsys):
    from alpha_lab.__main__ import main
    c = reportable
    main(evaluate_argv(c))
    printed = capsys.readouterr().out.strip()
    assert printed.startswith('data/reports/') and '\\' not in printed
    assert set(provenance.verify(c.root / printed)['files']) == {'evaluation.json', 'evaluation.md'}
    main([*evaluate_argv(c), '--parent', 'x'])
    assert journal(c.root)[-1]['parent_attempt_id'] == 'x' and journal(c.root)[-1]['event'] == 'completed'
    with pytest.raises(SystemExit):
        main(['evaluate', '--root', str(c.root)])


# --- fix round 1 ---------------------------------------------------------------------------------------------------

def test_regression_interval_is_labeled_asymptotic(built):
    method = built.document['regressions']['method']
    assert method['interval'] == 'asymptotic normal, estimate +/- 1.96 standard errors'
    assert 'asymptotic normal, estimate +/- 1.96 standard errors' in built.markdown


def synthetic_month_ends(first='2013-12', months=48):
    year, month = int(first[:4]), int(first[5:])
    out = []
    for _ in range(months + 1):
        out.append(xnys_month_end(f'{year}-{month:02d}'))
        year, month = (year + 1, 1) if month == 12 else (year, month + 1)
    return out


def test_regression_inputs_and_an_ungated_fit_against_independent_values():
    """48 complete months from the December 2013 base: y, the Model A regressor and the four class proxies equal
    hand-computed month-end ratios, and the ungated fits equal an independent OLS."""
    rng = np.random.default_rng(11)
    ends = synthetic_month_ends()
    # Daily rows: each month-end plus one session in the middle of each month after the base (not a month-end).
    sessions = sorted([*ends, *(e[:8] + '15' for e in ends[1:])])
    tickers = ['BIL', *(t for members in GROUPS.values() for t in members)]
    tri = pd.DataFrame(np.cumprod(1 + rng.normal(0.003, 0.02, size=(len(sessions), len(tickers))), axis=0),
                       index=sessions, columns=tickers)
    navs = {label: np.cumprod(1 + rng.normal(0.004, 0.03, len(sessions))) * 100000 for label in KEYS}
    daily = {label: list(zip(sessions, map(float, navs[label]))) for label in KEYS}
    y, x_a, proxies = evaluation.regression_inputs('H1_252_4', daily['H1_252_4'], 'B3', daily['B3'], tri)
    at = [sessions.index(e) for e in ends]
    bil = tri['BIL'].to_numpy()[at]
    r_bil = bil[1:] / bil[:-1] - 1
    nav_c, nav_k = navs['H1_252_4'][at], navs['B3'][at]
    want_y = nav_c[1:] / nav_c[:-1] - 1 - r_bil
    want_x = nav_k[1:] / nav_k[:-1] - 1 - r_bil
    want_proxies = []
    for group, members in GROUPS.items():
        values = tri[list(members)].to_numpy()[at]
        want_proxies.append(np.mean(values[1:] / values[:-1] - 1 - r_bil[:, None], axis=1))
    assert list(y.index) == [e[:7] for e in ends[1:]] and y.index[0] == '2014-01' and len(y) == 48
    # The first month is based on the December 2013 month-end, not on a mid-month row.
    assert math.isclose(y.iloc[0], nav_c[1] / nav_c[0] - 1 - (bil[1] / bil[0] - 1), rel_tol=0, abs_tol=1e-15)
    assert np.allclose(y.to_numpy(), want_y, rtol=0, atol=1e-15)
    assert np.allclose(x_a.to_numpy(), want_x, rtol=0, atol=1e-15)
    assert list(proxies.columns) == list(GROUPS)
    for group, want in zip(GROUPS, want_proxies):
        assert np.allclose(proxies[group].to_numpy(), want, rtol=0, atol=1e-15)
    blocks = evaluation.regressions(daily, {sessions[-1]: tri})
    for model, Z in (('model_a', np.column_stack([np.ones(48), want_x])),
                     ('model_b', np.column_stack([np.ones(48), *want_proxies]))):
        coef = np.linalg.lstsq(Z, want_y, rcond=None)[0]
        block = blocks['H1_252_4'][model]
        assert block['months'] == 48 and block['reason'] is None and block['k'] == Z.shape[1]
        assert block['coefficients'] is not None and np.allclose(block['coefficients'], coef, rtol=0, atol=1e-12)
        assert block['standard_errors'] is not None and all(math.isfinite(v) for v in block['standard_errors'])
        assert math.isclose(block['alpha'], 12 * coef[0], rel_tol=1e-9)
    # The policy uses its comparator run, H2 the parent.
    assert blocks['P_A1']['model_a']['regressors'] == ['intercept', 'H1_252_3_WF']
    assert blocks['H2_4of6']['model_a']['regressors'] == ['intercept', 'H1_252_3']


def read_rows(c, label, name):
    return list(csv.reader(io.StringIO((c.runs[label] / name).read_text(encoding='utf-8'))))


def test_selection_log_uses_the_chosen_configuration_run(campaign, monkeypatch):
    """A consistent log that chooses H1_126_3: the policy rows are compared with the H1_126_3 run, so the rows of
    H1_252_3 are rejected and the rows of H1_126_3 are accepted."""
    monkeypatch.setattr(evaluation, 'SELECTION_YEARS', MINI_YEARS)
    entry = policy_log(campaign)[0]
    u = {**entry['utility'], 'H1_252_3': entry['utility']['H1_126_3'] - 0.01}
    best = max(u.values())
    close = [c for c in CANDIDATES if u[c] >= best - 0.001]
    assert close[0] == 'H1_126_3', 'the constructed log does not choose H1_126_3'
    log = [{**entry, 'utility': u, 'best_utility': best, 'close_set': close, 'chosen': 'H1_126_3'}]

    def relabel(rows):
        at = rows[0].index('selected_config')
        for row in rows[1:]:
            row[at] = 'H1_126_3'
    edit_csv(campaign, 'P_A1', 'signals.csv', relabel)
    start = WF[0]
    other = [r for r in read_rows(campaign, 'H1_126_3', 'signals.csv')[1:] if r[0] >= start]
    assert [r[:-2] for r in read_rows(campaign, 'P_A1', 'signals.csv')[1:]] != other, 'the fixture rows coincide'
    message = reject_log(campaign, verify_all(campaign), log, 'P_A1 decision')
    assert 'weights.csv' in message or 'signal rows' in message

    # The rows of H1_126_3 from the policy start on, with the two extra columns, are accepted.
    weights = [r for r in read_rows(campaign, 'H1_126_3', 'weights.csv')[1:] if r[0] >= start]
    edit_csv(campaign, 'P_A1', 'signals.csv', lambda rows: rows.__setitem__(
        slice(1, None), [[*r, '2014', 'H1_126_3'] for r in other]))
    edit_csv(campaign, 'P_A1', 'weights.csv', lambda rows: rows.__setitem__(slice(1, None), weights))
    assert evaluation.check_selection_log(log, verify_all(campaign)) is None


def test_selection_log_rejects_a_missing_policy_decision(campaign, monkeypatch):
    monkeypatch.setattr(evaluation, 'SELECTION_YEARS', MINI_YEARS)
    log = policy_log(campaign)

    def drop(rows):
        rows[1:] = [r for r in rows[1:] if r[0] != '2014-01-31']
    for name in ('decisions.csv', 'weights.csv', 'signals.csv'):
        edit_csv(campaign, 'P_A1', name, drop)
    message = reject_log(campaign, verify_all(campaign), log, 'P_A1 run files')
    assert 'decision sessions differ' in message


def test_withheld_passes_a_rule_error_with_its_message():
    with pytest.raises(evaluation.RuleError, match='^fixed text$'):
        with evaluation.withheld():
            raise evaluation.RuleError('fixed text')
    with pytest.raises(RuntimeError, match='^KeyError in the evaluation; message withheld') as info:
        with evaluation.withheld():
            raise KeyError('12345.67')
    assert '12345.67' not in ''.join(traceback.format_exception(info.value))


def test_a_rule_error_of_the_computation_is_raised_and_journaled(reportable, monkeypatch):
    c = reportable
    original = evaluation.bil_returns

    def short(market, last):
        out = original(market, last)
        out.pop(next(s for s in out if s >= '2014-01-01'))
        return out
    verify = evaluation.verified_n5_runs

    def verified_then_short(*args, **kwargs):
        # Verification (item 5) uses the full BIL series; the computation phase then sees one session less.
        runs = verify(*args, **kwargs)
        monkeypatch.setattr(evaluation, 'bil_returns', short)
        return runs
    monkeypatch.setattr(evaluation, 'verified_n5_runs', verified_then_short)
    expected = 'comparison H1_252_3 vs B3: BIL sessions differ from the run sessions'
    with pytest.raises(evaluation.RuleError) as info:
        evaluation.build_evaluation(c.root, dirs(c), expected_sha256=c.digest)
    assert str(info.value) == expected
    last = journal(c.root)[-1]
    assert last['event'] == 'failed' and last['error'] == f'RuleError: {expected}'


def test_whitelist_catches_the_json_escaped_root_path():
    document = {k: None for k in DOCUMENT_KEYS}
    root = 'C:\\Users\\x\\project'
    body = provenance.canonical_bytes({'a': root + '\\data'})
    assert root not in body.decode('utf-8') and json.dumps(root)[1:-1] in body.decode('utf-8')
    with pytest.raises(ValueError, match='run id or a path'):
        evaluation.enforce_whitelist(document, body, b'', [root])
    accented = 'C:\\Users\\\u0414\u043e\u043a'
    with pytest.raises(ValueError, match='run id or a path'):
        evaluation.enforce_whitelist(document, json.dumps({'a': accented}).encode(), b'', [accented])
