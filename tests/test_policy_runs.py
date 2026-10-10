"""The P_A1 policy run: registry entry, eleven frozen files, selection log, journal, withheld failure messages and
engine-level causality of the selection (N5 spec 4.1-4.2, 5, 8.3 and 12; D025 items 2-7 and 15)."""
import csv
import json
import traceback
import numpy as np
import pytest
from n3_fixtures import RISKY, benchmark_frames, benchmark_vintage
from alpha_lab import adaptive, engine, inference
from alpha_lab.adaptive import CANDIDATES, Policy
from alpha_lab.engine import PROVIDERS, RunConfig, Scenario, config_record, run_simulation
from alpha_lab.hypotheses import SIGNAL_COLUMNS_H1, SIGNAL_COLUMNS_POLICY
from alpha_lab.market import market_from_frames
from alpha_lab.metrics import WF_PERIODS
from alpha_lab.provenance import canonical_bytes, sha256
from test_engine_run import FILES, journal, lines

START, END = '2013-12-31', '2014-02-28'
FRAMES = {'start': '2007-12-03', 'end': '2014-03-31'}
POLICY_FILES = FILES | {'weights.csv', 'signals.csv', 'metrics.json', 'selection.json'}
PARAMETERS = {'candidates': ['H1_252_3', 'H1_252_4', 'H1_126_3', 'H1_126_4'], 'validation_years': 2,
              'context_years': 3, 'tolerance': 0.001, 'penalty': 1.5}
SEGMENT = ('2011-12-30', '2013-12-31')
WITHHELD = 'RuntimeError: {} in {} run; message withheld under the N5 viewing procedure'


def vintage(root):
    return benchmark_vintage(root, **FRAMES)


def policy_run(root, name='P_A1', stage=5):
    derived, digest = vintage(root)
    return run_simulation(root, derived, name, RunConfig(START, END), expected_sha256=digest, stage=stage)


def file_hashes(run_dir):
    return json.loads((run_dir / 'manifest.json').read_text())['files']


def failed_records(root):
    return [r for r in journal(root) if r['event'] == 'failed']


def real_providers(candidates=CANDIDATES):
    return {name: PROVIDERS[name].function for name in candidates}


def engine_adapter(markets=None):
    """The validation-run adapter of the registry factory: engine.simulate with RunConfig(start, end); the markets
    it receives are appended to `markets`."""
    def run(market, provider, start, end):
        if markets is not None:
            markets.append(market)
        return engine.simulate(market, provider, RunConfig(start, end))
    return run


@pytest.fixture(scope='module')
def base_frames():
    return benchmark_frames(**FRAMES)


def copy_frames(frames):
    return {t: f.copy() for t, f in frames.items()}


def ramp_after(frames, session):
    """Prices after `session` rise by a ticker-specific ramp, so returns after it change and earlier ones do not."""
    for i, frame in enumerate(frames.values()):
        after = frame.index > session
        factor = 1.0 + 0.05 * (i + 1) * np.arange(1, after.sum() + 1) / after.sum()
        frame.loc[after, ['open', 'close']] = frame.loc[after, ['open', 'close']].mul(factor, axis=0).to_numpy()
    return frames


def test_registry_entry_and_factory():
    entry = PROVIDERS['P_A1']
    assert (entry.version, entry.schedule, entry.kind, entry.parameters) == ('1', 'monthly', 'policy', PARAMETERS)
    first, second = entry.function(), entry.function()
    assert isinstance(first, Policy) and isinstance(second, Policy) and first is not second
    assert first.candidates == CANDIDATES
    assert config_record(RunConfig(START, END), 'P_A1')['provider'] == {'name': 'P_A1', 'version': '1',
                                                                       'parameters': PARAMETERS}
    assert config_record(RunConfig(START, END), 'H1_252_3')['provider']['parameters'] == {'lookback': 252, 'k': 3}
    assert 'parameters' not in config_record(RunConfig(START, END), 'B0')['provider']
    assert SIGNAL_COLUMNS_POLICY == SIGNAL_COLUMNS_H1 + ['selection_year', 'selected_config']


def test_policy_run_files_and_journal(tmp_path, no_network):
    run_dir = policy_run(tmp_path)
    started, completed = journal(tmp_path)
    files = file_hashes(run_dir)
    assert set(files) == POLICY_FILES and len(files) == 11
    assert started['purpose'] == completed['purpose'] == 'N5 policy run'
    assert started['candidate_ids'] == completed['candidate_ids'] == ['P_A1']
    assert completed['event'] == 'completed' and completed['quality_warnings'] == []
    assert json.loads((run_dir / 'config.json').read_text())['provider'] == {'name': 'P_A1', 'version': '1',
                                                                            'parameters': PARAMETERS}
    assert started['config']['provider']['parameters'] == PARAMETERS
    selection = json.loads((run_dir / 'selection.json').read_text())
    assert [e['year'] for e in selection] == [2014]
    entry = selection[0]
    assert (entry['selection_date'], entry['segment_start'], entry['segment_end']) == (SEGMENT[1], *SEGMENT)
    assert entry['decisions'] == 24 and set(entry['utility']) == set(CANDIDATES)
    assert (run_dir / 'selection.json').read_bytes() == canonical_bytes(selection)
    metrics = json.loads((run_dir / 'metrics.json').read_text())
    assert 'full' not in metrics['periods'] and 'development' not in metrics['periods']
    assert set(metrics['periods']) <= {name for name, _, _ in WF_PERIODS} and 'walk_forward' in metrics['periods']
    assert lines(run_dir, 'signals.csv')[0].split(',') == SIGNAL_COLUMNS_POLICY
    with (run_dir / 'signals.csv').open(newline='', encoding='utf-8') as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 2 * len(RISKY)
    assert [r['decision_session'] for r in rows[::len(RISKY)]] == ['2013-12-31', '2014-01-31']
    # P4: the December decision uses the selection of the next year.
    assert {r['selection_year'] for r in rows} == {'2014'}
    assert {r['selected_config'] for r in rows} == {entry['chosen']}
    weights = list(csv.DictReader((run_dir / 'weights.csv').read_text(encoding='utf-8').splitlines()))
    assert [w['decision_session'] for w in weights] == ['2013-12-31', '2014-01-31']


def test_single_candidate_policy_equals_the_fixed_configuration(tmp_path, no_network, monkeypatch):
    single = engine.Provider(lambda: Policy(engine_adapter(), real_providers(('H1_252_3',)), ('H1_252_3',)),
                             '1', 'monthly', 'policy', {**PARAMETERS, 'candidates': ['H1_252_3']})
    monkeypatch.setitem(engine.PROVIDERS, 'P_single', single)
    policy_dir = policy_run(tmp_path / 'policy', 'P_single')
    fixed_dir = policy_run(tmp_path / 'fixed', 'H1_252_3')
    policy_files, fixed_files = file_hashes(policy_dir), file_hashes(fixed_dir)
    assert set(policy_files) == set(fixed_files) | {'selection.json'}
    shared = set(fixed_files) - {'config.json', 'signals.csv'}
    assert shared == {'decisions.csv', 'orders.csv', 'trades.csv', 'payouts.csv', 'daily.csv', 'invariants.json',
                      'weights.csv', 'metrics.json'}
    for name in sorted(shared):
        assert (policy_dir / name).read_bytes() == (fixed_dir / name).read_bytes(), name
    with (policy_dir / 'signals.csv').open(newline='', encoding='utf-8') as stream:
        policy_rows = list(csv.DictReader(stream))
    with (fixed_dir / 'signals.csv').open(newline='', encoding='utf-8') as stream:
        fixed_rows = list(csv.DictReader(stream))
    assert [{k: r[k] for k in SIGNAL_COLUMNS_H1} for r in policy_rows] == fixed_rows
    assert {(r['selection_year'], r['selected_config']) for r in policy_rows} == {('2014', 'H1_252_3')}
    [entry] = json.loads((policy_dir / 'selection.json').read_text())
    assert entry['chosen'] == 'H1_252_3' and entry['stability']['frequency'] == {'H1_252_3': 1.0}


@pytest.mark.parametrize('stage', [None])
def test_policy_run_requires_stage_five(tmp_path, no_network, stage):
    with pytest.raises(ValueError, match='stage'):
        policy_run(tmp_path, stage=stage)
    assert not (tmp_path / 'experiments/EXPERIMENT_LOG.jsonl').exists()


@pytest.mark.parametrize('stage', [4, '5'])
def test_policy_run_rejects_unknown_stages(tmp_path, no_network, stage):
    with pytest.raises(ValueError, match='stage'):
        policy_run(tmp_path, stage=stage)
    assert not (tmp_path / 'experiments/EXPERIMENT_LOG.jsonl').exists()


@pytest.mark.parametrize('config', [RunConfig(START, END, scenario=Scenario(cost=0.002)),
                                    RunConfig(START, END, scenario=Scenario(lag=2)),
                                    RunConfig(START, END, initial_cash=50000.0)])
def test_policy_run_rejects_a_non_main_scenario(tmp_path, no_network, config):
    derived, digest = vintage(tmp_path)
    with pytest.raises(ValueError, match='main scenario'):
        run_simulation(tmp_path, derived, 'P_A1', config, expected_sha256=digest, stage=5)
    assert not (tmp_path / 'experiments/EXPERIMENT_LOG.jsonl').exists()


def assert_withheld(root, excinfo, capsys, exception, number):
    expected = WITHHELD.format(exception, 'P_A1')
    assert str(excinfo.value) == expected.removeprefix('RuntimeError: ')
    assert excinfo.value.__cause__ is None and excinfo.value.__suppress_context__
    failed = failed_records(root)
    assert len(failed) == 1 and failed[0]['status'] == 'failed' and failed[0]['error'] == expected
    assert number not in json.dumps(journal(root)[1:])
    assert number not in ''.join(traceback.format_exception(excinfo.value))
    captured = capsys.readouterr()
    assert number not in captured.out + captured.err
    assert not (root / 'data/runs').exists()


def test_policy_failure_messages_stay_withheld(tmp_path, no_network, monkeypatch, capsys):
    def raising(t, history):
        raise ValueError('cash -12.5')
    monkeypatch.setitem(engine.PROVIDERS, 'H1_126_3', engine.Provider(raising, '1', 'monthly', 'hypothesis',
                                                                     {'lookback': 126, 'k': 3}))
    with pytest.raises(RuntimeError) as excinfo:
        policy_run(tmp_path)
    assert_withheld(tmp_path, excinfo, capsys, 'ValueError', '12.5')


def test_failed_validation_invariant_stops_the_run_with_a_withheld_message(tmp_path, no_network, monkeypatch,
                                                                         capsys):
    real = engine.simulate

    def broken(market, provider, config):
        result = real(market, provider, config)
        if config.end_session == SEGMENT[1]:
            result.invariants = {**result.invariants, 'passed': False,
                                 'costs': {'passed': False, 'detail': 'gap 4321.5'}}
        return result
    monkeypatch.setattr(engine, 'simulate', broken)
    with pytest.raises(RuntimeError) as excinfo:
        policy_run(tmp_path)
    assert_withheld(tmp_path, excinfo, capsys, 'ValueError', '4321.5')


@pytest.mark.parametrize('target, exception, number', [
    ('result_files', ValueError('cash 12345.67'), '12345.67'), ('freeze', OSError('nav 9876.5'), '9876.5')])
def test_policy_serialization_and_freeze_failures_withheld(tmp_path, no_network, monkeypatch, capsys, target,
                                                           exception, number):
    def raising(*args, **kwargs):
        raise exception
    monkeypatch.setattr(engine, target, raising)
    with pytest.raises(RuntimeError) as excinfo:
        policy_run(tmp_path)
    assert_withheld(tmp_path, excinfo, capsys, type(exception).__name__, number)


def test_policy_run_before_the_first_selection_year_fails_withheld(tmp_path, no_network, capsys):
    derived, digest = vintage(tmp_path)
    with pytest.raises(RuntimeError) as excinfo:
        run_simulation(tmp_path, derived, 'P_A1', RunConfig('2013-10-31', END), expected_sha256=digest, stage=5)
    assert_withheld(tmp_path, excinfo, capsys, 'ValueError', 'outside')


def test_fallback_year_is_a_value_free_quality_warning(tmp_path, no_network, monkeypatch):
    monkeypatch.setattr(inference, 'utility', lambda e: np.full(np.shape(e)[:-1], np.nan))
    run_dir = policy_run(tmp_path)
    completed = journal(tmp_path)[-1]
    assert completed['event'] == 'completed'
    assert completed['quality_warnings'] == ['P_A1 fallback to H1_252_3 for selection year 2014']
    [entry] = json.loads((run_dir / 'selection.json').read_text())
    assert entry['fallback'] is True and entry['chosen'] == 'H1_252_3' and entry['best_utility'] is None
    assert set(entry['utility'].values()) == {None}
    assert entry['stability']['fallback_replicates'] == 1000


# Engine-level selection (spec 12): the real engine.simulate on synthetic markets.

def selection(market, t='2014-01-31'):
    markets = []
    policy = Policy(engine_adapter(markets), real_providers())
    decision = policy(t, market.history(t))
    # Every market handed to the engine ends at the selection date s_Y.
    assert len(markets) == len(CANDIDATES) and all(m.sessions[-1] == SEGMENT[1] for m in markets)
    return policy.selection_log(), decision


@pytest.fixture(scope='module')
def base_selection(base_frames):
    return selection(market_from_frames(base_frames))


def test_selection_is_causal_at_engine_level(base_frames, base_selection):
    # engine.simulate alone already ignores sessions after end_session, so this test cannot detect a missing
    # truncation by itself; the truncation is pinned by
    # test_adaptive.py::test_selection_uses_history_truncated_to_the_selection_date and by the recording assertion
    # in selection() that every market handed to the engine ends at s_Y.
    base_log, base_decision = base_selection
    later = market_from_frames(ramp_after(copy_frames(base_frames), SEGMENT[1]))
    later_log, later_decision = selection(later)
    assert later_log == base_log
    assert later_decision.signals != base_decision.signals, 'the control must change the decision signals at t'

    inside = market_from_frames(ramp_after(copy_frames(base_frames), '2013-06-28'))
    inside_log, _ = selection(inside)
    assert all(inside_log[0]['utility'][k] != base_log[0]['utility'][k] for k in CANDIDATES)


def test_validation_accounts_have_24_decisions_inside_the_segment(base_frames, base_selection, monkeypatch):
    market = market_from_frames(base_frames)
    recorded = []
    real = engine.simulate

    def recording(m, provider, config):
        result = real(m, provider, config)
        recorded.append((m, config, result))
        return result
    monkeypatch.setattr(engine, 'simulate', recording)
    policy = engine.p_a1()  # the registry factory path
    policy('2013-12-31', market.history('2013-12-31'))
    [entry] = policy.selection_log()
    assert len(recorded) == len(CANDIDATES)
    bil = market.close['BIL']
    for (m, config, result), name in zip(recorded, CANDIDATES):
        assert m.sessions[-1] == SEGMENT[1] and (config.start_session, config.end_session) == SEGMENT
        assert config == RunConfig(*SEGMENT) and config.decision_sessions is None
        assert config.scenario == Scenario() and config.initial_cash == 100000.0
        assert result.invariants['passed']
        assert len(result.decisions) == 24
        assert result.decisions[0]['decision_session'] == SEGMENT[0]
        assert result.decisions[-1]['decision_session'] == '2013-11-29'
        assert all(d['execution_session'] <= SEGMENT[1] for d in result.decisions)
        assert [d['session'] for d in result.daily][0] == SEGMENT[0] and result.daily[-1]['session'] == SEGMENT[1]
        navs = [d['nav'] for d in result.daily]
        sessions = [d['session'] for d in result.daily]
        e = [navs[i] / navs[i - 1] - 1 - (bil[sessions[i]] / bil[sessions[i - 1]] - 1) for i in range(1, len(navs))]
        mean = sum(e) / len(e)
        expected = 252 * mean - 1.5 * 252 * sum((x - mean) ** 2 for x in e) / (len(e) - 1)
        assert entry['utility'][name] == pytest.approx(expected, rel=1e-9, abs=1e-12)
    assert entry['decisions'] == 24 and entry['returns'] == len(recorded[0][2].daily) - 1
    # The same selection whichever decision requests it first (here the December close, before: January).
    assert policy.selection_log() == base_selection[0]


def test_a_month_end_missing_from_every_instrument_stops_the_selection(base_frames):
    frames = {t: f.drop(index='2013-06-28') for t, f in copy_frames(base_frames).items()}
    policy = Policy(engine_adapter(), real_providers())
    with pytest.raises(ValueError, match='2014'):
        policy('2014-01-31', market_from_frames(frames).history('2014-01-31'))
    assert policy.selection_log() == []


def test_selection_is_deterministic(base_frames, base_selection):
    again, _ = selection(market_from_frames(base_frames))
    assert again == base_selection[0]
    assert canonical_bytes(again) == canonical_bytes(base_selection[0])


def test_policy_runs_are_deterministic(tmp_path, no_network):
    derived, digest = vintage(tmp_path)
    first = run_simulation(tmp_path, derived, 'P_A1', RunConfig(START, END), expected_sha256=digest, stage=5)
    second = run_simulation(tmp_path, derived, 'P_A1', RunConfig(START, END), expected_sha256=digest, stage=5)
    assert first != second and file_hashes(first) == file_hashes(second)
    assert file_hashes(first)['selection.json'] == sha256((first / 'selection.json').read_bytes())


def test_adaptive_module_has_no_shared_cache():
    assert not any(isinstance(v, dict) for k, v in vars(adaptive).items() if not k.startswith('__'))
    assert not any(isinstance(v, dict) for k, v in vars(Policy).items() if not k.startswith('__'))
