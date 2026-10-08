import math

import numpy as np
import pytest

from alpha_lab.features import CASH, RISKY
from alpha_lab.portfolio import capped, common_risk, inverse_vol, risk_detail


def _q(**kw):
    q = {t: 0.0 for t in RISKY}
    q.update(kw)
    return q


def _cov(**diag):
    cov = np.zeros((9, 9))
    for t, v in diag.items():
        cov[RISKY.index(t), RISKY.index(t)] = v
    return cov


def _sigma(**kw):
    s = {t: 0.2 for t in RISKY}
    s.update(kw)
    return s


def test_inverse_vol_carries_m_over_k():
    # m=2, K=9, weights 1/0.1=10 and 1/0.2=5: q_SPY=(2/9)*(10/15)=4/27, q_TLT=(2/9)*(5/15)=2/27
    q = inverse_vol(_sigma(SPY=0.1, TLT=0.2), ['SPY', 'TLT'], k=9)
    assert set(q) == set(RISKY)
    assert q['SPY'] == pytest.approx(4 / 27)
    assert q['TLT'] == pytest.approx(2 / 27)
    assert all(q[t] == 0.0 for t in RISKY if t not in ('SPY', 'TLT'))


def test_inverse_vol_empty_selection():
    q = inverse_vol(_sigma(), [])
    assert q == {t: 0.0 for t in RISKY}


def test_cap_and_group_scaling():
    # v: SPY .25 (capped), EFA .2, EEM .1; group sum .55 -> scale .5/.55; cov=0 so a=1; BIL = 1 - .5
    w = common_risk(_q(SPY=0.4, EFA=0.2, EEM=0.1), np.zeros((9, 9)))
    assert w['SPY'] == pytest.approx(0.25 * 0.5 / 0.55)
    assert w['EFA'] == pytest.approx(0.2 * 0.5 / 0.55)
    assert w['EEM'] == pytest.approx(0.1 * 0.5 / 0.55)
    assert w[CASH] == pytest.approx(0.5)


def test_vol_target_binds():
    # v_TLT=.25, var .64: V=.25*.8=.2, a=.5, w_TLT=.125, BIL=.875
    w = common_risk(_q(TLT=0.25), _cov(TLT=0.64))
    assert w['TLT'] == pytest.approx(0.125)
    assert w[CASH] == pytest.approx(0.875)


def test_vol_target_does_not_bind():
    # v_SPY=.25, var .04: V=.05 <= .10 -> a=1
    w = common_risk(_q(SPY=0.25), _cov(SPY=0.04))
    assert w['SPY'] == pytest.approx(0.25)
    assert w[CASH] == pytest.approx(0.75)


def test_zero_variance_gives_a_one():
    w = common_risk(_q(), _cov(SPY=0.04))
    assert w[CASH] == 1.0
    assert all(w[t] == 0.0 for t in RISKY)


def test_small_negative_variance_rounds_to_zero_and_large_raises():
    # v_SPY=.1: v'Sv = .01*cov_SPY
    w = common_risk(_q(SPY=0.1), _cov(SPY=-5e-11))  # -5e-13 -> 0 -> a=1
    assert w['SPY'] == pytest.approx(0.1)
    with pytest.raises(ValueError):
        common_risk(_q(SPY=0.1), _cov(SPY=-1e-7))  # -1e-9


def test_result_is_python_floats_and_bil_non_negative():
    w = common_risk(_q(SPY=0.3, TLT=0.1), _cov(SPY=0.04, TLT=0.01))
    assert set(w) == set(RISKY) | {CASH}
    assert all(type(v) is float for v in w.values())
    assert w[CASH] >= 0.0
    assert all(type(v) is float for v in inverse_vol(_sigma(), ['SPY']).values())


def _frozen_common_risk(q, cov):
    """Inline copy of the N3 common_risk algorithm before the split (reference for bit identity)."""
    # The constants below (0.25, 0.50, 0.10, 1e-12) are copied from the pre-split portfolio.common_risk, the parent of
    # commit 8b224b4; do not regenerate them from the code under test.
    groups = {'Equity': ('SPY', 'EFA', 'EEM'), 'Treasury': ('IEF', 'TLT'), 'Credit': ('LQD', 'HYG'), 'Real': ('GLD', 'DBC')}
    v = {t: min(float(q[t]), 0.25) for t in RISKY}
    for members in groups.values():
        total = math.fsum(v[t] for t in members)
        if total > 0.50:
            for t in members:
                v[t] = v[t] * 0.50 / total
    vec = np.array([v[t] for t in RISKY], dtype=float)
    variance = float(vec @ np.asarray(cov, dtype=float) @ vec)
    if variance < -1e-12:
        raise ValueError(f'negative portfolio variance {variance}')
    vol = math.sqrt(max(variance, 0.0))
    scale = 1.0 if vol == 0.0 else min(1.0, 0.10 / vol)
    w = {t: float(scale * v[t]) for t in RISKY}
    cash = 1.0 - math.fsum(w.values())
    if cash < 0.0:
        if cash < -1e-12:
            raise ValueError(f'risky weights exceed 100%: cash {cash}')
        cash = 0.0
    w[CASH] = float(cash)
    return w


def test_risk_detail_matches_common_risk():
    hand = [
        (_q(SPY=0.4, EFA=0.2, EEM=0.1), np.zeros((9, 9))),
        (_q(TLT=0.25), _cov(TLT=0.64)),
        (_q(SPY=0.25), _cov(SPY=0.04)),
        (_q(), _cov(SPY=0.04)),
        (_q(SPY=0.1), _cov(SPY=-5e-11)),
        (_q(SPY=0.3, TLT=0.1), _cov(SPY=0.04, TLT=0.01)),
    ]
    rng = np.random.default_rng(20261008)
    random_cases = []
    for _ in range(50):
        q = {t: 0.0 for t in RISKY}
        for i in rng.choice(9, size=4, replace=False):  # at most 4 names at the 25% cap keeps risky weight <= 100%
            q[RISKY[i]] = float(rng.uniform(0.0, 0.45))
        m = rng.normal(size=(9, 9)) * 0.1
        random_cases.append((q, m @ m.T))
    for q, cov in hand + random_cases:
        expected = _frozen_common_risk(q, cov)
        v, a, w = risk_detail(q, cov)
        assert w == expected
        assert common_risk(q, cov) == expected
        assert v == capped(q)
        assert type(a) is float and 0.0 < a <= 1.0
        for t in RISKY:
            assert w[t] == float(a * v[t])


def test_risk_detail_scale_values():
    v, a, w = risk_detail(_q(), _cov(SPY=0.04))
    assert a == 1.0 and all(v[t] == 0.0 for t in RISKY)
    v, a, w = risk_detail(_q(TLT=0.25), _cov(TLT=0.64))
    assert a == pytest.approx(0.5)
    assert w['TLT'] == a * v['TLT']


def test_capped_group_cap_hand_case():
    v = capped(_q(SPY=0.4, EFA=0.2, EEM=0.1))
    assert set(v) == set(RISKY)
    assert v['SPY'] == 0.25 * 0.5 / 0.55
    assert v['EFA'] == 0.2 * 0.5 / 0.55
    assert v['EEM'] == 0.1 * 0.5 / 0.55
    assert all(v[t] == 0.0 for t in RISKY if t not in ('SPY', 'EFA', 'EEM'))
