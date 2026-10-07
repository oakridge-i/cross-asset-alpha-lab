"""Offline reconciliation of Yahoo distributions against frozen issuer evidence."""
from pathlib import Path

from .evidence import AMOUNT_BASES, parse_invesco_json, parse_ishares_html, parse_ssga_xlsx
from .normalize import TOLERANCE, match_tolerance
from .pipeline import (check_vintage_lineage, corrections_info, normalized, project_path, read_corrections,
                       require_inside)
from .provenance import Run, canonical_bytes, freeze, sha256, verify

CLASSES = ['matched', 'amount_mismatch', 'issuer_only', 'yahoo_only', 'outside_issuer_coverage']


def issuer_events(evidence, manifest):
    """{ticker: (source, events)} for parseable sources; refuses snapshots with failed sources."""
    out = {}
    for s in manifest['metadata']['sources']:
        if s['status'] != 'completed':
            raise ValueError(f'failed evidence source: {s["id"]}')
        # Documents too: a no_distributions status may only cite files frozen in this snapshot.
        if manifest['files'].get(s['file']) != s['sha256']:
            raise ValueError(f'evidence source {s["id"]} does not match the manifest')
        if s['kind'] == 'document':
            continue
        if s.get('amount_basis') not in AMOUNT_BASES:
            raise ValueError(f'evidence source {s["id"]} has no valid amount_basis')
        body = (evidence / s['file']).read_bytes()
        for ticker in s['tickers']:
            if ticker in out:
                raise ValueError(f'several distribution sources for {ticker}')
            if s['kind'] == 'ssga_xlsx':
                out[ticker] = s, parse_ssga_xlsx(body, ticker)
            elif s['kind'] == 'ishares_html' and len(s['tickers']) == 1:
                out[ticker] = s, parse_ishares_html(body)
            elif s['kind'] == 'invesco_json' and len(s['tickers']) == 1:
                out[ticker] = s, parse_invesco_json(body)
            else:
                raise ValueError(f'unsupported evidence source: {s["id"]}')
    return out


def source_ref(source, evidence_snapshot):
    """Evidence citation shared by payable dates and derived corrections: issuer URL, evidence snapshot
    project path and file#sha256, so a reader can locate and verify the exact byte evidence."""
    return f'{source["url"]} {evidence_snapshot}/{source["file"]}#{source["sha256"]}'


def no_distribution_sources(manifest):
    """{ticker: [source, ...]} for document sources asserting the issuer makes no distributions;
    a ticker may be corroborated by more than one document."""
    out = {}
    for s in manifest['metadata']['sources']:
        if s['kind'] == 'document':
            for ticker in s.get('no_distributions') or []:
                out.setdefault(ticker, []).append(s)
    return out


def compare(frame, source, events, start, end):
    """Classify ex-date events in as-traded units; materiality sums |yahoo - issuer| / previous as-traded close
    over compared events. current_units issuer amounts are scaled by the split factor applied to Yahoo."""
    view = frame.loc[start:end]
    yahoo = {d: round(float(a), 10) for d, a in view.dividend[view.dividend > 0].items()}
    first, last = events[0]['ex_date'], events[-1]['ex_date']
    issuer = {e['ex_date']: e for e in events if start <= e['ex_date'] <= end and e['amount'] > 0}
    zero_dates = sorted(e['ex_date'] for e in events if start <= e['ex_date'] <= end and e['amount'] == 0)
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
        # Same as normalize's future_split_factor on sessions; also defined for non-session issuer dates.
        factor = float(frame.split_ratio[frame.index > d].prod())
        raw = i and i['amount']
        amount = None if i is None else round(raw * factor if source['amount_basis'] == 'current_units' else raw, 10)
        diff = round((y or 0.) - (amount or 0.), 10)
        tolerance = match_tolerance(factor)
        row = dict(ex_date=d, yahoo_amount=y, issuer_amount=amount, issuer_raw_amount=raw,
                   amount_basis=source['amount_basis'], split_factor=factor, tolerance=tolerance, diff=diff,
                   record_date=i and i['record_date'], payable_date=i and i['payable_date'],
                   previous_close=float(before.iloc[-1]), bps=abs(diff) / float(before.iloc[-1]) * 1e4)
        bps += row['bps']
        kind = ('issuer_only' if y is None else 'yahoo_only' if i is None
                else 'matched' if abs(diff) <= tolerance + 1e-12 else 'amount_mismatch')
        result[kind].append(row)
    counts = {'yahoo_events': len(yahoo), 'issuer_events': len(issuer), 'issuer_zero_rows': len(zero_dates)}
    counts |= {k: len(v) for k, v in result.items()}
    confirmed = not any(result[k] for k in CLASSES[1:])
    return dict(status='confirmed' if confirmed else 'unresolved', counts=counts, materiality_bps=bps,
                coverage={'first_ex_date': first, 'last_ex_date': last},
                source={k: source[k] for k in ['id', 'url', 'file', 'sha256', 'kind', 'amount_basis']},
                issuer_zero_dates=zero_dates, **result)


def reconcile(root, source_snapshot, evidence_snapshot, parent=None, corrections=None):
    """corrections is a dict or a path relative to root: applying a corrected vintage's corrections.json
    here lets a corrected frame be reconciled again, to confirm the correction actually resolves the event."""
    root, source, evidence = Path(root).resolve(), Path(source_snapshot).resolve(), Path(evidence_snapshot).resolve()
    corrections, corrections_path = read_corrections(
        root, corrections, 'N1 issuer distribution reconciliation',
        {'source_snapshot': project_path(root, source), 'evidence_snapshot': project_path(root, evidence)}, parent)
    cfg = {'source_snapshot': project_path(root, source), 'evidence_snapshot': project_path(root, evidence),
           'tolerance': TOLERANCE, 'corrections': corrections or {}}
    with Run(root, 'N1 issuer distribution reconciliation', cfg, parent) as run:
        require_inside(root, source, evidence)
        manifest, evidence_manifest = verify(source), verify(evidence)
        run.base.update(source_manifest_sha256=sha256((source / 'manifest.json').read_bytes()),
                        evidence_manifest_sha256=sha256((evidence / 'manifest.json').read_bytes()))
        config = manifest['metadata']['config']
        run.base.update(universe=config['universe'], splits=config.get('splits', {}))
        info = corrections_info(root, corrections, corrections_path)
        run.base.update(info)
        if corrections_path is not None:
            check_vintage_lineage(root, run.base['source_manifest_sha256'], corrections_path, None)
        issuer = issuer_events(evidence, evidence_manifest)
        no_distributions = no_distribution_sources(evidence_manifest)
        frames = normalized(source, manifest, {}, corrections or {})
        start, end = config['common_start'], config['cutoff']
        tickers, payable = {}, {}
        for ticker, frame in frames.items():
            if ticker not in issuer:
                view = frame.loc[start:end]
                yahoo_events = int((view.dividend > 0).sum())
                if docs := no_distributions.get(ticker):
                    status = 'confirmed_no_distributions' if yahoo_events == 0 else 'unresolved'
                    basis = next((d['basis'] for d in docs if d.get('basis')), None)
                    tickers[ticker] = {'status': status, 'basis': basis,
                                       'source': [{k: d[k] for k in ['id', 'url', 'file', 'sha256', 'kind']}
                                                  for d in docs],
                                       'counts': {'yahoo_events': yahoo_events}, 'issuer_zero_dates': []}
                else:
                    tickers[ticker] = {'status': 'unverified_no_issuer_source', 'source': None,
                                       'counts': {'yahoo_events': yahoo_events}, 'issuer_zero_dates': []}
                continue
            s, events = issuer[ticker]
            tickers[ticker] = c = compare(frame, s, events, start, end)
            ref = source_ref(s, cfg['evidence_snapshot'])
            dates = {m['ex_date']: {'date': m['payable_date'], 'source': ref} for m in c['matched']
                     if m['payable_date'] and m['payable_date'] >= m['ex_date']}
            if dates:
                payable[ticker] = dates
        comparison = {'schema_version': 1, 'tolerance': TOLERANCE, 'window': {'start': start, 'end': end},
                      'tickers': tickers}
        target = root / 'data/reconciliation' / run.run_id
        freeze(target, {'comparison.json': canonical_bytes(comparison), 'payable.json': canonical_bytes(payable)},
               {'source_snapshot': cfg['source_snapshot'], 'evidence_snapshot': cfg['evidence_snapshot'],
                'source_manifest_sha256': run.base['source_manifest_sha256'],
                'evidence_manifest_sha256': run.base['evidence_manifest_sha256'],
                'environment': run.env, 'run_id': run.run_id, 'tolerance': TOLERANCE} | info)
        warnings = []
        for status, text in [('unresolved', 'Unresolved issuer reconciliation'),
                             ('unverified_no_issuer_source', 'No issuer distribution source')]:
            if names := [t for t, c in tickers.items() if c['status'] == status]:
                warnings.append(f'{text}: {", ".join(names)}')
        run.finish('completed', [target.relative_to(root).as_posix()],
                   sha256((target / 'manifest.json').read_bytes()), warnings)
    return target
