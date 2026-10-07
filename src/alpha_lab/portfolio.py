"""Section 5 weight construction: inverse volatility and common risk limits."""
import math

import numpy as np

from alpha_lab.features import CASH, RISKY

GROUPS = {'Equity': ('SPY', 'EFA', 'EEM'), 'Treasury': ('IEF', 'TLT'), 'Credit': ('LQD', 'HYG'), 'Real': ('GLD', 'DBC')}
ETF_CAP = 0.25
GROUP_CAP = 0.50
VOL_TARGET = 0.10
VARIANCE_TOLERANCE = 1e-12


def inverse_vol(sigma, selected, k=9):
    """q_i = (m / k) * (1 / sigma_i) / sum_S(1 / sigma_j) for i in S, 0 elsewhere."""
    chosen = set(selected)
    q = {t: 0.0 for t in RISKY}
    if not chosen:
        return q
    total = math.fsum(1.0 / float(sigma[t]) for t in chosen)
    for t in chosen:
        q[t] = float(len(chosen) / k * (1.0 / float(sigma[t])) / total)
    return q


def common_risk(q, cov):
    """Apply ETF cap, group cap, volatility target and cash remainder; returns weights over RISKY + BIL."""
    v = {t: min(float(q[t]), ETF_CAP) for t in RISKY}
    for members in GROUPS.values():
        total = math.fsum(v[t] for t in members)
        if total > GROUP_CAP:
            for t in members:
                v[t] = v[t] * GROUP_CAP / total
    vec = np.array([v[t] for t in RISKY], dtype=float)
    variance = float(vec @ np.asarray(cov, dtype=float) @ vec)
    if variance < -VARIANCE_TOLERANCE:
        raise ValueError(f'negative portfolio variance {variance}')
    vol = math.sqrt(max(variance, 0.0))
    scale = 1.0 if vol == 0.0 else min(1.0, VOL_TARGET / vol)
    w = {t: float(scale * v[t]) for t in RISKY}
    cash = 1.0 - math.fsum(w.values())
    if cash < 0.0:
        if cash < -VARIANCE_TOLERANCE:
            raise ValueError(f'risky weights exceed 100%: cash {cash}')
        cash = 0.0
    w[CASH] = float(cash)
    return w
