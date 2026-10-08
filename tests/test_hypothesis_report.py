"""N4 hypothesis report verification (spec 7 items 1-7): one rejection per rule, acceptance cases and value-free
parse errors, on synthetic six-run projects."""
import csv
import io
import json
import math
from pathlib import Path
import re
import shutil
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
    return hr._verify_in_run(p.root, runs or dirs(p), expected_sha256=expected_sha256 or p.digest)


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
    out = verify_runs(p, runs)
    assert journal(p.root)[-1]['error'] == 'finish not called'
    return out


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
    name, session, ticker, row = find(project, ('H1_126_4',), lambda n, r: r['selected'] == 'True'
                                      and float(r['q']) < 0.25)
    scale = float(row['scale'])
    v = '%.10g' % (5e-05 / scale)
    weight = '%.10g' % (scale * float(v))
    assert 'e-05' in v and 'e-05' in weight
    w = weights_row(project, name, session)
    risky = {t: float(weight) if t == ticker else float(w[f'w_{t}']) for t in RISKY}
    bil = '%.10g' % (1 - math.fsum(risky.values()))
    usd = '%.10g' % (1 - math.fsum([*risky.values(), float(bil)]))
    edit_decision(project, name, session, {ticker: {'v': v, 'weight': weight}}, {'w_BIL': bil, 'usd': usd})
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
    reject(project, r'item 2-3, H1_126_4: .*not completed', runs=dirs(project, {'H1_126_4': bad}))


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
    # with scale 1 a weight of 0.26 needs v = 0.26, which the v bound also rejects
    reject_rules(project, {'item 5 ETF cap', 'item 5 v bound'})


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
    reject_rules(project, {'item 5 group cap'})


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
    reject_rules(project, {'item 5 v bound'})


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
    # q > 0 is also implied by the q sum, the q sigma equality and the v bound
    reject_rules(project, {'item 5 q positive', 'item 5 q sum', 'item 5 q sigma', 'item 5 v bound'})


def test_report_rejects_q_not_inverse_to_sigma(project):
    def selected(n, s):
        return [r for r in rows(project, n) if r['decision_session'] == s and r['selected'] == 'True']
    shift = 0.01
    for name in NON_PARENT:
        for session in SESSIONS:
            chosen = selected(name, session)
            donor = next((r for r in chosen if min(float(r['q']) - shift, 0.25) >= float(r['v'])), None)
            if donor and len(chosen) >= 2:
                break
        else:
            continue
        break
    else:
        raise AssertionError('no decision with room to move q in the synthetic template')
    taker = next(r for r in chosen if r is not donor)
    edit_decision(project, name, session, {donor['ticker']: {'q': repr(float(donor['q']) - shift)},
                                           taker['ticker']: {'q': repr(float(taker['q']) + shift)}})
    reject_rules(project, {'item 5 q sigma'})


def test_report_rejects_scale_above_one(project):
    name, session, _, _ = find(project, ('H1_126_4',), lambda n, r: r['scale'] == '1')
    mine = [r for r in rows(project, name) if r['decision_session'] == session]
    edit_decision(project, name, session, {r['ticker']: {'scale': '1.5', 'v': repr(float(r['weight']) / 1.5)}
                                           for r in mine})
    reject_rules(project, {'item 5 scale bound'})


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
