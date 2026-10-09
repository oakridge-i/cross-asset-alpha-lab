"""Utility, paired circular block bootstrap and Holm adjustment (spec sections 6.2-6.4, P8)."""
import numpy as np
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


def test_bootstrap_shares_replicates_for_equal_n_and_length():
    assert np.array_equal(block_indices(90, 21, 30, 20261006), block_indices(90, 21, 30, 20261006))
    assert not np.array_equal(block_indices(90, 21, 30, 20261006), block_indices(90, 63, 30, 20261006))


def test_holm_worked_examples():
    out = holm({'a': 0.01, 'b': 0.04, 'c': 0.03, 'd': 0.5, 'e': 0.02, 'f': 0.2})
    expected = {'a': 0.06, 'e': 0.10, 'c': 0.12, 'b': 0.12, 'f': 0.4, 'd': 0.5}
    assert set(out) == set(expected)
    assert all(abs(out[k] - v) < 1e-12 for k, v in expected.items())
    assert holm({'x': 0.6, 'y': 0.7}) == {'x': 1.0, 'y': 1.0}
