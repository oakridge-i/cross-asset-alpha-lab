from datetime import datetime, timezone
import json
from pathlib import Path
import pandas as pd
import pytest
from alpha_lab import reconcile as r
from alpha_lab.pipeline import audit_snapshot, replay_snapshot
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


def source(root, gld_dividends=(), name='s'):
    charts = {
        # BIL-like 1:2 reverse split: Yahoo reports 0.406 per post-split share before the split.
        'BIL': chart('BIL', [90.] * 6 + [91.] * 4, [('2017-11-29', 0.406)], [('2017-12-05', 1, 2)]),
        'SPY': chart('SPY', [100.] * 10, [('2017-11-28', 0.5), ('2017-11-29', 0.7), ('2017-11-30', 1.0),
                                          ('2017-12-04', 0.3)]),
        'EFA': chart('EFA', [60.] * 10, [('2017-11-29', 0.648931)]),
        'GLD': chart('GLD', [120.] * 10, gld_dividends),
        # EEM-like 3:1 split; Yahoo amounts are per post-split share, as-traded = 3x before the split.
        'EEM': chart('EEM', [50.] * 10, [('2017-11-29', 0.649), ('2017-11-30', 0.5004), ('2017-12-01', 0.40053333333)],
                     [('2017-12-05', 3, 1)])}
    files = {}
    for ticker, body in charts.items():
        files[f'raw/{ticker}-0.json'] = body
        files[f'adapter/{ticker}.csv'] = parse_chart(body, ticker).drop(columns='Capital Gains').to_csv(
            index_label='Date').encode()
    config = {'universe': list(charts), 'start': '2017-11-27', 'common_start': '2017-11-28', 'cutoff': '2017-12-08',
              'end_exclusive': '2017-12-09', 'pay_delay_days': 10, 'adjustment_factor_tolerance': 0.00005}
    return freeze(root / f'data/snapshots/{name}', files, {'config': config, 'retrieved_at': '2026-10-06T00:00:00+00:00'})


SSGA = [
    ['T-Bill', 'BIL', 'x', '11/29/2017', '11/30/2017', '12/05/2017', '0.203102', '', '', 'Monthly'],
    ['T-Bill', 'BIL', 'x', '11/30/2017', '12/01/2017', '12/06/2017', '0.000000', '', '', 'Monthly'],
    ['S&P 500', 'SPY', 'x', '11/29/2017', '11/30/2017', '12/15/2017', '0.7004', '', '', 'Quarterly'],
    ['S&P 500', 'SPY', 'x', '11/30/2017', '12/01/2017', '12/16/2017', '1.0011', '', '', 'Quarterly'],
    ['S&P 500', 'SPY', 'x', '12/01/2017', '12/04/2017', '12/17/2017', '0.25', '', '', 'Quarterly'],
    ['S&P 500', 'SPY', 'x', '12/11/2017', '12/12/2017', '12/18/2017', '0.4', '', '', 'Quarterly'],
]
EFA = {'exDate': [20171129], 'recordDate': [20171130], 'payableDate': [20171128], 'totalDistribution': ['0.648931']}
# iShares restates pre-split distributions in current units.
EEM = {'exDate': [20171129, 20171130, 20171201], 'recordDate': [None] * 3, 'payableDate': [None] * 3,
       'totalDistribution': ['0.648931', '0.5', '0.4']}


def evidence(root, failed=False, change=None):
    files = {'ssga.xlsx': xlsx(SSGA), 'efa.html': page(EFA, EFA), 'eem.html': page(EEM, EEM), 'memo.pdf': b'%PDF memo'}
    sources = [dict(id=i, file=f, url=f'https://issuer.test/{f}', kind=k, tickers=t, amount_basis=b,
                    retrieved_at='2026-10-06T00:00:00', sha256=sha256(files[f]), http_status=200, status='completed')
               for i, f, k, t, b in [('ssga', 'ssga.xlsx', 'ssga_xlsx', ['SPY', 'BIL'], 'as_traded'),
                                     ('efa', 'efa.html', 'ishares_html', ['EFA'], 'current_units'),
                                     ('eem', 'eem.html', 'ishares_html', ['EEM'], 'current_units'),
                                     ('memo', 'memo.pdf', 'document', ['EEM'], None)]]
    if failed:
        sources[1].update(status='failed', error='HTTP 403')
    if change:
        sources[0].update(change)
    return freeze(root / 'data/evidence/e', files, {'sources': sources})


def run(root):
    target = r.reconcile(root, source(root), evidence(root))
    load = lambda name: json.loads((target / name).read_bytes())
    return target, load('comparison.json'), load('payable.json')


def gld_evidence(root, name, drop=None, change=None):
    """Same issuer sources as evidence(), plus two document sources corroborating that GLD pays no
    distributions: a prospectus (which also carries the explicit `basis` for the status) and a FAQ.
    drop omits a file from the frozen snapshot; change updates the prospectus source metadata."""
    files = {'ssga.xlsx': xlsx(SSGA), 'efa.html': page(EFA, EFA), 'eem.html': page(EEM, EEM),
             'memo.pdf': b'%PDF memo', 'gld.pdf': b'%PDF gld prospectus', 'gld-faq.pdf': b'%PDF gld faq'}
    sources = [dict(id=i, file=f, url=f'https://issuer.test/{f}', kind=k, tickers=t, amount_basis=b,
                    retrieved_at='2026-10-06T00:00:00', sha256=sha256(files[f]), http_status=200, status='completed')
               for i, f, k, t, b in [('ssga', 'ssga.xlsx', 'ssga_xlsx', ['SPY', 'BIL'], 'as_traded'),
                                     ('efa', 'efa.html', 'ishares_html', ['EFA'], 'current_units'),
                                     ('eem', 'eem.html', 'ishares_html', ['EEM'], 'current_units'),
                                     ('memo', 'memo.pdf', 'document', ['EEM'], None)]]
    sources.append(dict(id='gld', file='gld.pdf', url='https://issuer.test/gld.pdf', kind='document',
                        tickers=['GLD'], amount_basis=None, no_distributions=['GLD'],
                        statements=[{'quote': 'will not receive dividends', 'page': 'p. 9'},
                                    {'quote': 'distributions to Shareholders in only two circumstances', 'page': 'p. 30'}],
                        basis='Distributions are permitted only in two narrow indenture cases (excess cash '
                              'reserve or trust termination); the GLD FAQ states no distributions of sale '
                              'proceeds are made; GLD has not been terminated; Yahoo shows zero dividend '
                              'events for GLD in the reconciliation window.',
                        retrieved_at='2026-10-06T00:00:00', sha256=sha256(files['gld.pdf']), http_status=200,
                        status='completed'))
    sources.append(dict(id='gld-faq', file='gld-faq.pdf', url='https://issuer.test/gld-faq.pdf', kind='document',
                        tickers=['GLD'], amount_basis=None, no_distributions=['GLD'],
                        statements=[{'quote': "makes no distributions of sale proceeds to the Trust's shareholders",
                                    'page': 'p. 3'}],
                        retrieved_at='2026-10-06T00:00:00', sha256=sha256(files['gld-faq.pdf']), http_status=200,
                        status='completed'))
    if change:
        sources[-2].update(change)
    if drop:
        files.pop(drop)
    return freeze(root / f'data/evidence/{name}', files, {'sources': sources})


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
    assert (m['issuer_raw_amount'], m['amount_basis'], m['split_factor'], m['tolerance']) == (
        0.203102, 'as_traded', 0.5, 0.0005)
    assert bil['materiality_bps'] == pytest.approx(0.000102 / 45 * 1e4)


def test_issuer_zero_dates_recorded(tmp_path, no_network):
    _, c, _ = run(tmp_path)
    assert c['tickers']['BIL']['issuer_zero_dates'] == ['2017-11-30']
    assert c['tickers']['SPY']['issuer_zero_dates'] == []
    # Present (possibly empty) on every ticker, including GLD's unverified_no_issuer_source, so a
    # consumer (e.g. Task 2's correction rules) can index it uniformly without a status check first.
    assert all('issuer_zero_dates' in t for t in c['tickers'].values())


def test_gld_no_distribution_status(tmp_path, no_network):
    target = r.reconcile(tmp_path, source(tmp_path), gld_evidence(tmp_path, 'e-gld-clean'))
    c = json.loads((target / 'comparison.json').read_bytes())
    gld = c['tickers']['GLD']
    assert gld['status'] == 'confirmed_no_distributions'
    assert gld['counts']['yahoo_events'] == 0
    assert gld['issuer_zero_dates'] == []
    assert {s['id'] for s in gld['source']} == {'gld', 'gld-faq'}  # both corroborating documents are listed
    assert gld['basis'] and 'two' in gld['basis']  # the no-distribution scope is explicit, not just asserted

    target2 = r.reconcile(tmp_path, source(tmp_path, gld_dividends=[('2017-11-29', 0.01)], name='s2'),
                          gld_evidence(tmp_path, 'e-gld-dividend'))
    c2 = json.loads((target2 / 'comparison.json').read_bytes())
    gld2 = c2['tickers']['GLD']
    assert gld2['status'] == 'unresolved'
    assert gld2['counts']['yahoo_events'] == 1
    assert gld2['issuer_zero_dates'] == []


def test_discrepancy_classes_coverage_and_materiality(tmp_path, no_network):
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
    assert gld['issuer_zero_dates'] == []  # present and empty, not absent, for a ticker without issuer events
    assert c['tolerance'] == r.TOLERANCE == 0.0005


def test_current_unit_issuer_amounts_and_tolerance_scale_with_split_factor(tmp_path, no_network):
    _, c, _ = run(tmp_path)
    eem = c['tickers']['EEM']
    pick = lambda kind: [(x['ex_date'], x['yahoo_amount'], x['issuer_raw_amount'], x['issuer_amount'],
                          x['amount_basis'], x['split_factor'], x['tolerance']) for x in eem[kind]]
    assert pick('matched') == [('2017-11-29', 1.947, 0.648931, 1.946793, 'current_units', 3.0, 0.0015),
                               ('2017-11-30', 1.5012, 0.5, 1.5, 'current_units', 3.0, 0.0015)]
    assert pick('amount_mismatch') == [('2017-12-01', 1.2016, 0.4, 1.2, 'current_units', 3.0, 0.0015)]
    assert [x['diff'] for x in eem['matched']] == [0.000207, 0.0012]
    assert eem['amount_mismatch'][0]['diff'] == pytest.approx(0.0016)
    assert eem['status'] == 'unresolved'


def test_payable_only_for_matched_events_and_audit_accepts_it(tmp_path, no_network):
    target, _, payable = run(tmp_path)
    ref = 'https://issuer.test/ssga.xlsx data/evidence/e/ssga.xlsx#' + sha256(xlsx(SSGA))
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
    assert rows[1]['quality_warnings'] == ['Unresolved issuer reconciliation: SPY, EEM',
                                           'No issuer distribution source: GLD']
    manifest = lambda name: sha256((tmp_path / f'data/{name}/manifest.json').read_bytes())
    assert (rows[1]['source_manifest_sha256'], rows[1]['evidence_manifest_sha256']) == (
        manifest('snapshots/s'), manifest('evidence/e'))
    assert rows[3]['source_manifest_sha256'] == manifest('snapshots/s')


def test_altered_evidence_bytes_are_refused(tmp_path, no_network):
    e = evidence(tmp_path)
    (e / 'ssga.xlsx').write_bytes(xlsx(SSGA[:1]))
    with pytest.raises(ValueError, match='content hash mismatch'):
        r.reconcile(tmp_path, source(tmp_path), e)
    rows = [json.loads(x) for x in (tmp_path / 'experiments/EXPERIMENT_LOG.jsonl').read_text().splitlines()]
    assert [x['event'] for x in rows] == ['started', 'failed']


def test_failed_evidence_source_is_refused_and_logged(tmp_path, no_network):
    with pytest.raises(ValueError, match='failed evidence source'):
        r.reconcile(tmp_path, source(tmp_path), evidence(tmp_path, failed=True))
    rows = [json.loads(x) for x in (tmp_path / 'experiments/EXPERIMENT_LOG.jsonl').read_text().splitlines()]
    assert [x['event'] for x in rows] == ['started', 'failed']


@pytest.mark.parametrize('change', [{'file': 'missing.xlsx'}, {'sha256': '0' * 64}, {'amount_basis': None}],
                         ids=['file_not_in_manifest', 'hash_not_manifest', 'no_amount_basis'])
def test_evidence_metadata_must_agree_with_manifest(tmp_path, change, no_network):
    with pytest.raises(ValueError):
        r.reconcile(tmp_path, source(tmp_path), evidence(tmp_path, change=change))
    rows = [json.loads(x) for x in (tmp_path / 'experiments/EXPERIMENT_LOG.jsonl').read_text().splitlines()]
    assert [x['event'] for x in rows] == ['started', 'failed']


@pytest.mark.parametrize('drop,change', [('gld.pdf', None), (None, {'sha256': '0' * 64})],
                         ids=['document_not_in_manifest', 'document_hash_not_manifest'])
def test_no_distribution_documents_must_be_in_the_manifest(tmp_path, drop, change, no_network):
    with pytest.raises(ValueError, match='evidence source gld does not match the manifest'):
        r.reconcile(tmp_path, source(tmp_path), gld_evidence(tmp_path, 'e-gld', drop=drop, change=change))
    rows = [json.loads(x) for x in (tmp_path / 'experiments/EXPERIMENT_LOG.jsonl').read_text().splitlines()]
    assert [x['event'] for x in rows] == ['started', 'failed']
    assert not (tmp_path / 'data/reconciliation').exists()


def test_out_of_project_snapshots_are_logged_as_failed_runs(tmp_path, no_network):
    root = tmp_path / 'project'
    inside, outside = source(root), evidence(tmp_path)
    with pytest.raises(ValueError, match='outside project'):
        r.reconcile(root, inside, outside)
    with pytest.raises(ValueError, match='outside project'):
        audit_snapshot(root, source(tmp_path / 'other'))
    with pytest.raises(ValueError, match='outside project'):
        replay_snapshot(root, outside)
    rows = [json.loads(x) for x in (root / 'experiments/EXPERIMENT_LOG.jsonl').read_text().splitlines()]
    assert [x['event'] for x in rows] == ['started', 'failed'] * 3
    assert rows[0]['config']['evidence_snapshot'] == outside.as_posix()


def test_cli_reconcile_output_feeds_audit_payable_unchanged(tmp_path, capsys, no_network):
    from alpha_lab.__main__ import main
    source(tmp_path), evidence(tmp_path)
    main(['reconcile', 'data/snapshots/s', 'data/evidence/e', '--root', str(tmp_path)])
    target = Path(capsys.readouterr().out.strip())
    main(['audit', 'data/snapshots/s', '--root', str(tmp_path), '--payable', str(target / 'payable.json')])
    derived = Path(capsys.readouterr().out.strip())
    assert (derived / 'payable.json').read_bytes() == (target / 'payable.json').read_bytes()
