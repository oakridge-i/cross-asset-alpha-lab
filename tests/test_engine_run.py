"""Journaled N2 runs: frozen result files, determinism, failure journaling, simulate CLI."""
import io
import json
import math
import sys
from pathlib import Path
import pytest
from alpha_lab import engine
from alpha_lab.__main__ import main
from alpha_lab.engine import RunConfig, invariant_rotation, run_simulation
from alpha_lab.market import PROXY_BASIS, market_from_frames
from alpha_lab.provenance import sha256, verify
from n2_fixtures import SESSIONS, frame, write_vintage

END = '2017-12-08'
FILES = {'config.json', 'decisions.csv', 'orders.csv', 'trades.csv', 'payouts.csv', 'daily.csv', 'invariants.json'}
BASE = RunConfig('2017-11-28', END)
RICH = RunConfig('2017-11-28', END, ('2017-11-28', '2017-12-04'))
ARGS = ['simulate', 'data/derived/synthetic', '--provider', 'invariant_rotation', '--start', '2017-11-28', '--end', END]


def flat(price):
    return [price] * len(SESSIONS)


def put(values, changes):
    return [changes.get(s, v) for s, v in zip(SESSIONS, values)]


def plain_frames():
    return {'AAA': frame(flat(100.0)), 'BBB': frame(flat(50.0))}


def rich_frames():
    """AAA pays an actual dividend (credited 12-05) and a proxy one (still receivable at the end); BBB splits 2:1."""
    pay = {'2017-11-30': ('2017-12-05', 'actual'), '2017-12-04': ('2017-12-14', PROXY_BASIS)}
    dividend = put(flat(0.0), {'2017-11-30': 1.0, '2017-12-04': 0.5})
    after_split = {s: 50.0 for s in SESSIONS if s >= '2017-12-05'}
    return {'AAA': frame(flat(100.0), dividend=dividend, payable=pay),
            'BBB': frame(put(flat(100.0), after_split), split=put(flat(1.0), {'2017-12-05': 2.0}))}


def vintage(root, frames):
    """Synthetic vintage under root; returns (snapshot path, its manifest sha256)."""
    derived = write_vintage(root, frames)
    return derived, sha256((derived / 'manifest.json').read_bytes())


def execute(root, frames=None, config=BASE, **kwargs):
    derived, digest = vintage(root, frames or plain_frames())
    return run_simulation(root, derived, 'invariant_rotation', config, expected_sha256=digest, **kwargs)


def journal(root):
    return [json.loads(line) for line in (root / 'experiments/EXPERIMENT_LOG.jsonl').read_text(encoding='utf-8').splitlines()]


def lines(run_dir, name):
    return (run_dir / name).read_text(encoding='utf-8').splitlines()


def test_run_is_journaled_and_frozen(tmp_path, no_network):
    run_dir = execute(tmp_path)
    started, completed = journal(tmp_path)
    assert (started['event'], completed['event']) == ('started', 'completed')
    assert started['purpose'] == 'N2 execution run'
    assert set(verify(run_dir)['files']) == FILES
    assert run_dir == tmp_path.resolve() / 'data/runs' / completed['run_id']
    assert completed['output_paths'] == [f'data/runs/{run_dir.name}']
    assert completed['data_sha256'] == sha256((run_dir / 'manifest.json').read_bytes())
    assert completed['quality_warnings'] == [] and completed['universe'] == ['AAA', 'BBB']
    assert started['config']['provider'] == {'name': 'invariant_rotation', 'version': '1'}
    assert started['config']['derived_snapshot'] == 'data/derived/synthetic'
    assert started['config']['decision_sessions'] is None
    assert started['config']['scenario'] == {'cost': 0.001, 'lag': 1, 'reserve': 0.01, 'proxy_pay_days': 10}


def test_run_is_deterministic(tmp_path, no_network):
    derived, digest = vintage(tmp_path, rich_frames())
    first, second = (run_simulation(tmp_path, derived, 'invariant_rotation', RICH, expected_sha256=digest)
                     for _ in range(2))
    assert first != second
    assert verify(first)['files'] == verify(second)['files']


def test_reserved_end_is_failed_run(tmp_path, no_network):
    derived, digest = vintage(tmp_path, plain_frames())
    config = RunConfig('2017-11-28', '2023-01-03')
    with pytest.raises(ValueError, match='after the last open session'):
        run_simulation(tmp_path, derived, 'invariant_rotation', config, expected_sha256=digest)
    assert [r['event'] for r in journal(tmp_path)] == ['started', 'failed']
    assert not (tmp_path / 'data/runs').exists()


def test_other_vintage_is_failed_run(tmp_path, no_network):
    derived, _ = vintage(tmp_path, plain_frames())
    with pytest.raises(ValueError, match='unexpected vintage'):
        run_simulation(tmp_path, derived, 'invariant_rotation', BASE)  # the default pins the approved vintage
    assert [r['event'] for r in journal(tmp_path)] == ['started', 'failed']
    assert not (tmp_path / 'data/runs').exists()


def test_vintage_outside_project_is_failed_run(tmp_path, no_network):
    root = tmp_path / 'project'
    derived, digest = vintage(tmp_path / 'elsewhere', plain_frames())
    with pytest.raises(ValueError, match='outside project'):
        run_simulation(root, derived, 'invariant_rotation', BASE, expected_sha256=digest)
    assert [r['event'] for r in journal(root)] == ['started', 'failed']
    assert not (root / 'data/runs').exists()


def test_failed_invariant_is_frozen_and_journaled(tmp_path, monkeypatch, no_network):
    real = engine.nav
    monkeypatch.setattr(engine, 'nav', lambda account, closes: real(account, closes) + 1.0)
    run_dir = execute(tmp_path)
    last = journal(tmp_path)[-1]
    assert (last['event'], last['quality_warnings']) == ('invariants_failed', ['nav_identity'])
    assert last['output_paths'] == [f'data/runs/{run_dir.name}']
    assert set(verify(run_dir)['files']) == FILES
    invariants = json.loads((run_dir / 'invariants.json').read_bytes())
    assert invariants['passed'] is False and invariants['nav_identity']['passed'] is False
    assert invariants['cash_flow']['passed'] is True


def test_result_files_hold_the_hand_computed_run(tmp_path, no_network):
    """RICH run by hand: 742 AAA + 247 BBB bought 11-29; 12-04 NAV 101014.1; BBB order 419 doubles on the split."""
    derived, digest = vintage(tmp_path, rich_frames())
    run_dir = run_simulation(tmp_path, derived, 'invariant_rotation', RICH, expected_sha256=digest)
    assert json.loads((run_dir / 'config.json').read_bytes()) == {
        'start_session': '2017-11-28', 'end_session': END, 'decision_sessions': ['2017-11-28', '2017-12-04'],
        'initial_cash': 100000.0, 'scenario': {'cost': 0.001, 'lag': 1, 'reserve': 0.01, 'proxy_pay_days': 10},
        'provider': {'name': 'invariant_rotation', 'version': '1'},
        'vintage': 'data/derived/synthetic', 'manifest_sha256': digest}
    assert lines(run_dir, 'decisions.csv') == [
        'decision_session,execution_session,nav,buy_fill,turnover,costs_usd',
        '2017-11-28,2017-11-29,100000,1,0.989,98.9',
        '2017-12-04,2017-12-05,101014.1,1,0.8196875486,82.8']
    assert lines(run_dir, 'orders.csv') == [
        'decision_session,execution_session,ticker,weight,close,target_qty,held_qty,order_qty,filled_qty,'
        'status,cancel_reason',
        '2017-11-28,2017-11-29,AAA,0.75,100,742,0,742,742,filled,',
        '2017-11-28,2017-11-29,BBB,0.25,100,247,0,247,247,filled,',
        '2017-12-04,2017-12-05,AAA,0.3333333333,100,333,742,-409,409,filled,',
        '2017-12-04,2017-12-05,BBB,0.6666666667,100,666,247,838,838,filled,']
    assert lines(run_dir, 'trades.csv') == [
        'session,ticker,side,qty,price,notional,cost,cash_after',
        '2017-11-29,AAA,buy,742,100,74200,74.2,25725.8',
        '2017-11-29,BBB,buy,247,100,24700,24.7,1001.1',
        '2017-12-05,AAA,sell,409,100,40900,40.9,42602.2',
        '2017-12-05,BBB,buy,838,50,41900,41.9,660.3']
    assert lines(run_dir, 'payouts.csv') == [
        'ticker,ex_session,pay_session,pay_basis,qty,amount_per_share,amount,status',
        'AAA,2017-11-30,2017-12-05,actual,742,1,742,paid',
        'AAA,2017-12-04,2017-12-14,proxy_ex_plus_10_calendar_days,742,0.5,371,receivable']
    daily = lines(run_dir, 'daily.csv')
    assert daily[0] == 'session,cash,receivables,positions_value,nav,qty_AAA,qty_BBB' and len(daily) == 10
    assert daily[1] == '2017-11-28,100000,0,0,100000,0,0'
    assert daily[3] == '2017-11-30,1001.1,742,98900,100643.1,742,247'
    assert daily[6] == '2017-12-05,660.3,371,99900,100931.3,333,1332'
    assert daily[9] == '2017-12-08,660.3,371,99900,100931.3,333,1332'
    invariants = json.loads((run_dir / 'invariants.json').read_bytes())
    assert invariants['passed'] is True
    assert invariants['split_events'] == [['BBB', '2017-12-05']]
    assert invariants['proxy_payouts'] == [['AAA', '2017-12-04', '2017-12-14']]


def test_run_without_decisions_freezes_header_only_tables(tmp_path, no_network):
    run_dir = execute(tmp_path, config=RunConfig('2017-11-28', END, ()))
    for name in ('decisions.csv', 'orders.csv', 'trades.csv', 'payouts.csv'):
        assert len(lines(run_dir, name)) == 1
    daily = lines(run_dir, 'daily.csv')
    assert len(daily) == 10 and set(daily[1:]) == {f'{s},100000,0,0,100000,0,0' for s in SESSIONS[1:]}
    assert journal(tmp_path)[-1]['event'] == 'completed'


def test_result_files_carry_no_run_identity(tmp_path, no_network):
    derived, digest = vintage(tmp_path, rich_frames())
    run_dir = run_simulation(tmp_path, derived, 'invariant_rotation', RICH, expected_sha256=digest)
    for name in FILES:
        body = (run_dir / name).read_bytes()
        assert b'\r' not in body
        for identity in (run_dir.name, str(tmp_path), tmp_path.as_posix()):
            assert identity.encode() not in body


def test_invariant_rotation_weights():
    market = market_from_frames({'AAA': frame(flat(10.0)), 'BBB': frame(flat(10.0))})
    july, august = invariant_rotation('2008-07-23', market), invariant_rotation('2008-08-29', market)
    assert list(july) == ['AAA', 'BBB']
    assert july == pytest.approx({'AAA': 0.4, 'BBB': 0.6}, abs=1e-15)  # m = 24103: raw 1 + 1, 1 + 2
    assert august == pytest.approx({'AAA': 0.75, 'BBB': 0.25}, abs=1e-15)  # m = 24104: raw 1 + 2, 1 + 0
    assert math.fsum(july.values()) == pytest.approx(1, abs=1e-12) and all(w > 0 for w in july.values())
    assert july != august


def test_invariant_rotation_uses_only_the_date_and_the_tickers():
    cheap = market_from_frames({'AAA': frame(flat(10.0)), 'BBB': frame(flat(10.0))})
    dear = market_from_frames({'AAA': frame(flat(99.0)), 'BBB': frame(flat(7.0))})
    assert invariant_rotation('2008-07-23', cheap) == invariant_rotation('2008-07-23', dear)
    assert invariant_rotation('2008-07-01', cheap) == invariant_rotation('2008-07-31', cheap)


def test_invariant_rotation_stays_within_the_engine_weight_limit_for_ten_tickers():
    market = market_from_frames({f'T{i}': frame(flat(10.0)) for i in range(10)})
    previous = None
    for year in range(2007, 2023):
        for month in range(1, 13):
            weights = invariant_rotation(f'{year}-{month:02d}-15', market)
            assert list(weights) == list(market.tickers) and min(weights.values()) > 0
            assert 1 - 1e-12 <= math.fsum(weights.values()) <= 1 + engine.WEIGHT_SUM_TOLERANCE
            assert weights != previous
            previous = weights


def cli(tmp_path, derived, digest, *extra):
    return ['simulate', derived.relative_to(tmp_path).as_posix(), '--provider', 'invariant_rotation',
            '--start', '2017-11-28', '--end', END, '--root', str(tmp_path), '--expected-sha256', digest, *extra]


def test_cli_simulate(tmp_path, capsys, no_network):
    derived, digest = vintage(tmp_path, plain_frames())
    main(cli(tmp_path, derived, digest))
    printed = capsys.readouterr().out.strip()
    run_dir = tmp_path / printed
    assert printed.startswith('data/runs/') and '\\' not in printed and not Path(printed).is_absolute()
    assert run_dir.is_dir() and run_dir.parent == tmp_path / 'data/runs'
    assert set(verify(run_dir)['files']) == FILES


def test_cli_simulate_on_cp1252_console(tmp_path, monkeypatch, no_network):
    root = tmp_path / 'проект'
    derived, digest = vintage(root, plain_frames())
    raw = io.BytesIO()
    console = io.TextIOWrapper(raw, encoding='cp1252')
    monkeypatch.setattr(sys, 'stdout', console)
    main(cli(root, derived, digest))
    console.flush()
    printed = raw.getvalue().decode('cp1252')
    assert journal(root)[-1]['status'] == 'completed'
    assert printed.startswith('data/runs/') and len(printed.splitlines()) == 1
    assert (root / printed.strip()).is_dir()


def test_cli_scenario_options_and_parent(tmp_path, capsys, no_network):
    derived, digest = vintage(tmp_path, plain_frames())
    main(cli(tmp_path, derived, digest, '--cost', '0.002', '--lag', '2', '--reserve', '0.02', '--proxy-days', '30',
             '--parent', 'attempt-1'))
    run_dir = tmp_path / capsys.readouterr().out.strip()
    assert json.loads((run_dir / 'config.json').read_bytes())['scenario'] == {
        'cost': 0.002, 'lag': 2, 'reserve': 0.02, 'proxy_pay_days': 30}
    assert journal(tmp_path)[-1]['parent_attempt_id'] == 'attempt-1'


@pytest.mark.parametrize('argv', [ARGS[:1] + ARGS[2:], ARGS[:2] + ARGS[4:], ARGS[:4] + ARGS[6:], ARGS[:6],
                                  ARGS[:3] + ['nope'] + ARGS[4:]],
                         ids=['derived', 'provider', 'start', 'end', 'unknown_provider'])
def test_cli_simulate_refuses_incomplete_arguments(tmp_path, argv):
    with pytest.raises(SystemExit):
        main([*argv, '--root', str(tmp_path)])
    assert not (tmp_path / 'experiments').exists()
