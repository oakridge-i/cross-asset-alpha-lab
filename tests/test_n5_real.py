"""Real-vintage checks of the N5 code before the freeze (spec 8 items 1-3, 12; D023 item 6, D025 item 16).

Every run is in memory (engine.simulate and engine.result_files with stage 5): nothing is journaled or written. Output
and assertion messages are limited to counts, flags and maximum differences; no assertion compares figures directly,
so a failure cannot print a utility, return, selection, NAV or weight."""
import hashlib
from functools import lru_cache
from pathlib import Path

import numpy as np
import pytest

from alpha_lab import engine
from alpha_lab import market as m
from alpha_lab import provenance
from alpha_lab.adaptive import validation_segment
from alpha_lab.evaluation import REFERENCES
from alpha_lab.metrics import compute_metrics, periods_for
from test_hypotheses_real import N3_FILES

ROOT = Path(__file__).resolve().parents[1]
FULL = ('2008-12-31', '2022-12-30')
WALK_FORWARD = ('2013-12-31', '2022-12-30')
BENCHMARKS = ('B0', 'B1', 'B2', 'B3', 'REF_SPY')
CONFIGURATIONS = ('H1_252_3', 'H1_252_4', 'H1_126_3', 'H1_126_4', 'H2_4of6', 'H2_5of6')
YEARS = tuple(range(2014, 2023))
# Protocol values restated so that the recomputation does not import adaptive, inference or metrics constants.
ORDER = ('H1_252_3', 'H1_252_4', 'H1_126_3', 'H1_126_4')
FALLBACK = 'H1_252_3'
CLOSE = 0.001
ANNUAL = 252.0
PENALTY = 1.5
UTILITY_TOLERANCE = 1e-12
METRICS_TOLERANCE = 1e-9
CASH = 'BIL'
# Periods of a full-window run (metrics section 11): blocks, then the calendar years 2009 to 2022.
PERIODS = (('full', '2009-01-01', '2022-12-31'), ('development', '2009-01-01', '2013-12-31'),
           ('walk_forward', '2014-01-01', '2022-12-31'), ('2014-2016', '2014-01-01', '2016-12-31'),
           ('2017-2019', '2017-01-01', '2019-12-31'), ('2020-2022', '2020-01-01', '2022-12-31')) + tuple(
    (str(y), f'{y}-01-01', f'{y}-12-31') for y in range(2009, 2023))

real_vintage = pytest.mark.skipif(not (ROOT / m.VINTAGE / 'manifest.json').exists(),
                                  reason='derived vintage is not in this checkout')


@lru_cache(maxsize=None)
def _market():
    return m.load_market(ROOT, Path(m.VINTAGE))


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _compare(expected, actual, tolerance):
    """(ok, diff); ok is False when expected, actual or their difference is missing or not finite, or diff > tolerance."""
    if expected is None or actual is None:
        return False, float('inf')
    expected, actual = float(expected), float(actual)
    with np.errstate(invalid='ignore'):
        diff = abs(actual - expected)
    ok = bool(np.isfinite(expected) and np.isfinite(actual) and np.isfinite(diff) and diff <= tolerance)
    return ok, diff


@lru_cache(maxsize=None)
def _run(name):
    """(result, config, files) of a full-window run of a registered benchmark or configuration, in memory, stage 5."""
    market = _market()
    entry = engine.PROVIDERS[name]
    sessions = (FULL[0],) if entry.schedule == 'first_only' else None
    config = engine.RunConfig(*FULL, decision_sessions=sessions)
    try:
        result = engine.simulate(market, entry.function, config)
        files = engine.result_files(result, config, name, market, stage=5)
    except Exception as exc:  # engine messages can carry cash, weight sums or variances
        raise AssertionError(f'{type(exc).__name__} in the in-memory run of {name}') from None
    return result, config, files


@lru_cache(maxsize=None)
def _bil_returns():
    """{session: BIL return}: the theoretical total-return index T_d = T_{d-1} * s_d * (C_d + D_d) / C_{d-1} built
    with NumPy from the vintage's close, dividend and split data (not features.total_return_index), then
    T_d / T_{d-1} - 1. A prefix of the sessions gives the same index, so the values serve truncated histories too."""
    market = _market()
    close = market.close[CASH].to_numpy(dtype=float)
    dividend = market.dividend[CASH].to_numpy(dtype=float)
    split = market.split_ratio[CASH].to_numpy(dtype=float)
    ratio = np.ones_like(close)
    ratio[1:] = split[1:] * (close[1:] + dividend[1:]) / close[:-1]
    index = np.cumprod(ratio)
    if not (np.isfinite(index).all() and (index > 0).all()):
        raise AssertionError('BIL total-return index is not finite and positive')
    returns = index[1:] / index[:-1] - 1.0
    return dict(zip(market.sessions[1:], returns))


def _excess(daily):
    """Sessions after the first daily row and e = NAV_d / NAV_{d-1} - 1 - r_BIL,d."""
    bil = _bil_returns()
    sessions = [d['session'] for d in daily]
    nav = np.array([d['nav'] for d in daily], dtype=float)
    e = nav[1:] / nav[:-1] - 1.0 - np.array([bil[s] for s in sessions[1:]], dtype=float)
    return sessions[1:], e


def _utility(e):
    return ANNUAL * np.mean(e) - PENALTY * ANNUAL * np.var(e, ddof=1)


def _choose(utilities):
    """Close-set rule and preference order, restated: with every U finite, the close set holds the candidates with
    U >= best - 0.001 in the preference order and its first member is chosen; otherwise the fallback is chosen."""
    if not all(np.isfinite(utilities[k]) for k in ORDER):
        return FALLBACK, [], None
    best = max(utilities[k] for k in ORDER)
    close = [k for k in ORDER if utilities[k] >= best - CLOSE]
    return close[0], close, best


@real_vintage
def test_n3_regression_with_stage_five(no_network):
    assert sorted(N3_FILES) == sorted(BENCHMARKS)
    assert sum(len(files) for files in N3_FILES.values()) == 45
    mismatched, compared = [], 0
    for name in BENCHMARKS:
        files = _run(name)[2]
        if sorted(files) != sorted(N3_FILES[name]):
            mismatched.append(f'{name}: file set')
            continue
        for file, digest in N3_FILES[name].items():
            compared += 1
            if _sha(files[file]) != digest:
                mismatched.append(f'{name}/{file}')
    print(f'benchmarks {len(BENCHMARKS)}, hashes compared {compared}, mismatches {len(mismatched)}')
    assert compared == 45, f'{compared} of 45 hashes compared'
    assert not mismatched, f'benchmark files differ from N3: {mismatched}'


@real_vintage
def test_shared_files_match_the_n4_replacement_runs(no_network):
    absent = [REFERENCES[n] for n in CONFIGURATIONS if not (ROOT / 'data/runs' / REFERENCES[n]).is_dir()]
    if absent:
        pytest.skip(f'N4 replacement run directories absent: data/runs/{", data/runs/".join(absent)}')
    mismatched, compared = [], 0
    for name in CONFIGURATIONS:
        try:  # verify checks the manifest hash and the file inventory; only the `files` hashes are used
            expected = provenance.verify(ROOT / 'data/runs' / REFERENCES[name])['files']
        except Exception as exc:
            raise AssertionError(f'{type(exc).__name__} verifying the N4 run of {name}') from None
        files = _run(name)[2]
        if len(expected) != 9 or set(files) != set(expected) | {'metrics.json'}:
            mismatched.append(f'{name}: file set')
            continue
        for file, digest in expected.items():
            compared += 1
            if _sha(files[file]) != digest:
                mismatched.append(f'{name}/{file}')
    print(f'configurations {len(CONFIGURATIONS)}, shared hashes compared {compared}, mismatches {len(mismatched)}')
    assert compared == 9 * len(CONFIGURATIONS), f'{compared} of {9 * len(CONFIGURATIONS)} hashes compared'
    assert not mismatched, f'shared files differ from N4: {mismatched}'


@lru_cache(maxsize=None)
def _policy_log():
    """Selection log of the P_A1 provider (registry factory) after an in-memory run over the walk-forward window."""
    policy = engine.PROVIDERS['P_A1'].function()
    try:
        result = engine.simulate(_market(), policy, engine.RunConfig(*WALK_FORWARD))
    except Exception as exc:  # policy messages are withheld until the freeze
        raise AssertionError(f'{type(exc).__name__} in the in-memory P_A1 run') from None
    if not result.invariants['passed']:
        raise AssertionError('a run invariant failed in the in-memory P_A1 run')
    return policy.selection_log()


def _independent_selection(year):
    """(chosen, close_set, best, decisions, returns, flags) of `year` from the four H1 providers' validation accounts
    run by engine.simulate on the history truncated to the segment end, with U and the rule restated here."""
    first, last = validation_segment(year)
    history = _market().history(last)
    utilities, counts, sessions_seen, ok = {}, set(), set(), True
    for name in ORDER:
        try:
            result = engine.simulate(history, engine.PROVIDERS[name].function, engine.RunConfig(first, last))
        except Exception as exc:
            raise AssertionError(f'{type(exc).__name__} in the validation account of {name} for {year}') from None
        ok &= result.invariants['passed']
        sessions, e = _excess(result.daily)
        sessions_seen.add(tuple(sessions))
        counts.add((len(result.decisions), len(e)))
        with np.errstate(invalid='ignore', divide='ignore'):
            utilities[name] = float(_utility(e))
    chosen, close, best = _choose(utilities)
    consistent = ok and len(counts) == 1 and len(sessions_seen) == 1
    decisions, returns = counts.pop() if len(counts) == 1 else (None, None)
    return chosen, close, best, decisions, returns, consistent


@real_vintage
def test_policy_selection_is_recomputed_independently(no_network):
    log = {e['year']: e for e in _policy_log()}
    assert sorted(log) == list(YEARS), f'{len(log)} selection years logged'
    agree, max_diff = 0, 0.0
    for year in YEARS:
        entry = log[year]
        chosen, close, best, decisions, returns, consistent = _independent_selection(year)
        first, last = validation_segment(year)
        same = (consistent and entry['chosen'] == chosen and entry['close_set'] == close
                and entry['fallback'] is (best is None) and entry['segment_start'] == first
                and entry['segment_end'] == last and entry['decisions'] == decisions and entry['returns'] == returns)
        if best is None or entry['best_utility'] is None:
            same &= best is None and entry['best_utility'] is None
        else:
            within, diff = _compare(best, entry['best_utility'], UTILITY_TOLERANCE)
            if np.isfinite(diff):
                max_diff = max(max_diff, diff)
            same &= within
        agree += bool(same)
    print(f'selection years {len(YEARS)}, years that agree {agree}, max finite utility difference {max_diff:.3e}')
    assert agree == len(YEARS), f'{agree} of {len(YEARS)} years agree'


@real_vintage
def test_metrics_match_an_independent_computation(no_network):
    names = [p[0] for p in PERIODS]
    max_diff, compared, failures, period_sets = 0.0, 0, 0, 0
    for name in CONFIGURATIONS:
        result, config, _ = _run(name)
        computed = compute_metrics(_market(), result, periods_for(config))['periods']
        if sorted(computed) != sorted(names):
            period_sets += 1
            continue
        sessions, e = _excess(result.daily)
        nav = np.array([d['nav'] for d in result.daily], dtype=float)
        for period, first, last in PERIODS:
            rows = np.array([i + 1 for i, s in enumerate(sessions) if first <= s <= last])
            growth = nav[rows[-1]] / nav[rows[0] - 1]
            expected = {'total_return': growth - 1.0, 'utility': _utility(e[rows - 1])}
            for key, value in expected.items():
                within, diff = _compare(value, computed[period][key], METRICS_TOLERANCE)
                failures += not within
                if np.isfinite(diff):
                    max_diff = max(max_diff, diff)
                compared += 1
    print(f'configurations {len(CONFIGURATIONS)}, values compared {compared}, failures {failures}, '
          f'period-set mismatches {period_sets}, max finite abs difference {max_diff:.3e}')
    assert period_sets == 0, f'{period_sets} configurations with a different period set'
    assert compared == 2 * len(PERIODS) * len(CONFIGURATIONS), f'{compared} values compared'
    assert failures == 0, f'{failures} values missing, not finite or beyond 1e-9'


def test_comparison_treats_non_finite_values_as_failures():
    assert _compare(1.0, 1.0 + 1e-12, 1e-9) == (True, pytest.approx(1e-12, abs=1e-15))
    assert not _compare(1.0, 1.1, 1e-9)[0]
    assert not _compare(float('nan'), 1.0, 1e-9)[0]
    assert not _compare(1.0, float('nan'), 1e-9)[0]
    assert not _compare(float('nan'), float('nan'), 1e-9)[0]
    assert not _compare(float('inf'), float('inf'), 1e-9)[0]
    assert not _compare(1.0, float('-inf'), 1e-9)[0]
    assert not _compare(None, 1.0, 1e-9)[0] and not _compare(1.0, None, 1e-9)[0]
