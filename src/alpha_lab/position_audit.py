"""Independent position-balance audit of frozen runs (D026): reconciles every recorded position with the vintage
split ratios and the filled trades, every trade with the vintage open, the scenario cost and its order, and every
order row with the vintage sessions, the scenario lag and the fill it records. Reads only config.json, daily.csv,
trades.csv and orders.csv of a run and the vintage; never the engine's account object."""
import csv
import json
import math
from pathlib import Path
from alpha_lab.engine import DAILY_COLUMNS, ORDER_COLUMNS, TRADE_COLUMNS
from alpha_lab.market import VINTAGE_MANIFEST_SHA256, load_market
from alpha_lab.pipeline import project_path, require_inside
from alpha_lab.provenance import Run, canonical_bytes, freeze, sha256, verify

# Frozen CSV files carry 10 significant digits (engine.csv_bytes, '%.10g'), so each parsed operand is off by at most
# 0.5e-9 of its own magnitude. Comparing a - b where a and b are sums of such operands, the rounding error is at most
# 0.5e-9 times the sum of the operand magnitudes; 1e-9 of that sum bounds it with a factor of two to spare, and the
# absolute 1e-9 covers zero positions. The product case notional = qty * price carries three roundings (qty, price and
# notional), 1.5e-9 relative, against a tolerance of 2e-9: a margin of about 1.33x, still safe but thinner.
# Detection margin: the tolerance on a position is about 2e-9 times its size (the carried and the recorded position
# both enter the magnitude), so a one-share error is detected in every session for positions below about 5e8 shares,
# with a margin of about 5x at 1e8 shares.
ABS_TOLERANCE = 1e-9
REL_TOLERANCE = 1e-9
TRADE_KINDS = ('price', 'notional', 'cost', 'order_link', 'filled_qty', 'side', 'order_without_trade',
               'trade_without_fill', 'unknown')
# Order checks (D026, addition of 10 October 2026), counted once per orders.csv row and kind: order_value (order_qty
# not finite or zero, filled_qty not finite or negative), order_reference (ticker not in the vintage, decision or
# execution session outside the run window), order_timing (execution not `lag` vintage sessions after the decision),
# fill_bound (filled_qty above abs(order_qty)) and order_status (status, cancel reason and fill disagree).
ORDER_KINDS = ('order_value', 'order_reference', 'order_timing', 'fill_bound', 'order_status')
# Settled orders in orders.csv are filled, partial or cancelled, and the cancel reasons go with them: a filled order
# has no reason; a sell that is not filled in full is short of the position, a buy short of cash or of a whole share; an
# order without a valid open in the vintage is cancelled with no_valid_open and in no other way.
SHORTFALL_REASONS = {'buy': ('insufficient_cash', 'fractional_quantity'), 'sell': ('exceeds_position',)}
NO_OPEN_REASON = 'no_valid_open'
# Order of failure checks at the same session and ticker when naming the first failure.
CHECK_ORDER = ('sessions', 'columns', 'position', 'cumulative', *TRADE_KINDS, *ORDER_KINDS)


def within(difference, magnitude):
    return math.isfinite(difference) and abs(difference) <= ABS_TOLERANCE + REL_TOLERANCE * magnitude


def read_csv(path):
    with open(path, encoding='utf-8', newline='') as stream:
        reader = csv.DictReader(stream)
        return reader.fieldnames or [], list(reader)


def number(text):
    try:
        return float(text)
    except (TypeError, ValueError):
        return math.nan


def order_failures(order, market, window, at, lag):
    """Kinds of the order checks that one orders.csv row fails, from the row, the vintage and the scenario lag."""
    bad = set()
    ticker, decision, execution = order['ticker'], order['decision_session'], order['execution_session']
    known = ticker in market.tickers and decision in window and execution in window
    if not known:
        bad.add('order_reference')
    elif at[execution] - at[decision] != lag:
        bad.add('order_timing')
    ordered, filled = number(order['order_qty']), number(order['filled_qty'])
    if not (math.isfinite(ordered) and ordered != 0 and math.isfinite(filled) and filled >= 0):
        return bad | {'order_value'}
    size = abs(ordered)
    # filled_qty and order_qty are rounded to 10 significant digits: equal within the audit tolerance is equal.
    full = abs(filled - size) <= ABS_TOLERANCE + REL_TOLERANCE * (filled + size)
    if not full and filled > size:
        return bad | {'fill_bound'}
    status, reason = order['status'], order['cancel_reason']
    reasons = SHORTFALL_REASONS['buy' if ordered > 0 else 'sell']
    opening = float(market.open.at[execution, ticker]) if known else None  # None: the row names no vintage open
    if opening is not None and not (math.isfinite(opening) and opening > 0):
        consistent = status == 'cancelled' and filled == 0 and reason == NO_OPEN_REASON
    elif status == 'filled':
        consistent = full and reason == ''
    elif status == 'partial':
        consistent = filled > 0 and reason in reasons
    elif status == 'cancelled':
        consistent = filled == 0 and reason in (reasons if opening is not None else (*reasons, NO_OPEN_REASON))
    else:
        consistent = False
    return bad if consistent else bad | {'order_status'}


def audit_run(run_dir, market):
    """Audit of one frozen run against `market` (its vintage); returns a JSON-ready dict of counts and flags."""
    run_dir = Path(run_dir)
    config = json.loads((run_dir / 'config.json').read_bytes())
    cost, lag = config['scenario']['cost'], config['scenario']['lag']
    tickers = list(market.tickers)
    sessions = [s for s in market.sessions if config['start_session'] <= s <= config['end_session']]
    daily_header, daily = read_csv(run_dir / 'daily.csv')
    trade_header, trades = read_csv(run_dir / 'trades.csv')
    order_header, orders = read_csv(run_dir / 'orders.csv')
    failures = []  # (session, ticker, check)
    kinds = dict.fromkeys(TRADE_KINDS, 0)
    order_kinds = dict.fromkeys(ORDER_KINDS, 0)
    out = {'sessions': len(daily), 'positions_checked': 0, 'position_failures': 0, 'cumulative_failures': 0,
           'max_position_difference': 0.0, 'trades': len(trades), 'trade_failures': 0,
           'trade_failure_kinds': kinds, 'orders_checked': len(orders), 'order_failures': 0,
           'order_failure_kinds': order_kinds, 'structure_failures': 0}
    structure = []
    if daily_header != [*DAILY_COLUMNS, *(f'qty_{t}' for t in tickers)] or trade_header != TRADE_COLUMNS \
            or order_header != ORDER_COLUMNS:
        structure.append((None, None, 'columns'))
    if [r.get('session') for r in daily] != sessions:
        structure.append((None, None, 'sessions'))
    if structure:
        out['structure_failures'] = len(structure)
        return finish(out, structure)

    window = set(sessions)
    at = {s: i for i, s in enumerate(market.sessions)}
    invalid_values = set()  # indexes of order rows that fail order_value
    for i, o in enumerate(orders):
        bad = order_failures(o, market, window, at, lag)
        if 'order_value' in bad:
            invalid_values.add(i)
        for kind in sorted(bad):
            order_kinds[kind] += 1
            failures.append((o['execution_session'], o['ticker'], kind))
    out['order_failures'] = sum(order_kinds.values())

    bought = {}  # (session, ticker) -> filled buy quantity; sells below
    sold = {}
    trade_keys = {}
    order_index = {}  # (execution_session, ticker) -> order rows
    for o in orders:
        order_index.setdefault((o['execution_session'], o['ticker']), []).append(o)
    for t in trades:
        key = (t['session'], t['ticker'])
        trade_keys[key] = trade_keys.get(key, 0) + 1
        qty, price, notional, paid = (number(t[c]) for c in ('qty', 'price', 'notional', 'cost'))
        if t['session'] not in window or t['ticker'] not in tickers or not (math.isfinite(qty) and qty > 0):
            kinds['unknown'] += 1
            failures.append((*key, 'unknown'))
            continue
        if t['side'] == 'buy':
            bought[key] = bought.get(key, 0.0) + qty
        elif t['side'] == 'sell':
            sold[key] = sold.get(key, 0.0) + qty
        opening = float(market.open.at[t['session'], t['ticker']])
        checks = {'price': math.isfinite(price) and price > 0 and within(price - opening, abs(price) + abs(opening)),
                  'notional': math.isfinite(notional) and notional >= 0
                  and within(notional - qty * price, abs(notional) + abs(qty * price)),
                  'cost': math.isfinite(paid) and paid >= 0
                  and within(paid - cost * notional, abs(paid) + abs(cost * notional))}
        if t['side'] not in ('buy', 'sell'):
            checks['side'] = False
        linked = order_index.get(key, [])
        if len(linked) != 1:
            checks['order_link'] = False
        else:
            order = linked[0]
            filled, signed = number(order['filled_qty']), number(order['order_qty'])
            checks['filled_qty'] = within(filled - qty, abs(filled) + abs(qty))
            checks['side'] = checks.get('side', True) and (
                (t['side'] == 'buy' and signed > 0) or (t['side'] == 'sell' and signed < 0))
        for kind, ok in checks.items():
            if not ok:
                kinds[kind] += 1
                failures.append((*key, kind))
    for i, o in enumerate(orders):
        if i in invalid_values:  # an invalid fill is already counted; it is not read as "no fill"
            continue
        key = (o['execution_session'], o['ticker'])
        filled, count = number(o['filled_qty']), trade_keys.get(key, 0)
        if filled > 0 and count != 1:
            kinds['order_without_trade'] += 1
            failures.append((*key, 'order_without_trade'))
        elif not filled > 0 and count != 0:
            kinds['trade_without_fill'] += 1
            failures.append((*key, 'trade_without_fill'))
    out['trade_failures'] = sum(kinds.values())

    recorded_previous = dict.fromkeys(tickers, 0.0)  # accounts start in cash
    cumulative = dict.fromkeys(tickers, 0.0)
    cumulative_magnitude = dict.fromkeys(tickers, 0.0)  # sum of the operand magnitudes of the cumulative chain
    largest = 0.0
    for row in daily:
        session = row['session']
        for ticker in tickers:
            key = (session, ticker)
            ratio = float(market.split_ratio.at[session, ticker])
            buy, sell = bought.get(key, 0.0), sold.get(key, 0.0)
            recorded = number(row[f'qty_{ticker}'])
            carried = ratio * recorded_previous[ticker]
            expected = carried + buy - sell
            difference = expected - recorded
            out['positions_checked'] += 1
            if not within(difference, abs(carried) + buy + sell + abs(recorded)):
                out['position_failures'] += 1
                failures.append((*key, 'position'))
            cumulative[ticker] = ratio * cumulative[ticker] + buy - sell
            cumulative_magnitude[ticker] = ratio * cumulative_magnitude[ticker] + buy + sell
            drift = cumulative[ticker] - recorded
            if not within(drift, cumulative_magnitude[ticker] + abs(recorded)):
                out['cumulative_failures'] += 1
                failures.append((*key, 'cumulative'))
            largest = max([largest, *(abs(d) for d in (difference, drift) if math.isfinite(d))])
            recorded_previous[ticker] = recorded
    out['max_position_difference'] = largest
    return finish(out, failures)


def finish(out, failures):
    """Pass flag and the first failure in session order (a session and a ticker are not figures)."""
    out['passed'] = not failures
    if failures:
        session, ticker, check = min(failures, key=lambda f: (f[0] or '', f[1] or '', CHECK_ORDER.index(f[2])))
        out['first_failure'] = {'session': session, 'ticker': ticker, 'check': check}
    else:
        out['first_failure'] = None
    return out


def audited_runs(root, run_dirs, expected_sha256):
    """Verified run directories inside data/runs on one approved vintage; returns (paths, market)."""
    runs = (root / 'data/runs').resolve()
    paths, manifests, configs = [], [], []
    for d in run_dirs:
        path = (root / d).resolve()
        if path.parent != runs:
            raise ValueError(f'run directory outside data/runs: {d}')
        manifests.append(verify(path))
        configs.append(json.loads((path / 'config.json').read_bytes()))
        paths.append(path)
    if not paths:
        raise ValueError('at least one run directory required')
    if len({p.name for p in paths}) != len(paths):
        raise ValueError('a run directory is given more than once')
    derived = {m['metadata']['derived_snapshot'] for m in manifests}
    if len(derived) != 1:
        raise ValueError(f'runs on different vintages: {sorted(derived)}')
    snapshot = (root / derived.pop()).resolve()
    require_inside(root, snapshot)
    market = load_market(root, snapshot.relative_to(root), expected_sha256)
    for path, manifest, config in zip(paths, manifests, configs):
        if not (config['manifest_sha256'] == manifest['metadata']['derived_manifest_sha256'] == market.manifest_sha256
                and config['vintage'] == market.vintage):
            raise ValueError(f'{path.name}: run vintage is not the approved vintage')
    return paths, market


def build_position_audit(root, run_dirs, parent=None, expected_sha256=VINTAGE_MANIFEST_SHA256):
    """Journaled audit of frozen runs; freezes data/reports/<run_id>/position_audit.json and returns that path.
    Status completed when every run passes, otherwise audit_failed with the failing run ids as warnings."""
    root = Path(root).resolve()
    config = {'runs': [project_path(root, (root / d).resolve()) for d in run_dirs], 'expected_sha256': expected_sha256}
    with Run(root, 'Position audit', config, parent, candidate_ids=[]) as run:
        paths, market = audited_runs(root, run_dirs, expected_sha256)
        run.base['universe'] = list(market.tickers)
        audits = {p.name: audit_run(p, market) for p in paths}
        failed = [p.name for p in paths if not audits[p.name]['passed']]
        # An audit receipt, not an evaluation document: run ids are its keys.
        document = {'runs': audits, 'totals': {'runs': len(audits), 'runs_passed': len(audits) - len(failed)}}
        sources = [{'run_id': p.name, 'manifest_sha256': sha256((p / 'manifest.json').read_bytes())} for p in paths]
        target = root / 'data/reports' / run.run_id
        freeze(target, {'position_audit.json': canonical_bytes(document)},
               {'sources': sources, 'derived_manifest_sha256': market.manifest_sha256, 'environment': run.env,
                'run_id': run.run_id})
        run.finish('audit_failed' if failed else 'completed', [project_path(root, target)],
                   sha256((target / 'manifest.json').read_bytes()), failed)
    return target
