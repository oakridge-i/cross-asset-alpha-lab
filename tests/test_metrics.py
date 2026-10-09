"""Section 11 metrics against hand-computed numbers."""
import json
import math
import numpy as np
import pandas as pd
import pytest
from n3_fixtures import benchmark_vintage
from alpha_lab.engine import PROVIDERS, Result, RunConfig, simulate
from alpha_lab.market import load_market, market_from_frames
from alpha_lab.metrics import PERIODS, WF_PERIODS, compute_metrics, excess_series, periods_for
from alpha_lab.provenance import canonical_bytes

TICKERS = ('SPY', 'TLT', 'GLD', 'BIL')


def frame_for(sessions, close):
    n = len(sessions)
    out = pd.DataFrame({'open': close, 'close': close, 'dividend': [0.0] * n, 'split_ratio': [1.0] * n,
                        'payable_date': [''] * n, 'payable_basis': [''] * n}, index=pd.Index(sessions, name='session'))
    return out.astype({'open': float, 'close': float})


def market(sessions, **closes):
    """Synthetic market; every ticker defaults to a flat close of 100."""
    return market_from_frames({t: frame_for(sessions, closes.get(t, [100.0] * len(sessions))) for t in TICKERS})


def row(session, nav, cash=0.0, receivables=0.0, **qty):
    return {'session': session, 'cash': cash, 'receivables': receivables, 'positions_value': 0.0, 'nav': nav,
            **{t: 0.0 for t in TICKERS}, **qty}


def result(daily, decisions=(), weights=()):
    return Result(list(decisions), [], [], [], daily, {}, list(weights))


def decision(decision_session, execution_session, nav, turnover, costs):
    return {'decision_session': decision_session, 'execution_session': execution_session, 'nav': nav,
            'buy_fill': 0.0, 'turnover': turnover, 'costs_usd': costs}


S = ['2008-12-31', '2009-01-02', '2009-01-05', '2009-01-06']
BIL = [100.0, 100.0, 100.01, 100.03]
Y = ['2009-12-28', '2009-12-29', '2009-12-30', '2009-12-31', '2010-01-04', '2010-01-05']
Y_NAV = [100000.0, 100000.0, 100000.0, 90000.0, 99000.0]  # rows 12-29 .. 01-05


def january():
    daily = [row('2009-01-02', 100000.0), row('2009-01-05', 99900.0), row('2009-01-06', 100899.0)]
    return market(S, BIL=BIL), result(daily)


def year_boundary(decisions=(), weights=()):
    daily = [row(s, n) for s, n in zip(Y[1:], Y_NAV)]
    return market(Y), result(daily, decisions, weights)


def test_returns_include_first_entry_and_base_nav():
    m, r = january()
    full = compute_metrics(m, r)['periods']['full']
    assert full['n_returns'] == 2
    assert full['total_return'] == pytest.approx(0.00899, abs=1e-12)  # 100899 / 100000 - 1


def test_cagr_vol_sharpe_utility_match_formulas():
    m, r = january()
    full = compute_metrics(m, r)['periods']['full']
    rets = np.array([-0.001, 0.01])  # 99900 / 100000 - 1, 100899 / 99900 - 1
    bil = np.array([100.01 / 100.0 - 1, 100.03 / 100.01 - 1])
    e = rets - bil
    assert full['cagr'] == pytest.approx(1.00899 ** (252 / 2) - 1, rel=1e-12)
    assert full['volatility'] == pytest.approx(math.sqrt(252) * rets.std(ddof=1), rel=1e-12)
    assert full['mean_excess'] == pytest.approx(252 * e.mean(), rel=1e-12)
    assert full['sharpe_bil'] == pytest.approx(math.sqrt(252) * e.mean() / e.std(ddof=1), rel=1e-12)
    assert full['utility'] == pytest.approx(252 * e.mean() - 1.5 * 252 * e.var(ddof=1), rel=1e-12)
    # by hand: std(r) = |0.01 - (-0.001)| / sqrt(2) = 0.0077781745930520
    assert full['volatility'] == pytest.approx(math.sqrt(252) * 0.0077781745930520, rel=1e-9)


def test_zero_excess_variance_gives_null_sharpe():
    r = result([row('2009-01-02', 100.0), row('2009-01-05', 200.0), row('2009-01-06', 400.0)])
    full = compute_metrics(market(S), r)['periods']['full']  # flat BIL, so e = 1 on both days
    assert full['sharpe_bil'] is None
    assert full['mean_excess'] == 252.0 and full['utility'] == 252.0
    assert full['volatility'] == 0.0


def test_single_return_has_null_dispersion_metrics():
    m, r = january()
    full = compute_metrics(m, result(r.daily[:2]))['periods']['full']
    assert full['n_returns'] == 1
    assert full['volatility'] is None and full['sharpe_bil'] is None and full['utility'] is None
    assert full['total_return'] == pytest.approx(-0.001, abs=1e-15)


def test_drawdown_includes_base_nav():
    m, r = year_boundary()
    periods = compute_metrics(m, r)['periods']
    assert periods['2010']['max_drawdown'] == pytest.approx(-0.10, abs=1e-15)  # 90000 is the first 2010 NAV
    assert periods['2009']['max_drawdown'] == 0.0
    assert periods['full']['max_drawdown'] == pytest.approx(-0.10, abs=1e-15)


def test_period_base_is_previous_close():
    m, r = year_boundary()
    periods = compute_metrics(m, r)['periods']
    assert periods['2009']['n_returns'] == 2  # the first row 2009-12-29 has no return
    assert periods['2009']['total_return'] == 0.0
    assert periods['2010']['n_returns'] == 2
    assert periods['2010']['total_return'] == pytest.approx(-0.01, abs=1e-15)  # 99000 / 100000 - 1
    assert periods['full']['total_return'] == pytest.approx(-0.01, abs=1e-15)


def test_decisions_turnover_costs_by_execution_session():
    d1 = decision('2009-12-30', '2009-12-31', 100000.0, 0.4, 50.0)
    d2 = decision('2009-12-31', '2010-01-04', 90000.0, 0.2, 30.0)  # decided in 2009, executed in 2010
    d3 = decision('2010-01-04', '2010-01-05', 90000.0, 0.3, 90.0)
    weights = [{'decision_session': d['decision_session'], 'SPY': a, 'TLT': b, 'GLD': 0.0}
               for d, a, b in ((d1, 0.1, 0.1), (d2, 0.3, 0.2), (d3, 0.4, 0.2))]
    m, r = year_boundary([d1, d2, d3], weights)
    periods = compute_metrics(m, r)['periods']
    y09, y10 = periods['2009'], periods['2010']
    assert (y09['decisions'], y09['turnover'], y09['costs_usd']) == (1, 0.4, 50.0)
    assert y09['turnover_annual'] == pytest.approx(0.4 * 252 / 2, rel=1e-12)
    assert y09['mean_target_risky'] == pytest.approx(0.2, abs=1e-15)
    assert (y10['decisions'], y10['costs_usd']) == (2, 120.0)
    assert y10['turnover'] == pytest.approx(0.5, abs=1e-15) and y10['turnover_annual'] == pytest.approx(63.0)
    assert y10['mean_target_risky'] == pytest.approx(0.55, abs=1e-15)  # (.5 + .6) / 2


def test_cost_ratio_is_sum_of_relative_costs():
    d2 = decision('2009-12-31', '2010-01-04', 100000.0, 0.2, 30.0)
    d3 = decision('2010-01-04', '2010-01-05', 90000.0, 0.3, 90.0)
    weights = [{'decision_session': d['decision_session'], 'SPY': 0.0} for d in (d2, d3)]
    m, r = year_boundary([d2, d3], weights)
    y10 = compute_metrics(m, r)['periods']['2010']
    assert y10['cost_ratio'] == pytest.approx(0.0003 + 0.001, rel=1e-12)  # 30 / 100000 + 90 / 90000
    assert y10['cost_ratio'] != pytest.approx(120 / 95000, rel=1e-3)


def test_no_decisions_in_period():
    m, r = year_boundary()
    y10 = compute_metrics(m, r)['periods']['2010']
    assert (y10['decisions'], y10['turnover'], y10['turnover_annual'], y10['costs_usd'], y10['cost_ratio']) == \
        (0, 0.0, 0.0, 0.0, 0.0)
    assert y10['mean_target_risky'] is None


def test_shares_and_maxima():
    daily = [row('2009-01-02', 100000.0),
             row('2009-01-05', 100000.0, cash=20000.0, receivables=1000.0, SPY=100.0, TLT=100.0, BIL=200.0),
             row('2009-01-06', 100000.0, cash=10000.0, receivables=3000.0, SPY=150.0, TLT=100.0, BIL=100.0)]
    full = compute_metrics(market(S, SPY=[400.0] * 4, TLT=[200.0] * 4), result(daily))['periods']['full']
    assert full['mean_cash_usd'] == pytest.approx(0.15) and full['mean_bil'] == pytest.approx(0.15)
    assert full['mean_cash_plus_bil'] == pytest.approx(0.30) and full['mean_receivables'] == pytest.approx(0.02)
    assert full['mean_risky'] == pytest.approx(0.7)  # (.6 + .8) / 2
    assert full['mean_group'] == pytest.approx({'Equity': 0.5, 'Treasury': 0.2, 'Credit': 0.0, 'Real': 0.0})
    assert full['max_group']['Equity'] == pytest.approx(0.6)
    assert full['mean_weight']['SPY'] == pytest.approx(0.5) and full['max_weight']['SPY'] == pytest.approx(0.6)
    assert full['max_weight']['TLT'] == pytest.approx(0.2) and full['mean_weight']['GLD'] == 0.0


def test_periods_without_returns_are_omitted():
    m, r = january()
    out = compute_metrics(m, r)
    assert set(out['periods']) == {'full', 'development', '2009'}
    assert out['schema_version'] == 1
    json.loads(canonical_bytes(out))  # no NaN or infinity anywhere


def test_period_order_follows_periods():
    m, r = year_boundary()
    expected = [n for n, _, _ in PERIODS if n in ('full', 'development', '2009', '2010')]
    assert list(compute_metrics(m, r)['periods']) == expected


def test_session_after_last_open_is_rejected():
    m = market(['2022-12-29', '2022-12-30', '2023-01-03'])
    r = result([row('2022-12-29', 100.0), row('2022-12-30', 101.0), row('2023-01-03', 102.0)])
    with pytest.raises(ValueError):
        compute_metrics(m, r)


def test_excess_series_feeds_the_same_utility(tmp_path, no_network):
    derived, digest = benchmark_vintage(tmp_path)
    market = load_market(tmp_path, derived, digest)
    run = simulate(market, PROVIDERS['B2'].function, RunConfig('2008-12-31', '2009-03-31'))
    excess = excess_series(market, run)
    assert [s for s in excess] == [d['session'] for d in run.daily[1:]]
    values = np.array(list(excess.values()))
    expected = 252 * values.mean() - 1.5 * 252 * values.var(ddof=1)
    full = compute_metrics(market, run)['periods']['full']
    assert full['n_returns'] == len(values) > 1
    assert full['utility'] == pytest.approx(expected, abs=1e-12)
    assert full['mean_excess'] == pytest.approx(252 * values.mean(), abs=1e-12)


def test_excess_series_of_a_run_without_rows_is_empty():
    assert excess_series(market(S), result([])) == {}


def test_walk_forward_periods_for_late_start():
    late = periods_for(RunConfig('2013-12-31', '2022-12-30'))
    assert late is WF_PERIODS and 'full' not in [p[0] for p in late]
    assert [p[0] for p in late] == ['walk_forward', '2014-2016', '2017-2019', '2020-2022',
                                    *(str(y) for y in range(2014, 2023))]
    assert late[0] == ('walk_forward', '2014-01-01', '2022-12-31')
    assert periods_for(RunConfig('2008-12-31', '2022-12-30')) is PERIODS
