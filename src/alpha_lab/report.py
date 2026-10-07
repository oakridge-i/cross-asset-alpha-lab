"""Journaled N3 benchmark report: verifies the five benchmark runs and freezes deterministic summary tables."""
from contextlib import contextmanager
import json
from pathlib import Path
from alpha_lab.engine import PROVIDERS
from alpha_lab.market import VINTAGE_MANIFEST_SHA256
from alpha_lab.metrics import METRICS_SCHEMA, PERIODS
from alpha_lab.pipeline import project_path
from alpha_lab.provenance import Run, canonical_bytes, freeze, sha256, verify

BENCHMARKS = ('B0', 'B1', 'B2', 'B3', 'REF_SPY')
RUN_FILES = {'config.json', 'decisions.csv', 'orders.csv', 'trades.csv', 'payouts.csv', 'daily.csv',
             'invariants.json', 'weights.csv', 'metrics.json'}
SHARED = ('manifest_sha256', 'scenario', 'start_session', 'end_session', 'initial_cash')
AGREE = ('provider', 'scenario', 'start_session', 'end_session', 'decision_sessions', 'initial_cash')
SUMMARY = ('total_return', 'cagr', 'volatility', 'mean_excess', 'sharpe_bil', 'utility', 'max_drawdown', 'decisions',
           'turnover_annual', 'costs_usd', 'cost_ratio', 'mean_cash_plus_bil', 'mean_receivables', 'mean_risky',
           'mean_target_risky')
ANNUAL = ('total_return', 'volatility', 'mean_excess', 'sharpe_bil', 'max_drawdown')
DECIMALS = {'sharpe_bil': 3, 'utility': 3}
PLAIN = {'decisions': '{:d}', 'costs_usd': '{:.2f}'}
ORDER = [name for name, _, _ in PERIODS]


def journal_rows(root):
    path = root / 'experiments/EXPERIMENT_LOG.jsonl'
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line]


def read_json(path):
    return json.loads(path.read_bytes())


@contextmanager
def well_formed(label):
    """Missing keys or wrong types in a run's files or journal rows are a failed check, not a crash."""
    try:
        yield
    except (KeyError, TypeError, AttributeError, IndexError) as exc:
        raise ValueError(f'{label}: malformed run data ({type(exc).__name__}: {exc})') from exc


def require(condition, message):
    if not condition:
        raise ValueError(message)


def check_journal(root, run_dir, rows, config):
    """Check 3: one started and one completed record, clean tree, outputs, data hash and config agreement."""
    mine = [r for r in rows if r.get('run_id') == run_dir.name]
    started = [r for r in mine if r['event'] == 'started']
    terminal = [r for r in mine if r['event'] != 'started']
    require(len(started) == 1 and len(terminal) == 1, f'{run_dir.name}: needs one started and one terminal record')
    started, terminal = started[0], terminal[0]
    require(terminal['event'] == terminal['status'] == 'completed',
            f'{run_dir.name}: run status is {terminal["status"]}, not completed')
    for record in (started, terminal):
        require(record['dirty_tree'] is False, f'{run_dir.name}: dirty_tree is not false')
        require(record['git_sha'], f'{run_dir.name}: git_sha is null')
    require(terminal['output_paths'] == [f'data/runs/{run_dir.name}'], f'{run_dir.name}: unexpected output_paths')
    require(terminal['data_sha256'] == sha256((run_dir / 'manifest.json').read_bytes()),
            f'{run_dir.name}: data_sha256 differs from the manifest hash')
    require(started['config_sha256'] == sha256(canonical_bytes(started['config'])),
            f'{run_dir.name}: config_sha256 differs from the journaled config')
    for key in AGREE:
        require(started['config'].get(key) == config.get(key), f'{run_dir.name}: journaled {key} differs from config.json')


def common_periods(metrics):
    """Identical period key sets across the metrics documents; returns the keys in canonical order."""
    keys = [set(m['periods']) for m in metrics.values()]
    require(all(k == keys[0] for k in keys), 'metrics documents have different periods')
    return sorted(keys[0], key=lambda k: (ORDER.index(k) if k in ORDER else len(ORDER), k))


def verified_runs(root, run_dirs, expected_sha256):
    """Checks 1-5 in order; returns {benchmark: (run_dir, manifest, config, metrics)}."""
    require(len(run_dirs) == len(BENCHMARKS), f'exactly five run directories required, got {len(run_dirs)}')
    dirs = []
    for d in run_dirs:
        path = (root / d).resolve()
        require(path.parent == (root / 'data/runs').resolve(), f'run directory outside data/runs: {d}')
        dirs.append(path)
    found = {}
    for path in dirs:
        with well_formed(path.name):
            manifest = verify(path)
            require(set(manifest['files']) == RUN_FILES, f'{path.name}: not a benchmark run')
            config = read_json(path / 'config.json')
            found.setdefault(config['provider']['name'], []).append((path, manifest, config))
    require(sorted(found) == sorted(BENCHMARKS) and all(len(v) == 1 for v in found.values()),
            'each of B0, B1, B2, B3 and REF_SPY is required exactly once')
    rows = journal_rows(root)
    out = {}
    for name in BENCHMARKS:
        path, manifest, config = found[name][0]
        with well_formed(path.name):
            check_journal(root, path, rows, config)
            require(read_json(path / 'invariants.json')['passed'] is True, f'{path.name}: invariants did not pass')
            metrics = read_json(path / 'metrics.json')
            require(config['provider']['version'] == PROVIDERS[name].version, f'{name}: provider version is not current')
            require(metrics['schema_version'] == METRICS_SCHEMA, f'{name}: metrics schema version is not current')
            require(config['manifest_sha256'] == expected_sha256 == manifest['metadata']['derived_manifest_sha256'],
                    f'{name}: vintage manifest hash is not the approved one')
            out[name] = (path, manifest, config, metrics)
    first = out[BENCHMARKS[0]][2]
    for name, (_, _, config, _) in out.items():
        with well_formed(name):
            for key in SHARED:
                require(config[key] == first[key], f'{name}: {key} differs from B0')
    with well_formed('metrics'):
        common_periods({n: v[3] for n, v in out.items()})
    return out


def number(key, value):
    if value is None:
        return 'n/a'
    if key in PLAIN:
        return PLAIN[key].format(value)
    if key in DECIMALS:
        return f'{value:.{DECIMALS[key]}f}'
    return f'{value * 100:.2f}%'


def table(header, rows):
    lines = ['| ' + ' | '.join(header) + ' |', '|' + '|'.join(['---'] * len(header)) + '|']
    lines += ['| ' + ' | '.join(row) + ' |' for row in rows]
    return '\n'.join(lines)


def render_markdown(document):
    """Deterministic Markdown tables, a pure function of the report document."""
    benchmarks = document['benchmarks']
    names = list(benchmarks)
    periods = common_periods(benchmarks)
    years = [p for p in periods if p.isdigit()]
    out = ['# Benchmarks', '', f"Window {document['window']['start_session']} to {document['window']['end_session']}, "
           f"initial cash {document['initial_cash']:.2f}, scenario {json.dumps(document['scenario'], sort_keys=True)}.", '']
    for period in (p for p in periods if not p.isdigit()):
        rows = [[n, *(number(k, benchmarks[n]['periods'][period][k]) for k in SUMMARY)] for n in names]
        out += [f'## {period}', '', table(['benchmark', *SUMMARY], rows), '']
    for key in ANNUAL:
        rows = [[y, *(number(key, benchmarks[n]['periods'][y][key]) for n in names)] for y in years]
        if rows:
            out += [f'## Annual {key}', '', table(['year', *names], rows), '']
    if 'full' in periods:
        groups = list(benchmarks[names[0]]['periods']['full']['mean_group'])
        header = ['benchmark', *(f'mean {g}' for g in groups), *(f'max {g}' for g in groups), 'max weight']
        rows = []
        for n in names:
            full = benchmarks[n]['periods']['full']
            rows.append([n, *(number('x', full['mean_group'][g]) for g in groups),
                         *(number('x', full['max_group'][g]) for g in groups),
                         number('x', max(full['max_weight'].values()))])
        out += ['## Groups (full)', '', table(header, rows), '']
    return '\n'.join(out)


def build_report(root, run_dirs, parent=None, expected_sha256=VINTAGE_MANIFEST_SHA256):
    """Journaled report on five verified benchmark runs; returns data/reports/<run_id>."""
    root = Path(root).resolve()
    config = {'runs': [project_path(root, (root / d).resolve()) for d in run_dirs], 'expected_sha256': expected_sha256}
    with Run(root, 'N3 benchmark report', config, parent, candidate_ids=BENCHMARKS) as run:
        runs = verified_runs(root, run_dirs, expected_sha256)
        first = runs[BENCHMARKS[0]][2]
        document = {'window': {k: first[k] for k in ('start_session', 'end_session')}, 'scenario': first['scenario'],
                    'initial_cash': first['initial_cash'], 'benchmarks': {n: runs[n][3] for n in BENCHMARKS}}
        files = {'benchmarks.json': canonical_bytes(document),
                 'benchmarks.md': render_markdown(document).encode('utf-8')}
        sources = [{'candidate': n, 'run_id': runs[n][0].name,
                    'manifest_sha256': sha256((runs[n][0] / 'manifest.json').read_bytes())} for n in BENCHMARKS]
        target = root / 'data/reports' / run.run_id
        freeze(target, files, {'sources': sources, 'environment': run.env, 'run_id': run.run_id})
        run.finish('completed', [project_path(root, target)], sha256((target / 'manifest.json').read_bytes()), [])
    return target
