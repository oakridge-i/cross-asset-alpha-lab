# N2 Execution Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Account and execution engine that turns target weights at a decision close into orders executed at the next Open, with costs, splits, dividend receivables, cash, NAV, a frozen trade journal and hand-checked reconciliations.

**Architecture:** `market.py` loads the approved vintage into a common-calendar `Market`; `ledger.py` holds the `Account` state and pure event functions; `engine.py` runs the day loop, sizing, scenarios, invariants, output files and the journaled run. Target weights come from a provider callable; N2 ships only test providers.

**Tech Stack:** Python 3.14, pandas, numpy, exchange_calendars (already in requirements.lock), pytest.

**Spec:** `docs/superpowers/specs/2026-10-07-n2-execution-design.md` (read it before any task; section numbers below refer to it).

## Global Constraints

- Work in worktree `.worktrees/n1-data`, branch `claude/n2-execution`. Test command: `PYTHONPATH=src .venv/Scripts/python -m pytest -q -p no:cacheprovider --basetemp="$TEMP/n2"`.
- No new dependencies. No changes to `data/derived/`, `data/corrections/`, existing N1 modules' behavior, or `experiments/EXPERIMENT_LOG.jsonl` (only Task 6 appends to it through `Run`). Tests use `tmp_path` and the `no_network` fixture from `tests/conftest.py`.
- Code, comments, identifiers, commit messages in English, format `type: summary`; project docs in Russian. No `Co-Authored-By` trailer. Before each commit `git config user.email` must print `241006549+oakridge-i@users.noreply.github.com`.
- Tickers are processed in ASCII order. Dates are ISO strings `YYYY-MM-DD`.
- Sizing formula exactly `math.floor((1 - reserve) * weight * nav / close)` in this operation order.
- Cash tolerance `-1e-8` (below it: `ValueError`). Hand reconciliation asserts use `pytest.approx(value, abs=1e-9)`.
- Base scenario: cost `0.001`, lag `1`, reserve `0.01`, proxy_pay_days `10`; initial cash `100000.0`.
- Reserved guard: `end_session` must be `<= '2022-12-30'`; every execution session must be `<= end_session`.

## Review Focus

- Float floor at an exact-integer quotient (nav 100000, close 100, weight 1, reserve 0.01) must give the deterministic value 990, not 989 — test in Task 2.
- Provider output with a negative, NaN, missing or unknown ticker weight, or sum > 1 + 1e-12, must fail the run with `ValueError` — test in Task 3.
- A month-end decision whose execution session would fall after `end_session` (2022-12-30 → 2023-01-03 is reserved) must not be scheduled by default and must be rejected if passed explicitly — test in Task 3.
- Unsorted, duplicate, non-calendar decision sessions, or a start before the market's first session, must be rejected — test in Task 3.
- A provider must never see rows after the decision session, even through `Market` attributes such as pay maps — test in Task 1 (`history`) and Task 3 (mutation test).

---

### Task 1: Market loader and payable contract

**Files:**
- Create: `src/alpha_lab/market.py`
- Test: `tests/test_market.py`, helper `tests/n2_fixtures.py`

**Interfaces:**
- Produces:
  - Constants: `VINTAGE = 'data/derived/20261006T172442-80ef993493'`, `VINTAGE_MANIFEST_SHA256 = 'f89346107cf7da6ca052693d188b8a576a08d42024c86865b0a42a63b1d294f2'`, `COMMON_START = '2007-05-30'`, `PROXY_BASIS = 'proxy_ex_plus_10_calendar_days'`, `ACTUAL_BASIS = 'actual'`, `RESERVED_START = '2023-01-01'`, `LAST_OPEN_SESSION = '2022-12-30'`.
  - `@dataclass(frozen=True) class Market`: `tickers: tuple[str, ...]`, `sessions: tuple[str, ...]`, `open/close/dividend/split_ratio: pd.DataFrame` (index = sessions, columns = tickers, float), `payable: dict[tuple[str, str], tuple[str, str]]` mapping `(ticker, ex_session) -> (pay_session, basis)`, `vintage: str`, `manifest_sha256: str`. Methods: `index(session: str) -> int` (ValueError if absent), `history(t: str) -> Market` (sessions ≤ t; payable keys with ex_session ≤ t only).
  - `proxy_pay_session(ex_session: str, days: int) -> str`: first XNYS session on or after `ex_session + days` calendar days (use `normalize.calendar(...).date_to_session(..., direction='next')`; XNYS is used because pay dates may fall after the last bar; inside the data window it equals the common calendar).
  - `market_from_frames(frames: dict[str, pd.DataFrame], vintage: str = 'synthetic', manifest_sha256: str = '', start: str | None = None) -> Market`: frames indexed by session with columns `open, close, dividend, split_ratio, payable_date, payable_basis`; common calendar = intersection of sessions, from `start` (default first common session). Validates the payable contract on every row with `dividend > 0`: basis in {`actual`, `PROXY_BASIS`}, non-empty `payable_date >= ex_session`, and for `PROXY_BASIS` rows `payable_date == proxy_pay_session(ex, 10)`; any violation → `ValueError` naming ticker and date. `open` may be NaN (engine cancels); `close` must be finite > 0 on every common session.
  - `load_market(root: Path, derived: Path, expected_sha256: str | None = VINTAGE_MANIFEST_SHA256) -> Market`: `provenance.verify(derived)`; SHA-256 of `manifest.json` must equal `expected_sha256` when not None, else `ValueError('unexpected vintage ...')`; reads `normalized/<T>.csv` for every `<T>` in the manifest, `start=COMMON_START`.
  - `tests/n2_fixtures.py`: `SESSIONS = ['2017-11-27', '2017-11-28', '2017-11-29', '2017-11-30', '2017-12-01', '2017-12-04', '2017-12-05', '2017-12-06', '2017-12-07', '2017-12-08']`; `frame(close, open=None, dividend=None, split=None, payable=None) -> pd.DataFrame` (lists over SESSIONS; `payable` maps ex_session → (date, basis)); `write_vintage(root, frames) -> Path` freezing `data/derived/synthetic/normalized/<T>.csv` with the columns above via `provenance.freeze`.

- [ ] **Step 1: Write failing tests** in `tests/test_market.py`:
  - `test_common_calendar_is_intersection`: AAA on all SESSIONS, BBB missing `2017-11-29` → `market.sessions` lacks `2017-11-29`, length 9.
  - `test_payable_contract` parametrized over: basis `'proxy'` (unknown), empty basis with dividend 0.5, payable `2017-11-28` for ex `2017-11-30`, `PROXY_BASIS` with payable `2017-12-08` for ex `2017-11-30` (expected `2017-12-11`) → each `pytest.raises(ValueError)`; `PROXY_BASIS` with `2017-12-11` and `actual` with `2017-12-05` load fine and `market.payable[('AAA', '2017-11-30')] == ('2017-12-11', PROXY_BASIS)`.
  - `test_proxy_pay_session`: `proxy_pay_session('2017-11-30', 10) == '2017-12-11'`, `(..., 0) == '2017-11-30'`, `(..., 30) == '2018-01-02'`.
  - `test_history_excludes_future`: `m.history('2017-11-30')` has 4 sessions, last `2017-11-30`, and payable key for ex `2017-12-04` absent.
  - `test_load_market_checks_hash` (uses `write_vintage`): wrong `expected_sha256='0'*64` → ValueError; correct hash loads.
  - `test_real_vintage_loads` with `pytest.mark.skipif(not (ROOT / VINTAGE / 'manifest.json').exists(), ...)`: 10 tickers, `sessions[0] == '2007-05-30'`, `len(sessions) == 4869`, `market.payable[('BIL', '2008-03-03')][1] == PROXY_BASIS`, `split_ratio.loc['2008-07-24', 'EEM'] == 3.0`, `split_ratio.loc['2017-11-30', 'BIL'] == 0.5`.
- [ ] **Step 2: Run** `... pytest tests/test_market.py` → FAIL (`ModuleNotFoundError: alpha_lab.market`).
- [ ] **Step 3: Implement** `market.py` and `tests/n2_fixtures.py` per Interfaces.
- [ ] **Step 4: Run** `tests/test_market.py` → PASS; full suite → all pass.
- [ ] **Step 5: Commit** `feat: add N2 market loader with payable contract`.

### Task 2: Ledger state and event functions

**Files:**
- Create: `src/alpha_lab/ledger.py`
- Test: `tests/test_ledger.py`

**Interfaces:**
- Consumes: nothing from Task 1 except ticker/session strings.
- Produces:
  - `CASH_TOLERANCE = 1e-8`.
  - `@dataclass class Receivable`: `ticker, ex_session, pay_session, basis: str`, `qty, amount_per_share: float`, `status: str = 'receivable'`; property `amount = qty * amount_per_share`.
  - `@dataclass class Order`: `decision_session, execution_session, ticker: str`, `weight, close: float`, `target_qty: int`, `held_qty: float`, `qty: float` (signed, current units), `filled_qty: float = 0.0`, `status: str = 'pending'` (`filled` / `partial` / `cancelled`), `cancel_reason: str = ''` (`no_valid_open` / `insufficient_cash` / `exceeds_position`).
  - `@dataclass class Trade`: `session, ticker, side ('sell'|'buy'): str`, `qty, price, notional, cost, cash_after: float`.
  - `@dataclass class Account`: `cash: float`, `positions: dict[str, float]`, `receivables: list[Receivable]`, `pending: list[Order]`; `Account.new(tickers, cash=100000.0)`.
  - `apply_splits(account, ratios: dict[str, float]) -> list[str]`: multiply position and pending `qty` (and `held_qty`, `target_qty` stay as decided) by ratio ≠ 1; return tickers split with nonzero position or pending order.
  - `accrue_dividends(account, session, dividends: dict[str, float], pay: dict[str, tuple[str, str]]) -> list[Receivable]`: for each ticker with dividend > 0 and position > 0, append a Receivable with the position after splits.
  - `credit_payouts(account, session) -> list[Receivable]`: receivables with `pay_session == session` → cash, status `paid`, removed from `account.receivables`.
  - `size_orders(account, decision_session, execution_session, weights: dict[str, float], closes: dict[str, float], nav: float, reserve: float) -> list[Order]`: per spec §6; zero-qty orders not created; appended to `account.pending` and returned.
  - `execute_orders(account, session, opens: dict[str, float], cost: float) -> list[Trade]`: orders with `execution_session == session`; sells then buys exactly as spec §6; sets status/filled/cancel_reason; removes them from `pending`; raises `ValueError` if cash < `-CASH_TOLERANCE` after buys.
  - `nav(account, closes: dict[str, float]) -> float` and `receivables_total(account) -> float`.
- [ ] **Step 1: Write failing tests** in `tests/test_ledger.py`:
  - `test_split_converts_positions_and_pending`: positions `{'CCC': 100.0}`, one pending Order qty 10 → `apply_splits(acc, {'CCC': 3.0})` gives position 300.0, order qty 30.0, cash unchanged; ratio 0.5 on 1087 shares gives 543.5.
  - `test_size_orders_exact_integer_quotient`: nav 100000.0, close 100.0, weight 1.0, reserve 0.01 → `target_qty == 990`.
  - `test_sell_then_buy_with_fill_ratio`: cash 0, position AAA 10 @ open 100, pending sell AAA −10 and buy BBB +20 @ open 60, cost 0.001 → sell proceeds 999.0; R = 20·60·1.001 = 1201.2; fill = 999/1201.2; bought `floor(fill*20) == 16`; cash = 999 − 16·60·1.001 = 38.04; BBB order status `partial`, `cancel_reason == 'insufficient_cash'`.
  - `test_no_valid_open_cancels`: open `float('nan')` → order `cancelled`, `no_valid_open`, no trade.
  - `test_sell_exceeding_position_is_capped`: position 5, order −8 → trade qty 5, status `partial`, `exceeds_position`.
  - `test_dividend_right_and_credit`: position 0 with pending buy → no receivable; position 2020, dividend 1.0, pay `('2017-12-05', 'actual')` → receivable amount 2020.0; `credit_payouts` on `2017-12-05` adds 2020.0 to cash and empties receivables.
- [ ] **Step 2: Run** `tests/test_ledger.py` → FAIL (module missing).
- [ ] **Step 3: Implement** `ledger.py` per Interfaces.
- [ ] **Step 4: Run** → PASS; full suite → all pass.
- [ ] **Step 5: Commit** `feat: add N2 ledger state and event functions`.

### Task 3: Simulation loop, scenarios, invariants and hand reconciliations

**Files:**
- Create: `src/alpha_lab/engine.py`
- Test: `tests/test_engine.py`
- Create: `docs/n2/manual_reconciliation.md` (Russian; one subsection per case below with the arithmetic lines exactly as listed)

**Interfaces:**
- Consumes: `Market`, `market_from_frames`, `proxy_pay_session`, `LAST_OPEN_SESSION` (Task 1); everything in Task 2.
- Produces:
  - `@dataclass(frozen=True) class Scenario`: `cost=0.001, lag=1, reserve=0.01, proxy_pay_days=10`; validated: cost in {0, 0.001, 0.002, 0.005}, lag in {1, 2}, reserve in {0, 0.01, 0.02}, proxy_pay_days in {0, 10, 30}.
  - `@dataclass(frozen=True) class RunConfig`: `start_session: str, end_session: str, decision_sessions: tuple[str, ...] | None = None, scenario: Scenario = Scenario(), initial_cash: float = 100000.0`.
  - `month_end_sessions(market, start, end, lag) -> list[str]`: last session of each month in `[start, end]` whose execution session (index + lag) exists and is ≤ end.
  - `@dataclass class Result`: `decisions: list[dict]`, `orders: list[Order]`, `trades: list[Trade]`, `payouts: list[Receivable]`, `daily: list[dict]`, `invariants: dict`.
  - `simulate(market, provider, config) -> Result`. Provider signature `provider(t: str, history: Market) -> dict[str, float]`; called with `market.history(t)`. Day loop over sessions from `start_session` to `end_session`: steps 1–5 of spec §5 (pay map for proxy rows recomputed with `proxy_pay_session(ex, scenario.proxy_pay_days)`, basis written as `f'proxy_ex_plus_{k}_calendar_days'`), close valuation into `daily`, then sizing on decision sessions. `decisions` rows: `decision_session, execution_session, nav, buy_fill, turnover, costs_usd` (filled after execution). `invariants`: dict of the seven checks in spec §8 plus `split_events: list[[ticker, session]]` and `proxy_payouts: list[[ticker, ex_session, pay_session]]`, each check `{'passed': bool, 'detail': str}`; `invariants['passed']` = all checks passed.
  - Validation errors (`ValueError`): end after `LAST_OPEN_SESSION`; start/end/decision not in `market.sessions`; decisions unsorted or duplicated; execution after end; provider weights invalid (Review Focus line 2); decision while an earlier order is pending.
- [ ] **Step 1: Write failing tests** in `tests/test_engine.py` using `tests/n2_fixtures.py` (all prices constant unless stated, `payable` actual unless stated, explicit `decision_sessions`, base scenario unless stated):
  - `test_case1_before_after_open`: AAA close 100, open on 11-29 = 100.5; decision 11-28 weight 1 → order target 990; trade 11-29 qty 990 @100.5, cost 99.495; cash 405.505; NAV 11-29 = 99405.505. Mutating close/open of 11-30..12-08 leaves `orders` target_qty/close identical.
  - `test_case2_reverse_split_with_pending_order`: BBB close/open 91 through 12-04, ratio 0.5 on 12-05, close/open 182 from 12-05; decisions 11-28 (w 1), 12-04 (w 0.5), 12-06 (w 0). Expect buy 1087 @91 on 11-29, cash 984.083; decision 12-04 NAV 99901.083, target 543, order −544 → after split −272, position 543.5; sell 272 @182 proceeds 49454.496, cash 50438.579, position 271.5; decision 12-06 order −271.5, sell 271.5 @182 on 12-07 proceeds 49363.587, cash 99802.166, position 0; `split_events == [['BBB', '2017-12-05']]`.
  - `test_case3_ex_and_pay`: DDD and EEE close/open 49, both dividend 1.0 ex 11-30 paid 12-05 actual. Decisions 11-28 {DDD 1}, 11-29 {DDD 0, EEE 1}, 12-04 {EEE 1}. Expect: 11-29 buy DDD 2020, cash 921.02; 11-30 receivable DDD 2020.0 (none for EEE), sell DDD 2020 proceeds 98881.02, buy EEE 2018 (98980.882), cash 821.158, NAV 101723.158; 12-04 order EEE +37; 12-05 credit 2020 then buy 37 (1814.813), cash 1026.345, NAV 101721.345.
  - `test_case3b_proxy_zero_days`: FFF close/open 41, dividend 0.25 ex 11-30, basis `PROXY_BASIS` paid `2017-12-11`; decision 11-28 {FFF 1} → 2414 shares; base: payout status `receivable` pay `2017-12-11` amount 603.5; `Scenario(proxy_pay_days=0)`: paid on `2017-11-30`, basis `proxy_ex_plus_0_calendar_days`, `proxy_payouts == [['FFF', '2017-11-30', '2017-11-30']]`.
  - `test_case4_gap_fill_ratio`: GGG close 97, open on 11-29 = 99; decision 11-28 {GGG 1} → target 1020, fill = 100000/101080.98, bought 1009, cash 9.109, status `partial`, `insufficient_cash`.
  - `test_case5_switch`: HHH close/open 80, III 40; decisions 11-28 {HHH 1}, 11-29 {HHH 0, III 1}. Expect 1237 HHH, cash 941.04; NAV 99901.04; 11-30 sell 1237 (proceeds 98861.04), buy 2472 III (98978.88), cash 823.20; decision row 11-29: `costs_usd == 197.84`, `turnover == pytest.approx(197840 / 99901.04)`.
  - `test_case6_lag2`: JJJ close 97, open 50 on 11-29, open 98 on 11-30; `Scenario(lag=2)`, decision 11-28 → no trade on 11-29; 11-30 buy 1019, cash 38.138.
  - `test_review_focus_validation`: parametrized invalid weights (−0.1, NaN, missing ticker, unknown ticker `ZZZ`, sum 1.01), end `2023-01-03`, decision `2017-12-08` with lag 1 and end `2017-12-08`, unsorted decisions, decision not a session (`2017-11-25`) → each `pytest.raises(ValueError)`.
  - `test_invariants_pass_on_cases`: for cases 1–6 `result.invariants['passed'] is True`.
- [ ] **Step 2: Run** `tests/test_engine.py` → FAIL (module missing).
- [ ] **Step 3: Implement** `engine.py` per Interfaces; write `docs/n2/manual_reconciliation.md` with each case's inputs and arithmetic.
- [ ] **Step 4: Run** → PASS; full suite → all pass.
- [ ] **Step 5: Commit** `feat: add N2 simulation loop with hand-checked reconciliations`.

### Task 4: Output files, journaled run, CLI and test provider

**Files:**
- Modify: `src/alpha_lab/engine.py` (append), `src/alpha_lab/__main__.py`
- Test: `tests/test_engine_run.py`

**Interfaces:**
- Consumes: `simulate`, `Result`, `RunConfig`, `Scenario` (Task 3); `load_market` (Task 1); `provenance.Run`, `provenance.freeze`, `provenance.canonical_bytes`, `provenance.sha256`.
- Produces:
  - `invariant_rotation(t: str, history: Market) -> dict[str, float]`: m = 12·year + month of t; tickers in ASCII order with index i; raw_i = 1 + (m + i) mod 3; w_i = raw_i / Σ raw. Uses only `t`.
  - `PROVIDERS = {'invariant_rotation': (invariant_rotation, '1')}` (name → function, version).
  - `result_files(result, config, provider_name, market) -> dict[str, bytes]`: `config.json` (canonical bytes: config fields, scenario, provider name/version, `market.vintage`, `market.manifest_sha256`), `decisions.csv`, `orders.csv`, `trades.csv`, `payouts.csv`, `daily.csv` (columns as in spec §7; `daily.csv` adds one `qty_<TICKER>` column per ticker), `invariants.json`. CSV via pandas `to_csv(index=False, lineterminator='\n', float_format='%.10g')` for deterministic bytes.
  - `run_simulation(root: Path, derived: Path, provider_name: str, config: RunConfig, parent: str | None = None, expected_sha256: str | None = VINTAGE_MANIFEST_SHA256) -> Path`: inside `Run(root, 'N2 execution run', cfg_dict, parent)`: `load_market`, `simulate`, `freeze(root / 'data/runs' / run.run_id, files, metadata)`, `run.finish('completed' if invariants passed else 'invariants_failed', [path], sha256(manifest.json bytes), warnings)`. Any exception → journaled `failed` by `Run`.
  - CLI: `python -m alpha_lab simulate <derived> --provider invariant_rotation --start S --end E [--cost --lag --reserve --proxy-days] --root R --parent P` prints the run directory.
- [ ] **Step 1: Write failing tests** in `tests/test_engine_run.py` (synthetic vintage via `write_vintage` on SESSIONS with tickers AAA, BBB; `expected_sha256` = its manifest hash):
  - `test_run_is_journaled_and_frozen`: journal events `['started', 'completed']`, purpose `N2 execution run`; `verify(run_dir)` passes; files set equals the seven names above.
  - `test_run_is_deterministic`: two runs with identical config → identical `manifest['files']` hashes.
  - `test_reserved_end_is_failed_run`: `end_session='2023-01-03'` → `ValueError`, journal `['started', 'failed']`, no `data/runs` directory.
  - `test_invariant_rotation_weights`: for `t='2008-07-23'` weights sum to 1, all > 0, and differ from `t='2008-08-29'`.
  - `test_cli_simulate`: `main(['simulate', <rel derived>, '--provider', 'invariant_rotation', '--start', '2017-11-28', '--end', '2017-12-08', '--root', str(tmp_path)])` prints an existing directory. Since the CLI uses the real-vintage hash, add `--expected-sha256` option (default the constant) and pass the synthetic hash in the test.
- [ ] **Step 2: Run** → FAIL.
- [ ] **Step 3: Implement** per Interfaces.
- [ ] **Step 4: Run** → PASS; full suite → all pass.
- [ ] **Step 5: Commit** `feat: add journaled N2 runs, output files and simulate CLI`.

### Task 5: Execution model document and decision D021

**Files:**
- Create: `EXECUTION_MODEL.md` (Russian)
- Modify: `DECISIONS.md` (append D021), `README.md` (link to EXECUTION_MODEL.md and docs/n2/manual_reconciliation.md)

- [ ] **Step 1:** Write `EXECUTION_MODEL.md`: normative description of spec §2 contract, §4 parameters and reserved guard, §5 event order, §6 sizing/execution/costs, §7 output schemas, §8 invariants, with references to RESEARCH_PROTOCOL.md lines 40–54 and 118–126 and to module/function names from Tasks 1–4. Style per AGENTS.md (dry, no evaluative words).
- [ ] **Step 2:** Append `## D021 — 2026-10-07: толкования протокола в движке исполнения N2` listing each interpretation from spec §11 with reason, alternative and consequence, in the format of D016–D020.
- [ ] **Step 3:** `git diff --check` clean; full test suite passes.
- [ ] **Step 4: Commit** `docs: add N2 execution model and decision D021`.

### Task 6: Real-data invariant run and N2 report (controller task)

Run by the controller, not a subagent, because it appends to the real journal.

- [ ] **Step 1:** Clean tree check: `git status --short` empty.
- [ ] **Step 2:** Run `PYTHONPATH=src .venv/Scripts/python -m alpha_lab simulate data/derived/20261006T172442-80ef993493 --provider invariant_rotation --start 2007-05-31 --end 2022-12-30 --root .` → prints `data/runs/<run_id>`; journal last event `completed`.
- [ ] **Step 3:** Check `invariants.json`: `passed` true; `split_events` contains `['EEM', '2008-07-24']` and `['BIL', '2017-11-30']`; `proxy_payouts` contains BIL ex `2008-03-03`. Rerun once with `--parent <run_id>` and compare `manifest.json` `files` hashes (identical).
- [ ] **Step 4:** Commit journal lines: `chore: log N2 invariant runs <run_id> and <run_id2>`.
- [ ] **Step 5:** Write `docs/n2/N2_REPORT.md` (invariant results, counts of decisions/trades/cancellations by reason, both splits, proxy payout, D016–D019 limitations; no NAV or returns), update `STATUS.md` (stage, checks, last verified commit, next step N3) and `README.md` (verified `simulate` command). Commit `docs: add N2 report and update STATUS and README`.
- [ ] **Step 6:** Whole-branch review (superpowers:requesting-code-review), fix findings, then merge per superpowers:finishing-a-development-branch.
