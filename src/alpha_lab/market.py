"""Approved derived vintage as a market on a common session calendar, with the payable-date contract."""
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path, PurePosixPath
import numpy as np
import pandas as pd
from alpha_lab.normalize import calendar, iso_date
from alpha_lab.provenance import sha256, verify

VINTAGE = 'data/derived/20261006T172442-80ef993493'
VINTAGE_MANIFEST_SHA256 = 'f89346107cf7da6ca052693d188b8a576a08d42024c86865b0a42a63b1d294f2'
COMMON_START = '2007-05-30'
PROXY_BASIS = 'proxy_ex_plus_10_calendar_days'
ACTUAL_BASIS = 'actual'
RESERVED_START = '2023-01-01'
LAST_OPEN_SESSION = '2022-12-30'
COLUMNS = ['open', 'close', 'dividend', 'split_ratio', 'payable_date', 'payable_basis']
_PROXY_DAYS = 10


@dataclass(frozen=True)
class Market:
    tickers: tuple[str, ...]
    sessions: tuple[str, ...]
    open: pd.DataFrame
    close: pd.DataFrame
    dividend: pd.DataFrame
    split_ratio: pd.DataFrame
    payable: dict[tuple[str, str], tuple[str, str]]  # (ticker, ex_session) -> (pay_session, basis)
    vintage: str
    manifest_sha256: str

    def index(self, session):
        try:
            return self.sessions.index(session)
        except ValueError:
            raise ValueError(f'not a market session: {session}') from None

    def history(self, t):
        """Market restricted to sessions <= t; later payable rows are dropped with their ex-dates."""
        n = self.index(t) + 1
        return Market(self.tickers, self.sessions[:n], self.open.iloc[:n], self.close.iloc[:n],
                      self.dividend.iloc[:n], self.split_ratio.iloc[:n],
                      {k: v for k, v in self.payable.items() if k[1] <= t},
                      self.vintage, self.manifest_sha256)


def proxy_pay_session(ex_session, days, cal=None):
    """First XNYS session on or after ex_session + days calendar days (pay dates may follow the last bar)."""
    target = date.fromisoformat(ex_session) + timedelta(days=days)
    cal = calendar(ex_session, target + timedelta(days=15)) if cal is None else cal
    return cal.date_to_session(target.isoformat(), direction='next').date().isoformat()


def text(value):
    return '' if pd.isna(value) else str(value)


def require(ticker, f, column, ok):
    bad = f.index[~ok(f[column]).to_numpy()]
    if len(bad):
        raise ValueError(f'invalid {column}: {ticker}/{bad[0]}')


def check_payable(ticker, f, cal):
    """Payable contract on every dividend row; returns {(ticker, ex): (pay_session, basis)}."""
    out = {}
    for ex, basis, pay in zip(f.index, f.payable_basis, f.payable_date):
        basis, pay, where = text(basis), text(pay), f'{ticker}/{ex}'
        if basis not in (ACTUAL_BASIS, PROXY_BASIS):
            raise ValueError(f'payable_basis must be {ACTUAL_BASIS} or {PROXY_BASIS}: {where} has {basis!r}')
        if not iso_date(pay) or pay < ex:
            raise ValueError(f'payable_date must be an ISO date not before the ex-date: {where} has {pay!r}')
        if basis == PROXY_BASIS and pay != proxy_pay_session(ex, _PROXY_DAYS, cal):
            raise ValueError(f'proxy payable_date is not ex + {_PROXY_DAYS} calendar days: {where} has {pay}')
        out[(ticker, ex)] = (pay, basis)
    return out


def check_pay_sessions(payable, sessions):
    """Payments not later than the last session must fall on a session of the calendar."""
    common = set(sessions)
    for (t, ex), (pay, _) in payable.items():
        if pay <= sessions[-1] and pay not in common:
            raise ValueError(f'payment on a session outside the common calendar: {t}/{ex} -> {pay}')


def check_events(ticker, f, sessions, start):
    """Dividends and splits on sessions in [start, last session] that are not common sessions."""
    common = set(sessions)
    for s, dividend, split in zip(f.index, f.dividend, f.split_ratio):
        if (start is None or s >= start) and s <= sessions[-1] and s not in common:
            if (np.isfinite(dividend) and dividend > 0) or (np.isfinite(split) and split != 1):
                raise ValueError(f'event on a session outside the common calendar: {ticker}/{s}')


def market_from_frames(frames, vintage='synthetic', manifest_sha256='', start=None):
    """Common calendar = sessions present for every ticker (from `start`); validates the frames."""
    tickers = tuple(sorted(frames))
    for t in tickers:
        if not frames[t].index.is_unique:
            raise ValueError(f'duplicate sessions: {t}')
    sessions = sorted(set.intersection(*(set(frames[t].index) for t in tickers)))
    sessions = tuple(s for s in sessions if start is None or s >= start)
    if not sessions:
        raise ValueError('no common sessions')
    cal = calendar(sessions[0], date.fromisoformat(sessions[-1]) + timedelta(days=_PROXY_DAYS + 15))
    positive = lambda s: np.isfinite(s) & (s > 0)
    nonnegative = lambda s: np.isfinite(s) & (s >= 0)
    payable = {}
    for t in tickers:
        check_events(t, frames[t], sessions, start)
        f = frames[t].loc[list(sessions), COLUMNS]
        require(t, f, 'close', positive)
        require(t, f, 'open', lambda s: s.isna() | positive(s))
        require(t, f, 'dividend', nonnegative)
        require(t, f, 'split_ratio', positive)
        payable |= check_payable(t, f[f.dividend > 0], cal)
    check_pay_sessions(payable, sessions)

    def table(column):
        data = {t: frames[t].loc[list(sessions), column].astype(float).to_numpy() for t in tickers}
        return pd.DataFrame(data, index=pd.Index(sessions, name='session'), columns=list(tickers))

    return Market(tickers, sessions, table('open'), table('close'), table('dividend'), table('split_ratio'),
                  payable, vintage, manifest_sha256)


def load_market(root, derived, expected_sha256=VINTAGE_MANIFEST_SHA256):
    """Verify the derived vintage, check its manifest hash and read normalized/<TICKER>.csv for every ticker."""
    root = Path(root)
    path = root / derived
    manifest = verify(path)
    digest = sha256((path / 'manifest.json').read_bytes())
    if expected_sha256 is not None and digest != expected_sha256:
        raise ValueError(f'unexpected vintage {path.name}: manifest sha256 {digest}')
    names = sorted(n for n in manifest['files'] if n.startswith('normalized/') and n.endswith('.csv'))
    frames = {PurePosixPath(n).stem: pd.read_csv(path / n, index_col='session', usecols=['session', *COLUMNS])
              for n in names}
    try:
        vintage = path.relative_to(root).as_posix()
    except ValueError:
        vintage = path.as_posix()
    return market_from_frames(frames, vintage, digest, COMMON_START)
