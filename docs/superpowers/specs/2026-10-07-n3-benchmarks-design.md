# N3: benchmarks B0-B3 and REF_SPY - specification

Date: 7 October 2026. Branch `claude/n3-benchmarks`, created from `main` at `d8458b4`. Basis: RESEARCH_PROTOCOL.md sections 3-6, 9, 11 and 12; docs/MASTER_PLAN.md section 5 (N3: "Reproducible B0-B3 report"); EXECUTION_MODEL.md; decisions D020 and D021; docs/n2/N2_REPORT.md; the deferred items in STATUS.md. Agreed with the user on 7 October 2026: full section 11 metrics may be published for 2009-2022 only; REF_SPY is a single purchase; N3 runs the main scenario only; `invariants_failed` and `quality_failed` exit with code 3.

## 1. Goal and boundaries

N3 implements the section 5 weight construction, the five benchmarks of section 6, the section 11 metrics that apply to a single portfolio, and a reproducible benchmark report on the approved vintage. N3 succeeds when the five benchmark runs complete with all seven invariants passing, the report run accepts them, a repeat of all six runs reproduces the result files byte for byte, and the report is published within the limits of section 4 below.

Before any benchmark is computed, N3 closes the N2 deferred items that affect it (section 2). Deferred item (b), the `payable.json` check in N1 audit, is a separate N1 branch and is outside N3.

Outside N3: H1/H2 and P_A1; the bootstrap, Holm adjustment and regressions of section 11, which compare candidates with comparators; the section 12 scenario grid, leave-one-class-out and calendar-block robustness runs (N6); any session after 2022-12-30. No new dependencies.

Data: only `data/derived/20261006T172442-80ef993493` (D020), loaded through `market.load_market` with the pinned manifest hash. The period guard of D021 item 7 is unchanged.

## 2. N2 deferred items closed first

2.1. Events on sessions outside the common calendar. `market.market_from_frames` additionally rejects, with `ValueError` naming ticker and session:

- a row of a ticker frame whose session is not in the common calendar, lies in [`start`, last common session], and has a finite `dividend > 0` or a finite `split_ratio != 1`;
- an accepted payout (a `Market.payable` entry) whose payment session is not later than the last common session and is not a common session.

Rows before `start` remain unchecked (D021 item 13); rows after the last common session are outside every run. A payment session later than the last common session remains allowed: such a payout stays `receivable`. The approved vintage must still load (`test_real_vintage_loads`).

2.2. Payment sessions after scenario recomputation. `engine.pay_map` recomputes proxy rows for `proxy_pay_days` = k (D021 item 5). After recomputation it applies the same rule as 2.1 to every row: a payment session not later than the last market session and not a market session raises `ValueError`. The check runs inside the Run, so the run is journaled as `failed`. On the approved vintage XNYS and the common calendar coincide, so k = 0, 10 and 30 all pass.

2.3. Numeric weights. `normalize.finite_number` accepts any `numbers.Real` that is finite, including `np.int64`, `np.float32` and `np.float64`, and rejects `bool`, `np.bool_`, NaN and infinities. N1 callers pass values parsed from JSON and are unaffected. The engine weight check keeps its other conditions (keys, >= 0, `math.fsum` <= 1 + 1e-12).

2.4. Initial cash. `RunConfig.__post_init__` rejects an `initial_cash` that is not a finite real number greater than 0 (`ValueError`), using the predicate of 2.3. The rejection happens when the configuration is created, before a Run exists, like a Scenario value outside the grid (D021 item 15), and is therefore not journaled. Reason: `provenance.canonical_bytes` forbids NaN and infinities, so a non-finite value cannot be written into a `started` record; a uniform pre-Run rule for all invalid values is simpler than encoding non-finite numbers. The command line does not expose `initial_cash`. `ZeroDivisionError` in turnover can no longer occur.

2.5. Exit code. `python -m alpha_lab simulate` and `python -m alpha_lab audit` print the output directory and then exit with code 3 when the run's terminal status is `invariants_failed` or `quality_failed` respectively; `completed` exits with 0. Exceptions keep Python's code 1 and argparse errors code 2. `report` (section 7) has no such status: it either completes or fails.

2.6. Records. A new decision D022 amends D021 items 11 (exit code), 13 (scope of event checks) and 14 (numeric types), and records the N3 interpretations of sections 3-6 below. EXECUTION_MODEL.md, docs/REPRODUCIBILITY.md and experiments/README.md replace every statement that these commands exit with 0 on a failed check.

## 3. Features (`src/alpha_lab/features.py`)

All functions take a `Market` (normally `Market.history(t)`) and use only its sessions.

- `total_return_index(market)`: per ticker, T at the first session = 1 and T_d / T_{d-1} = s_d × (C_d + D_d) / C_{d-1} (protocol line 40), with s = `split_ratio`, C = close, D = dividend on the ex-date in as-traded units. A non-finite or non-positive result raises `ValueError`.
- `daily_returns(T)`: r_d = T_d / T_{d-1} - 1.
- Warm-up: a benchmark decision at t requires at least 253 consecutive common-calendar closes (252 returns) for all ten tickers up to and including t (protocol line 52). The requirement applies to every benchmark, including B0 and REF_SPY, which do not use the values, so that all comparisons share the same first eligible decision. Fewer sessions raise `ValueError`.
- `sigma(r, t)`: for each risky ticker, sqrt(252) × sample standard deviation (ddof = 1) of the latest 63 returns ending at t. A zero, non-finite or incomplete value raises `ValueError` (protocol line 58: an eligibility error, not an infinite score); the run fails rather than dropping the ticker (protocol line 54).
- `covariance(r, t)` (protocol line 60): 252 × sample covariance (ddof = 1) of the latest 126 daily excess returns r_i - r_BIL of the nine risky tickers, in the fixed order of `GROUPS`. The full 9 × 9 matrix is checked: asymmetry above 1e-12 or a smallest eigenvalue below -1e-12 raises `ValueError`.

## 4. Weight construction (`src/alpha_lab/portfolio.py`)

`GROUPS` = Equity: SPY, EFA, EEM; Treasury: IEF, TLT; Credit: LQD, HYG; Real: GLD, DBC (protocol section 2). BIL is the cash ETF and belongs to no group.

`inverse_vol(sigma, selected, K)`: q_i = (m / K) × (1/sigma_i) / Σ_{j in S} (1/sigma_j) for i in S, m = |S|, and 0 outside S (protocol line 64); an empty S gives all zeros (line 66).

`common_risk(q, cov)` (protocol lines 68-71):

1. v_i = min(q_i, 0.25).
2. For each group with Σ v > 0.50, multiply the group's v by 0.50 / Σ v; the removed weight is not reallocated.
3. V² = v' Σ v. If V² < -1e-12, `ValueError`; if -1e-12 <= V² < 0, V² = 0. V = sqrt(V²). a = 1 if V = 0, otherwise min(1, 0.10 / V). An all-zero v (for example an empty B3 selection) gives V = 0 and a = 1.
4. w_i = a × v_i; w_BIL = 1 - fsum(w_i). A w_BIL in [-1e-12, 0) is set to 0; a lower value raises `ValueError`.

The result is a dictionary over all ten tickers whose values are Python floats. Unit tests check each step against hand-computed values, including a capped ticker, a group above 0.50, a binding and a non-binding volatility target, V = 0, and the PSD rejection.

## 5. Benchmarks (`src/alpha_lab/benchmarks.py`)

Each benchmark is a provider `provider(t, history) -> dict[str, float]` (EXECUTION_MODEL.md section 2) that first applies the warm-up check of section 3.

| ID | Weights at decision t |
|---|---|
| B0 | BIL = 1, all others 0. |
| B1 | q_i = 1/9 for the nine risky ETFs, then `common_risk`. |
| B2 | `inverse_vol(sigma, all nine, K = 9)`, then `common_risk`. |
| B3 | S = {i : (T_i,t / T_i,t-252) / (T_BIL,t / T_BIL,t-252) - 1 > 0} with t-252 the session 252 sessions before t; `inverse_vol(sigma, S, K = 9)`, so q carries the factor m/9; then `common_risk`. No 21-session skip. |
| REF_SPY | SPY = 1, all others 0; no caps and no volatility target. |

Registry. `engine.PROVIDERS` maps a name to a `Provider(function, version, schedule, kind)`. `schedule` is `monthly` (default decision rule, D021 item 9) or `first_only`; `kind` is `test` or `benchmark`. `invariant_rotation` is `monthly`/`test`, version 1, unchanged. B0-B3 are `monthly`/`benchmark`, REF_SPY is `first_only`/`benchmark`; all start at version 1.

REF_SPY. `run_simulation` sets `decision_sessions = (start_session,)` for a `first_only` provider before the Run is opened, so the single decision appears in the journaled and frozen configuration. The position is bought once; distributions become USD cash under the common model and are not reinvested; there is no later trade.

Window. All five runs use `start_session = 2008-12-31` and `end_session = 2022-12-30` with the main scenario (cost 0.001, lag 1, reserve 0.01, proxy 10) and initial cash 100000. The first decision is the close of 2008-12-31 and executes at the open of 2009-01-02 (protocol line 135); the 2008-12-31 row of `daily.csv` is the starting observation (NAV 100000) and is not evaluated as a return. The default rule then decides at every month end through 2022-11-30 (D021 item 9). B0 reinvests distributions and free cash at each monthly decision through ordinary rebalancing.

Journal. For a `benchmark` provider the Run sets `candidate_ids = [name]` and the purpose `N3 benchmark run`; `test` providers keep `N2 execution run` and an empty list.

## 6. Run outputs and metrics (`src/alpha_lab/metrics.py`)

Runs of `test` providers freeze the seven N2 files unchanged. Runs of `benchmark` providers freeze nine: the seven N2 files plus

- `weights.csv`: one row per decision: `decision_session`, then `w_<TICKER>` for the ten tickers in ASCII order, then `usd` = 1 - fsum of the weights, formatted like the other CSV files;
- `metrics.json`: canonical JSON, `schema_version` 1, computed in memory from unrounded values (the run's daily rows, decisions and the market), never from the CSV files.

Series. NAV_d for every session of the run; r_d = NAV_d / NAV_{d-1} - 1, so the first return (2009-01-02) includes the first entry relative to initial NAV (protocol line 157). r_BIL_TR,d from the theoretical T of BIL (section 3), not from B0's NAV. e_d = r_d - r_BIL_TR,d (protocol line 46).

Periods. `full` 2009-01-01 to 2022-12-31, `development` 2009-2013, `walk_forward` 2014-2022, blocks `2014-2016`, `2017-2019`, `2020-2022`, and each calendar year 2009-2022. A period's returns are those of its sessions within the run; its base NAV is the NAV at the close of the last run session before it. All periods end no later than 2022-12-30; `metrics.py` raises `ValueError` otherwise.

Per period:

| Key | Definition |
|---|---|
| n_returns | number of daily returns |
| total_return | NAV_end / NAV_base - 1 |
| cagr | (NAV_end / NAV_base)^(252 / n_returns) - 1 |
| volatility | sqrt(252) × std(r, ddof = 1) |
| mean_excess | 252 × mean(e) |
| sharpe_bil | sqrt(252) × mean(e) / std(e, ddof = 1); `null` when std(e) = 0 |
| utility | 252 × mean(e) - 1.5 × 252 × var(e, ddof = 1) (protocol line 151) |
| max_drawdown | min over the period of NAV_d / max(NAV_base, NAV up to d) - 1 |
| decisions | number of decisions whose execution session lies in the period |
| turnover | Σ over those decisions of one-way turnover (Σ trade notional / NAV at the decision close); also `turnover_annual` = turnover × 252 / n_returns |
| costs_usd | Σ trade costs of those decisions |
| cost_ratio | Σ over those decisions of costs_usd / NAV at the decision close: a sum of relative costs, not the exact loss of compound return |
| mean_cash_usd, mean_bil, mean_cash_plus_bil, mean_receivables | session means of USD cash, BIL value, their sum and unpaid receivables, each divided by NAV |
| mean_risky, mean_group.<G>, mean_weight.<T> | session means of actual risky value, value per group and per risky ETF, divided by NAV |
| max_group.<G>, max_weight.<T> | maxima of the same actual shares, disclosing drift beyond the 50% and 25% target caps (protocol line 73) |
| mean_target_risky | mean of Σ risky target weights over the period's decisions |

All years are complete, so a partial-year total return does not arise in N3. Numbers that are undefined are `null`, never NaN or infinity.

## 7. Report (`python -m alpha_lab report RUN_DIR... --root PROJECT`)

A Run with purpose `N3 benchmark report` and `candidate_ids` B0, B1, B2, B3, REF_SPY. Before computing anything it requires, failing the Run with `ValueError` otherwise:

1. Exactly five run directories inside `data/runs`, whose frozen providers are B0, B1, B2, B3 and REF_SPY, each once.
2. Each directory passes `provenance.verify` and holds the nine benchmark files.
3. In the journal, the directory's run_id has exactly one `started` and one terminal record; the terminal status is `completed`; both records have `dirty_tree` false and a non-null `git_sha`; `output_paths` equals `["data/runs/<run_id>"]`; `data_sha256` equals the SHA-256 of the directory's `manifest.json`; the `started` record's `config_sha256` equals the hash of its `config`, and that config agrees with `config.json` in provider, version, scenario, window, decision sessions and initial cash.
4. `invariants.json` has `passed` true.
5. All five share the approved manifest hash (`VINTAGE_MANIFEST_SHA256`, in `config.json` and the manifest metadata), the scenario, `start_session`, `end_session` and `initial_cash`; each provider version equals the current registry version and each `metrics.json` has the current `schema_version`.

Output in `data/reports/<run_id>/`: `benchmarks.json` (canonical JSON of the five metrics documents in the order B0, B1, B2, B3, REF_SPY, plus the common window and scenario) and `benchmarks.md` (deterministic Markdown tables of the published metrics). Neither file contains a run_id, timestamp or path. Provenance goes into the manifest metadata: for each benchmark its run_id and run manifest SHA-256, plus the environment and the report's run_id. The terminal record's `data_sha256` is the SHA-256 of the report manifest.

Reproducibility comparison: a repeated benchmark run and a repeated report are compared by their manifest `files` dictionaries (per-file SHA-256), not by the manifest bytes, which contain run identifiers.

## 8. Registered runs

Environment: the locked environment of the N2 runs, `../n1-data/.venv/Scripts/python` relative to the N3 worktree root, with `PYTHONPATH=src` of the N3 worktree. The approved vintage is copied into the N3 worktree's `data/derived/` (excluded from Git) and checked by `provenance.verify` and the manifest hash before the first run.

Sequence, each step on a clean tree, with the new journal lines committed before the next step:

1. `simulate` for B0, B1, B2, B3, REF_SPY with `--start 2008-12-31 --end 2022-12-30`.
2. `report` over the five run directories.
3. Repeats of the five runs, each with `--parent` set to its first run, then a repeat of the report with `--parent` set to the first report.
4. Comparison of the manifest `files` dictionaries for all six pairs.

Any `failed` or `invariants_failed` run stays in the journal; its cause is fixed and the run is repeated with `--parent`, and the report lists it.

## 9. Publication

`docs/n3/N3_REPORT.md` publishes the report tables for 2009-2022 only: `full`, `development`, `walk_forward`, the three blocks and the annual rows, for all five benchmarks, with the run ids, git SHAs, the reproducibility comparison and invariant results. It publishes nothing after 2022-12-30, no candidate comparisons (no ΔU, bootstrap or regressions) and no H1/H2 values. It discloses realized volatility and cash shares rather than assuming equal risk (protocol line 87), the drift maxima beyond the caps, that REF_SPY has no risk controls, and the data limitations of D016-D020.

## 10. Tests

TDD, synthetic markets in `tmp_path` under `no_network`, as in N2:

- Section 2: one test per rejection rule (event on a dropped session, payment on a dropped session, payment recomputed for k onto a missing session, numpy scalars accepted, bool rejected, initial cash 0, negative, NaN, infinity) and exit codes 0/3 for `simulate` and `audit`.
- Features: T across a split and a dividend on the same session; sigma and covariance against direct NumPy formulas; warm-up of 252 and 253 closes; zero sigma; asymmetric and non-PSD matrices.
- Portfolio and benchmarks: the hand-computed cases of section 4; B3 with an empty, partial and full selection; REF_SPY with a single decision.
- Metrics: hand-computed NAV series for every key, including zero variance, period bases, drawdown from the base NAV and cost ratio.
- Runs and report: nine files for benchmark runs, seven for test runs; determinism; candidate_ids; every report rejection in section 7; identical report files for repeated inputs.
- Real vintage (skipped when absent): the vintage loads under 2.1; all five providers return valid weights at 2008-12-31 and 2022-11-30.

## 11. Documents

D022 in DECISIONS.md; EXECUTION_MODEL.md (sections 1, 2 and 5); docs/n3/N3_REPORT.md; README.md, STATUS.md, docs/REPRODUCIBILITY.md and experiments/README.md. English, in the style of the documentation edition (docs/DOCUMENTATION_EDITION.md): factual, with protocol line references, no account of how the work was organized.
