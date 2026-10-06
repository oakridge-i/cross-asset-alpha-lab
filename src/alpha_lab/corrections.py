"""Explicit, per-event issuer corrections derived from reconciliation output, frozen as a separate vintage.

The Yahoo source snapshot is never modified or re-acquired. A correction is only ever derived for an
event reconciliation already classified as unresolved against issuer evidence; a matched event is never
touched. Three rules, matching the issuer-authoritative decision:
  - issuer_only  -> add the issuer's as-traded amount (Yahoo had no event on that ex-date).
  - amount_mismatch -> replace Yahoo's amount with the issuer's as-traded amount.
  - yahoo_only   -> remove, but only when the issuer lists an explicit zero-amount row on that ex-date;
                    otherwise the event is left unresolved rather than silently dropped.
"""
import json
from pathlib import Path
from .pipeline import NO_CORRECTIONS_SHA256, project_path, require_inside
from .provenance import Run, canonical_bytes, freeze, sha256, verify
from .reconcile import source_ref


def derive(comparison, evidence_ref):
    """{ticker: {ex_date: {action, yahoo_amount, issuer_amount, payable_date, source}}} from a
    comparison.json-shaped dict. evidence_ref is the evidence snapshot's project path (as recorded in the
    reconciliation run's metadata), combined with each ticker's own issuer source to build the evidence
    citation. Tickers without a parseable issuer source (no_distributions/unverified statuses) are skipped."""
    out = {}
    for ticker, c in comparison.get('tickers', {}).items():
        source = c.get('source')
        if not source or isinstance(source, list):
            continue  # no issuer distribution source to cite a correction against
        ref = source_ref(source, evidence_ref)
        events = {}
        for row in c.get('issuer_only', []):
            events[row['ex_date']] = {'action': 'add', 'yahoo_amount': row['yahoo_amount'],
                                      'issuer_amount': row['issuer_amount'], 'payable_date': row['payable_date'],
                                      'source': ref}
        for row in c.get('amount_mismatch', []):
            events[row['ex_date']] = {'action': 'replace', 'yahoo_amount': row['yahoo_amount'],
                                      'issuer_amount': row['issuer_amount'], 'payable_date': row['payable_date'],
                                      'source': ref}
        zero_dates = set(c.get('issuer_zero_dates', []))
        for row in c.get('yahoo_only', []):
            if row['ex_date'] in zero_dates:
                events[row['ex_date']] = {'action': 'remove', 'yahoo_amount': row['yahoo_amount'],
                                          'issuer_amount': 0.0, 'payable_date': None, 'source': ref}
            # else: no explicit issuer zero row on this ex-date; the event stays unresolved, uncorrected.
        if events:
            out[ticker] = events
    return out


def corrections_run(root, reconciliation_snapshot, parent=None):
    """Freezes data/corrections/<run_id>/{corrections.json, payable.json}. corrections.json is derive()'s
    output; payable.json is the reconciliation's payable plus the actual payable date for every add/replace
    event that has one (a remove event never pays, so it contributes nothing)."""
    root, reconciliation = Path(root).resolve(), Path(reconciliation_snapshot).resolve()
    cfg = {'reconciliation_snapshot': project_path(root, reconciliation)}
    with Run(root, 'N1 issuer corrections', cfg, parent) as run:
        require_inside(root, reconciliation)
        manifest = verify(reconciliation)
        # Corrections are derived from Yahoo-vs-issuer differences; a corrected frame has none left to derive
        # from, so a corrected reconciliation must never seed another corrections vintage.
        if manifest['metadata'].get('corrections_sha256', NO_CORRECTIONS_SHA256) != NO_CORRECTIONS_SHA256:
            raise ValueError('reconciliation snapshot was produced with corrections; use the uncorrected one')
        run.base['reconciliation_manifest_sha256'] = sha256((reconciliation / 'manifest.json').read_bytes())
        comparison = json.loads((reconciliation / 'comparison.json').read_bytes())
        reconciled_payable = json.loads((reconciliation / 'payable.json').read_bytes())
        evidence_ref = manifest['metadata']['evidence_snapshot']
        corrections = derive(comparison, evidence_ref)
        payable = {ticker: dict(dates) for ticker, dates in reconciled_payable.items()}
        for ticker, events in corrections.items():
            for ex_date, event in events.items():
                if event['action'] in ('add', 'replace') and event.get('payable_date'):
                    if event['payable_date'] < ex_date:
                        raise ValueError(f'issuer payable date precedes the ex-date: {ticker}/{ex_date}')
                    payable.setdefault(ticker, {})[ex_date] = {'date': event['payable_date'],
                                                                'source': event['source']}
        target = root / 'data/corrections' / run.run_id
        freeze(target, {'corrections.json': canonical_bytes(corrections), 'payable.json': canonical_bytes(payable)},
               {'reconciliation_snapshot': cfg['reconciliation_snapshot'],
                'reconciliation_manifest_sha256': run.base['reconciliation_manifest_sha256'],
                'environment': run.env, 'run_id': run.run_id})
        run.finish('completed', [target.relative_to(root).as_posix()],
                   sha256((target / 'manifest.json').read_bytes()), [])
    return target
