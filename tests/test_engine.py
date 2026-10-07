"""Simulation loop: hand-checked reconciliations (docs/n2/manual_reconciliation.md), validation, invariants."""
import math
import numpy as np
import pytest
from alpha_lab import engine
from alpha_lab.engine import RunConfig, Scenario, month_end_sessions, simulate
from alpha_lab.market import PROXY_BASIS, market_from_frames
from n2_fixtures import SESSIONS, frame

END = '2017-12-08'
CHECKS = ['cash_non_negative', 'nav_identity', 'cash_flow', 'split_quantity_only', 'receivable_conservation',
          'execution_timing', 'costs']


def flat(price):
    return [price] * len(SESSIONS)


def put(values, changes):
    """List `values` with entries replaced by session -> value."""
    return [changes.get(s, v) for s, v in zip(SESSIONS, values)]


def since(first, value):
    return {s: value for s in SESSIONS if s >= first}


def provider(plan):
    return lambda t, history: {k: plan[t].get(k, 0.0) for k in history.tickers}


def run(frames, plan, scenario=Scenario(), end=END, **config):
    market = market_from_frames(frames)
    cfg = RunConfig(min(plan), end, tuple(sorted(plan)), scenario, **config)
    return simulate(market, provider(plan), cfg)


def trades_of(result, session):
    return [t for t in result.trades if t.session == session]


def cash_on(result, session):
    return next(d['cash'] for d in result.daily if d['session'] == session)


def row_on(result, session):
    return next(d for d in result.daily if d['session'] == session)


def case1(late_close=100.0, late_open=100.0):
    close = put(flat(100.0), since('2017-11-30', late_close))
    open_ = put(put(flat(100.0), {'2017-11-29': 100.5}), since('2017-11-30', late_open))
    return run({'AAA': frame(close, open=open_)}, {'2017-11-28': {'AAA': 1.0}})


def case2():
    price = put(flat(91.0), since('2017-12-05', 182.0))
    f = frame(price, split=put(flat(1.0), {'2017-12-05': 0.5}))
    plan = {'2017-11-28': {'BBB': 1.0}, '2017-12-04': {'BBB': 0.5}, '2017-12-06': {'BBB': 0.0}}
    return run({'BBB': f}, plan)


def case2b():
    price = put(flat(61.0), since('2017-12-05', 20.0))
    f = frame(price, split=put(flat(1.0), {'2017-12-05': 3.0}))
    return run({'CCC': f}, {'2017-11-28': {'CCC': 0.5}, '2017-12-04': {'CCC': 1.0}})


def case3():
    pay = {'2017-11-30': ('2017-12-05', 'actual')}
    f = lambda: frame(flat(49.0), dividend=put(flat(0.0), {'2017-11-30': 1.0}), payable=pay)
    plan = {'2017-11-28': {'DDD': 1.0}, '2017-11-29': {'DDD': 0.0, 'EEE': 1.0}, '2017-12-04': {'EEE': 1.0}}
    return run({'DDD': f(), 'EEE': f()}, plan)


def case3b(days=10):
    pay = {'2017-11-30': ('2017-12-11', PROXY_BASIS)}
    f = frame(flat(41.0), dividend=put(flat(0.0), {'2017-11-30': 0.25}), payable=pay)
    return run({'FFF': f}, {'2017-11-28': {'FFF': 1.0}}, Scenario(proxy_pay_days=days))


def case4():
    f = frame(flat(97.0), open=put(flat(97.0), {'2017-11-29': 99.0}))
    return run({'GGG': f}, {'2017-11-28': {'GGG': 1.0}})


def case5():
    plan = {'2017-11-28': {'HHH': 1.0}, '2017-11-29': {'HHH': 0.0, 'III': 1.0}}
    return run({'HHH': frame(flat(80.0)), 'III': frame(flat(40.0))}, plan)


def case6():
    f = frame(flat(97.0), open=put(flat(97.0), {'2017-11-29': 50.0, '2017-11-30': 98.0}))
    return run({'JJJ': f}, {'2017-11-28': {'JJJ': 1.0}}, Scenario(lag=2))


def case6b():
    f = frame(flat(97.0), open=put(flat(97.0), {'2017-11-29': math.nan}))
    return run({'KKK': f}, {'2017-11-28': {'KKK': 1.0}})


def test_case1_before_after_open():
    result = case1()
    [order] = result.orders
    assert (order.ticker, order.target_qty, order.qty, order.close) == ('AAA', 990, 990.0, 100.0)
    [trade] = result.trades
    assert (trade.session, trade.side, trade.qty, trade.price) == ('2017-11-29', 'buy', 990.0, 100.5)
    assert trade.cost == pytest.approx(99.495, abs=1e-9)
    assert trade.cash_after == pytest.approx(405.505, abs=1e-9)
    day = row_on(result, '2017-11-29')
    assert day['cash'] == pytest.approx(405.505, abs=1e-9) and day['AAA'] == 990.0
    assert day['nav'] == pytest.approx(99405.505, abs=1e-9)
    changed = case1(late_close=250.0, late_open=17.0)
    assert [(o.target_qty, o.close) for o in changed.orders] == [(o.target_qty, o.close) for o in result.orders]


def test_case2_reverse_split_with_pending_order():
    result = case2()
    [buy] = trades_of(result, '2017-11-29')
    assert (buy.side, buy.qty, buy.price) == ('buy', 1087.0, 91.0)
    assert cash_on(result, '2017-11-29') == pytest.approx(984.083, abs=1e-9)
    first, second, third = result.orders
    assert first.target_qty == 1087
    assert (second.decision_session, second.target_qty, second.held_qty) == ('2017-12-04', 543, 1087.0)
    assert second.qty == -272.0 and second.filled_qty == 272.0 and second.status == 'filled'
    decision = next(d for d in result.decisions if d['decision_session'] == '2017-12-04')
    assert decision['nav'] == pytest.approx(99901.083, abs=1e-9)
    [sell] = trades_of(result, '2017-12-05')
    assert (sell.side, sell.qty, sell.price) == ('sell', 272.0, 182.0)
    assert sell.notional * 0.999 == pytest.approx(49454.496, abs=1e-9)
    assert cash_on(result, '2017-12-05') == pytest.approx(50438.579, abs=1e-9)
    assert row_on(result, '2017-12-05')['BBB'] == 271.5
    assert (third.target_qty, third.held_qty, third.qty) == (0, 271.5, -271.5)
    [last] = trades_of(result, '2017-12-07')
    assert (last.side, last.qty, last.price) == ('sell', 271.5, 182.0)
    assert last.notional * 0.999 == pytest.approx(49363.587, abs=1e-9)
    assert cash_on(result, '2017-12-07') == pytest.approx(99802.166, abs=1e-9)
    assert row_on(result, '2017-12-07')['BBB'] == 0.0
    assert result.invariants['split_events'] == [['BBB', '2017-12-05']]


def test_case2b_forward_split_with_pending_order():
    result = case2b()
    [buy] = trades_of(result, '2017-11-29')
    assert (buy.side, buy.qty, buy.price) == ('buy', 811.0, 61.0)
    assert cash_on(result, '2017-11-29') == pytest.approx(50479.529, abs=1e-9)
    first, second = result.orders
    assert first.target_qty == 811
    decision = next(d for d in result.decisions if d['decision_session'] == '2017-12-04')
    assert decision['nav'] == pytest.approx(99950.529, abs=1e-9)
    assert (second.target_qty, second.held_qty) == (1622, 811.0)
    assert second.qty == 2433.0 and second.filled_qty == 2433.0 and second.status == 'filled'
    [late] = trades_of(result, '2017-12-05')
    assert (late.side, late.qty, late.price) == ('buy', 2433.0, 20.0)
    assert late.notional * 1.001 == pytest.approx(48708.66, abs=1e-9)
    assert result.decisions[1]['buy_fill'] == 1.0
    day = row_on(result, '2017-12-05')
    assert day['CCC'] == 4866.0 and day['cash'] == pytest.approx(1770.869, abs=1e-9)
    assert day['nav'] == pytest.approx(99090.869, abs=1e-9)
    assert result.invariants['split_events'] == [['CCC', '2017-12-05']]


def test_case3_ex_and_pay():
    result = case3()
    [buy] = trades_of(result, '2017-11-29')
    assert (buy.ticker, buy.qty) == ('DDD', 2020.0)
    assert cash_on(result, '2017-11-29') == pytest.approx(921.02, abs=1e-9)
    [receivable] = result.payouts
    assert (receivable.ticker, receivable.ex_session, receivable.pay_session, receivable.basis) == (
        'DDD', '2017-11-30', '2017-12-05', 'actual')
    assert receivable.qty == 2020.0 and receivable.amount == pytest.approx(2020.0, abs=1e-9)
    assert receivable.status == 'paid'
    sell, buy = trades_of(result, '2017-11-30')
    assert (sell.ticker, sell.side, sell.qty) == ('DDD', 'sell', 2020.0)
    assert sell.notional * 0.999 == pytest.approx(98881.02, abs=1e-9)
    assert (buy.ticker, buy.side, buy.qty) == ('EEE', 'buy', 2018.0)
    assert buy.notional * 1.001 == pytest.approx(98980.882, abs=1e-9)
    day = row_on(result, '2017-11-30')
    assert day['cash'] == pytest.approx(821.158, abs=1e-9) and day['receivables'] == pytest.approx(2020.0, abs=1e-9)
    assert day['nav'] == pytest.approx(101723.158, abs=1e-9)
    order = next(o for o in result.orders if o.decision_session == '2017-12-04')
    assert (order.ticker, order.target_qty, order.held_qty, order.qty) == ('EEE', 2055, 2018.0, 37.0)
    [late] = trades_of(result, '2017-12-05')
    assert (late.ticker, late.qty) == ('EEE', 37.0)
    assert late.notional * 1.001 == pytest.approx(1814.813, abs=1e-9)
    day = row_on(result, '2017-12-05')
    assert day['cash'] == pytest.approx(1026.345, abs=1e-9) and day['receivables'] == 0.0
    assert day['nav'] == pytest.approx(101721.345, abs=1e-9)


def test_case3b_proxy_zero_days():
    result = case3b()
    assert row_on(result, '2017-11-28')['FFF'] == 0.0 and row_on(result, END)['FFF'] == 2414.0
    [payout] = result.payouts
    assert (payout.status, payout.pay_session, payout.basis) == ('receivable', '2017-12-11', PROXY_BASIS)
    assert payout.amount == pytest.approx(603.5, abs=1e-9)
    assert row_on(result, END)['receivables'] == pytest.approx(603.5, abs=1e-9)
    assert result.invariants['proxy_payouts'] == [['FFF', '2017-11-30', '2017-12-11']]
    assert result.invariants['passed'] is True
    zero = case3b(days=0)
    [payout] = zero.payouts
    assert (payout.status, payout.pay_session, payout.basis) == ('paid', '2017-11-30', 'proxy_ex_plus_0_calendar_days')
    assert payout.amount == pytest.approx(603.5, abs=1e-9)
    assert zero.invariants['proxy_payouts'] == [['FFF', '2017-11-30', '2017-11-30']]
    assert row_on(zero, '2017-11-30')['receivables'] == 0.0 and zero.invariants['passed'] is True


def test_case4_gap_fill_ratio():
    result = case4()
    [order] = result.orders
    assert order.target_qty == 1020 and order.qty == 1020.0
    [buy] = result.trades
    assert (buy.qty, buy.price) == (1009.0, 99.0)
    assert result.decisions[0]['buy_fill'] == pytest.approx(100000 / 101080.98, abs=1e-12)
    assert cash_on(result, '2017-11-29') == pytest.approx(9.109, abs=1e-9)
    assert (order.status, order.filled_qty, order.cancel_reason) == ('partial', 1009.0, 'insufficient_cash')


def test_case5_switch():
    result = case5()
    [first] = trades_of(result, '2017-11-29')
    assert (first.ticker, first.qty) == ('HHH', 1237.0)
    assert cash_on(result, '2017-11-29') == pytest.approx(941.04, abs=1e-9)
    assert row_on(result, '2017-11-29')['nav'] == pytest.approx(99901.04, abs=1e-9)
    sell, buy = trades_of(result, '2017-11-30')
    assert (sell.ticker, sell.side, sell.qty) == ('HHH', 'sell', 1237.0)
    assert sell.notional * 0.999 == pytest.approx(98861.04, abs=1e-9)
    assert (buy.ticker, buy.side, buy.qty) == ('III', 'buy', 2472.0)
    assert buy.notional * 1.001 == pytest.approx(98978.88, abs=1e-9)
    assert cash_on(result, '2017-11-30') == pytest.approx(823.20, abs=1e-9)
    switch = next(d for d in result.decisions if d['decision_session'] == '2017-11-29')
    assert switch['costs_usd'] == pytest.approx(197.84, abs=1e-9)
    assert switch['turnover'] == pytest.approx(197840 / 99901.04, abs=1e-12)
    assert switch['buy_fill'] == 1.0 and switch['execution_session'] == '2017-11-30'


def test_case6_lag2():
    result = case6()
    assert trades_of(result, '2017-11-29') == []
    [order] = result.orders
    assert (order.execution_session, order.target_qty) == ('2017-11-30', 1020)
    [buy] = trades_of(result, '2017-11-30')
    assert (buy.qty, buy.price) == (1019.0, 98.0)
    assert cash_on(result, '2017-11-30') == pytest.approx(38.138, abs=1e-9)
    assert cash_on(result, '2017-11-29') == 100000.0


def test_case6b_order_without_valid_open_is_cancelled():
    result = case6b()
    [order] = result.orders
    assert (order.status, order.cancel_reason, order.filled_qty) == ('cancelled', 'no_valid_open', 0.0)
    assert result.trades == [] and result.decisions[0]['buy_fill'] == 1.0
    assert cash_on(result, END) == 100000.0


@pytest.mark.parametrize('case', [case1, case2, case2b, case3, case3b, case4, case5, case6, case6b])
def test_invariants_pass_on_cases(case):
    invariants = case().invariants
    assert invariants['passed'] is True
    assert [k for k in invariants if k in CHECKS] == CHECKS
    assert all(invariants[k]['passed'] is True and invariants[k]['detail'] for k in CHECKS)


def test_invariant_failure_is_reported(monkeypatch):
    real = engine.nav
    monkeypatch.setattr(engine, 'nav', lambda account, closes: real(account, closes) + 1.0)
    invariants = case1().invariants
    assert invariants['passed'] is False and invariants['nav_identity']['passed'] is False
    assert invariants['cash_flow']['passed'] is True


def test_cost_and_cash_flow_violations_are_reported(monkeypatch):
    real = engine.execute_orders

    def inflated(*args):
        trades, fill = real(*args)
        for t in trades:
            t.cost *= 2
        return trades, fill

    monkeypatch.setattr(engine, 'execute_orders', inflated)
    invariants = case1().invariants
    assert invariants['passed'] is False
    assert invariants['costs']['passed'] is False and invariants['cash_flow']['passed'] is False
    assert invariants['nav_identity']['passed'] is True


def test_execution_timing_violation_is_reported(monkeypatch):
    real = engine.execute_orders

    def off_open(account, session, opens, cost):
        trades, fill = real(account, session, opens, cost)
        for t in trades:
            t.price += 0.01
            t.notional = t.qty * t.price
            t.cost = cost * t.notional
        return trades, fill

    monkeypatch.setattr(engine, 'execute_orders', off_open)
    invariants = case1().invariants
    assert invariants['passed'] is False
    assert invariants['execution_timing']['passed'] is False and invariants['costs']['passed'] is True
    assert invariants['nav_identity']['passed'] is True


def test_receivable_conservation_violation_is_reported(monkeypatch):
    def unmarked(account, session):
        due = [r for r in account.receivables if r.pay_session == session]
        for r in due:
            account.cash += r.amount  # cash arrives but the payout is never marked paid
        account.receivables[:] = [r for r in account.receivables if r.pay_session != session]
        return due

    monkeypatch.setattr(engine, 'credit_payouts', unmarked)
    invariants = case3().invariants
    assert invariants['passed'] is False
    assert invariants['receivable_conservation']['passed'] is False
    assert invariants['nav_identity']['passed'] is True and invariants['execution_timing']['passed'] is True


def test_split_that_moves_money_is_reported(monkeypatch):
    real = engine.apply_splits

    def leaking(account, ratios):
        split = real(account, ratios)
        account.cash += 1.0 if split else 0.0
        return split

    monkeypatch.setattr(engine, 'apply_splits', leaking)
    invariants = case2().invariants
    assert invariants['passed'] is False and invariants['split_quantity_only']['passed'] is False
    assert invariants['execution_timing']['passed'] is True


def test_daily_rows_cover_the_window():
    result = case5()
    assert [d['session'] for d in result.daily] == SESSIONS[1:]
    assert set(result.daily[0]) == {'session', 'cash', 'receivables', 'positions_value', 'nav', 'HHH', 'III'}
    day = row_on(result, '2017-11-30')
    assert day['positions_value'] == pytest.approx(2472 * 40.0, abs=1e-9) and day['HHH'] == 0.0


def test_month_end_sessions_default_decisions():
    market = market_from_frames({'AAA': frame(flat(10.0))})
    assert month_end_sessions(market, '2017-11-27', END, 1) == ['2017-11-30']
    assert month_end_sessions(market, '2017-11-27', END, 2) == ['2017-11-30']
    assert month_end_sessions(market, '2017-12-01', END, 1) == []
    assert month_end_sessions(market, '2017-11-27', '2017-11-30', 1) == []
    result = simulate(market, lambda t, h: {'AAA': 1.0}, RunConfig('2017-11-27', END))
    assert [d['decision_session'] for d in result.decisions] == ['2017-11-30']
    assert [t.session for t in result.trades] == ['2017-12-01']


def bad_weights(weights):
    return lambda t, history: weights


@pytest.mark.parametrize('weights', [
    {'AAA': -0.1, 'BBB': 0.5},
    {'AAA': math.nan, 'BBB': 0.5},
    {'AAA': None, 'BBB': 0.5},
    {'AAA': 'x', 'BBB': 0.5},
    {'AAA': 0.5},
    {'AAA': 0.5, 'BBB': 0.5, 'ZZZ': 0.0},
    {'AAA': 0.5, 'BBB': 0.51},
])
def test_review_focus_invalid_weights(weights):
    market = market_from_frames({'AAA': frame(flat(10.0)), 'BBB': frame(flat(10.0))})
    config = RunConfig('2017-11-28', END, ('2017-11-28',))
    with pytest.raises(ValueError):
        simulate(market, bad_weights(weights), config)


@pytest.mark.parametrize('config', [
    RunConfig('2017-11-28', '2023-01-03', ('2017-11-28',)),
    RunConfig('2017-11-28', END, ('2017-12-08',)),
    RunConfig('2017-11-28', END, ('2017-12-04', '2017-11-28')),
    RunConfig('2017-11-28', END, ('2017-11-28', '2017-11-28')),
    RunConfig('2017-11-28', END, ('2017-11-25',)),
    RunConfig('2017-11-25', END, ('2017-11-28',)),
    RunConfig('2017-11-28', '2017-12-09', ('2017-11-28',)),
    RunConfig('2017-12-04', '2017-11-28', ()),
    RunConfig('2017-11-29', END, ('2017-11-28',)),
    RunConfig('2017-11-28', END, ('2017-12-07',), Scenario(lag=2)),
    RunConfig('2017-11-28', END, ('2017-11-28', '2017-11-29'), Scenario(lag=2)),
])
def test_review_focus_invalid_run_configuration(config):
    market = market_from_frames({'AAA': frame(flat(10.0))})
    with pytest.raises(ValueError):
        simulate(market, lambda t, h: {'AAA': 1.0}, config)


@pytest.mark.parametrize('cash', [0, 0.0, -1.0, float('nan'), float('inf'), True])
def test_run_config_rejects_bad_initial_cash(cash):
    with pytest.raises(ValueError, match='initial_cash'):
        RunConfig('2017-11-28', END, initial_cash=cash)


def test_provider_numpy_weights_are_accepted(no_network):
    market = market_from_frames({'AAA': frame(flat(10.0)), 'BBB': frame(flat(10.0))})
    config = RunConfig('2017-11-28', END, ('2017-11-28',))
    weights = {'AAA': np.float32(0.5), 'BBB': np.int64(0)}
    result = simulate(market, bad_weights(weights), config)
    assert result.trades


def test_execution_after_end_session_is_rejected():
    market = market_from_frames({'AAA': frame(flat(10.0))})
    config = RunConfig('2017-11-28', '2017-12-07', ('2017-12-07',))
    with pytest.raises(ValueError, match='execution of decision .* is after end_session'):
        simulate(market, lambda t, h: {'AAA': 1.0}, config)


def test_reserved_period_guard(monkeypatch):
    market = market_from_frames({'AAA': frame(flat(10.0))})
    monkeypatch.setattr(engine, 'LAST_OPEN_SESSION', '2017-12-06')
    with pytest.raises(ValueError, match='after the last open session'):
        simulate(market, lambda t, h: {'AAA': 1.0}, RunConfig('2017-11-28', END, ('2017-11-28',)))
    config = RunConfig('2017-11-28', '2017-12-06', ('2017-11-28',))
    assert simulate(market, lambda t, h: {'AAA': 1.0}, config).invariants['passed'] is True


def test_decision_on_last_session_with_room_for_execution_is_accepted():
    market = market_from_frames({'AAA': frame(flat(10.0))})
    result = simulate(market, lambda t, h: {'AAA': 1.0}, RunConfig('2017-11-28', END, ('2017-12-07',)))
    assert [t.session for t in result.trades] == [END]


@pytest.mark.parametrize('field, value', [('cost', 0.003), ('lag', 3), ('reserve', 0.05), ('proxy_pay_days', 5)])
def test_scenario_rejects_values_outside_the_grid(field, value):
    with pytest.raises(ValueError, match=field):
        Scenario(**{field: value})


def test_scenario_accepts_the_grid():
    for cost in (0, 0.001, 0.002, 0.005):
        assert Scenario(cost=cost).cost == cost
    assert Scenario() == Scenario(cost=0.001, lag=1, reserve=0.01, proxy_pay_days=10)
    assert Scenario(lag=2, reserve=0.02, proxy_pay_days=30).proxy_pay_days == 30


def test_provider_sees_history_up_to_the_decision_only():
    market = market_from_frames({'AAA': frame(flat(10.0))})
    seen = []

    def spy(t, history):
        seen.append((t, history.sessions[-1], len(history.sessions)))
        return {'AAA': 1.0}

    simulate(market, spy, RunConfig('2017-11-28', END, ('2017-11-28', '2017-12-04')))
    assert seen == [('2017-11-28', '2017-11-28', 2), ('2017-12-04', '2017-12-04', 6)]


def test_recomputed_proxy_payment_on_missing_session_fails():
    import pandas as pd
    from alpha_lab.normalize import calendar
    ex, gone = '2017-11-28', '2017-12-28'
    days = [d.date().isoformat() for d in calendar('2017-11-27', '2018-01-12').sessions]
    assert engine.proxy_pay_session(ex, 30) == gone and gone in days
    f = frame(flat(10.0)).reindex(days)
    f[['open', 'close']] = 10.0
    f[['dividend']] = 0.0
    f[['split_ratio']] = 1.0
    f[['payable_date', 'payable_basis']] = ''
    f.loc[ex, ['dividend', 'payable_date', 'payable_basis']] = [0.5, engine.proxy_pay_session(ex, 10), PROXY_BASIS]
    f.index.name = 'session'
    market = market_from_frames({'AAA': f.drop(index=gone)})
    assert gone not in market.sessions and market.sessions[-1] > gone
    with pytest.raises(ValueError, match='payment on a session outside the common calendar'):
        engine.pay_map(market, Scenario(proxy_pay_days=30))
    assert engine.pay_map(market, Scenario(proxy_pay_days=10))[('AAA', ex)][0] == '2017-12-08'
