"""Network acquisition and deterministic offline audit/replay commands."""
import io
import json
from pathlib import Path
import numpy as np
import pandas as pd
from .acquire import download
from .normalize import normalize, REQUIRED
from .quality import parse_chart, assess
from .provenance import Run, canonical_bytes, freeze, now, sha256, verify


def normalized(source, manifest, payable, corrections=None):
    """Full-history normalized frames after raw/adapter cross-checks; shared by audit and reconciliation.
    corrections is {ticker: {ex_date: {...}}}; a ticker outside the universe is rejected, not ignored."""
    cfg = manifest['metadata']['config']
    corrections = corrections or {}
    if unknown := set(corrections) - set(cfg['universe']):
        raise ValueError(f'correction for ticker(s) outside the universe: {sorted(unknown)}')
    frames = {}
    for ticker in cfg['universe']:
        candidates = []
        for name in manifest['files']:
            if name.startswith(f'raw/{ticker}-') and name.endswith('.json'):
                try:
                    body = (source / name).read_bytes()
                    count = len(json.loads(body)['chart']['result'][0].get('timestamp', []))
                    candidates.append((count, name))
                except (KeyError, TypeError, IndexError, json.JSONDecodeError):
                    continue  # failed request remains in raw evidence; full successful request required
        if not candidates:
            raise ValueError(f'no chart for {ticker}')
        _, name = max(candidates)
        f = parse_chart((source / name).read_bytes(), ticker)
        f = f.loc[cfg['start']:cfg['cutoff']]
        adapter = pd.read_csv(source / f'adapter/{ticker}.csv', index_col=0, float_precision='round_trip')
        # Offset-bearing yfinance dates are local midnight; preserve the session date.
        adapter.index = pd.to_datetime(adapter.index.str[:10])
        if list(f.index) != list(adapter.index) or not set(REQUIRED).issubset(adapter.columns):
            raise ValueError(f'adapter session/schema mismatch: {ticker}')
        for col in REQUIRED:
            if not np.allclose(f[col], adapter[col], rtol=0, atol=1e-12, equal_nan=True):
                raise ValueError(f'adapter/raw value mismatch: {ticker}/{col}')
        gains = adapter['Capital Gains'] if 'Capital Gains' in adapter.columns else 0.
        if not np.allclose(f['Capital Gains'], gains, rtol=0, atol=1e-12):
            raise ValueError(f'adapter/raw value mismatch: {ticker}/Capital Gains')
        x = normalize(f, ticker, manifest['metadata']['retrieved_at'], manifest['files'][name],
                      payable.get(ticker, {}), pay_delay_days=cfg['pay_delay_days'],
                      corrections=corrections.get(ticker, {}))
        frames[ticker] = x
    return frames


def build(source, manifest, payable, corrections=None):
    cfg = manifest['metadata']['config']
    corrections = corrections or {}
    frames = normalized(source, manifest, payable, corrections)
    files = {f'normalized/{t}.csv': x.to_csv(lineterminator='\n').encode() for t, x in frames.items()}
    report = assess(frames, cfg['common_start'], cfg['cutoff'],
                    adjustment_tolerance=cfg['adjustment_factor_tolerance'])
    files['quality.json'] = canonical_bytes(report)
    files['payable.json'] = canonical_bytes(payable)
    # Always present (possibly empty), alongside payable.json, so replay rebuilds identically either way.
    files['corrections.json'] = canonical_bytes(corrections)
    return files, report


def load_json(root, path, purpose, cfg, parent):
    """Read a JSON input; an unreadable file is still journaled as a failed run of `purpose`."""
    path = (Path(root) / path).resolve()
    try:
        return json.loads(path.read_bytes())
    except (OSError, ValueError):
        with Run(root, purpose, cfg | {'unreadable_input': project_path(root, path)}, parent):
            raise


def acquire_snapshot(root, config, parent=None, *, downloader=None):
    """config is a dict or a path relative to root; downloader defaults to the yfinance adapter."""
    root = Path(root).resolve()
    if isinstance(config, Path):
        config = load_json(root, config, 'N1 acquisition', {}, parent)
    with Run(root, 'N1 acquisition', config, parent) as run:
        if downloader is None:
            import yfinance as yf
            cache = root / 'data/yfinance-cache'
            cache.mkdir(parents=True, exist_ok=True)
            yf.set_tz_cache_location(str(cache))
            downloader = download
        files = {}
        target = root / 'data/snapshots' / run.run_id
        run.base['output_paths'] = [target.relative_to(root).as_posix()]
        try:
            downloader(config['universe'], config['start'], config['end_exclusive'], files)
        finally:
            freeze(target, files, {'config': config, 'environment': run.env, 'retrieved_at': now(),
                                   'run_id': run.run_id, 'git_sha': run.base['git_sha']})
            run.base['data_sha256'] = sha256((target / 'manifest.json').read_bytes())
            run.base['null_reasons']['data_sha256'] = None
        run.finish('completed', run.base['output_paths'], run.base['data_sha256'], [])
    return target


def project_path(root, path):
    """POSIX path for run configs; out-of-project paths stay absolute so the refusal is logged."""
    return path.relative_to(root).as_posix() if path.is_relative_to(root) else path.as_posix()


def require_inside(root, *paths):
    for path in paths:
        if not path.is_relative_to(root):
            raise ValueError(f'snapshot outside project: {path}')


def audit_snapshot(root, source, parent=None, payable=None, corrections=None):
    """payable and corrections are each a dict or a path relative to root (an unreadable file is
    journaled as failed)."""
    root, source = Path(root).resolve(), Path(source).resolve()
    if isinstance(payable, Path):
        payable = load_json(root, payable, 'N1 offline QA', {'source_snapshot': project_path(root, source)}, parent)
    if isinstance(corrections, Path):
        corrections = load_json(root, corrections, 'N1 offline QA',
                                {'source_snapshot': project_path(root, source)}, parent)
    # Start before verifying, so corruption/missing manifests are also logged.
    cfg = {'source_snapshot': project_path(root, source), 'payable': payable or {}, 'corrections': corrections or {}}
    with Run(root, 'N1 offline QA', cfg, parent) as run:
        require_inside(root, source)
        manifest = verify(source)
        run.base['source_manifest_sha256'] = sha256((source / 'manifest.json').read_bytes())
        run.base.update(universe=manifest['metadata']['config']['universe'],
                        splits=manifest['metadata']['config'].get('splits', {}))
        source_hash = sha256((source / 'manifest.json').read_bytes())
        files, report = build(source, manifest, payable or {}, corrections or {})
        target = root / 'data/derived' / run.run_id
        freeze(target, files, {'source_snapshot': source.relative_to(root).as_posix(),
                              'source_manifest_sha256': source_hash, 'environment': run.env,
                              'config': manifest['metadata']['config'], 'run_id':run.run_id})
        run.finish('completed' if report['technical_pass'] else 'quality_failed',
                   [target.relative_to(root).as_posix()], sha256((target/'manifest.json').read_bytes()), report['warnings'])
    return target


def replay_snapshot(root, derived, parent=None):
    root, derived = Path(root).resolve(), Path(derived).resolve()
    with Run(root, 'N1 offline replay', {'derived_snapshot':project_path(root, derived)}, parent) as run:
        require_inside(root, derived)
        m = verify(derived)
        run.base['derived_manifest_sha256'] = sha256((derived / 'manifest.json').read_bytes())
        source = (root / m['metadata']['source_snapshot']).resolve()
        if not source.is_relative_to(root):
            raise ValueError('source snapshot outside project')
        sm = verify(source)
        run.base['source_manifest_sha256'] = sha256((source/'manifest.json').read_bytes())
        if run.base['source_manifest_sha256'] != m['metadata']['source_manifest_sha256']:
            raise ValueError('source manifest changed')
        payable = json.loads((derived/'payable.json').read_bytes())
        corrections = json.loads((derived/'corrections.json').read_bytes())
        files, report = build(source, sm, payable, corrections)
        if {k:sha256(v) for k,v in files.items()} != m['files']:
            raise ValueError('replay differs from frozen derived files')
        run.base.update(universe=sm['metadata']['config']['universe'], splits=sm['metadata']['config'].get('splits',{}))
        run.finish('completed', [derived.relative_to(root).as_posix()], sha256((derived/'manifest.json').read_bytes()),
                   ['Exact replay does not certify data quality.'])
    return True
