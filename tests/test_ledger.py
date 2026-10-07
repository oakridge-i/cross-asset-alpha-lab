"""Ledger: account state and event functions (split, accrue, credit, sells, buys, NAV)."""
import pytest
from alpha_lab import ledger as lg

DECISION, EXECUTION = '2017-11-28', '2017-11-29'


def order(ticker, qty, session=EXECUTION):
    return lg.Order(DECISION, session, ticker, 0.5, 100.0, int(max(qty, 0)), 0.0, float(qty))


def account(cash=0.0, positions=None, pending=()):
    return lg.Account(cash, dict(positions or {}), [], list(pending))


def test_new_account_is_flat_with_initial_cash():
    acc = lg.Account.new(['BBB', 'AAA'])
    assert acc.cash == 100000.0 and acc.positions == {'AAA': 0.0, 'BBB': 0.0}
    assert acc.receivables == [] and acc.pending == []


def test_split_converts_positions_and_pending():
    acc = account(cash=50.0, positions={'CCC': 100.0, 'DDD': 7.0}, pending=[order('CCC', 10)])
    assert lg.apply_splits(acc, {'CCC': 3.0, 'DDD': 1.0, 'EEE': 2.0}) == ['CCC']
    assert acc.positions == {'CCC': 300.0, 'DDD': 7.0}
    assert acc.pending[0].qty == 30.0 and acc.pending[0].target_qty == 10 and acc.pending[0].held_qty == 0.0
    assert acc.cash == 50.0
    half = account(positions={'CCC': 1087.0})
    assert lg.apply_splits(half, {'CCC': 0.5}) == ['CCC']
    assert half.positions['CCC'] == 543.5


def test_split_reports_pending_only_ticker():
    acc = account(positions={'CCC': 0.0}, pending=[order('CCC', 4)])
    assert lg.apply_splits(acc, {'CCC': 2.0}) == ['CCC']
    assert acc.pending[0].qty == 8.0 and acc.positions == {'CCC': 0.0}


def test_size_orders_exact_integer_quotient():
    acc = account()
    orders = lg.size_orders(acc, DECISION, EXECUTION, {'AAA': 1.0}, {'AAA': 100.0}, 100000.0, 0.01)
    assert len(orders) == 1 and acc.pending == orders
    o = orders[0]
    assert o.target_qty == 990 and o.held_qty == 0.0 and o.qty == 990.0
    assert (o.decision_session, o.execution_session, o.ticker, o.weight, o.close) == (
        DECISION, EXECUTION, 'AAA', 1.0, 100.0)
    assert o.status == 'pending' and o.filled_qty == 0.0 and o.cancel_reason == ''


def test_size_orders_diff_against_position_skips_zero_and_sorts():
    acc = account(positions={'AAA': 50.0, 'BBB': 543.5, 'CCC': 10.0})
    weights, closes = {'CCC': 0.1, 'BBB': 0.5, 'AAA': 0.2}, {'AAA': 100.0, 'BBB': 50.0, 'CCC': 100.0}
    orders = lg.size_orders(acc, DECISION, EXECUTION, weights, closes, 10000.0, 0.0)
    assert [(o.ticker, o.target_qty, o.held_qty, o.qty) for o in orders] == [
        ('AAA', 20, 50.0, -30.0), ('BBB', 100, 543.5, -443.5)]
    assert [o.ticker for o in acc.pending] == ['AAA', 'BBB']


def test_size_orders_rejects_new_decision_while_pending():
    acc = account(pending=[order('AAA', 1)])
    with pytest.raises(ValueError, match='pending'):
        lg.size_orders(acc, DECISION, EXECUTION, {'AAA': 1.0}, {'AAA': 100.0}, 1000.0, 0.0)


def test_sell_then_buy_with_fill_ratio():
    sell, buy = order('AAA', -10), order('BBB', 20)
    acc = account(cash=0.0, positions={'AAA': 10.0, 'BBB': 0.0}, pending=[buy, sell])
    trades, fill = lg.execute_orders(acc, EXECUTION, {'AAA': 100.0, 'BBB': 60.0}, 0.001)
    assert fill == pytest.approx(999 / 1201.2, abs=1e-12)
    assert [(t.side, t.ticker, t.qty, t.price) for t in trades] == [
        ('sell', 'AAA', 10.0, 100.0), ('buy', 'BBB', 16.0, 60.0)]
    s, b = trades
    assert (s.session, s.notional) == (EXECUTION, 1000.0)
    assert s.cost == pytest.approx(1.0, abs=1e-9) and s.cash_after == pytest.approx(999.0, abs=1e-9)
    assert b.notional == pytest.approx(960.0, abs=1e-9) and b.cost == pytest.approx(0.96, abs=1e-9)
    assert b.cash_after == pytest.approx(38.04, abs=1e-9)
    assert acc.cash == pytest.approx(38.04, abs=1e-9)
    assert acc.positions['AAA'] == 0.0 and acc.positions['BBB'] == 16.0
    assert (sell.status, sell.filled_qty, sell.cancel_reason) == ('filled', 10.0, '')
    assert (buy.status, buy.filled_qty, buy.cancel_reason) == ('partial', 16.0, 'insufficient_cash')
    assert acc.pending == []


def test_full_fill_and_no_buys_report_unit_fill():
    buy = order('AAA', 3)
    acc = account(cash=1000.0, pending=[buy])
    trades, fill = lg.execute_orders(acc, EXECUTION, {'AAA': 100.0}, 0.0)
    assert fill == 1.0 and (buy.status, buy.filled_qty, buy.cancel_reason) == ('filled', 3.0, '')
    assert acc.positions == {'AAA': 3.0} and acc.cash == pytest.approx(700.0, abs=1e-9)
    idle = account(cash=5.0, positions={'AAA': 1.0})
    assert lg.execute_orders(idle, EXECUTION, {'AAA': 100.0}, 0.001) == ([], 1.0)


def test_fractional_buy_remainder_is_not_a_cash_shortfall():
    buy = order('AAA', 456.5)
    acc = account(cash=10000.0, pending=[buy])
    trades, fill = lg.execute_orders(acc, EXECUTION, {'AAA': 10.0}, 0.0)
    assert fill == 1.0 and [(t.ticker, t.qty) for t in trades] == [('AAA', 456.0)]
    assert (buy.status, buy.filled_qty, buy.cancel_reason) == ('partial', 456.0, 'fractional_quantity')
    assert acc.positions == {'AAA': 456.0} and acc.cash == pytest.approx(5440.0, abs=1e-9)


def test_fractional_buy_with_cash_shortfall_reports_insufficient_cash():
    buy = order('AAA', 456.5)
    acc = account(cash=1000.0, pending=[buy])
    trades, fill = lg.execute_orders(acc, EXECUTION, {'AAA': 10.0}, 0.0)
    assert fill == pytest.approx(1000 / 4565, abs=1e-12) and [(t.ticker, t.qty) for t in trades] == [('AAA', 100.0)]
    assert (buy.status, buy.filled_qty, buy.cancel_reason) == ('partial', 100.0, 'insufficient_cash')


def test_no_cash_cancels_buy_without_trade():
    buy = order('AAA', 5)
    acc = account(cash=0.0, pending=[buy])
    trades, fill = lg.execute_orders(acc, EXECUTION, {'AAA': 10.0}, 0.0)
    assert trades == [] and fill == 0.0 and acc.positions == {}
    assert (buy.status, buy.filled_qty, buy.cancel_reason) == ('cancelled', 0.0, 'insufficient_cash')


def test_no_valid_open_cancels():
    orders = [order('AAA', 5), order('BBB', -2), order('CCC', 1), order('DDD', 1), order('EEE', 1)]
    acc = account(cash=1000.0, positions={'AAA': 0.0, 'BBB': 4.0}, pending=orders)
    opens = {'AAA': float('nan'), 'BBB': 0.0, 'CCC': -1.0, 'DDD': float('inf')}
    trades, fill = lg.execute_orders(acc, EXECUTION, opens, 0.001)
    assert trades == [] and fill == 1.0 and acc.cash == 1000.0 and acc.positions['BBB'] == 4.0
    assert [(o.status, o.cancel_reason, o.filled_qty) for o in orders] == [('cancelled', 'no_valid_open', 0.0)] * 5
    assert acc.pending == []


def test_invalid_open_is_excluded_from_fill_requirement():
    bad, good = order('AAA', 1000), order('BBB', 10)
    acc = account(cash=1000.0, pending=[bad, good])
    trades, fill = lg.execute_orders(acc, EXECUTION, {'AAA': float('nan'), 'BBB': 100.0}, 0.0)
    assert fill == 1.0 and [(t.ticker, t.qty) for t in trades] == [('BBB', 10.0)]
    assert (good.status, bad.cancel_reason) == ('filled', 'no_valid_open')


def test_sell_exceeding_position_is_capped():
    capped, empty = order('AAA', -8), order('BBB', -3)
    acc = account(cash=0.0, positions={'AAA': 5.0}, pending=[capped, empty])
    trades, fill = lg.execute_orders(acc, EXECUTION, {'AAA': 10.0, 'BBB': 10.0}, 0.0)
    assert [(t.ticker, t.qty) for t in trades] == [('AAA', 5.0)] and fill == 1.0
    assert (capped.status, capped.filled_qty, capped.cancel_reason) == ('partial', 5.0, 'exceeds_position')
    assert (empty.status, empty.filled_qty, empty.cancel_reason) == ('cancelled', 0.0, 'exceeds_position')
    assert acc.positions['AAA'] == 0.0 and acc.cash == 50.0


def test_only_orders_for_the_session_execute():
    now, later = order('AAA', 1), order('BBB', 1, session='2017-11-30')
    acc = account(cash=1000.0, pending=[now, later])
    trades, _ = lg.execute_orders(acc, EXECUTION, {'AAA': 10.0, 'BBB': 10.0}, 0.0)
    assert [t.ticker for t in trades] == ['AAA'] and acc.pending == [later] and later.status == 'pending'


def test_negative_cash_after_buys_raises():
    acc = account(cash=-1.0, positions={'AAA': 1.0}, pending=[order('AAA', -1)])
    with pytest.raises(ValueError, match='cash'):
        lg.execute_orders(acc, EXECUTION, {'AAA': 0.5}, 0.0)


def test_dividend_right_and_credit():
    flat = account(positions={'AAA': 0.0}, pending=[order('AAA', 5)])
    assert lg.accrue_dividends(flat, '2017-12-01', {'AAA': 1.0}, {'AAA': ('2017-12-05', 'actual')}) == []
    assert flat.receivables == []
    acc = account(cash=10.0, positions={'AAA': 2020.0, 'BBB': 5.0})
    pay = {'AAA': ('2017-12-05', 'actual'), 'BBB': ('2017-12-05', 'actual')}
    new = lg.accrue_dividends(acc, '2017-12-01', {'AAA': 1.0, 'BBB': 0.0}, pay)
    assert acc.receivables == new and len(new) == 1
    r = new[0]
    assert (r.ticker, r.ex_session, r.pay_session, r.basis, r.qty, r.amount_per_share, r.status) == (
        'AAA', '2017-12-01', '2017-12-05', 'actual', 2020.0, 1.0, 'receivable')
    assert r.amount == 2020.0 and lg.receivables_total(acc) == 2020.0
    assert lg.credit_payouts(acc, '2017-12-04') == [] and acc.cash == 10.0
    paid = lg.credit_payouts(acc, '2017-12-05')
    assert paid == [r] and r.status == 'paid' and acc.cash == 2030.0
    assert acc.receivables == [] and lg.receivables_total(acc) == 0.0


def test_nav_counts_cash_positions_and_receivables():
    acc = account(cash=100.0, positions={'AAA': 2.0, 'BBB': 0.0})
    acc.receivables.append(lg.Receivable('AAA', '2017-12-01', '2017-12-05', 'actual', 2.0, 0.25))
    assert lg.nav(acc, {'AAA': 10.0, 'BBB': float('nan')}) == pytest.approx(120.5, abs=1e-9)
