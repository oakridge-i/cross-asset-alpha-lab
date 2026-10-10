"""Hypothesis provider runs: journal, frozen files, signal records, withheld failure messages and engine-level
causality."""
import csv
import json
import math
import traceback
import numpy as np
import pytest
from n3_fixtures import RISKY, benchmark_frames, benchmark_vintage
from n2_fixtures import write_vintage
from alpha_lab import engine
from alpha_lab.__main__ import main
from alpha_lab.engine import PROVIDERS, Result, RunConfig, provider_weights, result_files, run_simulation
from alpha_lab.hypotheses import SIGNAL_COLUMNS_H1, SIGNAL_COLUMNS_H2
from alpha_lab.market import load_market, market_from_frames
from alpha_lab.provenance import sha256
from test_engine_run import FILES, journal, lines

START, END = '2008-12-31', '2009-03-31'
HYPOTHESIS_FILES = FILES | {'weights.csv', 'signals.csv'}
PARAMETERS = {'H1_252_3': {'lookback': 252, 'k': 3}, 'H1_252_4': {'lookback': 252, 'k': 4},
              'H1_126_3': {'lookback': 126, 'k': 3}, 'H1_126_4': {'lookback': 126, 'k': 4},
              'H2_4of6': {'h': 4, 'parent': 'H1_252_3'}, 'H2_5of6': {'h': 5, 'parent': 'H1_252_3'}}
WITHHELD = 'RuntimeError: {} in {} run; message withheld under the N4 viewing restriction'


def execute(root, name, **kwargs):
    derived, digest = benchmark_vintage(root, **kwargs)
    return run_simulation(root, derived, name, RunConfig(START, END), expected_sha256=digest)


def failed_records(root):
    return [r for r in journal(root) if r['event'] == 'failed']


@pytest.mark.parametrize('name', sorted(PARAMETERS))
def test_hypothesis_run_files_and_journal(tmp_path, no_network, name):
    run_dir = execute(tmp_path, name)
    started, completed = journal(tmp_path)
    manifest = json.loads((run_dir / 'manifest.json').read_text())
    assert set(manifest['files']) == HYPOTHESIS_FILES
    assert started['purpose'] == completed['purpose'] == 'N4 hypothesis run'
    assert started['candidate_ids'] == completed['candidate_ids'] == [name]
    assert completed['event'] == 'completed'
    assert json.loads((run_dir / 'config.json').read_text())['provider']['parameters'] == PARAMETERS[name]
    assert started['config']['provider']['parameters'] == PARAMETERS[name]


def test_benchmark_config_has_no_parameters(tmp_path, no_network):
    config = json.loads((execute(tmp_path, 'B2') / 'config.json').read_text())
    assert set(config['provider']) == {'name', 'version'}


@pytest.mark.parametrize('name, columns', [('H1_252_3', SIGNAL_COLUMNS_H1), ('H2_4of6', SIGNAL_COLUMNS_H2)])
def test_signals_csv_columns_and_order(tmp_path, no_network, name, columns):
    run_dir = execute(tmp_path, name, drift={'DBC': -0.002, 'HYG': -0.002})
    with (run_dir / 'signals.csv').open(newline='', encoding='utf-8') as stream:
        rows = list(csv.DictReader(stream))
    assert b'\r' not in (run_dir / 'signals.csv').read_bytes()
    assert lines(run_dir, 'signals.csv')[0].split(',') == columns
    risky = sorted(RISKY)
    assert len(rows) % len(risky) == 0 and len(rows) >= 3 * len(risky)
    decisions = [r['decision_session'] for r in rows[::len(risky)]]
    assert decisions == sorted(decisions) and len(set(decisions)) == len(decisions)
    for i in range(0, len(rows), len(risky)):
        block = rows[i:i + len(risky)]
        assert {r['decision_session'] for r in block} == {decisions[i // len(risky)]}
        assert [r['ticker'] for r in block] == risky == sorted(risky)
    assert all((r['rank'] == '') == (r['eligible'] == 'False') for r in rows)
    assert any(r['rank'] == '' for r in rows) and any(r['rank'] != '' for r in rows)
    assert all(r['rank'].isdigit() for r in rows if r['rank'])
    assert {r['selected'] for r in rows} <= {'True', 'False'}


def test_zero_decision_run_keeps_the_signal_header_of_its_configuration():
    market = market_from_frames(benchmark_frames())
    empty = Result([], [], [], [], [], {'passed': True})
    for name, columns in (('H1_126_4', SIGNAL_COLUMNS_H1), ('H2_5of6', SIGNAL_COLUMNS_H2)):
        files = result_files(empty, RunConfig(START, END), name, market)
        assert files['signals.csv'] == (','.join(columns) + '\n').encode()


def test_hypothesis_runs_are_deterministic(tmp_path, no_network):
    derived, digest = benchmark_vintage(tmp_path)
    first = run_simulation(tmp_path, derived, 'H2_4of6', RunConfig(START, END), expected_sha256=digest)
    second = run_simulation(tmp_path, derived, 'H2_4of6', RunConfig(START, END), expected_sha256=digest)
    assert first != second
    assert json.loads((first / 'manifest.json').read_text())['files'] == \
        json.loads((second / 'manifest.json').read_text())['files']


def test_compute_metrics_not_called_for_hypotheses(tmp_path, no_network, monkeypatch):
    def refuse(*args, **kwargs):
        raise AssertionError('compute_metrics called for a hypothesis run')
    monkeypatch.setattr(engine, 'compute_metrics', refuse)
    run_dir = execute(tmp_path, 'H1_126_3')
    assert 'metrics.json' not in json.loads((run_dir / 'manifest.json').read_text())['files']
    assert not (run_dir / 'metrics.json').exists()


def test_h2_run_with_mid_month_decision_fails(tmp_path, no_network):
    derived, digest = benchmark_vintage(tmp_path)
    config = RunConfig(START, END, decision_sessions=('2009-01-15',))
    with pytest.raises(RuntimeError) as excinfo:
        run_simulation(tmp_path, derived, 'H2_4of6', config, expected_sha256=digest)
    expected = WITHHELD.format('ValueError', 'H2_4of6')
    assert str(excinfo.value) == expected.removeprefix('RuntimeError: ')
    failed = failed_records(tmp_path)
    assert len(failed) == 1 and failed[0]['status'] == 'failed' and failed[0]['error'] == expected
    assert not (tmp_path / 'data/runs').exists()


def test_failure_message_withheld(tmp_path, no_network, monkeypatch):
    def raising(t, history):
        raise ValueError('cash -12.5')
    monkeypatch.setitem(engine.PROVIDERS, 'H1_252_3',
                        engine.Provider(raising, '1', 'monthly', 'hypothesis', PARAMETERS['H1_252_3']))
    derived, digest = benchmark_vintage(tmp_path)
    with pytest.raises(RuntimeError) as excinfo:
        run_simulation(tmp_path, derived, 'H1_252_3', RunConfig(START, END), expected_sha256=digest)
    expected = WITHHELD.format('ValueError', 'H1_252_3')
    assert str(excinfo.value) == expected.removeprefix('RuntimeError: ')
    failed = failed_records(tmp_path)
    assert len(failed) == 1 and failed[0]['error'] == expected
    assert '12.5' not in json.dumps(journal(tmp_path)[1:])
    rendered = ''.join(traceback.format_exception(excinfo.value))
    assert '12.5' not in rendered


@pytest.mark.parametrize('target, exception, number', [
    ('result_files', ValueError('cash 12345.67'), '12345.67'), ('freeze', OSError('nav 9876.5'), '9876.5')])
def test_serialization_and_freeze_failures_withheld(tmp_path, no_network, monkeypatch, capsys, target, exception,
                                                    number):
    def raising(*args, **kwargs):
        raise exception
    monkeypatch.setattr(engine, target, raising)
    derived, digest = benchmark_vintage(tmp_path)
    with pytest.raises(RuntimeError) as excinfo:
        run_simulation(tmp_path, derived, 'H1_252_3', RunConfig(START, END), expected_sha256=digest)
    expected = WITHHELD.format(type(exception).__name__, 'H1_252_3')
    assert str(excinfo.value) == expected.removeprefix('RuntimeError: ')
    assert excinfo.value.__cause__ is None and excinfo.value.__suppress_context__
    failed = failed_records(tmp_path)
    assert len(failed) == 1 and failed[0]['status'] == 'failed' and failed[0]['error'] == expected
    assert number not in json.dumps(journal(tmp_path)[1:])
    assert number not in ''.join(traceback.format_exception(excinfo.value))
    captured = capsys.readouterr()
    assert number not in captured.out + captured.err


@pytest.mark.parametrize('target, exception', [('result_files', ValueError('cash 12345.67')),
                                               ('freeze', OSError('nav 9876.5'))])
@pytest.mark.parametrize('name', ['B0', 'invariant_rotation'])
def test_non_hypothesis_serialization_failures_propagate_unchanged(tmp_path, no_network, monkeypatch, target,
                                                                   exception, name):
    def raising(*args, **kwargs):
        raise exception
    monkeypatch.setattr(engine, target, raising)
    derived, digest = benchmark_vintage(tmp_path)
    with pytest.raises(type(exception)) as excinfo:
        run_simulation(tmp_path, derived, name, RunConfig(START, END), expected_sha256=digest)
    assert excinfo.value is exception
    failed = failed_records(tmp_path)
    assert len(failed) == 1 and failed[0]['error'] == f'{type(exception).__name__}: {exception}'


def test_non_hypothesis_failures_keep_their_messages(tmp_path, no_network):
    derived, digest = benchmark_vintage(tmp_path)
    with pytest.raises(ValueError, match='after the last open session'):
        run_simulation(tmp_path, derived, 'B0', RunConfig(START, '2023-01-03'), expected_sha256=digest)
    assert failed_records(tmp_path)[0]['error'].startswith('ValueError: ')


def frames_vintage(root, frames):
    derived = write_vintage(root, frames)
    return derived, sha256((derived / 'manifest.json').read_bytes())


def run_rows(root, frames, name):
    derived, digest = frames_vintage(root, frames)
    run_dir = run_simulation(root, derived, name, RunConfig(START, END), expected_sha256=digest)
    return {file: list(csv.DictReader((run_dir / file).read_text(encoding='utf-8').splitlines()))
            for file in ('weights.csv', 'signals.csv', 'payouts.csv')}


def with_dividend(frames, ticker, ex, pay, amount):
    frames[ticker].loc[ex, ['dividend', 'payable_date', 'payable_basis']] = [amount, pay, 'actual']
    return frames


def through(rows, t):
    return [r for r in rows if r['decision_session'] <= t]


@pytest.mark.parametrize('name', ['H1_252_3', 'H2_4of6'])
def test_decisions_causal_at_engine_level(tmp_path, no_network, name):
    t = '2009-01-30'
    base = run_rows(tmp_path / 'a', with_dividend(benchmark_frames(), 'EEM', '2009-01-15', '2009-01-23', 0.4), name)
    assert len({r['decision_session'] for r in base['weights.csv']}) >= 3
    assert len(through(base['weights.csv'], t)) >= 2

    # B: prices and a distribution after t differ.
    changed = with_dividend(with_dividend(benchmark_frames(), 'EEM', '2009-01-15', '2009-01-23', 0.4),
                            'EEM', '2009-02-12', '2009-02-24', 0.9)
    for i, frame in enumerate(changed.values()):
        after = frame.index > t
        factor = 1.0 + 0.03 * (i + 1) * np.arange(1, after.sum() + 1) / after.sum()
        frame.loc[after, ['open', 'close']] = frame.loc[after, ['open', 'close']].mul(factor, axis=0).to_numpy()
    other = run_rows(tmp_path / 'b', changed, name)
    for file in ('weights.csv', 'signals.csv'):
        assert through(other[file], t) == through(base[file], t)
    assert other['signals.csv'] != base['signals.csv'], 'the control vintage must change a later decision'

    # C: only the payment session of an actual distribution moves later, past t.
    moved = run_rows(tmp_path / 'c', with_dividend(benchmark_frames(), 'EEM', '2009-01-15', '2009-02-10', 0.4), name)
    for file in ('weights.csv', 'signals.csv'):
        assert through(moved[file], t) == through(base[file], t)
    assert base['payouts.csv'] and moved['payouts.csv'] != base['payouts.csv']


def with_split(frames, session, ratio):
    """Every ticker splits `ratio`-for-1 on `session`: raw prices and per-share dividends from then on are divided by
    the ratio, so total returns are unchanged and only quantities move."""
    for frame in frames.values():
        frame.loc[session, 'split_ratio'] = ratio
        after = frame.index >= session
        frame.loc[after, ['open', 'close', 'dividend']] = frame.loc[after, ['open', 'close', 'dividend']] / ratio
    return frames


@pytest.mark.parametrize('name', ['H1_252_3', 'H2_4of6'])
def test_decisions_unchanged_by_a_later_split_at_engine_level(tmp_path, no_network, name):
    """Prices are raw and the adjusted history is built from the sessions up to t only, so a split dated after t
    cannot reach a decision at or before t; with total returns unchanged by construction the later decisions do not
    change either, so the control is the executed split and the changed quantities."""
    t = '2009-01-30'
    split_session = '2009-02-12'
    results = {}
    for label, frames in (('base', benchmark_frames()), ('split', with_split(benchmark_frames(), split_session, 2.0))):
        derived, digest = frames_vintage(tmp_path / label, frames)
        run_dir = run_simulation(tmp_path / label, derived, name, RunConfig(START, END), expected_sha256=digest)
        results[label] = {file: (run_dir / file).read_text(encoding='utf-8')
                          for file in ('weights.csv', 'signals.csv', 'daily.csv', 'invariants.json')}
    base, split = results['base'], results['split']
    rows = {label: {file: list(csv.DictReader(r[file].splitlines())) for file in ('weights.csv', 'signals.csv')}
            for label, r in results.items()}
    assert len(through(rows['base']['weights.csv'], t)) >= 2
    for file in ('weights.csv', 'signals.csv'):
        assert through(rows['split'][file], t) == through(rows['base'][file], t)
    assert json.loads(base['invariants.json'])['split_events'] == []
    assert json.loads(split['invariants.json'])['split_events'], 'the split must reach the executed account'
    assert split['daily.csv'] != base['daily.csv']


def test_registry_describes_every_provider():
    assert {n: (p.version, p.schedule, p.kind, p.parameters) for n, p in PROVIDERS.items()} == {
        'invariant_rotation': ('1', 'monthly', 'test', {}),
        **{n: ('1', 'monthly', 'benchmark', {}) for n in ('B0', 'B1', 'B2', 'B3')},
        'REF_SPY': ('1', 'first_only', 'benchmark', {}),
        **{n: ('1', 'monthly', 'hypothesis', p) for n, p in PARAMETERS.items()},
        'P_A1': ('1', 'monthly', 'policy', {'candidates': ['H1_252_3', 'H1_252_4', 'H1_126_3', 'H1_126_4'],
                                            'validation_years': 2, 'context_years': 3, 'tolerance': 0.001,
                                            'penalty': 1.5})}


def test_provider_weights_unchanged_for_dict_providers(tmp_path, no_network):
    derived, digest = benchmark_vintage(tmp_path)
    market = load_market(tmp_path, derived, digest)
    weights = provider_weights(PROVIDERS['B0'].function, market, START)
    assert set(weights) == set(market.tickers)
    assert all(isinstance(w, float) and w >= 0 for w in weights.values())
    assert math.fsum(weights.values()) <= 1 + 1e-12
    assert weights == PROVIDERS['B0'].function(START, market.history(START))
    hypothesis = provider_weights(PROVIDERS['H1_252_3'].function, market, START)
    assert set(hypothesis) == set(market.tickers)


def staged(root, name, stage):
    derived, digest = benchmark_vintage(root)
    return run_simulation(root, derived, name, RunConfig(START, END), expected_sha256=digest, stage=stage)


def file_hashes(run_dir):
    return json.loads((run_dir / 'manifest.json').read_text())['files']


@pytest.mark.parametrize('name', ['H1_252_3', 'H2_4of6'])
def test_stage_five_hypothesis_run_has_ten_files_and_the_n5_purpose(tmp_path, no_network, name):
    old = staged(tmp_path / 'old', name, None)
    new = staged(tmp_path / 'new', name, 5)
    started, completed = journal(tmp_path / 'new')
    assert started['purpose'] == completed['purpose'] == 'N5 hypothesis run'
    assert started['candidate_ids'] == completed['candidate_ids'] == [name]
    assert completed['event'] == 'completed'
    old_files, new_files = file_hashes(old), file_hashes(new)
    assert set(new_files) == HYPOTHESIS_FILES | {'metrics.json'} and len(new_files) == 10
    assert {k: v for k, v in new_files.items() if k != 'metrics.json'} == old_files
    metrics = json.loads((new / 'metrics.json').read_text())
    assert metrics['schema_version'] == 1 and 'full' in metrics['periods']
    assert new_files['metrics.json'] == sha256((new / 'metrics.json').read_bytes())


def test_stage_five_benchmark_files_are_identical_to_stage_none(tmp_path, no_network):
    old = staged(tmp_path / 'old', 'B2', None)
    new = staged(tmp_path / 'new', 'B2', 5)
    assert file_hashes(new) == file_hashes(old)
    assert len(file_hashes(new)) == 9
    assert journal(tmp_path / 'old')[0]['purpose'] == 'N3 benchmark run'
    assert [r['purpose'] for r in journal(tmp_path / 'new')] == ['N5 benchmark run'] * 2


def test_stage_none_hypothesis_run_is_unchanged(tmp_path, no_network):
    run_dir = staged(tmp_path, 'H1_126_4', None)
    assert set(file_hashes(run_dir)) == HYPOTHESIS_FILES and len(file_hashes(run_dir)) == 9
    assert not (run_dir / 'metrics.json').exists()
    assert [r['purpose'] for r in journal(tmp_path)] == ['N4 hypothesis run'] * 2


def test_stage_five_failure_messages_stay_withheld(tmp_path, no_network, monkeypatch):
    def raising(t, history):
        raise ValueError('cash -12.5')
    monkeypatch.setitem(engine.PROVIDERS, 'H1_252_3',
                        engine.Provider(raising, '1', 'monthly', 'hypothesis', PARAMETERS['H1_252_3']))
    with pytest.raises(RuntimeError) as excinfo:
        staged(tmp_path, 'H1_252_3', 5)
    expected = WITHHELD.format('ValueError', 'H1_252_3').replace('N4 viewing restriction', 'N5 viewing procedure')
    assert str(excinfo.value) == expected.removeprefix('RuntimeError: ')
    assert excinfo.value.__cause__ is None and excinfo.value.__suppress_context__
    failed = failed_records(tmp_path)
    assert len(failed) == 1 and failed[0]['error'] == expected
    assert '12.5' not in json.dumps(journal(tmp_path)[1:])
    assert '12.5' not in ''.join(traceback.format_exception(excinfo.value))


def cli_argv(root, derived, digest, name, *extra):
    return ['simulate', derived.relative_to(root).as_posix(), '--provider', name, '--start', START, '--end', END,
            '--root', str(root), '--expected-sha256', digest, *extra]


def cli_run(root, name, *extra):
    derived, digest = benchmark_vintage(root)
    main(cli_argv(root, derived, digest, name, *extra))
    return root / journal(root)[-1]['output_paths'][0]


def test_cli_simulate_stage_five_option(tmp_path, no_network):
    """The --stage 5 option of the simulate command line reaches run_simulation (the real-vintage CLI is not run)."""
    b0 = cli_run(tmp_path / 'b0', 'B0', '--stage', '5')
    assert [r['purpose'] for r in journal(tmp_path / 'b0')] == ['N5 benchmark run'] * 2
    assert len(file_hashes(b0)) == 9 and 'metrics.json' in file_hashes(b0)
    h1 = cli_run(tmp_path / 'h1', 'H1_252_3', '--stage', '5')
    assert [r['purpose'] for r in journal(tmp_path / 'h1')] == ['N5 hypothesis run'] * 2
    assert len(file_hashes(h1)) == 10 and 'metrics.json' in file_hashes(h1)
    plain = cli_run(tmp_path / 'plain', 'H1_252_3')
    assert [r['purpose'] for r in journal(tmp_path / 'plain')] == ['N4 hypothesis run'] * 2
    assert len(file_hashes(plain)) == 9 and not (plain / 'metrics.json').exists()


def test_cli_simulate_rejects_stage_four(tmp_path, no_network):
    derived, digest = benchmark_vintage(tmp_path)
    with pytest.raises(SystemExit) as exit_info:
        main(cli_argv(tmp_path, derived, digest, 'H1_252_3', '--stage', '4'))
    assert exit_info.value.code == 2
    assert not (tmp_path / 'experiments').exists()


@pytest.mark.parametrize('stage', [4, 0, '5'])
def test_unknown_stage_raises_before_any_journal_record(tmp_path, no_network, stage):
    with pytest.raises(ValueError, match='stage'):
        staged(tmp_path, 'H1_252_3', stage)
    assert not (tmp_path / 'experiments/EXPERIMENT_LOG.jsonl').exists()


def test_stage_five_test_provider_raises_before_any_journal_record(tmp_path, no_network):
    with pytest.raises(ValueError, match='stage'):
        staged(tmp_path, 'invariant_rotation', 5)
    assert not (tmp_path / 'experiments/EXPERIMENT_LOG.jsonl').exists()
