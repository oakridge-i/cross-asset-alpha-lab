"""N4 hypothesis report: verification of the six H1/H2 runs (spec section 7, items 1-7).

Run files are read as text and only the columns the report may read (spec section 7, last paragraph); daily.csv is
never opened by this module. Error messages name the rule, the configuration and, where applicable, the session and
ticker, and never carry a field value."""
from collections import Counter, namedtuple
from contextlib import contextmanager
import csv
from datetime import date, timedelta
from itertools import groupby
import math
from pathlib import Path
import re
from alpha_lab import report
from alpha_lab.engine import PROVIDERS
from alpha_lab.market import VINTAGE_MANIFEST_SHA256
from alpha_lab.normalize import calendar
from alpha_lab.pipeline import project_path
from alpha_lab.provenance import Run, canonical_bytes

HYPOTHESES = ('H1_252_3', 'H1_252_4', 'H1_126_3', 'H1_126_4', 'H2_4of6', 'H2_5of6')
PURPOSE = 'N4 hypothesis run'
REPORT_PURPOSE = 'N4 hypothesis report'
# Spec 4.6, held here independently of the provider registry.
PARAMETERS = {'H1_252_3': {'lookback': 252, 'k': 3}, 'H1_252_4': {'lookback': 252, 'k': 4},
              'H1_126_3': {'lookback': 126, 'k': 3}, 'H1_126_4': {'lookback': 126, 'k': 4},
              'H2_4of6': {'h': 4, 'parent': 'H1_252_3'}, 'H2_5of6': {'h': 5, 'parent': 'H1_252_3'}}
K = {'H1_252_3': 3, 'H1_252_4': 4, 'H1_126_3': 3, 'H1_126_4': 4, 'H2_4of6': 3, 'H2_5of6': 3}
H = {'H2_4of6': 4, 'H2_5of6': 5}
PARENT = 'H1_252_3'
PAIRS = (('H1_252_3', 'H1_252_4'), ('H1_126_3', 'H1_126_4'))
EXPECTED_START = '2008-12-31'
EXPECTED_END = '2022-12-30'
EXPECTED_SCENARIO = {'cost': 0.001, 'lag': 1, 'reserve': 0.01, 'proxy_pay_days': 10}
EXPECTED_CASH = 100000.0
DECISION_MONTHS = ('2008-12', '2022-11')
ABS_TOL = 1e-9
REL_TOL = 1e-8
FAILURES_SHOWN = 20

# Universe, caps and file layouts, held independently of the producing code (protocol lines 66-73, spec 4.5, 5.3).
CASH = 'BIL'
RISKY = ('DBC', 'EEM', 'EFA', 'GLD', 'HYG', 'IEF', 'LQD', 'SPY', 'TLT')
TICKERS = tuple(sorted((*RISKY, CASH)))
GROUPS = {'Equity': ('SPY', 'EFA', 'EEM'), 'Treasury': ('IEF', 'TLT'), 'Credit': ('LQD', 'HYG'),
          'Real': ('GLD', 'DBC')}
ETF_CAP = 0.25
GROUP_CAP = 0.50
RUN_FILES = {'config.json', 'decisions.csv', 'orders.csv', 'trades.csv', 'payouts.csv', 'daily.csv',
             'invariants.json', 'weights.csv', 'signals.csv'}
WEIGHT_COLUMNS = ('decision_session', *(f'w_{t}' for t in TICKERS), 'usd')
SIGNAL_COLUMNS_H1 = ('decision_session', 'ticker', 'momentum', 'sigma', 'score', 'eligible', 'rank', 'selected', 'q',
                     'v', 'scale', 'weight')
EXCESS = tuple(f'excess_{j}' for j in range(1, 7))
SIGNAL_COLUMNS_H2 = (*SIGNAL_COLUMNS_H1, 'parent_weight', *EXCESS, 'positive_months', 'filter_pass')
PARENT_FIELDS = ('momentum', 'sigma', 'score', 'eligible', 'rank', 'selected', 'q', 'v', 'scale')
PAIR_FIELDS = ('momentum', 'score', 'eligible', 'rank')
PERMITTED = {'decisions.csv': ('decision_session', 'execution_session', 'turnover', 'buy_fill'),
             'orders.csv': ('execution_session', 'status', 'cancel_reason'),
             'trades.csv': ('session', 'side'),
             'payouts.csv': ('ex_session', 'status', 'pay_basis')}

RunFiles = namedtuple('RunFiles', 'path config decisions weights signals orders trades payouts invariants')

NUMBER = re.compile(r'-?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?')
INTEGER = re.compile(r'\d+')


def close_rel(a, b):
    """|a - b| <= REL_TOL * max(|a|, |b|); exact when both are 0."""
    return abs(a - b) <= REL_TOL * max(abs(a), abs(b))


def _months():
    first = date.fromisoformat(DECISION_MONTHS[0] + '-01')
    year, month = (int(x) for x in DECISION_MONTHS[1].split('-'))
    after = date(year + month // 12, month % 12 + 1, 1)
    return first, after


def _xnys_sessions():
    """XNYS sessions from the first decision month to two weeks after the last."""
    first, after = _months()
    return [d.date().isoformat() for d in calendar(first, after + timedelta(days=14)).sessions]


def expected_decisions():
    """The last XNYS session of each month in DECISION_MONTHS, in order."""
    after = _months()[1].isoformat()
    last = {}
    for session in _xnys_sessions():
        if session < after:
            last[session[:7]] = session
    return list(last.values())


def _next_session():
    sessions = _xnys_sessions()
    return dict(zip(sessions, sessions[1:]))


@contextmanager
def rule(item, name):
    """Prefix a structural failure with its item and configuration; malformed data is a failed check."""
    try:
        with report.well_formed(name):
            yield
    except ValueError as exc:
        raise ValueError(f'item {item}, {name}: {exc}') from None


def read_columns(path, columns, exact=False):
    """Rows of a CSV file restricted to the given columns, as text; with exact, the header must equal columns."""
    try:
        with path.open(newline='', encoding='utf-8') as stream:
            reader = csv.reader(stream)
            header = next(reader, None) or []
            body = list(reader)
    except (csv.Error, UnicodeDecodeError):
        raise ValueError(f'{path.name} is not a readable UTF-8 CSV file') from None
    if exact:
        report.require(header == list(columns), f'{path.name} columns are not the expected layout')
    report.require(len(set(header)) == len(header), f'{path.name} has repeated columns')
    missing = [c for c in columns if c not in header]
    report.require(not missing, f'{path.name} lacks the columns {missing}')
    at = [header.index(c) for c in columns]
    rows = []
    for line, row in enumerate(body, 2):
        report.require(len(row) == len(header), f'{path.name} line {line} does not have {len(header)} fields')
        rows.append({c: row[i] for c, i in zip(columns, at)})
    return rows


def _difference(actual, expected):
    repeated = [s for s, n in Counter(actual).items() if n > 1]
    missing = [s for s in expected if s not in set(actual)]
    extra = [s for s in actual if s not in set(expected)]
    if missing:
        return f'missing {missing[0]}'
    if extra:
        return f'unexpected {extra[0]}'
    if repeated:
        return f'repeated {repeated[0]}'
    return 'out of order'


def _sessions_match(name, actual, expected):
    report.require(actual == expected,
                   f'{name} decision sessions are not the expected month ends ({_difference(actual, expected)})')


def _invariant_flags(invariants):
    """Flags and event lists only; the detail fields carry USD amounts and are not kept."""
    return {'passed': invariants['passed'],
            'checks': {k: v['passed'] for k, v in invariants.items() if isinstance(v, dict)},
            'split_events': invariants['split_events'], 'proxy_payouts': invariants['proxy_payouts']}


def _check_config(name, manifest, config, invariants, expected_sha256):
    """Item 4, configuration part."""
    report.require(invariants['passed'] is True, 'invariants did not pass')
    report.require(config['provider']['version'] == PROVIDERS[name].version, 'provider version is not current')
    report.require(config['manifest_sha256'] == expected_sha256 == manifest['metadata']['derived_manifest_sha256'],
                   'vintage manifest hash is not the approved one')
    fixed = {'start_session': EXPECTED_START, 'end_session': EXPECTED_END, 'scenario': EXPECTED_SCENARIO,
             'initial_cash': EXPECTED_CASH, 'decision_sessions': None}
    for key, value in fixed.items():
        report.require(canonical_bytes(config[key]) == canonical_bytes(value),
                       f'config.json {key} is not the registered value')
    report.require(canonical_bytes(config['provider']['parameters']) == canonical_bytes(PARAMETERS[name]),
                   'config.json provider parameters are not those of spec 4.6')


def _check_calendar(name, path, signal_columns):
    """Item 4, calendar part; returns the permitted columns of the run's files."""
    expected = expected_decisions()
    following = _next_session()
    decisions = read_columns(path / 'decisions.csv', PERMITTED['decisions.csv'])
    _sessions_match('decisions.csv', [r['decision_session'] for r in decisions], expected)
    for row in decisions:
        report.require(row['execution_session'] == following[row['decision_session']],
                       f'decisions.csv {row["decision_session"]}: execution_session is not the next XNYS session')
    weights = read_columns(path / 'weights.csv', WEIGHT_COLUMNS, exact=True)
    _sessions_match('weights.csv', [r['decision_session'] for r in weights], expected)
    signals = read_columns(path / 'signals.csv', signal_columns, exact=True)
    blocks = [(session, list(rows)) for session, rows in groupby(signals, key=lambda r: r['decision_session'])]
    _sessions_match('signals.csv', [s for s, _ in blocks], expected)
    for session, rows in blocks:
        tickers = [r['ticker'] for r in rows]
        if tickers != list(RISKY):
            wrong = next((a for a, b in zip(tickers, RISKY) if a != b), None)
            report.require(False, f'signals.csv {session}: rows are not the nine risky tickers in ASCII order '
                                  f'({len(tickers)} rows, first differing ticker {wrong})')
    others = {f: read_columns(path / f, PERMITTED[f]) for f in ('orders.csv', 'trades.csv', 'payouts.csv')}
    return decisions, weights, signals, others


class Failures:
    """Items 5-7 are all evaluated; the failed rules and the first failures are reported together."""

    def __init__(self):
        self.items = []

    def require(self, condition, label, name, session, ticker=None):
        if not condition:
            self.items.append((label, ' '.join(x for x in (name, session, ticker) if x)))

    def raise_any(self):
        if not self.items:
            return
        labels = list(dict.fromkeys(label for label, _ in self.items))
        shown = '; '.join(f'{label} at {where}' for label, where in self.items[:FAILURES_SHOWN])
        more = len(self.items) - FAILURES_SHOWN
        raise ValueError(f'failed checks ({", ".join(labels)}): {shown}' + (f'; and {more} more' if more > 0 else ''))


def number(text, item, name, file, session, ticker, column):
    """Float of a %.10g field; a malformed or non-finite field is reported without its text."""
    if NUMBER.fullmatch(text) is None or not math.isfinite(float(text)):
        raise ValueError(f'item {item} parse: {name} {file} {session} {ticker} {column} is not a finite number')
    return float(text)


def integer(text, item, name, file, session, ticker, column):
    if INTEGER.fullmatch(text) is None:
        raise ValueError(f'item {item} parse: {name} {file} {session} {ticker} {column} is not an integer')
    return int(text)


def flag(text, item, name, file, session, ticker, column):
    if text not in ('True', 'False'):
        raise ValueError(f'item {item} parse: {name} {file} {session} {ticker} {column} is not True or False')
    return text == 'True'


def _parse_decision(name, session, weights_row, rows):
    """Parsed weights and signal fields of one decision (item 5 parse)."""
    w = {t: number(weights_row[f'w_{t}'], 5, name, 'weights.csv', session, t, f'w_{t}') for t in TICKERS}
    usd = number(weights_row['usd'], 5, name, 'weights.csv', session, None, 'usd')
    sizing = 'parent_weight' if name in H else 'weight'
    parsed = {}
    for row in rows:
        t = row['ticker']

        def num(column):
            return number(row[column], 5, name, 'signals.csv', session, t, column)
        parsed[t] = {'momentum': num('momentum'), 'sigma': num('sigma'), 'score': num('score'), 'q': num('q'),
                     'v': num('v'), 'scale': num('scale'), 'sizing': num(sizing),
                     'eligible': flag(row['eligible'], 5, name, 'signals.csv', session, t, 'eligible'),
                     'selected': flag(row['selected'], 5, name, 'signals.csv', session, t, 'selected'),
                     'rank': None if row['rank'] == '' else integer(row['rank'], 5, name, 'signals.csv', session,
                                                                     t, 'rank')}
    return w, usd, parsed


def _check_decision(fail, name, session, weights_row, rows):
    """Item 5 for one configuration and decision."""
    w, usd, p = _parse_decision(name, session, weights_row, rows)
    for t in RISKY:
        fail.require(-ABS_TOL <= w[t] <= ETF_CAP + ABS_TOL, 'item 5 ETF cap', name, session, t)
    for group, members in GROUPS.items():
        fail.require(math.fsum(w[t] for t in members) <= GROUP_CAP + ABS_TOL, 'item 5 group cap', name, session, group)
    fail.require(abs(w[CASH] - (1 - math.fsum(w[t] for t in RISKY))) <= ABS_TOL, 'item 5 BIL remainder', name,
                 session, CASH)
    fail.require(abs(usd - (1 - math.fsum(w.values()))) <= ABS_TOL, 'item 5 usd remainder', name, session)
    fail.require(abs(usd) <= ABS_TOL, 'item 5 usd bound', name, session)
    for row in rows:
        t = row['ticker']
        fail.require(row['weight'] == weights_row[f'w_{t}'], 'item 5 weight text', name, session, t)
    for t, s in p.items():
        fail.require(s['sigma'] > 0, 'item 5 sigma positive', name, session, t)
        fail.require(s['sigma'] > 0 and close_rel(s['score'], s['momentum'] / s['sigma']), 'item 5 score', name,
                     session, t)
        fail.require(s['eligible'] == (s['score'] > 0), 'item 5 eligible', name, session, t)
        fail.require((s['rank'] is not None) == s['eligible'], 'item 5 rank presence', name, session, t)
        fail.require(s['selected'] == (s['rank'] is not None and s['rank'] <= K[name]), 'item 5 selection', name,
                     session, t)
        if s['selected']:
            fail.require(s['q'] > 0, 'item 5 q positive', name, session, t)
        else:
            fail.require(s['q'] == 0 and s['v'] == 0 and s['sizing'] == 0, 'item 5 non-selected zero', name,
                         session, t)
        fail.require(s['v'] <= min(s['q'], ETF_CAP) + ABS_TOL, 'item 5 v bound', name, session, t)
        fail.require(abs(s['sizing'] - s['scale'] * s['v']) <= ABS_TOL, 'item 5 weight scale', name, session, t)
    ranked = sorted((s['rank'], t) for t, s in p.items() if s['rank'] is not None)
    fail.require([r for r, _ in ranked] == list(range(1, len(ranked) + 1)), 'item 5 rank sequence', name, session)
    for (_, a), (_, b) in zip(ranked, ranked[1:]):
        fail.require(p[a]['score'] >= p[b]['score'], 'item 5 rank order', name, session, b)
    selected = [t for t, s in p.items() if s['selected']]
    fail.require(abs(math.fsum(s['q'] for s in p.values()) - len(selected) / K[name]) <= ABS_TOL, 'item 5 q sum', name,
                 session)
    for t in selected[1:]:
        fail.require(close_rel(p[t]['q'] * p[t]['sigma'], p[selected[0]]['q'] * p[selected[0]]['sigma']),
                     'item 5 q sigma', name, session, t)
    fail.require(len({row['scale'] for row in rows}) == 1, 'item 5 scale text', name, session)
    for t, s in p.items():
        fail.require(0 < s['scale'] <= 1 + ABS_TOL, 'item 5 scale bound', name, session, t)
    return w


def _check_across(fail, blocks):
    """Item 6, per decision and ticker."""
    for session, rows in blocks[PARENT].items():
        for t in RISKY:
            for name in HYPOTHESES:
                fail.require(blocks[name][session][t]['sigma'] == rows[t]['sigma'], 'item 6 sigma across runs', name,
                             session, t)
            for small, large in PAIRS:
                a, b = blocks[small][session][t], blocks[large][session][t]
                fail.require(all(a[f] == b[f] for f in PAIR_FIELDS), 'item 6 pair signals', large, session, t)
                fail.require(a['selected'] != 'True' or b['selected'] == 'True', 'item 6 pair subset', large, session,
                             t)


def _check_h2(fail, blocks, weights, bil):
    """Item 7, per H2 configuration, decision and ticker."""
    first, second = H
    for session, parent_rows in blocks[PARENT].items():
        for name in H:
            fail.require(bil[name][session] >= bil[PARENT][session], 'item 7 H2 BIL', name, session, CASH)
            for t in RISKY:
                row, parent = blocks[name][session][t], parent_rows[t]
                fail.require(all(row[f] == parent[f] for f in PARENT_FIELDS), 'item 7 H2 parent columns', name,
                             session, t)
                fail.require(row['parent_weight'] == parent['weight'] == weights[PARENT][session][f'w_{t}'],
                             'item 7 H2 parent weight', name, session, t)
                excess = [number(row[c], 7, name, 'signals.csv', session, t, c) for c in EXCESS]
                months = integer(row['positive_months'], 7, name, 'signals.csv', session, t, 'positive_months')
                passed = flag(row['filter_pass'], 7, name, 'signals.csv', session, t, 'filter_pass')
                fail.require(months == sum(1 for e in excess if e > 0), 'item 7 H2 positive months', name, session, t)
                fail.require(passed == (months >= H[name]), 'item 7 H2 filter', name, session, t)
                fail.require(row['weight'] == (row['parent_weight'] if passed else '0'), 'item 7 H2 weight', name,
                             session, t)
            for t in RISKY:
                a, b = blocks[first][session][t], blocks[second][session][t]
                fail.require(all(a[c] == b[c] for c in (*EXCESS, 'positive_months')), 'item 7 H2 months across runs',
                             second, session, t)


def verified_hypothesis_runs(root, run_dirs, expected_sha256, base):
    """Items 1-7 of spec section 7 in order; returns {configuration: RunFiles} holding permitted columns only."""
    root = Path(root)
    report.require(len(run_dirs) == len(HYPOTHESES),
                   f'item 1: exactly six run directories required, got {len(run_dirs)}')
    found = {}
    for d in run_dirs:
        with rule(1, Path(d).name):
            path = report.run_path(root, d)
            manifest, config = report.verify_run_dir(root, path, RUN_FILES, label='hypothesis')
            found.setdefault(config['provider']['name'], []).append((path, manifest, config))
    report.require(sorted(found) == sorted(HYPOTHESES) and all(len(v) == 1 for v in found.values()),
                   f'item 1: each of {", ".join(HYPOTHESES)} is required exactly once')
    rows = report.journal_rows(root)
    out, blocks, weights, bil = {}, {}, {}, {}
    for name in HYPOTHESES:
        path, manifest, config = found[name][0]
        with rule('2-3', name):
            started = report.check_journal(root, path, rows, config, base, PURPOSE, label='hypothesis')
            terminal = next(r for r in rows if r.get('run_id') == path.name and r['event'] != 'started')
            report.require(terminal['purpose'] == PURPOSE and terminal['candidate_ids'] == [name],
                           f'{path.name}: terminal record purpose or candidate_ids is not that of a {name} hypothesis run')
        with rule(3, name):
            report.require(report.src_tree(root, started['git_sha']) == report.src_tree(root, base['git_sha']),
                           f'{path.name}: src tree differs from the report commit')
        with rule(4, name):
            invariants = report.read_json(path / 'invariants.json')
            _check_config(name, manifest, config, invariants, expected_sha256)
            columns = SIGNAL_COLUMNS_H2 if name in H else SIGNAL_COLUMNS_H1
            decisions, weight_rows, signals, others = _check_calendar(name, path, columns)
            out[name] = RunFiles(path, config, decisions, weight_rows, signals, others['orders.csv'],
                                 others['trades.csv'], others['payouts.csv'], _invariant_flags(invariants))
        blocks[name] = {s: {r['ticker']: r for r in group} for s, group in
                        groupby(signals, key=lambda r: r['decision_session'])}
        weights[name] = {r['decision_session']: r for r in weight_rows}
    fail = Failures()
    for name in HYPOTHESES:
        bil[name] = {}
        for session, by_ticker in blocks[name].items():
            w = _check_decision(fail, name, session, weights[name][session], [by_ticker[t] for t in RISKY])
            bil[name][session] = w[CASH]
    _check_across(fail, blocks)
    _check_h2(fail, blocks, weights, bil)
    fail.raise_any()
    return out


def _verify_in_run(root, run_dirs, parent=None, expected_sha256=VINTAGE_MANIFEST_SHA256):
    """Journaled verification without output; a rejection ends the Run as failed. The report builder adds the
    document and finishes the Run."""
    root = Path(root).resolve()
    config = {'runs': [project_path(root, (root / d).resolve()) for d in run_dirs], 'expected_sha256': expected_sha256}
    with Run(root, REPORT_PURPOSE, config, parent, candidate_ids=HYPOTHESES) as run:
        return verified_hypothesis_runs(root, run_dirs, expected_sha256, run.base)
