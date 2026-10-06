import json
import pandas as pd
import pytest
from alpha_lab import quality as q


def chart():
    return {'chart': {'error': None, 'result': [{'meta': {'symbol':'TEST','currency':'USD','exchangeTimezoneName':'America/New_York'},
       'timestamp': [1511879400,1511965800],
       'indicators': {'quote': [{'open':[10,9],'high':[10,9],'low':[10,9],'close':[10,9],'volume':[100,100]}],
                      'adjclose':[{'adjclose':[9,9]}]},
       'events': {'dividends': {'a': {'date':1511965800,'amount':1}}}}]}}


def test_chart_preserves_event_on_exact_session():
    x = q.parse_chart(json.dumps(chart()).encode(), 'TEST')
    assert x['Dividends'].tolist() == [0, 1]
    assert x.index.strftime('%Y-%m-%d').tolist() == ['2017-11-28','2017-11-29']


@pytest.mark.parametrize('change', ['orphan', 'currency', 'ticker', 'shape', 'duplicate_event'])
def test_source_errors_fail_closed(change):
    data = chart(); r = data['chart']['result'][0]
    if change == 'orphan': r['events']['dividends']['a']['date'] += 86400
    if change == 'currency': r['meta']['currency'] = 'EUR'
    if change == 'ticker': r['meta']['symbol'] = 'OTHER'
    if change == 'shape': r['indicators']['quote'][0]['open'] = [10]
    if change == 'duplicate_event': r['events']['dividends']['b'] = dict(r['events']['dividends']['a'])
    with pytest.raises(ValueError): q.parse_chart(json.dumps(data).encode(), 'TEST')


def test_missing_dividend_causes_adjustment_break():
    from alpha_lab.normalize import normalize
    f=q.parse_chart(json.dumps(chart()).encode(),'TEST')
    good=normalize(f,'TEST','now','hash')
    assert q.assess({'TEST':good},'2017-11-28','2017-11-29')['technical_pass'] is True
    f['Dividends']=0
    bad=normalize(f,'TEST','now','hash')
    report=q.assess({'TEST':bad},'2017-11-28','2017-11-29')
    assert report['technical_pass'] is False
    assert report['assets']['TEST']['adjustment_breaks'] == 1


def test_common_coverage_detects_missing_boundary():
    from alpha_lab.normalize import normalize
    f=q.parse_chart(json.dumps(chart()).encode(),'TEST')
    x=normalize(f,'TEST','now','hash')
    report=q.assess({'TEST':x},'2017-11-27','2017-11-29')
    assert report['technical_pass'] is False
    assert report['assets']['TEST']['missing_sessions'] == ['2017-11-27']
