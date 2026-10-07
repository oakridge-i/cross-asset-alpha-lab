"""Causal features: theoretical total-return index, sigma and excess-return covariance (protocol lines 40, 52-60)."""
import numpy as np

WARMUP_CLOSES = 253
SIGMA_RETURNS = 63
COV_RETURNS = 126
ANNUAL = 252
RISKY = ('SPY', 'EFA', 'EEM', 'IEF', 'TLT', 'LQD', 'HYG', 'GLD', 'DBC')
CASH = 'BIL'
_TOLERANCE = 1e-12


def total_return_index(market):
    """T per ticker: 1 at the first session, T_d / T_{d-1} = s_d * (C_d + D_d) / C_{d-1}."""
    ratio = market.split_ratio * (market.close + market.dividend) / market.close.shift(1)
    ratio.iloc[0] = 1.0
    index = ratio.cumprod()
    for ticker in index.columns:
        values = index[ticker].to_numpy()
        if not (np.isfinite(values).all() and (values > 0).all()):
            raise ValueError(f'total-return index is not finite and positive: {ticker}')
    return index


def daily_returns(index):
    """r_d = T_d / T_{d-1} - 1; the first row is dropped."""
    return (index / index.shift(1) - 1).iloc[1:]


def require_warmup(market):
    if len(market.sessions) < WARMUP_CLOSES:
        raise ValueError(f'warm-up needs {WARMUP_CLOSES} closes, got {len(market.sessions)}')


def _returns(market, count):
    require_warmup(market)
    r = daily_returns(total_return_index(market))
    if len(r) < count:
        raise ValueError(f'need {count} returns, got {len(r)}')
    return r


def sigma(market):
    """sqrt(252) * sample std (ddof=1) of the latest 63 returns, per risky ticker."""
    r = _returns(market, SIGMA_RETURNS)
    out = {}
    for ticker in RISKY:
        value = float(np.sqrt(ANNUAL) * np.std(r[ticker].to_numpy()[-SIGMA_RETURNS:], ddof=1))
        if not np.isfinite(value) or value <= 0:
            raise ValueError(f'sigma is zero or not finite: {ticker}')
        out[ticker] = value
    return out


def check_covariance(matrix):
    m = np.asarray(matrix, dtype=float)
    if not np.isfinite(m).all():
        raise ValueError('covariance is not finite')
    if np.max(np.abs(m - m.T)) > _TOLERANCE:
        raise ValueError('covariance is not symmetric')
    if np.linalg.eigvalsh(m).min() < -_TOLERANCE:
        raise ValueError('covariance is not positive semidefinite')


def covariance(market):
    """252 * sample covariance (ddof=1) of the latest 126 excess returns over BIL, in RISKY order."""
    r = _returns(market, COV_RETURNS)
    excess = r[list(RISKY)].sub(r[CASH], axis=0).to_numpy()[-COV_RETURNS:]
    matrix = ANNUAL * np.cov(excess.T, ddof=1)
    check_covariance(matrix)
    return matrix
