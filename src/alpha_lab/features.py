"""Causal features: theoretical total-return index, sigma, excess-return covariance, momentum and month-end levels
(protocol lines 40, 52-60, 93-107)."""
from datetime import date
import numpy as np
from alpha_lab.normalize import calendar

WARMUP_CLOSES = 253
SIGMA_RETURNS = 63
COV_RETURNS = 126
ANNUAL = 252
RISKY = ('SPY', 'EFA', 'EEM', 'IEF', 'TLT', 'LQD', 'HYG', 'GLD', 'DBC')
CASH = 'BIL'
MOMENTUM_SKIP = 21
MONTH_LEVELS = 7
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


def momentum(index, lookback, skip=MOMENTUM_SKIP):
    """M_i = (T_i[t-skip] / T_i[t-L]) / (T_BIL[t-skip] / T_BIL[t-L]) - 1 per risky ticker; t is the last row.

    The window holds the L - skip returns from T[t-L] = index.iloc[-(L+1)] to T[t-skip] = index.iloc[-(skip+1)]."""
    if not 0 <= skip < lookback:
        raise ValueError(f'momentum needs 0 <= skip < lookback, got skip {skip} and lookback {lookback}')
    if len(index) < lookback + 1:
        raise ValueError(f'momentum needs {lookback + 1} sessions, got {len(index)}')
    growth = index.iloc[-(skip + 1)] / index.iloc[-(lookback + 1)]
    return {ticker: float(growth[ticker] / growth[CASH] - 1) for ticker in RISKY}


def _month_number(month):
    year, number = month.split('-')
    return 12 * int(year) + int(number)


def month_end_levels(market, index, count=MONTH_LEVELS):
    """Index rows at the last session of each of the latest `count` calendar months of the history, ascending.

    Each of these sessions must be the last XNYS session of its month and the months must be consecutive;
    the month of t contributes t, so a t that is not the last XNYS session of its month raises."""
    sessions = tuple(market.sessions)
    if tuple(index.index) != sessions:
        raise ValueError('index rows do not match the market sessions')
    last = {}
    for session in sessions:
        last[session[:7]] = session
    months = sorted(last)[-count:]
    if len(months) < count:
        raise ValueError(f'need {count} calendar months, got {len(months)}')
    numbers = [_month_number(m) for m in months]
    if any(b - a != 1 for a, b in zip(numbers, numbers[1:])):
        raise ValueError(f'month-end months are not consecutive: {months[0]} to {months[-1]}')
    year, number = divmod(numbers[-1], 12)  # first day of the month after the last month
    xnys = calendar(f'{months[0]}-01', date(year, number + 1, 1).isoformat())
    month_end = {}
    for day in xnys.sessions:
        month_end[day.date().isoformat()[:7]] = day.date().isoformat()
    for m in months:
        if last[m] != month_end[m]:
            raise ValueError(f'{last[m]} is not the last XNYS session of {m}')
    return index.loc[[last[m] for m in months]].copy()


def monthly_excess(levels):
    """E_i,j = (T_i,end(j) / T_i,end(j-1)) / (T_BIL,end(j) / T_BIL,end(j-1)) - 1 for consecutive month-end rows,
    oldest first, indexed by end(j), columns RISKY."""
    if len(levels) < 2:
        raise ValueError(f'monthly excess needs at least 2 month-end levels, got {len(levels)}')
    growth = (levels / levels.shift(1)).iloc[1:]
    return growth[list(RISKY)].div(growth[CASH], axis=0) - 1
