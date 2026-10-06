"""Registered Yahoo acquisition through yfinance with source capture."""
from urllib.parse import urlsplit
import re

from .provenance import canonical_bytes, now


def recording_session(files):
    from requests import Session

    class RecordingSession(Session):
        def get(self, url, **kwargs):
            response = super().get(url, **kwargs)
            path = urlsplit(url).path
            match = re.fullmatch(r'/v8/finance/chart/([A-Z0-9.-]+)', path)
            if match:
                symbol = match[1]
                prefix = f'raw/{symbol}-'
                number = sum(k.startswith(prefix) and k.endswith('.json') for k in files)
                name = f'{prefix}{number}.json'
                files[name] = response.content
                params = kwargs.get('params') or {}
                files[f'requests/{symbol}-{number}.json'] = canonical_bytes({
                    'source': 'https://' + urlsplit(url).netloc + path,
                    'parameters': {k: v for k, v in params.items()
                                   if k in {'period1', 'period2', 'interval', 'events', 'range', 'includePrePost'}},
                    'retrieved_at': now(), 'status_code': response.status_code,
                    'raw_file': name})
            return response

    # Python's TLS stack supports Unicode Windows CA paths; curl's CAfile does not.
    session = RecordingSession()
    session.headers['User-Agent'] = 'Mozilla/5.0'
    return session


def download(tickers, start, end, files=None, *, ticker_factory=None, session=None):
    """files is caller-owned so partial evidence survives a failing ticker."""
    if files is None:
        files = {}
    if ticker_factory is None:
        import yfinance as yf
        ticker_factory = yf.Ticker
        yf.config.debug.hide_exceptions = False
    owned = session is None
    session = session if session is not None else recording_session(files)
    try:
        for ticker in tickers:
            if not re.fullmatch('[A-Z0-9.-]+', ticker):
                raise ValueError('invalid ticker')
            frame = ticker_factory(ticker, session=session).history(
                start=start, end=end, interval='1d', prepost=False, actions=True,
                auto_adjust=False, back_adjust=False, repair=False, keepna=True,
                rounding=False, timeout=30)
            if frame.empty:
                raise ValueError(f'empty history: {ticker}')
            if not any(k.startswith(f'raw/{ticker}-') for k in files):
                raise ValueError(f'missing raw body: {ticker}')
            files[f'adapter/{ticker}.csv'] = frame.to_csv(index_label='Date', lineterminator='\n').encode()
    finally:
        if owned:
            session.close()
    return files
