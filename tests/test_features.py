import numpy as np
import pytest
from alpha_lab import features
from alpha_lab.features import (ANNUAL, CASH, COV_RETURNS, RISKY, SIGMA_RETURNS, WARMUP_CLOSES, check_covariance,
                                covariance, daily_returns, require_warmup, sigma, total_return_index)
from alpha_lab.market import market_from_frames
from n2_fixtures import SESSIONS, frame
from n3_fixtures import benchmark_frames


def full_market(**kwargs):
    return market_from_frames(benchmark_frames(**kwargs))


def test_constants():
    assert (WARMUP_CLOSES, SIGMA_RETURNS, COV_RETURNS, ANNUAL) == (253, 63, 126, 252)
    assert RISKY == ('SPY', 'EFA', 'EEM', 'IEF', 'TLT', 'LQD', 'HYG', 'GLD', 'DBC') and CASH == 'BIL'


def test_total_return_index_split_and_dividend_same_session():
    close = [100., 102., 51.] + [51.] * 7
    dividend = [0., 0., 0.5] + [0.] * 7
    split = [1., 1., 2.] + [1.] * 7
    f = frame(close, dividend=dividend, split=split, payable={SESSIONS[2]: ('2017-12-05', 'actual')})
    T = total_return_index(market_from_frames({'AAA': f}))['AAA']
    assert T.iloc[0] == 1.0
    assert T.iloc[1] == pytest.approx(1.02, rel=1e-15)
    assert T.iloc[2] == pytest.approx(1.02 * 2 * (51 + 0.5) / 102, rel=1e-15)
    r = daily_returns(total_return_index(market_from_frames({'AAA': f})))
    assert len(r) == 9 and r['AAA'].iloc[1] == pytest.approx(2 * 51.5 / 102 - 1, rel=1e-12)


def test_non_positive_index_is_rejected():
    m = market_from_frames({'AAA': frame([100.] * 10)})
    bad = m.close.copy()
    bad.iloc[3] = np.nan
    with pytest.raises(ValueError, match='AAA'):
        total_return_index(type(m)(m.tickers, m.sessions, m.open, bad, m.dividend, m.split_ratio, m.payable,
                                   m.vintage, m.manifest_sha256))


def test_sigma_matches_numpy():
    m = full_market()
    r = daily_returns(total_return_index(m))
    s = sigma(m)
    assert list(s) == list(RISKY)
    for t in RISKY:
        assert s[t] == pytest.approx(np.sqrt(252) * np.std(r[t].to_numpy()[-63:], ddof=1), rel=1e-12)


def test_covariance_matches_numpy():
    m = full_market()
    r = daily_returns(total_return_index(m))
    excess = r[list(RISKY)].sub(r['BIL'], axis=0).to_numpy()
    expected = 252 * np.cov(excess[-126:].T, ddof=1)
    got = covariance(m)
    assert got.shape == (9, 9)
    np.testing.assert_allclose(got, expected, rtol=1e-12, atol=1e-18)


def test_features_use_only_history():
    frames = benchmark_frames()
    m = market_from_frames(frames)
    t = m.sessions[300]
    for f in frames.values():
        f.loc[f.index > t, ['open', 'close']] *= 1.7
    changed = market_from_frames(frames)
    assert sigma(m.history(t)) == sigma(changed.history(t))
    np.testing.assert_array_equal(covariance(m.history(t)), covariance(changed.history(t)))
    assert sigma(m) != sigma(changed)


def test_warmup_boundary():
    m = full_market(start='2008-01-02', end='2008-12-31')
    assert len(m.sessions) == 253
    require_warmup(m)
    short = m.history(m.sessions[251])
    assert len(short.sessions) == 252
    with pytest.raises(ValueError, match='253'):
        require_warmup(short)
    with pytest.raises(ValueError):
        sigma(short)
    with pytest.raises(ValueError):
        covariance(short)


def test_zero_sigma_is_rejected():
    frames = benchmark_frames()
    frames['LQD'].loc[:, ['open', 'close']] = 100.
    with pytest.raises(ValueError, match='LQD'):
        sigma(market_from_frames(frames))


def test_asymmetric_or_non_psd_covariance_is_rejected():
    with pytest.raises(ValueError):
        check_covariance(np.array([[1., 0.1], [0., 1.]]))
    with pytest.raises(ValueError):
        check_covariance(np.array([[1., 2.], [2., 1.]]))
    check_covariance(np.array([[1., 0.], [0., 0.]]))


def test_fixture_series_are_usable_for_variants():
    down = {t: -0.002 for t in RISKY}
    m = full_market(drift=down)
    T = total_return_index(m)
    assert (T.iloc[-1][list(RISKY)] < T.iloc[-253][list(RISKY)]).all()
    assert features.sigma(m)['SPY'] > 0
