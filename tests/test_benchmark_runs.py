"""Benchmark provider runs: journal entry, frozen target weights, REF_SPY single decision."""
import json
import math
import pytest
from n3_fixtures import benchmark_frames, benchmark_vintage
from alpha_lab import benchmarks
from alpha_lab.engine import PROVIDERS, RunConfig, run_simulation
from alpha_lab.market import market_from_frames
from test_engine_run import FILES, journal, lines

START, END = '2008-12-31', '2009-03-31'
LATER = ('2009-02-13', '2009-02-20', 0.7)


def execute(root, name, **kwargs):
    derived, digest = benchmark_vintage(root, **kwargs)
    return run_simulation(root, derived, name, RunConfig(START, END), expected_sha256=digest)


def test_registry_describes_every_provider():
    assert {n: (p.version, p.schedule, p.kind) for n, p in PROVIDERS.items()} == {
        'invariant_rotation': ('1', 'monthly', 'test'),
        **{n: ('1', 'monthly', 'benchmark') for n in ('B0', 'B1', 'B2', 'B3')},
        'REF_SPY': ('1', 'first_only', 'benchmark'),
        'H1_252_3': ('1', 'monthly', 'hypothesis'),
        'H1_252_4': ('1', 'monthly', 'hypothesis'),
        'H1_126_3': ('1', 'monthly', 'hypothesis'),
        'H1_126_4': ('1', 'monthly', 'hypothesis'),
        'H2_4of6': ('1', 'monthly', 'hypothesis'),
        'H2_5of6': ('1', 'monthly', 'hypothesis')}


def test_benchmark_run_is_journaled_with_candidate(tmp_path, no_network):
    execute(tmp_path, 'B2')
    started, completed = journal(tmp_path)
    assert (started['event'], completed['event']) == ('started', 'completed')
    assert started['purpose'] == completed['purpose'] == 'N3 benchmark run'
    assert started['candidate_ids'] == completed['candidate_ids'] == ['B2']


def test_benchmark_run_freezes_weights(tmp_path, no_network):
    run_dir = execute(tmp_path, 'B2')
    assert set(json.loads((run_dir / 'manifest.json').read_text())['files']) == FILES | {'weights.csv', 'metrics.json'}
    rows = lines(run_dir, 'weights.csv')
    tickers = sorted(benchmark_frames())
    assert rows[0] == ','.join(['decision_session', *(f'w_{t}' for t in tickers), 'usd'])
    decisions = [r.split(',')[0] for r in lines(run_dir, 'decisions.csv')[1:]]
    assert decisions == [r.split(',')[0] for r in rows[1:]] and decisions[0] == START
    assert lines(run_dir, 'decisions.csv')[1].split(',')[1] == '2009-01-02'
    market = market_from_frames(benchmark_frames())
    first = [float(x) for x in rows[1].split(',')[1:]]
    expected = benchmarks.b2(START, market.history(START))
    assert first[:-1] == pytest.approx([expected[t] for t in tickers], rel=1e-9, abs=1e-9)
    assert first[-1] == pytest.approx(1 - math.fsum(expected.values()), abs=1e-9)


def test_ref_spy_single_decision_and_no_later_trades(tmp_path, no_network):
    run_dir = execute(tmp_path, 'REF_SPY', spy_dividends=(LATER,))
    assert json.loads((run_dir / 'config.json').read_text())['decision_sessions'] == [START]
    assert journal(tmp_path)[0]['config']['decision_sessions'] == [START]
    assert len(lines(run_dir, 'weights.csv')) == 2
    trades = lines(run_dir, 'trades.csv')[1:]
    assert trades and {r.split(',')[0] for r in trades} == {'2009-01-02'}
    payouts = lines(run_dir, 'payouts.csv')
    assert any(r.startswith('SPY,2009-02-13,2009-02-20') and r.endswith('paid') for r in payouts)
    daily = lines(run_dir, 'daily.csv')
    header = daily[0].split(',')
    last = dict(zip(header, daily[-1].split(',')))
    assert float(last['cash']) > 0 and float(last['qty_SPY']) == float(daily[-2].split(',')[header.index('qty_SPY')])


def test_test_provider_keeps_seven_files(tmp_path, no_network):
    run_dir = execute(tmp_path, 'invariant_rotation')
    assert set(json.loads((run_dir / 'manifest.json').read_text())['files']) == FILES
    started = journal(tmp_path)[0]
    assert started['candidate_ids'] == [] and started['purpose'] == 'N2 execution run'


def test_benchmark_runs_are_deterministic(tmp_path, no_network):
    first = execute(tmp_path / 'a', 'B3')
    second = execute(tmp_path / 'b', 'B3')
    files = [json.loads((d / 'manifest.json').read_text())['files'] for d in (first, second)]
    assert files[0] == files[1]
