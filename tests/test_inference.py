"""Utility, paired circular block bootstrap and Holm adjustment (spec sections 6.2-6.4, P8)."""
import numpy as np
from alpha_lab import inference
from alpha_lab.inference import block_indices, holm, paired_bootstrap, summarize, utility


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
