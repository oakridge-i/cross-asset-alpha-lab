"""N5 evaluation report, part 1: verification of the thirteen N5 runs before any evaluation figure is computed (spec
7.1 items 1-5; D025 items 12, 16 and 17).

Error messages name the rule ('item <n>') and the run directory or label and, where relevant, the file, period and
metric, and never carry a value read from a file; the original exception is suppressed (spec 8.3)."""
from collections import namedtuple
from contextlib import contextmanager
import math
from pathlib import Path
from alpha_lab import hypothesis_report as hr, provenance, report
from alpha_lab.engine import PROVIDERS, STAGE_PURPOSES
from alpha_lab.features import CASH, total_return_index
from alpha_lab.market import LAST_OPEN_SESSION, load_market
from alpha_lab.metrics import METRICS_SCHEMA, PERIODS, WF_PERIODS
from alpha_lab.provenance import canonical_bytes

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
