"""Annualized one-way turnover of one run over `full` with two denominators: NAV at the decision close (the
published value, D022 item 11) and NAV at the Open of the execution session before the trades (D023 item 1).

Read-only: verifies the run directory and the approved vintage, prints the two values and writes nothing.
Usage: PYTHONPATH=src python docs/n4/turnover_denominator.py RUN_DIR VINTAGE_DIR
"""
import argparse
import json
import math
from pathlib import Path
import pandas as pd
from alpha_lab.features import ANNUAL
from alpha_lab.market import VINTAGE_MANIFEST_SHA256, load_market
from alpha_lab.metrics import BLOCKS
from alpha_lab.provenance import sha256, verify

FIRST, LAST = next((first, last) for name, first, last in BLOCKS if name == 'full')


def finite_positive(x):
    return x is not None and math.isfinite(x) and x > 0


def open_nav(market, daily, decision, execution):
    """cash + receivables at the decision close + dividends accrued at the execution session on the post-split
    quantity + post-split quantity at the execution Open (engine order: split, accrual, crediting, trades)."""
    row = daily.loc[decision]
    total = float(row['cash']) + float(row['receivables'])
    for t in market.tickers:
        held = float(row[f'qty_{t}'])
        if held == 0:
            continue
        qty = held * float(market.split_ratio.at[execution, t])
        price = float(market.open.at[execution, t])
        if not finite_positive(price):
            raise ValueError(f'held ticker without a finite positive Open: {t}/{execution}')
        total += qty * float(market.dividend.at[execution, t]) + qty * price
    return total


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('run_dir', type=Path)
    parser.add_argument('vintage_dir', type=Path)
    args = parser.parse_args()
    run, vintage = args.run_dir.resolve(), args.vintage_dir.resolve()
    verify(run)
    verify(vintage)
    digest = sha256((vintage / 'manifest.json').read_bytes())
    if digest != VINTAGE_MANIFEST_SHA256:
        raise ValueError(f'vintage is not the approved vintage: manifest sha256 {digest}')
    config = json.loads((run / 'config.json').read_bytes())
    if config['manifest_sha256'] != VINTAGE_MANIFEST_SHA256:
        raise ValueError(f'run was not made on the approved vintage: {config["manifest_sha256"]}')
    if config['scenario']['lag'] != 1:
        raise ValueError(f'the execution Open definition assumes lag 1: lag {config["scenario"]["lag"]}')
    market = load_market(vintage.parent, vintage, VINTAGE_MANIFEST_SHA256)

    text = {'decision_session': str, 'execution_session': str, 'session': str, 'ticker': str, 'side': str}
    decisions = pd.read_csv(run / 'decisions.csv', dtype=text)
    trades = pd.read_csv(run / 'trades.csv', dtype=text)
    daily = pd.read_csv(run / 'daily.csv', dtype=text).set_index('session')

    n_returns = sum(1 for s in daily.index[1:] if FIRST <= s <= LAST)
    notional = trades.groupby('session')['notional'].apply(lambda x: math.fsum(x.astype(float))).to_dict()
    close_terms, open_terms = [], []
    for d in decisions.itertuples(index=False):
        if not FIRST <= d.execution_session <= LAST:
            continue
        if market.index(d.execution_session) != market.index(d.decision_session) + 1:
            raise ValueError(f'execution is not the next session: {d.decision_session} -> {d.execution_session}')
        traded = notional.get(d.execution_session, 0.0)
        close_terms.append(traded / float(d.nav))
        open_terms.append(traded / open_nav(market, daily, d.decision_session, d.execution_session))
    print(f'turnover_annual full, NAV at the decision close: {math.fsum(close_terms) * ANNUAL / n_returns!r}')
    print(f'turnover_annual full, NAV at the execution Open before trades: '
          f'{math.fsum(open_terms) * ANNUAL / n_returns!r}')


if __name__ == '__main__':
    main()
