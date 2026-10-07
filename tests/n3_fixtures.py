"""Synthetic ten-ticker frames and vintages for N3 tests."""
import numpy as np
import pandas as pd
from alpha_lab.market import PROXY_BASIS, proxy_pay_session
from alpha_lab.normalize import calendar
from alpha_lab.provenance import sha256
from n2_fixtures import write_vintage

RISKY = ('SPY', 'EFA', 'EEM', 'IEF', 'TLT', 'LQD', 'HYG', 'GLD', 'DBC')
SPY_EX, SPY_PAY = '2008-06-20', '2008-06-30'
BIL_EX = '2008-07-01'


def benchmark_frames(start='2007-12-03', end='2009-03-31', seed=20261007, drift=None):
    """Ten tickers (RISKY + BIL) on XNYS sessions; `drift` overrides the daily log drift per ticker."""
    sessions = [d.date().isoformat() for d in calendar('2007-11-01', end).sessions if d.date().isoformat() >= start]
    rng = np.random.default_rng(seed)
    drift = {**{t: 0.0003 for t in RISKY}, 'BIL': 0.00015, **(drift or {})}
    n = len(sessions)
    frames = {}
    for t in (*RISKY, 'BIL'):
        vol = 0.0005 if t == 'BIL' else 0.01
        close = 100. * np.exp(np.cumsum(drift[t] + vol * rng.standard_normal(n)))
        open_ = np.append(close[0], close[:-1] * (1 + 0.001 * rng.standard_normal(n - 1)))
        f = pd.DataFrame({'open': open_, 'close': close, 'dividend': 0., 'split_ratio': 1.,
                          'payable_date': '', 'payable_basis': ''}, index=pd.Index(sessions, name='session'))
        frames[t] = f
    frames['SPY'].loc[SPY_EX, ['dividend', 'payable_date', 'payable_basis']] = [0.5, SPY_PAY, 'actual']
    frames['BIL'].loc[BIL_EX, ['dividend', 'payable_date', 'payable_basis']] = [
        0.1, proxy_pay_session(BIL_EX, 10), PROXY_BASIS]
    return frames


def benchmark_vintage(root, **kwargs):
    """Freeze benchmark_frames under root; returns (snapshot path, manifest sha256)."""
    derived = write_vintage(root, benchmark_frames(**kwargs))
    return derived, sha256((derived / 'manifest.json').read_bytes())
