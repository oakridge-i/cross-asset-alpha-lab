# N4: hypotheses H1 and H2, six configurations - specification

Date: 8 October 2026. Branch `claude/n4-hypotheses`, created from `main` at `a1d734e`. Basis: RESEARCH_PROTOCOL.md sections 4, 5, 7, 9, 11, 13 and 14; docs/MASTER_PLAN.md section 5 (N4: "Six configurations, causal features, experiment records"); EXECUTION_MODEL.md; decisions D021 and D022; docs/n3/N3_REPORT.md; experiments/README.md; docs/REPRODUCIBILITY.md. Agreed with the user on 8 October 2026:

- N4 publishes no return, risk, utility, drawdown or USD-cost result of H1/H2. Only the diagnostics of section 6.2 may be published or shown; the quantities of section 6.3 are excluded; run directories are storage read only by code (section 6.1). This is an additional procedural restriction on viewing H1/H2 results. It does not make 2014-2022 independent history: that period is familiar and the N3 benchmarks for it are published (protocol section 9).
- One-way turnover (protocol line 157) and `cost_ratio`, which equals the scenario cost times turnover, are published as trading diagnostics. They are the only section 11 quantities of H1/H2 computed in N4.
- The turnover denominator remains NAV at the decision close (D022 item 11); D023 supplements that item with the literal alternative and its size for B3. N3 tables and code are unchanged; the N3 report wording is corrected (section 2).
- The status of the six configurations changes from `registered_not_tested` to `computed_not_evaluated` under the conditions of section 9. The journal gets no new event type.
- The section 12 scenarios, including the two diagnostic variants of H1_252_3 (score without division by sigma; equal weights in the selected set), are implemented and run in N6, not in N4.
- H1/H2 runs in N4 freeze no `metrics.json`; the return and risk metrics of section 11 for H1/H2 are first computed by the N5 code.

## 1. Goal and boundaries

N4 implements the six configurations of protocol section 7 as weight providers built on the existing primitives (`features.total_return_index`, `features.sigma`, `features.covariance`, `portfolio.inverse_vol`, `portfolio.common_risk`), records their causal signals, registers one run per configuration on the approved vintage, and verifies the six runs with a journaled report run. N4 succeeds when:

1. the six runs complete with all seven invariants passing;
2. the N4 report run accepts them, including the signal, sizing and H2-to-parent checks of section 7;
3. a repeat of all seven runs reproduces the manifest `files` dictionaries;
4. the N3 regression test of section 5.5 and the independent recomputation of section 11 pass on the approved vintage;
5. every N4 artifact and output stays within section 6.

Outside N4: P_A1 and walk-forward selection (protocol section 10, N5); ΔU, bootstrap, Holm adjustment and regressions (section 11, N5); the return, risk and utility metrics of section 11 for H1/H2 (N5); all section 12 scenarios and `scenario_id` (N6); any session after 2022-12-30; deferred item (b), the `payable.json` check in N1 audit (a separate N1 branch). No new dependencies.

Data: only `data/derived/20261006T172442-80ef993493` (D020), manifest SHA-256 `f89346107cf7da6ca052693d188b8a576a08d42024c86865b0a42a63b1d294f2`, loaded through `market.load_market` with the pinned hash. The period guard `LAST_OPEN_SESSION = '2022-12-30'` is unchanged. Environment manifest SHA-256 `5226dc9b0f21363873eb9a8420891733bbad1bc6c536262a3341eead520ce773`, the environment of the N3 runs.

## 2. Items closed first

2.1. Turnover denominator. Protocol line 157 defines one-way turnover as Σ|trade notional| / pretrade_NAV without fixing the moment. D022 item 11 chose NAV at the close of the decision session, the NAV from which orders are sized, and named NAV at the execution Open as the alternative; `engine.simulate` implements the choice. The N3 report calls the denominator "pretrade NAV". D023 item 1 supplements D022 item 11: in this project `pretrade_NAV` means NAV at the decision close; the literal reading, NAV immediately before the trades, is NAV at the Open of the execution session after the pre-open events, and differs by one overnight price move. D023 discloses the size of the difference for B3 over the period `full`.

The values are computed by `docs/n4/turnover_denominator.py RUN_DIR VINTAGE_DIR`, a read-only diagnostic outside `src` that writes nothing to the journal or `data/` and is not journaled. It runs `provenance.verify` on the run directory and on the vintage and requires the vintage manifest hash to equal the approved hash. It reads `decisions.csv`, `trades.csv` and `daily.csv` of the run and the Open, dividend and split ratio of the vintage. For each decision, pre-trade NAV at the execution Open = cash + receivables at the decision close + Σ post-split quantity × dividend for tickers with an ex-date at the execution session + Σ post-split quantity × Open of the execution session, where post-split quantity = quantity at the decision close × split ratio at the execution session. This matches the engine's order of events (split, accrual on post-split quantity, crediting, trades; crediting does not change NAV). The definition assumes lag 1, with no session between decision and execution; the script raises `ValueError` for another lag and for a held ticker without a finite positive Open. It prints the published `turnover_annual` of `full` recomputed from the CSV files and the alternative, both as Σ turnover × 252 / n_returns. Run on the first N3 B3 run `20261007T180033-bba99392df`. Published value in `metrics.json`: 2.927434880273802. Expected: the decision-close value agrees to 1e-9 and the alternative is 2.9257729824765 to 1e-9. D023 item 1 cites the script commit, the command, the B3 run manifest SHA-256, the vintage hash and both values.

The protocol stays at version 1.0: line 157 does not fix the moment, the decision-close NAV is also a pre-trade NAV and the sizing NAV, turnover changes no order, trade or NAV, and no section 13 criterion uses turnover. Provider versions, `METRICS_SCHEMA` and code are unchanged.

2.2. Proxy payment lag wording. docs/n3/N3_REPORT.md line 11 says "proxy payment lag 10 sessions". The contract (protocol line 42, D021 item 5) is 10 calendar days, then the first eligible session no earlier than ex-date + 10 calendar days. No N3 result is affected: no proxy payout falls inside the N3 window.

2.3. N3 report corrections. Line 11 is corrected per 2.2, line 87 to "divided by NAV at the decision close", and a dated section `Corrections` at the end of the report names both changes and refers to D023. Numbers, tables, run identifiers and hashes are unchanged. The report is not byte-registered in docs/DOCUMENTATION_EDITION.md.

## 3. Features (`src/alpha_lab/features.py`)

All functions take a `Market` restricted to sessions <= t (`Market.history(t)`) or its total-return index; t is the last session. The common warm-up of D022 item 6 (`require_warmup`, 253 closes) applies to every provider.

3.1. `momentum(index, lookback, skip=21)`: for each risky ticker,

M_i = (T_i[t-21] / T_i[t-L]) / (T_BIL[t-21] / T_BIL[t-L]) - 1 (protocol line 95),

with positional indices `T[t-21] = index.iloc[-22]` and `T[t-L] = index.iloc[-(L+1)]`. The window holds exactly L - 21 daily returns: 231 for L = 252, 105 for L = 126 (protocol line 93). Fewer than L + 1 sessions raise `ValueError`. Sigma is measured through t (protocol line 99) by the existing `sigma`.

3.2. `month_end_levels(market, index, count=7)`: the last `count` month-end sessions of the history and the index rows at those sessions, ascending. A month-end session is the last session of the history in a calendar month; the month of t contributes t. `ValueError` when fewer than `count` months are present, when any of the `count` sessions is not the last XNYS session of its calendar month (`normalize.calendar`), or when the `count` months are not consecutive calendar months. A failed check stops the run (protocol line 54); an incomplete month is never skipped. A t that is not the last XNYS session of its month therefore raises. Month t is included because its last session is complete at the 18:00 decision time (protocol line 107).

3.3. `monthly_excess(levels)`: for the six consecutive pairs of month-end levels and each risky ticker, E_i,j = (T_i,end(j) / T_i,end(j-1)) / (T_BIL,end(j) / T_BIL,end(j-1)) - 1 (protocol line 103), j = 1 oldest to 6 newest.

## 4. Providers (`src/alpha_lab/hypotheses.py`)

4.1. Contract. Every provider is called by the engine as `provider(t, history)`, like the benchmarks. `h1(t, history, lookback, k)` and `h2(t, history, h)` are bound in the registry with `functools.partial` on the keyword parameters. A hypothesis provider returns `Decision(weights, signals)`: `weights` is a dictionary of Python floats over the ten tickers; `signals` is a list of nine rows, one per risky ticker in ASCII order. Both come from one computation.

4.2. `portfolio.common_risk` is split without a change of results: `capped(q)` performs steps 1 and 2 of protocol lines 68-69 and returns v; `risk_detail(q, cov)` returns `(v, a, w)`, performing steps 3 and 4 on `capped(q)` with the current arithmetic; `common_risk(q, cov)` returns the w of `risk_detail` and keeps its signature and return value. The N3 regression test (section 5.5) confirms that benchmark results are unchanged.

4.3. H1(L, K), decision at the close of t:

1. `require_warmup(history)`; T = `total_return_index(history)`; sigma = `sigma(history)`; M = `momentum(T, L)`.
2. S_i = M_i / sigma_i (protocol line 97).
3. Eligible: S_i > 0, strictly. Ranked by the key (-S_i, ticker), ticker in ASCII order, so a ticker breaks only exact ties (protocol line 99). Selected: the first min(K, number eligible). Missing slots are not filled with non-positive scores.
4. q = `inverse_vol(sigma, selected, k=K)`; then `risk_detail(q, covariance(history))`. Unused slots remain in BIL (protocol line 66).

4.4. H2(h), decision at the close of t, with K = 3 from the parent:

1. Parent: H1(252, 3) on the same history with the same code (protocol line 101).
2. Levels: `month_end_levels(history, T, 7)`; E = `monthly_excess(levels)`; positive_months_i = #{j : E_i,j > 0}; E = 0 is not positive (protocol line 107). F_i = 1 if positive_months_i >= h, else 0.
3. w_i = parent w_i if F_i = 1, else 0.0, as a copy of the parent value or an exact zero, with no arithmetic on the weight. w_BIL = 1 - fsum of the remaining risky weights, the convention of protocol line 71 and D022 item 9 (a value in [-1e-12, 0) is set to 0; a lower value raises `ValueError`). No reranking, no replacement ticker, no redistribution, no second `common_risk`, no upward rescaling (protocol line 107).

4.5. Signal rows. Columns for H1: `decision_session`, `ticker`, `momentum`, `sigma`, `score`, `eligible`, `rank`, `selected`, `q`, `v`, `scale`, `weight`. `rank` is empty for a non-eligible ticker. `q` is 0 for a non-selected ticker; `v` is the weight after the ETF and group caps; `scale` is a of protocol line 70, the same on every row of a decision; `weight` is the final target weight. H2 rows carry the parent's values in the H1 columns except `weight`, which is the H2 weight, and add `parent_weight`, `excess_1` to `excess_6` (E_i,j, oldest to newest), `positive_months` and `filter_pass`.

4.6. Registry. `engine.PROVIDERS` gains the kind `hypothesis` and six entries, version `1`, schedule `monthly`:

| ID | Function | Parameters |
|---|---|---|
| H1_252_3 | H1 | lookback 252, k 3 |
| H1_252_4 | H1 | lookback 252, k 4 |
| H1_126_3 | H1 | lookback 126, k 3 |
| H1_126_4 | H1 | lookback 126, k 4 |
| H2_4of6 | H2 | h 4, parent H1_252_3 |
| H2_5of6 | H2 | h 5, parent H1_252_3 |

Parameters are fixed in the entries; the command line cannot change them. `Provider` gains a field `parameters` (a dictionary, empty for the test provider and the benchmarks). For the `hypothesis` kind only, `config_record` adds `parameters` to the `provider` object, so it is journaled in the `started` config and frozen in `config.json`; benchmark and test configs are byte-identical to N3. The test provider and the benchmarks are otherwise unchanged.

## 5. Runs and journal (`src/alpha_lab/engine.py`)

5.1. A new `provider_decision(provider, market, session)` accepts a provider that returns a dictionary or a `Decision` and returns `(weights, signals)`, with `signals = []` for a dictionary. The weight checks are unchanged (keys, finite and >= 0, fsum <= 1 + 1e-12). `provider_weights` keeps its signature and returns the weights of `provider_decision`; `simulate` calls `provider_decision`. `Result` gains the list `signals`.

5.2. Journal. For `kind == 'hypothesis'` the Run records the purpose `N4 hypothesis run` and `candidate_ids = [name]` in the `started` and the terminal record. The record schema is unchanged. An N4 run is one continuous account over its window without a time split; the section 9 roles (development 2009-2013, walk-forward 2014-2022) apply to N5 reporting, not to the run.

5.3. Files. A hypothesis run freezes nine files: the seven N2 files, `weights.csv` (as in D022 item 15) and `signals.csv`. It freezes no `metrics.json`, and `compute_metrics` is not called for this kind. Benchmark runs keep their nine N3 files; test runs keep seven. `signals.csv` is ordered by `decision_session`, then ticker in ASCII order; numbers use the `%.10g` format and LF line ends (D021 item 16); booleans are written `True`/`False`; an empty rank is an empty field.

5.4. Window and scenario, as in N3: `--start 2008-12-31 --end 2022-12-30`, cost 0.001, lag 1, reserve 0.01, proxy 10 calendar days, initial cash 100000. The first decision is the close of 2008-12-31, executed at the open of 2009-01-02; the last is 2022-11-30; 168 decisions. `simulate` prints only the output path and exits with code 3 on `invariants_failed` (D022 item 1).

5.5. N3 regression. A test on the real vintage (skipped when it is absent) runs B0, B1, B2, B3 and REF_SPY in memory with the N3 window and main scenario and requires the SHA-256 of every file from `result_files` to equal the corresponding entry of the `files` dictionary in the manifest of the first N3 run. The 45 expected hashes are copied into the test from the manifests of runs `20261007T180004-12aae80084`, `20261007T180018-b6c98bd0aa`, `20261007T180026-dffe07154c`, `20261007T180033-bba99392df` and `20261007T180039-be7dd8f43a`. The test shows that the N4 code changes no benchmark file, including `config.json`, `decisions.csv` (turnover) and `metrics.json`.

5.6. Role of the N4 runs for N5. N5 adds code to `src`, so N5 will rerun the benchmarks and the six configurations on its frozen code. The N4 runs are the reference for that rerun: the shared files must have identical hashes. A rerun with identical inputs is not an independent experiment.

## 6. Viewing restriction

6.1. Scope and storage. Sections 6.2 to 6.4 apply to every N4 artifact and output: frozen report files, docs/n4, README.md, STATUS.md, DECISIONS.md, EXECUTION_MODEL.md, experiments/README.md, docs/REPRODUCIBILITY.md, commit messages, pull request text, console output, test output including assertion and failure messages, implementation and review reports, and conversation with the user. The directories `data/runs/<id>` of hypothesis runs, all nine files included, are storage read only by code: `provenance.verify`, the invariant checks inside the run, the report checks and diagnostics of section 7, and tests whose output is limited by 6.4. No file of a hypothesis run is opened for inspection.

6.2. Permitted diagnostics. Only the following may be published or shown.

Whole run, per configuration: the `passed` flag of each of the seven invariants and the overall flag; the number of split events and of proxy payouts. The invariants are checked over the whole run, so these items have no annual breakdown.

Period `full` (2009-01-01 to 2022-12-31) and each calendar year 2009-2022, per configuration:

- Counts: decisions; orders by status, with cancellation reasons; trades by side; payouts by status at the end of the run (paid, receivable) and by basis (actual, proxy).
- Selection aggregates: mean number of eligible tickers (S > 0) and of selected tickers per decision; the distribution of the number selected, 0 to K; the number of empty selections.
- H2 filter aggregates: the share of parent-selected ticker-decisions that pass the filter; the number of decisions where the filter removes at least one ticker; the mean, over decisions with a positive parent risky target weight, of the share of that weight removed by the filter.
- Target-weight aggregates: mean and maximum of the summed risky target weight; mean target BIL weight; maximum target weight of any single ETF and of any group, without the ticker or group name; the number and share of decisions where the volatility target binds (`scale` < 1) and the mean `scale`.
- Trading activity: sum and mean per decision of one-way turnover (D022 item 11, D023 item 1); `cost_ratio` = scenario cost × sum of one-way turnover, which equals the definition of D022 item 13 up to floating-point rounding because costs = cost × notional; minimum `buy_fill` and the number of decisions with `buy_fill` < 1.

Period `full` only, per configuration and ticker: the selection frequency (share of decisions); for H2, the share of the ticker's parent selections that pass the filter.

Attribution: a decision, with its signals, target weights, turnover and `buy_fill`, belongs to the year of its execution session (D022 item 12); an order to the year of its `execution_session`; a trade to the year of its `session`; a payout to the year of its `ex_session`, the session at which the entitlement arises, counted with its status at the end of the run. A share or mean whose denominator is zero (for example the H2 pass share of a ticker the parent never selected, or a year without a decision with positive parent risky weight) is `null`, as in D022 item 14. `scale` < 1 and `buy_fill` < 1 are evaluated on the values parsed from the frozen `%.10g` text.

6.3. Excluded quantities. None of the following may be published, shown or described for H1/H2:

- NAV in any form, and returns of any frequency derived from it: total return, CAGR, realized volatility, excess return, mean excess return, Sharpe ratio, utility U, ΔU, drawdown;
- costs in USD;
- USD amounts of cash, positions and receivables; realized weights and cash shares (holdings × close / NAV);
- share quantities: `target_qty`, `held_qty`, `order_qty`, `filled_qty` in `orders.csv`, `qty` in `trades.csv` and `payouts.csv`, `qty_<TICKER>` in `daily.csv`; with prices they give NAV and USD amounts;
- profit and loss per trade or per ticker; payout amounts; trade notionals and their sums; the USD amounts in the `detail` fields of `invariants.json`;
- per-decision target weights, per-decision selections, and per-decision `q`, `v`, `scale` and `weight` values of the real runs, beyond the aggregates of 6.2; with public prices they reconstruct approximate monthly returns;
- per-ticker selection frequencies or H2 pass shares for any period other than `full`;
- any comparison of H1/H2 configurations with one another or with B0-B3 and REF_SPY on these quantities;
- regressions, bootstrap, Holm adjustment.

6.4. Handling. Tests on the real vintage and checks on real hypothesis runs print or report only sessions, tickers, flags, counts and maximum differences. Synthetic test data are unrestricted. An `invariants_failed` run is diagnosed from the names of the failed checks in the journal's `quality_warnings` and by reproducing the failure on synthetic data; reading a `detail` field or any other excluded column of a real run is recorded under the next rule. If an excluded quantity is shown, STATUS.md and the N4 report record what was shown, where, when and to whom. Any aggregate of 6.2 combined with public prices still permits approximate inference about exposures; D023 item 6 and the N4 report disclose this.

## 7. Report (`python -m alpha_lab hypothesis-report --runs RUN_DIR... --root PROJECT [--parent ATTEMPT] [--expected-sha256 HASH]`)

A Run with the purpose `N4 hypothesis report` and `candidate_ids` H1_252_3, H1_252_4, H1_126_3, H1_126_4, H2_4of6, H2_5of6, in `src/alpha_lab/hypothesis_report.py`. The journal and provenance checks shared with the N3 report are parameterized in `report.py` by the expected purpose and file set; the N3 report's behaviour and output bytes are unchanged (a test compares them). Checks added for N4 only (for example on the terminal record) live in `hypothesis_report.py`. `--expected-sha256` exists for tests on synthetic vintages; a registered report journals the approved hash. Before computing anything the report requires, failing the Run with `ValueError` naming the rule, the configuration and, where applicable, the session and ticker:

1. Exactly six run directories inside `data/runs` whose frozen providers are the six configurations, each once. Each passes `provenance.verify`; its file set equals the nine hypothesis files exactly, so a benchmark run or a directory with `metrics.json` is rejected.
2. Journal: exactly one `started` and one terminal record; terminal status `completed`; `dirty_tree` false and `git_sha` non-null in both; `output_paths`, `data_sha256` and `config_sha256` agree with the directory as in D022 item 16; the journaled config agrees with `config.json` in provider (name, version, parameters), scenario, window, decision sessions and initial cash; purpose `N4 hypothesis run` and `candidate_ids = [name]` in both records.
3. Code and environment: each `started` record's `environment_manifest_sha256` equals the report run's; the `src` tree of each run's `git_sha` equals the `src` tree of the report run's `git_sha`.
4. Configuration and calendar. `invariants.json` has `passed` true; each provider version equals the registry version; the approved manifest hash is in `config.json` and the manifest metadata. Each `config.json` has exactly: `start_session` 2008-12-31, `end_session` 2022-12-30, scenario cost 0.001, lag 1, reserve 0.01, proxy_pay_days 10, `initial_cash` 100000.0, `decision_sessions` null, and `provider.parameters` equal to the table of 4.6 held as a constant in `hypothesis_report.py`, independent of the registry. The expected decision sessions are the last XNYS session of each month from December 2008 to November 2022 (`normalize.calendar`), 168 sessions. The `decision_session` column of `decisions.csv` and of `weights.csv` equals this list in order; the `execution_session` of each decision is the next XNYS session after it; for each expected session `signals.csv` holds exactly nine rows whose tickers are the nine risky tickers in ASCII order, and it holds no other session.
5. Weights and signals, per configuration and decision, on values parsed from `%.10g` text with tolerance 1e-9 (relative 1e-9 where stated):
   - each of the nine risky weights is >= 0 and <= 0.25, and each group sum is <= 0.50; BIL is exempt (protocol line 73), so an empty selection with BIL = 1 is valid;
   - `w_BIL` = 1 - fsum of the nine risky weights; `usd` = 1 - fsum of the ten weights and |`usd`| <= 1e-9;
   - the `weight` field of `signals.csv` equals `w_<ticker>` of `weights.csv` as text;
   - `score` = `momentum` / `sigma` (relative 1e-9); `sigma` > 0; eligible exactly when `score` > 0;
   - the ranks of eligible tickers are 1 to m without gaps, and the score at rank r is >= the score at rank r + 1;
   - selected exactly when rank <= K, with K from the table of 4.6 (K = 3 for H2);
   - `q`, `v` and `weight` are `0` for a non-selected ticker and `q` > 0 for a selected ticker; fsum of `q` = m_selected / K; `q` × `sigma` is equal across the selected tickers (relative 1e-9);
   - `v` <= min(`q`, 0.25) for every ticker;
   - `scale` is the same text on all nine rows and 0 < `scale` <= 1; `weight` = `scale` × `v` for every ticker.
6. Across runs, per decision and ticker:
   - `sigma` is identical as text across all six runs;
   - `momentum`, `score`, `eligible` and `rank` are identical as text between H1_252_3 and H1_252_4, and between H1_126_3 and H1_126_4;
   - the selected set of H1_252_3 is a subset of that of H1_252_4, and that of H1_126_3 of that of H1_126_4.
7. H2 against H1_252_3, per decision and ticker:
   - the fields `momentum`, `sigma`, `score`, `eligible`, `rank`, `selected`, `q`, `v` and `scale` of the H2 row equal those of the H1_252_3 row as text;
   - `parent_weight` equals both the `weight` field of the H1_252_3 row and `w_<ticker>` of the H1_252_3 `weights.csv` as text;
   - `excess_1` to `excess_6` and `positive_months` are identical as text between H2_4of6 and H2_5of6; `positive_months` equals the number of `excess_j` > 0 (the sign survives `%.10g`);
   - `filter_pass` is true exactly when `positive_months` >= h;
   - the H2 weight equals `parent_weight` as text when `filter_pass` is true and equals `0` otherwise;
   - item 5 applies to H2 as well, so released weight that stays in USD instead of BIL is rejected; in addition the H2 BIL weight is not lower than the parent's.

The expected window, scenario, initial cash, decision months and parameter table are module-level constants of `hypothesis_report.py`, so that tests on synthetic vintages can set them; registered reports use the values above.

Output in `data/reports/<run_id>/`: `hypotheses.json` (canonical JSON) and `hypotheses.md` (deterministic Markdown tables). Both hold only the diagnostics of section 6.2, built from a whitelist of keys; neither holds a run id, timestamp or path. The report reads `weights.csv`, `signals.csv`, the `decision_session`, `execution_session`, `turnover` and `buy_fill` columns of `decisions.csv`, the `execution_session`, `status` and `cancel_reason` columns of `orders.csv`, the `session` and `side` columns of `trades.csv`, the `ex_session`, `status` and `pay_basis` columns of `payouts.csv`, and the flags and event lists of `invariants.json`. It does not read `daily.csv` or any other column; `provenance.verify` hashes all files as bytes. Run ids and run manifest hashes go into the report manifest metadata. A repeated report is compared by the manifest `files` dictionary.

## 8. Registered runs

Environment: `../../.venv/Scripts/python` relative to the worktree root, with `PYTHONPATH=src` of the worktree; the environment manifest hash must equal the value in section 1. The approved vintage is copied into the worktree's `data/derived/` (excluded from Git) and checked by `provenance.verify` and its manifest hash before the first run. Before the first run the full test suite passes and the whole branch has been reviewed.

Sequence, each step on a clean tree, with the new journal lines committed before the next step:

1. `simulate` for H1_252_3, H1_252_4, H1_126_3, H1_126_4, H2_4of6, H2_5of6 with the window of section 5.4.
2. `hypothesis-report` over the six run directories of step 1.
3. Repeats of the six runs, each with `--parent` set to its first run, then a repeat of the report over the six repeat directories with `--parent` set to the first report.
4. Comparison of the manifest `files` dictionaries for all seven pairs.

Failures. A `failed` or `invariants_failed` run, or a failed report, stays in the journal. Changes to `src` after the first registered run are bug fixes only, never motivated by the diagnostics of 6.2 (protocol line 188). Any such change requires rerunning all six configurations on the new tree, each with `--parent` set to its previous run, followed by a new report, because check 3 requires one `src` tree. A fix that changes the output of a provider increments its version; a change in H1_252_3 also increments the versions of H2_4of6 and H2_5of6. N4_REPORT lists every earlier run with its cause and versions. A failure in the repeat comparison is handled the same way.

After the branch is merged, `data/runs` and `data/reports` of the worktree are moved to `data/` of the main checkout.

## 9. Status of H1/H2

D023 defines the status `computed_not_evaluated`: the configuration has a completed registered run on the approved vintage; the first completed N4 report over the final set of six runs has accepted it; the repeat comparison of section 8 step 4 has found all seven pairs equal; no decision under protocol section 13 exists. The six configurations move from `registered_not_tested` to `computed_not_evaluated` when the last of these conditions is met. A failed run does not change the status. If an excluded quantity of 6.3 is shown, the status is unchanged and the disclosure of 6.4 is attached to it. Statuses of N5 and N6 are defined at those stages.

The journal records no status event. The evidence is the existing records: the six runs with purpose `N4 hypothesis run` and their `candidate_ids`, the completed report runs and the repeats. STATUS.md, README.md and experiments/README.md state the current status with these run ids. RESEARCH_PROTOCOL.md section 14 and docs/n0/protocol_manifest.json are historical and are not edited.

## 10. Publication

docs/n4/N4_REPORT.md publishes: purpose and boundaries; vintage, environment and commands; the registered runs with git SHAs and journal commits; the reproducibility comparison; invariant flags and counts; the diagnostics of section 6.2 reproduced from the frozen `hypotheses.md` with numbers unchanged; disclosures. The disclosures state that no return, risk, utility or USD-cost result of H1/H2 is published and that these metrics are first computed in N5; that turnover and `cost_ratio` are the only section 11 quantities published; that the viewing restriction is procedural, that published aggregates combined with public prices permit approximate inference about exposures, and that the restriction does not make 2014-2022 independent; that most of the 2008 crisis is outside the window (protocol line 141); the data limitations of D016-D020; and any failed run, rerun or display under sections 6.4 and 8.

## 11. Tests

TDD on synthetic markets in `tmp_path` under `no_network`, as in N2 and N3, with expected values computed independently of the code under test.

- Momentum window: a jump in the return from t-21 to t-20, or in any later return, leaves M unchanged and changes sigma; a jump in the return from t-L to t-L+1 changes M; a jump in the return from t-L-1 to t-L leaves M unchanged; L + 1 sessions suffice and L sessions raise `ValueError`.
- Month ends: fewer than seven months, a non-consecutive month, a month whose last history session is not its last XNYS session, and a t that is not a month end raise `ValueError`.
- Causality at engine level: two full markets that differ only after t, and two that differ only in the payment sessions of `payable`, give identical weights and signal rows at every decision <= t, for H1 and H2.
- H1: an exact tie in S broken by ticker; a near tie ordered by S; S = 0 not eligible; fewer than K eligible leaves the unused slots in BIL with q carrying m/K; an empty selection gives BIL = 1; a hand-computed decision for one configuration.
- H2: E = 0 not counted; the set of H2 tickers is a subset of the parent's; kept weights equal the parent's bit for bit; H2 BIL >= parent BIL; an empty parent gives BIL = 1; a hand-computed decision including `excess_1` to `excess_6`.
- `capped` and `risk_detail` give the same results as `common_risk` before the split.
- Runs: file sets for the three kinds; purpose, `candidate_ids` and `parameters` for all six configurations; benchmark `config.json` without `parameters`; no `metrics.json`; two identical runs give identical bytes; signal columns and order; an H2 run with a mid-month decision journals `failed`.
- Report: one rejection test per rule of section 7, including: a benchmark run or a directory with `metrics.json`; a duplicated directory; six mutually consistent runs with a shorter window, another cost, another initial cash or other parameters; a missing or extra decision session, dates that differ between `decisions.csv`, `weights.csv` and `signals.csv`, a duplicated or foreign ticker row; ranks in ascending score order; `inverse_vol` with k = 9; a score not divided by sigma; weight on a non-selected ticker; `weight` ≠ `scale` × `v`; momentum differing between H1_252_3 and H1_252_4; a modified H2 weight, `rank`, `selected`, `excess_j` or `positive_months`; an H2 BIL weight that leaves released weight in USD. Acceptance tests: an empty selection with BIL = 1; weights written in exponent notation by `%.10g`. Document tests: the keys equal the whitelist; replacing every excluded column of 6.3 (including quantity columns, `receivables`, `positions_value`, `cost`, `cash_after`) in synthetic run files leaves the document bytes unchanged (the document builder is tested directly, without `verify`); annual attribution and `null` denominators; a repeated report gives identical files; the N3 report gives the same bytes as before.
- Real vintage (skipped when absent; output limited by 6.4): the six providers return valid decisions at 2008-12-31 and 2022-11-30; an independent recomputation of the target weights and selections of all six configurations at all 168 decisions, written with NumPy without calling `features`, `portfolio` or `hypotheses`, with maximum absolute difference <= 1e-12 and identical selections; the N3 regression of section 5.5.

## 12. Documents

- DECISIONS.md: D023, dated 8 October 2026, written before any registered H1/H2 run, in the format of D022 (decision, alternative, consequence). Items: (1) turnover denominator, as a supplement to D022 item 11, with the values and provenance of 2.1; (2) proxy payment lag wording in N3_REPORT; (3) H1 window indexing and tie-break; (4) H2 month-end levels, the stopping checks of 3.2, E = 0, the application of the filter to the parent's weights and the BIL convention; (5) `Decision`, the provider contract, the `hypothesis` kind and its `parameters`, purpose, the nine files, `signals.csv` and the absence of `metrics.json`, which defers the experiments/README requirement on metrics to N5; (6) the viewing restriction of section 6, including storage, turnover and `cost_ratio`, and the residual inference from aggregates; (7) the N4 report and its checks; (8) the failure and rerun rule of section 8 and provider versions; (9) the status `computed_not_evaluated` and its transition; (10) the N3 regression and the role of the N4 runs for N5; (11) section 12 scenarios, `scenario_id`, the cost and delay grid, P_A1 and walk-forward assigned to N5 and N6.
- docs/n3/N3_REPORT.md: the corrections of section 2.3.
- docs/n4/turnover_denominator.py: the recomputation of section 2.1.
- EXECUTION_MODEL.md: a short section on hypothesis providers, `Decision` and `signals.csv`.
- experiments/README.md: the purposes `N4 hypothesis run` and `N4 hypothesis report`, the file set, the run sequence, the rerun rule and the current status; replace "The journal holds no H1/H2 result" (line 3); state the attempt count required before N5: the six registered configurations, any reruns after bug fixes with their causes, repeats with `--parent` not counted as attempts, no strategy attempt outside the journal in this project, the AAPL journal excluded.
- docs/REPRODUCIBILITY.md: N4 commands and the table of registered runs, distinguishing commands verified by the runs from commands not executed; replace "no strategy has been run" (line 3).
- README.md: stage N4, the status `computed_not_evaluated`, the statement that H1/H2 returns are not published before N5; replace "contains no strategy backtest" (line 7) and correct the milestone row that places cost and delay robustness in N4-N5 (section 12 robustness is N6).
- STATUS.md: an N4 section with runs, checks, limitations, the next step and the verified commit.
- docs/n4/N4_REPORT.md: section 10.

English, in the style of docs/DOCUMENTATION_EDITION.md: factual, with protocol line references, no account of how the work was organized. The line endings of each edited file are preserved (the repository sets `* -text`; DECISIONS.md, README.md, experiments/README.md and docs/REPRODUCIBILITY.md mix CRLF and LF lines); `git diff --stat` and `git diff --ignore-cr-at-eol` are checked before each commit. RESEARCH_PROTOCOL.md, docs/n0/protocol_manifest.json and the N3 tables are not edited.
