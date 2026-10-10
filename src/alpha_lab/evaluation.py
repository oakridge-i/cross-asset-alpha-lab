"""N5 evaluation report (spec 7; D025 items 1, 4, 6-10, 12-17).

Part 1 verifies the thirteen N5 runs before any evaluation figure is computed (spec 7.1 items 1-5); part 2 checks the
P_A1 selection log against its run files (item 6), then computes the comparisons, annual differences and regressions
of the walk-forward period (spec 6, 7.2, 7.3) and freezes evaluation.json and evaluation.md in a journaled report.

Verification messages name the rule ('item <n>') and the run directory or label and, where relevant, the file, period,
metric, selection year or decision session, and never carry a value read from a file or a selected configuration; the
original exception is suppressed. Every exception of the computation phase is re-raised as a value-free RuntimeError,
except the fixed-text RuleError of its own checks (spec 8.3)."""
from collections import namedtuple
from contextlib import contextmanager
import csv
import json
import math
from pathlib import Path
import re
import numpy as np
import pandas as pd
from alpha_lab import hypothesis_report as hr, inference, provenance, report
from alpha_lab.adaptive import CANDIDATES, FALLBACK, TOLERANCE, validation_segment
from alpha_lab.engine import PROVIDERS, STAGE_PURPOSES
from alpha_lab.features import CASH, total_return_index, xnys_month_end
from alpha_lab.market import LAST_OPEN_SESSION, VINTAGE_MANIFEST_SHA256, load_market
from alpha_lab.metrics import BLOCKS, METRICS_SCHEMA, PERIODS, WF_PERIODS, number
from alpha_lab.pipeline import project_path
from alpha_lab.portfolio import GROUPS
from alpha_lab.provenance import canonical_bytes, freeze, sha256

KEYS = ('B0', 'B1', 'B2', 'B3', 'REF_SPY', 'H1_252_3', 'H1_252_4', 'H1_126_3', 'H1_126_4', 'H2_4of6', 'H2_5of6',
        'P_A1', 'H1_252_3_WF')
COMPARATOR = 'H1_252_3_WF'
COMPARATOR_PROVIDER = 'H1_252_3'
# Run windows of spec 4.1; P_A1 and its comparator use the walk-forward window.
FULL_WINDOW = ('2008-12-31', '2022-12-30')
WF_WINDOW = ('2013-12-31', '2022-12-30')
WF_LABELS = ('P_A1', COMPARATOR)
# The first N3 benchmark runs and the N4 replacement runs whose shared files must be identical (D025 item 17).
REFERENCES = {'B0': '20261007T180004-12aae80084', 'B1': '20261007T180018-b6c98bd0aa',
              'B2': '20261007T180026-dffe07154c', 'B3': '20261007T180033-bba99392df',
              'REF_SPY': '20261007T180039-be7dd8f43a', 'H1_252_3': '20261008T192727-e5e184b7db',
              'H1_252_4': '20261008T192731-0f8d083cb0', 'H1_126_3': '20261008T192734-866ab4b3d7',
              'H1_126_4': '20261008T192737-45e578bd7c', 'H2_4of6': '20261008T192740-f8be1b1ad3',
              'H2_5of6': '20261008T192745-708215766a'}
REFERENCED = KEYS[:11]
# Main scenario and initial cash (spec 4.1), held here independently of the engine defaults.
SCENARIO = {'cost': 0.001, 'lag': 1, 'reserve': 0.01, 'proxy_pay_days': 10}
INITIAL_CASH = 100000.0
# Run files of spec 4.2 and D025 item 12: nine, ten and eleven.
FILES = {'benchmark': frozenset(report.RUN_FILES), 'hypothesis': frozenset(hr.RUN_FILES | {'metrics.json'}),
         'policy': frozenset(hr.RUN_FILES | {'metrics.json', 'selection.json'})}
# Utility U = 252 mean(e) - 1.5 * 252 var(e, ddof=1) (protocol line 151) and the metrics-versus-CSV tolerance (spec
# 6.2, D025 item 16).
ANNUAL = 252
PENALTY = 1.5
METRICS_TOLERANCE = 1e-7
MALFORMED = (KeyError, TypeError, AttributeError, IndexError, ArithmeticError, OSError, UnicodeError)

Run = namedtuple('Run', 'path manifest config metrics')


@contextmanager
def rule(item, where):
    """Prefix a failed check with its rule and run. Only the plain ValueError of a check passes its (value-free)
    message on; malformed data, including decoding errors whose text may quote the input, gets a fixed message."""
    try:
        yield
    except ValueError as exc:
        if type(exc) is not ValueError:
            raise ValueError(f'item {item}, {where}: malformed run data') from None
        raise ValueError(f'item {item}, {where}: {exc}') from None
    except MALFORMED:
        raise ValueError(f'item {item}, {where}: malformed run data') from None


def _same(value, expected):
    """Canonical JSON equality; a value that has no canonical form (NaN, infinity) is not equal."""
    try:
        return canonical_bytes(value) == canonical_bytes(expected)
    except ValueError:
        return False


def window(label):
    """(start_session, end_session) of a run label."""
    start, end = WF_WINDOW if label in WF_LABELS else FULL_WINDOW
    report.require(end <= LAST_OPEN_SESSION, 'run window ends after the last open session')
    return start, end


def periods_of(label):
    return WF_PERIODS if label in WF_LABELS else PERIODS


def _identify(root, run_dir):
    """Item 1 for one directory: inside data/runs, provenance.verify, the file set of its kind; returns (path,
    manifest, config, label)."""
    try:
        path = report.run_path(root, run_dir)
    except ValueError:
        raise ValueError('run directory is not directly inside data/runs') from None
    try:
        manifest = provenance.verify(path)
    except ValueError:
        raise ValueError('provenance.verify failed') from None
    config = report.read_json(path / 'config.json')
    name = config['provider']['name']
    report.require(isinstance(name, str) and name in PROVIDERS and PROVIDERS[name].kind in FILES,
                   'not a run of an N5 provider')
    kind = PROVIDERS[name].kind
    report.require(set(manifest['files']) == FILES[kind], f'not an N5 {kind} run (file set)')
    label = COMPARATOR if name == COMPARATOR_PROVIDER and config['start_session'] == WF_WINDOW[0] else name
    return path, manifest, config, label


def _src_tree(root, sha, whose):
    """report.src_tree with a message that names the record, not the journaled git_sha."""
    try:
        return report.src_tree(root, sha)
    except ValueError:
        raise ValueError(f'cannot resolve the src tree of {whose}') from None


def _check_journal(root, path, rows, config, base, kind):
    """Item 2: report.check_journal with the N5 purpose of the kind, and the terminal record's purpose and
    candidate_ids. The environment is item 3, so check_journal receives the run's own environment hash."""
    purpose = STAGE_PURPOSES[5][kind]
    started = [r for r in rows if r.get('run_id') == path.name and r['event'] == 'started']
    own = started[0]['environment_manifest_sha256'] if len(started) == 1 else base['environment_manifest_sha256']
    record = report.check_journal(root, path, rows, config, {**base, 'environment_manifest_sha256': own}, purpose,
                                  label=f'N5 {kind}')
    terminal = next(r for r in rows if r.get('run_id') == path.name and r['event'] != 'started')
    report.require(terminal['purpose'] == purpose and terminal['candidate_ids'] == [config['provider']['name']],
                   f'{path.name}: terminal record purpose or candidate_ids is not that of an N5 {kind} run')
    return record, terminal


def _check_config(label, kind, manifest, config, invariants, expected_sha256, vintage):
    """Item 4: vintage, provider version and parameters, window, scenario, initial cash, decision schedule, and the
    seven invariants with the overall flag."""
    hr._check_invariant_flags(hr._invariant_flags(invariants))
    name = config['provider']['name']
    entry = PROVIDERS[name]
    report.require(config['provider']['version'] == entry.version, 'provider version is not current')
    provider = {'name': name, 'version': entry.version}
    if kind in ('hypothesis', 'policy'):
        provider['parameters'] = entry.parameters
    report.require(_same(config['provider'], provider), 'config.json provider parameters are not those of the registry')
    report.require(config['manifest_sha256'] == expected_sha256 == manifest['metadata']['derived_manifest_sha256'],
                   'vintage manifest hash is not the approved one')
    report.require(config['vintage'] == vintage, 'config.json vintage differs from that of B0')
    start, end = window(label)
    fixed = {'start_session': start, 'end_session': end, 'scenario': SCENARIO, 'initial_cash': INITIAL_CASH,
             'decision_sessions': [start] if entry.schedule == 'first_only' else None}
    for key, value in fixed.items():
        report.require(_same(config[key], value), f'config.json {key} is not the registered value')


def _check_shared(root, kind, manifest, reference):
    """Item 5, spec 4.3: every file of the reference manifest has the same SHA-256 in the N5 run, whose file set is
    the reference set (benchmarks) or the reference set plus metrics.json (configurations)."""
    valid = isinstance(reference, str) and reference not in ('', '.', '..') and Path(reference).name == reference
    report.require(valid, 'no valid reference run id')
    path = root / 'data/runs' / reference
    report.require(path.is_dir(), 'reference run directory is missing')
    try:
        files = provenance.verify(path)['files']
    except ValueError:
        raise ValueError('reference run does not pass provenance.verify') from None
    added = set() if kind == 'benchmark' else {'metrics.json'}
    report.require(not added & set(files), 'reference run is not a run of the earlier campaign')
    report.require(set(manifest['files']) == set(files) | added, 'file set differs from the reference run')
    for name in sorted(files):
        report.require(manifest['files'][name] == files[name], f'{name} differs from the reference run')


def bil_returns(market, last):
    """{session: theoretical BIL total return} on the market's sessions up to `last` (D022 item 10)."""
    report.require(last <= LAST_OPEN_SESSION, 'daily.csv holds a session after the last open session')
    index = total_return_index(market.history(last))[CASH]
    sessions, values = list(index.index), [float(v) for v in index.to_numpy()]
    return {sessions[i]: values[i] / values[i - 1] - 1 for i in range(1, len(values))}


def recomputed(market, daily, first, last, bil=None):
    """n_returns, utility and total_return of the daily (session, nav) rows with first <= session <= last, each
    return based on the previous row (as metrics.period_metrics), or None when the period has no return. Computed
    here with math.fsum, independently of the metrics module."""
    bil = bil_returns(market, daily[-1][0]) if bil is None else bil
    rows = [i for i in range(1, len(daily)) if first <= daily[i][0] <= last]
    if not rows:
        return None
    excess = [daily[i][1] / daily[i - 1][1] - 1 - bil[daily[i][0]] for i in rows]
    n = len(excess)
    out = {'n_returns': n, 'total_return': daily[rows[-1]][1] / daily[rows[0] - 1][1] - 1, 'utility': None}
    if n > 1:
        mean = math.fsum(excess) / n
        variance = math.fsum((x - mean) ** 2 for x in excess) / (n - 1)
        out['utility'] = ANNUAL * mean - PENALTY * ANNUAL * variance
    return out


def _read_daily(path, market, config):
    """(session, nav) rows of daily.csv; the sessions must be the market sessions of the run window and every NAV a
    finite positive number."""
    rows = hr.read_columns(path / 'daily.csv', ('session', 'nav'))
    sessions = list(market.sessions)
    at = {s: i for i, s in enumerate(sessions)}
    start, end = config['start_session'], config['end_session']
    report.require(start in at and end in at and [r['session'] for r in rows] == sessions[at[start]:at[end] + 1],
                   'daily.csv sessions are not the market sessions of the run window')
    out = []
    for r in rows:
        text = r['nav']
        report.require(hr.NUMBER.fullmatch(text) is not None and math.isfinite(float(text)) and float(text) > 0,
                       f'daily.csv {r["session"]} nav is not a finite positive number')
        out.append((r['session'], float(text)))
    return out


def _number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _check_metrics(label, path, config, metrics, market, cache):
    """Item 5, metrics: the period keys of the label's list that have a return, and n_returns, utility and
    total_return of each recomputed from daily.csv and the theoretical BIL return to METRICS_TOLERANCE."""
    report.require(type(metrics['schema_version']) is int and metrics['schema_version'] == METRICS_SCHEMA,
                   'metrics schema version is not current')
    daily = _read_daily(path, market, config)
    last = daily[-1][0]
    if last not in cache:
        cache[last] = bil_returns(market, last)
    expected = {}
    for name, first, end in periods_of(label):
        values = recomputed(market, daily, first, end, cache[last])
        if values is not None:
            expected[name] = values
    stored = metrics['periods']
    report.require(isinstance(stored, dict) and set(stored) == set(expected),
                   'metrics.json periods are not those of the period list')
    for name, values in expected.items():
        block = stored[name]
        report.require(type(block['n_returns']) is int and block['n_returns'] == values['n_returns'],
                       f'metrics.json {name} n_returns disagrees with daily.csv')
        for key in ('utility', 'total_return'):
            want, have = values[key], block[key]
            agree = have is None if want is None else (
                _number(have) and math.isfinite(want) and abs(have - want) <= METRICS_TOLERANCE)
            report.require(agree, f'metrics.json {name} {key} disagrees with daily.csv')


def verified_n5_runs(root, run_dirs, expected_sha256, base, references=REFERENCES):
    """Items 1-5 of spec 7.1 in order (item 1 for every directory, items 2-4 run by run, then item 5 run by run);
    `base` is the started record of the evaluation run. Returns {label: Run} in KEYS order."""
    root = Path(root)
    found = {}
    for run_dir in run_dirs:
        with rule(1, Path(run_dir).name):
            path, manifest, config, label = _identify(root, run_dir)
        found.setdefault(label, []).append((path, manifest, config))
    for label in KEYS:
        report.require(label in found, f'item 1, {label}: run directory missing')
        report.require(len(found[label]) == 1, f'item 1, {label}: run directory given more than once')
    with rule(2, 'journal'):
        rows = report.journal_rows(root)
    with rule(3, 'report'):
        tree = _src_tree(root, base['git_sha'], 'the report git_sha')
    with rule(4, 'B0'):
        vintage = found['B0'][0][2]['vintage']
    runs = {}
    for label in KEYS:
        path, manifest, config = found[label][0]
        kind = PROVIDERS[config['provider']['name']].kind
        with rule(2, label):
            started, terminal = _check_journal(root, path, rows, config, base, kind)
        with rule(3, label):
            for record in (started, terminal):
                report.require(_src_tree(root, record['git_sha'], f'the {label} git_sha') == tree,
                               'src tree differs from the report commit')
            report.require(started['environment_manifest_sha256'] == base['environment_manifest_sha256'],
                           'environment differs from the report environment')
        with rule(4, label):
            invariants = report.read_json(path / 'invariants.json')
            _check_config(label, kind, manifest, config, invariants, expected_sha256, vintage)
        runs[label] = (path, manifest, config, kind)
    with rule(5, 'vintage'):
        derived = (root / vintage).resolve()
        report.require(derived.is_relative_to(root.resolve()), 'vintage outside the project')
        try:
            market = load_market(root, derived, expected_sha256)
        except Exception:
            raise ValueError('the approved vintage does not load') from None
    out, cache = {}, {}
    for label in KEYS:
        path, manifest, config, kind = runs[label]
        with rule(5, label):
            if label in REFERENCED:
                report.require(label in references, 'no reference run is given')
                _check_shared(root, kind, manifest, references[label])
            metrics = report.read_json(path / 'metrics.json')
            _check_metrics(label, path, config, metrics, market, cache)
        out[label] = Run(path, manifest, config, metrics)
    return out


# --- Part 2: the selection log (item 6) ---------------------------------------------------------------------------

POLICY = 'P_A1'
SELECTION_YEARS = tuple(range(2014, 2023))
SELECTION_KEYS = frozenset({'year', 'selection_date', 'segment_start', 'segment_end', 'decisions', 'returns', 'utility',
                            'best_utility', 'close_set', 'chosen', 'fallback', 'warning', 'stability'})
EXTRA_SIGNAL_COLUMNS = ['selection_year', 'selected_config']
DATE = re.compile(r'[0-9]{4}-[0-9]{2}-[0-9]{2}')


def _csv(path):
    """(header, rows) of a rectangular UTF-8 CSV file with distinct column names, all fields as text."""
    try:
        with path.open(newline='', encoding='utf-8') as stream:
            reader = csv.reader(stream)
            header = next(reader, None) or []
            body = list(reader)
    except (csv.Error, UnicodeDecodeError):
        raise ValueError(f'{path.name} is not a readable UTF-8 CSV file') from None
    report.require(header and len(set(header)) == len(header) and all(len(r) == len(header) for r in body),
                   f'{path.name} is not a rectangular CSV file with distinct columns')
    return header, body


def _by_decision(path, unique=False):
    """(header, {decision_session: rows}) in file order; with unique, one row per session, given as that row."""
    header, body = _csv(path)
    report.require(header[0] == 'decision_session', f'{path.name} does not start with decision_session')
    out = {}
    for row in body:
        out.setdefault(row[0], []).append(row)
    if unique:
        report.require(all(len(rows) == 1 for rows in out.values()), f'{path.name} repeats a decision session')
        out = {session: rows[0] for session, rows in out.items()}
    return header, out


def _executions(path):
    """{decision_session: execution_session} of decisions.csv in file order."""
    header, body = _csv(path / 'decisions.csv')
    report.require('decision_session' in header and 'execution_session' in header,
                   'decisions.csv lacks the decision or execution session column')
    d, x = header.index('decision_session'), header.index('execution_session')
    out = {r[d]: r[x] for r in body}
    report.require(len(out) == len(body), 'decisions.csv repeats a decision session')
    report.require(all(DATE.fullmatch(s) for s in out.values()), 'decisions.csv holds a malformed execution session')
    return out


def _check_entry(entry, year):
    """The semantics of one selection log entry, from its logged utilities (spec 7.1 item 6, P5-P7)."""
    report.require(isinstance(entry, dict) and set(entry) == SELECTION_KEYS, 'entry keys are not those of the log')
    start, end = validation_segment(year)
    report.require(entry['segment_start'] == start and entry['segment_end'] == end and entry['selection_date'] == end,
                   'segment dates or selection date are not those of the validation segment')
    u = entry['utility']
    report.require(isinstance(u, dict) and len(u) == len(CANDIDATES) and set(u) == set(CANDIDATES),
                   'utility keys are not the four candidates')
    report.require(all(u[c] is None or _number(u[c]) for c in CANDIDATES), 'a utility is neither a number nor null')
    report.require(type(entry['fallback']) is bool, 'the fallback flag is not a boolean')
    if not entry['fallback']:
        report.require(all(u[c] is not None for c in CANDIDATES),
                       'a utility of an entry without fallback is not finite')
        best = entry['best_utility']
        report.require(_number(best) and best == max(u[c] for c in CANDIDATES),
                       'best_utility is not the maximum of the logged utilities')
        close = [c for c in CANDIDATES if u[c] >= best - TOLERANCE]
        report.require(entry['close_set'] == close,
                       'close_set is not the set of candidates within the tolerance of best_utility')
        report.require(entry['chosen'] == close[0],
                       'chosen is not the first member of the close set in the preference order')
        report.require(entry['warning'] is None, 'an entry without fallback carries a warning')
    else:
        report.require(any(u[c] is None for c in CANDIDATES), 'a fallback entry has no missing utility')
        report.require(isinstance(entry['warning'], str) and entry['warning'].strip() != '',
                       'a fallback entry has no warning')
        report.require(entry['chosen'] == FALLBACK, 'the chosen configuration of a fallback entry is not the fallback')
        report.require(entry['best_utility'] is None and entry['close_set'] == [],
                       'a fallback entry has a best_utility or a close set')


def check_selection_log(log, runs):
    """Spec 7.1 item 6: nine entries for 2014 to 2022 in order, each consistent with its logged utilities; every
    decision of the policy run uses the selection of the year of its execution session, and its weights.csv row and
    signal rows equal those of the chosen configuration's full-window run at that decision. Messages name the rule,
    the run, the year or the decision session, never a value or a configuration."""
    with rule(6, f'{POLICY} selection.json'):
        report.require(isinstance(log, list) and len(log) == len(SELECTION_YEARS),
                       'the selection log does not hold one entry per walk-forward year')
        report.require(all(isinstance(e, dict) and type(e.get('year')) is int for e in log)
                       and [e['year'] for e in log] == list(SELECTION_YEARS),
                       'the selection log years are not the walk-forward years in order')
    chosen = {}
    for entry in log:
        year = entry['year']
        with rule(6, f'{POLICY} selection year {year}'):
            _check_entry(entry, year)
        chosen[year] = entry['chosen']
    with rule(6, f'{POLICY} run files'):
        path = runs[POLICY].path
        execution = _executions(path)
        weight_header, weights = _by_decision(path / 'weights.csv', unique=True)
        signal_header, signals = _by_decision(path / 'signals.csv')
        report.require(list(weights) == list(execution) and list(signals) == list(execution),
                       'decisions.csv, weights.csv and signals.csv hold different decision sessions')
        report.require(signal_header[-2:] == EXTRA_SIGNAL_COLUMNS,
                       'signals.csv does not end with selection_year and selected_config')
        start = runs[POLICY].config['start_session']
    configurations = {}
    with rule(6, 'H1 full-window run files'):
        for name in CANDIDATES:
            configurations[name] = (_by_decision(runs[name].path / 'weights.csv', unique=True),
                                    _by_decision(runs[name].path / 'signals.csv'))
    with rule(6, f'{POLICY} run files'):
        # The policy decides on the schedule of the configuration runs from its start session on.
        for name in sorted(set(chosen.values()), key=CANDIDATES.index):
            schedule = [s for s in configurations[name][0][1] if s >= start]
            report.require(list(execution) == schedule, 'decision sessions differ from those of the chosen '
                           'configuration runs from the policy start session on')
    for session, executed in execution.items():
        with rule(6, f'{POLICY} decision {session}'):
            rows = signals[session]
            year = executed[:4]
            report.require(all(r[-2] == year for r in rows),
                           'selection_year of the signal rows is not the year of the execution session')
            report.require(int(year) in chosen, 'no selection log entry for the year of the execution session')
            pick = chosen[int(year)]
            report.require(all(r[-1] == pick for r in rows),
                           'selected_config of the signal rows is not the chosen configuration of the year')
            (header, rows_w), (header_s, rows_s) = configurations[pick]
            report.require(header == weight_header and rows_w.get(session) == weights[session],
                           "weights.csv row differs from the chosen configuration's row at the decision")
            report.require(header_s == signal_header[:-2] and rows_s.get(session) == [r[:-2] for r in rows],
                           "signal rows differ from the chosen configuration's rows at the decision")


# --- Part 2: comparisons, annual differences and regressions (spec 6, 7.2-7.4) --------------------------------------

REPORT_PURPOSE = 'N5 evaluation report'
PRIMARY = (('H1_252_3', 'B3'), ('H1_252_4', 'B3'), ('H1_126_3', 'B3'), ('H1_126_4', 'B3'), ('H2_4of6', 'H1_252_3'),
           ('H2_5of6', 'H1_252_3'))
SUPPLEMENTARY = (('H2_4of6', 'B3'), ('H2_5of6', 'B3'), ('H2_4of6', 'B2'), ('H2_5of6', 'B2'))
POLICY_COMPARISON = (POLICY, COMPARATOR)
POLICY_NOTE = 'intervals conditional on the realized selections of P_A1; no p-value is reported (P13)'
# Paired circular block bootstrap (protocol line 161, P8) and the minimum effect (line 159).
REPLICATES = 10000
SEED = 20261006
LENGTHS = (21, 63, 126)
PRIMARY_LENGTH = 63
MINIMUM_EFFECT = 0.01
WALK_FORWARD = next((first, last) for name, first, last in BLOCKS if name == 'walk_forward')
# Model A regressor (protocol line 165, spec 6.5): B3 for H1, the parent for H2, the comparator run for P_A1.
REGRESSION_COMPARATOR = {'H1_252_3': 'B3', 'H1_252_4': 'B3', 'H1_126_3': 'B3', 'H1_126_4': 'B3',
                         'H2_4of6': 'H1_252_3', 'H2_5of6': 'H1_252_3', POLICY: COMPARATOR}
NW_LAG = 3
DOCUMENT_KEYS = ('window', 'scenario', 'initial_cash', 'manifest_sha256', 'provider_versions', 'metrics', 'comparisons',
                 'annual_differences', 'regressions', 'selection', 'disclosures')
# Spec 7.4, fixed text.
DISCLOSURES = (
    'All inferential figures are exploratory on familiar history, and the Holm adjustment does not restore '
    'independence (protocol line 163).',
    'The years 2014 to 2022 were the research period, and the project owner\'s prior exposure to them is non-zero and '
    'unquantified (G0).',
    'Each statistic is conditional on the model already selected (protocol line 167).',
    'The window excludes most of the 2008 crisis (protocol line 141).',
    'The data limitations recorded in D016 to D020 apply.',
    'Costs are modeled at 10 basis points per side.',
    'The walk-forward comparison with the continuous accounts differs from P_A1 by the start state: P_A1 and its '
    'comparator start in cash at 2013-12-31 (P2).',
    'Statistical non-significance does not establish the absence of an effect (protocol line 163).',
    'The results do not establish an investable track record.',
)
WITHHELD = '{} in the evaluation; message withheld under the N5 viewing procedure'


class RuleError(ValueError):
    """A failed check of the computation phase with a fixed, value-free message; it passes `withheld` unchanged."""


def _rule(condition, message):
    if not condition:
        raise RuleError(message)


@contextmanager
def withheld():
    """Re-raise any exception of the computation phase, except a RuleError, as a value-free RuntimeError with the
    original suppressed (spec 8.3)."""
    try:
        yield
    except RuleError:
        raise
    except Exception as exc:
        raise RuntimeError(WITHHELD.format(type(exc).__name__)) from None


def period_returns(daily):
    """(sessions, returns) of the daily (session, nav) rows inside the walk-forward period, each return based on the
    previous row, so the first is based on the last session before the period (or the start session)."""
    first, last = WALK_FORWARD
    keep = [i for i in range(1, len(daily)) if first <= daily[i][0] <= last]
    return [daily[i][0] for i in keep], np.array([daily[i][1] / daily[i - 1][1] - 1 for i in keep], dtype=float)


def _bil_in_period(bil, sessions, where):
    """BIL returns on the candidate's sessions; the BIL sessions of the period must be the same sessions."""
    first, last = WALK_FORWARD
    _rule([s for s in bil if first <= s <= last] == sessions, f'{where}: BIL sessions differ from the run sessions')
    return np.array([bil[s] for s in sessions], dtype=float)


def compare(series, bil, candidate, comparator, p_values=True):
    """DeltaU, the mean-excess difference, the minimum-effect flags and, for each block length, the basic interval and
    (with p_values) the one-sided p of the paired bootstrap (spec 6.2, 6.3, 7.3)."""
    where = f'comparison {candidate} vs {comparator}'
    (sc, rc), (sk, rk) = series[candidate], series[comparator]
    _rule(sc == sk and len(sc) > 1, f'{where}: candidate and comparator sessions differ')
    rb = _bil_in_period(bil[candidate], sc, where)
    results = {n: inference.paired_bootstrap(rc, rk, rb, n, replicates=REPLICATES, seed=SEED) for n in LENGTHS}
    main = results[PRIMARY_LENGTH]
    out = {'candidate': candidate, 'comparator': comparator, 'delta_u': main['delta_u'],
           'mean_excess_difference': main['mean_excess_difference'],
           'meets_minimum_effect': {'delta_u_at_least_minimum': main['delta_u'] >= MINIMUM_EFFECT,
                                    'mean_excess_difference_positive': main['mean_excess_difference'] > 0},
           'intervals': {str(n): {'ci_low': results[n]['ci_low'], 'ci_high': results[n]['ci_high']} for n in LENGTHS}}
    if p_values:
        out['p_values'] = {str(n): results[n]['p'] for n in LENGTHS}
    return out


def annual_differences(sessions, r_candidate, r_comparator):
    """Per calendar year the sum of the daily candidate-minus-comparator returns, the number of positive years and
    the largest positive annual sum as a share of the sum of the positive annual sums (protocol line 186)."""
    diff = np.asarray(r_candidate, dtype=float) - np.asarray(r_comparator, dtype=float)
    years = {}
    for session, d in zip(sessions, diff):
        years.setdefault(session[:4], []).append(float(d))
    sums = {year: math.fsum(values) for year, values in years.items()}
    positive = [v for v in sums.values() if v > 0]
    return {'years': sums, 'positive_years': len(positive),
            'largest_positive_share': max(positive) / math.fsum(positive) if positive else None}


def _previous_month(month):
    year, m = int(month[:4]), int(month[5:7])
    return f'{year - 1}-12' if m == 1 else f'{year}-{m - 1:02d}'


def month_ends(daily):
    """The base month-end and the month-end sessions of the complete months of the walk-forward period: a month counts
    only if its last XNYS session is inside the period and in the daily rows (spec 6.5)."""
    first, last = WALK_FORWARD
    present = {s for s, _ in daily}
    months = sorted({s[:7] for s, _ in daily if first <= s <= last})
    _rule(months != [], 'no month of the walk-forward period in the daily rows')
    base = xnys_month_end(_previous_month(months[0]))
    complete = [m for m in months if first <= xnys_month_end(m) <= last and xnys_month_end(m) in present]
    _rule(base in present, 'the base month-end of the walk-forward period is not in the daily rows')
    _rule(complete != [] and complete == months[:len(complete)], 'the complete months are not consecutive')
    return [base, *(xnys_month_end(m) for m in complete)]


def regression_block(names, y, X):
    """OLS with Newey-West standard errors (lag 3) and the annual alpha, or, when annual_alpha gives a reason,
    coefficients, standard errors and alpha all null with that reason (spec 6.5, P9)."""
    with np.errstate(all='ignore'):
        fit = inference.regress(np.asarray(y, dtype=float), np.asarray(X, dtype=float), lag=NW_LAG)
        alpha = inference.annual_alpha(fit)
    gated = alpha['reason'] is not None
    return {'regressors': ['intercept', *names], 'months': fit['n'], 'k': fit['k'], 'rank': fit['rank'],
            'cond': number(fit['cond']),
            'coefficients': None if gated else [float(v) for v in fit['coef']],
            'standard_errors': None if gated else [float(v) for v in fit['se']],
            'alpha': alpha['alpha'], 'se': alpha['se'], 'ci_low': alpha['ci_low'], 'ci_high': alpha['ci_high'],
            'reason': alpha['reason']}


def regression_inputs(label, rows, comparator, comparator_rows, tri):
    """(y, Model A regressor, class proxies) on the complete months of the walk-forward period: y = R - R_BIL, the
    comparator's R - R_BIL and the four class proxies of the member ETF excess returns over BIL, from the daily
    (session, nav) rows and the total-return frame `tri` (spec 6.5, P10)."""
    ends = month_ends(rows)
    _rule(month_ends(comparator_rows) == ends, f'regression {label}: months differ from those of {comparator}')
    _rule(all(s in tri.index for s in ends), f'regression {label}: month-ends missing from the BIL index')
    r_bil = inference.monthly_returns(tri.loc[ends, CASH])
    nav, nav_comparator = dict(rows), dict(comparator_rows)
    y = inference.monthly_returns({s: nav[s] for s in ends}) - r_bil
    x_a = inference.monthly_returns({s: nav_comparator[s] for s in ends}) - r_bil
    members = [t for group in GROUPS.values() for t in group]
    excess = pd.DataFrame({t: inference.monthly_returns(tri.loc[ends, t]) - r_bil for t in members})
    proxies = inference.class_proxies(excess, GROUPS)[list(GROUPS)]
    _rule(list(y.index) == list(x_a.index) == list(proxies.index), f'regression {label}: month labels differ')
    return y, x_a, proxies


def regressions(daily, index):
    """Models A and B for the six configurations and P_A1 on the complete months of the walk-forward period:
    y = R - R_BIL; Model A on the comparator's excess return, Model B on the four class proxies (spec 6.5, P10)."""
    out = {}
    for label, comparator in REGRESSION_COMPARATOR.items():
        y, x_a, proxies = regression_inputs(label, daily[label], comparator, daily[comparator],
                                            index[daily[label][-1][0]])
        out[label] = {'comparator': comparator,
                      'model_a': regression_block([comparator], y.to_numpy(), x_a.to_numpy()),
                      'model_b': regression_block(list(GROUPS), y.to_numpy(), proxies.to_numpy())}
    return out


def evaluation_document(root, runs, log, expected_sha256):
    """The whitelisted evaluation document (T1-T6) from verified runs and the checked selection log."""
    first = runs['B0'].config
    market = load_market(root, (root / first['vintage']).resolve(), expected_sha256)
    daily = {label: _read_daily(run.path, market, run.config) for label, run in runs.items()}
    lasts = sorted({rows[-1][0] for rows in daily.values()})
    _rule(all(last <= LAST_OPEN_SESSION for last in lasts), 'a run ends after the last open session')
    bil_by_last = {last: bil_returns(market, last) for last in lasts}
    index = {last: total_return_index(market.history(last)) for last in lasts}
    bil = {label: bil_by_last[rows[-1][0]] for label, rows in daily.items()}
    series = {label: period_returns(rows) for label, rows in daily.items()}
    primary = [compare(series, bil, c, k) for c, k in PRIMARY]
    adjusted = inference.holm({f'{e["candidate"]} vs {e["comparator"]}': e['p_values'][str(PRIMARY_LENGTH)]
                               for e in primary})
    for e in primary:
        e['holm_p'] = adjusted[f'{e["candidate"]} vs {e["comparator"]}']
    supplementary = [compare(series, bil, c, k) for c, k in SUPPLEMENTARY]
    policy = {**compare(series, bil, *POLICY_COMPARISON, p_values=False), 'note': POLICY_NOTE}

    def annual(pairs):
        return [{'candidate': c, 'comparator': k, **annual_differences(series[c][0], series[c][1], series[k][1])}
                for c, k in pairs]
    sessions = series['H1_252_3'][0]
    policy_config = runs[POLICY].config
    return {
        'window': {'continuous': {'start_session': first['start_session'], 'end_session': first['end_session']},
                   'policy': {'start_session': policy_config['start_session'],
                              'end_session': policy_config['end_session']},
                   'walk_forward': {'period_start': WALK_FORWARD[0], 'period_end': WALK_FORWARD[1],
                                    'first_session': sessions[0], 'last_session': sessions[-1],
                                    'returns': len(sessions)}},
        'scenario': first['scenario'], 'initial_cash': first['initial_cash'],
        'manifest_sha256': first['manifest_sha256'],
        'provider_versions': {label: run.config['provider']['version'] for label, run in runs.items()},
        'metrics': {label: run.metrics for label, run in runs.items()},
        'comparisons': {'method': {'replicates': REPLICATES, 'seed': SEED, 'lengths': list(LENGTHS),
                                   'primary_length': PRIMARY_LENGTH, 'holm_family_length': PRIMARY_LENGTH},
                        'primary': primary, 'supplementary': supplementary, 'policy': [policy]},
        'annual_differences': {'primary': annual(PRIMARY), 'supplementary': annual(SUPPLEMENTARY),
                               'policy': annual([POLICY_COMPARISON])},
        'regressions': {'method': {'covariance': 'Newey-West, Bartlett kernel', 'lag': NW_LAG,
                                   'finite_sample_factor': 'n/(n-k), k counting the intercept',
                                   'interval': 'asymptotic normal, estimate +/- 1.96 standard errors',
                                   'annual_alpha': '12 x monthly intercept',
                                   'gates': 'months < 36, rank deficiency, condition number > 1e8'},
                        'candidates': regressions(daily, index)},
        'selection': log,
        'disclosures': list(DISCLOSURES),
    }


def enforce_whitelist(document, body, markdown, forbidden):
    """The document holds exactly the whitelisted keys, and neither file holds a run id or a path (spec 7.2)."""
    _rule(isinstance(document, dict) and list(document) == list(DOCUMENT_KEYS),
          'evaluation document keys are not the whitelist')
    texts = (body.decode('utf-8'), markdown.decode('utf-8'))
    # Each forbidden string also in its JSON-escaped forms (a Windows path has its backslashes doubled in JSON).
    forms = {g for f in forbidden if f for g in (f, json.dumps(f, ensure_ascii=False)[1:-1], json.dumps(f)[1:-1])}
    _rule(not any(f in text for f in forms for text in texts),
          'evaluation document holds a run id or a path')


# --- Markdown --------------------------------------------------------------------------------------------------------

def _cell(value, spec='.6f'):
    if value is None:
        return 'n/a'
    if isinstance(value, bool):
        return 'true' if value else 'false'
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return format(value, spec)
    return str(value)


def _interval(block):
    return f'[{_cell(block["ci_low"])}, {_cell(block["ci_high"])}]'


def _pairs(names, values, spec='.6f'):
    return 'n/a' if values is None else '; '.join(f'{n} {_cell(v, spec)}' for n, v in zip(names, values))


def _metric(key, value):
    """A T1 cell: counts as integers, turnover as a multiple, other keys as in the N3 report (report.number)."""
    if value is None:
        return 'n/a'
    if isinstance(value, int) and not isinstance(value, bool):
        return str(value)
    if key == 'turnover':
        return f'{value:.2f}x'
    return report.number(key, value)


def render_markdown(document):
    """Deterministic Markdown tables of the document sections T1-T6; a pure function of the document.

    T1 holds every metric of metrics.json for every run and period: the scalar metrics in one table per period
    (report.SUMMARY first, then the other keys in sorted order) and one table per period for each of mean_group,
    max_group, mean_weight and max_weight (groups in GROUPS order, tickers sorted)."""
    window, metrics = document['window'], document['metrics']
    wf = window['walk_forward']
    labels = [k for k in KEYS if k in metrics] + sorted(k for k in metrics if k not in KEYS)
    out = ['# N5 evaluation report', '',
           f"Continuous accounts {window['continuous']['start_session']} to {window['continuous']['end_session']}; "
           f"P_A1 and its comparator {window['policy']['start_session']} to {window['policy']['end_session']}; "
           f"walk-forward statistics {wf['first_session']} to {wf['last_session']} ({wf['returns']} daily returns, "
           f"period {wf['period_start']} to {wf['period_end']}). Initial cash {document['initial_cash']:.2f}, scenario "
           f"{json.dumps(document['scenario'], sort_keys=True)}, vintage manifest {document['manifest_sha256']}.", '',
           report.table(['run', 'provider version'], [[k, str(document['provider_versions'][k])] for k in labels]), '',
           '## T1 Metrics', '']
    names = [name for name, _, _ in PERIODS]
    present = {p for k in labels for p in metrics[k]['periods']}
    for period in [p for p in names if p in present] + sorted(present - set(names)):
        mine = [k for k in labels if period in metrics[k]['periods']]
        values = {k: metrics[k]['periods'][period] for k in mine}
        keys = {key for v in values.values() for key in v}
        tables = sorted(key for key in keys if any(isinstance(v.get(key), dict) for v in values.values()))
        scalars = [key for key in report.SUMMARY if key in keys] + sorted(keys - set(report.SUMMARY) - set(tables))
        rows = [[k, *(_metric(key, values[k].get(key)) for key in scalars)] for k in mine]
        out += [f'### {period}', '', report.table(['run', *scalars], rows), '']
        for key in tables:
            members = {m for v in values.values() for m in (v.get(key) or {})}
            columns = [g for g in GROUPS if g in members] + sorted(members - set(GROUPS))
            rows = [[k, *(_metric('x', (values[k].get(key) or {}).get(m)) for m in columns)] for k in mine]
            out += [f'### {period} {key}', '', report.table(['run', *columns], rows), '']
    comparisons = document['comparisons']
    method = comparisons['method']
    lengths = [str(n) for n in method['lengths']]
    header = ['group', 'candidate', 'comparator', 'delta_u', 'mean_excess_difference', 'delta_u >= 0.01',
              'mean_excess_difference > 0', *(f'interval L={n}' for n in lengths), *(f'p L={n}' for n in lengths),
              f"Holm p L={method['holm_family_length']}"]
    rows = []
    for group in ('primary', 'supplementary', 'policy'):
        for e in comparisons[group]:
            flags = e['meets_minimum_effect']
            p = e.get('p_values')
            rows.append([group, e['candidate'], e['comparator'], _cell(e['delta_u']),
                         _cell(e['mean_excess_difference']), _cell(flags['delta_u_at_least_minimum']),
                         _cell(flags['mean_excess_difference_positive']),
                         *(_interval(e['intervals'][n]) for n in lengths),
                         *((_cell(p[n], '.4f') for n in lengths) if p else ['n/a'] * len(lengths)),
                         _cell(e.get('holm_p'), '.4f')])
    out += ['## T2 Comparisons (walk-forward period)', '',
            f"Paired circular block bootstrap, {method['replicates']} replicates, seed {method['seed']}, block lengths "
            f"{', '.join(lengths)}, primary length {method['primary_length']}; Holm adjustment over the primary family "
            f"at L={method['holm_family_length']}.", '', report.table(header, rows), '']
    out += [f"{e['candidate']} vs {e['comparator']}: {e['note']}." for e in comparisons['policy'] if 'note' in e]
    out += ['']
    annual = document['annual_differences']
    years = sorted({y for group in annual.values() for e in group for y in e['years']})
    rows = [[group, e['candidate'], e['comparator'], *(_cell(e['years'].get(y)) for y in years),
             _cell(e['positive_years']), _cell(e['largest_positive_share'], '.4f')]
            for group in ('primary', 'supplementary', 'policy') for e in annual[group]]
    out += ['## T3 Annual differences (sum of daily candidate minus comparator returns)', '',
            report.table(['group', 'candidate', 'comparator', *years, 'positive years', 'largest positive share'],
                         rows), '']
    reg = document['regressions']
    rows = []
    candidates = reg['candidates']
    order = [k for k in REGRESSION_COMPARATOR if k in candidates]
    for label in order + sorted(set(candidates) - set(order)):
        block = candidates[label]
        for model in ('model_a', 'model_b'):
            fit = block[model]
            rows.append([label, model, ', '.join(fit['regressors']), _cell(fit['months']), _cell(fit['k']),
                         _cell(fit['rank']), _cell(fit['cond'], '.3e'),
                         _pairs(fit['regressors'], fit['coefficients']),
                         _pairs(fit['regressors'], fit['standard_errors']), _cell(fit['alpha']), _cell(fit['se']),
                         _interval(fit), _cell(fit['reason'])])
    out += ['## T4 Regressions (complete months of the walk-forward period)', '',
            '; '.join(f'{k}: {v}' for k, v in reg['method'].items()) + '.', '',
            report.table(['candidate', 'model', 'regressors', 'months', 'k', 'rank', 'cond', 'coefficients',
                          'HAC standard errors', 'annual alpha', 'alpha se', 'alpha interval', 'reason'], rows), '']
    log = document['selection']
    names = sorted({c for e in log for c in e['utility']}, key=lambda c: (CANDIDATES + (c,)).index(c))
    rows = [[_cell(e['year']), e['selection_date'], f"{e['segment_start']} to {e['segment_end']}",
             _cell(e['decisions']), _cell(e['returns']), *(_cell(e['utility'].get(c)) for c in names),
             _cell(e['best_utility']), ', '.join(e['close_set']), e['chosen'], _cell(e['fallback']),
             _cell(e['warning']), *(_cell(e['stability']['frequency'].get(c), '.3f') for c in names),
             _cell(e['stability']['fallback_replicates'])] for e in log]
    out += ['## T5 P_A1 selection log', '',
            report.table(['year', 'selection date', 'validation segment', 'decisions', 'returns',
                          *(f'U {c}' for c in names), 'best U', 'close set', 'chosen', 'fallback', 'warning',
                          *(f'frequency {c}' for c in names), 'fallback replicates'], rows), '']
    out += ['## T6 Disclosures', '', *(f'- {s}' for s in document['disclosures']), '']
    return '\n'.join(out)


# --- The journaled report --------------------------------------------------------------------------------------------

def build_evaluation(root, run_dirs, parent=None, expected_sha256=VINTAGE_MANIFEST_SHA256):
    """Journaled N5 evaluation report: verifies the thirteen runs (items 1-5) and the selection log (item 6), then
    computes and freezes evaluation.json (canonical) and evaluation.md in data/reports/<run_id>; run ids and run
    manifest hashes go to the manifest metadata only. Returns the report directory."""
    root = Path(root).resolve()
    config = {'runs': [project_path(root, (root / d).resolve()) for d in run_dirs], 'expected_sha256': expected_sha256}
    run = provenance.Run(root, REPORT_PURPOSE, config, parent, candidate_ids=list(KEYS))
    run.base['seed'] = SEED  # the paired bootstrap seed, in the started and the terminal record
    run.base['null_reasons']['seed'] = None
    with run:
        report.require(run.base['dirty_tree'] is False, 'item 3, report: the report tree is dirty')
        runs = verified_n5_runs(root, run_dirs, expected_sha256, run.base, references=REFERENCES)
        with rule(6, f'{POLICY} selection.json'):
            log = report.read_json(runs[POLICY].path / 'selection.json')
        check_selection_log(log, runs)
        with withheld():
            document = evaluation_document(root, runs, log, expected_sha256)
            body = canonical_bytes(document)
            markdown = render_markdown(json.loads(body)).encode('utf-8')
            forbidden = [run.run_id, *(r.path.name for r in runs.values()), *REFERENCES.values(), str(root),
                         root.as_posix(), 'data/runs', 'data/reports']
            enforce_whitelist(document, body, markdown, forbidden)
            sources = [{'candidate': label, 'run_id': r.path.name,
                        'manifest_sha256': sha256((r.path / 'manifest.json').read_bytes())}
                       for label, r in runs.items()]
            target = root / 'data/reports' / run.run_id
            freeze(target, {'evaluation.json': body, 'evaluation.md': markdown},
                   {'sources': sources, 'environment': run.env, 'run_id': run.run_id})
            run.finish('completed', [project_path(root, target)], sha256((target / 'manifest.json').read_bytes()), [])
    return target
