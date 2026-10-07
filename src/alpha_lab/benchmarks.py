"""Section 5 benchmark weight providers: B0, B1, B2, B3 and REF_SPY."""
from alpha_lab.features import CASH, RISKY, covariance, require_warmup, sigma, total_return_index
from alpha_lab.portfolio import common_risk, inverse_vol

TREND_SESSIONS = 252


def _single(ticker):
    w = {t: 0.0 for t in (*RISKY, CASH)}
    w[ticker] = 1.0
    return w


def b0(t, history):
    """All cash: BIL = 1."""
    require_warmup(history)
    return _single(CASH)


def b1(t, history):
    """Equal q = 1/9 over the nine risky ETFs, then common risk limits."""
    require_warmup(history)
    return common_risk({i: 1.0 / len(RISKY) for i in RISKY}, covariance(history))


def b2(t, history):
    """Inverse volatility over all nine risky ETFs, then common risk limits."""
    require_warmup(history)
    return common_risk(inverse_vol(sigma(history), RISKY, len(RISKY)), covariance(history))


def b3(t, history):
    """Inverse volatility over risky ETFs whose 252-session total return beats BIL, then common risk limits."""
    require_warmup(history)
    index = total_return_index(history)
    n = TREND_SESSIONS + 1
    cash = index[CASH].iloc[-1] / index[CASH].iloc[-n]
    selected = [i for i in RISKY if (index[i].iloc[-1] / index[i].iloc[-n]) / cash - 1.0 > 0.0]
    return common_risk(inverse_vol(sigma(history), selected, len(RISKY)), covariance(history))


def ref_spy(t, history):
    """SPY = 1 with no caps and no volatility target."""
    require_warmup(history)
    return _single('SPY')
