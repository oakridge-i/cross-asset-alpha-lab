# N5: walk-forward evaluation, adaptive policy P_A1 and statistics - specification

Date: 9 October 2026. Status: approved by the project owner on 9 October 2026; the corrections of sections 15 and 16 were acknowledged the same day, and the interpretations are recorded as D025 in DECISIONS.md. Nothing in this document is implemented. Basis: RESEARCH_PROTOCOL.md sections 9 to 13 and 14; docs/MASTER_PLAN.md section 5 (N5: "Complete available selection log, consistent metrics and intervals"); decisions D021 to D024, in particular D023 items 6, 10 and 11; docs/n3/N3_REPORT.md; docs/n4/N4_REPORT.md; EXECUTION_MODEL.md; experiments/README.md. Requested by the project owner on 9 October 2026: a specification only, written before any code; implementation belongs to a separate working session on a new branch created from `main`.

The protocol fixes most formulas for N5. Where it is silent, this document proposes an interpretation and marks it **[P#]**. Section 2 lists all of them. Each is to be recorded in DECISIONS.md as D025, with reason, alternative and consequence, after the owner approves or amends it and before any registered N5 run. None adds a tunable parameter or changes a protocol formula; an interpretation that is judged to be a new economic rule requires a protocol version (protocol lines 126 and 196).

## 1. Goal and boundaries

N5 computes, with its own frozen code, the section 11 metrics, intervals and tests for the candidates registered in N4, adds the separate adaptive policy P_A1 of section 10, and publishes one registered evaluation. It is the first stage in which return, risk and utility figures of H1/H2 are computed (D023 items 6, 10 and 11). N5 succeeds when:

1. the benchmarks (B0-B3, REF_SPY) and the six configurations are rerun on the frozen N5 code, and every file that N3 or N4 already froze has the same SHA-256 (D023 item 10);
2. the six configurations and P_A1 have a frozen `metrics.json` produced by the same code as the benchmark metrics;
3. P_A1 has a complete selection log for every walk-forward year 2014 to 2022 (protocol section 10);
4. one registered evaluation report states, for the walk-forward period 2014-2022, the primary comparisons with their utility differences, intervals, p-values and Holm adjustment, the supplementary comparisons, the regressions of section 11 and the selection stability of P_A1;
5. a repeat of every run and of the report reproduces the manifest `files` dictionaries;
6. nothing after 2022-12-30 is computed and the reserved period stays closed.

N5 does not decide any hypothesis. The decisions of protocol section 13 need results that N5 does not produce (cost and delay scenarios, leave-one-class-out, the reserved period) and belong to N6. N5 reports raw quantities and the flags that follow mechanically from them (section 7.3); it uses no verdict wording.

Outside N5: the scenarios of protocol section 12 and `scenario_id` (N6); the reserved period 2023-2025 and the recent segment of 2026, including the selection of P_A1 for 2023 (N6); the section 13 decisions (N6); DSR and PBO (section 6.6); any new candidate, parameter, window, selection rule or data vintage; the deferred N1 item (b). No new dependency: NumPy and pandas, as in `requirements.lock`; there is no SciPy.

Data: only `data/derived/20261006T172442-80ef993493` (D020), manifest SHA-256 `f89346107cf7da6ca052693d188b8a576a08d42024c86865b0a42a63b1d294f2`, through `market.load_market`. The period guard `LAST_OPEN_SESSION = '2022-12-30'` is unchanged. Environment manifest SHA-256 `5226dc9b0f21363873eb9a8420891733bbad1bc6c536262a3341eead520ce773`, the environment of the N3 and N4 runs; a different environment needs a recorded reason.

## 2. Proposed interpretations

| # | Question left open by the protocol | Proposal | Alternative |
|---|---|---|---|
| P1 | Which accounts support the walk-forward statistics (lines 135, 159, 163)? | The slice 2014-01-02 to 2022-12-30 of the continuous accounts that start at 2008-12-31, the form already published for the benchmarks in the N3 report (`walk_forward` block, D022 item 12). | Fresh accounts that start in cash at 2013-12-31 for every candidate. This would change the published N3 `walk_forward` figures and require a second set of benchmark runs. |
| P2 | P_A1 must start in cash (it needs five prior years), so its account differs from the continuous H1_252_3 account at the start of 2014. What does "show fixed H1_252_3 alongside" compare against? | One supplementary run of the provider H1_252_3 over the P_A1 window (start 2013-12-31, in cash), named the P_A1 comparator. It is not a new candidate. | Slice of the continuous account; this biases the comparison by an entry cost and one overnight move. |
| P3 | Period labels of a run that starts in 2014. | P_A1 and its comparator are evaluated on the walk-forward period list only (section 4.2). `full`, `development` and 2009-2013 are not computed for them, because `full` would silently mean 2014-2022. | Reuse the full list and omit empty periods; `full` would be mislabeled. |
| P4 | Year of a decision under P_A1 (line 153: selection fixed before the year's first open). | A decision uses the selection of the calendar year of its execution session. The December decision therefore uses the next year's selection, made at the same close. | Year of the decision session; the January order would then carry the previous year's choice. |
| P5 | What is an "internal two-year segment" and its account (line 149)? | For selection year Y, a segment from the last XNYS session of December Y-3 to the last XNYS session of December Y-1. The account starts in cash at the first, uses the main scenario, and has the default monthly decisions whose execution falls inside the segment (24 decisions, December Y-3 to November Y-1). U is computed from its daily excess returns over the theoretical BIL return, the first return including the entry. The three earlier years are history only. | A segment ending on the selection date plus a final-month decision; it would need a decision whose execution is outside the segment. |
| P6 | "Close" candidates (line 151). | With best_U the maximum, the close set holds every candidate with U >= best_U - 0.001 (floating-point comparison as written); the first member in the order H1_252_3, H1_252_4, H1_126_3, H1_126_4 is selected. | None; the protocol states the rule. |
| P7 | "Numerical reasons" versus "defective inputs" (line 151). | Fallback to H1_252_3, with a warning recorded in the selection log and in the journal `quality_warnings`, applies only when a U is not finite while the data and the checks are complete. A missing session, a failed warm-up, an exception in a provider or a failed invariant in a validation account stops the run. | Fallback for every failure; it would hide defects. |
| P8 | Random numbers for the bootstrap (lines 161, 167). | One `numpy.random.Generator(PCG64(seed))` created afresh for each (n, L) pair; block starts drawn with `integers(0, n, size=(B, ceil(n / L)))`; indices modulo n; each replicate truncated to n observations. All tests that share n and L therefore share the replicates. | One generator for the whole report; results would depend on the order of tests. |
| P9 | Interval type for regressions (line 165). | Normal interval, estimate +/- 1.96 standard errors, from the Newey-West covariance with the finite-sample factor n / (n - k), where k counts every coefficient including the intercept. | Student t with n - k degrees of freedom; SciPy would be needed or the quantile coded by hand. |
| P10 | Monthly returns and class proxies (line 165). | Account monthly return: NAV at the last session of the month over NAV at the last session of the previous month, minus one. BIL: the same from the theoretical total return index. A class proxy is the unweighted mean of the monthly excess returns over BIL of the members of the group in `portfolio.GROUPS` (Equity: SPY, EFA, EEM; Treasury: IEF, TLT; Credit: LQD, HYG; Real: GLD, DBC). | None proposed; line 165 forbids optimizing weights. |
| P11 | DSR and PBO (line 167: optional). | Not implemented. A DSR needs an explicit trial set, and the owner has chosen not to quantify prior views and reviews (G0 in section 3). Revisit only if a trial count is reconstructed. | Implement with the six candidates plus P_A1 as trials. |
| P12 | Journal purposes. | New purposes `N5 benchmark run`, `N5 hypothesis run`, `N5 policy run` and `N5 evaluation report`, so the N3 and N4 reports accept and reject exactly what they accepted and rejected before. | Reuse the old purposes; the N4 report would accept runs with a different file set. |
| P13 | P_A1 inference (line 167: "no confirmatory p value is claimed"). | Report the utility difference of P_A1 against its comparator with the three basic intervals and no p-value, labeled conditional on the realized selections. | Also report a p-value; line 167 says no confirmatory p-value is claimed for the full adaptive procedure, so a p-value would need a label that keeps it from being read as one, and it adds nothing the interval does not. |
| P14 | Where the formal tests are computed. | Only for the walk-forward period. The development period and the full period receive the descriptive metrics but no interval or test, because the protocol names the walk-forward and reserved periods for the regressions (line 165) and for the decision criteria (line 186) and names the development period for no test; this is an interpretation of the staged evaluation, not a quotation covering every test. | Tests on all three periods; more comparisons on the same data without a protocol basis. |

## 3. Preconditions

- G0. Attempt reconstruction (protocol section 14; experiments/README.md). The protocol requires the number of all known manual and programmatic attempts to be reconstructed before N5. The journal supplies the registered ones: six configurations with their repeats and the bug-driven replacement campaign (zero new candidates, D024). The owner's statement of 9 October 2026 supplies the rest, as given: the owner has become familiar with the hypotheses and has reviewed the work a small number of times ("a couple of times"), declines to count views and reviews individually, and approves the specification in its first draft. Recorded consequence: prior exposure to H1/H2 is non-zero and unquantified (it supersedes the statement of 6 October, "Not sure / do not remember", protocol line 130, for the purposes of N5 without editing it); no manual parameter or period change is reported; the multiple-testing caveat stays in every N5 document as unresolved in size. The statement is copied into docs/n5/ATTEMPT_ACCOUNTING.md in milestone M1. This closes G0 for the purpose of computing; it does not quantify the number of trials, so DSR and PBO stay out (P11).
- G1. The owner approves or amends P1 to P14. Approved as drafted on 9 October 2026.
- G2. Access to the N4 artifacts from the primary checkout. The directories `data/runs` and `data/reports` of N4 exist only in the worktree `.worktrees/n4-hypotheses` and are not in Git. Copy, not move, the replacement-campaign runs and reports into the primary `data/`, verify each copy with `provenance.verify` and against the `data_sha256` of its journal record, and keep the worktree untouched. The N4 run directories remain storage read only by code until the evaluation (section 8).
- G3. A new branch created from `main` (for example `claude/n5-evaluation`) and its own worktree, as for N2 to N4. The implementation plan is written after this document is approved, as a separate artifact.
- G4. Reference hashes: the manifests of the five N3 benchmark runs and of the six replacement-campaign runs `20261008T192727-e5e184b7db`, `20261008T192731-0f8d083cb0`, `20261008T192734-866ab4b3d7`, `20261008T192737-45e578bd7c`, `20261008T192740-f8be1b1ad3` and `20261008T192745-708215766a`.

## 4. Runs and metrics

### 4.1 Run set

All runs use the approved vintage and the main scenario (cost 0.001, lag 1, reserve 0.01, proxy 10 calendar days, initial cash 100000).

| Runs | Provider | Window | Purpose |
|---|---|---|---|
| 5 | B0, B1, B2, B3, REF_SPY | 2008-12-31 to 2022-12-30 | `N5 benchmark run` |
| 6 | H1_252_3, H1_252_4, H1_126_3, H1_126_4, H2_4of6, H2_5of6 | 2008-12-31 to 2022-12-30 | `N5 hypothesis run` |
| 1 | P_A1 | 2013-12-31 to 2022-12-30 | `N5 policy run` |
| 1 | H1_252_3 (the P_A1 comparator, P2) | 2013-12-31 to 2022-12-30 | `N5 hypothesis run` |

Thirteen registered runs, one evaluation report, then thirteen repeats and a repeat report (section 9). The providers, their versions and parameters are those of N3 and N4; a provider version changes only for a bug fix that changes its output, with the cascade rule of D023 item 8.

### 4.2 Metrics for hypotheses and the policy

The `hypothesis` kind freezes `metrics.json` in N5 runs, computed in memory from unrounded values by the existing `metrics.compute_metrics` (D022 items 11 to 14), so benchmarks and candidates share one code path. The `policy` kind freezes the same file. The weights of these runs are frozen as in D022 item 15, and `signals.csv` as in D023 item 5.

Period lists: candidates and benchmarks started in 2008 use the existing list `PERIODS` (`full`, `development`, `walk_forward`, the three multi-year blocks and the years 2009 to 2022). P_A1 and its comparator use a walk-forward list: `walk_forward`, `2014-2016`, `2017-2019`, `2020-2022` and the years 2014 to 2022. The list is part of the metrics schema. The existing benchmark `metrics.json` bytes must not change (section 4.3), so the schema version stays 1 unless that requirement forces a change, which would be a defect to report. `metrics.compute_metrics` already takes the period list as a parameter, so the walk-forward list needs no change to the benchmark path. `metrics.py` keeps raising `ValueError` for a session after 2022-12-30.

The run files are nine for a benchmark run, ten for an N5 hypothesis run (the nine files of an N4 run plus `metrics.json`) and eleven for the policy run, which adds `selection.json` (section 5.5).

### 4.3 Identity with the earlier campaigns

For the five benchmarks, all nine files must equal the first N3 runs byte for byte (45 hashes). For each of the six configurations, the nine files of the N4 replacement run must be matched file by file, with `metrics.json` the only addition. `config.json` does not record the purpose, so it is expected to match; the implementer verifies this and reports any difference as a finding before the campaign. A mismatch in a shared file is a defect or a hidden change of code; it stops the campaign (D023 item 10).

## 5. The adaptive policy P_A1

### 5.1 Definition

Candidates: the four H1 configurations in the preference order H1_252_3, H1_252_4, H1_126_3, H1_126_4. The H2 configurations are not candidates (line 147: "H2's parent remains fixed"). H1_252_3, which is the H2 parent, is the first candidate and also the fixed configuration shown alongside the policy (line 147); the comparator run of P2 holds it fixed. The policy has no fitted parameter. Its frozen constants, recorded in the provider's `parameters` and therefore in `config.json`: the candidate order, validation years 2, context years 3, tolerance 0.001, penalty 1.5, and the window rule of P5.

### 5.2 Selection

For each selection year Y from 2014 to 2022, at the close of the last XNYS session s_Y of December Y-1:

1. Five full preceding calendar years Y-5 to Y-1 must exist in the history; this holds for 2014 (2009 to 2013).
2. For each candidate, simulate the validation account of P5 on the history up to s_Y, with the same engine, the same scenario and the same invariant checks. A failed invariant stops the run (P7).
3. Compute U = 252 x mean(e) - 1.5 x 252 x var(e, ddof=1) on the daily excess returns of the segment (line 151). All candidates share the same dates.
4. Apply the rule of P6; apply the fallback rule of P7 only if some U is not finite.

The selection uses information through s_Y only. The actual P_A1 account is one continuous account over 2013-12-31 to 2022-12-30 without reset (line 153): at each monthly decision it applies the target weights of the configuration chosen for the year of its execution session (P4), computed from the history up to that decision. Switching configurations creates ordinary orders and costs. Defaults: monthly decisions, 108 of them (2013-12-31 to 2022-11-30).

The provider obtains the selection by calling `engine.simulate` on the history restricted to sessions <= s_Y. The provider receives a history that ends at the decision session t, which is not earlier than s_Y, so it must truncate that history to s_Y with `Market.history(s_Y)` before simulating; otherwise a selection computed at a later call would use later data. The result for year Y may be cached only inside one provider instance created for one simulation, with a key that includes the year, the vintage manifest hash and s_Y; there is no module-level or process-wide cache, so a selection computed from one market, simulation or test fixture can never be reused for another. The selection must be identical whatever decision first requests it. In the registered run the December close is the first call that needs the year's selection. The provider raises `ValueError` for a decision whose selection year is before 2014 or after 2022, so it cannot be used for the reserved period without a separate freeze (N6).

The 2023 selection is not computed in N5, although only data before 2023 would be used: the first computation of a reserved-period decision is an N6 act under the freeze of protocol section 13.

### 5.3 Training years

The first three of the five years carry no score and no parameter (line 149). They enter only as history that the signals of the validation account use. The consequence to disclose: for 2014 the validation window 2012-2013 lies inside the development period, and the selection log therefore shows candidate utilities for 2012 to 2021 windows.

### 5.4 Stability

For each year Y, resample the 504-odd aligned daily excess returns of the four candidates on the validation segment with joint circular blocks of 63 sessions, 1000 replicates, seed 20261007 (P8), recompute the four U and apply the selection rule of P6 including its tolerance and order, and record the selection frequencies. Each replicate uses the same rule as the actual selection (line 167: "under the same rule"), including the fallback of P7 when a U is not finite; the number of replicates that used the fallback is recorded. This diagnoses selection uncertainty only; it is not an interval for the whole procedure (line 167).

### 5.5 Frozen outputs

`selection.json` (canonical JSON, produced from the same computation as the weights, never recomputed from CSV): per year Y, the selection date, the segment dates, the number of decisions and returns, the four U values, best_U, the close set, the chosen candidate, a fallback flag and warning, and the stability frequencies. `signals.csv` for P_A1 carries the signal rows of the chosen configuration plus the columns `selection_year` and `selected_config`. The selection log is complete: nine rows, one per walk-forward year.

## 6. Inference module (`src/alpha_lab/inference.py`)

Pure functions on NumPy arrays and dates, independent of the engine and the journal, so that each can be tested against a naive reference.

### 6.1 Daily series

Candidate and comparator daily returns r_t = NAV_t / NAV_{t-1} - 1 from `daily.csv`; BIL daily returns from the theoretical total return index of the vintage (D022 item 10); e = r - r_BIL. The aligned series for P1 are the sessions 2014-01-02 to 2022-12-30; the first return's base is the NAV of the last session of 2013. For P_A1 and its comparator the series start at 2014-01-02 with the base NAV of 2013-12-31.

### 6.2 Utility and effect

U as in line 151. DeltaU = U(candidate) - U(comparator). Mean-excess difference = 252 x (mean(e_candidate) - mean(e_comparator)). The inference module reads the frozen `daily.csv`, whose values carry 10 significant digits (D021 item 16), while `metrics.json` is computed from unrounded in-memory values. `metrics.utility` and the inference utility on the same run therefore agree only to rounding; the tolerance is 1e-7 (the rounding error is estimated at about 1e-9). The inference module itself must reproduce a loop implementation on identical inputs to 1e-12.

### 6.3 Paired circular block bootstrap

For L in {21, 63, 126}, B = 10000, seed 20261006, P8. For each replicate, take the same indices from the candidate, comparator and BIL series, compute both utilities and DeltaU*. The basic interval is [2 DeltaU_hat - Q_0.975, 2 DeltaU_hat - Q_0.025] with `numpy.quantile` method `linear`. The one-sided p for H0: DeltaU <= 0 is (1 + count[DeltaU* - DeltaU_hat >= DeltaU_hat]) / (B + 1). The primary length is 63; all three are shown; no length is chosen for a favorable result (line 161). Replicates are processed in chunks; the result must not depend on the chunk size.

### 6.4 Holm

The family has six members at L = 63: H1_252_3, H1_252_4, H1_126_3 and H1_126_4 against B3, and H2_4of6 and H2_5of6 against H1_252_3 (line 163). Holm adjusted p_(i) = max over j <= i of min(1, (m - j + 1) p_(j)), at FWER 5%. H2 against B3 and against B2 are mandatory supplementary comparisons with the same bootstrap, outside the family, and do not replace the parent comparison (line 159). P_A1 is outside the family (P13).

### 6.5 Regressions

Complete months of the walk-forward period only (108 months, January 2014 to December 2022; October 2026 and every incomplete month are excluded). y = R_candidate - R_BIL (P10). Model A: intercept plus the excess return of the primary comparator (B3 for H1, H1_252_3 for H2, the P_A1 comparator for P_A1). Model B: intercept plus the four class proxies; B3 is not added to Model B. OLS; Newey-West covariance with the Bartlett kernel, lag 3, and the factor n / (n - k), where k counts every coefficient including the intercept (P9). Annual alpha = 12 x monthly intercept; its standard error and both interval endpoints are scaled by 12 as well, with a 95% interval. No alpha figure is formed, and the report states the reason, when n < 36, when the design matrix is rank deficient, or when its condition number exceeds 1e8. Alpha and intervals are supplementary descriptions; no unadjusted confirmatory p-value is claimed (line 165).

### 6.6 Not implemented

DSR and PBO (P11). Any alternative class proxies or second price source (line 180). Bootstrap of the entire adaptive procedure (line 167).

## 7. Evaluation report

### 7.1 Command and checks

`python -m alpha_lab evaluate --runs RUN_DIR... --root PROJECT [--parent ATTEMPT] [--expected-sha256 HASH]` is a Run with purpose `N5 evaluation report` and the candidate ids of the thirteen runs. It reuses the shared journal and provenance checks of `report.py` and `hypothesis_report.py`. Before computing anything it requires, failing with `ValueError` that names the rule and the run:

1. exactly thirteen run directories with the providers and windows of section 4.1, each once, each passing `provenance.verify` with the file set of its kind;
2. for each run one `started` and one terminal record, status `completed`, a clean tree, a non-null `git_sha`, and `output_paths`, `data_sha256` and `config_sha256` in agreement with the directory; the purposes of P12;
3. the same `src` tree for all thirteen runs and the report, and the same environment manifest hash;
4. the approved vintage hash, scenario, initial cash and window of each run; all seven invariants and the overall flag `true` in each `invariants.json`;
5. for the five benchmarks and the six configurations the shared-file identity of section 4.3, read from the frozen N3 and N4 manifests, and for the metrics a recomputation of `utility` and `total_return` from `daily.csv` that agrees with `metrics.json` to 1e-7 (CSV rounding, section 6.2);
6. for P_A1, a complete selection log (nine years), with the weights of each decision equal to the chosen configuration's target weights at that decision, read from `weights.csv` and `signals.csv` of the corresponding configuration run (the same computation on the same history), and no fallback without a warning. The report also checks the selection log itself, from the logged utilities: the segment boundaries and selection date of each year are the calendar dates of P5; the logged best_U is the maximum of the four logged U; the close set is exactly the candidates with U >= best_U - 0.001; the chosen candidate is the first member of the close set in the preference order (or H1_252_3 with a recorded fallback); the logged selection year equals the year of the execution session of every decision it governs (P4). The report does not recompute the U values, which needs the validation accounts; that recomputation is the independent real-vintage test of section 12.

### 7.2 Outputs

`evaluation.json` (canonical JSON) and `evaluation.md` in `data/reports/<run_id>/`, built from a whitelist of keys, with no run id, timestamp or path (run ids and manifest hashes go to the report manifest metadata, as in D022 item 16). Contents:

- T1: the metrics of section 11 for the benchmarks, the six configurations, P_A1 and its comparator over the period lists of section 4.2, including the annual breakdown, cash and BIL, receivables, risky weights, groups, decisions, turnover and costs in USD and as a fraction of NAV.
- T2: for the walk-forward period, DeltaU, the mean-excess difference, the three intervals and three p-values, the Holm-adjusted p at 63, for the six family members and the supplementary comparisons; for P_A1 the intervals without p-values.
- T3: annual differences of the sum of daily candidate-minus-comparator returns for 2014 to 2022, the number of positive years and the largest positive share (descriptive; line 186 uses these in N6).
- T4: Models A and B for each candidate, with coefficients, HAC standard errors, annual alpha, interval, months, condition number, and gating reasons.
- T5: the P_A1 selection log and stability frequencies.
- T6: fixed disclosures (section 7.4).

### 7.3 Flags

Per comparison the report states `delta_u >= 0.01` and `mean_excess_difference > 0` (the minimum effect of line 159). It states no result such as "supported", "unsupported" or "candidate", and it makes no comparison that is not listed above. The utility difference against B2 and B0, and H1 against B2, are not computed in N5: B2 and B0 appear side by side in T1, and H1 against B2 is a section 12 scenario (N6). Only H2 against B2 is computed, as the protocol requires it in section 11.

### 7.4 Disclosures

The report states that: all inferential figures are exploratory on familiar history and the adjustment does not restore independence (line 163); 2014-2022 was the research period, and the owner's prior exposure is non-zero and unquantified (G0); each statistic is conditional on the model already selected (line 167); the window excludes most of the 2008 crisis (line 141); the data limitations of D016 to D020 apply; costs are modeled at 10 bps per side; the walk-forward comparison with the continuous accounts differs from P_A1 by the start state (P2); non-significance does not establish the absence of an effect (line 163); and the results do not establish an investable track record.

## 8. Viewing and freeze procedure

N5 ends the viewing restriction of D023 item 6 in a controlled way, because the purpose of the stage is to compute and publish these quantities.

1. Until the code is frozen, the restriction of D023 item 6 still applies to the real N4 run directories. Development uses synthetic markets. Real-vintage tests print only counts, flags and maximum differences.
2. Freeze: the full test suite passes on a clean tree; the whole branch is reviewed; the review finds no critical or important defect; the commit is recorded in STATUS.md and in D025 together with the `src` tree hash.
3. The registered campaign (section 9) runs once. The first evaluation report is the first time a figure is shown. The N5 run directories are read by the report code only until it has completed. Until then the failure messages of hypothesis and policy runs stay withheld as in D023 item 6, so a failed campaign step does not display a value. The same applies to the evaluation report: its errors name the rule and the run (and, where relevant, the year and the comparison) but never a value, a traceback that contains values, or a parsed number; exceptions from reading `daily.csv`, `metrics.json` or `selection.json` and from numerical comparisons are re-raised as value-free `RuntimeError` or `ValueError` with the original suppressed, in the console and in the journal `error` field, as D023 item 7 does for the N4 report.
4. After the first completed report and its repeat, the figures are published as they are. A change to any rule, candidate, window or period after seeing them is a new attempt with its own decision record, not an N5 repeat (line 192). A bug fix follows D023 item 8: all thirteen runs are rerun on the new tree with parent links, followed by a new report, and every attempt is disclosed.
5. The reserved period remains closed. The first N5 report states what was shown and when.

## 9. Registered campaign

Each step on a clean tree, with the new journal lines committed before the next step (D023 item 8):

1. the five benchmark runs, the six configuration runs, the P_A1 run and the P_A1 comparator run;
2. `evaluate` over the thirteen run directories;
3. a repeat of each of the thirteen runs with `--parent` set to its first run, then a repeat of the report over the thirteen repeat directories with `--parent` set to the first report;
4. a comparison of the manifest `files` dictionaries for all fourteen pairs, and of the shared files against the N3 and N4 references (section 4.3).

Commands use an absolute `--root` (the lesson of the failed launch of 8 October). A failed or `invariants_failed` run stays in the journal.

## 10. Status after N5

The status `computed_not_evaluated` is replaced for each of the six configurations by `evaluated_walk_forward` when the conditions of section 1 items 1 to 5 hold and no decision under protocol section 13 exists; for P_A1 the status is `evaluated_walk_forward` under the same conditions. The status states that walk-forward figures exist; it does not state that a configuration is useful or rejected. Statuses of N6 are defined at that stage. As in D023 item 9, the journal gets no new event type; the evidence is the existing records, and STATUS.md, README.md and experiments/README.md state the status with the run ids.

## 11. Attempt accounting

Add to experiments/README.md, as separate lines that are not summed as independent experiments: the seven candidates (six configurations and P_A1); the thirteen N5 runs, their thirteen repeats and the two evaluation reports; zero reruns after bug fixes unless one occurs; the comparator run, which is not a candidate; the in-memory validation simulations of P_A1, which are part of the policy and are not journaled attempts; the real-vintage tests, which are not attempts. The G0 statement and its consequences for the interpretation of the Holm family are stated beside them.

## 12. Tests

Test-driven, on synthetic markets in `tmp_path` under `no_network`, with expected values computed independently of the code under test, as in N2 to N4.

- Inference: utility against a loop implementation; identical candidate and comparator give DeltaU = 0 and p = 1; the circular indices wrap, cover n observations and are identical for equal (n, L); the bootstrap is invariant to the chunk size; a hand-checked tiny case for the interval and the p formula; Holm against a worked example, including ties and the cap at 1; NW covariance against an explicit loop for lag 0 (the HC1 form) and lag 3; OLS recovers known coefficients on noise-free data; rank deficiency, condition number above 1e8 and n < 36 suppress the alpha; the class proxies use exactly the members of `portfolio.GROUPS`; the month return definition, including January 2014 with the December 2013 base.
- Metrics: `metrics.json` of a hypothesis run equals an independent NumPy computation from `daily.csv`; benchmark `metrics.json` bytes unchanged; the walk-forward period list is used for P_A1 and `full` is absent.
- P_A1: causality at engine level (two markets that differ only after s_Y give the same selection for Y and earlier years; a change inside the validation window changes the U values); segment boundaries and the count of 24 decisions; no decision whose execution is after the segment end; the year mapping of P4 (the December decision uses the next year's selection); the close-set rule on constructed utilities, including a value exactly at best_U - 0.001 and the preference order; fallback only for a non-finite U and a stop for a defect; a policy forced to select one configuration in every year yields the same files as the fixed configuration run over the same window except `config.json`, `signals.csv` columns and `selection.json`; stability frequencies sum to one, and replicates that use the fallback are counted separately; the selection for a year is identical whichever decision first requests it, and uses no session after s_Y; a decision with a selection year outside 2014 to 2022 raises `ValueError`; determinism.
- Runs: purposes and file sets of the four kinds; the N4 `hypothesis-report` still rejects an N5 run and accepts an N4-form run with identical output bytes; the N3 report is unchanged.
- Evaluation report: one rejection test per rule of 7.1; the whitelist (a document built from synthetic runs contains no excluded column, run id or path); repeated report gives identical files; shared-file identity detects a modified file.
- Real vintage (skipped when absent; output limited to counts, flags and maximum differences until the freeze): N3 regression of 45 hashes with the new code; shared-file identity of the six configurations against the N4 replacement runs; an independent recomputation of the P_A1 selection for every year using only the weights of the four configurations and NumPy (the validation accounts of the four candidates recomputed from `daily` data of in-memory runs); the metrics identity of section 7.1 item 5.

## 13. Documents

- DECISIONS.md: D025, dated, written before any registered N5 run, with items for P1 to P14, the viewing procedure of section 8, the status of section 10 and the attempt accounting of section 11, each with reason, alternative and consequence. D023 item 6 is superseded explicitly for N5 outputs after the freeze; its text is preserved.
- docs/n5/ATTEMPT_ACCOUNTING.md: G0.
- EXECUTION_MODEL.md: the policy kind, the validation account and the N5 files.
- experiments/README.md: purposes, file sets, campaign sequence, status and the accounting of section 11.
- docs/REPRODUCIBILITY.md: N5 commands in the form verified by the runs.
- docs/n5/N5_REPORT.md: the figures of the evaluation report, copied without change, with the run table and the disclosures; written after the repeat report.
- README.md and STATUS.md: stage N5 and its limitations; no claim of alpha or investment value.
- RESEARCH_PROTOCOL.md and docs/n0/protocol_manifest.json are not edited.

English, in the style of docs/DOCUMENTATION_EDITION.md. The line endings of each edited file are preserved (the repository sets `* -text`; Markdown files are mostly LF, but some contain a few CRLF lines, for example 36 in docs/n4/N4_REPORT.md, and an editor or tool that normalizes the whole file produces a large false diff); `git diff --stat` and `git diff --ignore-cr-at-eol` are checked before each commit.

## 14. Work order and risk

Milestones on one branch, each reviewed before the next: M1, closure of G0 to G4 and the D025 draft; M2, metrics for hypotheses and policy kinds with the identity checks; M3, the inference module; M4, P_A1; M5, the evaluation report; M6, tests on the real vintage, branch review and freeze; M7, the campaign and the report. The campaign cannot be split, because the report requires one `src` tree.

The master plan estimates N5 at 10 to 15 hours. This scope (P_A1 with nested simulations, a bootstrap module, regressions and a new report with its own validation) is larger; the T3 table (descriptive, used by section 13 criteria that belong to N6) could be deferred to N6, but that would amend sections 7.2 and 10 and needs a recorded decision before the freeze. The P_A1 stability bootstrap cannot be deferred inside this specification: protocol line 167 requires stability to be shown, and section 1 item 4 makes it a completion condition.

Known risks: the nested simulations of P_A1 cost about eight times the account-years of a plain run over the same window (four candidates, two years, nine selection years, against nine years) and must be cached per year; the walk-forward statistics rest on 108 months and 2,266 daily returns (252, 252, 252, 251, 251, 252, 253, 252 and 251 for the years 2014 to 2022 by the XNYS calendar) of familiar history; the bootstrap of fixed accounts is conditional on the model already selected.

## 15. Revision note (9 October 2026, same-day re-check)

Corrections made after the owner's approval of the first draft, none of which changes P1 to P14 or any protocol formula:

1. Sections 6.2 and 7.1 item 5: the tolerance between `metrics.json` and the statistics computed from `daily.csv` was 1e-12 and 1e-9; it is 1e-7, because `daily.csv` is rounded to 10 significant digits (D021 item 16) and `metrics.json` is not.
2. Section 5.2: the P_A1 selection must be computed on a history truncated to s_Y whenever it is first requested, must not depend on the first caller, and the provider rejects selection years outside 2014 to 2022.
3. Section 8: failure messages of hypothesis and policy runs stay withheld during the campaign.
4. Section 7.3: the comparisons not computed in N5 (H1 against B2, anything against B0) are named.
5. Section 3 (G0, G1) and P11: the owner's statement and approval of 9 October 2026 are recorded.
6. Section 4.2: it is stated that `compute_metrics` already accepts a period list.
7. Section 13: the claim that Markdown files use CRLF was wrong and is corrected.

## 16. Revision note (independent review)

An independent review, made by a reviewer outside this working session, found three errors, four risks and two documentation notes. All were checked against the protocol and the calendar and all are accepted. The reviewer also checked the bootstrap construction, the Holm adjustment, the Newey-West form, the regression gates, the campaign arithmetic and the numerical line references, and found no mathematical error there.

1. Error, section 5.1: the sentence that H2's parent is not a candidate removed H1_252_3 from the candidate list. Corrected: only the H2 configurations are excluded.
2. Error, section 5.4: the stability bootstrap omitted the fallback of the registered rule; line 167 requires reselection under the same rule. Corrected, with a separate count of replicates that use the fallback.
3. Error, section 14: the walk-forward sample is 2,266 daily returns (checked against the XNYS calendar), not 2,260. The 108 months were correct.
4. Risk, section 5.2: the selection cache now has a defined scope (one provider instance, keyed by year, vintage hash and s_Y; no process-wide cache).
5. Risk, section 7.1: the report now checks the semantics of the selection log from the logged utilities; the recomputation of the utilities remains an independent test.
6. Risk, section 14: the statement that the stability bootstrap could be deferred without other changes was false and is replaced.
7. Risk, section 8: failure messages of the evaluation report itself are now value-free.
8. Note, P13, and 9. note, P14: the justifications no longer overstate the protocol text.
9. Clarifications adopted from the review: k counts the intercept in the Newey-West factor; the alpha standard error and interval scale by 12; the file counts are nine, ten and eleven.
