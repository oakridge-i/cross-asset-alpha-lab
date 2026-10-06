import json
from pathlib import Path
import pytest
from alpha_lab.provenance import freeze, verify
from alpha_lab import pipeline as p
from test_quality import chart


def source(root):
    config = {'universe':['TEST'], 'start':'2017-11-28', 'common_start':'2017-11-28',
              'cutoff':'2017-11-29','end_exclusive':'2017-11-30','pay_delay_days':10,
              'adjustment_factor_tolerance':0.00005}
    import pandas as pd
    f=pd.DataFrame({'Open':[10,9],'High':[10,9],'Low':[10,9],'Close':[10,9],
                    'Adj Close':[9,9],'Volume':[100,100],'Dividends':[0,1],'Stock Splits':[0,0]},
                   index=['2017-11-28','2017-11-29'])
    return freeze(root/'data/snapshots/test',{'raw/TEST-0.json':json.dumps(chart()).encode(),
                                          'adapter/TEST.csv':f.to_csv(index_label='Date').encode()},
                  {'config':config,'retrieved_at':'2026-10-06T00:00:00+00:00'})


def test_offline_audit_and_exact_replay(tmp_path,no_network):
    s=source(tmp_path)
    derived=p.audit_snapshot(tmp_path,s)
    report=json.loads((derived/'quality.json').read_bytes())
    assert report['technical_pass'] is True
    assert report['data_ready_for_n2'] is False
    assert p.replay_snapshot(tmp_path,derived) is True
    rows=[json.loads(x) for x in (tmp_path/'experiments/EXPERIMENT_LOG.jsonl').read_text().splitlines()]
    assert [r['event'] for r in rows] == ['started','completed','started','completed']


def test_corrupt_snapshot_creates_failed_audit(tmp_path):
    s=source(tmp_path)
    (s/'raw/TEST-0.json').write_bytes(b'corrupt')
    with pytest.raises(ValueError): p.audit_snapshot(tmp_path,s)
    rows=[json.loads(x) for x in (tmp_path/'experiments/EXPERIMENT_LOG.jsonl').read_text().splitlines()]
    assert [r['event'] for r in rows] == ['started','failed']


def test_adapter_disagreement_is_not_silently_accepted(tmp_path):
    s=source(tmp_path)
    m=verify(s)
    files={name:(s/name).read_bytes() for name in m['files']}
    files['adapter/TEST.csv']=files['adapter/TEST.csv'].replace(b'10,10,10,10',b'11,11,11,11')
    other=freeze(tmp_path/'data/snapshots/changed',files,m['metadata'])
    with pytest.raises(ValueError,match='adapter'): p.audit_snapshot(tmp_path,other)


def journal(root):
    return [json.loads(x) for x in (root/'experiments/EXPERIMENT_LOG.jsonl').read_text().splitlines()]


def capital_gain_source(root, adapter_column):
    import pandas as pd
    data = chart()
    data['chart']['result'][0]['events'] = {'capitalGains': {'a': {'date': 1511965800, 'amount': 1}}}
    s = source(root)
    m = verify(s)
    f = pd.DataFrame({'Open':[10,9],'High':[10,9],'Low':[10,9],'Close':[10,9],'Adj Close':[9,9],
                      'Volume':[100,100],'Dividends':[0,0],'Stock Splits':[0,0]}, index=['2017-11-28','2017-11-29'])
    if adapter_column:
        f['Capital Gains'] = [0, 0]
    files = {'raw/TEST-0.json': json.dumps(data).encode(), 'adapter/TEST.csv': f.to_csv(index_label='Date').encode()}
    return freeze(root/'data/snapshots/cg', files, m['metadata'])


@pytest.mark.parametrize('adapter_column', [True, False], ids=['adapter_zero', 'adapter_missing'])
def test_capital_gains_are_cross_checked_against_adapter(tmp_path, adapter_column, no_network):
    with pytest.raises(ValueError, match='Capital Gains'):
        p.audit_snapshot(tmp_path, capital_gain_source(tmp_path, adapter_column))


def tamper(root, derived, change):
    import shutil
    m = verify(derived)
    files = {name: (derived/name).read_bytes() for name in m['files']}
    metadata = dict(m['metadata'])
    if change == 'normalized':
        files['normalized/TEST.csv'] = files['normalized/TEST.csv'].replace(b'TEST', b'TSET', 1)
    if change == 'payable':
        files['payable.json'] = b'{"TEST":{"2017-11-29":{"date":"2017-12-01","source":"issuer"}}}\n'
    if change == 'source':
        source = root/metadata['source_snapshot']
        sm = verify(source)
        body = {name: (source/name).read_bytes() for name in sm['files']}
        shutil.rmtree(source)
        freeze(source, body, sm['metadata'] | {'retrieved_at': '2026-10-07T00:00:00+00:00'})
    if change == 'escape':
        metadata['source_snapshot'] = '../../etc'
    return freeze(root/'data/derived/tampered', files, metadata)


@pytest.mark.parametrize('change,message', [
    ('normalized', 'replay differs'), ('payable', 'replay differs'),
    ('source', 'source manifest changed'), ('escape', 'outside project')])
def test_replay_refuses_tampered_inputs(tmp_path, change, message, no_network):
    derived = tamper(tmp_path, p.audit_snapshot(tmp_path, source(tmp_path)), change)
    with pytest.raises(ValueError, match=message):
        p.replay_snapshot(tmp_path, derived)
    assert [r['event'] for r in journal(tmp_path)] == ['started', 'completed', 'started', 'failed']


def test_failed_acquisition_keeps_partial_raw_evidence(tmp_path, no_network):
    def downloader(tickers, start, end, files):
        files['raw/TEST-0.json'] = b'{"partial": true}'
        raise ConnectionError('network dropped after first body')
    config = {'universe': ['TEST'], 'start': '2017-11-28', 'end_exclusive': '2017-11-30'}
    with pytest.raises(ConnectionError):
        p.acquire_snapshot(tmp_path, config, downloader=downloader)
    [target] = (tmp_path/'data/snapshots').iterdir()
    m = verify(target)
    assert list(m['files']) == ['raw/TEST-0.json']
    assert (target/'raw/TEST-0.json').read_bytes() == b'{"partial": true}'
    rows = journal(tmp_path)
    assert [r['event'] for r in rows] == ['started', 'failed']
    from alpha_lab.provenance import sha256
    assert rows[-1]['data_sha256'] == sha256((target/'manifest.json').read_bytes())


def test_manifest_hashes_of_inputs_are_journaled(tmp_path, no_network):
    from alpha_lab.provenance import sha256
    s = source(tmp_path)
    derived = p.audit_snapshot(tmp_path, s)
    p.replay_snapshot(tmp_path, derived)
    audit, replay = journal(tmp_path)[1], journal(tmp_path)[3]
    source_hash = sha256((s/'manifest.json').read_bytes())
    assert audit['source_manifest_sha256'] == replay['source_manifest_sha256'] == source_hash
    assert replay['derived_manifest_sha256'] == sha256((derived/'manifest.json').read_bytes())


def test_unreadable_cli_inputs_are_logged_as_failed_runs(tmp_path, no_network):
    from alpha_lab.__main__ import main
    source(tmp_path)
    with pytest.raises(FileNotFoundError):
        main(['audit', 'data/snapshots/test', '--root', str(tmp_path), '--payable', 'missing.json'])
    with pytest.raises(FileNotFoundError):
        main(['evidence', '--root', str(tmp_path)])
    rows = journal(tmp_path)
    assert [r['event'] for r in rows] == ['started', 'failed', 'started', 'failed']
    assert rows[0]['purpose'] == 'N1 offline QA'
    assert rows[0]['config']['unreadable_input'] == 'missing.json'
    assert rows[2]['config']['unreadable_input'] == 'configs/n1_evidence.json'
