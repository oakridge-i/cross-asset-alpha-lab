"""Offline reconciliation of Yahoo distributions against frozen issuer evidence."""
from pathlib import Path

from .evidence import parse_ishares_html, parse_ssga_xlsx
from .pipeline import normalized
from .provenance import Run, canonical_bytes, freeze, sha256, verify

# Half of the 0.001 USD rounding step of Yahoo dividends; 1e-12 absorbs binary float error.
TOLERANCE = 0.0005
CLASSES = ['matched', 'amount_mismatch', 'issuer_only', 'yahoo_only', 'outside_issuer_coverage']


def issuer_events(evidence, manifest):
    """{ticker: (source, events)} for parseable sources; refuses snapshots with failed sources."""
    out = {}
    for s in manifest['metadata']['sources']:
        if s['status'] != 'completed':
            raise ValueError(f'failed evidence source: {s["id"]}')
        if s['kind'] == 'document':
            continue
        body = (evidence / s['file']).read_bytes()
        if sha256(body) != s['sha256']:
            raise ValueError(f'evidence hash mismatch: {s["file"]}')
        for ticker in s['tickers']:
            if ticker in out:
                raise ValueError(f'several distribution sources for {ticker}')
            if s['kind'] == 'ssga_xlsx':
                out[ticker] = s, parse_ssga_xlsx(body, ticker)
            elif s['kind'] == 'ishares_html' and len(s['tickers']) == 1:
                out[ticker] = s, parse_ishares_html(body)
            else:
                raise ValueError(f'unsupported evidence source: {s["id"]}')
    return out


def compare(frame, source, events, start, end):
    """Classify ex-date events; materiality sums |yahoo - issuer| / previous as-traded close over compared events."""
    view = frame.loc[start:end]
    yahoo = {d: round(float(a), 10) for d, a in view.dividend[view.dividend > 0].items()}
    first, last = events[0]['ex_date'], events[-1]['ex_date']
    issuer = {e['ex_date']: e for e in events if start <= e['ex_date'] <= end and e['amount'] > 0}
    zero = sum(start <= e['ex_date'] <= end and e['amount'] == 0 for e in events)
    result = {k: [] for k in CLASSES}
    bps = 0.
    for d in sorted(set(yahoo) | set(issuer)):
        y, i = yahoo.get(d), issuer.get(d)
        if i is None and not first <= d <= last:
            result['outside_issuer_coverage'].append({'ex_date': d, 'yahoo_amount': y})
            continue
        before = frame.close[frame.index < d]
        if before.empty:
            raise ValueError(f'no previous close before {d}')
        diff = round((y or 0.) - (i['amount'] if i else 0.), 10)
        row = dict(ex_date=d, yahoo_amount=y, issuer_amount=i and i['amount'], diff=diff,
                   record_date=i and i['record_date'], payable_date=i and i['payable_date'],
                   previous_close=float(before.iloc[-1]), bps=abs(diff) / float(before.iloc[-1]) * 1e4)
        bps += row['bps']
        kind = ('issuer_only' if y is None else 'yahoo_only' if i is None
                else 'matched' if abs(diff) <= TOLERANCE + 1e-12 else 'amount_mismatch')
        result[kind].append(row)
    counts = {'yahoo_events': len(yahoo), 'issuer_events': len(issuer), 'issuer_zero_rows': zero}
    counts |= {k: len(v) for k, v in result.items()}
    confirmed = not any(result[k] for k in CLASSES[1:])
    return dict(status='confirmed' if confirmed else 'unresolved', counts=counts, materiality_bps=bps,
                coverage={'first_ex_date': first, 'last_ex_date': last},
                source={'id': source['id'], 'file': source['file'], 'sha256': source['sha256'], 'kind': source['kind']},
                **result)


def reconcile(root, source_snapshot, evidence_snapshot, parent=None):
    root, source, evidence = Path(root).resolve(), Path(source_snapshot).resolve(), Path(evidence_snapshot).resolve()
    cfg = {'source_snapshot': source.relative_to(root).as_posix(),
           'evidence_snapshot': evidence.relative_to(root).as_posix(), 'tolerance': TOLERANCE}
    with Run(root, 'N1 issuer distribution reconciliation', cfg, parent) as run:
        manifest, evidence_manifest = verify(source), verify(evidence)
        config = manifest['metadata']['config']
        run.base.update(universe=config['universe'], splits=config.get('splits', {}))
        issuer = issuer_events(evidence, evidence_manifest)
        frames = normalized(source, manifest, {})
        start, end = config['common_start'], config['cutoff']
        tickers, payable = {}, {}
        for ticker, frame in frames.items():
            if ticker not in issuer:
                view = frame.loc[start:end]
                tickers[ticker] = {'status': 'unverified_no_issuer_source', 'source': None,
                                   'counts': {'yahoo_events': int((view.dividend > 0).sum())}}
                continue
            s, events = issuer[ticker]
            tickers[ticker] = c = compare(frame, s, events, start, end)
            ref = f'{s["file"]}#{s["sha256"]}'
            dates = {m['ex_date']: {'date': m['payable_date'], 'source': ref} for m in c['matched']
                     if m['payable_date'] and m['payable_date'] >= m['ex_date']}
            if dates:
                payable[ticker] = dates
        comparison = {'schema_version': 1, 'tolerance': TOLERANCE, 'window': {'start': start, 'end': end},
                      'tickers': tickers}
        target = root / 'data/reconciliation' / run.run_id
        freeze(target, {'comparison.json': canonical_bytes(comparison), 'payable.json': canonical_bytes(payable)},
               {'source_snapshot': cfg['source_snapshot'], 'evidence_snapshot': cfg['evidence_snapshot'],
                'source_manifest_sha256': sha256((source / 'manifest.json').read_bytes()),
                'evidence_manifest_sha256': sha256((evidence / 'manifest.json').read_bytes()),
                'environment': run.env, 'run_id': run.run_id, 'tolerance': TOLERANCE})
        warnings = []
        for status, text in [('unresolved', 'Unresolved issuer reconciliation'),
                             ('unverified_no_issuer_source', 'No issuer distribution source')]:
            if names := [t for t, c in tickers.items() if c['status'] == status]:
                warnings.append(f'{text}: {", ".join(names)}')
        run.finish('completed', [target.relative_to(root).as_posix()],
                   sha256((target / 'manifest.json').read_bytes()), warnings)
    return target
