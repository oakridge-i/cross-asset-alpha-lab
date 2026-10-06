"""N0 source metadata/quality probe. No features, NAV or strategy evaluation.

Standard library only; stdout by default. --output must name a new file.
Payload hashes are evidence of fetched responses, not a saved N1 snapshot.
"""

import argparse
import datetime as dt
import hashlib
import json
import math
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


TICKERS = ['SPY', 'EFA', 'EEM', 'IEF', 'TLT', 'LQD', 'HYG', 'GLD', 'DBC', 'BIL']
START = int(dt.datetime(1990, 1, 1, tzinfo=dt.timezone.utc).timestamp())
END = int(dt.datetime(2026, 10, 6, tzinfo=dt.timezone.utc).timestamp())


def day(timestamp):
    return dt.datetime.fromtimestamp(timestamp, dt.timezone.utc).date().isoformat()


def probe(ticker):
    url = (f'https://query1.finance.yahoo.com/v8/finance/chart/{ticker}'
           f'?period1={START}&period2={END}&interval=1d&events=div%2Csplits%2CcapitalGains')
    item = {'ticker': ticker, 'url': url,
            'checked_at_utc': dt.datetime.now(dt.timezone.utc).isoformat()}
    valid_days = set()
    try:
        request = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(request, timeout=25) as response:
            raw = response.read()
            item['http_status'] = response.status
        item['response_sha256'] = hashlib.sha256(raw).hexdigest()
        chart = json.loads(raw)['chart']
        if chart.get('error'):
            raise ValueError(str(chart['error']))
        data = chart['result'][0]
        timestamps = data.get('timestamp', [])
        meta = data.get('meta', {})
        quotes = data['indicators']['quote'][0]
        invalid = inconsistent = missing_volume = negative_volume = 0
        for i, timestamp in enumerate(timestamps):
            values = [quotes.get(k, [None] * len(timestamps))[i]
                      for k in ('open', 'high', 'low', 'close')]
            if all(v is not None and math.isfinite(v) and v > 0 for v in values):
                op, hi, lo, cl = values
                if lo <= min(op, cl) <= max(op, cl) <= hi:
                    valid_days.add(day(timestamp))
                else:
                    inconsistent += 1
            else:
                invalid += 1
            volume = quotes.get('volume', [None] * len(timestamps))[i]
            if volume is None or not math.isfinite(volume):
                missing_volume += 1
            elif volume < 0:
                negative_volume += 1
        events = data.get('events', {})
        dividends = list(events.get('dividends', {}).values())
        splits = list(events.get('splits', {}).values())
        item.update(
            status='available', currency=meta.get('currency'),
            exchange_timezone=meta.get('exchangeTimezoneName'),
            exchange=meta.get('fullExchangeName'), returned_rows=len(timestamps),
            first_valid_session=min(valid_days) if valid_days else None,
            last_valid_session=max(valid_days) if valid_days else None,
            valid_ohlc_rows=len(valid_days), invalid_ohlc_rows=invalid,
            inconsistent_ohlc_rows=inconsistent, missing_volume_rows=missing_volume,
            negative_volume_rows=negative_volume,
            duplicate_timestamps=len(timestamps) - len(set(timestamps)),
            timestamps_strictly_increasing=all(a < b for a, b in zip(timestamps, timestamps[1:])),
            adjclose_present='adjclose' in data['indicators'],
            dividend_count=len(dividends), split_count=len(splits),
            capital_gain_count=len(events.get('capitalGains', {})),
            dividend_keys=sorted({k for event in dividends for k in event}),
            dividend_count_by_year=dict(sorted(Counter(day(e['date'])[:4] for e in dividends).items())),
            first_dividend_date=min((day(e['date']) for e in dividends), default=None),
            last_dividend_date=max((day(e['date']) for e in dividends), default=None),
            split_events=[{**event, 'session': day(event['date'])} for event in splits],
            pay_dates_in_dividend_events=any('pay' in k.lower() for e in dividends for k in e),
        )
    except Exception as error:
        item.update(status='unavailable', error_type=type(error).__name__, error=str(error))
    return item, valid_days


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.output and args.output.exists():
        parser.error('--output already exists; preserve the previous receipt and choose a new file')
    with ThreadPoolExecutor(max_workers=2) as executor:
        pairs = list(executor.map(probe, TICKERS))
    common = sorted(set.intersection(*(days for _, days in pairs)))
    receipt = {
        'purpose': 'N0 source accessibility/shape probe, not N1 certified snapshot',
        'cutoff_inclusive': '2026-10-05', 'strategy_performance_calculated': False,
        'raw_payloads_saved': False, 'exchange_calendar_validated': False,
        'results': [item for item, _ in pairs],
        'common_valid_observed_sessions': len(common),
        'first_common_valid_observed_session': common[0] if common else None,
        'last_common_valid_observed_session': common[-1] if common else None,
        'observed_returns_available_at_2008_12_31': max(0, len([d for d in common if d <= '2008-12-31']) - 1),
    }
    rendered = json.dumps(receipt, ensure_ascii=False, indent=2) + '\n'
    if args.output:
        with args.output.open('x', encoding='utf-8') as stream:
            stream.write(rendered)
    print(rendered)
    return 0 if all(item['status'] == 'available' for item, _ in pairs) else 1


if __name__ == '__main__':
    raise SystemExit(main())
