"""Synthetic frames and vintages for N2 tests."""
from pathlib import Path
import pandas as pd
from alpha_lab.provenance import freeze

SESSIONS = ['2017-11-27', '2017-11-28', '2017-11-29', '2017-11-30', '2017-12-01',
            '2017-12-04', '2017-12-05', '2017-12-06', '2017-12-07', '2017-12-08']


def frame(close, open=None, dividend=None, split=None, payable=None):
    """One ticker over SESSIONS; `payable` maps ex_session -> (payable_date, payable_basis)."""
    payable = payable or {}
    out = pd.DataFrame({'open': list(close if open is None else open), 'close': list(close),
                        'dividend': list(dividend or [0.] * len(SESSIONS)),
                        'split_ratio': list(split or [1.] * len(SESSIONS)),
                        'payable_date': [payable.get(s, ('', ''))[0] for s in SESSIONS],
                        'payable_basis': [payable.get(s, ('', ''))[1] for s in SESSIONS]},
                       index=pd.Index(SESSIONS, name='session'))
    numeric = ['open', 'close', 'dividend', 'split_ratio']
    out[numeric] = out[numeric].astype(float)
    return out


def write_vintage(root, frames):
    """Freeze frames as data/derived/synthetic/normalized/<T>.csv; returns the snapshot path."""
    files = {f'normalized/{t}.csv': frames[t].to_csv(index_label='session').encode() for t in sorted(frames)}
    return freeze(Path(root) / 'data/derived/synthetic', files, {'synthetic': True})
