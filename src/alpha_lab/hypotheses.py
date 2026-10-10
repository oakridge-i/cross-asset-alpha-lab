"""Section 7 hypothesis weight providers: H1 (relative strength) and H2 (month-persistence filter on the fixed parent
H1_252_3). Each provider returns the target weights together with the signal rows of the same computation
(spec 4.1, 4.3-4.5; protocol lines 93-107)."""
import math
from collections import namedtuple

from alpha_lab.features import (CASH, MONTH_LEVELS, RISKY, covariance, momentum, month_end_levels, monthly_excess,
                                require_warmup, sigma, total_return_index)
from alpha_lab.portfolio import VARIANCE_TOLERANCE, inverse_vol, risk_detail

Decision = namedtuple('Decision', 'weights signals')
SIGNAL_COLUMNS_H1 = ['decision_session', 'ticker', 'momentum', 'sigma', 'score', 'eligible', 'rank', 'selected', 'q',
                     'v', 'scale', 'weight']
SIGNAL_COLUMNS_H2 = SIGNAL_COLUMNS_H1 + ['parent_weight', 'excess_1', 'excess_2', 'excess_3', 'excess_4', 'excess_5',
                                         'excess_6', 'positive_months', 'filter_pass']
SIGNAL_COLUMNS_POLICY = SIGNAL_COLUMNS_H1 + ['selection_year', 'selected_config']
PARENT_LOOKBACK = 252
PARENT_K = 3


def _require_decision_session(t, history):
    if history.sessions[-1] != t:
        raise ValueError(f'history ends at {history.sessions[-1]}, not at the decision session {t}')


def h1(t, history, lookback, k):
    """H1(L, K) at the close of t: score S = M / sigma, eligible when S > 0, the first K by (-S, ticker) selected,
    inverse volatility with m / K of the budget, then the common risk rules (spec 4.3)."""
    _require_decision_session(t, history)
    require_warmup(history)
    index = total_return_index(history)
    vol = sigma(history)
    mom = momentum(index, lookback)
    score = {i: mom[i] / vol[i] for i in RISKY}
    order = sorted((i for i in RISKY if score[i] > 0.0), key=lambda i: (-score[i], i))
    selected = order[:k]
    q = inverse_vol(vol, selected, k)
    v, scale, weights = risk_detail(q, covariance(history))
    rank = {i: n for n, i in enumerate(order, 1)}
    signals = [{'decision_session': t, 'ticker': i, 'momentum': mom[i], 'sigma': vol[i], 'score': score[i],
                'eligible': i in rank, 'rank': rank.get(i), 'selected': i in selected, 'q': q[i], 'v': v[i],
                'scale': scale, 'weight': weights[i]} for i in sorted(RISKY)]
    return Decision(weights, signals)


def h2(t, history, h):
    """H2(h) at the close of t: the weight of H1(252, 3) kept where at least h of the latest six completed months
    have an excess return over BIL above zero, otherwise exactly 0.0; BIL takes the released weight (spec 4.4)."""
    parent = h1(t, history, PARENT_LOOKBACK, PARENT_K)
    excess = monthly_excess(month_end_levels(history, total_return_index(history), MONTH_LEVELS))
    months = {i: excess[i].tolist() for i in RISKY}
    positive = {i: sum(1 for e in months[i] if e > 0.0) for i in RISKY}
    weights = {i: parent.weights[i] if positive[i] >= h else 0.0 for i in RISKY}
    cash = 1.0 - math.fsum(weights.values())
    if cash < 0.0:
        if cash < -VARIANCE_TOLERANCE:
            raise ValueError(f'risky weights exceed 100%: cash {cash}')
        cash = 0.0
    weights[CASH] = float(cash)
    signals = [{**row, 'weight': weights[row['ticker']], 'parent_weight': row['weight'],
                **{f'excess_{j}': e for j, e in enumerate(months[row['ticker']], 1)},
                'positive_months': positive[row['ticker']], 'filter_pass': positive[row['ticker']] >= h}
               for row in parent.signals]
    return Decision(weights, signals)
