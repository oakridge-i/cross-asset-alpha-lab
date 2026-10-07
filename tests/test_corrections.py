"""Deriving explicit issuer corrections from reconciliation output and applying them as a frozen vintage."""
import json
import pytest
from alpha_lab import corrections as co
from alpha_lab.pipeline import NO_CORRECTIONS_SHA256, audit_snapshot
from alpha_lab.provenance import canonical_bytes, freeze, sha256, verify
from alpha_lab.quality import parse_chart
from alpha_lab.reconcile import reconcile
from test_evidence import xlsx
from test_reconcile import chart


def comparison_fixture():
    """Hand-built comparison.json shape covering every derive() rule with the brief's literal amounts."""
    src = {'id': 'ssga', 'url': 'https://issuer.test/ssga.xlsx', 'file': 'ssga.xlsx',
           'sha256': 'a' * 64, 'kind': 'ssga_xlsx', 'amount_basis': 'as_traded'}
    base = {'matched': [], 'issuer_only': [], 'amount_mismatch': [], 'yahoo_only': [],
            'outside_issuer_coverage': [], 'issuer_zero_dates': [], 'source': src, 'status': 'unresolved'}

    def row(**kw):
        return dict(record_date=None, issuer_raw_amount=None, amount_basis='as_traded', split_factor=1.0,
                    tolerance=0.0005, diff=0.0, previous_close=90.0, bps=0.0, **kw)

    return {'schema_version': 1, 'tolerance': 0.0005, 'window': {'start': '2012-01-01', 'end': '2023-12-31'},
            'tickers': {
                'HYG': base | {'issuer_only': [row(ex_date='2012-11-01', yahoo_amount=None, issuer_amount=0.510521,
                                                    payable_date='2012-11-07')]},
                'LQD': base | {'amount_mismatch': [row(ex_date='2023-12-14', yahoo_amount=0.379,
                                                       issuer_amount=0.37847, payable_date='2023-12-29')]},
                'BIL': base | {'issuer_zero_dates': ['2022-03-01'],
                               'yahoo_only': [row(ex_date='2022-03-01', yahoo_amount=0.022, issuer_amount=None,
                                                  payable_date=None)]},
                # No zero row on this ex-date: the yahoo_only event must stay uncorrected.
                'TLT': base | {'yahoo_only': [row(ex_date='2012-11-01', yahoo_amount=0.18, issuer_amount=None,
                                                  payable_date=None)]},
                # No issuer source at all (unverified_no_issuer_source / confirmed_no_distributions shape).
                'GLD': {'status': 'unverified_no_issuer_source', 'source': None, 'issuer_zero_dates': []},
            }}


def test_derive_rules():
    c = comparison_fixture()
    ref = 'https://issuer.test/ssga.xlsx data/evidence/e/ssga.xlsx#' + 'a' * 64
    result = co.derive(c, 'data/evidence/e')
    # TLT's yahoo_only has no issuer zero row and GLD has no issuer source: neither is corrected.
    assert set(result) == {'HYG', 'LQD', 'BIL'}
    assert result['HYG'] == {'2012-11-01': {'action': 'add', 'yahoo_amount': None, 'issuer_amount': 0.510521,
                                            'payable_date': '2012-11-07', 'source': ref}}
    assert result['LQD'] == {'2023-12-14': {'action': 'replace', 'yahoo_amount': 0.379, 'issuer_amount': 0.37847,
                                            'payable_date': '2023-12-29', 'source': ref}}
    assert result['BIL'] == {'2022-03-01': {'action': 'remove', 'yahoo_amount': 0.022, 'issuer_amount': 0.0,
                                            'payable_date': None, 'source': ref}}


SESSIONS = ['2017-11-27', '2017-11-28', '2017-11-29', '2017-11-30', '2017-12-01',
            '2017-12-04', '2017-12-05', '2017-12-06', '2017-12-07', '2017-12-08']


def source(root, name='cd', retrieved_at='2026-10-06T00:00:00+00:00'):
    charts = {
        # Mismatch at 11-30 (yahoo 1.0 vs issuer 1.05); issuer_only at 12-01 (issuer 0.25, no yahoo event).
        'CCC': chart('CCC', [100.] * 10, [('2017-11-30', 1.0)]),
        # Yahoo-only phantom at 11-29 with an explicit issuer zero row (removable); yahoo-only at 11-30 with
        # no issuer row at all (must stay unresolved); matched event at 12-01.
        'DDD': chart('DDD', [100.] * 10, [('2017-11-29', 0.05), ('2017-11-30', 0.07), ('2017-12-01', 0.03)]),
    }
    files = {}
    for ticker, body in charts.items():
        files[f'raw/{ticker}-0.json'] = body
        files[f'adapter/{ticker}.csv'] = parse_chart(body, ticker).drop(columns='Capital Gains').to_csv(
            index_label='Date').encode()
    config = {'universe': list(charts), 'start': '2017-11-27', 'common_start': '2017-11-28', 'cutoff': '2017-12-08',
              'end_exclusive': '2017-12-09', 'pay_delay_days': 10, 'adjustment_factor_tolerance': 0.00005}
    return freeze(root / f'data/snapshots/{name}', files,
                  {'config': config, 'retrieved_at': retrieved_at})


def evidence(root, name='cd'):
    rows = [
        ['CCC Fund', 'CCC', 'x', '11/30/2017', '12/01/2017', '12/06/2017', '1.05', '', '', 'Monthly'],
        ['CCC Fund', 'CCC', 'x', '12/01/2017', '12/04/2017', '12/08/2017', '0.25', '', '', 'Monthly'],
        ['DDD Fund', 'DDD', 'x', '11/29/2017', '11/30/2017', '12/05/2017', '0.000000', '', '', 'Monthly'],
        ['DDD Fund', 'DDD', 'x', '12/01/2017', '12/04/2017', '12/08/2017', '0.03', '', '', 'Monthly'],
    ]
    files = {'ssga.xlsx': xlsx(rows)}
    sources = [dict(id='ssga', file='ssga.xlsx', url='https://issuer.test/ssga.xlsx', kind='ssga_xlsx',
                    tickers=['CCC', 'DDD'], amount_basis='as_traded', retrieved_at='2026-10-06T00:00:00',
                    sha256=sha256(files['ssga.xlsx']), http_status=200, status='completed')]
    return freeze(root / f'data/evidence/{name}', files, {'sources': sources})


def test_corrected_reconcile_confirms(tmp_path, no_network):
    target = reconcile(tmp_path, source(tmp_path), evidence(tmp_path))
    before = json.loads((target / 'comparison.json').read_bytes())
    assert before['tickers']['CCC']['status'] == 'unresolved'
    assert before['tickers']['DDD']['counts']['yahoo_only'] == 2

    derived = co.corrections_run(tmp_path, target)
    corrections = json.loads((derived / 'corrections.json').read_bytes())
    assert set(corrections) == {'CCC', 'DDD'}
    assert set(corrections['CCC']) == {'2017-11-30', '2017-12-01'}
    assert corrections['CCC']['2017-11-30']['action'] == 'replace'
    assert corrections['CCC']['2017-12-01']['action'] == 'add'
    # Only the zero-row event on DDD is corrected; 2017-11-30 has no issuer zero row and stays unresolved.
    assert set(corrections['DDD']) == {'2017-11-29'}
    assert corrections['DDD']['2017-11-29']['action'] == 'remove'

    target2 = reconcile(tmp_path, source(tmp_path, 'cd2'), evidence(tmp_path, 'cd2'),
                        corrections=derived / 'corrections.json')
    c2 = json.loads((target2 / 'comparison.json').read_bytes())
    ccc = c2['tickers']['CCC']
    assert ccc['status'] == 'confirmed'
    assert (ccc['counts']['amount_mismatch'], ccc['counts']['issuer_only']) == (0, 0)
    ddd = c2['tickers']['DDD']
    assert ddd['status'] == 'unresolved'
    assert ddd['counts']['yahoo_only'] == 1  # the uncorrected 2017-11-30 event remains


def test_cli_corrections_output_feeds_reconcile(tmp_path, capsys, no_network):
    from alpha_lab.__main__ import main
    reconcile(tmp_path, source(tmp_path), evidence(tmp_path))
    [target] = (tmp_path / 'data/reconciliation').iterdir()
    main(['corrections', str(target.relative_to(tmp_path)), '--root', str(tmp_path)])
    from pathlib import Path
    out = capsys.readouterr().out.strip()
    derived = Path(out)
    assert (derived / 'corrections.json').exists()
    rows = [json.loads(x) for x in (tmp_path / 'experiments/EXPERIMENT_LOG.jsonl').read_text(encoding='utf-8').splitlines()]
    assert [r['event'] for r in rows] == ['started', 'completed', 'started', 'completed']


def hand_reconciliation(root, comparison, name='r', **metadata):
    """A frozen reconciliation-shaped snapshot built directly from a comparison dict."""
    return freeze(root / f'data/reconciliation/{name}',
                  {'comparison.json': canonical_bytes(comparison), 'payable.json': canonical_bytes({})},
                  {'evidence_snapshot': 'data/evidence/e'} | metadata)


@pytest.mark.parametrize('ticker,kind,date', [('HYG', 'issuer_only', '2012-10-31'),
                                              ('LQD', 'amount_mismatch', '2023-12-13')])
def test_corrections_run_rejects_payable_before_ex_date(tmp_path, ticker, kind, date, no_network):
    c = comparison_fixture()
    c['tickers'][ticker][kind][0]['payable_date'] = date
    with pytest.raises(ValueError, match='payable date precedes the ex-date'):
        co.corrections_run(tmp_path, hand_reconciliation(tmp_path, c))
    rows = [json.loads(x) for x in (tmp_path / 'experiments/EXPERIMENT_LOG.jsonl').read_text(encoding='utf-8').splitlines()]
    assert [r['event'] for r in rows] == ['started', 'failed']
    assert not (tmp_path / 'data/corrections').exists()


def test_corrections_provenance_and_corrected_reconciliation_is_refused(tmp_path, no_network):
    first = reconcile(tmp_path, source(tmp_path), evidence(tmp_path))
    m1 = verify(first)['metadata']
    assert (m1['corrections_sha256'], m1['corrections_path'], m1['corrections_vintage_run_id']) == (
        NO_CORRECTIONS_SHA256, None, None)
    derived = co.corrections_run(tmp_path, first)
    cfile = derived / 'corrections.json'

    s2, e2 = source(tmp_path, 'cd2'), evidence(tmp_path, 'cd2')
    second = reconcile(tmp_path, s2, e2, corrections=cfile)
    m2 = verify(second)['metadata']
    vintage = f'data/corrections/{derived.name}'
    assert m2['corrections_sha256'] == sha256(cfile.read_bytes())
    assert (m2['corrections_path'], m2['corrections_vintage'], m2['corrections_vintage_run_id']) == (
        f'{vintage}/corrections.json', vintage, derived.name)
    rows = [json.loads(x) for x in (tmp_path / 'experiments/EXPERIMENT_LOG.jsonl').read_text(encoding='utf-8').splitlines()]
    done = [r for r in rows if r['event'] == 'completed' and r['purpose'] == 'N1 issuer distribution reconciliation'][-1]
    assert (done['corrections_sha256'], done['corrections_path']) == (m2['corrections_sha256'], f'{vintage}/corrections.json')

    # A reconciliation made on an already corrected frame cannot seed another corrections vintage.
    with pytest.raises(ValueError, match='produced with corrections'):
        co.corrections_run(tmp_path, second)
    assert [r['event'] for r in [json.loads(x) for x in (
        tmp_path / 'experiments/EXPERIMENT_LOG.jsonl').read_text(encoding='utf-8').splitlines()]][-2:] == ['started', 'failed']

    # The derived snapshot records the same provenance, and the hash equals its frozen corrections.json.
    d = audit_snapshot(tmp_path, s2, payable=derived / 'payable.json', corrections=cfile)
    dm = verify(d)
    assert dm['metadata']['corrections_sha256'] == dm['files']['corrections.json'] == sha256(cfile.read_bytes())
    assert (dm['metadata']['corrections_path'], dm['metadata']['corrections_vintage_run_id']) == (
        f'{vintage}/corrections.json', derived.name)

    # An edited vintage file is refused through the vintage manifest.
    cfile.write_bytes(b'{}\n')
    with pytest.raises(ValueError, match='content hash mismatch'):
        audit_snapshot(tmp_path, source(tmp_path, 'cd3'), corrections=cfile)


def journal(root):
    return [json.loads(x) for x in (root / 'experiments/EXPERIMENT_LOG.jsonl').read_text(encoding='utf-8').splitlines()]


def test_audit_refuses_corrections_of_another_source_snapshot(tmp_path, no_network):
    first = reconcile(tmp_path, source(tmp_path), evidence(tmp_path))
    derived = co.corrections_run(tmp_path, first)
    # Same universe and prices, different manifest (retrieved_at): the vintage was not derived from this snapshot.
    other = source(tmp_path, 'other', retrieved_at='2026-10-07T00:00:00+00:00')
    with pytest.raises(ValueError, match='corrections vintage was derived from another source snapshot'):
        audit_snapshot(tmp_path, other, payable=derived / 'payable.json', corrections=derived / 'corrections.json')
    rows = journal(tmp_path)
    assert [r['event'] for r in rows][-2:] == ['started', 'failed']
    assert not (tmp_path / 'data/derived').exists()
    # The snapshot the reconciliation was made on is accepted.
    audit_snapshot(tmp_path, source(tmp_path, 'cd2'), payable=derived / 'payable.json',
                   corrections=derived / 'corrections.json')


def test_audit_refuses_payable_from_another_corrections_vintage(tmp_path, no_network):
    s = source(tmp_path)
    first = reconcile(tmp_path, s, evidence(tmp_path))
    a = co.corrections_run(tmp_path, first)
    b = co.corrections_run(tmp_path, reconcile(tmp_path, s, evidence(tmp_path, 'cd2')))
    assert a != b
    with pytest.raises(ValueError, match='payable and corrections belong to different vintages'):
        audit_snapshot(tmp_path, s, payable=a / 'payable.json', corrections=b / 'corrections.json')
    assert [r['event'] for r in journal(tmp_path)][-2:] == ['started', 'failed']
    # Same vintage, and a hand-written payable next to a vintage corrections file, are both accepted.
    audit_snapshot(tmp_path, s, payable=b / 'payable.json', corrections=b / 'corrections.json')
    audit_snapshot(tmp_path, s, payable={}, corrections=b / 'corrections.json')


def test_blank_issuer_amount_never_derives_a_remove(tmp_path, no_network):
    """parse -> compare -> derive: DDD 2017-11-29 has a Yahoo event and an SSGA row with all amounts blank."""
    rows = [['DDD Fund', 'DDD', 'x', '11/29/2017', '11/30/2017', '12/05/2017', '', '', '', 'Monthly'],
            ['DDD Fund', 'DDD', 'x', '12/01/2017', '12/04/2017', '12/08/2017', '0.03', '', '', 'Monthly']]
    files = {'ssga.xlsx': xlsx(rows)}
    sources = [dict(id='ssga', file='ssga.xlsx', url='https://issuer.test/ssga.xlsx', kind='ssga_xlsx',
                    tickers=['DDD'], amount_basis='as_traded', retrieved_at='2026-10-06T00:00:00',
                    sha256=sha256(files['ssga.xlsx']), http_status=200, status='completed')]
    blank = freeze(tmp_path / 'data/evidence/blank', files, {'sources': sources})
    with pytest.raises(ValueError, match='no distribution amount'):
        reconcile(tmp_path, source(tmp_path), blank)
    assert [r['event'] for r in journal(tmp_path)] == ['started', 'failed']
    assert not (tmp_path / 'data/reconciliation').exists()


def test_reconcile_refuses_corrections_of_another_source_snapshot(tmp_path, no_network):
    first = reconcile(tmp_path, source(tmp_path), evidence(tmp_path))
    derived = co.corrections_run(tmp_path, first)
    other = source(tmp_path, 'other', retrieved_at='2026-10-07T00:00:00+00:00')
    with pytest.raises(ValueError, match='corrections vintage was derived from another source snapshot'):
        reconcile(tmp_path, other, evidence(tmp_path, 'cd2'), corrections=derived / 'corrections.json')
    assert [r['event'] for r in journal(tmp_path)][-2:] == ['started', 'failed']
    assert len(list((tmp_path / 'data/reconciliation').iterdir())) == 1
    # The snapshot the corrections descend from is still accepted.
    reconcile(tmp_path, source(tmp_path, 'cd2'), evidence(tmp_path, 'cd3'), corrections=derived / 'corrections.json')


def corrected_derived(root):
    """source -> reconcile -> corrections vintage -> audit; returns (vintage, derived snapshot)."""
    vintage = co.corrections_run(root, reconcile(root, source(root), evidence(root)))
    derived = audit_snapshot(root, source(root, 'cd2'), payable=vintage / 'payable.json',
                             corrections=vintage / 'corrections.json')
    return vintage, derived


def test_corrections_copy_in_a_derived_snapshot_is_accepted(tmp_path, no_network):
    _, derived = corrected_derived(tmp_path)
    target = reconcile(tmp_path, source(tmp_path, 'cd3'), evidence(tmp_path, 'cd3'),
                       corrections=derived / 'corrections.json')
    assert json.loads((target / 'comparison.json').read_bytes())['tickers']['CCC']['status'] == 'confirmed'
    audit_snapshot(tmp_path, source(tmp_path, 'cd4'), payable=derived / 'payable.json',
                   corrections=derived / 'corrections.json')


def test_corrections_copy_in_a_derived_snapshot_of_another_source_is_refused(tmp_path, no_network):
    _, derived = corrected_derived(tmp_path)
    other = source(tmp_path, 'other', retrieved_at='2026-10-07T00:00:00+00:00')
    with pytest.raises(ValueError, match='derived snapshot was built from another source snapshot'):
        reconcile(tmp_path, other, evidence(tmp_path, 'cd3'), corrections=derived / 'corrections.json')
    assert [r['event'] for r in journal(tmp_path)][-2:] == ['started', 'failed']


def test_derived_snapshot_disagreeing_with_its_corrections_vintage_is_refused(tmp_path, no_network):
    vintage, derived = corrected_derived(tmp_path)
    meta = verify(derived)['metadata']
    # A hand-made derived-like snapshot citing the real vintage, but holding other corrections.
    fake = freeze(tmp_path / 'data/derived/fake', {'corrections.json': canonical_bytes({})},
                  {k: meta[k] for k in ['source_snapshot', 'source_manifest_sha256', 'corrections_vintage']})
    with pytest.raises(ValueError, match='corrections differ from the corrections vintage'):
        reconcile(tmp_path, source(tmp_path, 'cd3'), evidence(tmp_path, 'cd3'), corrections=fake / 'corrections.json')


def test_corrections_in_an_unrecognized_snapshot_are_refused(tmp_path, no_network):
    unknown = freeze(tmp_path / 'data/other/u', {'corrections.json': canonical_bytes({})}, {'note': 'x'})
    with pytest.raises(ValueError, match='neither a corrections vintage nor a derived snapshot'):
        reconcile(tmp_path, source(tmp_path), evidence(tmp_path), corrections=unknown / 'corrections.json')
    assert [r['event'] for r in journal(tmp_path)][-2:] == ['started', 'failed']


def test_derived_corrections_with_payable_of_another_snapshot_are_refused(tmp_path, no_network):
    vintage, derived = corrected_derived(tmp_path)
    with pytest.raises(ValueError, match='payable and corrections belong to different snapshots'):
        audit_snapshot(tmp_path, source(tmp_path, 'cd3'), payable=vintage / 'payable.json',
                       corrections=derived / 'corrections.json')
    assert [r['event'] for r in journal(tmp_path)][-2:] == ['started', 'failed']


def fake_derived(root, name, corrections, vintage_ref):
    """Derived-like snapshot for the cited source, holding `corrections` and citing `vintage_ref`."""
    s = source(root, name)
    return s, freeze(root / f'data/derived/{name}', {'corrections.json': canonical_bytes(corrections)},
                     {'source_snapshot': f'data/snapshots/{name}', 'corrections_vintage': vintage_ref,
                      'source_manifest_sha256': sha256((s / 'manifest.json').read_bytes())})


@pytest.mark.parametrize('ref,match', [('data/derived/loop', 'does not cite a corrections vintage'),
                                       (7, 'corrections_vintage must be a project path or None'),
                                       ('../outside', 'snapshot outside project')],
                         ids=['self_reference', 'not_a_string', 'outside_project'])
def test_derived_snapshot_with_a_bad_vintage_reference_is_refused(tmp_path, ref, match, no_network):
    s, fake = fake_derived(tmp_path, 'loop', {}, ref)
    with pytest.raises(ValueError, match=match):
        reconcile(tmp_path, s, evidence(tmp_path), corrections=fake / 'corrections.json')
    assert [r['event'] for r in journal(tmp_path)][-2:] == ['started', 'failed']


def test_derived_snapshot_without_a_vintage_is_accepted(tmp_path, no_network):
    s, fake = fake_derived(tmp_path, 'plain', {}, None)
    reconcile(tmp_path, s, evidence(tmp_path), corrections=fake / 'corrections.json')
