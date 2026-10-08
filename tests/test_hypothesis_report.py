"""N4 hypothesis report (spec 6.2 and 7): verification items 1-7 with one rejection per rule, acceptance cases and
value-free parse errors, the permitted diagnostics, the frozen document and Markdown, and the CLI, on synthetic data."""
import csv
import io
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import pytest
from n2_fixtures import write_vintage
from n3_fixtures import RISKY, benchmark_frames
from alpha_lab import engine, hypotheses, hypothesis_report as hr, provenance, report
from alpha_lab.engine import RunConfig, Scenario, run_simulation
from test_engine_run import journal
from test_report import CLEAN, SRC_TREE, Project, clone, edit_run, refreeze, rewrite_journal

START, END = '2008-12-31', '2009-03-31'
SYNTHETIC_MONTHS = ('2008-12', '2009-02')
SESSIONS = ['2008-12-31', '2009-01-30', '2009-02-27']
HYPOTHESES = ('H1_252_3', 'H1_252_4', 'H1_126_3', 'H1_126_4', 'H2_4of6', 'H2_5of6')
NON_PARENT = ('H1_252_4', 'H1_126_3', 'H1_126_4')
GROUPS = {'Equity': ('SPY', 'EFA', 'EEM'), 'Treasury': ('IEF', 'TLT'), 'Credit': ('LQD', 'HYG'), 'Real': ('GLD', 'DBC')}
GROUP_OF = {t: g for g, members in GROUPS.items() for t in members}
TICKERS = sorted((*RISKY, 'BIL'))
WEIGHT_COLUMNS = ['decision_session', *(f'w_{t}' for t in TICKERS), 'usd']
# Equity momentum, a binding group cap, a binding volatility target and H2 filter removals in the window.
DRIFT = {'SPY': 0.0007, 'EFA': 0.002, 'GLD': 0.001, 'TLT': 0.001, 'LQD': 0.0006}
LOUD = ('EEM', 'SPY')
FALLING = {t: -0.003 for t in RISKY}
REAL_GIT_STATE = provenance.git_state


def amplify(frame, power):
    """Raise the price path to a power: the same direction of moves with power times the log volatility."""
    base = frame['close'].iloc[0]
    louder = base * (frame['close'] / base) ** power
    frame['open'] = frame['open'] * louder / frame['close']
    frame['close'] = louder


def simulate(root, derived, digest, name, config=None):
    return run_simulation(root, derived, name, config or RunConfig(START, END), expected_sha256=digest)


def build_project(root, drift, loud):
    mp = pytest.MonkeyPatch()
    mp.setattr(provenance, 'git_state', lambda r: CLEAN)
    mp.setattr(report, 'src_tree', lambda r, sha: SRC_TREE)
    try:
        frames = benchmark_frames(drift=drift)
        for t in loud:
            amplify(frames[t], 3)
        derived = write_vintage(root, frames)
        digest = provenance.sha256((derived / 'manifest.json').read_bytes())
        runs = {n: simulate(root, derived, digest, n) for n in HYPOTHESES}
    finally:
        mp.undo()
    return Project(root, derived, digest, runs)


@pytest.fixture(scope='module')
def template(tmp_path_factory):
    return build_project(tmp_path_factory.mktemp('template'), DRIFT, LOUD)


@pytest.fixture(scope='module')
def falling(tmp_path_factory):
    return build_project(tmp_path_factory.mktemp('falling'), FALLING, ())


def synthetic_window(monkeypatch):
    monkeypatch.setattr(hr, 'EXPECTED_END', END)
    monkeypatch.setattr(hr, 'DECISION_MONTHS', SYNTHETIC_MONTHS)


@pytest.fixture
def project(template, tmp_path, monkeypatch, no_network):
    synthetic_window(monkeypatch)
    return clone(template, tmp_path / 'p', monkeypatch)


@pytest.fixture
def empty(falling, tmp_path, monkeypatch, no_network):
    synthetic_window(monkeypatch)
    return clone(falling, tmp_path / 'e', monkeypatch)


def dirs(p, replace=None):
    return [(replace or {}).get(n, p.runs[n]) for n in HYPOTHESES]


def verify_runs(p, runs=None, expected_sha256=None):
    return hr.build_hypothesis_report(p.root, runs or dirs(p), expected_sha256=expected_sha256 or p.digest)


def verified(p, runs=None):
    """The verified RunFiles outside a Run, with the base of the runs' own started records."""
    first = next(r for r in journal(p.root) if r.get('run_id') == p.runs[HYPOTHESES[0]].name)
    base = {'git_sha': CLEAN[0], 'environment_manifest_sha256': first['environment_manifest_sha256']}
    return hr.verified_hypothesis_runs(p.root, runs or dirs(p), p.digest, base)


def reject(p, match, runs=None, expected_sha256=None):
    with pytest.raises(ValueError, match=match) as info:
        verify_runs(p, runs, expected_sha256)
    started, failed = journal(p.root)[-2:]
    assert (started['event'], failed['event']) == ('started', 'failed')
    assert failed['purpose'] == 'N4 hypothesis report' and failed['candidate_ids'] == list(HYPOTHESES)
    assert not (p.root / 'data/reports').exists()
    return str(info.value)


def failed_rules(message):
    found = re.match(r'failed checks \(([^)]*)\)', message)
    return set(found.group(1).split(', ')) if found else set()


def reject_rules(p, expected, runs=None):
    """Items 5-7: the run is rejected and the failed rules are exactly the expected ones."""
    message = reject(p, 'failed checks', runs)
    assert failed_rules(message) == set(expected), message
    return message


def accepted(p, runs=None):
    target = verify_runs(p, runs)
    assert journal(p.root)[-1]['event'] == 'completed'
    assert provenance.verify(target)
    return verified(p, runs)


# --- run file access and controlled edits ------------------------------------------------------------------------

def read_csv(p, name, file):
    with (p.runs[name] / file).open(newline='', encoding='utf-8') as stream:
        reader = csv.DictReader(stream)
        return reader.fieldnames, list(reader)


def rows(p, name, file='signals.csv'):
    return read_csv(p, name, file)[1]


def signal(p, name, session, ticker):
    return next(r for r in rows(p, name) if r['decision_session'] == session and r['ticker'] == ticker)


def weights_row(p, name, session):
    return next(r for r in rows(p, name, 'weights.csv') if r['decision_session'] == session)


def csv_bytes(header, body):
    out = io.StringIO()
    writer = csv.DictWriter(out, header, lineterminator='\n')
    writer.writeheader()
    writer.writerows(body)
    return out.getvalue().encode()


def tamper(p, name, edits):
    """Apply {file: edit(rows)} to a run's CSV files and re-freeze it; the journal follows the new manifest."""
    files = {}
    for file, edit in edits.items():
        header, body = read_csv(p, name, file)
        edit(body)
        files[file] = csv_bytes(header, body)
    refreeze(p, name, files)


def edit_decision(p, name, session, signals=None, weights=None, rebalance=False, copy=True):
    """Edit signal fields {ticker: {column: text}} and weights.csv fields of one decision. With copy, a changed signal
    weight is also written to w_<ticker>; with rebalance, w_BIL and usd are recomputed from the parsed values;
    explicit weights.csv values win."""
    signals, weights = signals or {}, weights or {}

    def edit_signals(body):
        for r in body:
            if r['decision_session'] == session and r['ticker'] in signals:
                r.update(signals[r['ticker']])

    def edit_weights(body):
        row = next(r for r in body if r['decision_session'] == session)
        if copy:
            row.update({f'w_{t}': change['weight'] for t, change in signals.items() if 'weight' in change})
        row.update({k: v for k, v in weights.items() if k != 'usd'})
        if rebalance and 'w_BIL' not in weights:
            row['w_BIL'] = repr(1 - math.fsum(float(row[f'w_{t}']) for t in RISKY))
        if rebalance:
            row['usd'] = repr(1 - math.fsum(float(row[c]) for c in WEIGHT_COLUMNS[1:-1]))
        row.update({k: v for k, v in weights.items() if k == 'usd'})

    tamper(p, name, {'signals.csv': edit_signals, 'weights.csv': edit_weights})


def equivalent(text):
    """The same number written with one more trailing zero."""
    mantissa, _, exponent = text.partition('e')
    mantissa += '0' if '.' in mantissa else '.0'
    return mantissa + ('e' + exponent if exponent else '')


def find(p, names, predicate):
    """First (name, session, ticker, row) of a signal row satisfying predicate(name, row)."""
    for name in names:
        for r in rows(p, name):
            if predicate(name, r):
                return name, r['decision_session'], r['ticker'], r
    raise AssertionError('no matching signal row in the synthetic template')


def group_weight(p, name, session, ticker):
    w = weights_row(p, name, session)
    return math.fsum(float(w[f'w_{t}']) for t in GROUPS[GROUP_OF[ticker]])


# --- constants and helpers ---------------------------------------------------------------------------------------

def test_constants_match_the_specification():
    assert hr.HYPOTHESES == HYPOTHESES
    assert hr.PARAMETERS == {'H1_252_3': {'lookback': 252, 'k': 3}, 'H1_252_4': {'lookback': 252, 'k': 4},
                             'H1_126_3': {'lookback': 126, 'k': 3}, 'H1_126_4': {'lookback': 126, 'k': 4},
                             'H2_4of6': {'h': 4, 'parent': 'H1_252_3'}, 'H2_5of6': {'h': 5, 'parent': 'H1_252_3'}}
    assert hr.K == {'H1_252_3': 3, 'H1_252_4': 4, 'H1_126_3': 3, 'H1_126_4': 4, 'H2_4of6': 3, 'H2_5of6': 3}
    assert hr.H == {'H2_4of6': 4, 'H2_5of6': 5}
    assert (hr.EXPECTED_START, hr.EXPECTED_END, hr.EXPECTED_CASH) == ('2008-12-31', '2022-12-30', 100000.0)
    assert hr.EXPECTED_SCENARIO == {'cost': 0.001, 'lag': 1, 'reserve': 0.01, 'proxy_pay_days': 10}
    assert hr.DECISION_MONTHS == ('2008-12', '2022-11')
    assert (hr.ABS_TOL, hr.REL_TOL) == (1e-9, 1e-8)
    assert hr.RUN_FILES == report.RUN_FILES - {'metrics.json'} | {'signals.csv'}


def test_expected_decisions_are_168_month_ends():
    decisions = hr.expected_decisions()
    assert len(decisions) == 168 and decisions[0] == '2008-12-31' and decisions[-1] == '2022-11-30'
    assert decisions[:3] == ['2008-12-31', '2009-01-30', '2009-02-27']
    assert len({d[:7] for d in decisions}) == 168
    following = hr._next_session()
    assert following['2008-12-31'] == '2009-01-02' and following['2022-11-30'] == '2022-12-01'


def test_close_rel():
    assert hr.close_rel(0.0, 0.0) and not hr.close_rel(0.0, 1e-300)
    assert hr.close_rel(1.0, 1.0 + 0.9e-8) and not hr.close_rel(1.0, 1.0 + 1.1e-8)
    assert hr.close_rel(-2.0, -2.0 * (1 + 0.9e-8)) and not hr.close_rel(1.0, -1.0)


@pytest.mark.parametrize('a,b', [(math.inf, math.inf), (-math.inf, -math.inf), (1.0, math.inf),
                                 (-1.0, -math.inf), (math.nan, 0.0)])
def test_close_rel_rejects_non_finite_operands(a, b):
    assert not hr.close_rel(a, b)


def test_report_rejects_overflowing_derived_score_as_item_5_score(empty):
    session, ticker = SESSIONS[1], 'DBC'
    for name in HYPOTHESES:
        edit = {'momentum': '-1', 'sigma': '1e-309', 'score': '-1'}
        edit_decision(empty, name, session, {ticker: edit})
    message = reject_rules(empty, {'item 5 score'})
    assert all(part in message for part in ('item 5 score', session, ticker))
    assert '1e-309' not in message and '-1' not in message


def test_report_collects_group_weight_fsum_overflow(empty):
    session = SESSIONS[1]
    edit_decision(empty, 'H1_126_3', session,
                  weights={'w_SPY': '1e308', 'w_EFA': '1e308', 'w_EEM': '1e308'})
    message = reject(empty, 'failed checks')
    assert 'item 5 group cap' in failed_rules(message)
    assert 'H1_126_3' in message and session in message and 'Equity' in message


def test_report_collects_q_sum_fsum_overflow(empty):
    session = SESSIONS[1]
    edit_decision(empty, 'H1_126_3', session,
                  {ticker: {'q': '1e308'} for ticker in RISKY})
    message = reject(empty, 'failed checks')
    assert 'item 5 q sum' in failed_rules(message)
    assert 'H1_126_3' in message and session in message


# --- acceptance ---------------------------------------------------------------------------------------------------

def test_report_accepts_the_template_with_permitted_columns_only(project):
    out = accepted(project)
    assert list(out) == list(HYPOTHESES)
    for name, files in out.items():
        assert files.path == project.runs[name]
        assert {tuple(r) for r in files.decisions} == {('decision_session', 'execution_session', 'turnover',
                                                        'buy_fill')}
        assert [r['decision_session'] for r in files.decisions] == SESSIONS
        assert {tuple(r) for r in files.orders} <= {('execution_session', 'status', 'cancel_reason')}
        assert {tuple(r) for r in files.trades} <= {('session', 'side')}
        assert {tuple(r) for r in files.payouts} <= {('ex_session', 'status', 'pay_basis')}
        assert len(files.signals) == 9 * len(SESSIONS) and len(files.weights) == len(SESSIONS)
        assert set(files.invariants) == {'passed', 'checks', 'split_events', 'proxy_payouts'}
        assert files.invariants['passed'] is True and len(files.invariants['checks']) == 7
        assert 'detail' not in json.dumps(files.invariants)
    # the template exercises a binding group cap, a binding volatility target and a rank beyond K = 3
    signals = [r for n in HYPOTHESES for r in rows(project, n)]
    assert any(r['scale'] != '1' for r in signals)
    assert any(r['selected'] == 'True' and float(r['v']) < min(float(r['q']), 0.25) - 1e-6 for r in signals)
    assert any(r['rank'] == '4' and r['selected'] == 'True' for r in rows(project, 'H1_126_4'))


def test_report_never_opens_daily_csv_as_text(project, monkeypatch):
    opened = []
    real = Path.open

    def spy(self, mode='r', *args, **kwargs):
        opened.append((self.name, mode))
        return real(self, mode, *args, **kwargs)
    monkeypatch.setattr(Path, 'open', spy)
    accepted(project)
    assert ('signals.csv', 'r') in opened
    assert not [o for o in opened if o[0] == 'daily.csv' and 'b' not in o[1]]


def test_report_accepts_empty_selection_with_full_bil(empty):
    out = accepted(empty)
    for name in HYPOTHESES:
        assert all(r['eligible'] == 'False' and r['selected'] == 'False' and r['rank'] == '' and r['weight'] == '0'
                   for r in rows(empty, name))
        assert {r['w_BIL'] for r in out[name].weights} == {'1'}


def test_report_accepts_h2_with_filtered_ticker(project):
    accepted(project)
    for name in hr.H:
        h2 = rows(project, name)
        assert any(r['selected'] == 'True' and r['filter_pass'] == 'False' and r['parent_weight'] != '0'
                   and r['weight'] == '0' for r in h2)
    assert any(r['selected'] == 'True' and r['filter_pass'] == 'True' for r in rows(project, 'H2_4of6'))


def test_report_accepts_exponent_notation_weights(project):
    """A volatility scale of 0.0002 on one decision: v stays capped(q) and every selected weight is below 1e-4."""
    name, session, _, _ = find(project, ('H1_126_4',), lambda n, r: r['selected'] == 'True')
    mine = [r for r in rows(project, name) if r['decision_session'] == session]
    weight = {r['ticker']: '%.10g' % (0.0002 * float(r['v'])) for r in mine}
    assert any('e-05' in weight[r['ticker']] for r in mine if r['selected'] == 'True')
    bil = '%.10g' % (1 - math.fsum(float(x) for x in weight.values()))
    usd = '%.10g' % (1 - math.fsum([*(float(x) for x in weight.values()), float(bil)]))
    edit_decision(project, name, session, {t: {'scale': '0.0002', 'weight': x} for t, x in weight.items()},
                  {'w_BIL': bil, 'usd': usd})
    accepted(project)


def test_report_accepts_rounding_edge_values(project):
    """score texts 1.5e-9 and a q text 2e-9 away (relative) from exact agreement, as %.10g rounding can produce."""
    session = SESSIONS[1]
    scores = {r['ticker']: {'score': repr(float(r['momentum']) / float(r['sigma']) * (1 + 1.5e-9))}
              for r in rows(project, 'H1_126_3') if r['decision_session'] == session}
    edit_decision(project, 'H1_126_3', session, scores)
    edit_decision(project, 'H1_126_4', session, scores)
    chosen = [r for r in rows(project, 'H1_126_4') if r['decision_session'] == session and r['selected'] == 'True']
    assert len(chosen) >= 2
    edit_decision(project, 'H1_126_4', session, {chosen[-1]['ticker']: {'q': repr(float(chosen[-1]['q']) * (1 + 2e-9))}})
    accepted(project)
    for name in ('H1_126_3', 'H1_126_4'):
        mine = [r for r in rows(project, name) if r['decision_session'] == session]
        assert all(abs(float(r['score']) / (float(r['momentum']) / float(r['sigma'])) - 1) > 1.4e-9 for r in mine)


# --- item 1 -------------------------------------------------------------------------------------------------------

def test_report_rejects_wrong_count(project):
    reject(project, 'item 1: exactly six', runs=dirs(project)[:5])
    reject(project, 'item 1: exactly six', runs=[*dirs(project), project.runs['H1_252_3']])


def test_report_rejects_benchmark_run_and_duplicate(project):
    reject(project, 'item 1: each of .* exactly once', runs=dirs(project, {'H1_252_4': project.runs['H1_252_3']}))
    b0 = simulate(project.root, project.derived, project.digest, 'B0')
    reject(project, 'item 1, .*not a hypothesis run', runs=dirs(project, {'H1_126_3': b0}))


def test_report_rejects_metrics_json(project):
    refreeze(project, 'H1_126_4', {'metrics.json': provenance.canonical_bytes({'schema_version': 1})})
    reject(project, 'item 1, .*not a hypothesis run')


def test_report_rejects_run_outside_data_runs(project, tmp_path):
    elsewhere = tmp_path / 'elsewhere'
    shutil.copytree(project.runs['H2_4of6'], elsewhere)
    reject(project, 'item 1, .*outside data/runs', runs=dirs(project, {'H2_4of6': elsewhere}))


# --- items 2 and 3 ------------------------------------------------------------------------------------------------

@pytest.mark.parametrize('event', ['started', 'completed'])
def test_report_rejects_dirty_tree(project, event):
    edit_run(project, 'H1_252_4', event, dirty_tree=True)
    reject(project, r'item 2-3, H1_252_4: .*dirty_tree')


@pytest.mark.parametrize('event', ['started', 'completed'])
def test_report_rejects_null_git_sha(project, event):
    edit_run(project, 'H2_5of6', event, git_sha=None)
    reject(project, r'item 2-3, H2_5of6: .*git_sha is null')


def test_report_rejects_failed_status(project, monkeypatch):
    real = engine.nav
    with monkeypatch.context() as m:
        m.setattr(engine, 'nav', lambda account, closes: real(account, closes) + 1.0)
        bad = simulate(project.root, project.derived, project.digest, 'H1_126_4')
    assert journal(project.root)[-1]['event'] == 'invariants_failed'
    message = reject(project, r'item 2-3, H1_126_4: .*not completed', runs=dirs(project, {'H1_126_4': bad}))
    assert message == f'item 2-3, H1_126_4: {bad.name}: run status is not completed'
    assert 'invariants_failed' not in journal(project.root)[-1]['error']


def test_report_withholds_a_crafted_terminal_status(project):
    crafted = 'status-0.123456789'
    edit_run(project, 'H2_4of6', 'completed', status=crafted)
    message = reject(project, r'item 2-3, H2_4of6: .*run status is not completed$')
    assert crafted not in message and crafted not in journal(project.root)[-1]['error']


def test_report_withholds_an_unresolvable_git_sha(project, monkeypatch):
    crafted = 'e' * 39 + 'f'

    def src_tree(root, sha):
        if sha != CLEAN[0]:
            raise ValueError(f'cannot resolve the src tree of {sha}')
        return SRC_TREE
    monkeypatch.setattr(report, 'src_tree', src_tree)
    edit_run(project, 'H1_126_3', 'started', git_sha=crafted)
    edit_run(project, 'H1_126_3', 'completed', git_sha=crafted)
    message = reject(project, rf'^item 3, H1_126_3: cannot resolve the src tree of {project.runs["H1_126_3"].name} '
                              r'git_sha$')
    assert crafted not in message and crafted not in journal(project.root)[-1]['error']


def git(root, *args):
    subprocess.run(['git', '-c', 'user.name=test', '-c', 'user.email=test@example.invalid', '-c',
                    'commit.gpgsign=false', '-c', 'core.autocrlf=false', *args], cwd=root, check=True,
                   capture_output=True)


def real_git(p, monkeypatch):
    """Commit the whole synthetic project to a fresh repository and let the report run read its real git state."""
    monkeypatch.setattr(provenance, 'git_state', REAL_GIT_STATE)
    (p.root / 'notes.txt').write_bytes(b'tracked\n')
    git(p.root, 'init', '-q')
    git(p.root, 'add', '-A')
    git(p.root, 'commit', '-q', '-m', 'synthetic project')


def test_report_accepts_a_clean_report_tree(project, monkeypatch):
    real_git(project, monkeypatch)
    verify_runs(project)
    started, completed = journal(project.root)[-2:]
    assert started['dirty_tree'] is False and started['git_sha'] and completed['event'] == 'completed'


def test_report_rejects_a_dirty_report_tree(project, monkeypatch):
    real_git(project, monkeypatch)
    (project.root / 'notes.txt').write_bytes(b'modified\n')
    message = reject(project, r'^item 3: the report tree is dirty$')
    assert journal(project.root)[-2]['dirty_tree'] is True
    assert journal(project.root)[-1]['error'] == f'ValueError: {message}'


@pytest.mark.parametrize('event', ['started', 'completed'])
@pytest.mark.parametrize('changes', [{'purpose': 'N3 benchmark run'}, {'candidate_ids': ['H1_252_3']}])
def test_report_rejects_purpose_or_candidates_in_either_record(project, event, changes):
    edit_run(project, 'H1_126_3', event, **changes)
    reject(project, r'item 2-3, H1_126_3: .*purpose or candidate_ids')


def test_report_rejects_journaled_parameters_differing_from_config(project):
    def edit(body):
        for r in body:
            if r['run_id'] == project.runs['H2_4of6'].name and r['event'] == 'started':
                r['config']['provider']['parameters'] = {'h': 5, 'parent': 'H1_252_3'}
                r['config_sha256'] = provenance.sha256(provenance.canonical_bytes(r['config']))
    rewrite_journal(project, edit)
    reject(project, r'item 2-3, H2_4of6: .*journaled provider differs from config.json')


def test_report_rejects_environment_mismatch(project):
    edit_run(project, 'H1_252_3', 'started', environment_manifest_sha256='0' * 64)
    reject(project, r'item 2-3, H1_252_3: .*environment differs')


def test_report_rejects_src_tree_mismatch(project, monkeypatch):
    edit_run(project, 'H1_252_4', 'started', git_sha='d' * 40)
    monkeypatch.setattr(report, 'src_tree', lambda root, sha: SRC_TREE if sha == CLEAN[0] else 'c' * 40)
    reject(project, r'item 3, H1_252_4: .*src tree differs')


# --- item 4 -------------------------------------------------------------------------------------------------------

def test_report_rejects_failed_invariants(project):
    path = project.runs['H1_126_3'] / 'invariants.json'
    refreeze(project, 'H1_126_3', {'invariants.json': provenance.canonical_bytes(
        {**json.loads(path.read_bytes()), 'passed': False})})
    reject(project, r'item 4, H1_126_3: invariants did not pass')


def edit_invariants(p, name, edit):
    data = json.loads((p.runs[name] / 'invariants.json').read_bytes())
    edit(data)
    refreeze(p, name, {'invariants.json': provenance.canonical_bytes(data)})


@pytest.mark.parametrize('value', [False, 1, 'true', None])
def test_report_rejects_individual_invariant_flag_not_true(project, value):
    """A false or non-boolean flag of one check under an overall true flag; the message names the check only."""
    edit_invariants(project, 'H1_126_3', lambda d: d['costs'].update(passed=value))
    assert json.loads((project.runs['H1_126_3'] / 'invariants.json').read_bytes())['passed'] is True
    message = reject(project, r'item 4, H1_126_3: invariants.json check costs did not pass')
    assert message == 'item 4, H1_126_3: invariants.json check costs did not pass'
    assert journal(project.root)[-1]['error'] == f'ValueError: {message}'


def test_check_config_rejects_individual_invariant_flag(project):
    name = 'H1_252_4'
    manifest = json.loads((project.runs[name] / 'manifest.json').read_bytes())
    config = json.loads((project.runs[name] / 'config.json').read_bytes())
    invariants = json.loads((project.runs[name] / 'invariants.json').read_bytes())
    hr._check_config(name, manifest, config, invariants, project.digest)
    invariants['nav_identity']['passed'] = False
    with pytest.raises(ValueError, match='^invariants.json check nav_identity did not pass$'):
        hr._check_config(name, manifest, config, invariants, project.digest)


@pytest.mark.parametrize('value', [1, 'true', None])
def test_report_rejects_non_boolean_overall_flag(project, value):
    edit_invariants(project, 'H2_5of6', lambda d: d.update(passed=value))
    reject(project, r'^item 4, H2_5of6: invariants did not pass$')


def test_report_rejects_missing_invariant_check(project):
    edit_invariants(project, 'H1_252_3', lambda d: d.pop('execution_timing'))
    reject(project, r'^item 4, H1_252_3: invariants.json lacks the check execution_timing$')


def test_report_rejects_extra_invariant_check(project):
    edit_invariants(project, 'H1_252_3', lambda d: d.update(margin={'passed': True, 'detail': []}))
    reject(project, r'^item 4, H1_252_3: invariants.json holds the unexpected check margin$')


def test_report_rejects_stale_version(project, monkeypatch):
    monkeypatch.setitem(engine.PROVIDERS, 'H2_5of6', engine.PROVIDERS['H2_5of6']._replace(version='2'))
    reject(project, r'item 4, H2_5of6: provider version is not current')


def test_report_rejects_other_vintage_hash(project):
    reject(project, r'item 4, H1_252_3: vintage manifest hash', expected_sha256='0' * 64)
    refreeze(project, 'H1_126_3', metadata={'derived_manifest_sha256': '0' * 64})
    reject(project, r'item 4, H1_126_3: vintage manifest hash')


def rotated_parameters(monkeypatch):
    for name, other in zip(HYPOTHESES, (*HYPOTHESES[1:], HYPOTHESES[0])):
        monkeypatch.setitem(engine.PROVIDERS, name, engine.PROVIDERS[name]._replace(
            parameters=hr.PARAMETERS[other]))


@pytest.mark.parametrize('config, match', [
    (RunConfig(START, '2009-02-27'), 'end_session'),
    (RunConfig(START, END, scenario=Scenario(cost=0.002)), 'scenario'),
    (RunConfig(START, END, initial_cash=50000.0), 'initial_cash'),
    (RunConfig('2009-01-02', END), 'start_session'),
    (RunConfig(START, END, decision_sessions=tuple(SESSIONS)), 'decision_sessions'),
    (None, 'provider parameters')])
def test_report_rejects_consistent_but_wrong_configuration(project, monkeypatch, config, match):
    if config is None:
        rotated_parameters(monkeypatch)
    runs = {n: simulate(project.root, project.derived, project.digest, n, config) for n in HYPOTHESES}
    reject(project, rf'item 4, H1_252_3: config.json {match} (is|are) not', runs=[runs[n] for n in HYPOTHESES])


@pytest.mark.parametrize('months, match', [(('2008-12', '2009-03'), 'missing 2009-03-31'),
                                           (('2009-01', '2009-02'), 'unexpected 2008-12-31')])
def test_report_rejects_missing_or_extra_decision(project, monkeypatch, months, match):
    monkeypatch.setattr(hr, 'DECISION_MONTHS', months)
    reject(project, rf'item 4, H1_252_3: decisions.csv decision sessions .*{match}')


def test_report_rejects_decision_dates_differing_across_files(project):
    def shift(body):
        for r in body:
            if r['decision_session'] == '2009-01-30':
                r['decision_session'] = '2009-01-29'
    tamper(project, 'H1_126_4', {'weights.csv': shift})
    reject(project, r'item 4, H1_126_4: weights.csv decision sessions .*missing 2009-01-30')


def test_report_rejects_signal_dates_differing_across_files(project):
    def shift(body):
        for r in body:
            if r['decision_session'] == '2009-02-27':
                r['decision_session'] = '2009-02-26'
    tamper(project, 'H2_4of6', {'signals.csv': shift})
    reject(project, r'item 4, H2_4of6: signals.csv decision sessions .*missing 2009-02-27')


def test_report_rejects_repeated_decision_row(project):
    tamper(project, 'H1_252_4', {'decisions.csv': lambda body: body.insert(1, dict(body[1]))})
    reject(project, r'item 4, H1_252_4: decisions.csv decision sessions .*repeated 2009-01-30')


def test_report_rejects_wrong_execution_session(project):
    def later(body):
        body[1]['execution_session'] = '2009-02-03'
    tamper(project, 'H1_126_3', {'decisions.csv': later})
    reject(project, r'item 4, H1_126_3: decisions.csv 2009-01-30: execution_session is not the next XNYS session')


@pytest.mark.parametrize('edit, wrong', [
    (lambda body: body[11].update(ticker=body[10]['ticker']), 'EEM'),
    (lambda body: body[11].update(ticker='XYZ'), 'XYZ'),
    (lambda body: body.insert(10, dict(body[10])), 'EEM'),
    (lambda body: body.pop(11), 'GLD')])
def test_report_rejects_duplicated_or_foreign_ticker_row(project, edit, wrong):
    tamper(project, 'H1_126_3', {'signals.csv': edit})
    reject(project, rf'item 4, H1_126_3: signals.csv 2009-01-30: rows are not the nine risky tickers .*{wrong}')


def test_report_rejects_signal_file_with_other_columns(project):
    def drop_column(body):
        for r in body:
            r.pop('filter_pass')
    header, body = read_csv(project, 'H2_5of6', 'signals.csv')
    drop_column(body)
    refreeze(project, 'H2_5of6', {'signals.csv': csv_bytes([c for c in header if c != 'filter_pass'], body)})
    reject(project, r'item 4, H2_5of6: signals.csv columns are not the expected layout')


# --- item 5 -------------------------------------------------------------------------------------------------------

def etf_capped(p, extra):
    """A selected ticker of a non-parent H1 run with scale 1, v at the ETF cap, q above it and room in its group."""
    return find(p, NON_PARENT, lambda n, r: r['selected'] == 'True' and r['scale'] == '1' and r['v'] == '0.25'
                and float(r['q']) > 0.25 + 1e-6
                and group_weight(p, n, r['decision_session'], r['ticker']) + extra <= 0.5)


def test_report_rejects_risky_weight_above_the_etf_cap(project):
    name, session, ticker, _ = etf_capped(project, 2e-9)
    edit_decision(project, name, session, {ticker: {'v': repr(0.25 + 0.9e-9), 'weight': repr(0.25 + 1.8e-9)}},
                  rebalance=True)
    reject_rules(project, {'item 5 ETF cap'})


def test_report_rejects_risky_weight_026(project):
    name, session, ticker, _ = etf_capped(project, 0.011)
    edit_decision(project, name, session, {ticker: {'v': '0.26', 'weight': '0.26'}}, rebalance=True)
    # with scale 1 a weight of 0.26 needs v = 0.26, which v = capped(q) also rejects
    reject_rules(project, {'item 5 ETF cap', 'item 5 v capped'})


def test_report_rejects_group_weight_051(project):
    def roomy(n, r):
        if not (r['selected'] == 'True' and r['scale'] == '1'):
            return False
        room = min(float(r['q']), 0.25) - float(r['v'])
        return room >= 0.01 and abs(group_weight(project, n, r['decision_session'], r['ticker']) - 0.5) < 1e-9
    name, session, ticker, row = find(project, NON_PARENT, roomy)
    v = repr(float(row['v']) + 0.01)
    edit_decision(project, name, session, {ticker: {'v': v, 'weight': v}}, rebalance=True)
    assert abs(group_weight(project, name, session, ticker) - 0.51) < 1e-9
    # v = capped(q) keeps every group sum of v at or below 0.50, so with scale 1 the raised v breaks it as well
    reject_rules(project, {'item 5 group cap', 'item 5 v capped'})


def test_report_rejects_bil_not_the_remainder(project):
    w = weights_row(project, 'H1_126_4', SESSIONS[0])
    edit_decision(project, 'H1_126_4', SESSIONS[0], weights={'w_BIL': repr(float(w['w_BIL']) + 1.5e-9),
                                                             'usd': '-7e-10'})
    reject_rules(project, {'item 5 BIL remainder'})


def test_report_rejects_usd_beyond_its_bound(project):
    w = weights_row(project, 'H1_126_4', SESSIONS[1])
    edit_decision(project, 'H1_126_4', SESSIONS[1], weights={'w_BIL': repr(float(w['w_BIL']) - 0.9e-9),
                                                             'usd': '1.8e-09'})
    reject_rules(project, {'item 5 usd bound'})


def test_report_rejects_usd_not_the_remainder(project):
    w = weights_row(project, 'H1_126_4', SESSIONS[1])
    edit_decision(project, 'H1_126_4', SESSIONS[1], weights={'w_BIL': repr(float(w['w_BIL']) - 0.9e-9),
                                                             'usd': '-9e-10'})
    reject_rules(project, {'item 5 usd remainder'})


def test_report_rejects_signal_and_weights_text_mismatch(project):
    name, session, ticker, row = find(project, ('H1_126_4',), lambda n, r: r['selected'] == 'True')
    edit_decision(project, name, session, weights={f'w_{ticker}': equivalent(row['weight'])})
    reject_rules(project, {'item 5 weight text'})


def test_report_rejects_ascending_ranks(project):
    """The two best-ranked eligible tickers exchange ranks in both members of the 126 pair."""
    session = next(s for s in SESSIONS if sum(r['selected'] == 'True' and r['decision_session'] == s
                                              for r in rows(project, 'H1_126_3')) >= 2)
    top = {r['rank']: r['ticker'] for r in rows(project, 'H1_126_3') if r['decision_session'] == session}
    swap = {top['1']: {'rank': '2'}, top['2']: {'rank': '1'}}
    edit_decision(project, 'H1_126_3', session, swap)
    edit_decision(project, 'H1_126_4', session, swap)
    reject_rules(project, {'item 5 rank order'})


def test_report_rejects_q_with_k_9(project, monkeypatch):
    real = hypotheses.inverse_vol
    with monkeypatch.context() as m:
        m.setattr(hypotheses, 'inverse_vol', lambda sigma, selected, k: real(sigma, selected, 9))
        bad = simulate(project.root, project.derived, project.digest, 'H1_126_4')
    assert journal(project.root)[-1]['event'] == 'completed'
    reject_rules(project, {'item 5 q sum'}, runs=dirs(project, {'H1_126_4': bad}))


def test_report_rejects_score_not_divided_by_sigma(project):
    _, session, ticker, row = find(project, ('H1_126_3',), lambda n, r: r['eligible'] == 'False')
    for name in ('H1_126_3', 'H1_126_4'):
        edit_decision(project, name, session, {ticker: {'score': row['momentum']}})
    reject_rules(project, {'item 5 score'})


def test_report_rejects_weight_on_a_non_selected_ticker(project):
    name, session, ticker, _ = find(project, ('H1_126_4',), lambda n, r: r['selected'] == 'False')
    edit_decision(project, name, session, {ticker: {'weight': '9e-10'}})
    reject_rules(project, {'item 5 non-selected zero'})


def test_report_rejects_weight_not_scale_times_v(project):
    name, session, ticker, row = find(project, ('H1_126_4',), lambda n, r: r['selected'] == 'True')
    edit_decision(project, name, session, {ticker: {'weight': repr(float(row['weight']) - 0.001)}}, rebalance=True)
    reject_rules(project, {'item 5 weight scale'})


def test_report_rejects_v_above_q(project):
    def uncapped(n, r):
        if r['selected'] != 'True' or float(r['q']) >= 0.24:
            return False
        added = float(r['scale']) * 0.001
        return float(r['weight']) + added <= 0.25 and group_weight(project, n, r['decision_session'],
                                                                     r['ticker']) + added <= 0.5
    name, session, ticker, row = find(project, NON_PARENT, uncapped)
    v = float(row['q']) + 0.001
    edit_decision(project, name, session, {ticker: {'v': repr(v), 'weight': repr(float(row['scale']) * v)}},
                  rebalance=True)
    reject_rules(project, {'item 5 v capped'})


def test_report_rejects_scale_text_varying(project):
    _, session, ticker, row = find(project, ('H1_126_4',), lambda n, r: True)
    edit_decision(project, 'H1_126_4', session, {ticker: {'scale': equivalent(row['scale'])}})
    reject_rules(project, {'item 5 scale text'})


def wide_session(p):
    """A decision at which the 126 pair has more than four eligible tickers."""
    return next(s for s in SESSIONS if sum(r['eligible'] == 'True' and r['decision_session'] == s
                                           for r in rows(p, 'H1_126_4')) > 4)


def edit_pair(p, session, changes):
    for name in ('H1_126_3', 'H1_126_4'):
        edit_decision(p, name, session, changes)


def test_report_rejects_non_positive_sigma(project):
    _, session, ticker, row = find(project, ('H1_126_4',), lambda n, r: r['eligible'] == 'False')
    for name in HYPOTHESES:
        edit_decision(project, name, session, {ticker: {'sigma': '-' + row['sigma']}})
    # score = momentum / sigma is evaluated only for a positive sigma
    reject_rules(project, {'item 5 sigma positive', 'item 5 score'})


def test_report_rejects_eligible_with_a_non_positive_score(project):
    session = wide_session(project)
    mine = [r for r in rows(project, 'H1_126_4') if r['decision_session'] == session]
    m = sum(r['eligible'] == 'True' for r in mine)
    loser = next(r['ticker'] for r in mine if r['eligible'] == 'False')
    edit_pair(project, session, {loser: {'eligible': 'True', 'rank': str(m + 1)}})
    reject_rules(project, {'item 5 eligible'})


def test_report_rejects_rank_on_a_non_eligible_ticker(project):
    session = wide_session(project)
    mine = [r for r in rows(project, 'H1_126_4') if r['decision_session'] == session]
    m = sum(r['eligible'] == 'True' for r in mine)
    loser = next(r['ticker'] for r in mine if r['eligible'] == 'False')
    edit_pair(project, session, {loser: {'rank': str(m + 1)}})
    reject_rules(project, {'item 5 rank presence'})


def test_report_rejects_gap_in_ranks(project):
    session = wide_session(project)
    mine = [r for r in rows(project, 'H1_126_4') if r['decision_session'] == session]
    m = sum(r['eligible'] == 'True' for r in mine)
    last = next(r['ticker'] for r in mine if r['rank'] == str(m))
    edit_pair(project, session, {last: {'rank': str(m + 1)}})
    reject_rules(project, {'item 5 rank sequence'})


def test_report_rejects_zero_q_on_a_selected_ticker(project):
    session = next(s for s in SESSIONS if sum(r['selected'] == 'True' and r['decision_session'] == s
                                              for r in rows(project, 'H1_126_4')) >= 2)
    ticker = next(r['ticker'] for r in rows(project, 'H1_126_4') if r['decision_session'] == session
                  and r['selected'] == 'True')
    edit_decision(project, 'H1_126_4', session, {ticker: {'q': '0'}})
    # q > 0 is also implied by the q sum, the q sigma equality and v = capped(q)
    reject_rules(project, {'item 5 q positive', 'item 5 q sum', 'item 5 q sigma', 'item 5 v capped'})


def capped_by_hand(q):
    """Protocol lines 68-69 written out for the tests: ETF cap 0.25, then proportional group cap 0.50."""
    c = {t: min(x, 0.25) for t, x in q.items()}
    for members in GROUPS.values():
        total = math.fsum(c[t] for t in members)
        if total > 0.5:
            c.update({t: c[t] * 0.5 / total for t in members})
    return c


def test_report_rejects_q_not_inverse_to_sigma(project):
    """q moves by 0.01 between two selected tickers (the q sum is kept); v, weight and BIL follow the new q."""
    shift = 0.01
    name, session, _, donor = find(project, NON_PARENT, lambda n, r: r['selected'] == 'True'
                                   and float(r['q']) > 2 * shift and sum(
                                       x['selected'] == 'True' and x['decision_session'] == r['decision_session']
                                       for x in rows(project, n)) >= 2)
    mine = [r for r in rows(project, name) if r['decision_session'] == session]
    taker = next(r for r in mine if r['selected'] == 'True' and r is not donor and r['ticker'] != donor['ticker'])
    q = {r['ticker']: float(r['q']) for r in mine}
    q[donor['ticker']] -= shift
    q[taker['ticker']] += shift
    v = capped_by_hand(q)
    scale = float(donor['scale'])
    changes = {t: {'q': repr(q[t]), 'v': repr(v[t]), 'weight': repr(scale * v[t])} for t in q if q[t] > 0}
    edit_decision(project, name, session, changes, rebalance=True)
    reject_rules(project, {'item 5 q sigma'})


def test_report_rejects_scale_above_one(empty):
    """With an empty selection v = capped(q) and weight = scale x v stay 0, so only the scale bound fails."""
    edit_decision(empty, 'H1_126_4', SESSIONS[1], {t: {'scale': '1.5'} for t in RISKY})
    reject_rules(empty, {'item 5 scale bound'})


# --- item 6 -------------------------------------------------------------------------------------------------------

def test_report_rejects_momentum_differing_within_a_pair(project):
    row = signal(project, 'H1_252_4', SESSIONS[2], 'GLD')
    edit_decision(project, 'H1_252_4', SESSIONS[2], {'GLD': {'momentum': repr(float(row['momentum']) * (1 + 1e-12))}})
    reject_rules(project, {'item 6 pair signals'})


def test_report_rejects_sigma_differing_across_runs(project):
    row = signal(project, 'H1_126_4', SESSIONS[0], 'TLT')
    edit_decision(project, 'H1_126_4', SESSIONS[0], {'TLT': {'sigma': equivalent(row['sigma'])}})
    reject_rules(project, {'item 6 sigma across runs'})


def test_report_rejects_k3_selection_outside_k4(project):
    """Deselecting a K = 3 pick in H1_126_4: with rank equality across the pair this also breaks the selection
    rule (and the q sum unless the dropped q is exactly 1/4)."""
    _, session, ticker, row = find(project, ('H1_126_3',), lambda n, r: r['selected'] == 'True')
    edit_decision(project, 'H1_126_4', session, {ticker: {'selected': 'False', 'q': '0', 'v': '0', 'weight': '0'}},
                  rebalance=True)
    rules = failed_rules(reject(project, 'failed checks'))
    assert {'item 6 pair subset', 'item 5 selection'} <= rules <= {'item 6 pair subset', 'item 5 selection',
                                                                    'item 5 q sum'}


# --- item 7 -------------------------------------------------------------------------------------------------------

def test_report_rejects_h2_rank_edited(project):
    _, session, ticker, row = find(project, ('H2_4of6',), lambda n, r: r['rank'] != '')
    edit_decision(project, 'H2_4of6', session, {ticker: {'rank': '0' + row['rank']}})
    reject_rules(project, {'item 7 H2 parent columns'})


def test_report_rejects_h2_selected_edited(project):
    _, session, ticker, row = find(project, ('H2_5of6',), lambda n, r: r['selected'] == 'True')
    edit_decision(project, 'H2_5of6', session, {ticker: {'selected': 'False'}})
    # selected is a flag with one text per value, so the H2 row also breaks the item 5 selection rules
    reject_rules(project, {'item 7 H2 parent columns', 'item 5 selection', 'item 5 non-selected zero',
                           'item 5 q sum'})


def test_report_rejects_parent_weight_mismatch(project):
    _, session, ticker, row = find(project, ('H2_5of6',), lambda n, r: r['parent_weight'] != '0'
                                   and r['filter_pass'] == 'False')
    edit_decision(project, 'H2_5of6', session, {ticker: {'parent_weight': equivalent(row['parent_weight'])}})
    reject_rules(project, {'item 7 H2 parent weight'})


def test_report_rejects_parent_weight_changed_in_the_parent(project):
    """The parent's signal and weights.csv texts change together, so only the H2 rows disagree."""
    _, session, ticker, row = find(project, ('H1_252_3',), lambda n, r: r['selected'] == 'True')
    edit_decision(project, 'H1_252_3', session, {ticker: {'weight': equivalent(row['weight'])}})
    reject_rules(project, {'item 7 H2 parent weight'})


def test_report_rejects_parent_weights_csv_text_mismatch(project):
    _, session, ticker, row = find(project, ('H1_252_3',), lambda n, r: r['selected'] == 'True')
    edit_decision(project, 'H1_252_3', session, weights={f'w_{ticker}': equivalent(row['weight'])})
    reject_rules(project, {'item 5 weight text', 'item 7 H2 parent weight'})


def test_report_rejects_excess_differing_between_h2_runs(project):
    row = signal(project, 'H2_5of6', SESSIONS[1], 'GLD')
    edit_decision(project, 'H2_5of6', SESSIONS[1], {'GLD': {'excess_3': equivalent(row['excess_3'])}})
    reject_rules(project, {'item 7 H2 months across runs'})


def test_report_rejects_positive_months_differing_between_h2_runs(project):
    row = signal(project, 'H2_5of6', SESSIONS[2], 'HYG')
    edit_decision(project, 'H2_5of6', SESSIONS[2], {'HYG': {'positive_months': '0' + row['positive_months']}})
    reject_rules(project, {'item 7 H2 months across runs'})


def test_report_rejects_positive_months_not_the_count(project):
    _, session, ticker, row = find(project, ('H2_4of6',), lambda n, r: int(r['positive_months']) <= 3)
    months = int(row['positive_months'])
    wrong = str(months - 1 if months else months + 1)
    for name in hr.H:
        edit_decision(project, name, session, {ticker: {'positive_months': wrong}})
    reject_rules(project, {'item 7 H2 positive months'})


def test_report_rejects_filter_pass_inconsistent(project):
    _, session, ticker, _ = find(project, ('H2_5of6',), lambda n, r: r['filter_pass'] == 'False'
                                 and r['parent_weight'] == '0')
    edit_decision(project, 'H2_5of6', session, {ticker: {'filter_pass': 'True'}})
    reject_rules(project, {'item 7 H2 filter'})


def test_report_rejects_h2_weight_wrong(project):
    _, session, ticker, row = find(project, ('H2_4of6',), lambda n, r: r['filter_pass'] == 'True'
                                   and r['parent_weight'] != '0')
    text = equivalent(row['weight'])
    edit_decision(project, 'H2_4of6', session, {ticker: {'weight': text}}, weights={f'w_{ticker}': text})
    reject_rules(project, {'item 7 H2 weight'})


def test_report_rejects_h2_bil_leaving_released_weight_in_usd(project):
    _, session, _, _ = find(project, ('H2_4of6',), lambda n, r: r['selected'] == 'True'
                            and r['filter_pass'] == 'False')
    parent_bil = weights_row(project, 'H1_252_3', session)['w_BIL']
    edit_decision(project, 'H2_4of6', session, weights={'w_BIL': parent_bil}, rebalance=True)
    assert float(weights_row(project, 'H2_4of6', session)['usd']) > 0.01
    reject_rules(project, {'item 5 BIL remainder', 'item 5 usd bound'})


def test_report_rejects_h2_bil_below_the_parent(empty):
    edit_decision(empty, 'H2_5of6', SESSIONS[1], weights={'w_BIL': '0.9999999995', 'usd': '5e-10'})
    reject_rules(empty, {'item 7 H2 BIL'})


# --- parse errors -------------------------------------------------------------------------------------------------

@pytest.mark.parametrize('text', ['abc', 'nan', '1_0', 'inf'])
def test_report_parse_error_withholds_field_text(project, text):
    name, session, ticker, _ = find(project, ('H1_126_4',), lambda n, r: r['selected'] == 'True')
    edit_decision(project, name, session, weights={f'w_{ticker}': text})
    message = reject(project, rf'item 5 parse: {name} weights.csv {session} {ticker} w_{ticker} is not a finite')
    error = journal(project.root)[-1]['error']
    assert text not in message and text not in error
    assert error == f'ValueError: {message}'


def test_report_parse_error_in_signals_names_the_column(project):
    edit_decision(project, 'H2_4of6', SESSIONS[2], {'TLT': {'excess_2': '0.1x'}})
    message = reject(project, rf'item 7 parse: H2_4of6 signals.csv {SESSIONS[2]} TLT excess_2 is not a finite')
    assert '0.1x' not in journal(project.root)[-1]['error'] and '0.1x' not in message


def test_shared_helpers_say_hypothesis_when_asked(project):
    path = project.runs['H1_252_3']
    with pytest.raises(ValueError, match='not a hypothesis run'):
        report.verify_run_dir(project.root, path, report.RUN_FILES, label='hypothesis')
    with pytest.raises(ValueError, match='not a benchmark run'):
        report.verify_run_dir(project.root, path, report.RUN_FILES)


def test_report_rejects_unreadable_csv_without_its_bytes(project):
    path = project.runs['H1_126_4'] / 'trades.csv'
    refreeze(project, 'H1_126_4', {'trades.csv': path.read_bytes() + b'\xff\xfe9.87654\n'})
    message = reject(project, r'item 4, H1_126_4: trades.csv is not a readable UTF-8 CSV file')
    assert '9.87654' not in message and '9.87654' not in journal(project.root)[-1]['error']


def test_report_rejects_short_csv_row(project):
    path = project.runs['H1_252_4'] / 'payouts.csv'
    refreeze(project, 'H1_252_4', {'payouts.csv': path.read_bytes() + b'SPY,2009-01-02\n'})
    reject(project, r'item 4, H1_252_4: payouts.csv line \d+ does not have 8 fields')


def test_report_rejects_malformed_invariants(project):
    refreeze(project, 'H2_4of6', {'invariants.json': provenance.canonical_bytes({'passed': True})})
    reject(project, r'item 4, H2_4of6: .*malformed run data')


def bil_negative_decision():
    """A K = 4 decision that satisfies every item 5 rule except a BIL weight below -ABS_TOL: four risky weights at
    the ETF cap plus 0.9e-9, one per group, so the risky sum exceeds 1 by 3.6e-9."""
    chosen = ('GLD', 'IEF', 'LQD', 'SPY')
    rows = []
    for rank, t in enumerate(chosen, 1):
        momentum = repr(0.1 * (5 - rank))
        rows.append({'ticker': t, 'momentum': momentum, 'sigma': '0.1', 'score': repr(float(momentum) / 0.1),
                     'eligible': 'True', 'rank': str(rank), 'selected': 'True', 'q': '0.25', 'v': '0.25',
                     'scale': '1', 'weight': '0.2500000009'})
    for t in RISKY:
        if t not in chosen:
            rows.append({'ticker': t, 'momentum': '-0.1', 'sigma': '0.1', 'score': '-1', 'eligible': 'False',
                         'rank': '', 'selected': 'False', 'q': '0', 'v': '0', 'scale': '1', 'weight': '0'})
    rows.sort(key=lambda r: r['ticker'])
    weights = {'decision_session': '2009-01-30', **{f'w_{t}': '0' for t in TICKERS}, 'usd': '0'}
    weights.update({f'w_{t}': '0.2500000009' for t in chosen})
    weights['w_BIL'] = '-3.6e-09'
    return weights, rows


def test_item_5_rejects_negative_bil():
    weights, rows = bil_negative_decision()
    fail = hr.Failures()
    hr._check_decision(fail, 'H1_252_4', '2009-01-30', weights, rows)
    assert {label for label, _ in fail.items} == {'item 5 BIL non-negative'}
    # a BIL weight of -9e-10 is within the tolerance
    weights['w_BIL'] = '-9e-10'
    weights['w_SPY'] = weights['w_IEF'] = weights['w_LQD'] = '0.25'
    for r in rows:
        if r['ticker'] in ('SPY', 'IEF', 'LQD'):
            r['weight'] = '0.25'
    fail = hr.Failures()
    hr._check_decision(fail, 'H1_252_4', '2009-01-30', weights, rows)
    assert fail.items == []


def hand_decision(chosen, v, scale='1'):
    """One consistent decision of selected tickers {ticker: (q, sigma)} in descending score order, with the v texts
    given by hand (the test states the expected capped values); weight = scale x v, BIL the remainder, all %.10g."""
    rows = []
    for rank, (t, (q, sigma)) in enumerate(chosen.items(), 1):
        score = 0.1 * (10 - rank)
        momentum = '%.10g' % (score * sigma)
        rows.append({'ticker': t, 'momentum': momentum, 'sigma': '%.10g' % sigma,
                     'score': '%.10g' % (float(momentum) / sigma), 'eligible': 'True', 'rank': str(rank),
                     'selected': 'True', 'q': '%.10g' % q, 'v': v[t], 'scale': scale,
                     'weight': '%.10g' % (float(scale) * float(v[t]))})
    for t in RISKY:
        if t not in chosen:
            rows.append({'ticker': t, 'momentum': '-0.1', 'sigma': '0.1', 'score': '-1', 'eligible': 'False',
                         'rank': '', 'selected': 'False', 'q': '0', 'v': '0', 'scale': scale, 'weight': '0'})
    rows.sort(key=lambda r: r['ticker'])
    weights = {'decision_session': '2009-01-30', **{f'w_{r["ticker"]}': r['weight'] for r in rows}}
    weights['w_BIL'] = '%.10g' % (1 - math.fsum(float(r['weight']) for r in rows))
    weights['usd'] = '%.10g' % (1 - math.fsum(float(weights[f'w_{t}']) for t in TICKERS))
    return weights, rows


# K = 4: two equity tickers with q 0.30 capped at 0.25 each; the equity group sums to 0.50 exactly and is not scaled.
TWO_EQUITY = {'SPY': (0.3, 0.1), 'EFA': (0.3, 0.1), 'GLD': (0.2, 0.15), 'IEF': (0.2, 0.15)}
TWO_EQUITY_V = {'SPY': '0.25', 'EFA': '0.25', 'GLD': '0.2', 'IEF': '0.2'}
# K = 3: three equity tickers with q 0.40, 0.35, 0.25 (q x sigma = 0.07) capped at 0.25 each; the group sum 0.75 is
# scaled to 0.50, so each v is 0.25 x 0.50 / 0.75 = 1/6.
THREE_EQUITY = {'SPY': (0.4, 0.175), 'EFA': (0.35, 0.2), 'EEM': (0.25, 0.28)}
THREE_EQUITY_V = {'SPY': '0.1666666667', 'EFA': '0.1666666667', 'EEM': '0.1666666667'}


def item5_labels(name, weights, rows):
    fail = hr.Failures()
    hr._check_decision(fail, name, '2009-01-30', weights, rows)
    return fail.items


def test_item_5_accepts_capped_weights_with_a_binding_group_cap():
    assert item5_labels('H1_252_4', *hand_decision(TWO_EQUITY, TWO_EQUITY_V)) == []
    weights, rows = hand_decision(THREE_EQUITY, THREE_EQUITY_V, scale='0.6')
    assert {r['weight'] for r in rows if r['selected'] == 'True'} == {'0.1'}
    assert item5_labels('H1_252_3', weights, rows) == []


def test_item_5_rejects_v_ignoring_a_binding_group_cap():
    """v at the ETF cap without the proportional group scaling; the weights stay within every cap."""
    weights, rows = hand_decision(THREE_EQUITY, {t: '0.25' for t in THREE_EQUITY}, scale='0.6')
    assert item5_labels('H1_252_3', weights, rows) == [('item 5 v capped', f'H1_252_3 2009-01-30 {t}')
                                                        for t in ('EEM', 'EFA', 'SPY')]


def test_item_5_rejects_v_above_the_etf_cap():
    weights, rows = hand_decision(TWO_EQUITY, {**TWO_EQUITY_V, 'SPY': '0.26'}, scale='0.5')
    assert item5_labels('H1_252_4', weights, rows) == [('item 5 v capped', 'H1_252_4 2009-01-30 SPY')]


def test_report_rejects_selected_v_zeroed(project):
    """A decision with every selected v and weight zero and BIL = 1 is consistent apart from v = capped(q)."""
    name, session, _, _ = find(project, NON_PARENT, lambda n, r: r['selected'] == 'True')
    chosen = [r['ticker'] for r in rows(project, name) if r['decision_session'] == session and r['selected'] == 'True']
    edit_decision(project, name, session, {t: {'v': '0', 'weight': '0'} for t in chosen},
                  {'w_BIL': '1', 'usd': '0'})
    message = reject_rules(project, {'item 5 v capped'})
    assert all(f'{name} {session} {t}' in message for t in chosen)


def turnover_or_fill(p, name, column, text):
    def edit(body):
        body[1][column] = text
    tamper(p, name, {'decisions.csv': edit})


@pytest.mark.parametrize('column, text', [('turnover', '-1e-06'), ('buy_fill', '1.0000001'), ('buy_fill', '-0.1')])
def test_report_rejects_turnover_or_buy_fill_out_of_range(project, column, text):
    turnover_or_fill(project, 'H1_126_4', column, text)
    message = reject_rules(project, {f'item 5 {column}'})
    assert f'H1_126_4 {SESSIONS[1]}' in message and text not in message
    assert text not in journal(project.root)[-1]['error']


@pytest.mark.parametrize('text', ['1', '0'])
def test_report_accepts_buy_fill_at_its_bounds(project, text):
    turnover_or_fill(project, 'H2_4of6', 'buy_fill', text)
    accepted(project)


def test_report_rejects_malformed_turnover_without_its_text(project):
    turnover_or_fill(project, 'H1_252_3', 'turnover', '0.1x')
    message = reject(project, rf'item 5 parse: H1_252_3 decisions.csv {SESSIONS[1]} turnover is not a finite')
    assert '0.1x' not in message and '0.1x' not in journal(project.root)[-1]['error']


@pytest.mark.parametrize('text', ['١', '0.٥', '1e٣', '１'])
def test_number_rejects_non_ascii_digits(text):
    assert math.isfinite(float(text))  # Python's float accepts these digits; frozen %.10g text never has them
    with pytest.raises(ValueError, match='is not a finite number') as info:
        hr.number(text, 5, 'H1_252_3', 'signals.csv', '2009-01-30', 'SPY', 'q')
    assert text not in str(info.value)


@pytest.mark.parametrize('text', ['٣', '1٢', '４'])
def test_integer_rejects_non_ascii_digits(text):
    assert int(text) >= 0
    with pytest.raises(ValueError, match='is not an integer'):
        hr.integer(text, 5, 'H1_252_3', 'signals.csv', '2009-01-30', 'SPY', 'rank')


# --- diagnostics (spec 6.2) ---------------------------------------------------------------------------------------

YEARS = [str(y) for y in range(2009, 2023)]
PERIODS = ['full', *YEARS]
CHECKS = ('cash_non_negative', 'nav_identity', 'cash_flow', 'split_quantity_only', 'receivable_conservation',
          'execution_timing', 'costs')
PROXY = 'proxy_ex_plus_10_calendar_days'
# Hand-built decisions: (decision, execution, eligible, selected, scale, risky weights, turnover, buy_fill).
HAND = [('2008-12-31', '2009-01-02', ('EEM', 'IEF', 'SPY', 'TLT'), ('IEF', 'SPY', 'TLT'), '0.8',
         {'SPY': '0.2', 'TLT': '0.25', 'IEF': '0.15'}, '0.6', '1'),
        ('2009-06-30', '2009-07-01', ('SPY',), ('SPY',), '0.9999999999', {'SPY': '0.25'}, '0.3', '0.98'),
        ('2009-12-31', '2010-01-04', (), (), '1', {}, '0.25', '0.9999999999')]
# H2_4of6 filter passes per decision; EEM passes without being selected and must not count.
PASSES = [('EEM', 'IEF', 'SPY'), (), ()]
H2_WEIGHTS = [{'SPY': '0.2', 'IEF': '0.15'}, {}, {}]


def weight_row(session, risky):
    row = {'decision_session': session, **{f'w_{t}': risky.get(t, '0') for t in RISKY}, 'usd': '0'}
    row['w_BIL'] = repr(1 - math.fsum(float(v) for v in risky.values()))
    return row


def hand_runs():
    """RunFiles of H1_252_3 and H2_4of6 holding only the fields the diagnostics read."""
    decisions = [{'decision_session': d, 'execution_session': e, 'turnover': tu, 'buy_fill': bf}
                 for d, e, _, _, _, _, tu, bf in HAND]
    orders = [{'execution_session': '2009-01-02', 'status': 'filled', 'cancel_reason': ''},
              {'execution_session': '2009-01-02', 'status': 'partial', 'cancel_reason': 'insufficient_cash'},
              {'execution_session': '2009-07-01', 'status': 'cancelled', 'cancel_reason': 'no_valid_open'},
              {'execution_session': '2010-01-04', 'status': 'filled', 'cancel_reason': ''}]
    trades = [{'session': '2009-01-02', 'side': 'buy'}, {'session': '2009-01-02', 'side': 'buy'},
              {'session': '2009-07-01', 'side': 'sell'}, {'session': '2010-01-04', 'side': 'sell'}]
    payouts = [{'ex_session': '2008-12-31', 'status': 'paid', 'pay_basis': 'actual'},
               {'ex_session': '2009-03-20', 'status': 'paid', 'pay_basis': PROXY},
               {'ex_session': '2009-12-30', 'status': 'receivable', 'pay_basis': 'actual'},
               {'ex_session': '2010-12-20', 'status': 'receivable', 'pay_basis': 'actual'}]
    invariants = {'passed': True, 'checks': {c: True for c in CHECKS}, 'split_events': [['BIL', '2009-05-01']],
                  'proxy_payouts': [['SPY', '2009-03-20', '2009-03-30'], ['TLT', '2008-12-31', '2009-01-12']]}
    config = {'scenario': {'cost': 0.001, 'lag': 1, 'reserve': 0.01, 'proxy_pay_days': 10}}

    def signals(h2):
        out = []
        for i, (d, _, eligible, selected, scale, _, _, _) in enumerate(HAND):
            for t in RISKY:
                row = {'decision_session': d, 'ticker': t, 'eligible': str(t in eligible),
                       'selected': str(t in selected), 'scale': scale}
                if h2:
                    row['filter_pass'] = str(t in PASSES[i])
                out.append(row)
        return out
    parent = hr.RunFiles(None, config, decisions, [weight_row(d, w) for d, _, _, _, _, w, _, _ in HAND],
                         signals(False), orders, trades, payouts, invariants)
    h2 = parent._replace(weights=[weight_row(h[0], w) for h, w in zip(HAND, H2_WEIGHTS)], signals=signals(True))
    return {'H1_252_3': parent, 'H2_4of6': h2}


def approx(expected):
    return pytest.approx(expected, rel=1e-12, abs=1e-15)


def test_hand_counted_diagnostics():
    doc = hr.diagnostics(hand_runs())
    assert list(doc) == ['H1_252_3', 'H2_4of6']
    h1 = doc['H1_252_3']
    assert h1['integrity'] == {'passed': True, 'checks': {c: True for c in CHECKS}, 'split_events': 1,
                               'proxy_payouts': 2}
    full = h1['periods']['full']
    assert full['counts'] == {
        'decisions': 3, 'orders': {'filled': 2, 'partial': 1, 'cancelled': 1},
        'order_reasons': {'partial': {'no_valid_open': 0, 'insufficient_cash': 1, 'fractional_quantity': 0,
                                      'exceeds_position': 0},
                          'cancelled': {'no_valid_open': 1, 'insufficient_cash': 0, 'fractional_quantity': 0,
                                        'exceeds_position': 0}},
        'trades': {'buy': 2, 'sell': 2}, 'payout_status': {'paid': 1, 'receivable': 2},
        'payout_basis': {'actual': 2, 'proxy': 1}}
    assert full['selection'] == {'mean_eligible': approx(5 / 3), 'mean_selected': approx(4 / 3),
                                 'selected_distribution': {'0': 1, '1': 1, '2': 0, '3': 1}, 'empty_selections': 1}
    assert full['targets'] == {'mean_risky': approx(0.85 / 3), 'max_risky': approx(0.6), 'mean_bil': approx(2.15 / 3),
                               'max_etf': 0.25, 'max_group': approx(0.4), 'scale_binding': 2,
                               'scale_binding_share': approx(2 / 3), 'mean_scale': approx(2.7999999999 / 3)}
    assert full['trading'] == {'turnover_sum': approx(1.15), 'turnover_mean': approx(1.15 / 3),
                               'cost_ratio': approx(0.00115), 'min_buy_fill': 0.98, 'partial_fills': 2}
    assert full['ticker_selection'] == {**{t: 0.0 for t in RISKY}, 'SPY': approx(2 / 3), 'TLT': approx(1 / 3),
                                        'IEF': approx(1 / 3)}
    assert 'h2_filter' not in full and 'ticker_pass' not in full
    y2009, y2010 = h1['periods']['2009'], h1['periods']['2010']
    assert y2009['selection'] == {'mean_eligible': 2.5, 'mean_selected': 2.0,
                                  'selected_distribution': {'0': 0, '1': 1, '2': 0, '3': 1}, 'empty_selections': 0}
    assert y2009['targets'] == {'mean_risky': approx(0.425), 'max_risky': approx(0.6), 'mean_bil': approx(0.575),
                                'max_etf': 0.25, 'max_group': approx(0.4), 'scale_binding': 2,
                                'scale_binding_share': 1.0, 'mean_scale': approx(1.7999999999 / 2)}
    assert y2009['trading'] == {'turnover_sum': approx(0.9), 'turnover_mean': approx(0.45),
                                'cost_ratio': approx(0.0009), 'min_buy_fill': 0.98, 'partial_fills': 1}
    assert y2010['targets'] == {'mean_risky': 0.0, 'max_risky': 0.0, 'mean_bil': 1.0, 'max_etf': 0.0,
                                'max_group': 0.0, 'scale_binding': 0, 'scale_binding_share': 0.0, 'mean_scale': 1.0}
    assert y2010['trading'] == {'turnover_sum': 0.25, 'turnover_mean': 0.25, 'cost_ratio': approx(0.00025),
                                'min_buy_fill': 0.9999999999, 'partial_fills': 1}
    h2 = doc['H2_4of6']['periods']
    # passes among selected: decision 1 IEF and SPY of three, decision 2 none of one
    assert h2['full']['h2_filter'] == {'pass_share': 0.5, 'removal_decisions': 2,
                                       'mean_removed_share': approx(((0.6 - 0.35) / 0.6 + 1.0) / 2)}
    assert h2['2009']['h2_filter'] == h2['full']['h2_filter']
    assert h2['2010']['h2_filter'] == {'pass_share': None, 'removal_decisions': 0, 'mean_removed_share': None}
    assert h2['full']['ticker_pass'] == {**{t: None for t in RISKY}, 'SPY': 0.5, 'TLT': 0.0, 'IEF': 1.0}
    assert h2['full']['targets']['mean_risky'] == approx(0.35 / 3)
    assert h2['full']['selection'] == full['selection']  # the parent's selection columns


@pytest.mark.parametrize('edit, match', [
    (lambda inv: inv['checks'].update(costs=False), 'invariants.json check costs did not pass'),
    (lambda inv: inv['checks'].update(costs=1), 'invariants.json check costs did not pass'),
    (lambda inv: inv.update(passed=1), 'invariants did not pass'),
    (lambda inv: inv['checks'].pop('costs'), 'invariants.json lacks the check costs'),
    (lambda inv: inv['checks'].update(margin=True), 'invariants.json holds the unexpected check margin')])
def test_integrity_rejects_what_item_4_rejects(edit, match):
    runs = hand_runs()
    invariants = json.loads(json.dumps(runs['H1_252_3'].invariants))
    edit(invariants)
    runs['H1_252_3'] = runs['H1_252_3']._replace(invariants=invariants)
    with pytest.raises(ValueError, match=f'^diagnostics: H1_252_3 {match}$'):
        hr.diagnostics(runs)


@pytest.mark.parametrize('builder', ['_trading', '_h2_filter', '_counts'])
def test_builder_enforces_the_whitelist(monkeypatch, builder):
    real = getattr(hr, builder)
    monkeypatch.setattr(hr, builder, lambda *args: {**real(*args), 'leak': 1.0})
    section = builder.lstrip('_')
    with pytest.raises(ValueError, match=f'diagnostics: .* {section} keys are not the whitelist'):
        hr.diagnostics(hand_runs())


def test_builder_enforces_nested_whitelists(monkeypatch):
    real = hr._counts
    monkeypatch.setattr(hr, '_counts', lambda *args: {**real(*args), 'trades': {'buy': 0, 'sell': 0, 'short': 0}})
    with pytest.raises(ValueError, match='diagnostics: .* trades keys are not the whitelist'):
        hr.diagnostics(hand_runs())


def test_annual_attribution():
    doc = hr.diagnostics(hand_runs())['H1_252_3']['periods']
    # the 2008-12-31 decision executes on 2009-01-02 and belongs to 2009, with its signals and turnover
    assert doc['2009']['counts']['decisions'] == 2 and doc['2010']['counts']['decisions'] == 1
    assert doc['2009']['selection']['selected_distribution']['3'] == 1
    assert doc['2009']['trading']['turnover_sum'] == approx(0.9)
    # orders by execution_session, trades by session
    assert doc['2009']['counts']['orders'] == {'filled': 1, 'partial': 1, 'cancelled': 1}
    assert doc['2010']['counts']['orders'] == {'filled': 1, 'partial': 0, 'cancelled': 0}
    assert doc['2009']['counts']['trades'] == {'buy': 2, 'sell': 1}
    assert doc['2010']['counts']['trades'] == {'buy': 0, 'sell': 1}
    # payouts by ex_session with the end-of-run status; the 2008 entitlement belongs to no period
    assert doc['2009']['counts']['payout_status'] == {'paid': 1, 'receivable': 1}
    assert doc['2009']['counts']['payout_basis'] == {'actual': 1, 'proxy': 1}
    assert doc['2010']['counts']['payout_status'] == {'paid': 0, 'receivable': 1}
    for key in ('decisions', 'orders', 'trades', 'payout_status'):
        total = doc['full']['counts'][key]
        if isinstance(total, dict):
            assert all(total[k] == sum(doc[y]['counts'][key][k] for y in YEARS) for k in total)
        else:
            assert total == sum(doc[y]['counts'][key] for y in YEARS)


def test_null_denominators():
    doc = hr.diagnostics(hand_runs())
    empty = doc['H1_252_3']['periods']['2015']
    assert empty['counts']['decisions'] == 0
    assert empty['selection'] == {'mean_eligible': None, 'mean_selected': None,
                                  'selected_distribution': {'0': 0, '1': 0, '2': 0, '3': 0}, 'empty_selections': 0}
    assert empty['targets'] == {'mean_risky': None, 'max_risky': None, 'mean_bil': None, 'max_etf': None,
                                'max_group': None, 'scale_binding': 0, 'scale_binding_share': None,
                                'mean_scale': None}
    assert empty['trading'] == {'turnover_sum': 0.0, 'turnover_mean': None, 'cost_ratio': 0.0, 'min_buy_fill': None,
                                'partial_fills': 0}
    assert doc['H2_4of6']['periods']['2015']['h2_filter'] == {'pass_share': None, 'removal_decisions': 0,
                                                              'mean_removed_share': None}
    assert doc['H2_4of6']['periods']['full']['ticker_pass']['GLD'] is None
    # a null survives the canonical JSON and renders as n/a
    text = hr.render_markdown(json.loads(provenance.canonical_bytes(doc)))
    assert 'n/a' in text and 'None' not in text and 'nan' not in text


def leaf_paths(value, prefix=()):
    if isinstance(value, dict):
        for k, v in value.items():
            yield from leaf_paths(v, (*prefix, k))
    else:
        yield prefix


def test_document_keys_are_the_whitelist(project):
    doc = hr.diagnostics(verified(project))
    keys = hr.DOCUMENT_KEYS
    assert list(doc) == list(HYPOTHESES)
    assert keys['candidate'] == ('integrity', 'periods')
    assert keys['periods'] == tuple(PERIODS)
    assert keys['period'] == ('counts', 'selection', 'targets', 'trading', 'h2_filter')
    assert keys['full'] == ('ticker_selection', 'ticker_pass')
    assert keys['integrity'] == ('passed', 'checks', 'split_events', 'proxy_payouts')
    assert keys['counts'] == ('decisions', 'orders', 'order_reasons', 'trades', 'payout_status', 'payout_basis')
    assert keys['selection'] == ('mean_eligible', 'mean_selected', 'selected_distribution', 'empty_selections')
    assert keys['targets'] == ('mean_risky', 'max_risky', 'mean_bil', 'max_etf', 'max_group', 'scale_binding',
                               'scale_binding_share', 'mean_scale')
    assert keys['trading'] == ('turnover_sum', 'turnover_mean', 'cost_ratio', 'min_buy_fill', 'partial_fills')
    assert keys['h2_filter'] == ('pass_share', 'removal_decisions', 'mean_removed_share')
    for name, candidate in doc.items():
        h2 = name in hr.H
        assert list(candidate) == list(keys['candidate'])
        assert list(candidate['integrity']) == list(keys['integrity'])
        assert list(candidate['integrity']['checks']) == list(CHECKS)
        assert list(candidate['periods']) == PERIODS
        for period, block in candidate['periods'].items():
            sections = [s for s in keys['period'] if h2 or s != 'h2_filter']
            if period == 'full':
                sections += [s for s in keys['full'] if h2 or s != 'ticker_pass']
            assert list(block) == sections, (name, period)
            for section in sections:
                if section in keys:
                    assert list(block[section]) == list(keys[section])
            counts = block['counts']
            assert list(counts['orders']) == ['filled', 'partial', 'cancelled']
            assert list(counts['order_reasons']) == ['partial', 'cancelled']
            assert all(list(r) == ['no_valid_open', 'insufficient_cash', 'fractional_quantity', 'exceeds_position']
                       for r in counts['order_reasons'].values())
            assert list(counts['trades']) == ['buy', 'sell']
            assert list(counts['payout_status']) == ['paid', 'receivable']
            assert list(counts['payout_basis']) == ['actual', 'proxy']
            assert list(block['selection']['selected_distribution']) == [str(k) for k in range(hr.K[name] + 1)]
        full = candidate['periods']['full']
        assert list(full['ticker_selection']) == list(hr.RISKY)
        if h2:
            assert list(full['ticker_pass']) == list(hr.RISKY)
        # every leaf is a flag, a count, a finite number or null
        for path in leaf_paths(candidate):
            leaf = candidate
            for k in path:
                leaf = leaf[k]
            assert leaf is None or isinstance(leaf, (bool, int)) or math.isfinite(leaf), path
    assert doc['H1_252_3']['periods']['full']['counts']['decisions'] == len(SESSIONS)


EXCLUDED_REPLACEMENT = '7777.5'


def test_document_ignores_excluded_columns(project):
    """Every column the report may not read, including all quantities, is replaced in all six runs."""
    before = provenance.canonical_bytes(hr.diagnostics(verified(project)))
    replaced = set()
    for name in HYPOTHESES:
        files = {}
        for file in ('decisions.csv', 'orders.csv', 'trades.csv', 'payouts.csv', 'daily.csv'):
            header, body = read_csv(project, name, file)
            keep = hr.PERMITTED.get(file, ())
            for r in body:
                r.update({c: EXCLUDED_REPLACEMENT for c in header if c not in keep})
            replaced |= {c for c in header if c not in keep}
            files[file] = csv_bytes(header, body)
        invariants = json.loads((project.runs[name] / 'invariants.json').read_bytes())
        for check in CHECKS:
            invariants[check]['detail'] = EXCLUDED_REPLACEMENT
        files['invariants.json'] = provenance.canonical_bytes(invariants)
        refreeze(project, name, files)
    named = {'nav', 'costs_usd', 'cash', 'receivables', 'positions_value', 'notional', 'cost', 'cash_after', 'amount',
             'target_qty', 'held_qty', 'order_qty', 'filled_qty', 'qty', *(f'qty_{t}' for t in TICKERS)}
    assert named <= replaced
    after = provenance.canonical_bytes(hr.diagnostics(verified(project)))
    assert after == before


def test_ticker_items_full_only(project):
    doc = hr.diagnostics(verified(project))
    for name, candidate in doc.items():
        for period, block in candidate['periods'].items():
            assert ('ticker_selection' in block) == (period == 'full')
            assert ('ticker_pass' in block) == (period == 'full' and name in hr.H)
            if period != 'full':
                text = json.dumps(block)
                assert not any(t in text for t in TICKERS) and not any(g in text for g in GROUPS)
    text = hr.render_markdown(json.loads(provenance.canonical_bytes(doc)))
    annual = text[text.index('## Annual'):]
    assert not any(t in annual for t in TICKERS) and not any(g in annual for g in GROUPS)
    assert all(t in text[:text.index('## Annual')] for t in RISKY)


def test_markdown_layout_and_formats():
    doc = json.loads(provenance.canonical_bytes(hr.diagnostics(hand_runs())))
    text = hr.render_markdown(doc)
    assert text == hr.render_markdown(doc)
    headings = [line for line in text.splitlines() if line.startswith('## ')]
    assert headings[0] == '## Integrity (whole run)'
    first_annual = next(i for i, h in enumerate(headings) if h.startswith('## Annual'))
    assert all(h.startswith('## Full period') for h in headings[1:first_annual])
    assert all(h.startswith('## Annual') for h in headings[first_annual:])
    lines = text.splitlines()

    def row(heading, first, second=None):
        start = lines.index(heading)
        header = [c.strip() for c in lines[start + 2].strip('|').split('|')]
        for line in lines[start + 4:]:
            if not line.startswith('|'):
                break
            cells = [c.strip() for c in line.strip('|').split('|')]
            if cells[0] == first and (second is None or cells[1] == second):
                return dict(zip(header, cells))
        raise AssertionError((heading, first, second))
    integrity = row('## Integrity (whole run)', 'H1_252_3')
    assert integrity['passed'] == 'True' and integrity['split_events'] == '1' and integrity['proxy_payouts'] == '2'
    targets = row('## Full period: targets', 'H1_252_3')
    assert targets['mean_risky'] == '28.33%' and targets['scale_binding'] == '2'
    assert targets['scale_binding_share'] == '66.67%' and targets['mean_scale'] == '0.9333'
    trading = row('## Full period: trading', 'H1_252_3')
    # 0.001 x 1.15 is 0.0011499999999999999 in binary floating point
    assert trading['turnover_sum'] == '1.1500' and trading['cost_ratio'] == '0.0011'
    assert trading['min_buy_fill'] == '0.9800' and trading['partial_fills'] == '2'
    selection = row('## Full period: selection', 'H1_252_3')
    assert selection['mean_eligible'] == '1.67' and selection['selected 3'] == '1'
    assert row('## Full period: H2 filter', 'H2_4of6')['pass_share'] == '50.00%'
    assert row('## Full period: H2 ticker pass share', 'H2_4of6')['GLD'] == 'n/a'
    assert row('## Annual trading', '2015', 'H1_252_3')['turnover_mean'] == 'n/a'
    assert row('## Annual counts', '2009', 'H1_252_3')['decisions'] == '2'
    assert 'H1_252_3' not in row('## Full period: H2 filter', 'H2_4of6').values()


def test_markdown_note_explains_n_a_max_etf_and_h2_selection():
    text = hr.render_markdown(json.loads(provenance.canonical_bytes(hr.diagnostics(hand_runs()))))
    note = text.split('\n\n')[1]
    assert 'n/a marks a zero denominator or a minimum or maximum without values' in note
    assert 'max_etf covers the nine risky ETFs only' in note
    assert 'For H2 the selection and scale columns are those of the parent H1_252_3' in note


def report_files(target):
    manifest = provenance.verify(target)
    return manifest, {n: (target / n).read_bytes() for n in manifest['files']}


def test_report_freezes_without_run_ids(project):
    target = verify_runs(project)
    assert target.parent == project.root / 'data/reports'
    manifest, files = report_files(target)
    assert set(files) == {'hypotheses.json', 'hypotheses.md'}
    document = json.loads(files['hypotheses.json'])
    assert files['hypotheses.json'] == provenance.canonical_bytes(hr.diagnostics(verified(project)))
    assert files['hypotheses.md'] == hr.render_markdown(document).encode('utf-8')
    ids = [d.name for d in project.runs.values()] + [target.name]
    for body in files.values():
        text = body.decode('utf-8')
        assert not any(i in text for i in ids) and 'data/' not in text and 'created_at' not in text
        assert str(project.root) not in text and project.digest not in text
        assert '\r' not in text
    meta = manifest['metadata']
    assert meta['run_id'] == target.name and 'environment' in meta
    assert meta['sources'] == [{'candidate': n, 'run_id': project.runs[n].name,
                                'manifest_sha256': provenance.sha256((project.runs[n] / 'manifest.json').read_bytes())}
                               for n in HYPOTHESES]
    started, completed = journal(project.root)[-2:]
    assert (started['event'], completed['event']) == ('started', 'completed')
    assert completed['purpose'] == 'N4 hypothesis report' and completed['candidate_ids'] == list(HYPOTHESES)
    assert started['config'] == {'runs': [f'data/runs/{project.runs[n].name}' for n in HYPOTHESES],
                                 'expected_sha256': project.digest}
    assert completed['output_paths'] == [f'data/reports/{target.name}']
    assert completed['data_sha256'] == provenance.sha256((target / 'manifest.json').read_bytes())


def test_report_is_reproducible(project):
    first = verify_runs(project)
    second = hr.build_hypothesis_report(project.root, list(reversed(dirs(project))), expected_sha256=project.digest)
    assert first != second
    assert report_files(first)[0]['files'] == report_files(second)[0]['files']


def test_cli_hypothesis_report(project, capsys):
    from alpha_lab.__main__ import main
    argv = ['hypothesis-report', '--runs', *(f'data/runs/{project.runs[n].name}' for n in HYPOTHESES),
            '--root', str(project.root), '--expected-sha256', project.digest]
    main(argv)
    printed = capsys.readouterr().out.strip()
    assert printed.startswith('data/reports/') and '\\' not in printed
    assert set(provenance.verify(project.root / printed)['files']) == {'hypotheses.json', 'hypotheses.md'}
    main([*argv, '--parent', 'x'])
    assert journal(project.root)[-1]['parent_attempt_id'] == 'x'
    assert journal(project.root)[-1]['event'] == 'completed'
    with pytest.raises(SystemExit):
        main(['hypothesis-report', '--root', str(project.root)])
