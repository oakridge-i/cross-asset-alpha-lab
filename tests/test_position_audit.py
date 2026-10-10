"""Independent position-balance audit of frozen runs: clean runs of every kind pass, injected defects are named,
journal statuses and the position-audit CLI."""
import csv
import io
import json
import shutil
import socket
import pytest
from n2_fixtures import write_vintage
from n3_fixtures import RISKY, benchmark_frames
from alpha_lab.__main__ import main
from alpha_lab.engine import RunConfig, run_simulation
from alpha_lab.market import load_market
from alpha_lab.position_audit import audit_run, build_position_audit
from alpha_lab.provenance import canonical_bytes, sha256, verify
from test_engine_run import RICH, journal, rich_frames, vintage

SEVEN = ('cash_non_negative', 'nav_identity', 'cash_flow', 'split_quantity_only', 'receivable_conservation',
         'execution_timing', 'costs')
START, END = '2008-12-31', '2009-03-31'
POLICY_START, POLICY_END = '2013-12-31', '2014-02-28'
SPY_SPLIT, EEM_SPLIT, POLICY_SPLIT = '2009-02-02', '2009-03-10', '2014-01-15'
RISKY_SPLIT = '2009-02-17'
COST = 0.001
KINDS = ('price', 'notional', 'cost', 'order_link', 'filled_qty', 'side', 'order_without_trade',
         'trade_without_fill', 'unknown')


def split_frames():
    """N3 frames to 2014 with a 3:1 SPY split, a 2:1 split of every risky ETF and a 1:2 EEM split in the 2009 window
    and a 3:1 split of every risky ETF in the policy window; prices from each split session on are in post-split
    units."""
    frames = benchmark_frames(start='2007-12-03', end='2014-03-31')

    def split(ticker, session, ratio):
        f = frames[ticker]
        later = f.index >= session
        f.loc[later, ['open', 'close']] = f.loc[later, ['open', 'close']] / ratio
        f.loc[session, 'split_ratio'] = ratio

    split('SPY', SPY_SPLIT, 3.0)
    for t in RISKY:
        split(t, RISKY_SPLIT, 2.0)
    split('EEM', EEM_SPLIT, 0.5)
    for t in RISKY:
        split(t, POLICY_SPLIT, 3.0)
    return frames


def refuse(*args, **kwargs):
    raise AssertionError('test tried network access')


@pytest.fixture(scope='module')
def campaign(tmp_path_factory):
    """One synthetic project with a benchmark, the first-only reference, a hypothesis and the policy run."""
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(socket.socket, 'connect', refuse)
        mp.setattr(socket, 'create_connection', refuse)
        root = tmp_path_factory.mktemp('campaign').resolve()
        derived = write_vintage(root, split_frames())
        digest = sha256((derived / 'manifest.json').read_bytes())
        runs = {name: run_simulation(root, derived, name, RunConfig(START, END), expected_sha256=digest)
                for name in ('B1', 'REF_SPY', 'H1_252_3')}
        runs['P_A1'] = run_simulation(root, derived, 'P_A1', RunConfig(POLICY_START, POLICY_END),
                                      expected_sha256=digest, stage=5)
        market = load_market(root, derived.relative_to(root), digest)
        yield {'root': root, 'digest': digest, 'market': market, 'runs': runs}


@pytest.fixture
def rotation(tmp_path, no_network):
    """Clean test-provider run on the N2 vintage with a 2:1 BBB split on 2017-12-05 (also an execution session)."""
    root = tmp_path.resolve()
    derived, digest = vintage(root, rich_frames())
    run_dir = run_simulation(root, derived, 'invariant_rotation', RICH, expected_sha256=digest)
    return {'root': root, 'digest': digest, 'market': load_market(root, derived.relative_to(root), digest),
            'run': run_dir}


def rows(run_dir, name):
    with open(run_dir / name, encoding='utf-8', newline='') as stream:
        reader = csv.DictReader(stream)
        return reader.fieldnames, list(reader)


def refreeze(run_dir, name, header, records):
    """Rewrite one frozen file and its manifest so provenance.verify still passes (a defect inside the engine)."""
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=header, lineterminator='\n')
    writer.writeheader()
    writer.writerows(records)
    body = out.getvalue().encode()
    (run_dir / name).write_bytes(body)
    edit_manifest(run_dir, lambda manifest: manifest['files'].__setitem__(name, sha256(body)))


def edit_manifest(run_dir, edit):
    """Apply `edit` to the manifest of a run directory and refreeze it so provenance.verify still passes."""
    manifest = json.loads((run_dir / 'manifest.json').read_bytes())
    edit(manifest)
    encoded = canonical_bytes(manifest)
    (run_dir / 'manifest.json').write_bytes(encoded)
    (run_dir / 'manifest.sha256').write_text(sha256(encoded) + '\n', encoding='ascii')
    verify(run_dir)


def shift_qty(run_dir, ticker, change, market=None):
    """change(session, recorded quantity) -> new recorded quantity, applied to qty_<ticker> of daily.csv. With
    `market`, positions_value and nav of every changed row move by the change in shares times that session's close,
    so the defective record stays self-consistent."""
    header, records = rows(run_dir, 'daily.csv')
    for r in records:
        old = float(r[f'qty_{ticker}'])
        new = change(r['session'], old)
        r[f'qty_{ticker}'] = repr(new)
        if market is not None and new != old:
            value = (new - old) * float(market.close.loc[r['session'], ticker])
            for column in ('positions_value', 'nav'):
                r[column] = repr(float(r[column]) + value)
    refreeze(run_dir, 'daily.csv', header, records)


def copy_run(run_dir, label):
    target = run_dir.parent / f'{run_dir.name}-{label}'
    shutil.copytree(run_dir, target)
    return target


def invariants(run_dir):
    return json.loads((run_dir / 'invariants.json').read_bytes())


def window(market, run_dir):
    config = json.loads((run_dir / 'config.json').read_bytes())
    return [s for s in market.sessions if config['start_session'] <= s <= config['end_session']]


def assert_clean(audit, market, run_dir):
    sessions = window(market, run_dir)
    assert audit['passed'] is True and audit['first_failure'] is None
    assert audit['position_failures'] == audit['cumulative_failures'] == audit['trade_failures'] == 0
    assert audit['sessions'] == len(sessions)
    assert audit['positions_checked'] == len(sessions) * len(market.tickers)
    assert audit['trades'] == len(rows(run_dir, 'trades.csv')[1])
    assert audit['orders_checked'] == len(rows(run_dir, 'orders.csv')[1])
    assert audit['max_position_difference'] <= 1e-6
    assert set(audit['trade_failure_kinds']) == set(KINDS) and not any(audit['trade_failure_kinds'].values())


# Clean runs of every kind, each with real splits in its window


@pytest.mark.parametrize('name', ['B1', 'REF_SPY', 'H1_252_3', 'P_A1'])
def test_clean_runs_of_every_kind_pass(campaign, name, no_network):
    run_dir = campaign['runs'][name]
    assert invariants(run_dir)['passed'] is True and invariants(run_dir)['split_events']
    assert_clean(audit_run(run_dir, campaign['market']), campaign['market'], run_dir)


def test_clean_test_provider_run_with_a_split_on_an_execution_session_passes(rotation):
    run_dir = rotation['run']
    assert ['BBB', '2017-12-05'] in invariants(run_dir)['split_events']
    assert '2017-12-05' in {r['session'] for r in rows(run_dir, 'trades.csv')[1] if r['ticker'] == 'BBB'}
    assert_clean(audit_run(run_dir, rotation['market']), rotation['market'], run_dir)


def test_fractional_position_after_a_reverse_split_passes(campaign, no_network):
    run_dir = campaign['runs']['B1']
    assert ['EEM', EEM_SPLIT] in invariants(run_dir)['split_events']
    assert audit_run(run_dir, campaign['market'])['passed'] is True


# Defects that the seven run invariants do not see


def test_an_added_share_passes_the_invariants_and_fails_the_audit(rotation):
    run_dir, market = rotation['run'], rotation['market']
    before = rows(run_dir, 'daily.csv')[1]
    shift_qty(run_dir, 'AAA', lambda s, q: q + 1.0 if s >= '2017-12-01' else q, market)
    after = rows(run_dir, 'daily.csv')[1]
    # The defective record is self-consistent: nav moves with the extra share's value at that session's close.
    assert all(float(a['nav']) - float(b['nav']) == pytest.approx(market.close.loc[a['session'], 'AAA'])
               for a, b in zip(after, before) if a['session'] >= '2017-12-01')
    assert all(float(a['nav']) - float(a['positions_value']) == pytest.approx(
        float(b['nav']) - float(b['positions_value'])) for a, b in zip(after, before))
    assert all(invariants(run_dir)[name]['passed'] for name in SEVEN) and invariants(run_dir)['passed']
    audit = audit_run(run_dir, market)
    later = [s for s in window(market, run_dir) if s >= '2017-12-01']
    assert audit['passed'] is False
    assert audit['first_failure'] == {'session': '2017-12-01', 'ticker': 'AAA', 'check': 'position'}
    assert audit['position_failures'] == 1 and audit['cumulative_failures'] == len(later)
    assert audit['max_position_difference'] == pytest.approx(1.0)
    assert audit['trade_failures'] == 0


def test_a_lost_share_fails_the_audit(rotation):
    run_dir, market = rotation['run'], rotation['market']
    shift_qty(run_dir, 'BBB', lambda s, q: q - 1.0 if s >= '2017-12-06' else q)
    audit = audit_run(run_dir, market)
    assert audit['first_failure'] == {'session': '2017-12-06', 'ticker': 'BBB', 'check': 'position'}
    assert audit['position_failures'] == 1 and audit['passed'] is False


def test_a_wrong_split_ratio_fails_on_the_split_session(rotation):
    run_dir, market = rotation['run'], rotation['market']
    before = {r['session']: float(r['qty_BBB']) for r in rows(run_dir, 'daily.csv')[1]}['2017-12-04']
    assert before > 0
    # Ratio 3 instead of 2: the position gains one more pre-split position on the split session.
    shift_qty(run_dir, 'BBB', lambda s, q: q + before if s >= '2017-12-05' else q)
    assert invariants(run_dir)['passed']
    audit = audit_run(run_dir, market)
    assert audit['first_failure'] == {'session': '2017-12-05', 'ticker': 'BBB', 'check': 'position'}
    assert audit['position_failures'] == 1
    assert audit['max_position_difference'] == pytest.approx(before)


def test_slow_drift_is_found_only_by_the_cumulative_variant(campaign, no_network):
    run_dir = copy_run(campaign['runs']['REF_SPY'], 'drift')
    held = {r['session']: float(r['qty_SPY']) for r in rows(run_dir, 'daily.csv')[1]}
    after = sorted(s for s in held if s > RISKY_SPLIT)
    position = held[after[0]]
    assert position > 0 and all(held[s] == position for s in after)  # first-only: no trade after the splits
    # Per session the step is 0.8e-9 of the position, inside the per-session tolerance (1e-9 + 1e-9 of the
    # magnitude, at least 2e-9 of the position); the cumulative deviation grows by one step per session and exceeds
    # the cumulative tolerance (1e-9 + 1e-9 of twice the position, as no trade follows the purchase) from the third
    # session on (3 * 0.8e-9 > 2e-9).
    step = 0.8e-9 * position
    rank = {s: i + 1 for i, s in enumerate(after)}
    shift_qty(run_dir, 'SPY', lambda s, q: q + rank[s] * step if s in rank else q)
    audit = audit_run(run_dir, campaign['market'])
    assert audit['position_failures'] == 0 and audit['trade_failures'] == 0
    assert audit['cumulative_failures'] > 0 and audit['passed'] is False
    assert audit['first_failure']['ticker'] == 'SPY' and audit['first_failure']['check'] == 'cumulative'
    assert audit['first_failure']['session'] in rank


def test_trade_qty_different_from_the_order_filled_qty(rotation):
    run_dir, market = rotation['run'], rotation['market']
    header, records = rows(run_dir, 'orders.csv')
    filled = [r for r in records if float(r['filled_qty']) > 0]
    filled[0]['filled_qty'] = repr(float(filled[0]['filled_qty']) + 1.0)
    refreeze(run_dir, 'orders.csv', header, records)
    audit = audit_run(run_dir, market)
    assert audit['trade_failures'] == 1 and audit['trade_failure_kinds']['filled_qty'] == 1
    assert audit['position_failures'] == audit['cumulative_failures'] == 0
    assert audit['first_failure'] == {'session': filled[0]['execution_session'], 'ticker': filled[0]['ticker'],
                                      'check': 'filled_qty'}


def test_trade_at_a_price_other_than_the_open(rotation):
    run_dir, market = rotation['run'], rotation['market']
    header, records = rows(run_dir, 'trades.csv')
    t = records[0]
    price = float(t['price']) * 1.01
    t['price'], t['notional'] = repr(price), repr(float(t['qty']) * price)
    t['cost'] = repr(COST * float(t['qty']) * price)
    refreeze(run_dir, 'trades.csv', header, records)
    audit = audit_run(run_dir, market)
    assert audit['trade_failures'] == 1 and audit['trade_failure_kinds']['price'] == 1
    assert audit['first_failure'] == {'session': t['session'], 'ticker': t['ticker'], 'check': 'price'}


def test_cost_that_is_not_cost_times_notional(rotation):
    run_dir, market = rotation['run'], rotation['market']
    header, records = rows(run_dir, 'trades.csv')
    records[-1]['cost'] = repr(2 * float(records[-1]['cost']))
    refreeze(run_dir, 'trades.csv', header, records)
    audit = audit_run(run_dir, market)
    assert audit['trade_failures'] == 1 and audit['trade_failure_kinds']['cost'] == 1 and not audit['passed']


def test_filled_order_without_a_trade(rotation):
    run_dir, market = rotation['run'], rotation['market']
    header, records = rows(run_dir, 'orders.csv')
    assert '2017-12-04' not in {r['session'] for r in rows(run_dir, 'trades.csv')[1]}
    records.append({'decision_session': '2017-12-01', 'execution_session': '2017-12-04', 'ticker': 'AAA',
                    'weight': '0.5', 'close': '100', 'target_qty': '1', 'held_qty': '0', 'order_qty': '1',
                    'filled_qty': '1', 'status': 'filled', 'cancel_reason': ''})
    refreeze(run_dir, 'orders.csv', header, records)
    audit = audit_run(run_dir, market)
    assert audit['trade_failures'] == 1 and audit['trade_failure_kinds']['order_without_trade'] == 1
    assert audit['orders_checked'] == len(records)
    assert audit['first_failure'] == {'session': '2017-12-04', 'ticker': 'AAA', 'check': 'order_without_trade'}


def test_trade_without_its_order(rotation):
    run_dir, market = rotation['run'], rotation['market']
    trade = rows(run_dir, 'trades.csv')[1][0]
    header, records = rows(run_dir, 'orders.csv')
    kept = [r for r in records if (r['execution_session'], r['ticker']) != (trade['session'], trade['ticker'])]
    assert len(kept) == len(records) - 1
    refreeze(run_dir, 'orders.csv', header, kept)
    audit = audit_run(run_dir, market)
    assert audit['trade_failure_kinds']['order_link'] == 1 and audit['trade_failures'] == 1


def test_daily_sessions_must_equal_the_vintage_window(rotation):
    run_dir, market = rotation['run'], rotation['market']
    header, records = rows(run_dir, 'daily.csv')
    refreeze(run_dir, 'daily.csv', header, records[:-1])
    audit = audit_run(run_dir, market)
    assert audit['passed'] is False and audit['structure_failures'] == 1
    assert audit['first_failure'] == {'session': None, 'ticker': None, 'check': 'sessions'}


# Journaled audit and CLI


def document(target):
    return json.loads((target / 'position_audit.json').read_bytes())


def test_journal_completed_for_clean_runs(rotation):
    root, run_dir = rotation['root'], rotation['run']
    target = build_position_audit(root, [run_dir.relative_to(root)], expected_sha256=rotation['digest'])
    started, completed = journal(root)[-2:]
    assert (started['event'], completed['event'], completed['status']) == ('started', 'completed', 'completed')
    assert started['purpose'] == 'Position audit' and started['candidate_ids'] == []
    assert completed['quality_warnings'] == [] and completed['output_paths'] == [f'data/reports/{target.name}']
    assert target == root / 'data/reports' / completed['run_id']
    assert completed['data_sha256'] == sha256((target / 'manifest.json').read_bytes())
    assert set(verify(target)['files']) == {'position_audit.json'}
    doc = document(target)
    assert doc['totals'] == {'runs': 1, 'runs_passed': 1}
    assert doc['runs'][run_dir.name] == audit_run(run_dir, rotation['market'])


def test_journal_audit_failed_names_the_failing_run(rotation):
    root, run_dir = rotation['root'], rotation['run']
    bad = copy_run(run_dir, 'defect')
    shift_qty(bad, 'AAA', lambda s, q: q + 1.0 if s >= '2017-12-01' else q)
    target = build_position_audit(root, [run_dir, bad], expected_sha256=rotation['digest'])
    last = journal(root)[-1]
    assert last['event'] == last['status'] == 'audit_failed' and last['quality_warnings'] == [bad.name]
    assert last['output_paths'] == [f'data/reports/{target.name}']
    doc = document(target)
    assert doc['totals'] == {'runs': 2, 'runs_passed': 1}
    assert doc['runs'][bad.name]['passed'] is False and doc['runs'][run_dir.name]['passed'] is True


def test_audit_document_is_deterministic(rotation):
    root, run_dir = rotation['root'], rotation['run']
    first = build_position_audit(root, [run_dir], expected_sha256=rotation['digest'])
    second = build_position_audit(root, [run_dir], expected_sha256=rotation['digest'])
    assert first != second
    assert verify(first)['files'] == verify(second)['files']


def test_run_outside_data_runs_is_refused_and_journaled(rotation):
    root, run_dir = rotation['root'], rotation['run']
    outside = root / 'elsewhere' / run_dir.name
    shutil.copytree(run_dir, outside)
    with pytest.raises(ValueError, match='outside data/runs'):
        build_position_audit(root, [outside], expected_sha256=rotation['digest'])
    assert journal(root)[-1]['status'] == 'failed'


def test_tampered_run_directory_is_refused(rotation):
    root, run_dir = rotation['root'], rotation['run']
    bad = copy_run(run_dir, 'tampered')
    (bad / 'daily.csv').write_bytes((bad / 'daily.csv').read_bytes() + b'\n')
    with pytest.raises(ValueError, match='content hash mismatch'):
        build_position_audit(root, [bad], expected_sha256=rotation['digest'])
    assert journal(root)[-1]['status'] == 'failed'


def test_unapproved_vintage_is_refused(rotation):
    root, run_dir = rotation['root'], rotation['run']
    with pytest.raises(ValueError, match='unexpected vintage'):
        build_position_audit(root, [run_dir], expected_sha256='0' * 64)
    assert journal(root)[-1]['status'] == 'failed'


def test_runs_on_different_vintages_are_refused(rotation):
    root, run_dir = rotation['root'], rotation['run']
    other = copy_run(run_dir, 'other-vintage')
    edit_manifest(other, lambda m: m['metadata'].__setitem__('derived_snapshot', 'data/derived/another-vintage'))
    assert run_dir.parent == other.parent
    with pytest.raises(ValueError, match='runs on different vintages'):
        build_position_audit(root, [run_dir, other], expected_sha256=rotation['digest'])
    assert journal(root)[-1]['status'] == 'failed'


def cli(fixture, *runs):
    root = fixture['root']
    return ['position-audit', '--runs', *(r.relative_to(root).as_posix() for r in runs), '--root', str(root),
            '--expected-sha256', fixture['digest']]


def test_cli_exit_code_0_when_all_runs_pass(rotation, capsys):
    main(cli(rotation, rotation['run']))
    printed = capsys.readouterr().out.strip()
    assert printed.startswith('data/reports/') and (rotation['root'] / printed / 'position_audit.json').is_file()
    assert journal(rotation['root'])[-1]['status'] == 'completed'


def test_cli_exit_code_3_when_a_run_fails(rotation, capsys):
    bad = copy_run(rotation['run'], 'defect')
    shift_qty(bad, 'BBB', lambda s, q: q - 1.0 if s >= '2017-12-06' else q)
    with pytest.raises(SystemExit) as exc:
        main(cli(rotation, rotation['run'], bad))
    assert exc.value.code == 3
    assert (rotation['root'] / capsys.readouterr().out.strip() / 'position_audit.json').is_file()
    assert journal(rotation['root'])[-1]['status'] == 'audit_failed'
