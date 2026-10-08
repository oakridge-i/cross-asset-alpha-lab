# N2 account and execution model

This document describes the mechanics implemented in `src/alpha_lab/market.py`, `ledger.py` and `engine.py`, the N3 additions in `features.py`, `portfolio.py`, `benchmarks.py`, `metrics.py`, `report.py` and `__main__.py`, and the N4 modules `hypotheses.py` and `hypothesis_report.py` (with further additions in `features.py`, `portfolio.py`, `engine.py`, `report.py` and `__main__.py`). It rests on [RESEARCH_PROTOCOL.md](RESEARCH_PROTOCOL.md), section 3 (portfolio treatment of splits and distributions, lines 40-44), section 4 (decision calendar, gaps and stale Open, lines 48-54) and section 8 (execution, lines 118-126). Below, "line N" means line N of RESEARCH_PROTOCOL.md in the English edition; line numbers are the same as in the original protocol. Further sources are the [N2 design specification](docs/superpowers/specs/2026-10-07-n2-execution-design.md), the [N3 design specification](docs/superpowers/specs/2026-10-07-n3-benchmarks-design.md), the [N4 design specification](docs/superpowers/specs/2026-10-08-n4-hypotheses-design.md) and decisions D020, D021, D022 and D023 in [DECISIONS.md](DECISIONS.md). The calculations against which the tests check the engine are in [docs/n2/manual_reconciliation.md](docs/n2/manual_reconciliation.md).

Status as of 8 October 2026: the N2 modules are written and tested on synthetic markets. The registered run on the real vintage and its repeat were executed, and all seven invariants passed; the results and the receivable check are in [docs/n2/N2_REPORT.md](docs/n2/N2_REPORT.md). These results concern account mechanics and make no claim about strategy behavior. Target-weight calculation, metrics, B0-B3, REF_SPY and return tables belong to N3: the registered benchmark runs, their repeats and the report were executed on 7 October 2026, and the results are published in [docs/n3/N3_REPORT.md](docs/n3/N3_REPORT.md). The N4 providers for H1/H2 and the N4 report are implemented and tested on synthetic markets, and their target weights were also checked against an independent recomputation on the real vintage; the six registered runs of H1/H2, their repeats and the N4 report were executed on 8 October 2026 on the branch `claude/n4-hypotheses`, and the six configurations have the status `computed_not_evaluated`; the run ids and the permitted diagnostics are in [docs/n4/N4_REPORT.md](docs/n4/N4_REPORT.md), and no H1/H2 return or risk result is computed or published before N5. The weight construction and metric definitions are recorded in D022 and the N3 specification; this document describes the account, the registry, the run output and the exit codes.

Places where the protocol is silent and the model makes a choice are marked "Interpretation" with the number of the D021 item that records the reason, alternative and consequence. The N3 interpretations are recorded in D022. Items by section: 13 in section 1 (D022 items 2 and 3 amend it); 7, 9, 12 and 14 in section 2 (D022 items 4 and 5 amend 14); 1, 2 and 5 in section 3; 3, 4, 6, 8 and 10 in section 4; 11, 15 and 16 in section 5 (D022 items 1, 15 and 16 amend or extend them); 17 in section 6. The N4 interpretations are recorded in D023: items 3, 4 and 5 in section 8, with item 6 for the failure messages and item 7 for the report checks.

## 1. Input data

`market.load_market(root, derived, expected_sha256)` accepts only the vintage `data/derived/20261006T172442-80ef993493` (D020). It calls `provenance.verify`, compares the SHA-256 of `manifest.json` with `VINTAGE_MANIFEST_SHA256` (`f89346107cf7da6ca052693d188b8a576a08d42024c86865b0a42a63b1d294f2`) and reads `normalized/<TICKER>.csv` for every ticker in the manifest. Any other hash raises `ValueError`. The `expected_sha256` parameter exists for tests on synthetic vintages; for project data, a different value requires a new decision.

The columns read are `session`, `open`, `close`, `dividend`, `split_ratio`, `payable_date` and `payable_basis`. Open, close and dividend are in as-traded units ([DATA_CONTRACT.md](DATA_CONTRACT.md)); dividend includes capital gains; `split_ratio` is new shares divided by old shares on the split date and 1 on other days. `payable_date` is set on the ex-date row where dividend > 0 and denotes the session in which cash is credited. Adj Close is not passed to the engine: a dividend reaches NAV only through the receivable and then cash (line 44).

The common calendar consists of the sessions on which all ten tickers have bars, starting 2007-05-30 (`COMMON_START`). A session where any ticker has no row is not in the calendar. In the current vintage this is 4,869 sessions from 2007-05-30 to 2026-10-05, which is every expected XNYS session (N1 QA: 4,869 of 4,869). Sessions must not repeat in a ticker's file. On calendar rows, `market.market_from_frames` requires: close is finite and greater than 0; open is finite and greater than 0, or absent; dividend is finite and not less than 0; split_ratio is finite and greater than 0. Error messages name the ticker and, for column values and payouts, also the session. A missing Open does not remove the session from the calendar: an order for that session is cancelled (section 4).

Payable contract. On a row with dividend > 0, `payable_basis` is `actual` or `proxy_ex_plus_10_calendar_days` (`PROXY_BASIS`). An empty or other basis, an empty `payable_date`, a date that is not ISO-formatted, and a date earlier than the ex-date raise `ValueError`. For `proxy_ex_plus_10_calendar_days` rows the loader additionally requires `payable_date` to equal `market.proxy_pay_session(ex_session, 10)`, the first XNYS session no earlier than ex-date + 10 calendar days (line 42). Accepted rows are stored in `Market.payable`, keyed by (ticker, ex-date), with (payment session, basis) as the value. The vintage contains one proxy row: BIL, ex-date 2008-03-03, `payable_date` 2008-03-13.

The contract and the numeric checks apply only to rows of the common calendar, that is, from 2007-05-30. Earlier rows in the files for SPY, EFA and other tickers are not used by the engine and are not validated by the loader. Interpretation (D021, item 13).

Events outside the calendar. A row of a ticker file whose session is not in the common calendar, lies between 2007-05-30 and the last common session, and has a finite dividend > 0 or a finite split_ratio other than 1 raises `ValueError` naming the ticker and the session: the account would never apply it. An accepted payout whose payment session is not later than the last common session and is not a common session is rejected too. Rows before 2007-05-30 remain unchecked. A payment session later than the last common session is allowed; such a payout stays `receivable`. Interpretation (D022, item 2).

`Market.history(t)` returns the market up to and including session t. `Market.payable` rows with an ex-date after t are removed; the remaining rows keep their `pay_session`, including one later than t. Signals must not use such a date (line 42); the engine does not enforce this. The weight provider receives only this object.

## 2. Run parameters and period guard

Initial state (`ledger.Account.new`): 100000.0 USD, zero positions in every ticker, no receivables or orders (line 120). The parameters are set by `engine.RunConfig(start_session, end_session, decision_sessions=None, scenario=Scenario(), initial_cash=100000.0)` and `engine.Scenario(cost, lag, reserve, proxy_pay_days)`.

| Parameter | Permitted values | Main scenario |
|---|---|---|
| start_session | a session of the common calendar, the first decision date | set by the run |
| end_session | a session of the common calendar no later than 2022-12-30 | set by the run |
| decision_sessions | a strictly increasing list of sessions, or the default rule (below) | default rule |
| cost, c | 0, 0.001, 0.002, 0.005 (0, 10, 20 and 50 bps per side) | 0.001 |
| lag | 1, 2 sessions: next open or one extra session (line 173) | 1 |
| reserve, r | 0, 0.01, 0.02 | 0.01 |
| proxy_pay_days, k | 0, 10, 30 calendar days | 10 |
| initial_cash | a finite real number greater than 0 | 100000.0 |

`Scenario` rejects a value outside the grid (`ValueError`) and accepts any combination of grid values; the order of "one change at a time" scenarios is set by the protocol (lines 173-174), not by the engine. `RunConfig` rejects an `initial_cash` that is not a finite real number greater than 0 (`ValueError`) when the configuration is created. The rejection precedes the Run and is not journaled, like a Scenario value outside the grid, because `provenance.canonical_bytes` cannot encode NaN or infinity. A value that differs from the protocol value of 100000.0 is otherwise accepted, but the protocol does not provide for it, and the command line does not expose the parameter. Interpretation (D022, item 5).

Default decision dates are determined by `engine.month_end_sessions(market, start, end, lag)`: the last XNYS session of each calendar month. Months are taken whole, so an incomplete month at the end of the window does not become a decision date. A date is kept if it lies in [start, end], belongs to the common calendar, and its execution session (index + lag) exists and is no later than end. For the window from 2007-05-31 to 2022-12-30 the last decision falls on 2022-11-30: a decision on 2022-12-30 would execute in 2023. Interpretation (D021, item 9).

Period guard (lines 137 and 143: 2023-2025 closed until N6). `engine.validate` rejects a run if end_session is later than `LAST_OPEN_SESSION` = 2022-12-30 (the last session of 2022); this check runs first. A run is also rejected when the execution session of any decision is later than end_session. The other `validate` rejections: start_session or end_session is not a market session; start_session is later than end_session; a decision is not a market session, lies outside [start_session, end_session], or breaks the strictly increasing order of the list; a decision precedes the execution of the previous order (the decision index is less than the previous decision index plus lag), and this check fires even when the previous decision created no orders. Only a separate decision can lift the guard. The loader reads the vintage files in full, including sessions after 2022-12-30, so the guard restricts the run, not access to the data. Interpretation (D021, items 7 and 14).

A weight provider has the form `provider(t, history) -> dict[str, float]`, where history = `Market.history(t)`. The dictionary is accepted if its keys equal the market tickers (all ten, including BIL), the values are finite real numbers (`numbers.Real`, not `bool` or `np.bool_`) not less than 0, and `math.fsum` of the values does not exceed 1 + 1e-12 (`WEIGHT_SUM_TOLERANCE`). The remainder up to 1 stays in USD. Any violation raises `ValueError`. `np.int64`, `np.float32` and `np.float64` values are accepted; a `np.float32` value is widened to float64 with its representation error, so such weights may exceed the 1 + 1e-12 bound. Interpretation (D021, item 14, amended by D022, item 4).

`engine.PROVIDERS` maps a name to `Provider(function, version, schedule, kind, parameters)`. `parameters` is empty except for the kind `hypothesis` (section 8). `schedule` is `monthly` (the default decision rule above) or `first_only` (the single decision `start_session`, set by `run_simulation` before the Run is opened so that it appears in the journaled configuration). `kind` is `test`, `benchmark` or `hypothesis`. The six providers of the kinds `test` and `benchmark` are listed below, all at version 1; the six `hypothesis` providers of N4 are described in section 8.

| Name | schedule | kind |
|---|---|---|
| invariant_rotation | monthly | test |
| B0 | monthly | benchmark |
| B1 | monthly | benchmark |
| B2 | monthly | benchmark |
| B3 | monthly | benchmark |
| REF_SPY | first_only | benchmark |

The benchmark providers apply the warm-up of 253 closes to every benchmark and return weights over all ten tickers; their weights are defined in the N3 specification (sections 3-5) and the interpretations in D022 (items 6-9). B0 holds BIL; B1 holds equal q over the nine risky ETFs and B2 inverse volatility, both under the common caps and volatility target; B3 selects tickers by 252-session trend against BIL, then applies the same inverse-volatility weights; REF_SPY holds SPY once. Weights drift between decisions, and REF_SPY keeps distributions as USD cash.

`invariant_rotation` is a test function, not a strategy: each of the ten tickers is always held, w_i = (1 + (m + i) mod 3) / Σ, where m = 12 × year + month of the decision date and i is the ticker's index in ASCII order, counted from zero. The provider uses only the date and the ticker list. With one-based numbering the rotation would shift by one step; using the month number within the year instead of m gives the same weights, because 12 is divisible by 3. Interpretation (D021, item 12).

## 3. Order of events in a session

At the open of session s, `engine.simulate` performs these steps in order.

1. Split (`ledger.apply_splits`). For a ticker with split_ratio ≠ 1, the position quantity and the quantity of any pending order are multiplied by the ratio. Cash and receivables are unchanged.
2. Accrual (`ledger.accrue_dividends`). For a ticker with dividend > 0, the entitled quantity is the quantity after step 1, that is, the position at the previous session's close in new units. Receivable = quantity × dividend; the payment session is determined by the rule below. A zero position creates no receivable.
3. Crediting (`ledger.credit_payouts`). A receivable whose payment session is s becomes cash, including one accrued in step 2.
4. Sales of pending orders with execution in s (`ledger.execute_orders`).
5. Purchases of pending orders with execution in s (the same function).

At the close of s, `ledger.nav` computes NAV = cash + Σ qty × close + unpaid receivables, and a row for the session is written to `daily.csv`. If s is a decision date, the provider receives `Market.history(s)` and `ledger.size_orders` creates orders from the NAV at this close (section 4).

The order follows lines 42 and 122 and is extended where they are silent. Accrual precedes trades: a purchase at the ex-date open does not earn the entitlement, while a sale at the ex-date open retains it. Accrual precedes crediting: a payout whose payment session equals the ex-date (scenario proxy +0) is credited at the open of the same session. Payouts credited in step 3 and sale proceeds from step 4 are available for the purchases in step 5 (line 122). Interpretation (D021, item 1).

An order is rescaled at a split as quantity × ratio without rounding again to an integer; the order's target_qty and held_qty remain in decision-time units. A fractional residual of a position is kept until sale (line 120). Example from the manual reconciliation (case 2, ratio 0.5): a position of 1087 becomes 543.5, an order of -544 becomes -272, and the residual 271.5 is sold by the next order. Interpretation (D021, item 2).

The payment session is determined by `engine.pay_map`. For `actual` rows it is the vintage `payable_date` in every scenario. For `proxy_ex_plus_10_calendar_days` rows it is recomputed for the scenario proxy_pay_days = k: the first XNYS session no earlier than ex-date + k calendar days (`market.proxy_pay_session`); for k = 10 the result equals `payable_date`. The recomputation happens at run time; it creates no new vintage. The payout basis is written to `payouts.csv` as `actual` or `proxy_ex_plus_<k>_calendar_days` for the actual k. The vintage has one proxy row (BIL, 2008-03-03), so a k scenario affects at most one payout. Interpretation (D021, item 5).

A receivable due after end_session stays in NAV with status `receivable`. There is no forced crediting or liquidation on the last date (line 126).

## 4. Orders, execution, costs

Sizing. At the close of decision date t, for each ticker in ASCII order, including BIL, `ledger.size_orders` computes the target quantity Q = floor((1 - r) × w × NAV / close) (line 120, where r = 0.01). In code this is `math.floor((1 - reserve) * weight * nav / close)` with that order of operations; NAV is taken at the close of t, including unpaid receivables, and close is the close of t. The order is q = Q - h, where h is the position at the close of t; h is fractional if a fractional residual remained after a split. A zero order is not created. There is no minimum trade size or dead band: any nonzero difference creates an order. Interpretation (D021, item 4). Because NAV includes a receivable that has not yet become cash, the total of purchases may exceed cash at execution; the fill coefficient then reduces the purchases. `size_orders` rejects a new decision while orders are pending.

Execution. The execution session e is the common-calendar session with index decision index + lag. An order lives for one open; between t and e its quantity changes only through a split. With lag = 2 the quantity is fixed at the close of t and is not recomputed at the close of t + 1, and the fill coefficient is computed from cash at the open of e, after the credits and sales of that session, rather than from cash at the decision date. Interpretation (D021, item 3). A valid Open is a finite number greater than 0; without one, the order is cancelled before R is computed, with reason `no_valid_open` (line 54).

Sales (q < 0, by ticker in ASCII order). min(|q|, position) is sold at Open, and the proceeds qty × open × (1 - c) arrive immediately. An order exceeding the position has its remainder cancelled with reason `exceeds_position`; this is a defensive branch that does not fire when sizing is correct. Short positions and leverage are impossible. There are no trades between decision dates, and weights drift (line 73).

Purchases (q > 0). R = Σ q × open × (1 + c) over purchases with a valid Open, where q is taken in full, including a fractional part. fill = min(1, cash / R), where cash is the cash after the session's credits and sales (a negative value counts as zero); if R = 0, fill = 1. Each ticker buys floor(fill × q) shares, and cash decreases by qty × open × (1 + c). The unfilled remainder is not redistributed among tickers and is cancelled after one open (line 122). `ledger.execute_orders` returns the pair (trades, buy_fill); if the session has no purchases with a valid Open, buy_fill = 1.0. Interpretation (D021, item 8).

Cancellation reason for the remainder of a purchase: `insufficient_cash` if fewer than floor(q) shares were bought; otherwise `fractional_quantity`. The second case arises when an order is fractional after a split and its whole part was bought: such an order gets status `partial` even when fill = 1, and the position stays below target by the fractional part, which is less than one share. An order of less than one share is cancelled (`cancelled`) with the same reason. Because R is computed from the full fractional q, when cash lies between the actual expenditure and R the value of fill falls below 1, and a purchase of another ticker may shrink by one share. This is as written in the specification (section 6); the effect was not measured on real data. Interpretation (D021, item 10).

| Status | Condition | cancel_reason |
|---|---|---|
| filled | filled_qty equals abs(order_qty) | empty |
| partial | 0 < filled_qty < abs(order_qty) | `insufficient_cash`, `fractional_quantity` or `exceeds_position` |
| cancelled | filled_qty = 0 | `no_valid_open`, `insufficient_cash`, `fractional_quantity` or `exceeds_position` |

Costs: c × abs(qty) × open on each side, including BIL and the initial entry; the execution price is not worsened in addition. Replacing ETF A with B has two sides, and cost is charged on both. Corporate actions are free. Slippage and spread are included in c and are not measured (line 124).

Cash and quantities are stored as float64 without rounding to cents. After purchases, cash must not be below -1e-8 (`CASH_TOLERANCE`); otherwise `ValueError` is raised and the run ends as `failed`. Interpretation (D021, item 6).

## 5. Run output

`engine.run_simulation(root, derived, provider_name, config, parent, expected_sha256)` opens a `provenance.Run` with purpose `N2 execution run` for a `test` provider and `N3 benchmark run` for a `benchmark` provider (with `candidate_ids` = [provider name] in the `started` and the terminal record; test providers have an empty list), checks that the vintage lies inside the project, loads the market, runs `engine.simulate`, and only after a successful calculation freezes the result (`provenance.freeze`) in `data/runs/<run_id>/` (`data/` is excluded from Git). The command line is `python -m alpha_lab simulate DERIVED --provider NAME --start DATE --end DATE` with optional `--cost`, `--lag`, `--reserve`, `--proxy-days`, `--expected-sha256`, `--root`, `--parent`; decision dates always follow the default rule. The command prints the run directory relative to the project (`data/runs/<run_id>`, with forward slashes) and exits with code 0 when the run is `completed` and with code 3 when it is `invariants_failed` (see the end of this section); `main()` replaces characters in the output that the console cannot encode, so a non-ASCII project path does not turn a completed run into an error. The command is tested on synthetic vintages and was applied to the real vintage in the registered runs ([docs/n2/N2_REPORT.md](docs/n2/N2_REPORT.md)); its invocation is given in [docs/REPRODUCIBILITY.md](docs/REPRODUCIBILITY.md).

| File | Contents |
|---|---|
| config.json | RunConfig parameters (start_session, end_session, decision_sessions, scenario, initial_cash), provider (name, version), vintage (path relative to the project root), manifest_sha256 |
| decisions.csv | decision_session, execution_session, nav, buy_fill, turnover, costs_usd |
| orders.csv | decision_session, execution_session, ticker, weight, close, target_qty, held_qty, order_qty, filled_qty, status, cancel_reason |
| trades.csv | session, ticker, side, qty, price, notional, cost, cash_after |
| payouts.csv | ticker, ex_session, pay_session, pay_basis, qty, amount_per_share, amount, status |
| daily.csv | session, cash, receivables, positions_value, nav, then qty_<TICKER> for each ticker in ASCII order |
| invariants.json | results of the section 6 checks |

A run of a `benchmark` provider freezes nine files: these seven and two more.

| File | Contents |
|---|---|
| weights.csv | one row per decision: decision_session, then w_<TICKER> for the ten tickers in ASCII order, then usd = 1 - fsum of the weights |
| metrics.json | canonical JSON, `schema_version` 1: the section 11 metrics of one portfolio for the periods `full`, `development`, `walk_forward`, three blocks and each calendar year 2009-2022, computed in memory from unrounded values |

The metric definitions and their interpretations are in the N3 specification (section 6) and D022 (items 10-14). Runs of `test` providers freeze seven files. Interpretation (D022, item 15).

decisions.csv. Every decision has a row, including those without orders. nav is NAV at the close of the decision date; turnover = Σ notional of the execution session's trades / nav, over both sides, without dividing by 2; costs_usd = Σ cost of those trades; buy_fill is described in section 4.

orders.csv. weight, close, target_qty and held_qty refer to the decision moment (quantities and close in pre-split units, if a split occurs). order_qty is the order quantity at the execution moment, after rescaling for a split, and signed (a minus sign means a sale); therefore, after a split, order_qty does not equal target_qty - held_qty. filled_qty is the executed quantity, unsigned. Interpretation (D021, item 16).

trades.csv. side is `sell` or `buy`; qty and price are positive; notional = qty × price; cost = c × notional; cash_after is cash after the trade.

payouts.csv. All accrued payouts. Status `paid` means credited within the window; `receivable` means the payout was not credited by the end of the window and remains in NAV. amount = qty × amount_per_share.

daily.csv. One row for each session from start_session to end_session, with closing values: cash, unpaid receivables, positions_value = Σ qty × close, nav.

CSV files are written with fixed columns, LF line endings and floating-point numbers in the `%.10g` format (10 significant digits). The files contain no run_id, time or absolute paths, so runs with identical inputs produce files with identical SHA-256. The format loses precision: a price or amount in the CSV is not bit-for-bit equal to the in-memory value, and identities recomputed from the CSV hold to about 1e-4 USD. The section 6 checks work on unrounded values. config.json and invariants.json are written as canonical JSON without loss of precision. Interpretation (D021, item 16).

The journal `experiments/EXPERIMENT_LOG.jsonl` receives a `started` record and then one of three: `completed` (all section 6 checks passed), `invariants_failed` (at least one failed; the result is frozen for inspection and the names of failed checks are recorded in quality_warnings) or `failed` (an exception: closed period, a different vintage, a vintage outside the project, an input-data error). The journaled configuration contains the run parameters, the provider, the vintage path and the expected hash. In a `completed` or `invariants_failed` record, output_paths points to the run directory and data_sha256 equals the SHA-256 of its `manifest.json`. The specification (section 8) calls an invariant violation a failed run; here a separate status is used, like `quality_failed` in audit. With `invariants_failed`, `simulate` prints the run directory and then exits with code 3; the code is derived from the `passed` field of invariants.json, the value that sets the journal status. `audit` likewise exits with code 3 on `quality_failed`, from `technical_pass` in quality.json. Exceptions keep Python's code 1 and argparse errors code 2. Interpretation (D021, item 11, amended by D022, item 1).

Rejections before a `Run` exists are not journaled: a Scenario value outside the grid (the error is raised when the Scenario is created), an `initial_cash` that is not a finite number greater than 0 (raised in `RunConfig`), an unknown provider name (`KeyError` from Python; the command line restricts the choice through argparse) and argument-parsing errors. Rejections inside a `Run` are journaled: closed period, a different or external vintage, input-data errors (including a payment session recomputed for k onto a session outside the calendar, D022 item 3), invariant violations. Interpretation (D021, item 15).

Report. `python -m alpha_lab report --runs DIR... --root PROJECT [--parent ATTEMPT]` is a Run with purpose `N3 benchmark report` and `candidate_ids` B0, B1, B2, B3, REF_SPY. It fails with `ValueError` unless five directories in `data/runs` hold the five benchmarks once each, each passes `provenance.verify`, has the nine files and `invariants.json` with `passed` true, has one `started` and one `completed` journal record on a clean tree that agree with the directory and `config.json`, and all five share the approved manifest hash, scenario, window, initial cash, current provider versions and metrics schema. Each `started` record also has the purpose `N3 benchmark run`, `candidate_ids` = [provider name] and an `environment_manifest_sha256` equal to that of the report run, and the `src` tree of its `git_sha` equals the `src` tree of the report run's `git_sha` (`report.src_tree`, `git rev-parse <sha>:src`). It writes `benchmarks.json` and `benchmarks.md` to `data/reports/<run_id>/`; neither contains a run id, timestamp or path, and the run ids and run manifest hashes are in the report manifest metadata. A repeated run or report is compared with the original by the manifest `files` dictionaries, not by manifest bytes. The `--expected-sha256` option exists for tests on synthetic vintages; a registered report journals the approved hash. Interpretation (D022, item 16).

## 6. Invariants

`engine.run_invariants` checks every run against the quantities recorded in the loop and writes seven checks to invariants.json. Each has the fields `passed` and `detail` (text with unrounded numbers). The overall flag `passed` is true when all seven pass.

| Name | Check | Tolerance |
|---|---|---|
| cash_non_negative | the minimum of cash over the `daily.csv` rows and over trade `cash_after` is not below -1e-8 | 1e-8 |
| nav_identity | row NAV equals cash + Σ qty × close + (accrued - paid) cumulatively; the maximum discrepancy over sessions | 1e-6 |
| cash_flow | the change in cash over a session equals credited payouts plus sale proceeds minus purchase spending; the maximum discrepancy over sessions | 1e-6 |
| split_quantity_only | in step 1, cash and receivables did not change, and the position quantity and the order quantity became equal to the previous quantity times the ratio | exact equality |
| receivable_conservation | accrued = paid + remaining receivable; the sum of `payouts.csv` rows with status `paid` equals the paid total | 1e-6 |
| execution_timing | for an order, the execution session is `lag` after the decision, close equals the decision-session close, and target_qty is recomputed from the decision NAV; a trade has an order for that session and ticker, and its price equals the session Open | exact equality |
| costs | Σ cost of trades and Σ costs_usd of decisions equal c × Σ notional | 1e-6 |

In addition to the checks, invariants.json records `split_events`, a list of [ticker, session] pairs for splits that affected a position or a pending order, and `proxy_payouts`, a list of [ticker, ex-date, payment session] triples for every accrued payout on a proxy row, as recomputed for the scenario. The specification (section 10) prescribes using them in the real-data run to check that the EEM split of 2008-07-24, the BIL split of 2017-11-30 and the BIL proxy payout of 2008-03-03 passed through the engine. The check names and the list formats are fixed in code; renaming changes invariants.json and the reports that refer to these keys. Interpretation (D021, item 17).

## 7. Tests and what is not established

Tests. `tests/test_market.py`: the payable contract, the calendar, `history`, the vintage hash; `test_real_vintage_loads` reads the real vintage and is skipped if it is absent from the working copy. `tests/test_ledger.py`: events and orders separately. `tests/test_engine.py`: manual reconciliations (cases 1, 2, 2b, 3, 3b, 4, 5, 6 and 6b from docs/n2/manual_reconciliation.md, compared with abs=1e-9), negative invariant tests, the period guard, input validation. `tests/test_engine_run.py`: the journal, files, determinism, the command line. The engine tests run on synthetic markets in `tmp_path` under the `no_network` fixture. The N3 tests are `tests/test_features.py`, `tests/test_portfolio.py`, `tests/test_benchmarks.py`, `tests/test_benchmark_runs.py`, `tests/test_metrics.py` and `tests/test_report.py`; they also use synthetic data in `tmp_path`.

Not established. The number of decisions, the number of cancellations by reason, and the invariant results on real data come from the registered runs and are given in docs/n2/N2_REPORT.md. The effect of the D021 interpretations on the result was not measured: that requires comparison with alternative rules, which do not exist. This applies to counting the fractional order in R (section 4), to the k scenario (at most one payout), and to the absence of a trade threshold. A receivable whose pay_session is not a common-calendar session within the run window will not be credited and remains in NAV; `receivable_conservation` does not distinguish it from a receivable due after end_session, so after a run it is checked separately that every `receivable` row in payouts.csv has pay_session later than end_session. For the registered runs the check was performed: the only such row (SPY, payment 2023-01-31) is later than the end of the window (docs/n2/N2_REPORT.md).

The model executes at Open as a modeled price: there is no guarantee of a historical opening auction (line 34), order-book depth and volume are not modeled, and source volume is unverified and unused. Sale proceeds and payouts are available immediately; this simplifies settlement and is not a model of a settlement account (line 122). Taxes, withholding and currency conversion are absent (line 44). The data limitations of D016-D019 remain: the data are not point-in-time, the seven corrections were accepted by the user's decision without independent confirmation, the basis for GLD's status is weaker than a direct document, and the completeness of DBC history before 2007-12-17 is not proven.

File identity between the two runs was checked in one environment on one machine; it was not checked on another platform or with other library versions. The same scenario given from Python with integers (`cost=0`) and from the command line with floating-point numbers (`--cost 0`) produces different config.json bytes (`0` and `0.0`) and a different config_sha256 in the journal.

## 8. Hypothesis providers (N4)

The six configurations of RESEARCH_PROTOCOL.md section 7 are registered in `engine.PROVIDERS` with the kind `hypothesis`, version 1 and schedule `monthly`. The functions are `hypotheses.h1(t, history, lookback, k)` and `hypotheses.h2(t, history, h)`, bound with `functools.partial`; the features are in `features.py` (`momentum`, `month_end_levels`, `monthly_excess`) and the sizing in `portfolio.py` (`inverse_vol`, `capped`, `risk_detail`, `common_risk`). The interpretations are recorded in D023 (items 3-5) and the specification is [docs/superpowers/specs/2026-10-08-n4-hypotheses-design.md](docs/superpowers/specs/2026-10-08-n4-hypotheses-design.md). Synthetic tests, real-vintage target-weight checks and registered H1/H2 runs have been completed. The registered runs and permitted diagnostics are recorded in the [N4 report](docs/n4/N4_REPORT.md); they establish neither that a configuration adds value nor that it should be rejected.

| Name | Function | `provider.parameters` |
|---|---|---|
| H1_252_3 | h1 | `{'lookback': 252, 'k': 3}` |
| H1_252_4 | h1 | `{'lookback': 252, 'k': 4}` |
| H1_126_3 | h1 | `{'lookback': 126, 'k': 3}` |
| H1_126_4 | h1 | `{'lookback': 126, 'k': 4}` |
| H2_4of6 | h2 | `{'h': 4, 'parent': 'H1_252_3'}` |
| H2_5of6 | h2 | `{'h': 5, 'parent': 'H1_252_3'}` |

The parameters are fixed in the registry and cannot be set from the command line. `Provider` carries them in the field `parameters`; `config_record` writes them into the `provider` object of the journaled configuration and of `config.json` for the kind `hypothesis` only, so the configurations of test and benchmark runs are unchanged.

Decision. A hypothesis provider returns `Decision(weights, signals)` instead of a dictionary. `weights` is the dictionary of the section 2 contract over the ten tickers. `signals` is a list of nine rows, one per risky ticker in ASCII order, produced by the same computation as the weights. `engine.provider_decision` accepts either return type and returns `(weights, signals)`, with an empty list for a dictionary; the weight checks of section 2 are unchanged and `Result` gains the list `signals`. A provider sees only `Market.history(t)`; the H1 features use closes through t, and H2 uses the month-end sessions through t, which must be the last XNYS session of their calendar month (D023, item 4).

Output. A run of a `hypothesis` provider records the purpose `N4 hypothesis run` and `candidate_ids` = [provider name] in the `started` and the terminal record, and freezes nine files: the seven files of section 5, `weights.csv` (as for benchmarks) and `signals.csv`. It freezes no `metrics.json`: `compute_metrics` is not called for this kind, and the return and risk metrics of H1/H2 are first computed in N5. `signals.csv` has one row per decision and risky ticker, ordered by `decision_session` and then ticker in ASCII order. The H1 columns are `decision_session`, `ticker`, `momentum`, `sigma`, `score`, `eligible`, `rank`, `selected`, `q`, `v`, `scale` and `weight`. `rank` is 1-based among eligible tickers and empty otherwise; `q` is 0 for a ticker that is not selected; `v` is the weight after the single-ETF and group caps; `scale` is the volatility-target factor a of line 70, equal on the rows of a decision; `weight` is the target weight. H2 rows repeat the parent's values in these columns except `weight`, and add `parent_weight`, `excess_1` to `excess_6` (oldest to newest), `positive_months` and `filter_pass`. Numbers use the `%.10g` format, booleans are written `True` and `False`, and line ends are LF (section 5).

Failure messages. Some engine error messages contain cash, weight sums or variances. For the kind `hypothesis`, `run_simulation` therefore re-raises any exception from loading, simulation, serialization of the result files or freezing of the run directory as `RuntimeError('<exception type> in <name> run; message withheld under the N4 viewing restriction')` with the original suppressed. The console and the `error` field of the journal then read `RuntimeError: ...` and carry no value; the cause is found by reproduction on synthetic data. The restriction on viewing the output of H1/H2 runs is recorded in D023, item 6.

Report. `python -m alpha_lab hypothesis-report --runs RUN_DIR... --root PROJECT [--parent ATTEMPT]` is a Run with purpose `N4 hypothesis report` and `candidate_ids` H1_252_3, H1_252_4, H1_126_3, H1_126_4, H2_4of6, H2_5of6. It checks the six runs against the registered window, scenario, parameters, decision sessions and the signal, sizing and H2-to-parent identities before it computes the diagnostics of D023 item 6, and writes `hypotheses.json` and `hypotheses.md` to `data/reports/<run_id>/` without a run id, timestamp or path. The checks are listed in D023, item 7. `report` for the benchmarks is unchanged.
