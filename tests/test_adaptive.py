import ast
import inspect
from dataclasses import replace
from types import SimpleNamespace
import numpy as np
import pandas as pd
import pytest

from n3_fixtures import benchmark_frames
from alpha_lab import adaptive, inference, metrics
from alpha_lab.adaptive import CANDIDATES, FALLBACK, choose, selection_year, stability, validation_segment
from alpha_lab.hypotheses import Decision
from alpha_lab.market import market_from_frames
from alpha_lab.provenance import canonical_bytes


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


# Policy provider (N5 spec 5.2, 5.5; D025 items 4-7 and 15), unit level with a recording fake of engine.simulate.

SEGMENT_2014 = ('2011-12-30', '2013-12-31')
LOG_KEYS = {'year', 'selection_date', 'segment_start', 'segment_end', 'decisions', 'returns', 'utility',
            'best_utility', 'close_set', 'chosen', 'fallback', 'warning', 'stability'}
HOLDING = {'H1_252_3': 'SPY', 'H1_252_4': 'EFA', 'H1_126_3': 'IEF', 'H1_126_4': 'GLD'}


@pytest.fixture(scope='module')
def market():
    return market_from_frames(benchmark_frames(start='2007-12-03', end='2014-07-31'))


def fake_provider(name):
    def provider(t, history):
        assert history.sessions[-1] == t
        weights = dict.fromkeys(history.tickers, 0.0)
        weights[HOLDING[name]] = 0.5
        return Decision(weights, [{'decision_session': t, 'ticker': HOLDING[name], 'weight': 0.5},
                                  {'decision_session': t, 'ticker': 'TLT', 'weight': 0.0}])
    provider.candidate = name
    return provider


FAKE_PROVIDERS = {name: fake_provider(name) for name in CANDIDATES}


def fake_navs(market, sessions, name, drift):
    bil = market.close['BIL']
    noise = np.random.default_rng(CANDIDATES.index(name)).normal(0.0, 0.004, len(sessions))
    navs = [100000.0]
    for i in range(1, len(sessions)):
        r = bil[sessions[i]] / bil[sessions[i - 1]] - 1
        navs.append(navs[-1] * (1 + r + drift + noise[i]))
    return navs


class FakeSimulate:
    """Records (market, candidate, (start, end)); the NAV of a candidate grows by the BIL close return plus its drift and a
    noise term that depends only on the candidate, so the result does not depend on the call order."""

    def __init__(self, drift=None, failed=(), raising=None, short=(), nan=()):
        self.calls = []
        self.drift = {**dict.fromkeys(CANDIDATES, 0.0), **(drift or {})}
        self.failed, self.raising, self.short, self.nan = failed, raising, short, nan

    def __call__(self, market, provider, start, end):
        name = provider.candidate
        self.calls.append((market, name, (start, end)))
        if name == self.raising:
            raise RuntimeError('provider failed')
        sessions = [s for s in market.sessions if start <= s <= end]
        if name in self.short:
            sessions = sessions[:-1]
        navs = fake_navs(market, sessions, name, self.drift[name])
        if name in self.nan:
            navs[5] = float('nan')
        return SimpleNamespace(daily=[{'session': s, 'nav': v} for s, v in zip(sessions, navs)],
                               decisions=[{}] * 24, invariants={'passed': name not in self.failed})


def loop_utility(market, sessions, navs):
    """U from an explicit loop over the daily excess returns (no dividend on BIL inside the 2014 segment)."""
    bil = market.close['BIL']
    e = [navs[i] / navs[i - 1] - 1 - (bil[sessions[i]] / bil[sessions[i - 1]] - 1) for i in range(1, len(navs))]
    n = len(e)
    mean = sum(e) / n
    var = sum((x - mean) ** 2 for x in e) / (n - 1)
    return 252 * mean - 1.5 * 252 * var


def segment_sessions(market, year=2014):
    first, last = validation_segment(year)
    return [s for s in market.sessions if first <= s <= last]


def test_selection_uses_history_truncated_to_the_selection_date(market):
    fake = FakeSimulate()
    policy = adaptive.Policy(fake, FAKE_PROVIDERS)
    policy('2014-06-30', market.history('2014-06-30'))
    assert [name for _, name, _ in fake.calls] == list(CANDIDATES)
    for received, _, window in fake.calls:
        assert received.sessions[-1] == SEGMENT_2014[1]
        assert received.close.index[-1] == SEGMENT_2014[1]
        assert all(ex <= SEGMENT_2014[1] for _, ex in received.payable)
        assert window == SEGMENT_2014


def test_selection_is_independent_of_the_first_caller(market):
    first, second = adaptive.Policy(FakeSimulate(), FAKE_PROVIDERS), adaptive.Policy(FakeSimulate(), FAKE_PROVIDERS)
    for t in ('2014-06-30', '2013-12-31'):
        first(t, market.history(t))
    for t in ('2013-12-31', '2014-06-30'):
        second(t, market.history(t))
    assert first.selection_log() == second.selection_log()
    assert [e['year'] for e in first.selection_log()] == [2014]


def test_cache_is_per_instance(market):
    fake = FakeSimulate()
    one, two = adaptive.Policy(fake, FAKE_PROVIDERS), adaptive.Policy(fake, FAKE_PROVIDERS)
    one('2013-12-31', market.history('2013-12-31'))
    one('2014-01-31', market.history('2014-01-31'))
    assert len(fake.calls) == len(CANDIDATES)
    two('2014-01-31', market.history('2014-01-31'))
    assert len(fake.calls) == 2 * len(CANDIDATES)


def test_cache_key_includes_the_vintage_manifest(market):
    fake = FakeSimulate()
    policy = adaptive.Policy(fake, FAKE_PROVIDERS)
    policy('2014-01-31', market.history('2014-01-31'))
    other = replace(market, manifest_sha256='0' * 64)
    policy('2014-01-31', other.history('2014-01-31'))
    assert len(fake.calls) == 2 * len(CANDIDATES)


def test_selection_year_outside_range_raises(market):
    fake = FakeSimulate()
    policy = adaptive.Policy(fake, FAKE_PROVIDERS)
    with pytest.raises(ValueError):
        policy('2013-11-29', market.history('2013-11-29'))
    assert fake.calls == [] and policy.selection_log() == []


def test_policy_returns_the_chosen_configurations_decision(market):
    policy = adaptive.Policy(FakeSimulate(drift={'H1_126_4': 0.002}), FAKE_PROVIDERS)
    for t in ('2013-12-31', '2014-03-31'):
        decision = policy(t, market.history(t))
        expected = FAKE_PROVIDERS['H1_126_4'](t, market.history(t))
        assert decision.weights == expected.weights
        assert decision.signals == [{**row, 'selection_year': 2014, 'selected_config': 'H1_126_4'}
                                    for row in expected.signals]
    assert policy.selection_log()[0]['chosen'] == 'H1_126_4'


def test_selection_log_entry_matches_an_independent_computation(market):
    drift = {'H1_252_4': 0.0004, 'H1_126_3': 0.0004}
    policy = adaptive.Policy(FakeSimulate(drift=drift), FAKE_PROVIDERS)
    policy('2014-02-28', market.history('2014-02-28'))
    [entry] = policy.selection_log()
    assert set(entry) == LOG_KEYS
    sessions = segment_sessions(market)
    expected = {name: loop_utility(market, sessions, fake_navs(market, sessions, name, drift.get(name, 0.0)))
                for name in CANDIDATES}
    assert entry['utility'] == pytest.approx(expected, rel=1e-9, abs=1e-12)
    best = max(expected.values())
    close = [name for name in CANDIDATES if expected[name] >= best - 0.001]
    assert entry['year'] == 2014
    assert (entry['selection_date'], entry['segment_start'], entry['segment_end']) == \
        (SEGMENT_2014[1], SEGMENT_2014[0], SEGMENT_2014[1])
    assert entry['decisions'] == 24 and entry['returns'] == len(sessions) - 1
    assert entry['best_utility'] == pytest.approx(best, rel=1e-9)
    assert entry['close_set'] == close and entry['chosen'] == close[0]
    assert entry['fallback'] is False and entry['warning'] is None
    frequency = entry['stability']['frequency']
    assert set(frequency) == set(CANDIDATES) and sum(frequency.values()) == pytest.approx(1.0)
    assert entry['stability']['fallback_replicates'] == 0
    assert all(type(v) is float for v in entry['utility'].values())
    assert type(entry['best_utility']) is float and type(entry['decisions']) is int
    assert type(entry['returns']) is int and type(entry['fallback']) is bool
    assert all(type(v) is float for v in frequency.values())
    assert type(entry['stability']['fallback_replicates']) is int
    canonical_bytes(policy.selection_log())


def test_selection_log_is_a_copy(market):
    policy = adaptive.Policy(FakeSimulate(), FAKE_PROVIDERS)
    policy('2014-01-31', market.history('2014-01-31'))
    log = policy.selection_log()
    log[0]['chosen'] = 'changed'
    log[0]['utility']['H1_252_3'] = 'changed'
    assert policy.selection_log()[0]['chosen'] != 'changed'
    assert policy.selection_log()[0]['utility']['H1_252_3'] != 'changed'


def test_non_finite_utility_falls_back_with_a_warning(market):
    policy = adaptive.Policy(FakeSimulate(drift={'H1_126_3': 0.002}, nan=('H1_252_4',)), FAKE_PROVIDERS)
    decision = policy('2014-01-31', market.history('2014-01-31'))
    [entry] = policy.selection_log()
    assert entry['fallback'] is True and entry['chosen'] == FALLBACK
    assert entry['utility']['H1_252_4'] is None and type(entry['utility']['H1_126_3']) is float
    assert entry['best_utility'] is None and entry['close_set'] == []
    assert isinstance(entry['warning'], str) and 'H1_252_4' in entry['warning']
    # NAV 5 is not finite, so the excess returns at positions 4 and 5 are not finite.
    rows = inference.block_indices(entry['returns'], 63, 1000, 20261007)
    hit = int(np.isin(rows, (4, 5)).any(axis=1).sum())
    assert 0 < hit < 1000 and entry['stability']['fallback_replicates'] == hit
    assert decision.weights == FAKE_PROVIDERS[FALLBACK]('2014-01-31', market.history('2014-01-31')).weights
    canonical_bytes(policy.selection_log())


def test_failed_validation_invariant_stops(market):
    policy = adaptive.Policy(FakeSimulate(failed=('H1_126_3',)), FAKE_PROVIDERS)
    with pytest.raises(ValueError, match='invariant'):
        policy('2014-01-31', market.history('2014-01-31'))
    assert policy.selection_log() == []


def test_provider_exception_propagates(market):
    policy = adaptive.Policy(FakeSimulate(raising='H1_252_4'), FAKE_PROVIDERS)
    with pytest.raises(RuntimeError, match='provider failed'):
        policy('2014-01-31', market.history('2014-01-31'))
    assert policy.selection_log() == []


def test_candidates_must_share_their_sessions(market):
    policy = adaptive.Policy(FakeSimulate(short=('H1_126_4',)), FAKE_PROVIDERS)
    with pytest.raises(ValueError, match='session'):
        policy('2014-01-31', market.history('2014-01-31'))


def test_policy_requires_a_provider_for_every_candidate_and_the_fallback():
    with pytest.raises(ValueError):
        adaptive.Policy(FakeSimulate(), {k: v for k, v in FAKE_PROVIDERS.items() if k != 'H1_126_4'})
    with pytest.raises(ValueError):
        adaptive.Policy(FakeSimulate(), FAKE_PROVIDERS, candidates=('H1_252_4', 'H1_126_3'))
    with pytest.raises(ValueError):
        adaptive.Policy(FakeSimulate(), FAKE_PROVIDERS, candidates=())
    assert adaptive.Policy(FakeSimulate(), FAKE_PROVIDERS, candidates=('H1_252_3',)).candidates == ('H1_252_3',)


def test_single_candidate_policy_uses_its_order(market):
    fake = FakeSimulate()
    policy = adaptive.Policy(fake, FAKE_PROVIDERS, candidates=('H1_252_3',))
    policy('2014-01-31', market.history('2014-01-31'))
    [entry] = policy.selection_log()
    assert [name for _, name, _ in fake.calls] == ['H1_252_3']
    assert set(entry['utility']) == {'H1_252_3'} and entry['chosen'] == 'H1_252_3'
    assert entry['stability']['frequency'] == {'H1_252_3': 1.0}


def test_adaptive_does_not_import_the_engine():
    tree = ast.parse(inspect.getsource(adaptive))
    modules = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
    modules |= {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
    assert not any('engine' in m for m in modules)
    assert not hasattr(adaptive, 'engine')


def from_session(market, first):
    """The market restricted to sessions >= first (frames sliced, so no event before `first` remains)."""
    frames = {t: pd.DataFrame({'open': market.open[t], 'close': market.close[t], 'dividend': market.dividend[t],
                               'split_ratio': market.split_ratio[t], 'payable_date': '', 'payable_basis': ''})
              for t in market.tickers}
    for (t, ex), (pay, basis) in market.payable.items():
        frames[t].loc[ex, ['payable_date', 'payable_basis']] = [pay, basis]
    return market_from_frames({t: f.loc[f.index >= first] for t, f in frames.items()})


def test_selection_requires_five_full_years_of_history(market):
    # Selection year 2014 needs 2009 to 2013; the first XNYS session of 2009 is 2009-01-02.
    boundary = from_session(market, '2009-01-02')
    assert boundary.sessions[0] == '2009-01-02'
    fake = FakeSimulate()
    adaptive.Policy(fake, FAKE_PROVIDERS)('2014-01-31', boundary.history('2014-01-31'))
    assert len(fake.calls) == len(CANDIDATES)
    for first in ('2009-01-05', '2009-06-01'):
        late = from_session(market, first)
        fake = FakeSimulate()
        policy = adaptive.Policy(fake, FAKE_PROVIDERS)
        with pytest.raises(ValueError, match='history'):
            policy('2014-01-31', late.history('2014-01-31'))
        assert fake.calls == [] and policy.selection_log() == []


def test_selection_date_must_be_in_the_history(market):
    frames_market = from_session(market, '2008-01-02')
    sessions = [s for s in frames_market.sessions if s != SEGMENT_2014[1]]
    gap = replace(frames_market, sessions=tuple(sessions),
                  **{k: getattr(frames_market, k).loc[list(sessions)]
                     for k in ('open', 'close', 'dividend', 'split_ratio')})
    fake = FakeSimulate()
    with pytest.raises(ValueError, match='history'):
        adaptive.Policy(fake, FAKE_PROVIDERS)('2014-01-31', gap.history('2014-01-31'))
    assert fake.calls == []
