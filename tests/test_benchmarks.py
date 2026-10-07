from pathlib import Path

import pytest
from n3_fixtures import benchmark_frames

from alpha_lab import benchmarks, engine
from alpha_lab import market as m
from alpha_lab.features import CASH, RISKY, covariance, sigma, total_return_index
from alpha_lab.market import market_from_frames
from alpha_lab.portfolio import common_risk, inverse_vol

ROOT = Path(__file__).resolve().parents[1]
T = '2008-12-31'
PROVIDERS = (benchmarks.b0, benchmarks.b1, benchmarks.b2, benchmarks.b3, benchmarks.ref_spy)


def _history(**kw):
    return market_from_frames(benchmark_frames(**kw)).history(T)


def _selection(h):
    idx = total_return_index(h)
    n = benchmarks.TREND_SESSIONS + 1
    return {i for i in RISKY
            if (idx[i].iloc[-1] / idx[i].iloc[-n]) / (idx[CASH].iloc[-1] / idx[CASH].iloc[-n]) - 1 > 0}


def test_providers_require_warmup():
    market = market_from_frames(benchmark_frames(start='2008-01-02'))
    short = market.history('2008-12-30')
    for provider in PROVIDERS:
        with pytest.raises(ValueError):
            provider('2008-12-30', short)
    enough = market.history('2008-12-31')
    for provider in PROVIDERS:
        assert set(provider('2008-12-31', enough)) == {*RISKY, CASH}


def test_b0_and_ref_spy():
    h = _history()
    assert benchmarks.b0(T, h) == {**{t: 0.0 for t in RISKY}, CASH: 1.0}
    assert benchmarks.ref_spy(T, h) == {**{t: 0.0 for t in RISKY}, CASH: 0.0, 'SPY': 1.0}


def test_b1_equals_common_risk_of_equal_q():
    h = _history()
    assert benchmarks.b1(T, h) == common_risk({i: 1 / 9 for i in RISKY}, covariance(h))


def test_b2_equals_common_risk_of_inverse_vol():
    h = _history()
    assert benchmarks.b2(T, h) == common_risk(inverse_vol(sigma(h), RISKY, 9), covariance(h))


def test_b3_selection_uses_trend_vs_bil():
    drift = {t: (0.003 if k % 2 else -0.003) for k, t in enumerate(RISKY)}
    h = _history(drift=drift)
    chosen = _selection(h)
    assert 0 < len(chosen) < 9
    expected = common_risk(inverse_vol(sigma(h), chosen, 9), covariance(h))
    assert benchmarks.b3(T, h) == expected


def test_b3_empty_selection_is_all_bil():
    h = _history(drift={t: -0.003 for t in RISKY})
    assert _selection(h) == set()
    assert benchmarks.b3(T, h) == {**{t: 0.0 for t in RISKY}, CASH: 1.0}


def test_b3_full_selection_equals_b2():
    h = _history(drift={t: 0.003 for t in RISKY})
    assert _selection(h) == set(RISKY)
    assert benchmarks.b3(T, h) == benchmarks.b2(T, h)


def test_weights_pass_engine_check():
    market = market_from_frames(benchmark_frames())
    for provider in PROVIDERS:
        w = engine.provider_weights(provider, market, T)
        assert all(type(v) is float for v in w.values())


@pytest.mark.skipif(not (ROOT / m.VINTAGE / 'manifest.json').exists(), reason='derived vintage is not in this checkout')
def test_real_vintage_providers_pass_engine_check(no_network):
    market = m.load_market(ROOT, Path(m.VINTAGE))
    names = [n for n, p in engine.PROVIDERS.items() if p.kind == 'benchmark']
    assert names == ['B0', 'B1', 'B2', 'B3', 'REF_SPY']
    for name in names:
        for session in ('2008-12-31', '2022-11-30'):
            w = engine.provider_weights(engine.PROVIDERS[name].function, market, session)
            assert set(w) == set(market.tickers)
