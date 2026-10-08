"""N4 hypothesis report: verification of the six H1/H2 runs (spec section 7, items 1-7), the permitted diagnostics of
spec 6.2 and the frozen hypotheses.json and hypotheses.md.

Run files are read as text and only the columns the report may read (spec section 7, last paragraph); daily.csv is
never opened by this module. Error messages name the rule, the configuration and, where applicable, the session and
ticker, and never carry a field value."""
from collections import Counter, namedtuple
from contextlib import contextmanager
import csv
from datetime import date, timedelta
from itertools import groupby
import json
import math
from pathlib import Path
import re
from alpha_lab import report
from alpha_lab.engine import PROVIDERS
from alpha_lab.market import VINTAGE_MANIFEST_SHA256
from alpha_lab.normalize import calendar
from alpha_lab.pipeline import project_path
from alpha_lab.provenance import Run, canonical_bytes, freeze, sha256

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

# ASCII digits only: float() and int() also accept other Unicode decimal digits, which %.10g never writes.
NUMBER = re.compile(r'-?([0-9]+(\.[0-9]*)?|\.[0-9]+)([eE][+-]?[0-9]+)?')
INTEGER = re.compile(r'[0-9]+')


def close_rel(a, b):
    """|a - b| <= REL_TOL * max(|a|, |b|); exact when both are 0."""
    if not math.isfinite(a) or not math.isfinite(b):
        return False
    return abs(a - b) <= REL_TOL * max(abs(a), abs(b))


def _safe_fsum(values):
    """Return None when finite malformed inputs overflow the report's sum."""
    try:
        return math.fsum(values)
    except OverflowError:
        return None


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
    """Flags and event lists only; the detail fields carry USD amounts and are not kept. The check entries are the
    dict-valued keys of invariants.json."""
    return {'passed': invariants['passed'],
            'checks': {k: v['passed'] for k, v in invariants.items() if isinstance(v, dict)},
            'split_events': invariants['split_events'], 'proxy_payouts': invariants['proxy_payouts']}


def _check_invariant_flags(flags):
    """Item 4: exactly the seven checks of INVARIANT_CHECKS, each `passed` flag and the overall flag the boolean True
    (1, "true" and None are rejected). Messages name the check, never the flag value."""
    missing = [c for c in INVARIANT_CHECKS if c not in flags['checks']]
    report.require(not missing, f'invariants.json lacks the check {missing[0] if missing else ""}')
    extra = sorted(c for c in flags['checks'] if c not in INVARIANT_CHECKS)
    report.require(not extra, f'invariants.json holds the unexpected check {extra[0] if extra else ""}')
    for check in INVARIANT_CHECKS:
        report.require(flags['checks'][check] is True, f'invariants.json check {check} did not pass')
    report.require(flags['passed'] is True, 'invariants did not pass')


def _check_config(name, manifest, config, invariants, expected_sha256):
    """Item 4, configuration part; the invariant flags are checked first."""
    _check_invariant_flags(_invariant_flags(invariants))
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


def _parse_rule(item):
    """'item <n>' for a numbered rule of spec section 7; a text label (the diagnostics) is used as it is."""
    return item if isinstance(item, str) else f'item {item}'


def _where(item, name, file, session, ticker, column):
    """'<rule> parse: <configuration> <file> <session> [<ticker>] <column>'; a field without a ticker omits it."""
    return f'{_parse_rule(item)} parse: ' + ' '.join(x for x in (name, file, session, ticker, column) if x)


def number(text, item, name, file, session, ticker, column):
    """Float of a %.10g field; a malformed or non-finite field is reported without its text."""
    if NUMBER.fullmatch(text) is None or not math.isfinite(float(text)):
        raise ValueError(f'{_where(item, name, file, session, ticker, column)} is not a finite number')
    return float(text)


def integer(text, item, name, file, session, ticker, column):
    if INTEGER.fullmatch(text) is None:
        raise ValueError(f'{_where(item, name, file, session, ticker, column)} is not an integer')
    return int(text)


def flag(text, item, name, file, session, ticker, column):
    if text not in ('True', 'False'):
        raise ValueError(f'{_where(item, name, file, session, ticker, column)} is not True or False')
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


def _capped(q):
    """Steps 1 and 2 of the target weights (protocol lines 68-69), held here independently of portfolio.capped: each q
    capped at ETF_CAP, then the members of every group whose capped fsum exceeds GROUP_CAP scaled by GROUP_CAP / that
    sum, once and without reallocation."""
    c = {t: min(q[t], ETF_CAP) for t in RISKY}
    for members in GROUPS.values():
        total = _safe_fsum(c[t] for t in members)
        if total is not None and total > GROUP_CAP:
            for t in members:
                c[t] = c[t] * GROUP_CAP / total
    return c


def _check_decision(fail, name, session, weights_row, rows):
    """Item 5 for one configuration and decision."""
    w, usd, p = _parse_decision(name, session, weights_row, rows)
    capped = _capped({t: p[t]['q'] for t in RISKY})
    for t in RISKY:
        fail.require(-ABS_TOL <= w[t] <= ETF_CAP + ABS_TOL, 'item 5 ETF cap', name, session, t)
    for group, members in GROUPS.items():
        total = _safe_fsum(w[t] for t in members)
        fail.require(total is not None and total <= GROUP_CAP + ABS_TOL, 'item 5 group cap', name, session, group)
    risky_total = _safe_fsum(w[t] for t in RISKY)
    fail.require(risky_total is not None and abs(w[CASH] - (1 - risky_total)) <= ABS_TOL,
                 'item 5 BIL remainder', name, session, CASH)
    fail.require(w[CASH] >= -ABS_TOL, 'item 5 BIL non-negative', name, session, CASH)
    all_weights = _safe_fsum(w.values())
    fail.require(all_weights is not None and abs(usd - (1 - all_weights)) <= ABS_TOL,
                 'item 5 usd remainder', name, session)
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
        fail.require(abs(s['v'] - capped[t]) <= ABS_TOL, 'item 5 v capped', name, session, t)
        fail.require(abs(s['sizing'] - s['scale'] * s['v']) <= ABS_TOL, 'item 5 weight scale', name, session, t)
    ranked = sorted((s['rank'], t) for t, s in p.items() if s['rank'] is not None)
    fail.require([r for r, _ in ranked] == list(range(1, len(ranked) + 1)), 'item 5 rank sequence', name, session)
    for (_, a), (_, b) in zip(ranked, ranked[1:]):
        fail.require(p[a]['score'] >= p[b]['score'], 'item 5 rank order', name, session, b)
    selected = [t for t, s in p.items() if s['selected']]
    q_total = _safe_fsum(s['q'] for s in p.values())
    fail.require(q_total is not None and abs(q_total - len(selected) / K[name]) <= ABS_TOL, 'item 5 q sum', name,
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


def _check_trading(fail, name, decisions):
    """Item 5, decisions.csv: turnover >= 0 and 0 <= buy_fill <= 1, exact."""
    for row in decisions:
        session = row['decision_session']
        turnover = number(row['turnover'], 5, name, 'decisions.csv', session, None, 'turnover')
        buy_fill = number(row['buy_fill'], 5, name, 'decisions.csv', session, None, 'buy_fill')
        fail.require(turnover >= 0, 'item 5 turnover', name, session)
        fail.require(0 <= buy_fill <= 1, 'item 5 buy_fill', name, session)


def _src_tree(root, sha, whose):
    """report.src_tree with a message that names the record, not the journaled git_sha value."""
    try:
        return report.src_tree(root, sha)
    except ValueError:
        raise ValueError(f'cannot resolve the src tree of {whose}') from None


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
            report.require(_src_tree(root, started['git_sha'], f'{path.name} git_sha') ==
                           _src_tree(root, base['git_sha'], 'the report git_sha'),
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
        _check_trading(fail, name, out[name].decisions)
    _check_across(fail, blocks)
    _check_h2(fail, blocks, weights, bil)
    fail.raise_any()
    return out


# --- permitted diagnostics (spec 6.2) ------------------------------------------------------------------------------

INVARIANT_CHECKS = ('cash_non_negative', 'nav_identity', 'cash_flow', 'split_quantity_only', 'receivable_conservation',
                    'execution_timing', 'costs')
YEARS = tuple(str(y) for y in range(2009, 2023))
PERIODS = ('full', *YEARS)
ORDER_STATUSES = ('filled', 'partial', 'cancelled')
REASON_STATUSES = ('partial', 'cancelled')
CANCEL_REASONS = ('no_valid_open', 'insufficient_cash', 'fractional_quantity', 'exceeds_position')
SIDES = ('buy', 'sell')
PAYOUT_STATUSES = ('paid', 'receivable')
PAY_BASES = ('actual', 'proxy')
ACTUAL_BASIS = 'actual'
# The whitelist of the report document, mirroring spec 6.2. A candidate holds `integrity` (whole run) and `periods`;
# each period holds the `period` sections (`h2_filter` for H2 only); `full` alone adds the `full` per-ticker items
# (`ticker_pass` for H2 only). Nested count dictionaries are keyed by the fixed value lists above, the selection
# distribution by '0' to str(K), the integrity checks by INVARIANT_CHECKS and the per-ticker items by RISKY.
DOCUMENT_KEYS = {
    'candidate': ('integrity', 'periods'),
    'integrity': ('passed', 'checks', 'split_events', 'proxy_payouts'),
    'periods': PERIODS,
    'period': ('counts', 'selection', 'targets', 'trading', 'h2_filter'),
    'full': ('ticker_selection', 'ticker_pass'),
    'counts': ('decisions', 'orders', 'order_reasons', 'trades', 'payout_status', 'payout_basis'),
    'selection': ('mean_eligible', 'mean_selected', 'selected_distribution', 'empty_selections'),
    'targets': ('mean_risky', 'max_risky', 'mean_bil', 'max_etf', 'max_group', 'scale_binding', 'scale_binding_share',
                'mean_scale'),
    'trading': ('turnover_sum', 'turnover_mean', 'cost_ratio', 'min_buy_fill', 'partial_fills'),
    'h2_filter': ('pass_share', 'removal_decisions', 'mean_removed_share'),
}
DIAGNOSTICS = 'diagnostics'


def _mean(values):
    """fsum / count; None for no values (zero denominator)."""
    return math.fsum(values) / len(values) if values else None


def _share(count, total):
    return count / total if total else None


def _largest(values):
    return max(values, default=None)


def _year(session):
    return session[:4]


def _in_year(period, year):
    """`full` is 2009-01-01 to 2022-12-31, the union of the years; a year holds that calendar year."""
    return year in YEARS if period == 'full' else year == period


def _in(period, session):
    """The session belongs to the period by its calendar year."""
    return _in_year(period, _year(session))


def _known(value, allowed, name, file, session, column):
    """A categorical field must be one of the expected values; the message names the place, not the value."""
    if value not in allowed:
        raise ValueError(f'{DIAGNOSTICS}: {name} {file} {session} {column} is not a known value')
    return value


def _decision_records(name, files, parent):
    """One record per decision, from the parsed %.10g text of the permitted columns.

    - year: the year of the decision's execution_session (D022 item 12); signals and target weights follow it.
    - eligible, selected: the number of the nine signal rows with `eligible` / `selected` True (for H2 these are the
      parent's columns); selected_tickers lists the selected tickers.
    - passed_tickers (H2): selected tickers whose `filter_pass` is True.
    - scale: the `scale` field of the decision's signal rows (one text per decision, item 5).
    - risky: fsum of the nine w_<ticker> fields of weights.csv; bil: w_BIL; etf: the largest of the nine risky
      w_<ticker>; group: the largest group fsum (BIL excluded).
    - parent_risky (H2): fsum of the nine w_<ticker> fields of the parent's weights.csv at the same decision.
    - turnover, buy_fill: the decisions.csv fields."""
    signals = {s: {r['ticker']: r for r in rows} for s, rows in
               groupby(files.signals, key=lambda r: r['decision_session'])}
    weights = {r['decision_session']: r for r in files.weights}
    parent_weights = {r['decision_session']: r for r in parent.weights} if parent else {}
    records = []
    for row in files.decisions:
        session = row['decision_session']

        def num(text, file, ticker, column):
            return number(text, DIAGNOSTICS, name, file, session, ticker, column)

        def risky_weights(w_row):
            return {t: num(w_row[f'w_{t}'], 'weights.csv', t, f'w_{t}') for t in RISKY}
        rows = signals[session]
        w = risky_weights(weights[session])
        selected = [t for t in RISKY if rows[t]['selected'] == 'True']
        record = {'year': _year(row['execution_session']),
                  'turnover': num(row['turnover'], 'decisions.csv', None, 'turnover'),
                  'buy_fill': num(row['buy_fill'], 'decisions.csv', None, 'buy_fill'),
                  'eligible': sum(rows[t]['eligible'] == 'True' for t in RISKY),
                  'selected': len(selected), 'selected_tickers': selected,
                  'scale': num(rows[RISKY[0]]['scale'], 'signals.csv', RISKY[0], 'scale'),
                  'risky': math.fsum(w.values()),
                  'bil': num(weights[session][f'w_{CASH}'], 'weights.csv', CASH, f'w_{CASH}'),
                  'etf': max(w.values()),
                  'group': max(math.fsum(w[t] for t in members) for members in GROUPS.values())}
        if parent:
            record['passed_tickers'] = [t for t in selected if rows[t]['filter_pass'] == 'True']
            record['parent_risky'] = math.fsum(risky_weights(parent_weights[session]).values())
        records.append(record)
    return records


def _counts(name, files, period, decisions):
    """Counts of one period: decisions by execution year; orders by execution_session with status and, for partial
    and cancelled orders, cancel_reason; trades by session and side; payouts by ex_session with their end-of-run
    status and basis (actual, or proxy for the scenario's proxy basis)."""
    proxy = f"proxy_ex_plus_{files.config['scenario']['proxy_pay_days']}_calendar_days"
    orders = {s: 0 for s in ORDER_STATUSES}
    reasons = {s: {r: 0 for r in CANCEL_REASONS} for s in REASON_STATUSES}
    for o in files.orders:
        session = o['execution_session']
        status = _known(o['status'], ORDER_STATUSES, name, 'orders.csv', session, 'status')
        if status == 'filled':
            _known(o['cancel_reason'], ('',), name, 'orders.csv', session, 'cancel_reason')
            reason = None
        else:
            reason = _known(o['cancel_reason'], CANCEL_REASONS, name, 'orders.csv', session, 'cancel_reason')
        if _in(period, session):
            orders[status] += 1
            if status != 'filled':
                reasons[status][reason] += 1
    trades = {s: 0 for s in SIDES}
    for t in files.trades:
        side = _known(t['side'], SIDES, name, 'trades.csv', t['session'], 'side')
        if _in(period, t['session']):
            trades[side] += 1
    status_counts, basis_counts = {s: 0 for s in PAYOUT_STATUSES}, {b: 0 for b in PAY_BASES}
    for r in files.payouts:
        status = _known(r['status'], PAYOUT_STATUSES, name, 'payouts.csv', r['ex_session'], 'status')
        basis = _known(r['pay_basis'], (ACTUAL_BASIS, proxy), name, 'payouts.csv', r['ex_session'], 'pay_basis')
        if _in(period, r['ex_session']):
            status_counts[status] += 1
            basis_counts['actual' if basis == ACTUAL_BASIS else 'proxy'] += 1
    return {'decisions': len(decisions), 'orders': orders, 'order_reasons': reasons, 'trades': trades,
            'payout_status': status_counts, 'payout_basis': basis_counts}


def _selection(name, decisions):
    """mean_eligible / mean_selected: mean over the period's decisions of the number of eligible (S > 0) / selected
    tickers; selected_distribution: the number of decisions with 0 to K selected tickers; empty_selections: the
    number of decisions with none selected. For H2 these are the parent's selection columns."""
    return {'mean_eligible': _mean([d['eligible'] for d in decisions]),
            'mean_selected': _mean([d['selected'] for d in decisions]),
            'selected_distribution': {str(k): sum(d['selected'] == k for d in decisions) for k in range(K[name] + 1)},
            'empty_selections': sum(d['selected'] == 0 for d in decisions)}


def _targets(decisions):
    """mean_risky / max_risky: mean and maximum over decisions of the target risky weight (fsum of the nine
    w_<ticker>); mean_bil: mean target w_BIL; max_etf: the largest single risky target weight; max_group: the largest
    group sum; scale_binding: the number of decisions with parsed `scale` < 1; scale_binding_share: that number over
    the number of decisions; mean_scale: mean `scale`."""
    binding = sum(d['scale'] < 1 for d in decisions)
    return {'mean_risky': _mean([d['risky'] for d in decisions]),
            'max_risky': _largest([d['risky'] for d in decisions]),
            'mean_bil': _mean([d['bil'] for d in decisions]),
            'max_etf': _largest([d['etf'] for d in decisions]),
            'max_group': _largest([d['group'] for d in decisions]),
            'scale_binding': binding, 'scale_binding_share': _share(binding, len(decisions)),
            'mean_scale': _mean([d['scale'] for d in decisions])}


def _trading(cost, decisions):
    """turnover_sum: fsum of one-way turnover (0.0 without decisions); turnover_mean: that sum over the number of
    decisions; cost_ratio: scenario cost x turnover_sum (D022 item 13 up to rounding, because costs = cost x
    notional); min_buy_fill: the smallest parsed buy_fill; partial_fills: the number of decisions with parsed
    buy_fill < 1."""
    total = math.fsum(d['turnover'] for d in decisions)
    return {'turnover_sum': total, 'turnover_mean': _share(total, len(decisions)), 'cost_ratio': cost * total,
            'min_buy_fill': min((d['buy_fill'] for d in decisions), default=None),
            'partial_fills': sum(d['buy_fill'] < 1 for d in decisions)}


def _h2_filter(decisions):
    """pass_share: the number of parent-selected ticker-decisions whose filter_pass is True over the number of
    parent-selected ticker-decisions; removal_decisions: the number of decisions in which at least one
    parent-selected ticker fails the filter; mean_removed_share: mean, over decisions with a positive parent risky
    target weight, of (parent risky - H2 risky) / parent risky, both fsums of the nine w_<ticker> of weights.csv."""
    selected = sum(d['selected'] for d in decisions)
    passed = sum(len(d['passed_tickers']) for d in decisions)
    removed = [(d['parent_risky'] - d['risky']) / d['parent_risky'] for d in decisions if d['parent_risky'] > 0]
    return {'pass_share': _share(passed, selected),
            'removal_decisions': sum(len(d['passed_tickers']) < d['selected'] for d in decisions),
            'mean_removed_share': _mean(removed)}


def _per_ticker(decisions, h2):
    """`full` only. ticker_selection: per risky ticker, the number of decisions selecting it over the number of
    decisions (for H2 the parent's selection); ticker_pass (H2): per ticker, the number of its parent selections that
    pass the filter over the number of its parent selections."""
    out = {'ticker_selection': {t: _share(sum(t in d['selected_tickers'] for d in decisions), len(decisions))
                                for t in RISKY}}
    if h2:
        out['ticker_pass'] = {t: _share(sum(t in d['passed_tickers'] for d in decisions),
                                        sum(t in d['selected_tickers'] for d in decisions)) for t in RISKY}
    return out


def _integrity(name, invariants):
    """Whole run only: the seven invariant flags, the overall flag and the numbers of split events and proxy
    payouts; it accepts only what item 4 accepts."""
    try:
        _check_invariant_flags(invariants)
    except ValueError as exc:
        raise ValueError(f'{DIAGNOSTICS}: {name} {exc}') from None
    return {'passed': invariants['passed'], 'checks': {c: invariants['checks'][c] for c in INVARIANT_CHECKS},
            'split_events': len(invariants['split_events']), 'proxy_payouts': len(invariants['proxy_payouts'])}


def _enforce_whitelist(name, candidate):
    """The built document of one configuration holds exactly the keys of DOCUMENT_KEYS and of the fixed value lists,
    in order, at every level; the message names the section."""
    h2 = name in H

    def keys(label, block, expected):
        report.require(list(block) == list(expected), f'{DIAGNOSTICS}: {name} {label} keys are not the whitelist')
    keys('candidate', candidate, DOCUMENT_KEYS['candidate'])
    keys('integrity', candidate['integrity'], DOCUMENT_KEYS['integrity'])
    keys('checks', candidate['integrity']['checks'], INVARIANT_CHECKS)
    keys('periods', candidate['periods'], DOCUMENT_KEYS['periods'])
    for period, block in candidate['periods'].items():
        sections = [s for s in DOCUMENT_KEYS['period'] if h2 or s != 'h2_filter']
        if period == 'full':
            sections += [s for s in DOCUMENT_KEYS['full'] if h2 or s != 'ticker_pass']
        keys('period', block, sections)
        for section in sections:
            keys(section, block[section], RISKY if section in DOCUMENT_KEYS['full'] else DOCUMENT_KEYS[section])
        counts = block['counts']
        for label, expected in (('orders', ORDER_STATUSES), ('order_reasons', REASON_STATUSES), ('trades', SIDES),
                                ('payout_status', PAYOUT_STATUSES), ('payout_basis', PAY_BASES)):
            keys(label, counts[label], expected)
        for status in REASON_STATUSES:
            keys('order_reasons', counts['order_reasons'][status], CANCEL_REASONS)
        keys('selected_distribution', block['selection']['selected_distribution'],
             [str(k) for k in range(K[name] + 1)])


def diagnostics(runs):
    """The spec 6.2 document, a pure function of the RunFiles (permitted columns only) and the scenario cost of
    config.json: {configuration: {'integrity', 'periods': {period: sections}}} with the keys of DOCUMENT_KEYS.
    Configurations follow HYPOTHESES; an H2 configuration needs the RunFiles of its parent. A decision belongs to the
    year of its execution session, an order to that of its execution_session, a trade to that of its session and a
    payout to that of its ex_session; a mean, share, minimum or maximum without any value is None."""
    out = {}
    for name in (n for n in HYPOTHESES if n in runs):
        files, h2 = runs[name], name in H
        report.require(not h2 or PARENT in runs, f'{DIAGNOSTICS}: {name} needs the {PARENT} run')
        with report.well_formed(f'{DIAGNOSTICS}: {name}'):
            records = _decision_records(name, files, runs[PARENT] if h2 else None)
            cost = files.config['scenario']['cost']
            periods = {}
            for period in PERIODS:
                mine = [d for d in records if _in_year(period, d['year'])]
                block = {'counts': _counts(name, files, period, mine), 'selection': _selection(name, mine),
                         'targets': _targets(mine), 'trading': _trading(cost, mine)}
                if h2:
                    block['h2_filter'] = _h2_filter(mine)
                if period == 'full':
                    block.update(_per_ticker(mine, h2))
                periods[period] = block
            out[name] = {'integrity': _integrity(name, files.invariants), 'periods': periods}
            _enforce_whitelist(name, out[name])
    return out


# --- Markdown -------------------------------------------------------------------------------------------------------

SECTION_TITLES = {'counts': 'counts', 'selection': 'selection', 'targets': 'targets', 'trading': 'trading',
                  'h2_filter': 'H2 filter'}
PERCENT = {'mean_risky', 'max_risky', 'mean_bil', 'max_etf', 'max_group', 'scale_binding_share', 'pass_share',
           'mean_removed_share'}
FOUR = {'mean_scale', 'turnover_sum', 'turnover_mean', 'cost_ratio', 'min_buy_fill'}
TWO = {'mean_eligible', 'mean_selected'}
MISSING = object()


def _cell(key, value):
    """Shares as percentages with 2 decimals, scale, buy_fill, turnover and cost_ratio with 4 decimals, mean ticker
    counts with 2 decimals, counts as integers; null as n/a."""
    if value is MISSING:
        return '-'
    if value is None:
        return 'n/a'
    if isinstance(value, bool):
        return str(value)
    if key in PERCENT:
        return f'{value * 100:.2f}%'
    if key in FOUR:
        return f'{value:.4f}'
    if key in TWO:
        return f'{value:.2f}'
    return f'{value:d}'


def _columns(section, block, k_max):
    """(label, key, value) of one section in a fixed order."""
    if section == 'counts':
        out = [('decisions', 'decisions', block['decisions'])]
        out += [(f'orders {s}', 'n', block['orders'][s]) for s in ORDER_STATUSES]
        out += [(f'{s} {r}', 'n', block['order_reasons'][s][r]) for s in REASON_STATUSES for r in CANCEL_REASONS]
        out += [(f'trades {s}', 'n', block['trades'][s]) for s in SIDES]
        out += [(f'payouts {s}', 'n', block['payout_status'][s]) for s in PAYOUT_STATUSES]
        out += [(f'payouts {b}', 'n', block['payout_basis'][b]) for b in PAY_BASES]
        return out
    if section == 'selection':
        dist = block['selected_distribution']
        return [('mean_eligible', 'mean_eligible', block['mean_eligible']),
                ('mean_selected', 'mean_selected', block['mean_selected']),
                *((f'selected {k}', 'n', dist.get(str(k), MISSING)) for k in range(k_max + 1)),
                ('empty_selections', 'empty_selections', block['empty_selections'])]
    return [(key, key, block[key]) for key in DOCUMENT_KEYS[section]]


def _names(document):
    return [n for n in HYPOTHESES if n in document]


def render_markdown(document):
    """Deterministic Markdown of the diagnostics document: the whole-run integrity table, the `full` tables, then the
    annual aggregate tables, which carry no ticker or group names. A pure function of the document."""
    names = _names(document)
    k_max = max((K[n] for n in names), default=0)
    out = ['# N4 hypothesis diagnostics', '',
           'Permitted diagnostics of the six H1/H2 configurations. A decision belongs to the year of its execution '
           'session, an order to the year of its execution session, a trade to the year of its session and a payout '
           'to the year of its ex-dividend session, with its status at the end of the run. The full period is '
           '2009-01-01 to 2022-12-31. n/a marks a zero denominator or a minimum or maximum without values. '
           'max_etf covers the nine risky ETFs only. For H2 the selection and scale columns are those of the parent H1_252_3.',
           '',
           '## Integrity (whole run)', '',
           report.table(['configuration', 'passed', *INVARIANT_CHECKS, 'split_events', 'proxy_payouts'],
                        [[n, _cell('passed', document[n]['integrity']['passed']),
                          *(_cell(c, document[n]['integrity']['checks'][c]) for c in INVARIANT_CHECKS),
                          _cell('n', document[n]['integrity']['split_events']),
                          _cell('n', document[n]['integrity']['proxy_payouts'])] for n in names]), '']
    for section in DOCUMENT_KEYS['period']:
        mine = [n for n in names if section in document[n]['periods']['full']]
        if not mine:
            continue
        columns = [label for label, _, _ in _columns(section, document[mine[0]]['periods']['full'][section], k_max)]
        rows = [[n, *(_cell(key, value) for _, key, value in
                      _columns(section, document[n]['periods']['full'][section], k_max))] for n in mine]
        out += [f'## Full period: {SECTION_TITLES[section]}', '', report.table(['configuration', *columns], rows), '']
    for key, title in (('ticker_selection', 'ticker selection frequency'), ('ticker_pass', 'H2 ticker pass share')):
        mine = [n for n in names if key in document[n]['periods']['full']]
        if mine:
            rows = [[n, *(_cell('pass_share', document[n]['periods']['full'][key][t]) for t in RISKY)] for n in mine]
            out += [f'## Full period: {title}', '', report.table(['configuration', *RISKY], rows), '']
    for section in DOCUMENT_KEYS['period']:
        mine = [n for n in names if section in document[n]['periods']['full']]
        if not mine:
            continue
        columns = [label for label, _, _ in _columns(section, document[mine[0]]['periods']['full'][section], k_max)]
        rows = [[year, n, *(_cell(key, value) for _, key, value in
                            _columns(section, document[n]['periods'][year][section], k_max))]
                for year in YEARS for n in mine]
        out += [f'## Annual {SECTION_TITLES[section]}', '', report.table(['year', 'configuration', *columns], rows), '']
    return '\n'.join(out)


def build_hypothesis_report(root, run_dirs, parent=None, expected_sha256=VINTAGE_MANIFEST_SHA256):
    """Journaled N4 report: verifies the six runs (items 1-7), then freezes hypotheses.json (canonical JSON of the
    diagnostics) and hypotheses.md in data/reports/<run_id>; run ids and run manifest hashes go to the manifest
    metadata only. A rejection ends the Run as failed. Returns the report directory."""
    root = Path(root).resolve()
    config = {'runs': [project_path(root, (root / d).resolve()) for d in run_dirs], 'expected_sha256': expected_sha256}
    with Run(root, REPORT_PURPOSE, config, parent, candidate_ids=HYPOTHESES) as run:
        report.require(run.base['dirty_tree'] is False, 'item 3: the report tree is dirty')
        runs = verified_hypothesis_runs(root, run_dirs, expected_sha256, run.base)
        body = canonical_bytes(diagnostics(runs))
        files = {'hypotheses.json': body, 'hypotheses.md': render_markdown(json.loads(body)).encode('utf-8')}
        sources = [{'candidate': n, 'run_id': runs[n].path.name,
                    'manifest_sha256': sha256((runs[n].path / 'manifest.json').read_bytes())} for n in HYPOTHESES]
        target = root / 'data/reports' / run.run_id
        freeze(target, files, {'sources': sources, 'environment': run.env, 'run_id': run.run_id})
        run.finish('completed', [project_path(root, target)], sha256((target / 'manifest.json').read_bytes()), [])
    return target
