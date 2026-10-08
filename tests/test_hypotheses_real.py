"""Real-vintage checks of the H1/H2 providers and the N3 benchmark regression (spec 5.5, 6.4, 11).

Output is limited by spec 6.4: sessions, tickers, flags, counts and maximum differences only."""
import hashlib
import math
from functools import lru_cache
from pathlib import Path

import numpy as np
import pytest

from alpha_lab import engine
from alpha_lab import market as m

ROOT = Path(__file__).resolve().parents[1]
START = '2008-12-31'
END = '2022-12-30'
LAST_DECISION = '2022-11-30'
N_DECISIONS = 168
TOLERANCE = 1e-12

real_vintage = pytest.mark.skipif(not (ROOT / m.VINTAGE / 'manifest.json').exists(),
                                  reason='derived vintage is not in this checkout')

# SHA-256 of the files of the five N3 runs (manifest `files`), copied once from data/runs/<id>/manifest.json:
# B0 20261007T180004-12aae80084, B1 20261007T180018-b6c98bd0aa, B2 20261007T180026-dffe07154c,
# B3 20261007T180033-bba99392df, REF_SPY 20261007T180039-be7dd8f43a.
N3_FILES = {
    'B0': {
        'config.json': '73e902568fa59523ea19715daa1f0c6860db28eb6de55e3b427e51caf4e15be4',
        'daily.csv': 'db5c7f8375821d876016b4d426ddb546733266e20503966dec953a960df3c807',
        'decisions.csv': '7ef0424203069dfcc1a2b2ad6b51282d3f0a484456615f2155bc1830ac62ef65',
        'invariants.json': '57b46caa5e111f82b97a1a5141ceb5b48d7c054bc512ef683b88b66f7d62c6d8',
        'metrics.json': 'd529be642928e0cfcb437b92ad5509496bc2056c0b3d529e960d8e99647b0418',
        'orders.csv': '2022a1dbba6a475f8f96721277c3acaa94f14c4be5b1e1bc69c731e558c8f95e',
        'payouts.csv': 'c1019168f03ea9d7d44ea171858ee97655fb81c5ecde2b9acc3e7cca1013bf72',
        'trades.csv': '02cadfc52a98b3c5b9397dbb90f6bd8a24f79f6efe0ec693e056a16b8fad7bc2',
        'weights.csv': '007f4a4ba21d30e022886acaf243a57fcc2638abcd59b3aed0bfa2ecf9427c2f',
    },
    'B1': {
        'config.json': 'ac786425fb3add2b635b767f7c5d831b895abd7ebd5bbc19748b686a410b46d5',
        'daily.csv': '4f1a06a92379233f3d60be4f9396e363eac3ecd400ab9c24c3a443ac5ef58da5',
        'decisions.csv': '88d4b218d392cb8fa3b0b459acff5331eec1ba988a4a564856f5575f17ae8dd5',
        'invariants.json': '66c283c17d6e7fffb3160df145250c20926a32ad276c20b194719e7e5558d3bd',
        'metrics.json': '127bc891d14acd14a75a9b0826b58a0b2340bf3df40c95db709cd4f0f5bd3e9c',
        'orders.csv': 'f85e8dafd955fe5667e21ce839cd6b3d7247fdb7e5a2e3a0c274902292f3bc5f',
        'payouts.csv': 'b3cf26c54d5a63c30715a036e92ff2aef0449b0b85e5acc7ceda68ca7c87bb87',
        'trades.csv': 'b5ca16e0b72b05eeae0e99cdd5f3a8fcdd53cc06ec272d87fb68c7e5c1a81564',
        'weights.csv': '8c6d587ee5469600dc28e10ceaaba2cc422475830baf044bc0eb9b9571f30669',
    },
    'B2': {
        'config.json': '4d98df3b8c50c1c4752ec933d63646e2ae55431241ae4a24c97799c0ab2e6202',
        'daily.csv': 'de87210d61fff0c61a692f6b1d362c81fca932b85415aa655565f8a449702c0e',
        'decisions.csv': '2a776b24533c550869725bcf892cd76e867a09a26a17945916f2810787adfc46',
        'invariants.json': 'dc14c7fc93bdab75e9fa952d36b4356796b39dc115921839a34b076fe06d9186',
        'metrics.json': 'f4d23035bc26b4d7a46fc680e5a03d42c9bdacf3cd9121568e1e344f4977938a',
        'orders.csv': 'fde37993e6bab679d14cf47f9486907a47ccb36606d48e4aecff00df2fb118e1',
        'payouts.csv': '2082d7e2a726f2fe2de7f839b2cf5a2701705f099bf040f3395c5ebcd4b0e453',
        'trades.csv': '489d81645900244d2b37684e8ae4e8a02b0960a372c0e9f1f94401704a632bf3',
        'weights.csv': '8d462172bf3fa1b0608cacc4b42d36b456621c5324f95fbf7649388a50d9955a',
    },
    'B3': {
        'config.json': '26580da139b493ebb60f2d07d77cd35593c11edb82b11fd9d3f49caa6a1a1160',
        'daily.csv': 'db2b92ccd534a427b5d65cf80908f9fa4e2c299c67b84f456f48e01e7aca6ef9',
        'decisions.csv': '428f098c7303ddec6488fd3e24f65e34d0c4ec52f52c06e7659aaaffba40a6de',
        'invariants.json': '1db43c1dead4a0370b5118b8b31ab1654447f4b664dbc201e1bbd977e3057195',
        'metrics.json': '0dd0d98973e487b8b136030f18106271aad5a0171bd5927ccf28e175d82d53a2',
        'orders.csv': '19350fc153505ce579b163494147716c98c7c600cd38b242c12b1c2014ccaba0',
        'payouts.csv': 'b1110bd15fc5b86b2742f9315c24bcb7fb10da4833ff144c270f0e5b56808b75',
        'trades.csv': '3c163a3f030095ab2452dd7ac83548e7f9de7b2c1ea0c4c8ea1f3d3df2c8f581',
        'weights.csv': '415371beac05ff07f3335f1304920a4a0715208a7a58bf0d7186a4cdd817252e',
    },
    'REF_SPY': {
        'config.json': '306fafe6ffa70a583cb6a2b808819bb280a8964462c25c10c48e747c5435ea4b',
        'daily.csv': '49d66f283a792caf962beb32e63915c2d44162bd1b2ef8d2aa3a26a9b297f84c',
        'decisions.csv': 'c00342609add9f1576fa9e15e6b8d0010ed8690764ad4740f14a7bd821136592',
        'invariants.json': 'ec8b370a09fb6e860794ff3da9a1d0e386eafdc3e5c74042df455da6ef814868',
        'metrics.json': '9d4526990a42764d8902c95b11732c89e250b52711f348ce0e7162bb0f11ce86',
        'orders.csv': 'c4c3315e6db29842aa665dd1d15214d94a50e8a56aa3e2e0423b4a1c56e28dcf',
        'payouts.csv': 'a7b4266105c5ac925bf9ca1aefe93003f61c74963be6c9a4972fbe951187543d',
        'trades.csv': 'f7b8b2e939fca2ba198cccc0f0c245ff3528fdb49447738eec3359918820d6e4',
        'weights.csv': '80382360bb8825ff69730bf223809b98a6d9bdb6afef95f9bbf493252c5f3836',
    },
}

# Protocol constants restated here so that the recomputation does not import features, portfolio or hypotheses.
BIL = 'BIL'
RISKY = ('SPY', 'EFA', 'EEM', 'IEF', 'TLT', 'LQD', 'HYG', 'GLD', 'DBC')
GROUPS = (('SPY', 'EFA', 'EEM'), ('IEF', 'TLT'), ('LQD', 'HYG'), ('GLD', 'DBC'))
ETF_CAP = 0.25
GROUP_CAP = 0.50
VOL_TARGET = 0.10
SKIP = 21
SIGMA_N = 63
COV_N = 126
CONFIGS = {'H1_252_3': ('H1', 252, 3), 'H1_252_4': ('H1', 252, 4), 'H1_126_3': ('H1', 126, 3),
           'H1_126_4': ('H1', 126, 4), 'H2_4of6': ('H2', 252, 3, 4), 'H2_5of6': ('H2', 252, 3, 5)}


@lru_cache(maxsize=None)
def _market():
    return m.load_market(ROOT, Path(m.VINTAGE))


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _decide(name, session, market):
    """engine.provider_decision with the failure text limited to the exception type, the configuration and the
    session: engine messages can carry cash, weight sums or variances (spec 6.4)."""
    try:
        return engine.provider_decision(engine.PROVIDERS[name].function, market, session)
    except Exception as exc:
        raise AssertionError(f'{type(exc).__name__} at {name} {session}') from None


@real_vintage
def test_n3_benchmark_files_unchanged(no_network):
    market = _market()
    assert sorted(N3_FILES) == sorted(n for n, p in engine.PROVIDERS.items() if p.kind == 'benchmark')
    assert sum(len(files) for files in N3_FILES.values()) == 45
    mismatched = []
    for name, expected in N3_FILES.items():
        entry = engine.PROVIDERS[name]
        sessions = (START,) if entry.schedule == 'first_only' else None
        config = engine.RunConfig(START, END, decision_sessions=sessions)
        result = engine.simulate(market, entry.function, config)
        files = engine.result_files(result, config, name, market)
        if sorted(files) != sorted(expected):
            mismatched.append(f'{name}: file set')
            continue
        mismatched += [f'{name}/{file}' for file in sorted(expected) if _sha(files[file]) != expected[file]]
    assert not mismatched, f'benchmark files differ from N3: {mismatched}'


@real_vintage
def test_hypothesis_providers_on_real_vintage(no_network):
    market = _market()
    names = [n for n, p in engine.PROVIDERS.items() if p.kind == 'hypothesis']
    assert names == list(CONFIGS)
    failures = []
    for name in names:
        for session in (START, LAST_DECISION):
            weights, signals = _decide(name, session, market)
            where = f'{name} {session}'
            if set(weights) != set(market.tickers):
                failures.append(f'{where}: keys')
                continue
            failures += [f'{where} {t}: not a finite float >= 0' for t, w in weights.items()
                         if not (type(w) is float and math.isfinite(w) and w >= 0.0)]
            failures += [f'{where} {t}: above the ETF cap' for t in RISKY if weights[t] > ETF_CAP + TOLERANCE]
            failures += [f'{where} {"/".join(g)}: above the group cap' for g in GROUPS
                         if math.fsum(weights[t] for t in g) > GROUP_CAP + TOLERANCE]
            if weights[BIL] != 1.0 - math.fsum(weights[t] for t in RISKY):
                failures.append(f'{where}: BIL is not 1 - fsum(risky)')
            if sorted(r['ticker'] for r in signals) != sorted(RISKY):
                failures.append(f'{where}: signal tickers')
    assert not failures, failures


def _total_return_index(market):
    close = market.close.to_numpy(dtype=float)
    dividend = market.dividend.to_numpy(dtype=float)
    split = market.split_ratio.to_numpy(dtype=float)
    ratio = np.ones_like(close)
    ratio[1:] = split[1:] * (close[1:] + dividend[1:]) / close[:-1]
    index = np.cumprod(ratio, axis=0)
    if not (np.isfinite(index).all() and (index > 0).all()):
        raise AssertionError('total-return index is not finite and positive')
    return index


def _h1_target(index, columns, pos, lookback, k, where):
    """Weights over RISKY + BIL and the selected set at the session in row `pos`, from rows 0..pos only."""
    t = index[:pos + 1]
    risky = [columns[i] for i in RISKY]
    cash = columns[BIL]
    returns = t[1:] / t[:-1] - 1.0
    vol = np.sqrt(252.0) * np.std(returns[-SIGMA_N:][:, risky], axis=0, ddof=1)
    if not (np.isfinite(vol).all() and (vol > 0).all()):
        raise AssertionError(f'sigma is zero or not finite at row {pos}')
    excess = returns[-COV_N:][:, risky] - returns[-COV_N:][:, [cash]]
    centred = excess - excess.mean(axis=0)
    cov = 252.0 * (centred.T @ centred) / (COV_N - 1)
    near, far = t[-(SKIP + 1)], t[-(lookback + 1)]
    mom = (near[risky] / far[risky]) / (near[cash] / far[cash]) - 1.0
    score = mom / vol
    order = sorted((s, name) for s, name in zip(-score, RISKY) if s < 0.0)
    selected = [name for _, name in order[:k]]
    q = np.zeros(len(RISKY))
    if selected:
        chosen = [RISKY.index(name) for name in selected]
        inv = 1.0 / vol[chosen]
        q[chosen] = len(selected) / k * inv / inv.sum()
    v = np.minimum(q, ETF_CAP)
    for group in GROUPS:
        members = [RISKY.index(name) for name in group]
        total = v[members].sum()
        if total > GROUP_CAP:
            v[members] = v[members] * GROUP_CAP / total
    variance = float(v @ cov @ v)
    if variance < -1e-12:
        raise AssertionError(f'negative portfolio variance at row {pos}')
    port = math.sqrt(max(variance, 0.0))
    scale = 1.0 if port == 0.0 else min(1.0, VOL_TARGET / port)
    weights = dict(zip(RISKY, scale * v))
    weights[BIL] = _remainder(weights, where)
    return weights, set(selected)


def _remainder(weights, where):
    """BIL takes 1 minus the risky weights; a remainder in [-1e-12, 0) is set to 0, as in the provider."""
    cash = 1.0 - math.fsum(weights.values())
    if cash < 0.0:
        if cash < -TOLERANCE:
            raise AssertionError(f'risky weights exceed 100% at {where}')
        cash = 0.0
    return cash


def _positive_months(index, sessions, columns, pos):
    """Count of the latest six completed months with excess return over BIL > 0, per risky ticker."""
    last = {}
    for row, session in enumerate(sessions[:pos + 1]):
        last[session[:7]] = row
    months = sorted(last)[-7:]
    assert len(months) == 7
    numbers = [12 * int(x[:4]) + int(x[5:]) for x in months]
    assert all(b - a == 1 for a, b in zip(numbers, numbers[1:]))
    assert last[months[-1]] == pos
    levels = index[[last[x] for x in months]]
    growth = levels[1:] / levels[:-1]
    excess = growth[:, [columns[i] for i in RISKY]] / growth[:, [columns[BIL]]] - 1.0
    return dict(zip(RISKY, (excess > 0.0).sum(axis=0)))


def _decision_sessions(sessions):
    """Last session of each calendar month from START, excluding the month whose execution would be after END."""
    last = {}
    for session in sessions:
        if START <= session <= END:
            last[session[:7]] = session
    return [s for month, s in sorted(last.items()) if month != END[:7]]


@real_vintage
def test_independent_recomputation_of_targets(no_network):
    market = _market()
    sessions = list(market.sessions)
    decisions = _decision_sessions(sessions)
    assert len(decisions) == N_DECISIONS and decisions[0] == START and decisions[-1] == LAST_DECISION
    assert decisions == engine.month_end_sessions(market, START, END, 1)
    columns = {t: i for i, t in enumerate(market.close.columns)}
    index = _total_return_index(market)
    max_diff = 0.0
    compared = selection_mismatches = filter_mismatches = filter_rows = 0
    for t in decisions:
        pos = sessions.index(t)
        parents = {}
        for lookback, k in {(c[1], c[2]) for c in CONFIGS.values()}:
            parents[(lookback, k)] = _h1_target(index, columns, pos, lookback, k, f'H1_{lookback}_{k} {t}')
        positive = _positive_months(index, sessions, columns, pos)
        for name, spec in CONFIGS.items():
            expected, chosen = parents[(spec[1], spec[2])]
            if spec[0] == 'H2':
                chosen = {i for i in chosen if positive[i] >= spec[3]}
                expected = {i: (expected[i] if positive[i] >= spec[3] else 0.0) for i in RISKY}
                expected[BIL] = _remainder({i: expected[i] for i in RISKY}, f'{name} {t}')
            weights, signals = _decide(name, t, market)
            got = {r['ticker'] for r in signals if r['selected'] and (spec[0] == 'H1' or r['filter_pass'])}
            selection_mismatches += got != chosen
            if spec[0] == 'H2':
                assert [r['ticker'] for r in signals] == sorted(RISKY)
                filter_rows += len(signals)
                filter_mismatches += sum(r['filter_pass'] is not bool(positive[r['ticker']] >= spec[3])
                                         for r in signals)
            max_diff = max(max_diff, max(abs(weights[i] - expected[i]) for i in (*RISKY, BIL)))
            compared += 1
    print(f'decisions {len(decisions)}, configurations {len(CONFIGS)}, compared {compared}, '
          f'selection mismatches {selection_mismatches}, filter_pass rows {filter_rows}, '
          f'filter_pass mismatches {filter_mismatches}, max abs weight difference {max_diff:.3e}')
    assert compared == N_DECISIONS * len(CONFIGS)
    assert selection_mismatches == 0, f'{selection_mismatches} selection mismatches'
    assert filter_rows == 9 * N_DECISIONS * sum(spec[0] == 'H2' for spec in CONFIGS.values())
    assert filter_mismatches == 0, f'{filter_mismatches} filter_pass mismatches'
    assert max_diff <= TOLERANCE, f'max abs weight difference {max_diff:.3e}'
