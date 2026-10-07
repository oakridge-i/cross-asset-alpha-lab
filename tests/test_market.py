"""Market loader: common calendar, payable contract, vintage identity."""
from pathlib import Path
import pytest
from alpha_lab import market as m
from alpha_lab.provenance import sha256
from n2_fixtures import SESSIONS, frame, write_vintage

ROOT = Path(__file__).resolve().parents[1]
PRICES = [10., 11., 12., 13., 14., 15., 16., 17., 18., 19.]
DIV = [0., 0., 0., 0.5, 0., 0., 0., 0., 0., 0.]
EX = '2017-11-30'


def with_payable(payable):
    return m.market_from_frames({'AAA': frame(PRICES, dividend=DIV, payable=payable)})


def test_common_calendar_is_intersection():
    market = m.market_from_frames({'AAA': frame(PRICES), 'BBB': frame(PRICES).drop('2017-11-29')})
    assert '2017-11-29' not in market.sessions
    assert len(market.sessions) == 9
    assert market.tickers == ('AAA', 'BBB')
    assert list(market.close.index) == list(market.sessions)


def test_start_cuts_calendar():
    market = m.market_from_frames({'AAA': frame(PRICES)}, start='2017-11-30')
    assert market.sessions[0] == '2017-11-30' and len(market.sessions) == 7


@pytest.mark.parametrize('payable', [
    {EX: ('2017-12-04', 'proxy')},
    {},
    {EX: ('2017-12-05', '')},
    {EX: ('', m.ACTUAL_BASIS)},
    {EX: ('2017-11-28', m.ACTUAL_BASIS)},
    {EX: ('2017-12-8', m.ACTUAL_BASIS)},
    {EX: ('2017-12-08', m.PROXY_BASIS)},
])
def test_payable_contract_violations(payable):
    with pytest.raises(ValueError, match='AAA/2017-11-30'):
        with_payable(payable)


@pytest.mark.parametrize('payable, expected', [
    ({EX: ('2017-12-11', m.PROXY_BASIS)}, ('2017-12-11', m.PROXY_BASIS)),
    ({EX: ('2017-12-05', m.ACTUAL_BASIS)}, ('2017-12-05', m.ACTUAL_BASIS)),
    ({EX: (EX, m.ACTUAL_BASIS)}, (EX, m.ACTUAL_BASIS)),
])
def test_payable_contract_accepts(payable, expected):
    # 2017-12-11 is after the last bar: pay sessions are not restricted to the common calendar.
    market = with_payable(payable)
    assert market.payable == {('AAA', EX): expected}
    assert (expected[0] in market.sessions) == (expected[0] != '2017-12-11')


@pytest.mark.parametrize('column, bad', [
    ('close', float('nan')), ('close', 0.), ('open', 0.), ('dividend', float('nan')), ('dividend', -1.),
    ('split_ratio', 0.)])
def test_invalid_numbers_are_rejected(column, bad):
    f = frame(PRICES)
    f.loc['2017-12-01', column] = bad
    with pytest.raises(ValueError, match=f'invalid {column}: AAA/2017-12-01'):
        m.market_from_frames({'AAA': f})


def test_open_may_be_missing():
    f = frame(PRICES)
    f.loc['2017-12-01', 'open'] = float('nan')
    assert m.market_from_frames({'AAA': f}).open.isna().sum().sum() == 1


def test_proxy_pay_session():
    assert m.proxy_pay_session('2017-11-30', 10) == '2017-12-11'
    assert m.proxy_pay_session('2017-11-30', 0) == '2017-11-30'
    assert m.proxy_pay_session('2017-11-30', 30) == '2018-01-02'


def test_history_excludes_future():
    f = frame(PRICES, dividend=[0., 0., 0., 0.5, 0.25, 0., 0., 0., 0., 0.],
              payable={EX: ('2017-12-05', m.ACTUAL_BASIS), '2017-12-01': ('2017-12-06', m.ACTUAL_BASIS)})
    market = m.market_from_frames({'AAA': f}, vintage='v', manifest_sha256='h')
    past = market.history(EX)
    assert len(past.sessions) == 4 and past.sessions[-1] == EX
    assert all(len(t) == 4 for t in (past.open, past.close, past.dividend, past.split_ratio))
    assert set(market.payable) == {('AAA', EX), ('AAA', '2017-12-01')}
    assert set(past.payable) == {('AAA', EX)}
    assert (past.vintage, past.manifest_sha256) == ('v', 'h')
    assert len(market.sessions) == 10


def test_index():
    market = m.market_from_frames({'AAA': frame(PRICES)})
    assert market.index('2017-11-29') == 2
    with pytest.raises(ValueError, match='2017-11-25'):
        market.index('2017-11-25')
    with pytest.raises(ValueError, match='2017-11-25'):
        market.history('2017-11-25')


def test_load_market_checks_hash(tmp_path, no_network):
    derived = write_vintage(tmp_path, {'AAA': frame(PRICES, dividend=DIV, payable={EX: ('2017-12-05', m.ACTUAL_BASIS)}),
                                       'BBB': frame(PRICES)})
    with pytest.raises(ValueError, match='unexpected vintage'):
        m.load_market(tmp_path, derived, expected_sha256='0' * 64)
    digest = sha256((derived / 'manifest.json').read_bytes())
    market = m.load_market(tmp_path, derived, expected_sha256=digest)
    assert market.tickers == ('AAA', 'BBB') and list(market.sessions) == SESSIONS
    assert market.manifest_sha256 == digest
    assert market.payable == {('AAA', EX): ('2017-12-05', m.ACTUAL_BASIS)}
    assert m.load_market(tmp_path, derived, expected_sha256=None).vintage == 'data/derived/synthetic'


def test_load_market_rejects_other_vintage_by_default(tmp_path, no_network):
    derived = write_vintage(tmp_path, {'AAA': frame(PRICES)})
    with pytest.raises(ValueError, match='unexpected vintage'):
        m.load_market(tmp_path, derived)


@pytest.mark.skipif(not (ROOT / m.VINTAGE / 'manifest.json').exists(), reason='derived vintage is not in this checkout')
def test_real_vintage_loads(no_network):
    market = m.load_market(ROOT, Path(m.VINTAGE))
    assert len(market.tickers) == 10
    assert market.sessions[0] == '2007-05-30'
    assert len(market.sessions) == 4869
    assert market.vintage == m.VINTAGE and market.manifest_sha256 == m.VINTAGE_MANIFEST_SHA256
    assert market.payable[('BIL', '2008-03-03')][1] == m.PROXY_BASIS
    assert market.split_ratio.loc['2008-07-24', 'EEM'] == 3.0
    assert market.split_ratio.loc['2017-11-30', 'BIL'] == 0.5


def series(changes):
    return [changes.get(s, 0.) for s in SESSIONS]


def test_dividend_on_dropped_session_is_rejected():
    frames = {'AAA': frame(PRICES, dividend=series({'2017-12-01': 1.0}), payable={'2017-12-01': ('2017-12-05', m.ACTUAL_BASIS)}),
              'BBB': frame(PRICES).drop(index='2017-12-01')}
    with pytest.raises(ValueError, match='event on a session outside the common calendar: AAA/2017-12-01'):
        m.market_from_frames(frames)


def test_split_on_dropped_session_is_rejected():
    split = [2.0 if s == '2017-12-01' else 1.0 for s in SESSIONS]
    frames = {'AAA': frame(PRICES, split=split), 'BBB': frame(PRICES).drop(index='2017-12-01')}
    with pytest.raises(ValueError, match='event on a session outside the common calendar: AAA/2017-12-01'):
        m.market_from_frames(frames)


def test_events_before_start_are_not_checked():
    frames = {'AAA': frame(PRICES, dividend=series({'2017-11-27': 1.0}),
                           payable={'2017-11-27': ('2017-11-28', m.ACTUAL_BASIS)}),
              'BBB': frame(PRICES).drop(index='2017-11-27')}
    assert m.market_from_frames(frames, start='2017-11-28').sessions[0] == '2017-11-28'


def test_payment_on_dropped_session_is_rejected():
    frames = {'AAA': frame(PRICES, dividend=series({'2017-11-28': 1.0}),
                           payable={'2017-11-28': ('2017-12-01', m.ACTUAL_BASIS)}),
              'BBB': frame(PRICES).drop(index='2017-12-01')}
    with pytest.raises(ValueError, match='payment on a session outside the common calendar: AAA/2017-11-28 -> 2017-12-01'):
        m.market_from_frames(frames)


def test_payment_after_last_session_is_allowed():
    market = with_payable({EX: ('2017-12-14', m.ACTUAL_BASIS)})
    assert market.payable[('AAA', EX)] == ('2017-12-14', m.ACTUAL_BASIS)


def test_nan_dividend_on_dropped_session_is_ignored():
    dividend = [float('nan') if s == '2017-12-01' else 0. for s in SESSIONS]
    frames = {'AAA': frame(PRICES, dividend=dividend), 'BBB': frame(PRICES).drop(index='2017-12-01')}
    assert '2017-12-01' not in m.market_from_frames(frames).sessions
