"""Simulation loop: events of one session in spec order, orders at decision closes, scenarios, run invariants;
result files and the journaled, frozen run."""
from collections import namedtuple
from dataclasses import asdict, dataclass, field, replace
from datetime import date, timedelta
import functools
import math
from pathlib import Path
import pandas as pd
from alpha_lab.benchmarks import b0, b1, b2, b3, ref_spy
from alpha_lab.hypotheses import h1, h2, SIGNAL_COLUMNS_H1, SIGNAL_COLUMNS_H2
from alpha_lab.ledger import (CASH_TOLERANCE, Account, Order, Receivable, Trade, accrue_dividends, apply_splits,
                              credit_payouts, execute_orders, nav, receivables_total, size_orders)
from alpha_lab.market import (LAST_OPEN_SESSION, PROXY_BASIS, VINTAGE_MANIFEST_SHA256, load_market,
                              check_pay_sessions, proxy_pay_session)
from alpha_lab.metrics import compute_metrics
from alpha_lab.normalize import calendar, finite_number
from alpha_lab.pipeline import project_path, require_inside
from alpha_lab.provenance import Run, canonical_bytes, freeze, sha256

GRID = {'cost': (0, 0.001, 0.002, 0.005), 'lag': (1, 2), 'reserve': (0, 0.01, 0.02), 'proxy_pay_days': (0, 10, 30)}
WEIGHT_SUM_TOLERANCE = 1e-12
IDENTITY_TOLERANCE = 1e-6


@dataclass(frozen=True)
class Scenario:
    cost: float = 0.001
    lag: int = 1
    reserve: float = 0.01
    proxy_pay_days: int = 10

    def __post_init__(self):
        for name, allowed in GRID.items():
            if getattr(self, name) not in allowed:
                raise ValueError(f'{name} must be one of {allowed}: {getattr(self, name)!r}')


@dataclass(frozen=True)
class RunConfig:
    start_session: str
    end_session: str
    decision_sessions: tuple[str, ...] | None = None
    scenario: Scenario = Scenario()
    initial_cash: float = 100000.0

    def __post_init__(self):
        if not (finite_number(self.initial_cash) and self.initial_cash > 0):
            raise ValueError(f'initial_cash must be a finite number > 0: {self.initial_cash!r}')
        object.__setattr__(self, 'initial_cash', float(self.initial_cash))


@dataclass
class Result:
    decisions: list[dict]
    orders: list[Order]
    trades: list[Trade]
    payouts: list[Receivable]
    daily: list[dict]
    invariants: dict
    weights: list[dict] = field(default_factory=list)
    signals: list[dict] = field(default_factory=list)


def month_end_sessions(market, start, end, lag):
    """Last XNYS session of each month in [start, end] that is a market session with its execution <= end."""
    first = date.fromisoformat(start).replace(day=1)
    last = (date.fromisoformat(end).replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
    last_of_month = {(d.year, d.month): d.date().isoformat() for d in calendar(first, last).sessions}
    at = {s: i for i, s in enumerate(market.sessions)}
    return [s for s in last_of_month.values() if start <= s <= end and s in at
            and at[s] + lag < len(market.sessions) and market.sessions[at[s] + lag] <= end]


def validate(market, config, at):
    """Checks the run window and decision sessions; returns the decision sessions."""
    start, end, lag = config.start_session, config.end_session, config.scenario.lag
    if end > LAST_OPEN_SESSION:
        raise ValueError(f'end_session {end} is after the last open session {LAST_OPEN_SESSION}')
    for name, session in (('start_session', start), ('end_session', end)):
        if session not in at:
            raise ValueError(f'{name} is not a market session: {session}')
    if start > end:
        raise ValueError(f'start_session {start} is after end_session {end}')
    decisions = month_end_sessions(market, start, end, lag) if config.decision_sessions is None \
        else list(config.decision_sessions)
    for d in decisions:
        if d not in at:
            raise ValueError(f'decision is not a market session: {d}')
    if decisions != sorted(set(decisions)):
        raise ValueError('decision_sessions must be strictly increasing')
    for d in decisions:
        if not start <= d <= end:
            raise ValueError(f'decision {d} is outside [{start}, {end}]')
        if at[d] + lag >= len(market.sessions) or market.sessions[at[d] + lag] > end:
            raise ValueError(f'execution of decision {d} is after end_session {end}')
    for before, after in zip(decisions, decisions[1:]):
        if at[after] < at[before] + lag:
            raise ValueError(f'decision {after} while the order of {before} is still pending')
    return decisions


def pay_map(market, scenario):
    """(ticker, ex_session) -> (pay_session, basis); proxy rows are recomputed for the scenario's days."""
    k = scenario.proxy_pay_days
    out = {key: (proxy_pay_session(key[1], k), f'proxy_ex_plus_{k}_calendar_days') if basis == PROXY_BASIS
           else (pay, basis) for key, (pay, basis) in market.payable.items()}
    check_pay_sessions(out, market.sessions)
    return out


def provider_decision(provider, market, session):
    """Validated (weights, signals) of a provider that returns a weight dictionary or a Decision."""
    decision = provider(session, market.history(session))
    raw, signals = (decision.weights, decision.signals) if hasattr(decision, 'signals') else (decision, [])
    if set(raw) != set(market.tickers):
        raise ValueError(f'weights on {session} must cover exactly {list(market.tickers)}: got {sorted(raw)}')
    weights = {t: raw[t] for t in market.tickers}
    bad = [t for t, w in weights.items() if not (finite_number(w) and w >= 0)]
    if bad:
        raise ValueError(f'weights on {session} must be finite and >= 0: {bad}')
    if math.fsum(weights.values()) > 1 + WEIGHT_SUM_TOLERANCE:
        raise ValueError(f'weights on {session} sum to {math.fsum(weights.values())} > 1')
    return weights, signals


def provider_weights(provider, market, session):
    return provider_decision(provider, market, session)[0]


def check(passed, detail):
    return {'passed': bool(passed), 'detail': detail}


@dataclass
class Tally:
    """Quantities recorded during the day loop for the run invariants."""
    accrued: float = 0.0
    paid: float = 0.0
    nav_gap: float = 0.0
    flow_gap: float = 0.0
    split_events: list = field(default_factory=list)
    split_errors: list = field(default_factory=list)


def simulate(market, provider, config):
    """Day loop over [start_session, end_session]: spec §5 steps 1-5, close valuation, then sizing."""
    scenario = config.scenario
    at = {s: i for i, s in enumerate(market.sessions)}
    decisions = set(validate(market, config, at))
    opens, closes = market.open.to_dict('index'), market.close.to_dict('index')
    dividends, ratios = market.dividend.to_dict('index'), market.split_ratio.to_dict('index')
    pay = pay_map(market, scenario)
    account = Account.new(market.tickers, config.initial_cash)
    result, tally = Result([], [], [], [], [], {}), Tally()
    awaiting = {}  # execution session -> decisions row to complete
    for session in market.sessions[at[config.start_session]:at[config.end_session] + 1]:
        cash_before = account.cash
        held, queued, claims = dict(account.positions), [o.qty for o in account.pending], receivables_total(account)
        tally.split_events += [[t, session] for t in apply_splits(account, ratios[session])]
        tally.split_errors += [f'{t}/{session}' for t, r in ratios[session].items()
                               if account.positions[t] != held[t] * r]
        tally.split_errors += [f'{o.ticker}/{session}' for o, q in zip(account.pending, queued)
                               if o.qty != q * ratios[session][o.ticker]]
        if account.cash != cash_before or receivables_total(account) != claims:
            tally.split_errors.append(f'money/{session}')
        new = accrue_dividends(account, session, dividends[session],
                               {t: pay[(t, session)] for t, d in dividends[session].items() if d > 0})
        result.payouts += new
        credited = credit_payouts(account, session)
        trades, fill = execute_orders(account, session, opens[session], scenario.cost)
        result.trades += trades
        tally.accrued += sum(r.amount for r in new)
        tally.paid += sum(r.amount for r in credited)
        flow = sum(r.amount for r in credited) + sum(
            t.notional - t.cost if t.side == 'sell' else -(t.notional + t.cost) for t in trades)
        tally.flow_gap = max(tally.flow_gap, abs(account.cash - cash_before - flow))
        if session in awaiting:
            row = awaiting.pop(session)
            row['buy_fill'] = fill
            row['costs_usd'] = sum(t.cost for t in trades)
            row['turnover'] = sum(t.notional for t in trades) / row['nav']
        value = nav(account, closes[session])
        positions_value = sum(account.positions[t] * closes[session][t] for t in market.tickers
                              if account.positions[t])
        gap = abs(value - (account.cash + positions_value + tally.accrued - tally.paid))
        tally.nav_gap = max(tally.nav_gap, gap)
        result.daily.append({'session': session, 'cash': account.cash, 'receivables': receivables_total(account),
                             'positions_value': positions_value, 'nav': value, **account.positions})
        if session in decisions:
            execution = market.sessions[at[session] + scenario.lag]
            weights, signals = provider_decision(provider, market, session)
            result.weights.append({'decision_session': session, **weights})
            result.signals.extend(signals)
            result.orders += size_orders(account, session, execution, weights, closes[session], value,
                                         scenario.reserve)
            row = {'decision_session': session, 'execution_session': execution, 'nav': value,
                   'buy_fill': None, 'turnover': None, 'costs_usd': None}
            result.decisions.append(row)
            awaiting[execution] = row
    result.invariants = run_invariants(market, scenario, result, tally, receivables_total(account), at)
    return result


def run_invariants(market, scenario, result, tally, remaining, at):
    """Spec §8 checks from the recorded run; each is {'passed', 'detail'}."""
    notional = sum(t.notional for t in result.trades)
    cost_gap = max(abs(sum(t.cost for t in result.trades) - scenario.cost * notional),
                   abs(sum(d['costs_usd'] for d in result.decisions) - scenario.cost * notional))
    min_cash = min([d['cash'] for d in result.daily] + [t.cash_after for t in result.trades])
    settled = sum(r.amount for r in result.payouts if r.status == 'paid')
    conservation_gap = max(abs(tally.accrued - (tally.paid + remaining)), abs(settled - tally.paid))
    decision_nav = {d['decision_session']: d['nav'] for d in result.decisions}

    def sized(o):
        return math.floor((1 - scenario.reserve) * o.weight * decision_nav[o.decision_session] / o.close)

    mistimed = [f'{o.ticker}/{o.decision_session}' for o in result.orders
                if at[o.execution_session] - at[o.decision_session] != scenario.lag
                or o.close != market.close.at[o.decision_session, o.ticker] or o.target_qty != sized(o)]
    due = {(o.execution_session, o.ticker) for o in result.orders}
    mistimed += [f'{t.ticker}/{t.session}' for t in result.trades
                 if (t.session, t.ticker) not in due or t.price != market.open.at[t.session, t.ticker]]
    checks = {
        'cash_non_negative': check(min_cash >= -CASH_TOLERANCE, f'minimum cash {min_cash}'),
        'nav_identity': check(tally.nav_gap <= IDENTITY_TOLERANCE, f'maximum gap {tally.nav_gap}'),
        'cash_flow': check(tally.flow_gap <= IDENTITY_TOLERANCE, f'maximum gap {tally.flow_gap}'),
        'split_quantity_only': check(not tally.split_errors,
                                     f'{len(tally.split_events)} splits, violations {tally.split_errors}'),
        'receivable_conservation': check(conservation_gap <= IDENTITY_TOLERANCE,
                                         f'accrued {tally.accrued}, paid {tally.paid}, remaining {remaining}'),
        'execution_timing': check(not mistimed, f'{len(result.orders)} orders, {len(result.trades)} trades, '
                                                f'violations {mistimed}'),
        'costs': check(cost_gap <= IDENTITY_TOLERANCE, f'gap {cost_gap} on notional {notional}'),
    }
    proxy = {key for key, (_, basis) in market.payable.items() if basis == PROXY_BASIS}
    return {**checks, 'passed': all(c['passed'] for c in checks.values()), 'split_events': tally.split_events,
            'proxy_payouts': [[r.ticker, r.ex_session, r.pay_session] for r in result.payouts
                              if (r.ticker, r.ex_session) in proxy]}


def invariant_rotation(t, history):
    """Test provider, not a strategy: every ticker is held and the weights rotate with the month (spec §10)."""
    day = date.fromisoformat(t)
    month = 12 * day.year + day.month
    raw = {ticker: 1 + (month + i) % 3 for i, ticker in enumerate(sorted(history.tickers))}
    total = sum(raw.values())
    return {ticker: r / total for ticker, r in raw.items()}


# schedule: monthly | first_only; kind: test | benchmark | hypothesis
Provider = namedtuple('Provider', 'function version schedule kind parameters', defaults=({},))
PROVIDERS = {'invariant_rotation': Provider(invariant_rotation, '1', 'monthly', 'test'),
             'B0': Provider(b0, '1', 'monthly', 'benchmark'),
             'B1': Provider(b1, '1', 'monthly', 'benchmark'),
             'B2': Provider(b2, '1', 'monthly', 'benchmark'),
             'B3': Provider(b3, '1', 'monthly', 'benchmark'),
             'REF_SPY': Provider(ref_spy, '1', 'first_only', 'benchmark'),
             'H1_252_3': Provider(functools.partial(h1, lookback=252, k=3), '1', 'monthly', 'hypothesis',
                                  {'lookback': 252, 'k': 3}),
             'H1_252_4': Provider(functools.partial(h1, lookback=252, k=4), '1', 'monthly', 'hypothesis',
                                  {'lookback': 252, 'k': 4}),
             'H1_126_3': Provider(functools.partial(h1, lookback=126, k=3), '1', 'monthly', 'hypothesis',
                                  {'lookback': 126, 'k': 3}),
             'H1_126_4': Provider(functools.partial(h1, lookback=126, k=4), '1', 'monthly', 'hypothesis',
                                  {'lookback': 126, 'k': 4}),
             'H2_4of6': Provider(functools.partial(h2, h=4), '1', 'monthly', 'hypothesis',
                                 {'h': 4, 'parent': 'H1_252_3'}),
             'H2_5of6': Provider(functools.partial(h2, h=5), '1', 'monthly', 'hypothesis',
                                 {'h': 5, 'parent': 'H1_252_3'})}
DECISION_COLUMNS = ['decision_session', 'execution_session', 'nav', 'buy_fill', 'turnover', 'costs_usd']
ORDER_COLUMNS = ['decision_session', 'execution_session', 'ticker', 'weight', 'close', 'target_qty', 'held_qty',
                 'order_qty', 'filled_qty', 'status', 'cancel_reason']
TRADE_COLUMNS = ['session', 'ticker', 'side', 'qty', 'price', 'notional', 'cost', 'cash_after']
PAYOUT_COLUMNS = ['ticker', 'ex_session', 'pay_session', 'pay_basis', 'qty', 'amount_per_share', 'amount', 'status']
DAILY_COLUMNS = ['session', 'cash', 'receivables', 'positions_value', 'nav']


def weight_columns(tickers):
    return ['decision_session', *(f'w_{t}' for t in sorted(tickers)), 'usd']


def config_record(config, provider_name):
    """JSON form of the run parameters, journaled with the run and frozen in config.json."""
    sessions = config.decision_sessions
    entry = PROVIDERS[provider_name]
    provider = {'name': provider_name, 'version': entry.version}
    if entry.kind == 'hypothesis':
        provider['parameters'] = entry.parameters
    return {**asdict(config), 'decision_sessions': None if sessions is None else list(sessions),
            'provider': provider}


def csv_bytes(rows, columns):
    """Fixed columns, LF line ends and 10 significant digits, so equal results give equal bytes."""
    return pd.DataFrame(rows, columns=columns).to_csv(index=False, lineterminator='\n',
                                                      float_format='%.10g').encode()


def weight_rows(result, tickers):
    return [{**{f'w_{t}': w[t] for t in tickers}, 'decision_session': w['decision_session'],
             'usd': 1 - math.fsum(w[t] for t in tickers)} for w in result.weights]


def result_files(result, config, provider_name, market):
    """The seven frozen files, plus weights.csv for a benchmark or hypothesis provider, metrics.json for a benchmark
    and signals.csv for a hypothesis; none holds a run id, timestamp or path."""
    tickers = market.tickers
    orders = [{**asdict(o), 'order_qty': o.qty} for o in result.orders]  # qty at execution, after split conversion
    payouts = [{**asdict(r), 'pay_basis': r.basis, 'amount': r.amount} for r in result.payouts]
    daily = [{**d, **{f'qty_{t}': d[t] for t in tickers}} for d in result.daily]
    record = {**config_record(config, provider_name), 'vintage': market.vintage,
              'manifest_sha256': market.manifest_sha256}
    files = {'config.json': canonical_bytes(record),
             'decisions.csv': csv_bytes(result.decisions, DECISION_COLUMNS),
             'orders.csv': csv_bytes(orders, ORDER_COLUMNS),
             'trades.csv': csv_bytes([asdict(t) for t in result.trades], TRADE_COLUMNS),
             'payouts.csv': csv_bytes(payouts, PAYOUT_COLUMNS),
             'daily.csv': csv_bytes(daily, [*DAILY_COLUMNS, *(f'qty_{t}' for t in tickers)]),
             'invariants.json': canonical_bytes(result.invariants)}
    entry = PROVIDERS[provider_name]
    if entry.kind in ('benchmark', 'hypothesis'):
        files['weights.csv'] = csv_bytes(weight_rows(result, tickers), weight_columns(tickers))
    if entry.kind == 'benchmark':
        files['metrics.json'] = canonical_bytes(compute_metrics(market, result))
    if entry.kind == 'hypothesis':
        files['signals.csv'] = csv_bytes(result.signals, SIGNAL_COLUMNS_H2 if 'h' in entry.parameters
                                         else SIGNAL_COLUMNS_H1)
    return files


def run_simulation(root, derived, provider_name, config, parent=None, expected_sha256=VINTAGE_MANIFEST_SHA256):
    """Journaled N2/N3/N4 run on a verified vintage; data/runs/<run_id> is frozen only after simulate succeeds."""
    root = Path(root).resolve()
    derived = (root / derived).resolve()
    entry = PROVIDERS[provider_name]
    if entry.schedule == 'first_only':
        config = replace(config, decision_sessions=(config.start_session,))
    cfg = {**config_record(config, provider_name), 'derived_snapshot': project_path(root, derived),
           'expected_sha256': expected_sha256}
    purpose = {'benchmark': 'N3 benchmark run', 'hypothesis': 'N4 hypothesis run'}.get(entry.kind, 'N2 execution run')
    with Run(root, purpose, cfg, parent,
             candidate_ids=[provider_name] if entry.kind != 'test' else None) as run:
        try:
            require_inside(root, derived)
            market = load_market(root, derived, expected_sha256)
            run.base['universe'] = list(market.tickers)
            result = simulate(market, entry.function, config)
        except Exception as exc:
            if entry.kind != 'hypothesis':
                raise
            raise RuntimeError(f'{type(exc).__name__} in {provider_name} run; '
                               'message withheld under the N4 viewing restriction') from None
        target = root / 'data/runs' / run.run_id
        freeze(target, result_files(result, config, provider_name, market),
               {'derived_snapshot': cfg['derived_snapshot'], 'derived_manifest_sha256': market.manifest_sha256,
                'environment': run.env, 'run_id': run.run_id})
        failed = [name for name, c in result.invariants.items() if isinstance(c, dict) and not c['passed']]
        run.finish('completed' if result.invariants['passed'] else 'invariants_failed', [project_path(root, target)],
                   sha256((target / 'manifest.json').read_bytes()), failed)
    return target
