"""Utility, bootstrap, Holm, monthly returns, class proxies and Newey-West regressions (spec 6.2-6.5, P8-P10)."""
import numpy as np
import pandas as pd
from alpha_lab import inference
from alpha_lab.inference import (annual_alpha, block_indices, class_proxies, holm, monthly_returns, newey_west,
                                 paired_bootstrap, regress, summarize, utility)
from alpha_lab.portfolio import GROUPS


def test_utility_matches_loop():
    e = np.random.default_rng(3).normal(0.0004, 0.01, 50)
    xs = [float(x) for x in e]
    mean = sum(xs) / len(xs)
    var = sum((x - mean) ** 2 for x in xs) / (len(xs) - 1)
    assert abs(utility(e) - (252 * mean - 1.5 * 252 * var)) < 1e-12


def test_block_indices_shape_range_and_reproducibility():
    idx = block_indices(10, 4, 5, 1)
    assert idx.shape == (5, 10)
    assert np.issubdtype(idx.dtype, np.integer)
    assert idx.min() >= 0 and idx.max() < 10
    assert np.array_equal(idx, block_indices(10, 4, 5, 1))
    for row in idx:
        assert all(row[j + 1] == (row[j] + 1) % 10 for j in range(3))


def test_block_indices_when_n_is_not_a_multiple_of_the_length():
    assert block_indices(10, 4, 5, 1).shape[1] == 10
    assert block_indices(3, 4, 5, 1).shape[1] == 3


def test_summarize_hand_case():
    low, high, p = summarize(1.0, np.arange(0, 11, dtype=float))
    assert abs(low - (2 - 9.75)) < 1e-12
    assert abs(high - (2 - 0.25)) < 1e-12
    assert abs(p - (1 + 9) / (11 + 1)) < 1e-12


def test_identical_series_gives_p_one():
    rng = np.random.default_rng(5)
    r, bil = rng.normal(0.0005, 0.01, 120), rng.normal(0.0001, 0.0001, 120)
    out = paired_bootstrap(r, r.copy(), bil, 21, replicates=100)
    assert out['delta_u'] == 0 and out['p'] == 1.0
    assert out['ci_low'] == out['ci_high'] == 0.0


def test_bootstrap_is_chunk_invariant():
    rng = np.random.default_rng(6)
    c, k, bil = rng.normal(0.0006, 0.01, 90), rng.normal(0.0003, 0.009, 90), rng.normal(0.0001, 0.0001, 90)
    a = paired_bootstrap(c, k, bil, 21, replicates=200, chunk=7)
    b = paired_bootstrap(c, k, bil, 21, replicates=200, chunk=500)
    assert a == b


def test_bootstrap_point_estimates_on_original_series():
    rng = np.random.default_rng(7)
    c, k, bil = rng.normal(0.0006, 0.01, 90), rng.normal(0.0003, 0.009, 90), rng.normal(0.0001, 0.0001, 90)
    out = paired_bootstrap(c, k, bil, 21, replicates=50)
    assert abs(out['delta_u'] - (utility(c - bil) - utility(k - bil))) < 1e-12
    assert abs(out['mean_excess_difference'] - 252 * ((c - bil).mean() - (k - bil).mean())) < 1e-12


def test_bootstrap_shares_replicates_for_equal_n_and_length(monkeypatch):
    assert np.array_equal(block_indices(90, 21, 30, 20261006), block_indices(90, 21, 30, 20261006))
    assert not np.array_equal(block_indices(90, 21, 30, 20261006), block_indices(90, 63, 30, 20261006))
    drawn = []

    def record(n, length, replicates, seed):
        drawn.append(block_indices(n, length, replicates, seed))
        return drawn[-1]

    monkeypatch.setattr(inference, 'block_indices', record)
    rng = np.random.default_rng(8)
    bil = rng.normal(0.0001, 0.0001, 90)
    for _ in range(2):
        paired_bootstrap(rng.normal(0.0005, 0.01, 90), rng.normal(0.0003, 0.01, 90), bil, 21, replicates=30)
    assert len(drawn) == 2 and np.array_equal(drawn[0], drawn[1])


def test_circular_indices_wrap():
    n, length = 10, 4
    idx = block_indices(n, length, 200, 1)
    wraps = [(r, j) for r in range(len(idx)) for j in range(n - 1)
             if j % length != length - 1 and idx[r, j] == n - 1 and idx[r, j + 1] == 0]
    assert wraps


def test_bootstrap_matches_loop_reference():
    rng = np.random.default_rng(9)
    n, length, reps = 40, 6, 60
    c, k, bil = rng.normal(0.0006, 0.01, n), rng.normal(0.0003, 0.009, n), rng.normal(0.0001, 0.0001, n)

    def u(xs):
        mean = sum(xs) / len(xs)
        return 252 * mean - 1.5 * 252 * sum((x - mean) ** 2 for x in xs) / (len(xs) - 1)

    ec, ek = [float(a - b) for a, b in zip(c, bil)], [float(a - b) for a, b in zip(k, bil)]
    idx = block_indices(n, length, reps, 20261006)
    hat = u(ec) - u(ek)
    star = sorted(u([ec[i] for i in row]) - u([ek[i] for i in row]) for row in idx)

    def quantile(q):
        pos = q * (reps - 1)
        lo = int(pos)
        return star[lo] + (pos - lo) * (star[min(lo + 1, reps - 1)] - star[lo])

    out = paired_bootstrap(c, k, bil, length, replicates=reps, chunk=16)
    assert abs(out['delta_u'] - hat) < 1e-12
    assert abs(out['mean_excess_difference'] - 252 * (sum(ec) / n - sum(ek) / n)) < 1e-12
    assert abs(out['ci_low'] - (2 * hat - quantile(0.975))) < 1e-12
    assert abs(out['ci_high'] - (2 * hat - quantile(0.025))) < 1e-12
    assert out['p'] == (1 + sum(1 for d in star if d - hat >= hat)) / (reps + 1)


def test_holm_worked_examples():
    out = holm({'a': 0.01, 'b': 0.04, 'c': 0.03, 'd': 0.5, 'e': 0.02, 'f': 0.2})
    expected = {'a': 0.06, 'e': 0.10, 'c': 0.12, 'b': 0.12, 'f': 0.4, 'd': 0.5}
    assert set(out) == set(expected)
    assert all(abs(out[k] - v) < 1e-12 for k, v in expected.items())
    assert holm({'x': 0.6, 'y': 0.7}) == {'x': 1.0, 'y': 1.0}


def test_holm_ties():
    out = holm({'a': 0.01, 'b': 0.01, 'c': 0.5})
    assert all(abs(out[k] - v) < 1e-12 for k, v in {'a': 0.03, 'b': 0.03, 'c': 0.5}.items())


def _design(rng, n, cols):
    return rng.normal(0.0, 0.02, (n, cols))


def _expected_covariance(X, u, lag):
    """Explicit-loop Newey-West covariance of OLS on [1, X] with Bartlett weights and the n / (n - k) factor."""
    n = len(u)
    Z = [np.concatenate([[1.0], X[t]]) for t in range(n)]
    k = len(Z[0])
    s = sum(u[t] ** 2 * np.outer(Z[t], Z[t]) for t in range(n))
    for ell in range(1, lag + 1):
        w = 1 - ell / (lag + 1)
        for t in range(ell, n):
            s = s + w * u[t] * u[t - ell] * (np.outer(Z[t], Z[t - ell]) + np.outer(Z[t - ell], Z[t]))
    xtx_inv = np.linalg.inv(sum(np.outer(z, z) for z in Z))
    return xtx_inv @ s @ xtx_inv * n / (n - k)


def test_ols_recovers_noise_free_coefficients():
    x = np.random.default_rng(11).normal(0.0, 0.02, 60)
    fit = regress(0.002 + 1.5 * x, x)
    assert abs(fit['coef'][0] - 0.002) < 1e-10 and abs(fit['coef'][1] - 1.5) < 1e-10
    assert fit['n'] == 60 and fit['k'] == 2 and fit['rank'] == 2 and fit['cond'] < 1e8


def test_regress_adds_the_intercept_and_accepts_a_matrix():
    rng = np.random.default_rng(12)
    X = _design(rng, 50, 3)
    y = 0.001 + X @ np.array([0.5, -0.2, 0.9]) + rng.normal(0.0, 0.005, 50)
    fit = regress(y, X)
    assert fit['k'] == 4 and len(fit['coef']) == 4 and len(fit['se']) == 4
    Z = np.column_stack([np.ones(50), X])
    expected = np.linalg.solve(Z.T @ Z, Z.T @ y)
    assert np.max(np.abs(fit['coef'] - expected)) < 1e-10


def test_newey_west_lag_zero_is_hc1():
    rng = np.random.default_rng(13)
    n = 40
    X = _design(rng, n, 2)
    y = 0.001 + X @ np.array([1.0, -0.5]) + rng.normal(0.0, 0.01, n)
    Z = np.column_stack([np.ones(n), X])
    u = y - Z @ np.linalg.solve(Z.T @ Z, Z.T @ y)
    bread = np.linalg.inv(Z.T @ Z)
    meat = sum(u[t] ** 2 * np.outer(Z[t], Z[t]) for t in range(n))
    hc1 = bread @ meat @ bread * n / (n - 3)
    assert np.max(np.abs(newey_west(Z, u, lag=0) - hc1)) < 1e-14
    assert np.max(np.abs(newey_west(Z, u, lag=0) - _expected_covariance(X, u, 0))) < 1e-14


def test_newey_west_lag_three_matches_loop():
    rng = np.random.default_rng(14)
    n = 45
    X = _design(rng, n, 2)
    e = rng.normal(0.0, 0.01, n)
    noise = e + 0.6 * np.concatenate([[0.0], e[:-1]])
    y = 0.001 + X @ np.array([1.0, -0.5]) + noise
    Z = np.column_stack([np.ones(n), X])
    u = y - Z @ np.linalg.solve(Z.T @ Z, Z.T @ y)
    cov = newey_west(Z, u, lag=3)
    expected = _expected_covariance(X, u, 3)
    assert np.max(np.abs(cov - expected)) < 1e-14
    assert abs(cov[0, 0] - _expected_covariance(X, u, 0)[0, 0]) > 1e-9
    fit = regress(y, X)
    assert np.max(np.abs(fit['se'] - np.sqrt(np.diag(expected)))) < 1e-14


def test_monthly_returns_use_the_previous_month_end_as_base():
    values = pd.Series([100.0, 110.0, 121.0, 99.0, 108.9, 120.0],
                       index=['2013-12-30', '2013-12-31', '2014-01-15', '2014-01-31', '2014-02-14', '2014-02-28'])
    out = monthly_returns(values)
    assert list(out.index) == ['2014-01', '2014-02']
    assert abs(out['2014-01'] - (99.0 / 110.0 - 1)) < 1e-15
    assert abs(out['2014-02'] - (120.0 / 99.0 - 1)) < 1e-15


def test_monthly_returns_drop_a_first_month_without_base():
    values = pd.Series([100.0, 101.0], index=['2014-01-02', '2014-01-31'])
    assert len(monthly_returns(values)) == 0
    values = pd.Series([100.0, 101.0, 103.0, 104.0], index=['2014-01-02', '2014-01-31', '2014-02-03', '2014-02-28'])
    out = monthly_returns(values)
    assert list(out.index) == ['2014-02'] and abs(out['2014-02'] - (104.0 / 101.0 - 1)) < 1e-15


def test_class_proxies_use_the_group_members_only():
    rng = np.random.default_rng(15)
    cols = [t for members in GROUPS.values() for t in members]
    excess = pd.DataFrame(rng.normal(0.0, 0.03, (12, len(cols))), columns=cols,
                          index=[f'2014-{m:02d}' for m in range(1, 13)])
    excess['BIL'] = 0.123
    out = class_proxies(excess, GROUPS)
    assert list(out.columns) == list(GROUPS) and list(out.index) == list(excess.index)
    for name, members in GROUPS.items():
        for month in excess.index:
            expected = sum(float(excess.loc[month, t]) for t in members) / len(members)
            assert abs(out.loc[month, name] - expected) < 1e-15
    spy_efa_eem = [float(excess.loc['2014-03', t]) for t in ('SPY', 'EFA', 'EEM')]
    assert abs(out.loc['2014-03', 'Equity'] - sum(spy_efa_eem) / 3) < 1e-15


def _fit_for_gate(n, X, seed=16):
    rng = np.random.default_rng(seed)
    return regress(0.001 + rng.normal(0.0, 0.01, n), X)


def test_alpha_gates():
    rng = np.random.default_rng(17)
    short = _fit_for_gate(30, _design(rng, 30, 1))
    out = annual_alpha(short)
    assert out['reason'] == 'months' and out['alpha'] is None
    assert out['se'] is None and out['ci_low'] is None and out['ci_high'] is None

    x = _design(rng, 60, 1)
    twin = _fit_for_gate(60, np.column_stack([x, x]))
    assert twin['rank'] < twin['k']
    out = annual_alpha(twin)
    assert out['reason'] == 'rank' and out['alpha'] is None and out['se'] is None

    zero = _fit_for_gate(60, np.zeros((60, 1)))
    assert zero['rank'] < zero['k']
    assert annual_alpha(zero)['reason'] == 'rank' and annual_alpha(zero)['alpha'] is None

    nearly = _fit_for_gate(60, np.column_stack([x, x + 1e-9 * rng.normal(0.0, 1.0, (60, 1))]))
    assert nearly['rank'] == nearly['k'] and nearly['cond'] > 1e8
    out = annual_alpha(nearly)
    assert out['reason'] == 'condition' and out['alpha'] is None and out['ci_high'] is None

    both = _fit_for_gate(30, np.column_stack([x[:30], x[:30]]))
    assert annual_alpha(both)['reason'] == 'months'


def test_valid_alpha_scales_by_twelve():
    rng = np.random.default_rng(18)
    X = _design(rng, 60, 2)
    fit = regress(0.002 + X @ np.array([0.7, 0.3]) + rng.normal(0.0, 0.01, 60), X)
    out = annual_alpha(fit)
    assert out['reason'] is None
    assert abs(out['alpha'] - 12 * fit['coef'][0]) < 1e-15
    assert abs(out['se'] - 12 * fit['se'][0]) < 1e-15
    assert abs(out['ci_low'] - (out['alpha'] - 1.96 * out['se'])) < 1e-15
    assert abs(out['ci_high'] - (out['alpha'] + 1.96 * out['se'])) < 1e-15
    assert abs(out['ci_low'] - 12 * (fit['coef'][0] - 1.96 * fit['se'][0])) < 1e-14
