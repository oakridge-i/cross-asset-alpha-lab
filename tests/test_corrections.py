"""Deriving explicit issuer corrections from reconciliation output and applying them as a frozen vintage."""
import json
import pytest
from alpha_lab import corrections as co
from alpha_lab.provenance import freeze, sha256
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


def source(root, name='cd'):
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
                  {'config': config, 'retrieved_at': '2026-10-06T00:00:00+00:00'})


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
    rows = [json.loads(x) for x in (tmp_path / 'experiments/EXPERIMENT_LOG.jsonl').read_text().splitlines()]
    assert [r['event'] for r in rows] == ['started', 'completed', 'started', 'completed']
