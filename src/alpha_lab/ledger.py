"""Account state and pure event functions for one session: split, accrue, credit, sells, buys, NAV."""
from dataclasses import dataclass
import math

CASH_TOLERANCE = 1e-8


@dataclass
class Receivable:
    ticker: str
    ex_session: str
    pay_session: str
    basis: str
    qty: float
    amount_per_share: float
    status: str = 'receivable'

    @property
    def amount(self):
        return self.qty * self.amount_per_share


@dataclass
class Order:
    decision_session: str
    execution_session: str
    ticker: str
    weight: float
    close: float
    target_qty: int
    held_qty: float
    qty: float  # signed, in current units (split-adjusted)
    filled_qty: float = 0.0  # executed magnitude, always >= 0
    status: str = 'pending'  # filled / partial / cancelled
    cancel_reason: str = ''  # no_valid_open / insufficient_cash / fractional_quantity / exceeds_position


@dataclass
class Trade:
    session: str
    ticker: str
    side: str  # sell / buy
    qty: float
    price: float
    notional: float
    cost: float
    cash_after: float


@dataclass
class Account:
    cash: float
    positions: dict[str, float]
    receivables: list[Receivable]
    pending: list[Order]

    @classmethod
    def new(cls, tickers, cash=100000.0):
        return cls(cash, {t: 0.0 for t in sorted(tickers)}, [], [])


def apply_splits(account, ratios):
    """Scale position and pending order quantity by each ratio != 1; cash and receivables are untouched."""
    split = []
    for ticker in sorted(ratios):
        ratio = ratios[ticker]
        orders = [o for o in account.pending if o.ticker == ticker]
        position = account.positions.get(ticker, 0.0)
        if ratio == 1 or (position == 0 and not orders):
            continue
        if position:
            account.positions[ticker] = position * ratio
        for o in orders:
            o.qty *= ratio
        split.append(ticker)
    return split


def accrue_dividends(account, session, dividends, pay):
    """Receivable for each ticker with dividend > 0 on the current (post-split) position."""
    new = []
    for ticker in sorted(dividends):
        position = account.positions.get(ticker, 0.0)
        if dividends[ticker] > 0 and position > 0:
            pay_session, basis = pay[ticker]
            new.append(Receivable(ticker, session, pay_session, basis, position, dividends[ticker]))
    account.receivables.extend(new)
    return new


def credit_payouts(account, session):
    """Move receivables due on `session` into cash, in accrual order."""
    due = [r for r in account.receivables if r.pay_session == session]
    for r in due:
        account.cash += r.amount
        r.status = 'paid'
    account.receivables[:] = [r for r in account.receivables if r.pay_session != session]
    return due


def size_orders(account, decision_session, execution_session, weights, closes, nav, reserve):
    """Orders to reach floor((1 - reserve) * w * nav / close) shares; zero-size orders are not created."""
    if account.pending:
        raise ValueError(f'decision on {decision_session} while orders are still pending')
    orders = []
    for ticker in sorted(weights):
        target = math.floor((1 - reserve) * weights[ticker] * nav / closes[ticker])
        held = account.positions.get(ticker, 0.0)
        if target - held != 0:
            orders.append(Order(decision_session, execution_session, ticker, weights[ticker], closes[ticker],
                                target, held, target - held))
    account.pending.extend(orders)
    return orders


def _valid_open(price):
    return price is not None and math.isfinite(price) and price > 0


def _settle(order, filled, reason):
    order.filled_qty = filled
    order.status = 'filled' if filled == abs(order.qty) else 'partial' if filled > 0 else 'cancelled'
    order.cancel_reason = '' if order.status == 'filled' else reason


def _trade(account, session, ticker, side, qty, price, cost):
    """Move cash and record the trade; the position is updated by the caller."""
    notional = qty * price
    account.cash += notional * (1 - cost) if side == 'sell' else -notional * (1 + cost)
    return Trade(session, ticker, side, qty, price, notional, cost * qty * price, account.cash)


def execute_orders(account, session, opens, cost):
    """Sells, then buys at the open for orders due on `session`; returns (trades, buy_fill)."""
    due = sorted((o for o in account.pending if o.execution_session == session), key=lambda o: o.ticker)
    account.pending[:] = [o for o in account.pending if o.execution_session != session]
    for o in due:
        if not _valid_open(opens.get(o.ticker)):
            _settle(o, 0.0, 'no_valid_open')
    live = [o for o in due if o.status == 'pending']
    trades = []
    for o in (o for o in live if o.qty < 0):
        qty = min(-o.qty, max(account.positions.get(o.ticker, 0.0), 0.0))
        if qty > 0:
            account.positions[o.ticker] -= qty
            trades.append(_trade(account, session, o.ticker, 'sell', qty, opens[o.ticker], cost))
        _settle(o, qty, 'exceeds_position')
    buys = [o for o in live if o.qty > 0]
    required = sum(o.qty * opens[o.ticker] * (1 + cost) for o in buys)
    fill = 1.0 if required == 0 else min(1.0, max(account.cash, 0.0) / required)
    for o in buys:
        qty = float(math.floor(fill * o.qty))
        if qty > 0:
            account.positions[o.ticker] = account.positions.get(o.ticker, 0.0) + qty
            trades.append(_trade(account, session, o.ticker, 'buy', qty, opens[o.ticker], cost))
        # whole shares only: a shortfall below floor(q) is cash, the fractional part alone is not
        _settle(o, qty, 'insufficient_cash' if qty < math.floor(o.qty) else 'fractional_quantity')
    if account.cash < -CASH_TOLERANCE:
        raise ValueError(f'cash {account.cash} below tolerance after execution on {session}')
    return trades, fill


def receivables_total(account):
    return sum(r.amount for r in account.receivables)


def nav(account, closes):
    """cash + positions at close + unpaid receivables."""
    held = sum(account.positions[t] * closes[t] for t in sorted(account.positions) if account.positions[t])
    return account.cash + held + receivables_total(account)
