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


def normalized(source, manifest, payable):
    """Full-history normalized frames after raw/adapter cross-checks; shared by audit and reconciliation."""
    cfg = manifest['metadata']['config']
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
        x = normalize(f, ticker, manifest['metadata']['retrieved_at'], manifest['files'][name],
                      payable.get(ticker, {}), pay_delay_days=cfg['pay_delay_days'])
        frames[ticker] = x
    return frames


def build(source, manifest, payable):
    cfg = manifest['metadata']['config']
    frames = normalized(source, manifest, payable)
    files = {f'normalized/{t}.csv': x.to_csv(lineterminator='\n').encode() for t, x in frames.items()}
    report = assess(frames, cfg['common_start'], cfg['cutoff'],
                    adjustment_tolerance=cfg['adjustment_factor_tolerance'])
    files['quality.json'] = canonical_bytes(report)
    files['payable.json'] = canonical_bytes(payable)
    return files, report


def acquire_snapshot(root, config, parent=None):
    root = Path(root).resolve()
    with Run(root, 'N1 acquisition', config, parent) as run:
        import yfinance as yf
        cache = root / 'data/yfinance-cache'
        cache.mkdir(parents=True, exist_ok=True)
        yf.set_tz_cache_location(str(cache))
        files = {}
        target = root / 'data/snapshots' / run.run_id
        run.base['output_paths'] = [target.relative_to(root).as_posix()]
        try:
            download(config['universe'], config['start'], config['end_exclusive'], files)
        finally:
            freeze(target, files, {'config': config, 'environment': run.env, 'retrieved_at': now(),
                                   'run_id': run.run_id, 'git_sha': run.base['git_sha']})
            run.base['data_sha256'] = sha256((target / 'manifest.json').read_bytes())
            run.base['null_reasons']['data_sha256'] = None
        run.finish('completed', run.base['output_paths'], run.base['data_sha256'], [])
    return target


def audit_snapshot(root, source, parent=None, payable=None):
    root, source = Path(root).resolve(), Path(source).resolve()
    # Start before verifying, so corruption/missing manifests are also logged.
    cfg = {'source_snapshot': source.relative_to(root).as_posix(), 'payable': payable or {}}
    with Run(root, 'N1 offline QA', cfg, parent) as run:
        manifest = verify(source)
        run.base.update(universe=manifest['metadata']['config']['universe'],
                        splits=manifest['metadata']['config'].get('splits', {}))
        source_hash = sha256((source / 'manifest.json').read_bytes())
        files, report = build(source, manifest, payable or {})
        target = root / 'data/derived' / run.run_id
        freeze(target, files, {'source_snapshot': source.relative_to(root).as_posix(),
                              'source_manifest_sha256': source_hash, 'environment': run.env,
                              'config': manifest['metadata']['config'], 'run_id':run.run_id})
        run.finish('completed' if report['technical_pass'] else 'quality_failed',
                   [target.relative_to(root).as_posix()], sha256((target/'manifest.json').read_bytes()), report['warnings'])
    return target


def replay_snapshot(root, derived, parent=None):
    root, derived = Path(root).resolve(), Path(derived).resolve()
    with Run(root, 'N1 offline replay', {'derived_snapshot':derived.relative_to(root).as_posix()}, parent) as run:
        m = verify(derived)
        source = (root / m['metadata']['source_snapshot']).resolve()
        if not source.is_relative_to(root):
            raise ValueError('source snapshot outside project')
        sm = verify(source)
        if sha256((source/'manifest.json').read_bytes()) != m['metadata']['source_manifest_sha256']:
            raise ValueError('source manifest changed')
        payable = json.loads((derived/'payable.json').read_bytes())
        files, report = build(source, sm, payable)
        if {k:sha256(v) for k,v in files.items()} != m['files']:
            raise ValueError('replay differs from frozen derived files')
        run.base.update(universe=sm['metadata']['config']['universe'], splits=sm['metadata']['config'].get('splits',{}))
        run.finish('completed', [derived.relative_to(root).as_posix()], sha256((derived/'manifest.json').read_bytes()),
                   ['Exact replay does not certify data quality.'])
    return True
