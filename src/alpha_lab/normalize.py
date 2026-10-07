"""Explicit share units and modeled historical availability."""
from datetime import date, datetime, time, timedelta
import math
from zoneinfo import ZoneInfo
import numpy as np
import pandas as pd
import exchange_calendars as xcals

NY = ZoneInfo('America/New_York')
# Half of the 0.001 USD rounding step of Yahoo dividends. Yahoo rounds either in as-traded units (BIL) or
# in split-adjusted units (EEM), so the as-traded bound is TOLERANCE * max(1, future_split_factor).
# 1e-12 absorbs binary float error. Shared by reconciliation (matched/mismatch) and correction validation.
TOLERANCE = 0.0005
ACTIONS = ('add', 'replace', 'remove')
REQUIRED = ['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume', 'Dividends', 'Stock Splits']


def calendar(start, end):
    return xcals.get_calendar('XNYS', start=str(start), end=str(end))


def match_tolerance(split_factor):
    return TOLERANCE * max(1., split_factor)


def finite_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def check_correction(ticker, ex_date, correction, actual, split_factor):
    """Validate one correction regardless of its origin against the as-traded Yahoo amount `actual`."""
    where = f'{ticker}/{ex_date}'
    if not isinstance(correction, dict) or correction.get('action') not in ACTIONS:
        raise ValueError(f'correction action must be one of {", ".join(ACTIONS)}: {where}')
    action, issuer, source = correction['action'], correction.get('issuer_amount'), correction.get('source')
    if not isinstance(source, str) or not source.strip():
        raise ValueError(f'correction has no issuer source reference: {where}')
    if not finite_number(issuer) or issuer < 0:
        raise ValueError(f'correction issuer_amount must be a finite nonnegative number: {where}')
    if action == 'remove' and issuer != 0:
        raise ValueError(f'remove correction requires issuer_amount 0: {where}')
    if action != 'remove' and issuer == 0:
        raise ValueError(f'zero issuer_amount is only valid for a remove correction: {where}')
    if action == 'add':
        if abs(actual) > 1e-9:
            raise ValueError(f'correction add conflicts with an existing Yahoo event: {where}')
        return
    if abs(actual) <= 1e-9:
        raise ValueError(f'{action} correction targets a session with no Yahoo event: {where}')
    stated = correction.get('yahoo_amount')
    if not finite_number(stated) or abs(actual - stated) > 1e-9:
        raise ValueError(f'correction yahoo_amount disagrees with the source event: {where}')
    # Same predicate as reconciliation's 'matched': such an event is already confirmed, never corrected.
    if action == 'replace' and abs(round(stated - issuer, 10)) <= match_tolerance(split_factor) + 1e-12:
        raise ValueError(f'replace correction is within tolerance of the source amount (matched event): {where}')


def normalize(frame, ticker, retrieved_at, source_hash, payable=None, *, pay_delay_days=10, corrections=None):
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
    if ((f.Dividends > 0) & (f['Capital Gains'] > 0)).any():
        raise ValueError('dividend and capital gain on one date: basis not evidenced')
    if ((f.Low > f[['Open','Close']].min(axis=1)) | (f.High < f[['Open','Close']].max(axis=1))).any():
        raise ValueError('OHLC inequality')
    payable = dict(payable or {})
    # An issuer payable date carried by an add/replace correction is actual evidence even when no separate
    # payable file is passed; a payable file stating another date for the same event is a conflict.
    for ex_date, correction in (corrections or {}).items():
        if not isinstance(correction, dict) or correction.get('action') not in ('add', 'replace'):
            continue
        if when := correction.get('payable_date'):
            if ex_date in payable and payable[ex_date].get('date') != when:
                raise ValueError(f'conflicting actual payable dates: {ticker}/{ex_date}')
            payable.setdefault(ex_date, {'date': when, 'source': correction.get('source')})
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
    out['dividend_basis'] = 'source'
    out['dividend_correction_source'] = ''
    # Explicit, per-event issuer corrections, applied before total-return growth is computed so TR changes
    # only from the corrected session onward. A correction never silently repairs a matched event: it must
    # agree with the Yahoo-derived (as-traded) amount already on that session, or be rejected.
    for ex_date, correction in (corrections or {}).items():
        if ex_date not in out.index:
            raise ValueError(f'correction ex-date is not a session: {ticker}/{ex_date}')
        check_correction(ticker, ex_date, correction, float(out.loc[ex_date, 'dividend']),
                         float(out.loc[ex_date, 'future_split_factor']))
        out.loc[ex_date, 'dividend'] = 0. if correction['action'] == 'remove' else float(correction['issuer_amount'])
        out.loc[ex_date, 'dividend_basis'] = 'issuer_correction'
        out.loc[ex_date, 'dividend_correction_source'] = correction['source']
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
