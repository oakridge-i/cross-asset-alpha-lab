"""Hand-derived wealth and timing fixtures; no strategy returns."""
import pandas as pd
import pytest
from alpha_lab import normalize as n


def frame(prices, dates=None, splits=None, dividends=None):
    dates = dates or ['2017-11-28', '2017-11-29', '2017-11-30', '2017-12-01'][:len(prices)]
    return pd.DataFrame({'Open': prices, 'High': prices, 'Low': prices, 'Close': prices,
                         'Adj Close': prices, 'Volume': [100]*len(prices),
                         'Stock Splits': splits or [0]*len(prices),
                         'Dividends': dividends or [0]*len(prices)}, index=pd.to_datetime(dates))


def norm(f, **kwargs):
    return n.normalize(f, 'TEST', '2026-10-06T00:00:00+00:00', 'abc', **kwargs)


def test_reverse_split_preserves_wealth():
    x = norm(frame([90, 90, 90, 91], splits=[0, 0, .5, 0]))
    assert x['close'].tolist() == [45, 45, 90, 91]
    assert x['split_ratio'].tolist() == [1, 1, .5, 1]
    assert x['total_return_index'].tolist() == pytest.approx([1, 1, 1, 91/90])


def test_forward_split_plus_same_day_dividend_no_double_count():
    x = norm(frame([10, 10, 9, 9], splits=[0, 0, 3, 0], dividends=[0, 0, 1, 0]))
    assert x['close'].tolist() == [30, 30, 9, 9]
    assert x['dividend'].tolist() == [0, 0, 1, 0]
    assert x['total_return_index'].tolist() == [1, 1, 1, 1]


def test_future_rebasing_does_not_change_past_prices_dividends_or_tr():
    before = norm(frame([30, 29], dividends=[0, 1]))
    later = norm(frame([10, 29/3, 10, 11], splits=[0, 0, 3, 0], dividends=[0, 1/3, 0, 0]))
    for col in ['close', 'dividend', 'total_return_index']:
        assert later[col].iloc[:2].tolist() == pytest.approx(before[col].tolist())


def test_proxy_payday_weekend_and_beyond_price_cutoff():
    x = norm(frame([10, 9], dates=['2026-10-01', '2026-10-02'], dividends=[0, 1]))
    assert x.iloc[-1]['payable_date'] == '2026-10-12'
    assert x.iloc[-1]['payable_basis'] == 'proxy_ex_plus_10_calendar_days'
    actual = norm(frame([10, 9], dividends=[0, 1]), payable={'2017-11-29': {'date':'2017-12-02','source':'issuer'}})
    assert actual.iloc[-1]['payable_date'] == '2017-12-04'
    assert actual.iloc[-1]['payable_basis'] == 'actual'


def test_early_close_still_available_at_18_ny():
    x = norm(frame([10], dates=['2023-11-24']))
    assert x.iloc[0]['available_at'] == '2023-11-24T18:00:00-05:00'


@pytest.mark.parametrize('change', ['nan', 'negative', 'ohlc', 'duplicate', 'non_session', 'missing', 'negative_dividend', 'negative_split'])
def test_bad_rows_are_rejected_not_repaired(change):
    f = frame([10, 10, 10, 10])
    if change == 'nan': f.iloc[0, 0] = float('nan')
    if change == 'negative': f.iloc[0, 0] = -1
    if change == 'ohlc': f.iloc[0, 1] = 9
    if change == 'duplicate': f.index = pd.to_datetime(['2017-11-28']*4)
    if change == 'non_session': f.index = pd.to_datetime(['2017-11-25','2017-11-29','2017-11-30','2017-12-01'])
    if change == 'missing': f = f.drop(f.index[1])
    if change == 'negative_dividend': f.loc[f.index[0], 'Dividends'] = -1
    if change == 'negative_split': f.loc[f.index[0], 'Stock Splits'] = -1
    with pytest.raises(ValueError): norm(f)


def test_sandy_closures_are_not_missing_bars():
    x = norm(frame([10, 10], dates=['2012-10-26', '2012-10-31']))
    assert len(x) == 2


def test_payable_before_ex_date_rejected():
    with pytest.raises(ValueError):
        norm(frame([10, 9], dividends=[0, 1]), payable={'2017-11-29': {'date':'2017-11-28','source':'issuer'}})


def test_sandy_closure_bar_is_rejected():
    with pytest.raises(ValueError, match='non-session'):
        norm(frame([10, 10], dates=['2012-10-26', '2012-10-29']))


def test_capital_gain_alone_counts_as_distribution():
    f = frame([10, 9])
    f['Capital Gains'] = [0, 0.5]
    assert norm(f)['dividend'].tolist() == [0, 0.5]


def test_dividend_and_capital_gain_on_one_date_rejected_until_basis_is_evidenced():
    f = frame([10, 9], dividends=[0, 1])
    f['Capital Gains'] = [0, 0.5]
    with pytest.raises(ValueError, match='capital gain'):
        norm(f)


def test_normalize_applies_corrections():
    # The last session carries its own real, uncorrected dividend: a correction on other sessions must
    # leave it (and its payable date) completely untouched.
    f = frame([100, 99, 98, 97], dividends=[0, 0.4, 0, 0.2])
    baseline = norm(f)
    corrections = {
        # Replace an existing Yahoo event (issuer amount differs) ...
        '2017-11-29': {'action': 'replace', 'yahoo_amount': 0.4, 'issuer_amount': 0.45,
                       'payable_date': '2017-12-05', 'source': 'issuer-ref-replace'},
        # ... and add an issuer-only event where Yahoo had none.
        '2017-11-30': {'action': 'add', 'yahoo_amount': None, 'issuer_amount': 1.0,
                       'payable_date': '2017-12-10', 'source': 'issuer-ref-add'},
    }
    x = norm(f, payable={'2017-11-29': {'date': '2017-12-05', 'source': 'issuer-ref-replace'},
                         '2017-11-30': {'date': '2017-12-10', 'source': 'issuer-ref-add'}},
            corrections=corrections)
    # Prices and splits are untouched by a dividend correction.
    assert x['close'].tolist() == baseline['close'].tolist()
    assert x['split_ratio'].tolist() == baseline['split_ratio'].tolist()
    # The session before the first correction is byte-identical: TR only changes from the corrected session on.
    assert x['total_return_index'].iloc[0] == baseline['total_return_index'].iloc[0]
    assert x['total_return_index'].tolist()[1:] != baseline['total_return_index'].tolist()[1:]
    assert x['dividend'].tolist() == [0, 0.45, 1.0, 0.2]
    assert x['source_dividend'].tolist() == baseline['source_dividend'].tolist()  # source column never rewritten
    assert x['dividend_basis'].tolist() == ['source', 'issuer_correction', 'issuer_correction', 'source']
    assert x['dividend_correction_source'].tolist() == ['', 'issuer-ref-replace', 'issuer-ref-add', '']
    assert x.loc['2017-11-29', ['payable_date', 'payable_basis']].tolist() == ['2017-12-05', 'actual']
    # 2017-12-10 is a Sunday: the actual payable date snaps forward to the next session.
    assert x.loc['2017-11-30', ['payable_date', 'payable_basis']].tolist() == ['2017-12-11', 'actual']
    # The uncorrected real dividend on the last session is untouched, down to its proxy payable date.
    assert x.loc['2017-12-01', ['dividend', 'payable_date', 'payable_basis']].tolist() == \
        baseline.loc['2017-12-01', ['dividend', 'payable_date', 'payable_basis']].tolist()
    # No corrections at all: every row keeps the 'source' basis and an empty correction reference.
    assert baseline['dividend_basis'].tolist() == ['source'] * 4
    assert baseline['dividend_correction_source'].tolist() == [''] * 4


def test_correction_rejects_unknown_or_inconsistent():
    f = frame([100, 99, 98, 97], dividends=[0, 0.4, 0, 0])
    with pytest.raises(ValueError, match='not a session'):
        norm(f, corrections={'2099-01-01': {'action': 'replace', 'yahoo_amount': 0.4, 'issuer_amount': 0.45,
                                            'payable_date': None, 'source': 'ref'}})
    # Stale correction: the amount recorded at reconciliation time no longer matches the source event.
    with pytest.raises(ValueError, match='disagrees'):
        norm(f, corrections={'2017-11-29': {'action': 'replace', 'yahoo_amount': 0.5, 'issuer_amount': 0.45,
                                            'payable_date': None, 'source': 'ref'}})
    # An 'add' where Yahoo already carries an event on that session must be rejected, not merged.
    with pytest.raises(ValueError, match='conflicts'):
        norm(f, corrections={'2017-11-29': {'action': 'add', 'yahoo_amount': None, 'issuer_amount': 0.45,
                                            'payable_date': None, 'source': 'ref'}})
