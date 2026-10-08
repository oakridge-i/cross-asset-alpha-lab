"""H1 and H2 providers on synthetic markets (spec 4.1, 4.3-4.5, protocol lines 66-71 and 93-107).

Expectations are built here from the feature primitives, an explicit sort and the formulas of the protocol,
never by calling h1 or h2 to produce the expected value."""
import math

import numpy as np
import pytest
from n3_fixtures import benchmark_frames

from alpha_lab.features import CASH, RISKY, covariance, momentum, month_end_levels, monthly_excess, sigma, total_return_index
from alpha_lab.hypotheses import SIGNAL_COLUMNS_H1, SIGNAL_COLUMNS_H2, Decision, h1, h2
from alpha_lab.market import market_from_frames
from alpha_lab.portfolio import risk_detail

T = '2008-12-31'
ASCII = sorted(RISKY)
# Last XNYS sessions of 2008-06 ... 2008-12, written out by hand.
ENDS = ('2008-06-30', '2008-07-31', '2008-08-29', '2008-09-30', '2008-10-31', '2008-11-28', '2008-12-31')
# First XNYS session of 2008-07 ... 2008-12.
MONTH_STARTS = ('2008-07-01', '2008-08-01', '2008-09-02', '2008-10-01', '2008-11-03', '2008-12-01')
RAMP = 10
UP, DOWN, BIG_UP, BIG_DOWN = 1.2, 0.8, 1.5, 1 / 1.5
FLOAT_COLUMNS = ('momentum', 'sigma', 'score', 'q', 'v', 'scale', 'weight', 'parent_weight',
                 'excess_1', 'excess_2', 'excess_3', 'excess_4', 'excess_5', 'excess_6')


def negative(**drift):
    """Daily log drift: -0.003 for every risky ETF except the given overrides."""
    return {**{t: -0.003 for t in RISKY}, **drift}


def monthly_moves(frames, ticker, factors):
    """Scale `ticker` by factors[j] over the first RAMP sessions of the j-th month of 2008-07 ... 2008-12. A factor
    of 1.2 or 0.8 is far larger than a month of noise, so the excess return over BIL of that month is positive or
    negative as designed; a factor of 1 leaves the month unchanged."""
    f = frames[ticker]
    sessions = list(f.index)
    log_level = np.zeros(len(sessions))
    for start, factor in zip(MONTH_STARTS, factors):
        first = sessions.index(start)
        for p in range(first, len(sessions)):
            log_level[p] += math.log(factor) * min(1.0, (p - first + 1) / RAMP)
    f[['open', 'close']] = f[['open', 'close']].mul(np.exp(log_level), axis=0)


def follow_bil_through(frames, ticker, cutoff):
    """Up to `cutoff` the ticker is a copy of BIL (zero excess return, exactly); afterwards it keeps its own returns."""
    own, bil = frames[ticker], frames['BIL']
    head = own.index <= cutoff
    scale = bil.loc[cutoff, 'close'] / own.loc[cutoff, 'close']
    out = own.copy()
    out.loc[~head, ['open', 'close']] = own.loc[~head, ['open', 'close']] * scale
    out.loc[head] = bil.loc[head]
    frames[ticker] = out


def history(t=T, **kwargs):
    return market_from_frames(benchmark_frames(**kwargs)).history(t)


def expected_h1(h, lookback, k):
    """Protocol lines 66-71 and 93-99 from the primitives, an explicit sort and the q formula."""
    index = total_return_index(h)
    vol = sigma(h)
    mom = momentum(index, lookback)
    score = {i: mom[i] / vol[i] for i in RISKY}
    order = sorted((i for i in RISKY if score[i] > 0), key=lambda i: (-score[i], i))
    chosen = order[:k]
    inverse = {i: 1.0 / vol[i] for i in chosen}
    q = {i: len(chosen) / k * inverse[i] / math.fsum(inverse.values()) if i in chosen else 0.0 for i in RISKY}
    v, scale, w = risk_detail(q, covariance(h))
    return {'momentum': mom, 'sigma': vol, 'score': score, 'order': order, 'chosen': chosen, 'q': q, 'v': v,
            'scale': scale, 'weights': w}


def expected_rows(e, t):
    rows = []
    for i in ASCII:
        rows.append({'decision_session': t, 'ticker': i, 'momentum': e['momentum'][i], 'sigma': e['sigma'][i],
                     'score': e['score'][i], 'eligible': i in e['order'],
                     'rank': e['order'].index(i) + 1 if i in e['order'] else None, 'selected': i in e['chosen'],
                     'q': e['q'][i], 'v': e['v'][i], 'scale': e['scale'], 'weight': e['weights'][i]})
    return rows


def assert_rows(got, want, columns=SIGNAL_COLUMNS_H1):
    assert len(got) == len(want) == 9
    for g, w in zip(got, want):
        assert list(g) == list(columns)
        for column in columns:
            if column in FLOAT_COLUMNS:
                assert type(g[column]) is float
                assert g[column] == pytest.approx(w[column], rel=1e-12, abs=1e-15), (w['ticker'], column)
            else:
                assert g[column] == w[column], (w['ticker'], column)
                assert type(g[column]) is type(w[column])


def assert_weights(weights):
    assert set(weights) == {*RISKY, CASH}
    assert all(type(x) is float and math.isfinite(x) and x >= 0.0 for x in weights.values())
    assert math.fsum(weights.values()) == pytest.approx(1.0, abs=1e-12)


def hand_excess(h, ticker):
    """E_i,j for the six months 2008-07 ... 2008-12 from the hand-written month ends."""
    index = total_return_index(h)
    return [float((index.loc[b, ticker] / index.loc[a, ticker]) / (index.loc[b, CASH] / index.loc[a, CASH]) - 1)
            for a, b in zip(ENDS, ENDS[1:])]


def h2_scenario():
    """Parent H1_252_3 selects TLT, SPY and GLD (ranks 1-3); IEF is eligible at rank 4. Positive months of excess
    return: TLT 5, GLD 4, SPY 3, IEF 6. GLD moves more, so its volatility is higher and its weight lower."""
    frames = benchmark_frames(drift=negative(TLT=0.002, GLD=0.002, SPY=0.002))
    monthly_moves(frames, 'TLT', (UP, UP, UP, DOWN, UP, UP))
    monthly_moves(frames, 'GLD', (BIG_UP, BIG_DOWN, BIG_UP, BIG_UP, BIG_DOWN, BIG_UP))
    monthly_moves(frames, 'SPY', (DOWN, UP, UP, DOWN, UP, DOWN))
    monthly_moves(frames, 'IEF', (UP,) * 6)
    return market_from_frames(frames).history(T)


def test_signal_column_constants():
    assert SIGNAL_COLUMNS_H1 == ['decision_session', 'ticker', 'momentum', 'sigma', 'score', 'eligible', 'rank',
                                 'selected', 'q', 'v', 'scale', 'weight']
    assert SIGNAL_COLUMNS_H2 == SIGNAL_COLUMNS_H1 + ['parent_weight', 'excess_1', 'excess_2', 'excess_3', 'excess_4',
                                                     'excess_5', 'excess_6', 'positive_months', 'filter_pass']


def test_h1_hand_computed_decision():
    h = history(drift=negative(SPY=0.004, TLT=0.003, GLD=0.002, EFA=0.001, IEF=0.0))
    e = expected_h1(h, 252, 3)
    assert e['order'] == ['SPY', 'TLT', 'GLD', 'EFA']                 # four eligible, three slots
    assert e['chosen'] == ['SPY', 'TLT', 'GLD']
    d = h1(T, h, lookback=252, k=3)
    assert isinstance(d, Decision)
    assert_weights(d.weights)
    assert_rows(d.signals, expected_rows(e, T))
    # By hand: the three shares of 1/sigma are about 1/3 > 25%, so every ETF cap binds and v = 0.25 on three ETFs
    # of three different groups; a = min(1, 0.10 / sqrt(v' Sigma v)); BIL takes the rest.
    v = np.array([0.25 if i in e['chosen'] else 0.0 for i in RISKY])
    scale = min(1.0, 0.10 / math.sqrt(v @ covariance(h) @ v))
    for row in d.signals:
        assert row['v'] == (0.25 if row['selected'] else 0.0)
        assert row['scale'] == pytest.approx(scale, rel=1e-12)
        assert row['weight'] == pytest.approx(scale * row['v'], rel=1e-12, abs=1e-15)
    assert d.weights[CASH] == pytest.approx(1 - 0.75 * scale, rel=1e-12)
    # EFA is eligible, ranked fourth and unselected; the ineligible ETFs have no rank.
    efa = next(r for r in d.signals if r['ticker'] == 'EFA')
    assert (efa['eligible'], efa['rank'], efa['selected'], efa['q'], efa['weight']) == (True, 4, False, 0.0, 0.0)
    assert {r['ticker'] for r in d.signals if r['rank'] is None} == set(RISKY) - set(e['order'])


@pytest.mark.parametrize('lookback,k', [(252, 3), (252, 4), (126, 3), (126, 4)])
def test_h1_registered_configurations_match_the_primitives(lookback, k):
    h = history(drift=negative(SPY=0.004, TLT=0.003, GLD=0.002, EFA=0.001, IEF=0.0))
    e = expected_h1(h, lookback, k)
    assert 0 < len(e['chosen']) <= k
    d = h1(T, h, lookback=lookback, k=k)
    assert_weights(d.weights)
    assert_rows(d.signals, expected_rows(e, T))
    assert {i: d.weights[i] for i in RISKY} == pytest.approx({i: e['weights'][i] for i in RISKY}, rel=1e-12, abs=1e-15)
    assert d.weights[CASH] == pytest.approx(e['weights'][CASH], rel=1e-12, abs=1e-15)


def test_h1_exact_tie_breaks_by_ticker():
    # EEM is an exact copy of SPY: identical sigma, momentum and score. In RISKY order SPY comes first, in ASCII
    # order EEM does; the tie sits on the last slot (ranks 3 and 4 of K = 3).
    frames = benchmark_frames(drift=negative(IEF=0.006, TLT=0.005, SPY=0.002))
    frames['EEM'] = frames['SPY'].copy()
    h = market_from_frames(frames).history(T)
    e = expected_h1(h, 252, 3)
    assert e['score']['EEM'] == e['score']['SPY'] > 0
    assert e['order'] == ['IEF', 'TLT', 'EEM', 'SPY']
    d = h1(T, h, lookback=252, k=3)
    by_ticker = {r['ticker']: r for r in d.signals}
    assert by_ticker['EEM']['score'] == by_ticker['SPY']['score']
    assert (by_ticker['EEM']['rank'], by_ticker['EEM']['selected']) == (3, True)
    assert (by_ticker['SPY']['rank'], by_ticker['SPY']['selected']) == (4, False)
    assert d.weights['EEM'] > 0.0 and d.weights['SPY'] == 0.0
    assert_rows(d.signals, expected_rows(e, T))


def test_h1_near_tie_orders_by_score():
    # SPY exceeds its copy EEM by a relative 1e-12 in score: about a thousand times the rounding noise of the
    # feature arithmetic and below any rounded or tolerance-based tie. SPY must rank above EEM although "EEM" sorts
    # first by ticker.
    frames = benchmark_frames(drift=negative(IEF=0.006, TLT=0.005, SPY=0.002))
    frames['EEM'] = frames['SPY'].copy()
    frames['SPY'].loc['2008-08-15':, ['open', 'close']] *= 1 + 1e-12
    h = market_from_frames(frames).history(T)
    e = expected_h1(h, 252, 3)
    gap = e['score']['SPY'] / e['score']['EEM'] - 1
    assert 1e-13 < gap < 1e-11
    assert e['order'] == ['IEF', 'TLT', 'SPY', 'EEM']
    d = h1(T, h, lookback=252, k=3)
    by_ticker = {r['ticker']: r for r in d.signals}
    assert (by_ticker['SPY']['rank'], by_ticker['SPY']['selected']) == (3, True)
    assert (by_ticker['EEM']['rank'], by_ticker['EEM']['selected']) == (4, False)
    assert d.weights['SPY'] > 0.0 and d.weights['EEM'] == 0.0
    assert_rows(d.signals, expected_rows(e, T))


def test_h1_zero_score_not_eligible():
    # GLD is an exact copy of BIL: its momentum and score are exactly 0, which is not eligible (S > 0, strictly).
    # With K = 4 and three eligible ETFs the fourth slot stays in BIL instead of taking the zero score.
    frames = benchmark_frames(drift=negative(SPY=0.004, TLT=0.003, IEF=0.002))
    frames['GLD'] = frames['BIL'].copy()
    h = market_from_frames(frames).history(T)
    e = expected_h1(h, 252, 4)
    assert e['momentum']['GLD'] == 0.0 and e['score']['GLD'] == 0.0
    assert e['order'] == ['SPY', 'TLT', 'IEF']
    d = h1(T, h, lookback=252, k=4)
    gld = next(r for r in d.signals if r['ticker'] == 'GLD')
    assert (gld['score'], gld['eligible'], gld['rank'], gld['selected'], gld['q'], gld['weight']) == (
        0.0, False, None, False, 0.0, 0.0)
    assert math.fsum(r['q'] for r in d.signals) == pytest.approx(3 / 4, rel=1e-12)   # m / K
    assert_rows(d.signals, expected_rows(e, T))
    assert d.weights['GLD'] == 0.0


def test_h1_fewer_than_k_leaves_bil():
    h = history(drift=negative(IEF=0.004, GLD=0.003))
    e = expected_h1(h, 252, 3)
    assert e['order'] == ['IEF', 'GLD'] or e['order'] == ['GLD', 'IEF']
    d = h1(T, h, lookback=252, k=3)
    q = {r['ticker']: r['q'] for r in d.signals}
    inverse = {i: 1.0 / sigma(h)[i] for i in ('IEF', 'GLD')}
    for i in ('IEF', 'GLD'):                                            # q carries m / K = 2/3 of the budget
        assert q[i] == pytest.approx(2 / 3 * inverse[i] / sum(inverse.values()), rel=1e-12)
    assert math.fsum(q.values()) == pytest.approx(2 / 3, rel=1e-12)
    v = np.array([0.25 if i in ('IEF', 'GLD') else 0.0 for i in RISKY])      # both q exceed 25%
    scale = min(1.0, 0.10 / math.sqrt(v @ covariance(h) @ v))
    assert d.weights['IEF'] == pytest.approx(0.25 * scale, rel=1e-12)
    assert d.weights['GLD'] == pytest.approx(0.25 * scale, rel=1e-12)
    assert d.weights[CASH] == pytest.approx(1 - 0.5 * scale, rel=1e-12)
    assert_rows(d.signals, expected_rows(e, T))


def test_h1_empty_selection_is_all_bil():
    h = history(drift=negative())
    assert expected_h1(h, 252, 3)['order'] == []
    d = h1(T, h, lookback=252, k=3)
    assert d.weights == {**{i: 0.0 for i in RISKY}, CASH: 1.0}
    assert_weights(d.weights)
    assert len(d.signals) == 9
    for row in d.signals:
        assert (row['eligible'], row['rank'], row['selected'], row['q'], row['v'], row['scale'], row['weight']) == (
            False, None, False, 0.0, 0.0, 1.0, 0.0)
        assert row['score'] < 0.0


def test_h2_hand_computed_decision_h4():
    check_h2_decision(4, kept={'TLT', 'GLD'}, removed={'SPY'})


def test_h2_hand_computed_decision_h5():
    check_h2_decision(5, kept={'TLT'}, removed={'GLD', 'SPY'})


def check_h2_decision(h_param, kept, removed):
    h = h2_scenario()
    parent_expected = expected_h1(h, 252, 3)
    assert parent_expected['order'] == ['TLT', 'SPY', 'GLD', 'IEF']
    assert parent_expected['chosen'] == ['TLT', 'SPY', 'GLD']
    # Months with E > 0 from the hand-written month ends: the design of the scenario.
    positives = {i: sum(e > 0 for e in hand_excess(h, i)) for i in ('TLT', 'GLD', 'SPY', 'IEF')}
    assert positives == {'TLT': 5, 'GLD': 4, 'SPY': 3, 'IEF': 6}
    parent = h1(T, h, lookback=252, k=3)
    assert parent.weights['TLT'] > parent.weights['GLD'] > 0.0 and parent.weights['SPY'] > 0.0
    d = h2(T, h, h=h_param)
    assert isinstance(d, Decision)
    assert_weights(d.weights)
    # Kept weights are the parent's values, removed ones exactly 0.0; no replacement (IEF passes the filter at
    # rank 4 but stays at 0.0), no redistribution and no rescaling; BIL takes the released weight.
    for i in RISKY:
        if i in kept:
            assert d.weights[i] == parent.weights[i]
        else:
            assert d.weights[i] == 0.0 and type(d.weights[i]) is float
    assert d.weights[CASH] == 1.0 - math.fsum(parent.weights[i] for i in kept)
    assert d.weights[CASH] > parent.weights[CASH]
    assert len(d.signals) == 9
    for row in d.signals:
        i = row['ticker']
        assert list(row) == SIGNAL_COLUMNS_H2
        excess = hand_excess(h, i)
        for j in range(6):
            assert type(row[f'excess_{j + 1}']) is float
            assert row[f'excess_{j + 1}'] == pytest.approx(excess[j], rel=1e-12, abs=1e-15)
        count = sum(e > 0 for e in excess)
        assert row['positive_months'] == count and type(row['positive_months']) is int
        assert row['filter_pass'] is (count >= h_param)
        assert row['parent_weight'] == parent.weights[i]
        assert row['weight'] == d.weights[i]
    by_ticker = {r['ticker']: r for r in d.signals}
    assert by_ticker['IEF']['filter_pass'] is True and by_ticker['IEF']['weight'] == 0.0
    assert all(by_ticker[i]['filter_pass'] is False for i in removed)


def test_h2_zero_excess_month_not_positive():
    # EEM and EFA follow BIL exactly through 2008-07-31, so E_1 = 0 exactly; afterwards EEM has 3 and EFA 4
    # positive months. E = 0 is not positive: EEM counts 3, EFA 4 (counting zero would give 4 and 5).
    frames = benchmark_frames(drift=negative(EEM=0.003, EFA=0.003))
    monthly_moves(frames, 'EEM', (1.0, UP, DOWN, UP, DOWN, UP))
    monthly_moves(frames, 'EFA', (1.0, UP, UP, DOWN, UP, UP))
    for ticker in ('EEM', 'EFA'):
        follow_bil_through(frames, ticker, '2008-07-31')
    h = market_from_frames(frames).history(T)
    assert hand_excess(h, 'EEM')[0] == 0.0 and hand_excess(h, 'EFA')[0] == 0.0
    assert expected_h1(h, 252, 3)['chosen'] == ['EFA', 'EEM']
    d4, d5 = h2(T, h, h=4), h2(T, h, h=5)
    for d in (d4, d5):
        by_ticker = {r['ticker']: r for r in d.signals}
        assert by_ticker['EEM']['excess_1'] == 0.0 and by_ticker['EFA']['excess_1'] == 0.0
        assert (by_ticker['EEM']['positive_months'], by_ticker['EFA']['positive_months']) == (3, 4)
    parent = h1(T, h, lookback=252, k=3)
    assert parent.weights['EEM'] > 0.0 and parent.weights['EFA'] > 0.0
    assert (d4.weights['EEM'], d4.weights['EFA']) == (0.0, parent.weights['EFA'])
    assert (d5.weights['EEM'], d5.weights['EFA']) == (0.0, 0.0)
    assert d5.weights[CASH] == 1.0
    assert [r['filter_pass'] for r in d4.signals if r['ticker'] in ('EEM', 'EFA')] == [False, True]
    assert [r['filter_pass'] for r in d5.signals if r['ticker'] in ('EEM', 'EFA')] == [False, False]


def test_h2_subset_and_bil_not_lower():
    kept_total = removed_total = 0
    for seed in (1, 2, 3):
        rng = np.random.default_rng(seed)
        drift = {i: float(rng.choice([-0.002, 0.0005, 0.0015])) for i in RISKY}
        market = market_from_frames(benchmark_frames(seed=seed, drift=drift))
        for t in ('2008-12-31', '2009-01-30', '2009-02-27'):
            h = market.history(t)
            parent = h1(t, h, lookback=252, k=3)
            E = monthly_excess(month_end_levels(h, total_return_index(h)))
            positives = {i: int((E[i] > 0).sum()) for i in RISKY}
            for h_param in (4, 5):
                d = h2(t, h, h=h_param)
                assert_weights(d.weights)
                for i in RISKY:
                    assert d.weights[i] in (parent.weights[i], 0.0)
                    assert d.weights[i] <= parent.weights[i]
                    if parent.weights[i] > 0.0:
                        assert (d.weights[i] > 0.0) == (positives[i] >= h_param)
                        kept_total += d.weights[i] > 0.0
                        removed_total += d.weights[i] == 0.0
                assert d.weights[CASH] >= parent.weights[CASH]
                assert d.weights[CASH] == 1.0 - math.fsum(d.weights[i] for i in RISKY)
    assert kept_total > 0 and removed_total > 0                         # both outcomes occur in the scenarios


@pytest.mark.parametrize('excess_weight,expected', [(0.0, 0.0), (5e-13, 0.0), (2e-12, None)])
def test_h2_bil_clamp_follows_decision_d022_item_9(monkeypatch, excess_weight, expected):
    # A parent whose risky weights exceed 100% by a rounding amount: BIL = 1 - fsum in [-1e-12, 0) is set to 0, a
    # lower value raises. TLT (5 positive months) and GLD (4) pass the h = 4 filter, so both are kept.
    from alpha_lab import hypotheses
    h = h2_scenario()
    real = h1(T, h, lookback=252, k=3)
    weights = {**{i: 0.0 for i in RISKY}, 'TLT': 0.6, 'GLD': 0.4 + excess_weight, CASH: 0.0}
    monkeypatch.setattr(hypotheses, 'h1', lambda *args: Decision(weights, real.signals))
    if expected is None:
        with pytest.raises(ValueError, match='exceed 100%'):
            h2(T, h, h=4)
        return
    d = h2(T, h, h=4)
    assert d.weights[CASH] == expected and math.copysign(1.0, d.weights[CASH]) == 1.0
    assert (d.weights['TLT'], d.weights['GLD']) == (0.6, 0.4 + excess_weight)


def test_empty_parent_gives_all_bil_for_h2():
    h = history(drift=negative())
    assert h1(T, h, lookback=252, k=3).weights[CASH] == 1.0
    for h_param in (4, 5):
        d = h2(T, h, h=h_param)
        assert d.weights == {**{i: 0.0 for i in RISKY}, CASH: 1.0}
        assert len(d.signals) == 9
        for row in d.signals:
            assert (row['weight'], row['parent_weight'], row['selected'], row['q']) == (0.0, 0.0, False, 0.0)
            assert row['positive_months'] == sum(row[f'excess_{j}'] > 0 for j in range(1, 7))
            assert row['filter_pass'] is (row['positive_months'] >= h_param)


def test_h2_rejects_non_month_end():
    h = history('2009-02-26')
    assert h1('2009-02-26', h, lookback=252, k=3).weights                # H1 has no calendar constraint
    with pytest.raises(ValueError, match='last XNYS session'):
        h2('2009-02-26', h, h=4)


def test_signal_rows():
    h = h2_scenario()
    parent = h1(T, h, lookback=252, k=3)
    for d, columns in ((parent, SIGNAL_COLUMNS_H1), (h2(T, h, h=4), SIGNAL_COLUMNS_H2)):
        assert len(d.signals) == 9
        assert [r['ticker'] for r in d.signals] == ASCII
        assert all(list(r) == columns and r['decision_session'] == T for r in d.signals)
        assert len({r['scale'] for r in d.signals}) == 1
        assert all(r['weight'] == d.weights[r['ticker']] for r in d.signals)
        assert all(type(r[c]) is float for r in d.signals for c in columns if c in FLOAT_COLUMNS)
        assert all(type(r['eligible']) is bool and type(r['selected']) is bool for r in d.signals)
        ranks = sorted(r['rank'] for r in d.signals if r['eligible'])
        assert ranks == list(range(1, len(ranks) + 1))
        assert all(r['rank'] is None for r in d.signals if not r['eligible'])
        assert all(r['selected'] == (r['eligible'] and r['rank'] <= 3) for r in d.signals)
        assert all((r['q'] > 0.0) == r['selected'] for r in d.signals)
        assert all(r['eligible'] == (r['score'] > 0.0) for r in d.signals)
    child = h2(T, h, h=5)
    for row, parent_row in zip(child.signals, parent.signals):
        assert {c: row[c] for c in SIGNAL_COLUMNS_H1 if c != 'weight'} == {
            c: parent_row[c] for c in SIGNAL_COLUMNS_H1 if c != 'weight'}
    assert [r['weight'] for r in child.signals] != [r['weight'] for r in parent.signals]


def test_decisions_ignore_future_data():
    frames = benchmark_frames()
    base = market_from_frames(frames)
    rng = np.random.default_rng(7)
    later = [s for s in base.sessions if s > T]
    assert len(later) > 20
    for f in frames.values():
        f.loc[later, ['open', 'close']] *= rng.uniform(0.5, 2.0, size=(len(later), 1))
    changed = market_from_frames(frames)
    assert changed.close.loc[later[0]].tolist() != base.close.loc[later[0]].tolist()
    a, b = base.history(T), changed.history(T)
    assert h1(T, a, lookback=252, k=3) == h1(T, b, lookback=252, k=3)
    assert h1(T, a, lookback=126, k=4) == h1(T, b, lookback=126, k=4)
    assert h2(T, a, h=4) == h2(T, b, h=4)
    # The test is not vacuous: a change at t itself moves the decision.
    for f in frames.values():
        f.loc[T, ['open', 'close']] *= 1.3
    moved = market_from_frames(frames).history(T)
    assert h1(T, a, lookback=252, k=3) != h1(T, moved, lookback=252, k=3)


def test_providers_require_warmup():
    market = market_from_frames(benchmark_frames(start='2008-01-02'))
    short = market.history('2008-12-30')
    with pytest.raises(ValueError):
        h1('2008-12-30', short, lookback=252, k=3)
    with pytest.raises(ValueError):
        h2('2008-12-30', short, h=4)
    enough = market.history(T)
    assert set(h1(T, enough, lookback=252, k=3).weights) == {*RISKY, CASH}
    assert set(h2(T, enough, h=4).weights) == {*RISKY, CASH}


def test_providers_require_history_ending_at_t():
    h = history()
    with pytest.raises(ValueError, match='2008-12-30'):
        h1('2008-12-30', h, lookback=252, k=3)
    with pytest.raises(ValueError, match='2008-12-30'):
        h2('2008-12-30', h, h=4)
