import numpy as np
import pytest

from alpha_lab import adaptive, inference, metrics
from alpha_lab.adaptive import CANDIDATES, FALLBACK, choose, selection_year, stability, validation_segment


def test_constants():
    assert CANDIDATES == ('H1_252_3', 'H1_252_4', 'H1_126_3', 'H1_126_4')
    assert FALLBACK == 'H1_252_3'
    assert adaptive.TOLERANCE == 0.001
    assert adaptive.PENALTY == 1.5 == metrics.UTILITY_PENALTY
    assert (adaptive.FIRST_YEAR, adaptive.LAST_YEAR) == (2014, 2022)


def test_selection_year_mapping():
    assert selection_year('2013-12-31') == 2014
    assert selection_year('2014-06-30') == 2014
    assert selection_year('2022-11-30') == 2022
    for bad in ('2013-11-29', '2022-12-30'):
        with pytest.raises(ValueError):
            selection_year(bad)


def test_selection_year_non_final_december_session_keeps_its_year():
    assert selection_year('2014-12-15') == 2014
    assert selection_year('2014-12-31') == 2015


def test_validation_segment_boundaries():
    assert validation_segment(2014) == ('2011-12-30', '2013-12-31')
    assert validation_segment(2022) == ('2019-12-31', '2021-12-31')
    for bad in (2013, 2023):
        with pytest.raises(ValueError):
            validation_segment(bad)


def test_choose_prefers_the_earlier_close_candidate():
    result = choose({'H1_252_3': 0.10, 'H1_252_4': 0.1005, 'H1_126_3': 0.08, 'H1_126_4': 0.1005})
    assert result['close'] == ['H1_252_3', 'H1_252_4', 'H1_126_4']
    assert result['chosen'] == 'H1_252_3'
    assert result['best'] == 0.1005
    assert result['fallback'] is False
    assert result['warning'] is None


def test_choose_boundary():
    best = 0.2
    edge = best - 0.001
    base = {'H1_252_4': best, 'H1_126_3': 0.0, 'H1_126_4': 0.0}
    inside = choose({'H1_252_3': edge, **base})
    assert 'H1_252_3' in inside['close']
    outside = choose({'H1_252_3': edge - 1e-9, **base})
    assert 'H1_252_3' not in outside['close']
    assert outside['chosen'] == 'H1_252_4'


def test_choose_ranks_by_order_not_by_dict_position():
    result = choose({'H1_126_4': 0.5, 'H1_126_3': 0.5, 'H1_252_4': 0.1})
    assert result['close'] == ['H1_126_3', 'H1_126_4']
    assert result['chosen'] == 'H1_126_3'


def test_choose_accepts_a_subset_and_rejects_unknown_keys():
    result = choose({'H1_126_3': 0.3})
    assert result['chosen'] == 'H1_126_3' and result['close'] == ['H1_126_3'] and result['fallback'] is False
    with pytest.raises(ValueError):
        choose({'H1_252_3': 0.1, 'other': 0.2})


def test_choose_falls_back_only_for_a_non_finite_utility():
    for bad in (float('nan'), float('inf'), float('-inf')):
        result = choose({'H1_252_3': 0.1, 'H1_252_4': 0.3, 'H1_126_3': bad, 'H1_126_4': 0.2})
        assert result['chosen'] == 'H1_252_3'
        assert result['fallback'] is True
        assert result['best'] is None and result['close'] == []
        assert isinstance(result['warning'], str) and 'H1_126_3' in result['warning']
        assert 'H1_252_4' not in result['warning']
        stripped = result['warning']
        for name in CANDIDATES:
            stripped = stripped.replace(name, '')
        assert not any(ch.isdigit() for ch in stripped)
    finite = choose({'H1_252_3': 0.1, 'H1_252_4': 0.3, 'H1_126_3': 0.0, 'H1_126_4': 0.2})
    assert finite['fallback'] is False and finite['warning'] is None and finite['chosen'] == 'H1_252_4'


def _excess(seed=3, n=504):
    rng = np.random.default_rng(seed)
    series = {c: rng.normal(0.0, 0.01, n) for c in CANDIDATES}
    series['H1_126_3'] = np.full(n, 0.01)
    return series


def test_stability_with_a_dominant_candidate():
    series = _excess()
    result = stability(series, replicates=200)
    assert result['frequency']['H1_126_3'] == 1.0
    assert set(result['frequency']) == set(CANDIDATES)
    assert sum(result['frequency'].values()) == pytest.approx(1.0)
    assert result['fallback_replicates'] == 0
    assert stability(series, replicates=200) == result


def test_stability_joint_blocks_match_an_explicit_computation():
    rng = np.random.default_rng(5)
    n, replicates = 126, 50
    series = {c: rng.normal(0.0005 * i, 0.01, n) for i, c in enumerate(CANDIDATES)}
    idx = inference.block_indices(n, 21, replicates, 20261007)
    counts = dict.fromkeys(CANDIDATES, 0)
    for row in idx:
        u = {c: 252 * series[c][row].mean() - 1.5 * 252 * series[c][row].var(ddof=1) for c in CANDIDATES}
        best = max(u.values())
        counts[next(c for c in CANDIDATES if u[c] >= best - 0.001)] += 1
    result = stability(series, replicates=replicates, length=21)
    assert result['frequency'] == {c: counts[c] / replicates for c in CANDIDATES}
    assert sum(counts.values()) == replicates


def test_stability_counts_fallback_replicates():
    series = _excess()
    series['H1_252_4'] = series['H1_252_4'].copy()
    series['H1_252_4'][10] = np.nan
    result = stability(series, replicates=40)
    hit = int((inference.block_indices(504, 63, 40, 20261007) == 10).any(axis=1).sum())
    assert 0 < hit < 40
    assert result['fallback_replicates'] == hit
    series = _excess()
    series['H1_252_4'] = np.full(504, np.inf)
    result = stability(series, replicates=40)
    assert result['fallback_replicates'] == 40
    assert result['frequency']['H1_252_3'] == 1.0
    assert sum(result['frequency'].values()) == pytest.approx(1.0)


def test_stability_requires_equal_lengths():
    series = _excess()
    series['H1_126_4'] = series['H1_126_4'][:-1]
    with pytest.raises(ValueError):
        stability(series, replicates=10)
