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
