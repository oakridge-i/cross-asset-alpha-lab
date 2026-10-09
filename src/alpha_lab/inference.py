"""Pure inference helpers: utility, paired circular block bootstrap, Holm adjustment, monthly returns, class proxies
and Newey-West regressions (N5 spec 6.2-6.5, P8-P10)."""
import math
import numpy as np
import pandas as pd
from alpha_lab.features import ANNUAL
from alpha_lab.metrics import UTILITY_PENALTY

MIN_MONTHS = 36
MAX_CONDITION = 1e8
NORMAL_95 = 1.96


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


def monthly_returns(values):
    """Month-end ratio minus one on the series' own sessions, labeled YYYY-MM (P10).

    The base of a month is the last session of the previous month present in the series; a month without a
    base (the first one in the series) is not emitted.
    """
    series = pd.Series(values)
    month = pd.Index([str(label)[:7] for label in series.index])
    ends = series.groupby(month, sort=True).last()
    out = ends / ends.shift(1) - 1.0
    return out.iloc[1:]


def class_proxies(monthly_excess, groups):
    """Unweighted mean of the members' monthly excess returns for each group (P10)."""
    return pd.DataFrame({name: monthly_excess[list(members)].mean(axis=1) for name, members in groups.items()})


def newey_west(X, residuals, lag=3):
    """Newey-West covariance of OLS coefficients with Bartlett weights 1 - l / (lag + 1) and the factor n / (n - k).

    X is the full design matrix including the intercept column; k is its number of columns. lag = 0 is HC1.
    """
    X = np.asarray(X, dtype=float)
    u = np.asarray(residuals, dtype=float)
    n, k = X.shape
    scores = X * u[:, None]
    meat = scores.T @ scores
    for ell in range(1, lag + 1):
        cross = scores[ell:].T @ scores[:-ell]
        meat = meat + (1.0 - ell / (lag + 1)) * (cross + cross.T)
    bread = np.linalg.pinv(X.T @ X)
    factor = n / (n - k) if n > k else float('nan')
    return bread @ meat @ bread * factor


def regress(y, X, lag=3):
    """OLS of y on an intercept plus the columns of X; regress adds the intercept, so coef[0] is the intercept.

    Returns the coefficients, Newey-West standard errors, n, k (columns including the intercept), the design
    matrix rank and its condition number. Rank-deficient designs are fitted by least squares and reported through
    rank and cond; annual_alpha gates on them.
    """
    y = np.asarray(y, dtype=float)
    X = np.asarray(X, dtype=float)
    if X.ndim == 1:
        X = X[:, None]
    Z = np.column_stack([np.ones(len(y)), X])
    coef = np.linalg.lstsq(Z, y, rcond=None)[0]
    cov = newey_west(Z, y - Z @ coef, lag)
    return {'coef': coef, 'se': np.sqrt(np.diag(cov)), 'n': int(Z.shape[0]), 'k': int(Z.shape[1]),
            'cond': float(np.linalg.cond(Z)), 'rank': int(np.linalg.matrix_rank(Z))}


def annual_alpha(fit):
    """Annual alpha = 12 x the monthly intercept; its standard error and interval (+/- 1.96 se) are scaled by 12.

    Gates in order: months (n < 36), rank (rank < k), condition (cond > 1e8). A gated fit returns None for all
    four numbers and the reason; otherwise the reason is None.
    """
    if fit['n'] < MIN_MONTHS:
        reason = 'months'
    elif fit['rank'] < fit['k']:
        reason = 'rank'
    elif not fit['cond'] <= MAX_CONDITION:
        reason = 'condition'
    else:
        alpha, se = 12.0 * float(fit['coef'][0]), 12.0 * float(fit['se'][0])
        return {'alpha': alpha, 'se': se, 'ci_low': alpha - NORMAL_95 * se, 'ci_high': alpha + NORMAL_95 * se,
                'reason': None}
    return {'alpha': None, 'se': None, 'ci_low': None, 'ci_high': None, 'reason': reason}
