import numpy as np
import pandas as pd
import pytest
from alpha_lab.features import (CASH, MOMENTUM_SKIP, MONTH_LEVELS, RISKY, daily_returns, momentum, month_end_levels,
                                monthly_excess, sigma, total_return_index)
from alpha_lab.market import market_from_frames
from n3_fixtures import benchmark_frames

# Last XNYS sessions of 2008-08 ... 2009-02, written out by hand.
MONTH_ENDS = ('2008-08-29', '2008-09-30', '2008-10-31', '2008-11-28', '2008-12-31', '2009-01-30', '2009-02-27')


def full_index():
    return total_return_index(market_from_frames(benchmark_frames()))


def scaled(index, rows, factors):
    """Copy of index with the given rows of each ticker multiplied by its factor (a jump in one return)."""
    out = index.copy()
    for ticker, factor in factors.items():
        out.iloc[rows, out.columns.get_loc(ticker)] *= factor
    return out


def test_constants():
    assert (MOMENTUM_SKIP, MONTH_LEVELS) == (21, 7)


@pytest.mark.parametrize('lookback', [252, 126])
def test_momentum_formula(lookback):
    T = full_index()
    n = len(T)
    r = daily_returns(T)
    # The return ending at position p of T is r.iloc[p - 1]; the window holds the returns ending at
    # positions n - L ... n - 22, i.e. from T[t-L] to T[t-21].
    window = r.iloc[n - lookback - 1:n - 22]
    assert len(window) == lookback - 21
    assert window.index[0] == T.index[n - lookback] and window.index[-1] == T.index[n - 22]
    growth = (1 + window).prod()
    got = momentum(T, lookback)
    assert list(got) == list(RISKY)
    for ticker in RISKY:
        assert isinstance(got[ticker], float)
        assert got[ticker] == pytest.approx(growth[ticker] / growth[CASH] - 1, rel=1e-12, abs=1e-14)


def test_momentum_on_hand_built_index():
    n = 300
    T = pd.DataFrame(1.0, index=range(n), columns=[*RISKY, CASH])
    T.iloc[n - 253] = 2.0                      # T[t-252]
    T.iloc[n - 22] = 3.0                       # T[t-21]
    T.iloc[n - 22, T.columns.get_loc(CASH)] = 2.2
    T.iloc[n - 22, T.columns.get_loc('GLD')] = 1.0
    got = momentum(T, 252)
    assert got['SPY'] == pytest.approx((3.0 / 2.0) / (2.2 / 2.0) - 1, rel=1e-15)
    assert got['GLD'] == pytest.approx((1.0 / 2.0) / (2.2 / 2.0) - 1, rel=1e-15)


def test_momentum_window_excludes_last_21_returns():
    frames = benchmark_frames()
    base = market_from_frames(frames)
    for ticker, factor in (('SPY', 1.3), (CASH, 0.9)):
        frames[ticker].loc[frames[ticker].index[-21:], ['open', 'close']] *= factor
    changed = market_from_frames(frames)
    T, T2 = total_return_index(base), total_return_index(changed)
    np.testing.assert_allclose(T2['SPY'].to_numpy()[-21:], 1.3 * T['SPY'].to_numpy()[-21:], rtol=1e-12)
    for lookback in (252, 126):
        assert momentum(T2, lookback) == momentum(T, lookback)
    assert sigma(changed)['SPY'] != sigma(base)['SPY']
    # The return ending at position -22 is inside the window.
    for lookback in (252, 126):
        assert momentum(scaled(T, slice(-22, None), {'SPY': 1.3}), lookback)['SPY'] != momentum(T, lookback)['SPY']


@pytest.mark.parametrize('lookback', [252, 126])
def test_momentum_window_starts_at_t_minus_l(lookback):
    T = full_index()
    base = momentum(T, lookback)
    # The return ending at position -L is the first return of the window.
    jump = momentum(scaled(T, slice(-lookback, None), {'SPY': 1.25}), lookback)
    assert jump['SPY'] == pytest.approx(1.25 * (1 + base['SPY']) - 1, rel=1e-12)
    assert all(jump[t] == base[t] for t in RISKY if t != 'SPY')
    cash_jump = momentum(scaled(T, slice(-lookback, None), {CASH: 1.1}), lookback)
    for ticker in RISKY:
        assert cash_jump[ticker] == pytest.approx((1 + base[ticker]) / 1.1 - 1, rel=1e-12)
    # The return ending at position -(L+1) is outside the window.
    before = momentum(scaled(T, slice(None, -(lookback + 1)), {'SPY': 1.25, CASH: 1.1}), lookback)
    assert before == base
    # Scaling T[t-L] itself changes M.
    start = momentum(scaled(T, slice(None, -lookback), {'SPY': 1.25}), lookback)
    assert start['SPY'] == pytest.approx((1 + base['SPY']) / 1.25 - 1, rel=1e-12)


@pytest.mark.parametrize('lookback', [252, 126])
def test_momentum_needs_l_plus_one_sessions(lookback):
    T = full_index()
    assert momentum(T.iloc[-(lookback + 1):], lookback) == momentum(T, lookback)
    with pytest.raises(ValueError, match=str(lookback + 1)):
        momentum(T.iloc[-lookback:], lookback)


def test_momentum_rejects_lookback_not_above_skip():
    with pytest.raises(ValueError):
        momentum(full_index(), 21)


def history_levels(frames, t, count=MONTH_LEVELS):
    m = market_from_frames(frames).history(t)
    return month_end_levels(m, total_return_index(m), count)


def test_month_end_levels_and_excess(no_network):
    m = market_from_frames(benchmark_frames()).history('2009-02-27')
    T = total_return_index(m)
    levels = month_end_levels(m, T)
    assert tuple(levels.index) == MONTH_ENDS
    assert list(levels.columns) == list(T.columns)
    for s in MONTH_ENDS:
        for ticker in T.columns:
            assert levels.loc[s, ticker] == T.loc[s, ticker]
    E = monthly_excess(levels)
    assert E.shape == (6, 9) and list(E.columns) == list(RISKY)
    assert tuple(E.index) == MONTH_ENDS[1:]
    for j in range(1, 7):
        end, prev = MONTH_ENDS[j], MONTH_ENDS[j - 1]
        for ticker in RISKY:
            expected = (T.loc[end, ticker] / T.loc[prev, ticker]) / (T.loc[end, CASH] / T.loc[prev, CASH]) - 1
            assert E.loc[end, ticker] == pytest.approx(expected, rel=1e-12, abs=1e-15)


def test_month_end_levels_count_parameter(no_network):
    levels = history_levels(benchmark_frames(), '2009-02-27', count=3)
    assert tuple(levels.index) == MONTH_ENDS[-3:]


def test_month_end_levels_rejects_non_month_end_t(no_network):
    with pytest.raises(ValueError, match='last XNYS session'):
        history_levels(benchmark_frames(), '2009-02-26')


def test_month_end_levels_rejects_incomplete_month(no_network):
    frames = benchmark_frames()
    for f in frames.values():
        f.drop(index='2008-10-31', inplace=True)
    m = market_from_frames(frames).history('2009-02-27')
    assert '2008-10-30' in m.sessions and '2008-10-31' not in m.sessions
    with pytest.raises(ValueError, match='last XNYS session'):
        month_end_levels(m, total_return_index(m))


def test_month_end_levels_rejects_missing_month(no_network):
    frames = benchmark_frames()
    for ticker, f in frames.items():
        frames[ticker] = f[~f.index.str.startswith('2008-11')]
    m = market_from_frames(frames).history('2009-02-27')
    assert not any(s.startswith('2008-11') for s in m.sessions)
    with pytest.raises(ValueError, match='consecutive'):
        month_end_levels(m, total_return_index(m))


def test_month_end_levels_rejects_fewer_than_count_months(no_network):
    # 2007-12 ... 2008-05: six months.
    with pytest.raises(ValueError, match='7'):
        history_levels(benchmark_frames(), '2008-05-30')
    assert len(history_levels(benchmark_frames(), '2008-05-30', count=6)) == 6


def test_month_end_levels_rejects_index_of_another_history(no_network):
    m = market_from_frames(benchmark_frames())
    with pytest.raises(ValueError, match='index'):
        month_end_levels(m.history('2009-02-27'), total_return_index(m))


def test_month_end_levels_reuses_the_exchange_calendar(monkeypatch, no_network):
    from alpha_lab import features
    frames = benchmark_frames()
    history_levels(frames, '2009-02-27')                                      # warm any calendar cache
    calls = []
    original = features.calendar
    monkeypatch.setattr(features, 'calendar', lambda *args: calls.append(args) or original(*args))
    ends = ('2008-06-30', '2008-07-31', *MONTH_ENDS)                          # last XNYS sessions of 2008-06 ... 2009-02
    for t, first in (('2009-02-27', 2), ('2009-01-30', 1), ('2008-12-31', 0)):
        assert tuple(history_levels(frames, t).index) == ends[first:first + 7]
    assert calls == []
