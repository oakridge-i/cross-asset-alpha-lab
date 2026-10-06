from datetime import datetime, timezone
import json
from pathlib import Path
import pandas as pd
import pytest
from alpha_lab import reconcile as r
from alpha_lab.pipeline import audit_snapshot
from alpha_lab.provenance import freeze, sha256
from alpha_lab.quality import parse_chart
from test_evidence import page, table, xlsx

SESSIONS = ['2017-11-27', '2017-11-28', '2017-11-29', '2017-11-30', '2017-12-01',
            '2017-12-04', '2017-12-05', '2017-12-06', '2017-12-07', '2017-12-08']


def ts(day):
    return int(datetime.fromisoformat(day + 'T15:00').replace(tzinfo=timezone.utc).timestamp())


def chart(ticker, closes, dividends=(), splits=()):
    q = {k: closes for k in ['open', 'high', 'low', 'close']} | {'volume': [100] * len(closes)}
    events = {'dividends': {str(n): {'date': ts(d), 'amount': a} for n, (d, a) in enumerate(dividends)},
              'splits': {str(n): {'date': ts(d), 'numerator': a, 'denominator': b} for n, (d, a, b) in enumerate(splits)}}
    return json.dumps({'chart': {'error': None, 'result': [{
        'meta': {'symbol': ticker, 'currency': 'USD', 'exchangeTimezoneName': 'America/New_York'},
        'timestamp': [ts(d) for d in SESSIONS], 'indicators': {'quote': [q], 'adjclose': [{'adjclose': closes}]},
        'events': events}]}}).encode()


def source(root):
    charts = {
        # BIL-like 1:2 reverse split: Yahoo reports 0.406 per post-split share before the split.
        'BIL': chart('BIL', [90.] * 6 + [91.] * 4, [('2017-11-29', 0.406)], [('2017-12-05', 1, 2)]),
        'SPY': chart('SPY', [100.] * 10, [('2017-11-28', 0.5), ('2017-11-29', 0.7), ('2017-11-30', 1.0),
                                          ('2017-12-04', 0.3)]),
        'EFA': chart('EFA', [60.] * 10, [('2017-11-29', 0.648931)]),
        'GLD': chart('GLD', [120.] * 10)}
    files = {}
    for ticker, body in charts.items():
        files[f'raw/{ticker}-0.json'] = body
        files[f'adapter/{ticker}.csv'] = parse_chart(body, ticker).drop(columns='Capital Gains').to_csv(
            index_label='Date').encode()
    config = {'universe': list(charts), 'start': '2017-11-27', 'common_start': '2017-11-28', 'cutoff': '2017-12-08',
              'end_exclusive': '2017-12-09', 'pay_delay_days': 10, 'adjustment_factor_tolerance': 0.00005}
    return freeze(root / 'data/snapshots/s', files, {'config': config, 'retrieved_at': '2026-10-06T00:00:00+00:00'})


SSGA = [
    ['T-Bill', 'BIL', 'x', '11/29/2017', '11/30/2017', '12/05/2017', '0.203102', '', '', 'Monthly'],
    ['T-Bill', 'BIL', 'x', '11/30/2017', '12/01/2017', '12/06/2017', '0.000000', '', '', 'Monthly'],
    ['S&P 500', 'SPY', 'x', '11/29/2017', '11/30/2017', '12/15/2017', '0.7004', '', '', 'Quarterly'],
    ['S&P 500', 'SPY', 'x', '11/30/2017', '12/01/2017', '12/16/2017', '1.0011', '', '', 'Quarterly'],
    ['S&P 500', 'SPY', 'x', '12/01/2017', '12/04/2017', '12/17/2017', '0.25', '', '', 'Quarterly'],
    ['S&P 500', 'SPY', 'x', '12/11/2017', '12/12/2017', '12/18/2017', '0.4', '', '', 'Quarterly'],
]
EFA = {'exDate': [20171129], 'recordDate': [20171130], 'payableDate': [20171128], 'totalDistribution': ['0.648931']}


def evidence(root, failed=False):
    files = {'ssga.xlsx': xlsx(SSGA), 'efa.html': page(EFA, EFA), 'memo.pdf': b'%PDF memo'}
    sources = [dict(id=i, file=f, url=f'https://issuer.test/{f}', kind=k, tickers=t, retrieved_at='2026-10-06T00:00:00',
                    sha256=sha256(files[f]), http_status=200, status='completed')
               for i, f, k, t in [('ssga', 'ssga.xlsx', 'ssga_xlsx', ['SPY', 'BIL']),
                                  ('efa', 'efa.html', 'ishares_html', ['EFA']),
                                  ('memo', 'memo.pdf', 'document', ['EEM'])]]
    if failed:
        sources[1].update(status='failed', error='HTTP 403')
    return freeze(root / 'data/evidence/e', files, {'sources': sources})


def run(root):
    target = r.reconcile(root, source(root), evidence(root))
    load = lambda name: json.loads((target / name).read_bytes())
    return target, load('comparison.json'), load('payable.json')


def test_split_adjusted_yahoo_matches_as_traded_issuer_and_zero_rows_are_not_events(tmp_path, no_network):
    _, c, _ = run(tmp_path)
    bil = c['tickers']['BIL']
    assert bil['status'] == 'confirmed'
    assert bil['counts'] == {'yahoo_events': 1, 'issuer_events': 1, 'issuer_zero_rows': 1, 'matched': 1,
                             'amount_mismatch': 0, 'issuer_only': 0, 'yahoo_only': 0, 'outside_issuer_coverage': 0}
    assert bil['coverage'] == {'first_ex_date': '2017-11-29', 'last_ex_date': '2017-11-30'}
    [m] = bil['matched']
    assert (m['ex_date'], m['yahoo_amount'], m['issuer_amount'], m['diff']) == ('2017-11-29', 0.203, 0.203102, -0.000102)
    assert m['previous_close'] == 45.0
    assert bil['materiality_bps'] == pytest.approx(0.000102 / 45 * 1e4)


def test_discrepancy_classes_coverage_and_materiality(tmp_path):
    _, c, _ = run(tmp_path)
    spy = c['tickers']['SPY']
    assert spy['status'] == 'unresolved'
    assert spy['counts'] == {'yahoo_events': 4, 'issuer_events': 3, 'issuer_zero_rows': 0, 'matched': 1,
                             'amount_mismatch': 1, 'issuer_only': 1, 'yahoo_only': 1, 'outside_issuer_coverage': 1}
    assert spy['coverage'] == {'first_ex_date': '2017-11-29', 'last_ex_date': '2017-12-11'}
    pick = lambda kind: [(x['ex_date'], x['yahoo_amount'], x['issuer_amount']) for x in spy[kind]]
    assert pick('matched') == [('2017-11-29', 0.7, 0.7004)]
    assert pick('amount_mismatch') == [('2017-11-30', 1.0, 1.0011)]
    assert pick('issuer_only') == [('2017-12-01', None, 0.25)]
    assert pick('yahoo_only') == [('2017-12-04', 0.3, None)]
    assert spy['outside_issuer_coverage'] == [{'ex_date': '2017-11-28', 'yahoo_amount': 0.5}]
    # 0.0004 + 0.0011 + 0.25 + 0.3 USD on a previous close of 100.
    assert spy['materiality_bps'] == pytest.approx(55.15)
    assert c['tickers']['EFA']['status'] == 'confirmed'
    gld = c['tickers']['GLD']
    assert (gld['status'], gld['source'], gld['counts']['yahoo_events']) == ('unverified_no_issuer_source', None, 0)
    assert c['tolerance'] == r.TOLERANCE == 0.0005


def test_payable_only_for_matched_events_and_audit_accepts_it(tmp_path):
    target, _, payable = run(tmp_path)
    ref = 'ssga.xlsx#' + sha256(xlsx(SSGA))
    # EFA matched, but its payable date precedes the ex-date and is rejected.
    assert payable == {'BIL': {'2017-11-29': {'date': '2017-12-05', 'source': ref}},
                       'SPY': {'2017-11-29': {'date': '2017-12-15', 'source': ref}}}
    derived = audit_snapshot(tmp_path, tmp_path / 'data/snapshots/s', payable=payable)
    bil = pd.read_csv(derived / 'normalized/BIL.csv', index_col=0, keep_default_na=False)
    assert bil.loc['2017-11-29', ['payable_date', 'payable_basis', 'payable_source']].tolist() == [
        '2017-12-05', 'actual', ref]
    rows = [json.loads(x) for x in (tmp_path / 'experiments/EXPERIMENT_LOG.jsonl').read_text().splitlines()]
    assert [x['event'] for x in rows[:2]] == ['started', 'completed']
    assert rows[1]['output_paths'] == [target.relative_to(tmp_path).as_posix()]
    assert rows[1]['quality_warnings'] == ['Unresolved issuer reconciliation: SPY',
                                           'No issuer distribution source: GLD']


def test_failed_evidence_source_is_refused_and_logged(tmp_path, no_network):
    with pytest.raises(ValueError, match='failed evidence source'):
        r.reconcile(tmp_path, source(tmp_path), evidence(tmp_path, failed=True))
    rows = [json.loads(x) for x in (tmp_path / 'experiments/EXPERIMENT_LOG.jsonl').read_text().splitlines()]
    assert [x['event'] for x in rows] == ['started', 'failed']


def test_cli_reconcile_output_feeds_audit_payable_unchanged(tmp_path, capsys, no_network):
    from alpha_lab.__main__ import main
    source(tmp_path), evidence(tmp_path)
    main(['reconcile', 'data/snapshots/s', 'data/evidence/e', '--root', str(tmp_path)])
    target = Path(capsys.readouterr().out.strip())
    main(['audit', 'data/snapshots/s', '--root', str(tmp_path), '--payable', str(target / 'payable.json')])
    derived = Path(capsys.readouterr().out.strip())
    assert (derived / 'payable.json').read_bytes() == (target / 'payable.json').read_bytes()
