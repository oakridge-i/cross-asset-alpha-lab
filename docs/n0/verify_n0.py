"""Audit N0 artifacts and illustrative arithmetic; not engine/strategy tests."""

import argparse
import datetime as dt
import hashlib
import json
import math
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PREPARATION = ROOT.parent / 'quant-research-plan'
OUTPUT = ROOT / 'docs/n0/verification.json'


def git(*arguments, directory=ROOT):
    return subprocess.check_output(['git', '-c', f'safe.directory={directory.as_posix()}',
                                    '-C', str(directory), '--no-optional-locks', *arguments],
                                   text=True, encoding='utf-8').strip()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--no-write', action='store_true', help='Verify without updating the receipt')
    args = parser.parse_args()
    checks = []

    def check(name, passed, detail):
        checks.append({'name': name, 'passed': bool(passed), 'detail': detail})

    required = ['AGENTS.md', 'README.md', 'STATUS.md', 'DECISIONS.md',
                'RESEARCH_PROTOCOL.md', 'docs/MASTER_PLAN.md',
                'experiments/EXPERIMENT_LOG.jsonl', 'experiments/README.md',
                'docs/n0/N0_REPORT.md', 'docs/n0/AAPL_REUSE_AUDIT.md',
                'docs/n0/protocol_manifest.json', 'docs/n0/source_probe.json',
                'docs/n0/source_probe_extended.json', 'docs/n0/probe_sources.py',
                'docs/n0/verify_n0.py']
    check('required_artifacts', all((ROOT / p).is_file() for p in required), required)
    for source, target in [('AGENTS.template.md', 'AGENTS.md'),
                           ('MASTER_PLAN.md', 'docs/MASTER_PLAN.md'),
                           ('NEW_CHAT_BRIEF.md', 'docs/n0/NEW_CHAT_BRIEF.md'),
                           ('NEW_PROJECT_SETUP.md', 'docs/n0/NEW_PROJECT_SETUP.md')]:
        check(f'exact_copy:{source}', sha(PREPARATION / source) == sha(ROOT / target), sha(ROOT / target))
    check('empty_experiment_log', (ROOT / 'experiments/EXPERIMENT_LOG.jsonl').stat().st_size == 0,
          'N0 availability probes separate; no strategy/data pipeline experiments started')
    manifest = json.loads((ROOT / 'docs/n0/protocol_manifest.json').read_text(encoding='utf-8'))
    configs = manifest['configurations']
    h1 = [c for c in configs if c['hypothesis'] == 'H1']
    h2 = [c for c in configs if c['hypothesis'] == 'H2']
    check('six_fixed_configurations', len(configs) == 6 and len(h1) == 4 and len(h2) == 2,
          [c['id'] for c in configs])
    check('h1_exact_grid', {(c['lookback'], c['top_k'], c['skip']) for c in h1}
          == {(126, 3, 21), (126, 4, 21), (252, 3, 21), (252, 4, 21)}, '2 lengths x 2 top-k')
    check('h2_fixed_parent', all(c['parent'] == 'H1_252_3' for c in h2)
          and {c['positive_months'] for c in h2} == {4, 5}, 'No replacement of parent by selected H1')
    check('four_baselines', manifest['baselines'] == ['B0', 'B1', 'B2', 'B3'], manifest['baselines'])
    check('policy_is_separate', manifest['adaptive_policy']['id'] == 'P_A1'
          and not manifest['adaptive_policy']['confirmatory_pipeline_p_value'], 'Four H1 only; conditional inference disclosed')
    check('not_tested_or_independent', not manifest['strategy_results_computed']
          and not manifest['reserved_test_opened'] and not manifest['independent_historical_holdout_claimed'],
          manifest['historical_exposure'])
    probe = json.loads((ROOT / 'docs/n0/source_probe_extended.json').read_text(encoding='utf-8'))
    results = probe['results']
    check('ten_available_sources', len(results) == 10 and all(r['status'] == 'available' for r in results),
          [{'ticker': r['ticker'], 'last': r.get('last_valid_session')} for r in results])
    shape_fields = ['invalid_ohlc_rows', 'inconsistent_ohlc_rows', 'missing_volume_rows',
                    'negative_volume_rows', 'duplicate_timestamps']
    check('returned_rows_shape', all(all(r[k] == 0 for k in shape_fields)
          and r['timestamps_strictly_increasing'] for r in results),
          {'returned_rows': sum(r['returned_rows'] for r in results), 'calendar_validated': False})
    check('common_start_and_warmup', probe['first_common_valid_observed_session'] == '2007-05-30'
          and probe['observed_returns_available_at_2008_12_31'] >= 252,
          {'common_sessions': probe['common_valid_observed_sessions'],
           'warmup_returns': probe['observed_returns_available_at_2008_12_31']})
    check('no_pay_dates_disclosed', all(not r['pay_dates_in_dividend_events'] for r in results),
          'Missing pay dates are disclosed; not a data-certification pass')
    # Hand-specified examples check the chosen formulas, not an implemented engine.
    score = ((120 / 100) / 1.02 - 1) / 0.20
    check('h1_hand_example', math.isclose(score, 15 / 17, abs_tol=1e-12),
          {'T_end': 120, 'T_start': 100, 'cash_growth': 1.02, 'sigma': 0.2, 'score': score})
    months = [0.02, -0.01, 0.01, 0.0, 0.03, 0.01]
    positive = sum(x > 0 for x in months)
    check('h2_hand_example', positive == 4 and positive >= 4 and not positive >= 5,
          {'month_excess': months, 'positive_count': positive})
    check('split_dividend_hand_example', math.isclose(3 * (109.5 + 0.5) / 330, 1),
          '3:1 split, previous close330, ex-close109.5, post-share dividend0.5: TR wealth unchanged')
    weights = [min(1 / 3, 0.25)] * 3
    check('top3_cap_hand_example', sum(weights) == 0.75, {'risky_weights': weights, 'BIL_weight': 0.25})
    requested, cash, opening, cost = 10, 100, 11, 0.001
    fill = min(1, cash / (requested * opening * (1 + cost)))
    quantity = math.floor(fill * requested)
    remaining = cash - quantity * opening * (1 + cost)
    check('gap_partial_fill_hand_example', quantity == 9 and remaining >= 0,
          {'precreated_quantity': requested, 'open': opening, 'filled': quantity, 'cash_remaining': remaining})
    authored = ['README.md', 'STATUS.md', 'DECISIONS.md', 'RESEARCH_PROTOCOL.md',
                'experiments/README.md', 'docs/n0/N0_REPORT.md', 'docs/n0/AAPL_REUSE_AUDIT.md']
    broken = []
    local_links = 0
    for relative in authored:
        path = ROOT / relative
        content = path.read_text(encoding='utf-8')
        for target in re.findall(r'(?<!!)\[[^\]]+\]\(([^)]+)\)', content):
            if re.match(r'https?://|codex://', target):
                continue
            local_links += 1
            resolved = (path.parent / target.split('#')[0].strip('<>')).resolve()
            if resolved != OUTPUT and not resolved.exists():
                broken.append({'file': relative, 'target': target})
        check(f'no_placeholders:{relative}', not re.search(r'\b(?:TODO|TBD|FIXME)\b', content), 'Reviewed text')
    check('local_links', not broken, {'checked': local_links, 'broken': broken,
                                    'self_receipt_output': 'docs/n0/verification.json'})
    check('git_root_is_separate', Path(git('rev-parse', '--show-toplevel')).resolve() == ROOT, ROOT.name)
    check('no_remote', not git('remote'), 'Local repository only')
    ignored = git('check-ignore', 'data/probe.csv', 'outputs/results.csv', '.venv/pyvenv.cfg', '.env')
    check('sensitive_generated_paths_ignored', len(ignored.splitlines()) == 4, ignored.splitlines())
    check('diff_whitespace', not git('diff', '--check') and not git('diff', '--cached', '--check'), 'Working/staged diffs')
    old = Path(r'C:\Quantitive\model 1 aapl')
    release = ROOT.parent / 'aapl-finalization'
    check('aapl_source_unchanged', not git('status', '--porcelain', directory=old)
          and git('rev-parse', 'HEAD', directory=old) == 'ed4fd39518f1f58ad4065512bec8223443186bf3',
          'Old main clean and unchanged')
    check('aapl_release_unchanged', not git('status', '--porcelain', directory=release)
          and git('rev-parse', 'HEAD', directory=release) == '4d69932382af4a7bcaddfb4621f0973ea2d820c2',
          'Release worktree clean and unchanged')
    head = subprocess.run(['git', '-C', str(ROOT), 'rev-parse', '--verify', 'HEAD'],
                          capture_output=True, text=True)
    receipt = {
        'verified_at_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
        'stage': 'N0', 'status': 'passed' if all(c['passed'] for c in checks) else 'failed',
        'git_head_at_verification': head.stdout.strip() if head.returncode == 0 else None,
        'pass_count': sum(c['passed'] for c in checks), 'check_count': len(checks),
        'protocol_sha256': sha(ROOT / 'RESEARCH_PROTOCOL.md'),
        'protocol_manifest_sha256': sha(ROOT / 'docs/n0/protocol_manifest.json'),
        'file_hashes': {p: sha(ROOT / p) for p in required if p != 'STATUS.md'},
        'checks': checks,
        'limits': ['No engine or strategy tests run; illustrative arithmetic only',
                   'No calendar/independent market-data certification',
                   'No alpha or independent historical holdout claim'],
    }
    if not args.no_write:
        OUTPUT.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: receipt[k] for k in ['status', 'pass_count', 'check_count',
          'git_head_at_verification', 'protocol_sha256']}, ensure_ascii=False))
    for c in checks:
        if not c['passed']:
            print(json.dumps(c, ensure_ascii=False))
    return 0 if receipt['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
