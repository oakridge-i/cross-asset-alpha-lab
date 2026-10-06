"""Boundary tests: exact source flags, raw capture and failed/empty responses."""
import pandas as pd
import pytest
from alpha_lab import acquire as a


class Feed:
    def __init__(self, frame, files):
        self.frame, self.files = frame, files

    def history(self, **options):
        assert options['auto_adjust'] is False
        assert options['back_adjust'] is False
        assert options['repair'] is False
        assert options['keepna'] is True
        assert options['actions'] is True
        assert options['interval'] == '1d'
        assert options['end'] == '2026-10-06'
        self.files['raw/TEST-0.json'] = b'{"chart":{}}'
        return self.frame


def test_preserves_raw_and_output_without_filling(tmp_path):
    frame = pd.DataFrame({'Open': [1., float('nan')]}, index=['2026-10-02', '2026-10-05'])
    files = {}
    a.download(['TEST'], '1990-01-01', '2026-10-06', files,
               ticker_factory=lambda symbol, session: Feed(frame, files), session=object())
    assert files['raw/TEST-0.json'] == b'{"chart":{}}'
    assert b'2026-10-05,' in files['adapter/TEST.csv']


def test_empty_frame_raises_and_keeps_raw():
    files = {}
    with pytest.raises(ValueError, match='empty'):
        a.download(['TEST'], '1990-01-01', '2026-10-06', files,
                   ticker_factory=lambda symbol, session: Feed(pd.DataFrame(), files), session=object())
    assert 'raw/TEST-0.json' in files


def test_absent_raw_body_is_rejected():
    class Uncaptured:
        def history(self, **kwargs):
            return pd.DataFrame({'Open': [1]})
    with pytest.raises(ValueError, match='raw'):
        a.download(['TEST'], '1990-01-01', '2026-10-06', {},
                   ticker_factory=lambda symbol, session: Uncaptured(), session=object())
