"""Section 11 metrics of one benchmark run, from unrounded in-memory values (protocol lines 46, 151, 157)."""
import math
import numpy as np
from alpha_lab.features import ANNUAL, CASH, RISKY, total_return_index
from alpha_lab.market import LAST_OPEN_SESSION
from alpha_lab.portfolio import GROUPS

METRICS_SCHEMA = 1
BLOCKS = (('full', '2009-01-01', '2022-12-31'), ('development', '2009-01-01', '2013-12-31'),
          ('walk_forward', '2014-01-01', '2022-12-31'), ('2014-2016', '2014-01-01', '2016-12-31'),
          ('2017-2019', '2017-01-01', '2019-12-31'), ('2020-2022', '2020-01-01', '2022-12-31'))
PERIODS = BLOCKS + tuple((str(y), f'{y}-01-01', f'{y}-12-31') for y in range(2009, 2023))
# Runs that start after 2009 (the N5 policy and its comparator) have no `full` or `development` period (spec 4.2, P3).
WF_PERIODS = BLOCKS[2:] + tuple((str(y), f'{y}-01-01', f'{y}-12-31') for y in range(2014, 2023))
UTILITY_PENALTY = 1.5


def number(x):
    """Python float, or None when undefined (canonical JSON forbids NaN and infinity)."""
    x = float(x)
    return x if math.isfinite(x) else None


def shares(market, daily):
    """Per daily row: cash, BIL, receivables, risky value, group and ticker values, each divided by NAV."""
    risky = [t for t in RISKY if t in market.tickers]
    out = []
    for row in daily:
        close, nav = market.close.loc[row['session']], row['nav']
        value = {t: row[t] * close[t] / nav for t in {*risky, CASH} & set(market.tickers)}
        out.append({'cash_usd': row['cash'] / nav, 'bil': value.get(CASH, 0.0), 'receivables': row['receivables'] / nav,
                    'risky': math.fsum(value[t] for t in risky),
                    'group': {g: math.fsum(value[t] for t in ts if t in value) for g, ts in GROUPS.items()},
                    'weight': {t: value[t] for t in risky}})
    return out


def period_metrics(first, last, daily, excess, held, decisions, targets):
    """Metrics of the daily rows with first <= session <= last, or None when the period has no return."""
    rows = [i for i in range(1, len(daily)) if first <= daily[i]['session'] <= last]
    if not rows:
        return None
    navs = np.array([daily[i]['nav'] for i in rows], dtype=float)
    base = float(daily[rows[0] - 1]['nav'])
    prev = np.concatenate(([base], navs[:-1]))
    r, e, n = navs / prev - 1, np.array([excess[daily[i]['session']] for i in rows]), len(rows)
    growth = navs[-1] / base
    path = np.concatenate(([base], navs))
    mine = [d for d in decisions if first <= d['execution_session'] <= last]
    turnover = math.fsum(d['turnover'] for d in mine)
    cost = math.fsum(d['costs_usd'] / d['nav'] for d in mine)
    risky_targets = [targets[d['decision_session']] for d in mine]
    sessions = [held[i] for i in rows]

    def mean(f):
        return number(math.fsum(f(s) for s in sessions) / n)

    def high(f):
        return number(max(f(s) for s in sessions))

    var_e = e.var(ddof=1) if n > 1 else None
    std_e = e.std(ddof=1) if n > 1 else None
    out = {'n_returns': n, 'total_return': number(growth - 1), 'cagr': number(growth ** (ANNUAL / n) - 1),
           'volatility': number(math.sqrt(ANNUAL) * r.std(ddof=1)) if n > 1 else None,
           'mean_excess': number(ANNUAL * e.mean()),
           'sharpe_bil': number(math.sqrt(ANNUAL) * e.mean() / std_e) if n > 1 and std_e > 0 else None,
           'utility': number(ANNUAL * e.mean() - UTILITY_PENALTY * ANNUAL * var_e) if n > 1 else None,
           'max_drawdown': number((path / np.maximum.accumulate(path) - 1).min()),
           'decisions': len(mine), 'turnover': number(turnover), 'turnover_annual': number(turnover * ANNUAL / n),
           'costs_usd': number(math.fsum(d['costs_usd'] for d in mine)), 'cost_ratio': number(cost),
           'mean_cash_usd': mean(lambda s: s['cash_usd']), 'mean_bil': mean(lambda s: s['bil']),
           'mean_cash_plus_bil': mean(lambda s: s['cash_usd'] + s['bil']),
           'mean_receivables': mean(lambda s: s['receivables']), 'mean_risky': mean(lambda s: s['risky']),
           'mean_group': {g: mean(lambda s, g=g: s['group'][g]) for g in GROUPS},
           'mean_weight': {t: mean(lambda s, t=t: s['weight'][t]) for t in held[rows[0]]['weight']},
           'max_group': {g: high(lambda s, g=g: s['group'][g]) for g in GROUPS},
           'max_weight': {t: high(lambda s, t=t: s['weight'][t]) for t in held[rows[0]]['weight']},
           'mean_target_risky': number(math.fsum(risky_targets) / len(mine)) if mine else None}
    return out


def periods_for(config):
    """WF_PERIODS for a run that starts after 2009-01-01, else PERIODS."""
    return WF_PERIODS if config.start_session > '2009-01-01' else PERIODS


def excess_series(market, result):
    """{session: daily return minus the theoretical BIL return} for every daily row after the first."""
    daily = result.daily
    if any(d['session'] > LAST_OPEN_SESSION for d in daily):
        raise ValueError(f'session after {LAST_OPEN_SESSION}')
    if not daily:
        return {}
    index = total_return_index(market.history(daily[-1]['session']))[CASH]
    bil = (index / index.shift(1) - 1).to_dict()
    navs = {d['session']: d['nav'] for d in daily}
    return {s: navs[s] / navs[daily[i - 1]['session']] - 1 - bil[s] for i, s in
            ((i, d['session']) for i, d in enumerate(daily) if i > 0)}


def compute_metrics(market, result, periods=PERIODS):
    """{'schema_version', 'periods': {name: metrics}}; periods without a return are omitted."""
    daily = result.daily
    if any(d['session'] > LAST_OPEN_SESSION for d in daily):
        raise ValueError(f'session after {LAST_OPEN_SESSION}')
    if not daily:
        return {'schema_version': METRICS_SCHEMA, 'periods': {}}
    excess = excess_series(market, result)
    targets = {w['decision_session']: math.fsum(w[t] for t in RISKY if t in w) for w in result.weights}
    held = shares(market, daily)
    out = {}
    for name, first, last in periods:
        metrics = period_metrics(first, last, daily, excess, held, result.decisions, targets)
        if metrics is not None:
            out[name] = metrics
    return {'schema_version': METRICS_SCHEMA, 'periods': out}
