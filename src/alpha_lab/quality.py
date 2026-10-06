"""Raw chart validation and data quality diagnostics."""
import json
import numpy as np
import pandas as pd
from .normalize import calendar


def parse_chart(body, ticker):
    try:
        chart = json.loads(body)['chart']
        if chart.get('error') or len(chart['result']) != 1:
            raise ValueError('source error/result shape')
        r = chart['result'][0]
        meta = r['meta']
        if (meta['symbol'] != ticker or meta['currency'] != 'USD'
                or meta['exchangeTimezoneName'] != 'America/New_York'):
            raise ValueError('unexpected symbol/currency/timezone')
        idx = pd.to_datetime(r['timestamp'], unit='s', utc=True).tz_convert('America/New_York').tz_localize(None).normalize()
        if len(idx) == 0 or idx.has_duplicates or not idx.is_monotonic_increasing:
            raise ValueError('empty/duplicate/unordered chart')
        quote = r['indicators']['quote'][0]
        arrays = [quote[k] for k in ['open','high','low','close','volume']]
        arrays.append(r['indicators']['adjclose'][0]['adjclose'])
        if any(len(values) != len(idx) for values in arrays):
            raise ValueError('chart array length mismatch')
        f = pd.DataFrame({k.title():quote[k] for k in ['open','high','low','close','volume']}, index=idx)
        f['Adj Close'] = r['indicators']['adjclose'][0]['adjclose']
        for kind, column in [('dividends','Dividends'),('splits','Stock Splits'),('capitalGains','Capital Gains')]:
            f[column] = 0.
            seen = set()
            for event in r.get('events', {}).get(kind, {}).values():
                d = pd.to_datetime(event['date'], unit='s', utc=True).tz_convert('America/New_York').tz_localize(None).normalize()
                if d not in f.index or d in seen:
                    raise ValueError('orphan or duplicate corporate action')
                seen.add(d)
                if kind == 'splits':
                    amount = float(event['numerator']) / float(event['denominator'])
                    if not np.isfinite(amount) or amount <= 0:
                        raise ValueError('invalid split ratio')
                else:
                    amount = float(event['amount'])
                f.loc[d, column] = amount
        return f
    except (KeyError, TypeError, IndexError, ZeroDivisionError) as exc:
        raise ValueError(f'malformed chart: {exc}') from exc


def assess(frames, start, end, *, adjustment_tolerance=0.00005):
    expected = set(calendar(start, end).sessions.strftime('%Y-%m-%d'))
    assets, defects = {}, []
    for ticker, f in frames.items():
        view = f.loc[start:end]
        missing = sorted(expected - set(view.index))
        unexpected = sorted(set(view.index) - expected)
        ratio = view.source_adj_close / view.source_close
        # Yahoo's backwards dividend factor differs from ex-date cash reinvestment.
        residual = ratio / ratio.shift(1) * (1 - view.source_dividend / view.source_close.shift(1)) - 1
        breaks = residual.abs() > adjustment_tolerance
        largest = residual.abs().nlargest(10).index
        result = dict(rows=len(view), full_source_rows=len(f), first_session=f.index[0], last_session=f.index[-1],
                      missing_sessions=missing, unexpected_sessions=unexpected,
                      dividend_events=int((view.dividend > 0).sum()),
                      split_events=int((view.split_ratio != 1).sum()),
                      adjustment_breaks=int(breaks.sum()),
                      max_adjustment_residual=float(residual.abs().max()) if residual.notna().any() else None,
                      largest_adjustment_residuals=[{'session':d,'residual':float(residual.loc[d])} for d in largest],
                      dividend_counts_by_year={str(y):int(n) for y,n in view.groupby(view.index.str[:4]).dividend.apply(lambda x:(x>0).sum()).items()},
                      actual_payables=int((view.payable_basis=='actual').sum()))
        assets[ticker] = result
        if missing or unexpected or breaks.any():
            defects.append(ticker)
    return dict(schema_version=1, common_start=start, cutoff=end, expected_sessions=len(expected),
                technical_pass=bool(frames) and not defects, assets=assets, defective_assets=defects,
                adjustment_factor_tolerance=adjustment_tolerance,
                data_ready_for_n2=False,
                warnings=['External action-basis and distribution-completeness gates required.',
                          'Adj Close reconciliation is same-provider evidence, not independent certification.'])
