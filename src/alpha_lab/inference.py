"""Pure inference helpers: utility, paired circular block bootstrap and Holm adjustment (N5 spec 6.2-6.4, P8)."""
import math
import numpy as np
from alpha_lab.features import ANNUAL
from alpha_lab.metrics import UTILITY_PENALTY


def utility(e):
    """U = 252 * mean(e) - 1.5 * 252 * var(e, ddof=1) over the last axis of the daily excess returns."""
    e = np.asarray(e, dtype=float)
    return ANNUAL * e.mean(axis=-1) - UTILITY_PENALTY * ANNUAL * e.var(axis=-1, ddof=1)


def block_indices(n, length, replicates, seed):
    """Circular block indices of shape (replicates, n); one fresh Generator(PCG64(seed)) per (n, length) pair (P8)."""
    rng = np.random.Generator(np.random.PCG64(seed))
    starts = rng.integers(0, n, size=(replicates, math.ceil(n / length)))
    idx = (starts[:, :, None] + np.arange(length)) % n
    return idx.reshape(replicates, -1)[:, :n]


def summarize(delta_hat, delta_star):
    """Basic interval [2 d - Q_0.975, 2 d - Q_0.025] and one-sided p = (1 + #[d* - d >= d]) / (B + 1)."""
    star = np.asarray(delta_star, dtype=float)
    q_low, q_high = np.quantile(star, [0.025, 0.975], method='linear')
    p = (1 + int(np.count_nonzero(star - delta_hat >= delta_hat))) / (star.size + 1)
    return float(2 * delta_hat - q_high), float(2 * delta_hat - q_low), float(p)


def paired_bootstrap(r_candidate, r_comparator, r_bil, length, replicates=10000, seed=20261006, chunk=500):
    """Paired circular block bootstrap of DeltaU = U(candidate) - U(comparator) on excess returns over BIL."""
    e_c = np.asarray(r_candidate, dtype=float) - np.asarray(r_bil, dtype=float)
    e_k = np.asarray(r_comparator, dtype=float) - np.asarray(r_bil, dtype=float)
    idx = block_indices(len(e_c), length, replicates, seed)
    delta_hat = float(utility(e_c) - utility(e_k))
    star = np.empty(replicates)
    for lo in range(0, replicates, chunk):
        rows = idx[lo:lo + chunk]
        star[lo:lo + chunk] = utility(e_c[rows]) - utility(e_k[rows])
    ci_low, ci_high, p = summarize(delta_hat, star)
    return {'delta_u': delta_hat, 'mean_excess_difference': float(ANNUAL * (e_c.mean() - e_k.mean())),
            'ci_low': ci_low, 'ci_high': ci_high, 'p': p}


def holm(p_values):
    """Holm step-down adjusted p-values: running maximum of (m - j + 1) * p_(j), capped at 1."""
    order = sorted(p_values, key=lambda k: p_values[k])
    m, out, running = len(order), {}, 0.0
    for j, key in enumerate(order):
        running = max(running, min(1.0, (m - j) * p_values[key]))
        out[key] = running
    return out
