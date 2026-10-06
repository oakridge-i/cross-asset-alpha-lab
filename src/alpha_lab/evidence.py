"""Issuer distribution evidence: acquisition into immutable snapshots and pure parsers."""
from datetime import datetime
import html
import io
import json
import math
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile
import zlib

from .pipeline import load_json
from .provenance import Run, freeze, now, sha256

EXTENSIONS = {'ssga_xlsx': '.xlsx', 'ishares_html': '.html', 'invesco_json': '.json', 'document': '.pdf'}
# as_traded: per share on the ex-date; current_units: restated per share of today's unit count.
AMOUNT_BASES = {'as_traded', 'current_units'}
USER_AGENT = 'Mozilla/5.0'
MAIN = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
RELATIONSHIP = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'
SSGA_AMOUNTS = ['DIVIDEND ($)', 'SHORT TERM CAPITAL GAIN ($)', 'LONG TERM CAPITAL GAIN ($)']
SSGA_COLUMNS = ['TICKER', 'EX-DATE', 'RECORD DATE', 'PAYABLE DATE', *SSGA_AMOUNTS]


def event(ex_date, record_date, payable_date, amount):
    if ex_date is None:
        raise ValueError('missing ex-date')
    amount = round(float(amount), 10)
    if not math.isfinite(amount) or amount < 0:
        raise ValueError(f'invalid distribution amount on {ex_date}')
    return dict(ex_date=ex_date, record_date=record_date, payable_date=payable_date, amount=amount)


def ordered(events):
    by_date = {}
    for e in events:
        if e['ex_date'] in by_date:
            raise ValueError(f'duplicate issuer ex-date {e["ex_date"]}')
        by_date[e['ex_date']] = e
    return [by_date[d] for d in sorted(by_date)]


def xlsx_rows(body):
    """Cells of the first worksheet as {column: text}; stdlib only (openpyxl is not a dependency)."""
    z = zipfile.ZipFile(io.BytesIO(body))
    sheet = ET.fromstring(z.read('xl/workbook.xml')).find(f'{MAIN}sheets/{MAIN}sheet')
    rels = ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
    target = next((r.get('Target') for r in rels if r.get('Id') == sheet.get(RELATIONSHIP)), None)
    if target is None:
        raise ValueError('worksheet relationship not found')
    path = target[1:] if target.startswith('/') else 'xl/' + target
    strings = []
    if 'xl/sharedStrings.xml' in z.namelist():
        strings = [''.join(t.text or '' for t in si.iter(f'{MAIN}t'))
                   for si in ET.fromstring(z.read('xl/sharedStrings.xml'))]
    for row in ET.fromstring(z.read(path)).iter(f'{MAIN}row'):
        cells = {}
        for c in row.iter(f'{MAIN}c'):
            v = c.find(f'{MAIN}v')
            if c.get('t') == 's':
                value = strings[int(v.text)]
            elif c.get('t') == 'inlineStr':
                value = ''.join(t.text or '' for t in c.iter(f'{MAIN}t'))
            else:
                value = v.text if v is not None else ''
            cells[re.match('[A-Z]+', c.get('r'))[0]] = (value or '').strip()
        yield cells


def us_date(text):
    return datetime.strptime(text, '%m/%d/%Y').date().isoformat() if text else None


def parse_ssga_xlsx(body, ticker):
    """SSGA historical distributions workbook; amounts are as-traded totals incl. capital gains."""
    try:
        rows = xlsx_rows(body)
        for row in rows:
            if 'TICKER' in row.values() and 'EX-DATE' in row.values():
                columns = {name: col for col, name in row.items()}
                break
        else:
            raise ValueError('SSGA header not found')
        if missing := set(SSGA_COLUMNS) - set(columns):
            raise ValueError(f'SSGA columns missing: {sorted(missing)}')
        events = []
        for row in rows:
            if row.get(columns['TICKER']) != ticker:
                continue
            get = lambda name: row.get(columns[name], '')
            events.append(event(us_date(get('EX-DATE')), us_date(get('RECORD DATE')),
                                us_date(get('PAYABLE DATE')), sum(float(get(n) or 0) for n in SSGA_AMOUNTS)))
    except (KeyError, IndexError, TypeError, AttributeError, EOFError, NotImplementedError,
            zlib.error, zipfile.BadZipFile, ET.ParseError) as exc:
        raise ValueError(f'malformed SSGA workbook: {exc!r}') from exc
    if not events:
        raise ValueError(f'no SSGA distributions for {ticker}')
    return ordered(events)


def tables(node):
    """Column maps {name: values} of iShares distribution tables in either embedded layout."""
    items = list(node.values()) if isinstance(node, dict) else node if isinstance(node, list) else []
    columns = {i['name']: i['value'] for i in items if isinstance(i, dict) and 'name' in i and 'value' in i}
    if 'exDate' in columns and 'totalDistribution' in columns:
        yield columns
    for item in items:
        yield from tables(item)


def ishares_date(value):
    return datetime.strptime(str(value), '%Y%m%d').date().isoformat() if value is not None else None


def parse_ishares_html(body):
    """iShares product page; components props carry the distribution table as HTML-escaped JSON."""
    found = []
    for raw in re.findall(r'componentprops="([^"]*)"', body.decode('utf-8')):
        try:
            props = json.loads(html.unescape(raw))
        except json.JSONDecodeError:
            continue
        for columns in tables(props):
            try:
                names = ['exDate', 'recordDate', 'payableDate', 'totalDistribution']
                if len({len(columns[n]) for n in names}) != 1:
                    raise ValueError('iShares column length mismatch')
                found.append(ordered(event(ishares_date(x), ishares_date(r),
                                           ishares_date(p), a) for x, r, p, a in zip(*(columns[n] for n in names))))
            except (KeyError, TypeError) as exc:
                raise ValueError(f'malformed iShares table: {exc!r}') from exc
    if not found or not found[0]:
        raise ValueError('iShares distribution table not found or empty')
    if any(table != found[0] for table in found):
        raise ValueError('inconsistent iShares distribution tables')
    return found[0]


def parse_invesco_json(body):
    """Invesco distribution API capture (browser-fetched; the API itself refuses non-browser clients)."""
    try:
        data = json.loads(body)
        events = [event(d['exDate'], d.get('recordDate'), d.get('payDate'), d['distributionAmountPerUnit'])
                  for d in data['distributions']]
    except (KeyError, TypeError, json.JSONDecodeError) as exc:
        raise ValueError(f'malformed Invesco distribution JSON: {exc!r}') from exc
    if not events:
        raise ValueError('no Invesco distributions')
    return ordered(events)


def check(source, body):
    if source['kind'] == 'ssga_xlsx':
        for ticker in source['tickers']:
            parse_ssga_xlsx(body, ticker)
    elif source['kind'] == 'ishares_html':
        if len(source['tickers']) != 1:
            raise ValueError('an iShares page covers exactly one ticker')
        parse_ishares_html(body)
    elif source['kind'] == 'invesco_json':
        if len(source['tickers']) != 1:
            raise ValueError('an Invesco capture covers exactly one ticker')
        parse_invesco_json(body)
    elif not body.startswith(b'%PDF'):
        raise ValueError('document is not a PDF')


def fetch_evidence(root, config, parent=None):
    """config is a dict or a path relative to root."""
    root = Path(root).resolve()
    if isinstance(config, Path):
        config = load_json(root, config, 'N1 issuer evidence acquisition', {}, parent)
    with Run(root, 'N1 issuer evidence acquisition', config, parent) as run:
        import requests
        ids = [s['id'] for s in config['sources']]
        if len(set(ids)) != len(ids) or any(s['kind'] not in EXTENSIONS for s in config['sources']):
            raise ValueError('duplicate source id or unsupported source kind')
        if any(s['kind'] != 'document' and s.get('amount_basis') not in AMOUNT_BASES for s in config['sources']):
            raise ValueError(f'distribution sources need amount_basis in {sorted(AMOUNT_BASES)}')
        target = root / 'data/evidence' / run.run_id
        run.base['output_paths'] = [target.relative_to(root).as_posix()]
        files, sources = {}, []
        try:
            for s in config['sources']:
                entry = dict(id=s['id'], file=None, url=s['url'], kind=s['kind'], tickers=s['tickers'],
                             amount_basis=s.get('amount_basis'), local_capture=s.get('local_capture'),
                             no_distributions=s.get('no_distributions'), statements=s.get('statements'),
                             basis=s.get('basis'), retrieved_at=None, sha256=None, http_status=None, status='failed')
                sources.append(entry)
                if 'local_capture' in s:
                    # A manually captured file (e.g. a browser fetch of an API that refuses non-browser
                    # clients) is copied, never requested over the network, and must stay inside the project.
                    try:
                        local_path = (root / s['local_capture']).resolve()
                        if not local_path.is_relative_to(root):
                            raise ValueError(f'local capture outside project: {s["local_capture"]}')
                        body = local_path.read_bytes()
                        meta = json.loads(local_path.with_suffix('.capture.json').read_bytes())
                    except (OSError, ValueError, json.JSONDecodeError) as exc:
                        entry['error'] = f'{type(exc).__name__}: {exc}'
                        continue
                    name = s['id'] + EXTENSIONS[s['kind']]
                    files[name] = body
                    entry.update(retrieved_at=meta.get('captured_at_utc'), file=name, sha256=sha256(body))
                    try:
                        if entry['sha256'] != s['sha256']:
                            raise ValueError(f'local capture sha256 mismatch for {s["id"]}')
                        check(s, body)
                        entry['status'] = 'completed'
                    except Exception as exc:  # any check failure marks the source, never loses the snapshot
                        entry['error'] = f'{type(exc).__name__}: {exc}'
                    continue
                try:
                    # Verified TLS (certifi); a fresh session per request keeps no cookies.
                    response = requests.get(s['url'], headers={'User-Agent': USER_AGENT}, timeout=60)
                except requests.RequestException as exc:
                    entry['error'] = f'{type(exc).__name__}: {exc}'
                    continue
                status = response.status_code
                # Every received body is evidence; non-200 bodies are kept under a failure name.
                name = s['id'] + (EXTENSIONS[s['kind']] if status == 200 else f'.http{status}')
                files[name] = response.content
                entry.update(retrieved_at=now(), http_status=status, file=name, sha256=sha256(response.content))
                try:
                    if status != 200:
                        raise ValueError(f'HTTP {status}')
                    check(s, response.content)
                    entry['status'] = 'completed'
                except Exception as exc:  # any parser failure marks the source, never loses the snapshot
                    entry['error'] = f'{type(exc).__name__}: {exc}'
        finally:
            freeze(target, files, {'config': config, 'environment': run.env, 'run_id': run.run_id,
                                   'git_sha': run.base['git_sha'], 'sources': sources})
            run.base['data_sha256'] = sha256((target / 'manifest.json').read_bytes())
            run.base['null_reasons']['data_sha256'] = None
        if failed := [s['id'] for s in sources if s['status'] != 'completed']:
            raise RuntimeError(f'evidence sources failed: {", ".join(failed)}')
        run.finish('completed', run.base['output_paths'], run.base['data_sha256'], [])
    return target
