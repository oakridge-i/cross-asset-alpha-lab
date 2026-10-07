# N2: account and execution engine - specification

Date: 7 October 2026. Branch `claude/n2-execution`. Basis: RESEARCH_PROTOCOL.md section 8 (lines 118-126) and sections 3 and 4 (lines 40-54), DATA_CONTRACT.md, docs/MASTER_PLAN.md section 4.4 (lines 184-199) and section 5 (line 305), decision D020. Agreed with the user on 7 October 2026: N2 covers execution only; the weight algorithm (protocol section 5), the metrics (section 11), B0-B3 and REF_SPY belong to N3.

## 1. Goal and boundaries

N2 creates a tested engine that, from target weights on a decision date, builds orders, executes them at Open, accounts for costs, splits, dividends and cash, keeps a journal, and provides manual reconciliations of the mechanics. N2 succeeds when all manual reconciliations agree with the engine's calculation, a run checking the invariants on real data is completed and registered, and the mechanics are described in EXECUTION_MODEL.md.

Outside N2: target-weight calculation (section 5), metrics (section 11), B0-B3, REF_SPY, H1/H2, and any return tables. There are no new dependencies (numpy, pandas and exchange_calendars are already in requirements.lock).

## 2. Input data

Only the vintage `data/derived/20261006T172442-80ef993493` (D020). The loader verifies the manifest (`provenance.verify`) and that the SHA-256 of the manifest equals `f89346107cf7da6ca052693d188b8a576a08d42024c86865b0a42a63b1d294f2`; another vintage is rejected until a new decision exists.

Columns used from `normalized/<TICKER>.csv`: `session`, `open`, `close`, `dividend` (as-traded per share, including capital gains), `split_ratio` (new/old on the split date, otherwise 1), `payable_date` (the crediting session, set on the ex-date row when dividend > 0), `payable_basis`.

The `payable_basis` contract. On a row with dividend > 0 the loader accepts exactly two values: `actual` and `proxy_ex_plus_10_calendar_days` (this is how normalize.py records the computed date with pay_delay_days = 10 from the snapshot configuration). Any other value, an empty value when dividend > 0, or a `payable_date` earlier than the ex-date is a load error. For `proxy_ex_plus_10_calendar_days` rows the loader checks that `payable_date` equals the first session of the common calendar no earlier than ex-date + 10 calendar days; a mismatch is an error. Below in this specification, "proxy row" means a row with payable_basis = `proxy_ex_plus_10_calendar_days`. In the payout journal the date basis is recorded as `actual` or `proxy_ex_plus_<k>_calendar_days` for the scenario's actual k. In the N2 window there is one such row: BIL 2008-03-03. The common calendar consists of the sessions where all ten tickers have bars, starting 2007-05-30. A session for which at least one ticker has no row is not in the common calendar; the current vintage has no such sessions (4869/4869).

## 3. Modules

- `src/alpha_lab/market.py` - loading and validation of the vintage, the common calendar, and per-ticker tables of open/close/dividend/split_ratio/pay_session. `history(t)` returns data only for sessions <= t.
- `src/alpha_lab/ledger.py` - the account state (`Account`: cash, positions, receivables, pending orders) and pure event functions: split, receivable accrual, payout crediting, sales, purchases, valuation at Close. No input or output.
- `src/alpha_lab/engine.py` - the day loop, order calculation on decision dates, scenarios, the journal, invariant checks, result writing and run registration.
- Weight provider: a function `provider(t, history) -> dict[str, float]` over all ten tickers (including BIL). Weights >= 0 and sum <= 1 + 1e-12, otherwise an error. The remainder up to 1 stays in USD. N2 has only test providers; the section 5 algorithm will appear in N3 through the same interface.

## 4. Account and parameters

Initial state: 100000 USD, no positions. Run parameters: start_session (the first decision date), end_session, decision_sessions (by default the last session of each month in the common calendar between start and end), cost c in {0, 0.001, 0.002, 0.005} (base 0.001), lag in {1, 2} sessions (base 1), reserve r in {0, 0.01, 0.02} (base 0.01), proxy_pay_days in {0, 10, 30} (base 10).

Period guard: end_session no later than 2022-12-30 (the last session of 2022); the period from 2023-01-01 on is closed until N6 (RESEARCH_PROTOCOL.md, lines 137 and 143). The engine rejects such a run; lifting the prohibition requires a separate decision.

## 5. Order of events in session s

At the open of s, strictly in this order:

1. Split: for a ticker with split_ratio != 1, the position quantity and the quantity of a pending order are multiplied by the ratio. A fractional result is not rounded (RESEARCH_PROTOCOL.md, line 120). Cash does not change.
2. Receivable accrual: for a ticker with dividend > 0 on s, the entitled quantity is the quantity after step 1, that is, the position at the previous session's close in new units. Amount = quantity × dividend; the payment session = the row's `payable_date`, and for proxy rows (section 2) under the scenario proxy_pay_days = k, the first session of the common calendar no earlier than ex-date + k calendar days (for k = 10 it equals `payable_date`). `actual` rows are not changed by the scenario. A zero quantity creates no accrual.
3. Crediting: a receivable whose payment session is s becomes cash, including one accrued in step 2.
4. Sales of pending orders with execution in s (section 6).
5. Purchases of pending orders with execution in s.

At the close of s: NAV = cash + Σ qty × close + the sum of unpaid receivables. If s is a decision date, orders are created after valuation.

Cash credited in steps 3-4 is available for purchases in the same session. A purchase at the ex-date open does not earn the payout entitlement, and a sale at the ex-date open retains it: accrual comes before trades.

## 6. Orders and execution

Decision in session t (the close, 18:00 America/New_York): from the weights w_i supplied by the provider and NAV_t, the target quantity is Q_i = floor((1 - r) × w_i × NAV_t / close_i,t), an integer, including BIL. The order is q_i = Q_i - h_i,t, where h_i,t is the position at the close of t; q_i may be fractional if the position contains a fractional residual after a split. q_i = 0 creates no order. There is no minimum trade size.

Execution is in session e = t + lag sessions of the common calendar. An order lives for one open. Between t and e the order quantity changes only through a split (step 1). A new decision before the previous one has executed is not allowed (an error).

A valid Open is a finite number > 0. Without a valid Open, the order for that ticker is cancelled with reason `no_valid_open`.

Sales (q_i < 0): min(|q_i|, position) is sold at Open; proceeds qty × open × (1 - c) arrive immediately. An excess over the position is cancelled with reason `exceeds_position` (a defensive branch that does not arise when the calculation is correct).

Purchases (q_i > 0): the required amount is R = Σ q_i × open_i × (1 + c). fill = min(1, cash / R); if R = 0, fill = 1. floor(fill × q_i) shares of each ticker are bought; cash decreases by qty × open × (1 + c). The remainder is not redistributed; the unfilled part is cancelled with reason `insufficient_cash`. After the purchases, cash >= -1e-8, otherwise the run fails with an error.

Costs: c × |qty| × open on each side; corporate events are free. Cash and quantities are stored as float64 without rounding to cents.

## 7. Result journal

The run is registered through `provenance.Run` (purpose `N2 execution run`, `started` and `completed`/`failed`). The result is frozen through `provenance.freeze` in `data/runs/<run_id>/` (`data/` is excluded from Git: derived Yahoo data):

- `config.json` - parameters, provider (name and version), path and SHA-256 of the vintage manifest.
- `decisions.csv` - decision_session, execution_session, nav, buy_fill, turnover (Σ |executed notional| / decision nav), costs_usd.
- `orders.csv` - decision_session, execution_session, ticker, weight, close, target_qty, held_qty, order_qty (after the split, at the moment of execution), filled_qty, status (filled / partial / cancelled), cancel_reason.
- `trades.csv` - session, ticker, side, qty, price, notional, cost, cash_after.
- `payouts.csv` - ticker, ex_session, pay_session, pay_basis, qty, amount_per_share, amount, status (paid / receivable).
- `daily.csv` - session, cash, receivables, positions_value, nav, the quantity of each ticker.
- `invariants.json` - the results of the section 8 checks.

## 8. Run invariants

Checked on every run and written to invariants.json; a violation makes the run `failed`:

- cash >= -1e-8 in all sessions;
- NAV = cash + Σ qty × close + receivables (absolute discrepancy <= 1e-6);
- the change in cash over a session = payouts + sale proceeds - purchase cost (<= 1e-6);
- a split changes only the quantity: cash and receivables in step 1 do not change, and the quantity is multiplied by exactly the ratio;
- Σ accrued receivables = Σ paid + remaining receivables;
- every trade is executed in session decision + lag at the Open of that session; the order size was computed from the close of the decision session;
- costs = c × Σ |notional|.

## 9. Manual reconciliations (protocol section 8)

A synthetic market of 2-3 tickers on the real XNYS calendar, with numbers calculated by hand and recorded in docs/n2/manual_reconciliation.md; each case is a test with exact comparison (tolerance 1e-9):

1. Before and after the open: sizing at the decision close, execution at the next session's Open; changing rows after t does not change the orders.
2. A 1:2 split (like BIL 2017) and a 3:1 split (like EEM 2008) with a position and a pending order; the fractional residual and its sale.
3. Ex/pay: a purchase at the ex-date open without entitlement, a sale at the ex-date open with entitlement; a receivable in NAV before payment; crediting and purchase in the same session; scenario proxy +0.
4. Gap: Open above the decision close, fill < 1, cancellation of the remainder with a reason, cash not negative.
5. Replacing ETF A with B: the sale funds the purchase at the same open, costs on both sides.
6. Delay lag = 2 and cancellation of an order without a valid Open.

In addition: the period guard (end_session after 2022-12-30 is rejected), recording `failed` in the journal, and determinism (two runs produce byte-identical files).

## 10. Run checking the invariants on real data

Provider `invariant_rotation` (a test provider, not a strategy): each of the ten tickers is always in the portfolio and the weight varies with the month number, w_i = (1 + (m + i) mod 3) / Σ, where i is the ticker's index in alphabetical order. This produces trades every month, holds EEM through the split of 2008-07-24 and BIL through the split of 2017-11-30, and passes through all payouts. Window: the first decision date is 2007-05-31 (the last session of May 2007 in the common calendar, which begins 2007-05-30), the end is 2022-12-30, base parameters. The provider does not use history, so the protocol's warmup period (253 closes) does not apply to this run; the run is not an evaluation and does not set the start of an evaluation window. The window covers the EEM split of 2008-07-24, the BIL split of 2017-11-30 and the BIL proxy payout of 2008-03-03; the run checks that all three events passed through the engine (a record in invariants.json). The D017 limitation (completeness of DBC history before 2007-12-17) is disclosed in the report. Only the invariant results, the number of decisions, trades, cancellations by reason, and the check of the two splits are published; NAV and returns are not published as results.

## 11. Documents

- EXECUTION_MODEL.md (repository root) - the normative description of sections 4-8 with references to the protocol.
- docs/n2/manual_reconciliation.md - six cases with manual calculations.
- DECISIONS.md, D021 - interpretations absent from the protocol: the order of steps 1-5, fractional rescaling of an order at a split, fixing the quantity at lag = 2 and fill from actual cash, the absence of a trade threshold, the proxy scenario as a recomputation of proxy rows only without a new vintage, float64 without cents, the period guard.
- docs/n2/N2_REPORT.md, STATUS.md, README.md (commands after verification).

## 12. N2 readiness check

All tests pass, including the six manual reconciliations; the section 10 run is `completed` in the journal on a clean tree; two runs produce identical file SHA-256 values; the branch code review has no Critical/Important findings; D021 is recorded. After that, N3 connects the section 5 weight algorithm as a provider.
