import html
import io
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import threading
import zipfile
import pytest
from alpha_lab import evidence as e
from alpha_lab.provenance import verify

MAIN = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
HEADER = ['FUND NAME', 'TICKER', 'CUSIP', 'EX-DATE', 'RECORD DATE', 'PAYABLE DATE', 'DIVIDEND ($)',
          'SHORT TERM CAPITAL GAIN ($)', 'LONG TERM CAPITAL GAIN ($)', 'FREQUENCY']


def xlsx(rows):
    """Minimal SSGA-like workbook: all cells are shared strings, empty strings are omitted cells."""
    strings, sheet = [], []
    for r, row in enumerate([HEADER] + rows, 1):
        cells = []
        for c, value in enumerate(row):
            if value == '':
                continue
            if value not in strings:
                strings.append(value)
            cells.append(f'<c r="{"ABCDEFGHIJ"[c]}{r}" t="s"><v>{strings.index(value)}</v></c>')
        sheet.append(f'<row r="{r}">{"".join(cells)}</row>')
    parts = {
        'xl/workbook.xml': f'<workbook xmlns="{MAIN}" xmlns:r="http://schemas.openxmlformats.org/'
                           'officeDocument/2006/relationships"><sheets><sheet name="dividend" sheetId="1" '
                           'r:id="rId1"/></sheets></workbook>',
        'xl/_rels/workbook.xml.rels': '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/'
                                      'relationships"><Relationship Id="rId1" Target="worksheets/sheet1.xml" '
                                      'Type="worksheet"/></Relationships>',
        'xl/sharedStrings.xml': f'<sst xmlns="{MAIN}">'
                                + ''.join(f'<si><t>{html.escape(s)}</t></si>' for s in strings) + '</sst>',
        'xl/worksheets/sheet1.xml': f'<worksheet xmlns="{MAIN}"><sheetData>{"".join(sheet)}</sheetData></worksheet>'}
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as z:
        for name, text in parts.items():
            # Fixed timestamps keep the workbook bytes, and so its sha256, deterministic.
            z.writestr(zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0)), text)
    return buffer.getvalue()


SSGA_ROWS = [
    ['SPDR S&P 500', 'SPY', '78462F103', '09/18/2026', '09/18/2026', '10/30/2026', '1.888834', '', '', 'Quarterly'],
    ['SPDR S&P 500', 'SPY', '78462F103', '12/19/2008', '12/23/2008', '01/30/2009', '0.698', '0.080000', '0.040000', 'Quarterly'],
    ['SPDR T-Bill', 'BIL', '78468R663', '07/02/2007', '07/05/2007', '07/11/2007', '0.203102', '', '', 'Monthly'],
]


def test_ssga_total_includes_capital_gains_and_filters_ticker():
    assert e.parse_ssga_xlsx(xlsx(SSGA_ROWS), 'SPY') == [
        {'ex_date': '2008-12-19', 'record_date': '2008-12-23', 'payable_date': '2009-01-30', 'amount': 0.818},
        {'ex_date': '2026-09-18', 'record_date': '2026-09-18', 'payable_date': '2026-10-30', 'amount': 1.888834}]
    assert e.parse_ssga_xlsx(xlsx(SSGA_ROWS), 'BIL') == [
        {'ex_date': '2007-07-02', 'record_date': '2007-07-05', 'payable_date': '2007-07-11', 'amount': 0.203102}]


@pytest.mark.parametrize('rows', [[], [SSGA_ROWS[0], SSGA_ROWS[0]], [SSGA_ROWS[0][:3] + ['2026-09-18'] + SSGA_ROWS[0][4:]]],
                         ids=['absent', 'duplicate', 'iso_date'])
def test_ssga_missing_duplicate_or_malformed_fails_closed(rows):
    with pytest.raises(ValueError):
        e.parse_ssga_xlsx(xlsx(rows), 'SPY')


def table(total=('0.350802', '0.648931')):
    return {'exDate': [20260615, 20071224], 'recordDate': [20260615, None], 'payableDate': [20260618, 20080104],
            'incomeAmount': ['0.350802', '0.6489'], 'totalDistribution': list(total)}


def page(first, second):
    perf = {'containersByNameMap': {'distributions': {'subContainersByNameMap': {'table': {'dataPointsByNameMap': {
        k: {'name': k, 'fullName': f'performance.distributions.table.{k}', 'value': v} for k, v in first.items()}}}}}}
    dist = {'distributionTableData': [{'name': k, 'value': v} for k, v in second.items()]}
    return ''.join(f'<div><walrus-render-on-client componentprops="{html.escape(json.dumps(x))}"></walrus-render-on-client></div>'
                   for x in [{'unrelated': True}, perf, dist]).encode()


def test_ishares_page_uses_total_distribution():
    assert e.parse_ishares_html(page(table(), table())) == [
        {'ex_date': '2007-12-24', 'record_date': None, 'payable_date': '2008-01-04', 'amount': 0.648931},
        {'ex_date': '2026-06-15', 'record_date': '2026-06-15', 'payable_date': '2026-06-18', 'amount': 0.350802}]


@pytest.mark.parametrize('body', [b'<html>Access Denied</html>', page(table(), table(('0.350802', '0.7'))),
                                  page(*[dict.fromkeys(['exDate', 'recordDate', 'payableDate', 'totalDistribution'], [])] * 2)],
                         ids=['no_table', 'inconsistent', 'empty'])
def test_ishares_missing_or_inconsistent_table_fails_closed(body):
    with pytest.raises(ValueError):
        e.parse_ishares_html(body)


def corrupted_xlsx():
    """Deflate-compressed workbook whose workbook.xml stream is damaged (zlib.error on read)."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(xlsx(SSGA_ROWS))) as src, zipfile.ZipFile(buffer, 'w') as dst:
        for name in src.namelist():
            dst.writestr(zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0)), src.read(name), zipfile.ZIP_DEFLATED)
    body = bytearray(buffer.getvalue())
    info = zipfile.ZipFile(io.BytesIO(bytes(body))).getinfo('xl/workbook.xml')
    start = info.header_offset + 30 + len(info.filename)
    body[start:start + 4] = bytes([255]) * 4
    return bytes(body)


def test_corrupted_workbook_raises_value_error():
    with pytest.raises(ValueError, match='malformed SSGA workbook'):
        e.parse_ssga_xlsx(corrupted_xlsx(), 'SPY')


@pytest.fixture
def server():
    routes = {'/ssga.xlsx': (200, xlsx(SSGA_ROWS)), '/eem': (200, page(table(), table())),
              '/memo.pdf': (200, b'%PDF-1.4 memo'), '/blocked': (403, b'Access Denied'),
              '/corrupt.xlsx': (200, corrupted_xlsx())}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            status, body = routes.get(self.path, (404, b'missing'))
            self.send_response(status)
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    httpd = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield f'http://127.0.0.1:{httpd.server_address[1]}'
    httpd.shutdown()
    httpd.server_close()


def config(url, *extra):
    return {'protocol_version': '1.0', 'sources': [
        {'id': 'ssga', 'url': f'{url}/ssga.xlsx', 'kind': 'ssga_xlsx', 'tickers': ['SPY', 'BIL'],
         'amount_basis': 'as_traded'},
        {'id': 'eem', 'url': f'{url}/eem', 'kind': 'ishares_html', 'tickers': ['EEM'], 'amount_basis': 'current_units'},
        {'id': 'memo', 'url': f'{url}/memo.pdf', 'kind': 'document', 'tickers': ['EEM']}, *extra]}


def events(root):
    return [json.loads(x)['event'] for x in (root / 'experiments/EXPERIMENT_LOG.jsonl').read_text().splitlines()]


def test_fetch_freezes_sources_with_metadata(tmp_path, server):
    target = e.fetch_evidence(tmp_path, config(server))
    m = verify(target)
    assert target.parent == tmp_path / 'data/evidence'
    assert sorted(m['files']) == ['eem.html', 'memo.pdf', 'ssga.xlsx']
    assert [(s['id'], s['file'], s['kind'], s['tickers'], s['http_status'], s['status'], s['sha256'])
            for s in m['metadata']['sources']] == [
        ('ssga', 'ssga.xlsx', 'ssga_xlsx', ['SPY', 'BIL'], 200, 'completed', m['files']['ssga.xlsx']),
        ('eem', 'eem.html', 'ishares_html', ['EEM'], 200, 'completed', m['files']['eem.html']),
        ('memo', 'memo.pdf', 'document', ['EEM'], 200, 'completed', m['files']['memo.pdf'])]
    assert all(s['retrieved_at'] for s in m['metadata']['sources'])
    assert [s['amount_basis'] for s in m['metadata']['sources']] == ['as_traded', 'current_units', None]
    assert events(tmp_path) == ['started', 'completed']


def test_fetch_requires_amount_basis_for_distribution_sources(tmp_path, no_network):
    cfg = config('https://issuer.test')
    del cfg['sources'][1]['amount_basis']
    with pytest.raises(ValueError, match='amount_basis'):
        e.fetch_evidence(tmp_path, cfg)
    assert events(tmp_path) == ['started', 'failed']


def test_fetch_failure_freezes_partial_evidence_and_logs_failed(tmp_path, server):
    bad = [{'id': 'blocked', 'url': f'{server}/blocked', 'kind': 'ishares_html', 'tickers': ['EFA'],
            'amount_basis': 'current_units'},
           {'id': 'fake', 'url': f'{server}/eem', 'kind': 'document', 'tickers': ['EEM']},
           {'id': 'corrupt', 'url': f'{server}/corrupt.xlsx', 'kind': 'ssga_xlsx', 'tickers': ['SPY'],
            'amount_basis': 'as_traded'}]
    with pytest.raises(RuntimeError, match='blocked, fake, corrupt'):
        e.fetch_evidence(tmp_path, config(server, *bad))
    [target] = (tmp_path / 'data/evidence').iterdir()
    m = verify(target)
    assert sorted(m['files']) == ['blocked.http403', 'corrupt.xlsx', 'eem.html', 'fake.pdf', 'memo.pdf', 'ssga.xlsx']
    assert (target / 'blocked.http403').read_bytes() == b'Access Denied'
    status = {s['id']: (s['status'], s['http_status'], s['file']) for s in m['metadata']['sources']}
    assert status['blocked'] == ('failed', 403, 'blocked.http403')
    assert status['corrupt'] == ('failed', 200, 'corrupt.xlsx')
    assert all(s['sha256'] == m['files'][s['file']] for s in m['metadata']['sources'])
    assert status['fake'] == ('failed', 200, 'fake.pdf')
    assert status['ssga'] == ('completed', 200, 'ssga.xlsx')
    rows = [json.loads(x) for x in (tmp_path / 'experiments/EXPERIMENT_LOG.jsonl').read_text().splitlines()]
    assert [r['event'] for r in rows] == ['started', 'failed']
    assert rows[-1]['output_paths'] == [target.relative_to(tmp_path).as_posix()]
    assert rows[-1]['data_sha256'] is not None


def test_registered_evidence_config_is_well_formed():
    from pathlib import Path
    cfg = json.loads((Path(__file__).parents[1] / 'configs/n1_evidence.json').read_bytes())
    ids = [s['id'] for s in cfg['sources']]
    assert len(set(ids)) == len(ids)
    assert all(s['kind'] in e.EXTENSIONS and s['url'].startswith('https://') for s in cfg['sources'])
    covered = {t for s in cfg['sources'] if s['kind'] != 'document' for t in s['tickers']}
    assert covered == {'SPY', 'BIL', 'EFA', 'EEM', 'IEF', 'TLT', 'LQD', 'HYG'}
    assert all(len(s['tickers']) == 1 for s in cfg['sources'] if s['kind'] == 'ishares_html')
    assert {s['kind']: s['amount_basis'] for s in cfg['sources'] if s['kind'] != 'document'} == {
        'ssga_xlsx': 'as_traded', 'ishares_html': 'current_units'}
