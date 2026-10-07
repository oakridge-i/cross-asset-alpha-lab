"""Simulation loop: events of one session in spec order, orders at decision closes, scenarios, run invariants."""
from dataclasses import dataclass, field
from datetime import date, timedelta
import math
from alpha_lab.ledger import (CASH_TOLERANCE, Account, Order, Receivable, Trade, accrue_dividends, apply_splits,
                              credit_payouts, execute_orders, nav, receivables_total, size_orders)
from alpha_lab.market import LAST_OPEN_SESSION, PROXY_BASIS, proxy_pay_session
from alpha_lab.normalize import calendar, finite_number

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


@dataclass
class Result:
    decisions: list[dict]
    orders: list[Order]
    trades: list[Trade]
    payouts: list[Receivable]
    daily: list[dict]
    invariants: dict


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
    return {key: (proxy_pay_session(key[1], k), f'proxy_ex_plus_{k}_calendar_days') if basis == PROXY_BASIS
            else (pay, basis) for key, (pay, basis) in market.payable.items()}


def provider_weights(provider, market, session):
    raw = provider(session, market.history(session))
    if set(raw) != set(market.tickers):
        raise ValueError(f'weights on {session} must cover exactly {list(market.tickers)}: got {sorted(raw)}')
    weights = {t: raw[t] for t in market.tickers}
    bad = [t for t, w in weights.items() if not (finite_number(w) and w >= 0)]
    if bad:
        raise ValueError(f'weights on {session} must be finite and >= 0: {bad}')
    if math.fsum(weights.values()) > 1 + WEIGHT_SUM_TOLERANCE:
        raise ValueError(f'weights on {session} sum to {math.fsum(weights.values())} > 1')
    return weights


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
            weights = provider_weights(provider, market, session)
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
