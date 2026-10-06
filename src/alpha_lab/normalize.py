"""Explicit share units and modeled historical availability."""
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo
import numpy as np
import pandas as pd
import exchange_calendars as xcals

NY = ZoneInfo('America/New_York')
REQUIRED = ['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume', 'Dividends', 'Stock Splits']


def calendar(start, end):
    return xcals.get_calendar('XNYS', start=str(start), end=str(end))


def normalize(frame, ticker, retrieved_at, source_hash, payable=None, *, pay_delay_days=10):
    if frame.empty or not set(REQUIRED).issubset(frame.columns):
        raise ValueError('empty history or missing required columns')
    if not isinstance(pay_delay_days, int) or pay_delay_days < 0:
        raise ValueError('pay delay must be nonnegative integer')
    f = frame.copy()
    idx = pd.DatetimeIndex(f.index)
    if idx.tz is not None:
        idx = idx.tz_convert(NY).tz_localize(None)
    f.index = idx.normalize()
    if f.index.hasnans or f.index.has_duplicates or not f.index.is_monotonic_increasing:
        raise ValueError('invalid, duplicate or unordered sessions')
    f['Capital Gains'] = f.get('Capital Gains', 0.)
    numeric = REQUIRED + ['Capital Gains']
    if not np.isfinite(f[numeric].to_numpy(dtype=float)).all():
        raise ValueError('non-finite observations')
    if (f[['Open','High','Low','Close','Adj Close']] <= 0).any().any():
        raise ValueError('non-positive price')
    if (f[['Volume','Dividends','Stock Splits','Capital Gains']] < 0).any().any():
        raise ValueError('negative volume/action')
    if ((f.Low > f[['Open','Close']].min(axis=1)) | (f.High < f[['Open','Close']].max(axis=1))).any():
        raise ValueError('OHLC inequality')
    payable = payable or {}
    bound = f.index[-1].date() + timedelta(days=pay_delay_days + 370)
    for value in payable.values():
        bound = max(bound, date.fromisoformat(value['date']) + timedelta(days=15))
    cal = calendar(f.index[0].date(), bound)
    expected = cal.sessions_in_range(f.index[0], f.index[-1])
    if list(expected) != list(f.index):
        raise ValueError('missing or non-session bars')
    ratios = f['Stock Splits'].replace(0, 1).astype(float)
    # Strictly subsequent ratios: split day has already switched to new shares.
    factor = ratios.iloc[::-1].cumprod().iloc[::-1] / ratios
    out = pd.DataFrame(index=f.index.strftime('%Y-%m-%d'))
    out.index.name = 'session'
    for name in ['Open', 'High', 'Low', 'Close']:
        out[name.lower()] = (f[name] * factor).to_numpy()
    out['source_close'] = f.Close.to_numpy()
    out['source_adj_close'] = f['Adj Close'].to_numpy()
    out['source_volume'] = f.Volume.to_numpy()
    out['source_dividend'] = (f.Dividends + f['Capital Gains']).to_numpy()
    out['dividend'] = ((f.Dividends + f['Capital Gains']) * factor).to_numpy()
    out['split_ratio'] = ratios.to_numpy()
    out['future_split_factor'] = factor.to_numpy()
    growth = out.split_ratio * (out.close + out.dividend) / out.close.shift(1)
    growth.iloc[0] = 1.
    out['total_return_index'] = growth.cumprod()
    out['available_at'] = [datetime.combine(date.fromisoformat(d), time(18), NY).isoformat() for d in out.index]
    out['payable_date'] = ''
    out['payable_basis'] = ''
    out['payable_source'] = ''
    for d in out.index[out.dividend > 0]:
        event = payable.get(d)
        if event:
            when = date.fromisoformat(event['date'])
            if not event.get('source') or when < date.fromisoformat(d):
                raise ValueError('invalid actual payable evidence')
            basis, source = 'actual', event['source']
        else:
            when = date.fromisoformat(d) + timedelta(days=pay_delay_days)
            basis, source = f'proxy_ex_plus_{pay_delay_days}_calendar_days', 'RESEARCH_PROTOCOL_v1.0'
        out.loc[d, 'payable_date'] = cal.date_to_session(str(when), direction='next').date().isoformat()
        out.loc[d, 'payable_basis'] = basis
        out.loc[d, 'payable_source'] = source
    out['ticker'] = ticker
    out['currency'] = 'USD'
    out['timezone'] = 'America/New_York'
    out['availability_basis'] = 'historical_model_assumption'
    out['retrieved_at'] = retrieved_at
    out['source'] = 'Yahoo chart via yfinance'
    out['source_sha256'] = source_hash
    out['adjustment_basis'] = 'as_traded_from_split_adjusted_provisional'
    out['volume_basis'] = 'source_unconfirmed_not_used'
    return out
