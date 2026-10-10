# N4 report: hypotheses H1 and H2, registered runs and permitted diagnostics

Date: 8 October 2026. Branch `claude/n4-hypotheses`, merged into `main` through PR #1 on 8 October 2026 (see the integration receipt at the end of this document). The sections between this header and the receipt describe the state before that merge and are retained as historical evidence.

## Purpose and boundaries

N4 implements the six configurations of the [research protocol](../../RESEARCH_PROTOCOL.md), section 7, as weight providers: H1_252_3, H1_252_4, H1_126_3 and H1_126_4 (momentum relative to BIL, with lookback 252 or 126 sessions and 3 or 4 selected tickers), and H2_4of6 and H2_5of6 (a persistence filter over six calendar months, with the thresholds 4 of 6 and 5 of 6, applied to the selections of the H1 parent H1_252_3). It records their causal signals, registers one run per configuration on the approved vintage, verifies the six runs with a journaled report run, and repeats every run and the report. The design is in [the N4 specification](../superpowers/specs/2026-10-08-n4-hypotheses-design.md); the interpretations that the protocol leaves open, the viewing restriction, the run procedure and the status of the configurations are recorded in [D023](../../DECISIONS.md); the mechanics are described in [EXECUTION_MODEL.md](../../EXECUTION_MODEL.md).

N4 does not produce a result on whether any configuration adds value:

- No return, risk, utility, drawdown or USD-cost result of H1/H2 is computed for publication or published. The runs freeze no `metrics.json`, and the section 11 metrics of H1/H2 are first computed by the N5 code (D023, items 6 and 10).
- No configuration is compared with another, with B0-B3 or with REF_SPY. No ΔU, bootstrap, Holm adjustment or regression is computed. The adaptive policy P_A1 and the walk-forward selection belong to N5.
- The scenarios of protocol section 12 (the cost and delay grid and the two diagnostic variants of H1_252_3) are not run. They belong to N6.
- Nothing after 2022-12-30 is computed, and the reserved period remains closed.

What N4 publishes is the evidence that the six runs completed, passed the seven financial invariants and reproduce with identical result-file hashes, together with the diagnostics permitted by D023, item 6, copied from a frozen report file.

## Vintage, environment and commands

Vintage: `data/derived/20261006T172442-80ef993493` (corrected, with `corrections.json`; D019, approved by D020), manifest SHA-256 `f89346107cf7da6ca052693d188b8a576a08d42024c86865b0a42a63b1d294f2`. Window 2008-12-31 to 2022-12-30; the first decision is at the close of 2008-12-31 and is executed at the open of 2009-01-02. There are 168 decisions, the last XNYS session of each month from December 2008 to November 2022. Main scenario: cost 0.001 per side, lag 1, reserve 0.01, proxy payment lag 10 calendar days, then the first eligible session; initial cash 100000. Environment manifest SHA-256 `5226dc9b0f21363873eb9a8420891733bbad1bc6c536262a3341eead520ce773`, the value journaled by every N4 record, as by the N3 runs.

Commands as executed, from the root of the branch's working copy (a Git worktree of the project, which reaches the project's environment through a relative path):

```bash
PYTHONPATH=src ../../.venv/Scripts/python -m alpha_lab simulate data/derived/20261006T172442-80ef993493 --provider NAME --start 2008-12-31 --end 2022-12-30 --root .
PYTHONPATH=src ../../.venv/Scripts/python -m alpha_lab hypothesis-report --runs <six run dirs> --root .
```

`NAME` took the six values H1_252_3, H1_252_4, H1_126_3, H1_126_4, H2_4of6 and H2_5of6, and `<six run dirs>` stands for the six directories `data/runs/<run id>` of the first runs listed below. Each repeat of a run adds `--parent <run id of the first run>`, and the repeat of the report adds `--parent 20261008T174328-e5860d5cf2`. The journal lines of each step were committed on a clean tree before the next step. The subject lines of the repeat commits use the word "rerun"; they denote the repeats with `--parent`, not reruns after a bug fix. The project-root form of the commands (`.venv/Scripts/python`, after the branch is merged) has not been executed. The directories `data/runs` and `data/reports` and the vintage copy in `data/derived` of the working copy are not in Git.

## Registered runs

All fourteen records below are `completed`, without quality warnings. The report accepts only runs with `dirty_tree` false and a non-null `git_sha` (D023, item 7). The manifest column is the SHA-256 of `manifest.json` of the run or report directory, the value journaled as `data_sha256` of the terminal record.

First runs (no parent):

| configuration | run id | git SHA at start | journal commit | manifest SHA-256 |
|---|---|---|---|---|
| H1_252_3 | 20261008T174218-4053e6ea58 | 353196a | ae629c4 | `af258aa451a1224990ac7f56862b7e2c8cd3dbde136ed026f6f1108624dd2ae3` |
| H1_252_4 | 20261008T174253-cbb9ce2219 | ae629c4 | 23a157c | `f494128756a28d9c65571b9b0a15f7b5734da93bda4ed3530b6ecdcf11c4653f` |
| H1_126_3 | 20261008T174300-8531bbf3ae | 23a157c | 2d9f24a | `62da8876b78ffcedd8a7091230a356436c5a474f86440654fcdf962ce3cc6205` |
| H1_126_4 | 20261008T174303-337a7c2114 | 2d9f24a | 73501bc | `f39ba6caac4c8337a32514fa8a0964da2423d3ebc5ab8de565d21d8d5b0cf48b` |
| H2_4of6 | 20261008T174309-3f0ab95aeb | 73501bc | f857975 | `2cea0ed11b01d3747c897e337476507a91973c43f31e3d6c4a06790fba3a4cea` |
| H2_5of6 | 20261008T174315-44f030c165 | f857975 | b938f40 | `dc68b43134a7447c0875d54d8f87e2f823facbfb6ef27f0de2687f8d6be6cbe7` |

First report (over the six first runs; no parent):

| configuration | run id | git SHA at start | journal commit | manifest SHA-256 |
|---|---|---|---|---|
| six configurations | 20261008T174328-e5860d5cf2 | b938f40 | 6498f44 | `48008786ff018e83fc839b245b8891d7e2c004360c07008244973786182e17b4` |

Repeats (each with the first run of the same configuration as parent):

| configuration | run id | parent | git SHA at start | journal commit | manifest SHA-256 |
|---|---|---|---|---|---|
| H1_252_3 | 20261008T174340-dfb6a1c558 | 20261008T174218-4053e6ea58 | 6498f44 | 6244b39 | `825aa005d7d84c0c409c8af994aeb65c02ae3c087c18f0e9d7c26fa902f43c2a` |
| H1_252_4 | 20261008T174343-bda6d756d5 | 20261008T174253-cbb9ce2219 | 6244b39 | 85cf34a | `af3828edf7a94ce39675258ce9180033d6b3e938e9786930016e382cc1474ee6` |
| H1_126_3 | 20261008T174347-8fc8ed2441 | 20261008T174300-8531bbf3ae | 85cf34a | 3d17051 | `2d17187eb3afea33929ba413c5d3a023a237605db56c94f73284453c77a63385` |
| H1_126_4 | 20261008T174355-8d6580f98d | 20261008T174303-337a7c2114 | 3d17051 | 52d5daf | `9e776e7fdb9d197aa872c6c8a72125a65f136fd0b3dca8a7819dc303dc1c8153` |
| H2_4of6 | 20261008T174358-e5b5bd731e | 20261008T174309-3f0ab95aeb | 52d5daf | 9504121 | `7a7b7992138b9a9c0f6d3b6cbb6ebfe4e313aec5a96ae6d8560ab3e6448863e1` |
| H2_5of6 | 20261008T174405-a2006cbd61 | 20261008T174315-44f030c165 | 9504121 | d0de40d | `9fa36b5a508fc6dbb83fabc116b3a794907dbf4275450f44af3da64ae819d2af` |

Repeat report (over the six repeat directories; parent: the first report):

| configuration | run id | parent | git SHA at start | journal commit | manifest SHA-256 |
|---|---|---|---|---|---|
| six configurations | 20261008T174417-e6157ee9c6 | 20261008T174328-e5860d5cf2 | d0de40d | f921b41 | `2d779872473d34ed84f9e9a0843a80201ed5af1feeac07f8aa6f1b1398bbf9de` |

Every run and report started from the same `src` tree, `b2791448e4888b9a8cc3677458b3bd5a28afd9ae`, which is also the `src` tree of commit `bbf7640`. The journal holds 94 records at the end of the repeat report; 28 of them are N4 records (a `started` and a terminal record for each of the 14 runs and reports).

## Reproducibility

For each of the six configurations, the `files` dictionary of `manifest.json` (9 files) is identical in the first run and in its repeat, so every result file has the same SHA-256. The `files` dictionaries of the two reports (2 files, `hypotheses.json` and `hypotheses.md`) are identical. All seven pairs are equal. The comparison verified both manifests with `provenance.verify` and compared their `files` dictionaries; the script is in [docs/REPRODUCIBILITY.md](../REPRODUCIBILITY.md). The manifest bytes differ by run identifiers in the metadata and, for the report manifests, by the referenced run ids and run manifest hashes (D022, item 16).

## Verification before the runs

The full test suite passed before the first run: 602 passed, 0 skipped, at commit `bbf7640`, in an isolated copy made with `git archive` and the approved vintage. The suite includes the two tests on the real vintage (the N3 regression over 45 benchmark file hashes and the independent recomputation of the target weights of the six configurations at all 168 decisions), which evaluate target weights and benchmark files and compute no H1/H2 account (D023, item 10). The `src` tree of `bbf7640` equals the `src` tree of every N4 record. The commit before the first run, `353196a`, updated STATUS.md only.

## Invariants and counts

The flags below are checked over the whole run, so they have no annual breakdown. The first report accepted the six runs under the checks of D023, item 7, which include all seven invariant flags.

| configuration | passed | cash_non_negative | nav_identity | cash_flow | split_quantity_only | receivable_conservation | execution_timing | costs | split_events | proxy_payouts |
|---|---|---|---|---|---|---|---|---|---|---|
| H1_252_3 | True | True | True | True | True | True | True | True | 1 | 0 |
| H1_252_4 | True | True | True | True | True | True | True | True | 1 | 0 |
| H1_126_3 | True | True | True | True | True | True | True | True | 1 | 0 |
| H1_126_4 | True | True | True | True | True | True | True | True | 1 | 0 |
| H2_4of6 | True | True | True | True | True | True | True | True | 1 | 0 |
| H2_5of6 | True | True | True | True | True | True | True | True | 1 | 0 |

The columns are the seven checks of the engine (D021) and the overall flag `passed`; `split_events` and `proxy_payouts` are counts. The full-period and annual counts follow in the next section.

## Permitted diagnostics

The tables below are copied without change from `data/reports/20261008T174328-e5860d5cf2/hypotheses.md`, the frozen file of the first report run `20261008T174328-e5860d5cf2` (SHA-256 of the file: `f2d57e985ea2d29fbb30a762a6ea9cc38e8f74a0b194ef63995d6a7526ed174d`). The repeat report `20261008T174417-e6157ee9c6` has an identical `files` dictionary. The directory is not in Git, so the tables here are the published record. Only the diagnostics permitted by D023, item 6 are included; every other quantity of the runs was excluded from viewing and is not described here.

Definitions (D023, item 6):

- Attribution. A decision belongs to the year of its execution session (D022, item 12), an order to the year of its execution session, a trade to the year of its session, and a payout to the year of its ex-dividend session, counted with its status at the end of the run. `full` is the union of the years 2009-2022 (2009-01-01 to 2022-12-31), so an item dated 2008 belongs to no period.
- Notation. `-` marks a `selected k` bucket above the configuration's K (for H2, the parent's K = 3); it is not a zero count. `n/a` would mark a zero denominator or a minimum or maximum without values; it does not occur in the tables.
- Counts. Orders are counted by final status; the reasons `no_valid_open`, `insufficient_cash`, `fractional_quantity` and `exceeds_position` are counted for partial and cancelled orders. Payouts are counted by status at the end of the run (`paid`, `receivable`) and by basis (`actual`, `proxy`).
- Selection. `mean_eligible` is the mean number of tickers per decision with a strictly positive score, `mean_selected` the mean number selected; `selected 0` to `selected 4` count decisions by the number of selected tickers; `empty_selections` counts decisions with none. For H2 the selection columns and the scale columns are those of the parent H1_252_3, because H2 rows carry the parent's `scale`.
- Targets. `mean_risky` and `max_risky` are the mean and maximum of the summed risky target weight per decision; `mean_bil` is the mean target BIL weight. `max_etf` is the maximum target weight of any single ETF and covers the nine risky ETFs only; BIL is reported through `mean_bil`. `max_group` is the maximum target weight of any group. `scale_binding` is the number of decisions where the volatility target binds (`scale` < 1), `scale_binding_share` its share of decisions, and `mean_scale` the mean `scale`.
- Trading. `turnover_sum` and `turnover_mean` are the sum and the mean per decision of one-way turnover, with the denominator NAV at the decision close (D022, item 11; D023, item 1). `cost_ratio` is the scenario cost (0.001) times `turnover_sum`, which equals the definition of D022, item 13 up to floating-point rounding. `min_buy_fill` is the minimum `buy_fill` over decisions and `partial_fills` the number of decisions with `buy_fill` < 1.
- H2 filter. `pass_share` is the share of parent-selected ticker-decisions that pass the filter; `removal_decisions` is the number of decisions where the filter removes at least one ticker; `mean_removed_share` is the mean, over decisions with a positive parent risky target weight, of the share of that weight removed by the filter.
- Ticker tables. Period `full` only: the share of decisions in which a ticker is selected, and for H2 the share of the ticker's parent selections that pass the filter.

Turnover and `cost_ratio`, with the count of decisions and the mean target risky weight, are the only section 11 table items of H1/H2 published here. None of them is a return, risk, utility, drawdown or USD-cost measure.

### Full period: counts

| configuration | decisions | orders filled | orders partial | orders cancelled | partial no_valid_open | partial insufficient_cash | partial fractional_quantity | partial exceeds_position | cancelled no_valid_open | cancelled insufficient_cash | cancelled fractional_quantity | cancelled exceeds_position | trades buy | trades sell | payouts paid | payouts receivable | payouts actual | payouts proxy |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| H1_252_3 | 168 | 712 | 7 | 0 | 0 | 4 | 3 | 0 | 0 | 0 | 0 | 0 | 387 | 332 | 375 | 0 | 375 | 0 |
| H1_252_4 | 168 | 828 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 450 | 378 | 452 | 0 | 452 | 0 |
| H1_126_3 | 168 | 744 | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 388 | 359 | 354 | 0 | 354 | 0 |
| H1_126_4 | 168 | 880 | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 457 | 426 | 425 | 0 | 425 | 0 |
| H2_4of6 | 168 | 561 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 276 | 285 | 271 | 0 | 271 | 0 |
| H2_5of6 | 168 | 348 | 5 | 0 | 0 | 0 | 5 | 0 | 0 | 0 | 0 | 0 | 177 | 176 | 167 | 0 | 167 | 0 |

### Full period: selection

| configuration | mean_eligible | mean_selected | selected 0 | selected 1 | selected 2 | selected 3 | selected 4 | empty_selections |
|---|---|---|---|---|---|---|---|---|
| H1_252_3 | 5.77 | 2.86 | 0 | 9 | 6 | 153 | - | 0 |
| H1_252_4 | 5.77 | 3.67 | 0 | 9 | 6 | 16 | 137 | 0 |
| H1_126_3 | 5.60 | 2.80 | 6 | 3 | 9 | 150 | - | 6 |
| H1_126_4 | 5.60 | 3.62 | 6 | 3 | 9 | 13 | 137 | 6 |
| H2_4of6 | 5.77 | 2.86 | 0 | 9 | 6 | 153 | - | 0 |
| H2_5of6 | 5.77 | 2.86 | 0 | 9 | 6 | 153 | - | 0 |

### Full period: targets

| configuration | mean_risky | max_risky | mean_bil | max_etf | max_group | scale_binding | scale_binding_share | mean_scale |
|---|---|---|---|---|---|---|---|---|
| H1_252_3 | 63.79% | 75.00% | 36.21% | 25.00% | 50.00% | 6 | 3.57% | 0.9969 |
| H1_252_4 | 72.26% | 92.29% | 27.74% | 25.00% | 50.00% | 8 | 4.76% | 0.9964 |
| H1_126_3 | 62.25% | 75.00% | 37.75% | 25.00% | 50.00% | 8 | 4.76% | 0.9879 |
| H1_126_4 | 69.79% | 93.08% | 30.21% | 25.00% | 50.00% | 18 | 10.71% | 0.9838 |
| H2_4of6 | 43.79% | 75.00% | 56.21% | 25.00% | 50.00% | 6 | 3.57% | 0.9969 |
| H2_5of6 | 22.01% | 74.07% | 77.99% | 25.00% | 50.00% | 6 | 3.57% | 0.9969 |

### Full period: trading

| configuration | turnover_sum | turnover_mean | cost_ratio | min_buy_fill | partial_fills |
|---|---|---|---|---|---|
| H1_252_3 | 55.3562 | 0.3295 | 0.0554 | 0.9975 | 1 |
| H1_252_4 | 45.9509 | 0.2735 | 0.0460 | 1.0000 | 0 |
| H1_126_3 | 78.8426 | 0.4693 | 0.0788 | 0.9829 | 1 |
| H1_126_4 | 72.9070 | 0.4340 | 0.0729 | 0.9844 | 1 |
| H2_4of6 | 61.2594 | 0.3646 | 0.0613 | 1.0000 | 0 |
| H2_5of6 | 46.6491 | 0.2777 | 0.0466 | 1.0000 | 0 |

### Full period: H2 filter

| configuration | pass_share | removal_decisions | mean_removed_share |
|---|---|---|---|
| H2_4of6 | 69.17% | 94 | 32.10% |
| H2_5of6 | 34.79% | 153 | 65.84% |

### Full period: ticker selection frequency

| configuration | DBC | EEM | EFA | GLD | HYG | IEF | LQD | SPY | TLT |
|---|---|---|---|---|---|---|---|---|---|
| H1_252_3 | 18.45% | 10.71% | 22.62% | 22.02% | 47.02% | 40.48% | 42.26% | 51.19% | 30.95% |
| H1_252_4 | 23.21% | 17.86% | 31.55% | 33.33% | 56.55% | 48.21% | 59.52% | 59.52% | 37.50% |
| H1_126_3 | 22.02% | 16.07% | 26.19% | 21.43% | 42.86% | 35.12% | 44.05% | 43.45% | 29.17% |
| H1_126_4 | 26.79% | 27.38% | 33.93% | 32.14% | 50.00% | 39.88% | 56.55% | 55.95% | 39.29% |
| H2_4of6 | 18.45% | 10.71% | 22.62% | 22.02% | 47.02% | 40.48% | 42.26% | 51.19% | 30.95% |
| H2_5of6 | 18.45% | 10.71% | 22.62% | 22.02% | 47.02% | 40.48% | 42.26% | 51.19% | 30.95% |

### Full period: H2 ticker pass share

| configuration | DBC | EEM | EFA | GLD | HYG | IEF | LQD | SPY | TLT |
|---|---|---|---|---|---|---|---|---|---|
| H2_4of6 | 67.74% | 61.11% | 73.68% | 62.16% | 88.61% | 42.65% | 78.87% | 81.40% | 46.15% |
| H2_5of6 | 41.94% | 22.22% | 39.47% | 16.22% | 48.10% | 13.24% | 45.07% | 51.16% | 11.54% |

### Annual counts

| year | configuration | decisions | orders filled | orders partial | orders cancelled | partial no_valid_open | partial insufficient_cash | partial fractional_quantity | partial exceeds_position | cancelled no_valid_open | cancelled insufficient_cash | cancelled fractional_quantity | cancelled exceeds_position | trades buy | trades sell | payouts paid | payouts receivable | payouts actual | payouts proxy |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2009 | H1_252_3 | 12 | 51 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 32 | 19 | 39 | 0 | 39 | 0 |
| 2009 | H1_252_4 | 12 | 50 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 30 | 20 | 41 | 0 | 41 | 0 |
| 2009 | H1_126_3 | 12 | 57 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 32 | 25 | 35 | 0 | 35 | 0 |
| 2009 | H1_126_4 | 12 | 63 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 37 | 26 | 40 | 0 | 40 | 0 |
| 2009 | H2_4of6 | 12 | 32 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 19 | 13 | 23 | 0 | 23 | 0 |
| 2009 | H2_5of6 | 12 | 15 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 8 | 7 | 17 | 0 | 17 | 0 |
| 2010 | H1_252_3 | 12 | 52 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 22 | 30 | 24 | 0 | 24 | 0 |
| 2010 | H1_252_4 | 12 | 64 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 24 | 40 | 30 | 0 | 30 | 0 |
| 2010 | H1_126_3 | 12 | 55 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 30 | 25 | 26 | 0 | 26 | 0 |
| 2010 | H1_126_4 | 12 | 70 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 36 | 34 | 35 | 0 | 35 | 0 |
| 2010 | H2_4of6 | 12 | 50 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 23 | 27 | 22 | 0 | 22 | 0 |
| 2010 | H2_5of6 | 12 | 27 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 12 | 15 | 7 | 0 | 7 | 0 |
| 2011 | H1_252_3 | 12 | 56 | 4 | 0 | 0 | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 33 | 27 | 20 | 0 | 20 | 0 |
| 2011 | H1_252_4 | 12 | 67 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 36 | 31 | 29 | 0 | 29 | 0 |
| 2011 | H1_126_3 | 12 | 56 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 28 | 28 | 22 | 0 | 22 | 0 |
| 2011 | H1_126_4 | 12 | 66 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 30 | 36 | 27 | 0 | 27 | 0 |
| 2011 | H2_4of6 | 12 | 50 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 26 | 24 | 19 | 0 | 19 | 0 |
| 2011 | H2_5of6 | 12 | 36 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 20 | 16 | 10 | 0 | 10 | 0 |
| 2012 | H1_252_3 | 12 | 52 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 26 | 26 | 34 | 0 | 34 | 0 |
| 2012 | H1_252_4 | 12 | 58 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 32 | 26 | 43 | 0 | 43 | 0 |
| 2012 | H1_126_3 | 12 | 56 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 30 | 26 | 33 | 0 | 33 | 0 |
| 2012 | H1_126_4 | 12 | 63 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 32 | 31 | 41 | 0 | 41 | 0 |
| 2012 | H2_4of6 | 12 | 43 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 21 | 22 | 23 | 0 | 23 | 0 |
| 2012 | H2_5of6 | 12 | 29 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 15 | 14 | 14 | 0 | 14 | 0 |
| 2013 | H1_252_3 | 12 | 52 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 29 | 23 | 24 | 0 | 24 | 0 |
| 2013 | H1_252_4 | 12 | 59 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 38 | 21 | 28 | 0 | 28 | 0 |
| 2013 | H1_126_3 | 12 | 48 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 23 | 25 | 15 | 0 | 15 | 0 |
| 2013 | H1_126_4 | 12 | 58 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 35 | 23 | 20 | 0 | 20 | 0 |
| 2013 | H2_4of6 | 12 | 39 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 19 | 20 | 14 | 0 | 14 | 0 |
| 2013 | H2_5of6 | 12 | 26 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 13 | 13 | 7 | 0 | 7 | 0 |
| 2014 | H1_252_3 | 12 | 48 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 26 | 22 | 21 | 0 | 21 | 0 |
| 2014 | H1_252_4 | 12 | 56 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 33 | 23 | 28 | 0 | 28 | 0 |
| 2014 | H1_126_3 | 12 | 50 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 25 | 25 | 27 | 0 | 27 | 0 |
| 2014 | H1_126_4 | 12 | 65 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 33 | 32 | 33 | 0 | 33 | 0 |
| 2014 | H2_4of6 | 12 | 49 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 27 | 22 | 20 | 0 | 20 | 0 |
| 2014 | H2_5of6 | 12 | 31 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 17 | 14 | 10 | 0 | 10 | 0 |
| 2015 | H1_252_3 | 12 | 50 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 28 | 22 | 30 | 0 | 30 | 0 |
| 2015 | H1_252_4 | 12 | 58 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 31 | 27 | 38 | 0 | 38 | 0 |
| 2015 | H1_126_3 | 12 | 56 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 28 | 28 | 24 | 0 | 24 | 0 |
| 2015 | H1_126_4 | 12 | 60 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 32 | 28 | 29 | 0 | 29 | 0 |
| 2015 | H2_4of6 | 12 | 28 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 13 | 15 | 12 | 0 | 12 | 0 |
| 2015 | H2_5of6 | 12 | 15 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 7 | 8 | 5 | 0 | 5 | 0 |
| 2016 | H1_252_3 | 12 | 51 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 27 | 24 | 28 | 0 | 28 | 0 |
| 2016 | H1_252_4 | 12 | 62 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 31 | 31 | 32 | 0 | 32 | 0 |
| 2016 | H1_126_3 | 12 | 51 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 29 | 22 | 32 | 0 | 32 | 0 |
| 2016 | H1_126_4 | 12 | 64 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 36 | 28 | 36 | 0 | 36 | 0 |
| 2016 | H2_4of6 | 12 | 23 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 10 | 13 | 13 | 0 | 13 | 0 |
| 2016 | H2_5of6 | 12 | 15 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 7 | 8 | 8 | 0 | 8 | 0 |
| 2017 | H1_252_3 | 12 | 53 | 1 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 26 | 28 | 30 | 0 | 30 | 0 |
| 2017 | H1_252_4 | 12 | 63 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 38 | 25 | 34 | 0 | 34 | 0 |
| 2017 | H1_126_3 | 12 | 57 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 30 | 27 | 26 | 0 | 26 | 0 |
| 2017 | H1_126_4 | 12 | 67 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 37 | 30 | 32 | 0 | 32 | 0 |
| 2017 | H2_4of6 | 12 | 45 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 21 | 24 | 29 | 0 | 29 | 0 |
| 2017 | H2_5of6 | 12 | 38 | 1 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 18 | 21 | 26 | 0 | 26 | 0 |
| 2018 | H1_252_3 | 12 | 49 | 2 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 27 | 24 | 21 | 0 | 21 | 0 |
| 2018 | H1_252_4 | 12 | 59 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 32 | 27 | 25 | 0 | 25 | 0 |
| 2018 | H1_126_3 | 12 | 53 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 25 | 28 | 21 | 0 | 21 | 0 |
| 2018 | H1_126_4 | 12 | 59 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 27 | 32 | 22 | 0 | 22 | 0 |
| 2018 | H2_4of6 | 12 | 41 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 18 | 23 | 16 | 0 | 16 | 0 |
| 2018 | H2_5of6 | 12 | 23 | 4 | 0 | 0 | 0 | 4 | 0 | 0 | 0 | 0 | 0 | 11 | 16 | 15 | 0 | 15 | 0 |
| 2019 | H1_252_3 | 12 | 50 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 29 | 21 | 42 | 0 | 42 | 0 |
| 2019 | H1_252_4 | 12 | 59 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 28 | 31 | 49 | 0 | 49 | 0 |
| 2019 | H1_126_3 | 12 | 49 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 25 | 24 | 40 | 0 | 40 | 0 |
| 2019 | H1_126_4 | 12 | 61 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 29 | 32 | 45 | 0 | 45 | 0 |
| 2019 | H2_4of6 | 12 | 47 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 24 | 23 | 35 | 0 | 35 | 0 |
| 2019 | H2_5of6 | 12 | 19 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 13 | 6 | 19 | 0 | 19 | 0 |
| 2020 | H1_252_3 | 12 | 54 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 29 | 25 | 31 | 0 | 31 | 0 |
| 2020 | H1_252_4 | 12 | 65 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 37 | 28 | 39 | 0 | 39 | 0 |
| 2020 | H1_126_3 | 12 | 60 | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 30 | 33 | 26 | 0 | 26 | 0 |
| 2020 | H1_126_4 | 12 | 71 | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 40 | 34 | 33 | 0 | 33 | 0 |
| 2020 | H2_4of6 | 12 | 42 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 19 | 23 | 25 | 0 | 25 | 0 |
| 2020 | H2_5of6 | 12 | 22 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 10 | 12 | 15 | 0 | 15 | 0 |
| 2021 | H1_252_3 | 12 | 56 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 31 | 25 | 21 | 0 | 21 | 0 |
| 2021 | H1_252_4 | 12 | 64 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 36 | 28 | 22 | 0 | 22 | 0 |
| 2021 | H1_126_3 | 12 | 58 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 33 | 25 | 16 | 0 | 16 | 0 |
| 2021 | H1_126_4 | 12 | 72 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 33 | 39 | 21 | 0 | 21 | 0 |
| 2021 | H2_4of6 | 12 | 45 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 25 | 20 | 12 | 0 | 12 | 0 |
| 2021 | H2_5of6 | 12 | 35 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 16 | 19 | 6 | 0 | 6 | 0 |
| 2022 | H1_252_3 | 12 | 38 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 22 | 16 | 10 | 0 | 10 | 0 |
| 2022 | H1_252_4 | 12 | 44 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 24 | 20 | 14 | 0 | 14 | 0 |
| 2022 | H1_126_3 | 12 | 38 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 20 | 18 | 11 | 0 | 11 | 0 |
| 2022 | H1_126_4 | 12 | 41 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 20 | 21 | 11 | 0 | 11 | 0 |
| 2022 | H2_4of6 | 12 | 27 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 11 | 16 | 8 | 0 | 8 | 0 |
| 2022 | H2_5of6 | 12 | 17 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 10 | 7 | 8 | 0 | 8 | 0 |

### Annual selection

| year | configuration | mean_eligible | mean_selected | selected 0 | selected 1 | selected 2 | selected 3 | selected 4 | empty_selections |
|---|---|---|---|---|---|---|---|---|---|
| 2009 | H1_252_3 | 4.08 | 2.75 | 0 | 0 | 3 | 9 | - | 0 |
| 2009 | H1_252_4 | 4.08 | 3.25 | 0 | 0 | 3 | 3 | 6 | 0 |
| 2009 | H1_126_3 | 5.92 | 2.92 | 0 | 0 | 1 | 11 | - | 0 |
| 2009 | H1_126_4 | 5.92 | 3.75 | 0 | 0 | 1 | 1 | 10 | 0 |
| 2009 | H2_4of6 | 4.08 | 2.75 | 0 | 0 | 3 | 9 | - | 0 |
| 2009 | H2_5of6 | 4.08 | 2.75 | 0 | 0 | 3 | 9 | - | 0 |
| 2010 | H1_252_3 | 7.75 | 3.00 | 0 | 0 | 0 | 12 | - | 0 |
| 2010 | H1_252_4 | 7.75 | 4.00 | 0 | 0 | 0 | 0 | 12 | 0 |
| 2010 | H1_126_3 | 6.75 | 3.00 | 0 | 0 | 0 | 12 | - | 0 |
| 2010 | H1_126_4 | 6.75 | 4.00 | 0 | 0 | 0 | 0 | 12 | 0 |
| 2010 | H2_4of6 | 7.75 | 3.00 | 0 | 0 | 0 | 12 | - | 0 |
| 2010 | H2_5of6 | 7.75 | 3.00 | 0 | 0 | 0 | 12 | - | 0 |
| 2011 | H1_252_3 | 8.08 | 3.00 | 0 | 0 | 0 | 12 | - | 0 |
| 2011 | H1_252_4 | 8.08 | 4.00 | 0 | 0 | 0 | 0 | 12 | 0 |
| 2011 | H1_126_3 | 6.33 | 3.00 | 0 | 0 | 0 | 12 | - | 0 |
| 2011 | H1_126_4 | 6.33 | 4.00 | 0 | 0 | 0 | 0 | 12 | 0 |
| 2011 | H2_4of6 | 8.08 | 3.00 | 0 | 0 | 0 | 12 | - | 0 |
| 2011 | H2_5of6 | 8.08 | 3.00 | 0 | 0 | 0 | 12 | - | 0 |
| 2012 | H1_252_3 | 6.42 | 3.00 | 0 | 0 | 0 | 12 | - | 0 |
| 2012 | H1_252_4 | 6.42 | 4.00 | 0 | 0 | 0 | 0 | 12 | 0 |
| 2012 | H1_126_3 | 6.17 | 3.00 | 0 | 0 | 0 | 12 | - | 0 |
| 2012 | H1_126_4 | 6.17 | 4.00 | 0 | 0 | 0 | 0 | 12 | 0 |
| 2012 | H2_4of6 | 6.42 | 3.00 | 0 | 0 | 0 | 12 | - | 0 |
| 2012 | H2_5of6 | 6.42 | 3.00 | 0 | 0 | 0 | 12 | - | 0 |
| 2013 | H1_252_3 | 5.67 | 3.00 | 0 | 0 | 0 | 12 | - | 0 |
| 2013 | H1_252_4 | 5.67 | 3.83 | 0 | 0 | 0 | 2 | 10 | 0 |
| 2013 | H1_126_3 | 4.33 | 2.67 | 0 | 1 | 2 | 9 | - | 0 |
| 2013 | H1_126_4 | 4.33 | 3.25 | 0 | 1 | 2 | 2 | 7 | 0 |
| 2013 | H2_4of6 | 5.67 | 3.00 | 0 | 0 | 0 | 12 | - | 0 |
| 2013 | H2_5of6 | 5.67 | 3.00 | 0 | 0 | 0 | 12 | - | 0 |
| 2014 | H1_252_3 | 5.33 | 3.00 | 0 | 0 | 0 | 12 | - | 0 |
| 2014 | H1_252_4 | 5.33 | 3.67 | 0 | 0 | 0 | 4 | 8 | 0 |
| 2014 | H1_126_3 | 6.75 | 3.00 | 0 | 0 | 0 | 12 | - | 0 |
| 2014 | H1_126_4 | 6.75 | 4.00 | 0 | 0 | 0 | 0 | 12 | 0 |
| 2014 | H2_4of6 | 5.33 | 3.00 | 0 | 0 | 0 | 12 | - | 0 |
| 2014 | H2_5of6 | 5.33 | 3.00 | 0 | 0 | 0 | 12 | - | 0 |
| 2015 | H1_252_3 | 5.00 | 3.00 | 0 | 0 | 0 | 12 | - | 0 |
| 2015 | H1_252_4 | 5.00 | 3.75 | 0 | 0 | 0 | 3 | 9 | 0 |
| 2015 | H1_126_3 | 4.33 | 2.67 | 1 | 0 | 1 | 10 | - | 1 |
| 2015 | H1_126_4 | 4.33 | 3.33 | 1 | 0 | 1 | 2 | 8 | 1 |
| 2015 | H2_4of6 | 5.00 | 3.00 | 0 | 0 | 0 | 12 | - | 0 |
| 2015 | H2_5of6 | 5.00 | 3.00 | 0 | 0 | 0 | 12 | - | 0 |
| 2016 | H1_252_3 | 5.00 | 2.67 | 0 | 2 | 0 | 10 | - | 0 |
| 2016 | H1_252_4 | 5.00 | 3.42 | 0 | 2 | 0 | 1 | 9 | 0 |
| 2016 | H1_126_3 | 6.67 | 3.00 | 0 | 0 | 0 | 12 | - | 0 |
| 2016 | H1_126_4 | 6.67 | 3.83 | 0 | 0 | 0 | 2 | 10 | 0 |
| 2016 | H2_4of6 | 5.00 | 2.67 | 0 | 2 | 0 | 10 | - | 0 |
| 2016 | H2_5of6 | 5.00 | 2.67 | 0 | 2 | 0 | 10 | - | 0 |
| 2017 | H1_252_3 | 6.33 | 3.00 | 0 | 0 | 0 | 12 | - | 0 |
| 2017 | H1_252_4 | 6.33 | 4.00 | 0 | 0 | 0 | 0 | 12 | 0 |
| 2017 | H1_126_3 | 6.42 | 3.00 | 0 | 0 | 0 | 12 | - | 0 |
| 2017 | H1_126_4 | 6.42 | 4.00 | 0 | 0 | 0 | 0 | 12 | 0 |
| 2017 | H2_4of6 | 6.33 | 3.00 | 0 | 0 | 0 | 12 | - | 0 |
| 2017 | H2_5of6 | 6.33 | 3.00 | 0 | 0 | 0 | 12 | - | 0 |
| 2018 | H1_252_3 | 5.83 | 2.92 | 0 | 0 | 1 | 11 | - | 0 |
| 2018 | H1_252_4 | 5.83 | 3.67 | 0 | 0 | 1 | 2 | 9 | 0 |
| 2018 | H1_126_3 | 4.50 | 2.58 | 1 | 0 | 2 | 9 | - | 1 |
| 2018 | H1_126_4 | 4.50 | 3.33 | 1 | 0 | 2 | 0 | 9 | 1 |
| 2018 | H2_4of6 | 5.83 | 2.92 | 0 | 0 | 1 | 11 | - | 0 |
| 2018 | H2_5of6 | 5.83 | 2.92 | 0 | 0 | 1 | 11 | - | 0 |
| 2019 | H1_252_3 | 5.17 | 2.75 | 0 | 1 | 1 | 10 | - | 0 |
| 2019 | H1_252_4 | 5.17 | 3.58 | 0 | 1 | 1 | 0 | 10 | 0 |
| 2019 | H1_126_3 | 6.00 | 2.83 | 0 | 1 | 0 | 11 | - | 0 |
| 2019 | H1_126_4 | 6.00 | 3.58 | 0 | 1 | 0 | 2 | 9 | 0 |
| 2019 | H2_4of6 | 5.17 | 2.75 | 0 | 1 | 1 | 10 | - | 0 |
| 2019 | H2_5of6 | 5.17 | 2.75 | 0 | 1 | 1 | 10 | - | 0 |
| 2020 | H1_252_3 | 6.75 | 3.00 | 0 | 0 | 0 | 12 | - | 0 |
| 2020 | H1_252_4 | 6.75 | 4.00 | 0 | 0 | 0 | 0 | 12 | 0 |
| 2020 | H1_126_3 | 6.17 | 3.00 | 0 | 0 | 0 | 12 | - | 0 |
| 2020 | H1_126_4 | 6.17 | 3.92 | 0 | 0 | 0 | 1 | 11 | 0 |
| 2020 | H2_4of6 | 6.75 | 3.00 | 0 | 0 | 0 | 12 | - | 0 |
| 2020 | H2_5of6 | 6.75 | 3.00 | 0 | 0 | 0 | 12 | - | 0 |
| 2021 | H1_252_3 | 6.83 | 3.00 | 0 | 0 | 0 | 12 | - | 0 |
| 2021 | H1_252_4 | 6.83 | 4.00 | 0 | 0 | 0 | 0 | 12 | 0 |
| 2021 | H1_126_3 | 6.33 | 3.00 | 0 | 0 | 0 | 12 | - | 0 |
| 2021 | H1_126_4 | 6.33 | 4.00 | 0 | 0 | 0 | 0 | 12 | 0 |
| 2021 | H2_4of6 | 6.83 | 3.00 | 0 | 0 | 0 | 12 | - | 0 |
| 2021 | H2_5of6 | 6.83 | 3.00 | 0 | 0 | 0 | 12 | - | 0 |
| 2022 | H1_252_3 | 2.50 | 1.92 | 0 | 6 | 1 | 5 | - | 0 |
| 2022 | H1_252_4 | 2.50 | 2.25 | 0 | 6 | 1 | 1 | 4 | 0 |
| 2022 | H1_126_3 | 1.75 | 1.58 | 4 | 1 | 3 | 4 | - | 4 |
| 2022 | H1_126_4 | 1.75 | 1.67 | 4 | 1 | 3 | 3 | 1 | 4 |
| 2022 | H2_4of6 | 2.50 | 1.92 | 0 | 6 | 1 | 5 | - | 0 |
| 2022 | H2_5of6 | 2.50 | 1.92 | 0 | 6 | 1 | 5 | - | 0 |

### Annual targets

| year | configuration | mean_risky | max_risky | mean_bil | max_etf | max_group | scale_binding | scale_binding_share | mean_scale |
|---|---|---|---|---|---|---|---|---|---|
| 2009 | H1_252_3 | 62.38% | 74.82% | 37.62% | 25.00% | 50.00% | 3 | 25.00% | 0.9648 |
| 2009 | H1_252_4 | 67.66% | 86.97% | 32.34% | 25.00% | 50.00% | 0 | 0.00% | 1.0000 |
| 2009 | H1_126_3 | 56.02% | 69.73% | 43.98% | 25.00% | 50.00% | 6 | 50.00% | 0.8341 |
| 2009 | H1_126_4 | 61.80% | 80.94% | 38.20% | 25.00% | 50.00% | 9 | 75.00% | 0.8177 |
| 2009 | H2_4of6 | 31.26% | 74.82% | 68.74% | 25.00% | 50.00% | 3 | 25.00% | 0.9648 |
| 2009 | H2_5of6 | 12.32% | 47.84% | 87.68% | 25.00% | 47.84% | 3 | 25.00% | 0.9648 |
| 2010 | H1_252_3 | 67.74% | 75.00% | 32.26% | 25.00% | 50.00% | 1 | 8.33% | 0.9979 |
| 2010 | H1_252_4 | 79.61% | 90.31% | 20.39% | 25.00% | 50.00% | 2 | 16.67% | 0.9832 |
| 2010 | H1_126_3 | 69.46% | 75.00% | 30.54% | 25.00% | 50.00% | 0 | 0.00% | 1.0000 |
| 2010 | H1_126_4 | 79.30% | 86.74% | 20.70% | 25.00% | 50.00% | 1 | 8.33% | 0.9950 |
| 2010 | H2_4of6 | 62.30% | 71.59% | 37.70% | 25.00% | 50.00% | 1 | 8.33% | 0.9979 |
| 2010 | H2_5of6 | 19.43% | 68.06% | 80.57% | 25.00% | 50.00% | 1 | 8.33% | 0.9979 |
| 2011 | H1_252_3 | 68.55% | 75.00% | 31.45% | 25.00% | 50.00% | 0 | 0.00% | 1.0000 |
| 2011 | H1_252_4 | 78.48% | 87.44% | 21.52% | 25.00% | 50.00% | 0 | 0.00% | 1.0000 |
| 2011 | H1_126_3 | 66.70% | 75.00% | 33.30% | 25.00% | 50.00% | 0 | 0.00% | 1.0000 |
| 2011 | H1_126_4 | 77.94% | 85.54% | 22.06% | 25.00% | 48.25% | 1 | 8.33% | 0.9988 |
| 2011 | H2_4of6 | 54.81% | 70.45% | 45.19% | 25.00% | 50.00% | 0 | 0.00% | 1.0000 |
| 2011 | H2_5of6 | 31.52% | 67.38% | 68.48% | 25.00% | 42.29% | 0 | 0.00% | 1.0000 |
| 2012 | H1_252_3 | 66.34% | 75.00% | 33.66% | 25.00% | 50.00% | 1 | 8.33% | 0.9986 |
| 2012 | H1_252_4 | 82.43% | 88.93% | 17.57% | 25.00% | 50.00% | 0 | 0.00% | 1.0000 |
| 2012 | H1_126_3 | 67.60% | 75.00% | 32.40% | 25.00% | 50.00% | 1 | 8.33% | 0.9986 |
| 2012 | H1_126_4 | 81.35% | 89.29% | 18.65% | 25.00% | 50.00% | 0 | 0.00% | 1.0000 |
| 2012 | H2_4of6 | 49.18% | 68.38% | 50.82% | 25.00% | 50.00% | 1 | 8.33% | 0.9986 |
| 2012 | H2_5of6 | 28.02% | 50.00% | 71.98% | 25.00% | 50.00% | 1 | 8.33% | 0.9986 |
| 2013 | H1_252_3 | 69.74% | 75.00% | 30.26% | 25.00% | 50.00% | 0 | 0.00% | 1.0000 |
| 2013 | H1_252_4 | 76.62% | 85.81% | 23.38% | 25.00% | 50.00% | 0 | 0.00% | 1.0000 |
| 2013 | H1_126_3 | 61.91% | 75.00% | 38.09% | 25.00% | 50.00% | 0 | 0.00% | 1.0000 |
| 2013 | H1_126_4 | 64.85% | 78.68% | 35.15% | 25.00% | 50.00% | 0 | 0.00% | 1.0000 |
| 2013 | H2_4of6 | 38.94% | 69.68% | 61.06% | 25.00% | 44.68% | 0 | 0.00% | 1.0000 |
| 2013 | H2_5of6 | 21.44% | 40.12% | 78.56% | 25.00% | 25.00% | 0 | 0.00% | 1.0000 |
| 2014 | H1_252_3 | 63.38% | 69.95% | 36.62% | 25.00% | 50.00% | 0 | 0.00% | 1.0000 |
| 2014 | H1_252_4 | 68.75% | 81.13% | 31.25% | 25.00% | 50.00% | 0 | 0.00% | 1.0000 |
| 2014 | H1_126_3 | 64.82% | 69.21% | 35.18% | 25.00% | 50.00% | 0 | 0.00% | 1.0000 |
| 2014 | H1_126_4 | 76.02% | 83.78% | 23.98% | 25.00% | 50.00% | 0 | 0.00% | 1.0000 |
| 2014 | H2_4of6 | 61.29% | 69.95% | 38.71% | 25.00% | 50.00% | 0 | 0.00% | 1.0000 |
| 2014 | H2_5of6 | 29.97% | 63.08% | 70.03% | 25.00% | 38.08% | 0 | 0.00% | 1.0000 |
| 2015 | H1_252_3 | 68.62% | 71.37% | 31.38% | 25.00% | 49.44% | 0 | 0.00% | 1.0000 |
| 2015 | H1_252_4 | 75.40% | 84.84% | 24.60% | 25.00% | 43.33% | 0 | 0.00% | 1.0000 |
| 2015 | H1_126_3 | 61.24% | 75.00% | 38.76% | 25.00% | 50.00% | 0 | 0.00% | 1.0000 |
| 2015 | H1_126_4 | 66.17% | 84.13% | 33.83% | 25.00% | 50.00% | 0 | 0.00% | 1.0000 |
| 2015 | H2_4of6 | 24.85% | 67.65% | 75.15% | 25.00% | 46.37% | 0 | 0.00% | 1.0000 |
| 2015 | H2_5of6 | 9.18% | 46.36% | 90.82% | 25.00% | 25.00% | 0 | 0.00% | 1.0000 |
| 2016 | H1_252_3 | 60.73% | 72.43% | 39.27% | 25.00% | 50.00% | 0 | 0.00% | 1.0000 |
| 2016 | H1_252_4 | 68.55% | 86.96% | 31.45% | 25.00% | 50.00% | 0 | 0.00% | 1.0000 |
| 2016 | H1_126_3 | 65.21% | 70.63% | 34.79% | 25.00% | 50.00% | 0 | 0.00% | 1.0000 |
| 2016 | H1_126_4 | 74.36% | 78.96% | 25.64% | 25.00% | 50.00% | 0 | 0.00% | 1.0000 |
| 2016 | H2_4of6 | 22.78% | 72.43% | 77.22% | 25.00% | 50.00% | 0 | 0.00% | 1.0000 |
| 2016 | H2_5of6 | 13.82% | 47.43% | 86.18% | 25.00% | 25.00% | 0 | 0.00% | 1.0000 |
| 2017 | H1_252_3 | 67.23% | 75.00% | 32.77% | 25.00% | 50.00% | 0 | 0.00% | 1.0000 |
| 2017 | H1_252_4 | 78.12% | 88.76% | 21.88% | 25.00% | 50.00% | 0 | 0.00% | 1.0000 |
| 2017 | H1_126_3 | 65.61% | 75.00% | 34.39% | 25.00% | 50.00% | 0 | 0.00% | 1.0000 |
| 2017 | H1_126_4 | 77.84% | 89.21% | 22.16% | 25.00% | 50.00% | 0 | 0.00% | 1.0000 |
| 2017 | H2_4of6 | 62.18% | 74.07% | 37.82% | 25.00% | 50.00% | 0 | 0.00% | 1.0000 |
| 2017 | H2_5of6 | 49.48% | 74.07% | 50.52% | 25.00% | 50.00% | 0 | 0.00% | 1.0000 |
| 2018 | H1_252_3 | 58.99% | 74.67% | 41.01% | 25.00% | 50.00% | 1 | 8.33% | 0.9950 |
| 2018 | H1_252_4 | 67.64% | 75.00% | 32.36% | 25.00% | 50.00% | 0 | 0.00% | 1.0000 |
| 2018 | H1_126_3 | 59.27% | 75.00% | 40.73% | 25.00% | 50.00% | 0 | 0.00% | 1.0000 |
| 2018 | H1_126_4 | 63.20% | 93.08% | 36.80% | 25.00% | 50.00% | 0 | 0.00% | 1.0000 |
| 2018 | H2_4of6 | 38.00% | 54.58% | 62.00% | 25.00% | 50.00% | 1 | 8.33% | 0.9950 |
| 2018 | H2_5of6 | 19.60% | 36.11% | 80.40% | 25.00% | 36.11% | 1 | 8.33% | 0.9950 |
| 2019 | H1_252_3 | 64.52% | 75.00% | 35.48% | 25.00% | 50.00% | 0 | 0.00% | 1.0000 |
| 2019 | H1_252_4 | 75.38% | 89.26% | 24.62% | 25.00% | 50.00% | 0 | 0.00% | 1.0000 |
| 2019 | H1_126_3 | 65.77% | 75.00% | 34.23% | 25.00% | 50.00% | 0 | 0.00% | 1.0000 |
| 2019 | H1_126_4 | 74.01% | 88.22% | 25.99% | 25.00% | 50.00% | 0 | 0.00% | 1.0000 |
| 2019 | H2_4of6 | 48.76% | 75.00% | 51.24% | 25.00% | 50.00% | 0 | 0.00% | 1.0000 |
| 2019 | H2_5of6 | 14.58% | 25.00% | 85.42% | 25.00% | 25.00% | 0 | 0.00% | 1.0000 |
| 2020 | H1_252_3 | 65.14% | 69.30% | 34.86% | 25.00% | 50.00% | 0 | 0.00% | 1.0000 |
| 2020 | H1_252_4 | 74.34% | 81.88% | 25.66% | 25.00% | 50.00% | 6 | 50.00% | 0.9661 |
| 2020 | H1_126_3 | 64.69% | 70.18% | 35.31% | 25.00% | 50.00% | 1 | 8.33% | 0.9979 |
| 2020 | H1_126_4 | 72.24% | 85.07% | 27.76% | 25.00% | 50.00% | 7 | 58.33% | 0.9622 |
| 2020 | H2_4of6 | 49.44% | 69.30% | 50.56% | 25.00% | 50.00% | 0 | 0.00% | 1.0000 |
| 2020 | H2_5of6 | 21.24% | 43.85% | 78.76% | 25.00% | 43.85% | 0 | 0.00% | 1.0000 |
| 2021 | H1_252_3 | 62.34% | 73.35% | 37.66% | 25.00% | 50.00% | 0 | 0.00% | 1.0000 |
| 2021 | H1_252_4 | 69.74% | 74.96% | 30.26% | 25.00% | 48.19% | 0 | 0.00% | 1.0000 |
| 2021 | H1_126_3 | 66.28% | 75.00% | 33.72% | 25.00% | 50.00% | 0 | 0.00% | 1.0000 |
| 2021 | H1_126_4 | 73.45% | 85.21% | 26.55% | 25.00% | 50.00% | 0 | 0.00% | 1.0000 |
| 2021 | H2_4of6 | 46.88% | 68.07% | 53.12% | 25.00% | 43.07% | 0 | 0.00% | 1.0000 |
| 2021 | H2_5of6 | 27.55% | 61.94% | 72.45% | 25.00% | 43.07% | 0 | 0.00% | 1.0000 |
| 2022 | H1_252_3 | 47.38% | 75.00% | 52.62% | 25.00% | 50.00% | 0 | 0.00% | 1.0000 |
| 2022 | H1_252_4 | 48.89% | 92.29% | 51.11% | 25.00% | 49.50% | 0 | 0.00% | 1.0000 |
| 2022 | H1_126_3 | 36.93% | 73.33% | 63.07% | 25.00% | 48.71% | 0 | 0.00% | 1.0000 |
| 2022 | H1_126_4 | 34.53% | 72.55% | 65.47% | 25.00% | 42.78% | 0 | 0.00% | 1.0000 |
| 2022 | H2_4of6 | 22.39% | 73.80% | 77.61% | 25.00% | 50.00% | 0 | 0.00% | 1.0000 |
| 2022 | H2_5of6 | 9.99% | 25.00% | 90.01% | 25.00% | 25.00% | 0 | 0.00% | 1.0000 |

### Annual trading

| year | configuration | turnover_sum | turnover_mean | cost_ratio | min_buy_fill | partial_fills |
|---|---|---|---|---|---|---|
| 2009 | H1_252_3 | 4.4642 | 0.3720 | 0.0045 | 1.0000 | 0 |
| 2009 | H1_252_4 | 3.0519 | 0.2543 | 0.0031 | 1.0000 | 0 |
| 2009 | H1_126_3 | 6.6364 | 0.5530 | 0.0066 | 1.0000 | 0 |
| 2009 | H1_126_4 | 5.0993 | 0.4249 | 0.0051 | 1.0000 | 0 |
| 2009 | H2_4of6 | 4.3403 | 0.3617 | 0.0043 | 1.0000 | 0 |
| 2009 | H2_5of6 | 2.3939 | 0.1995 | 0.0024 | 1.0000 | 0 |
| 2010 | H1_252_3 | 3.7824 | 0.3152 | 0.0038 | 1.0000 | 0 |
| 2010 | H1_252_4 | 2.8219 | 0.2352 | 0.0028 | 1.0000 | 0 |
| 2010 | H1_126_3 | 5.6357 | 0.4696 | 0.0056 | 1.0000 | 0 |
| 2010 | H1_126_4 | 4.6454 | 0.3871 | 0.0046 | 1.0000 | 0 |
| 2010 | H2_4of6 | 5.4476 | 0.4540 | 0.0054 | 1.0000 | 0 |
| 2010 | H2_5of6 | 6.0080 | 0.5007 | 0.0060 | 1.0000 | 0 |
| 2011 | H1_252_3 | 6.2776 | 0.5231 | 0.0063 | 0.9975 | 1 |
| 2011 | H1_252_4 | 4.1851 | 0.3488 | 0.0042 | 1.0000 | 0 |
| 2011 | H1_126_3 | 5.2755 | 0.4396 | 0.0053 | 1.0000 | 0 |
| 2011 | H1_126_4 | 3.9831 | 0.3319 | 0.0040 | 1.0000 | 0 |
| 2011 | H2_4of6 | 6.2383 | 0.5199 | 0.0062 | 1.0000 | 0 |
| 2011 | H2_5of6 | 4.8947 | 0.4079 | 0.0049 | 1.0000 | 0 |
| 2012 | H1_252_3 | 3.1763 | 0.2647 | 0.0032 | 1.0000 | 0 |
| 2012 | H1_252_4 | 1.2221 | 0.1018 | 0.0012 | 1.0000 | 0 |
| 2012 | H1_126_3 | 4.9809 | 0.4151 | 0.0050 | 1.0000 | 0 |
| 2012 | H1_126_4 | 4.3477 | 0.3623 | 0.0043 | 1.0000 | 0 |
| 2012 | H2_4of6 | 4.5040 | 0.3753 | 0.0045 | 1.0000 | 0 |
| 2012 | H2_5of6 | 4.8524 | 0.4044 | 0.0049 | 1.0000 | 0 |
| 2013 | H1_252_3 | 2.8097 | 0.2341 | 0.0028 | 1.0000 | 0 |
| 2013 | H1_252_4 | 2.8896 | 0.2408 | 0.0029 | 1.0000 | 0 |
| 2013 | H1_126_3 | 5.0685 | 0.4224 | 0.0051 | 1.0000 | 0 |
| 2013 | H1_126_4 | 5.6424 | 0.4702 | 0.0056 | 1.0000 | 0 |
| 2013 | H2_4of6 | 3.9251 | 0.3271 | 0.0039 | 1.0000 | 0 |
| 2013 | H2_5of6 | 2.4535 | 0.2045 | 0.0025 | 1.0000 | 0 |
| 2014 | H1_252_3 | 2.1090 | 0.1757 | 0.0021 | 1.0000 | 0 |
| 2014 | H1_252_4 | 3.0934 | 0.2578 | 0.0031 | 1.0000 | 0 |
| 2014 | H1_126_3 | 3.2535 | 0.2711 | 0.0033 | 1.0000 | 0 |
| 2014 | H1_126_4 | 4.1767 | 0.3481 | 0.0042 | 1.0000 | 0 |
| 2014 | H2_4of6 | 2.0581 | 0.1715 | 0.0021 | 1.0000 | 0 |
| 2014 | H2_5of6 | 3.9613 | 0.3301 | 0.0040 | 1.0000 | 0 |
| 2015 | H1_252_3 | 3.3025 | 0.2752 | 0.0033 | 1.0000 | 0 |
| 2015 | H1_252_4 | 2.6059 | 0.2172 | 0.0026 | 1.0000 | 0 |
| 2015 | H1_126_3 | 8.3040 | 0.6920 | 0.0083 | 1.0000 | 0 |
| 2015 | H1_126_4 | 5.8048 | 0.4837 | 0.0058 | 1.0000 | 0 |
| 2015 | H2_4of6 | 4.3607 | 0.3634 | 0.0044 | 1.0000 | 0 |
| 2015 | H2_5of6 | 3.5962 | 0.2997 | 0.0036 | 1.0000 | 0 |
| 2016 | H1_252_3 | 6.0525 | 0.5044 | 0.0061 | 1.0000 | 0 |
| 2016 | H1_252_4 | 6.4268 | 0.5356 | 0.0064 | 1.0000 | 0 |
| 2016 | H1_126_3 | 3.3190 | 0.2766 | 0.0033 | 1.0000 | 0 |
| 2016 | H1_126_4 | 4.5028 | 0.3752 | 0.0045 | 1.0000 | 0 |
| 2016 | H2_4of6 | 3.6906 | 0.3076 | 0.0037 | 1.0000 | 0 |
| 2016 | H2_5of6 | 2.8579 | 0.2382 | 0.0029 | 1.0000 | 0 |
| 2017 | H1_252_3 | 5.0004 | 0.4167 | 0.0050 | 1.0000 | 0 |
| 2017 | H1_252_4 | 2.8047 | 0.2337 | 0.0028 | 1.0000 | 0 |
| 2017 | H1_126_3 | 6.4404 | 0.5367 | 0.0064 | 1.0000 | 0 |
| 2017 | H1_126_4 | 4.7519 | 0.3960 | 0.0048 | 1.0000 | 0 |
| 2017 | H2_4of6 | 4.4554 | 0.3713 | 0.0045 | 1.0000 | 0 |
| 2017 | H2_5of6 | 4.1137 | 0.3428 | 0.0041 | 1.0000 | 0 |
| 2018 | H1_252_3 | 3.5022 | 0.2918 | 0.0035 | 1.0000 | 0 |
| 2018 | H1_252_4 | 3.1549 | 0.2629 | 0.0032 | 1.0000 | 0 |
| 2018 | H1_126_3 | 6.1745 | 0.5145 | 0.0062 | 1.0000 | 0 |
| 2018 | H1_126_4 | 5.9292 | 0.4941 | 0.0059 | 1.0000 | 0 |
| 2018 | H2_4of6 | 4.3540 | 0.3628 | 0.0044 | 1.0000 | 0 |
| 2018 | H2_5of6 | 2.3315 | 0.1943 | 0.0023 | 1.0000 | 0 |
| 2019 | H1_252_3 | 4.7120 | 0.3927 | 0.0047 | 1.0000 | 0 |
| 2019 | H1_252_4 | 4.3529 | 0.3627 | 0.0044 | 1.0000 | 0 |
| 2019 | H1_126_3 | 5.4358 | 0.4530 | 0.0054 | 1.0000 | 0 |
| 2019 | H1_126_4 | 5.0405 | 0.4200 | 0.0050 | 1.0000 | 0 |
| 2019 | H2_4of6 | 6.9951 | 0.5829 | 0.0070 | 1.0000 | 0 |
| 2019 | H2_5of6 | 0.9972 | 0.0831 | 0.0010 | 1.0000 | 0 |
| 2020 | H1_252_3 | 3.3188 | 0.2766 | 0.0033 | 1.0000 | 0 |
| 2020 | H1_252_4 | 2.5838 | 0.2153 | 0.0026 | 1.0000 | 0 |
| 2020 | H1_126_3 | 7.3914 | 0.6160 | 0.0074 | 0.9829 | 1 |
| 2020 | H1_126_4 | 7.5207 | 0.6267 | 0.0075 | 0.9844 | 1 |
| 2020 | H2_4of6 | 4.0048 | 0.3337 | 0.0040 | 1.0000 | 0 |
| 2020 | H2_5of6 | 2.9100 | 0.2425 | 0.0029 | 1.0000 | 0 |
| 2021 | H1_252_3 | 4.1721 | 0.3477 | 0.0042 | 1.0000 | 0 |
| 2021 | H1_252_4 | 2.7663 | 0.2305 | 0.0028 | 1.0000 | 0 |
| 2021 | H1_126_3 | 5.8946 | 0.4912 | 0.0059 | 1.0000 | 0 |
| 2021 | H1_126_4 | 5.8068 | 0.4839 | 0.0058 | 1.0000 | 0 |
| 2021 | H2_4of6 | 3.8370 | 0.3198 | 0.0038 | 1.0000 | 0 |
| 2021 | H2_5of6 | 4.1852 | 0.3488 | 0.0042 | 1.0000 | 0 |
| 2022 | H1_252_3 | 2.6764 | 0.2230 | 0.0027 | 1.0000 | 0 |
| 2022 | H1_252_4 | 3.9917 | 0.3326 | 0.0040 | 1.0000 | 0 |
| 2022 | H1_126_3 | 5.0322 | 0.4193 | 0.0050 | 1.0000 | 0 |
| 2022 | H1_126_4 | 5.6556 | 0.4713 | 0.0057 | 1.0000 | 0 |
| 2022 | H2_4of6 | 3.0482 | 0.2540 | 0.0030 | 1.0000 | 0 |
| 2022 | H2_5of6 | 1.0936 | 0.0911 | 0.0011 | 1.0000 | 0 |

### Annual H2 filter

| year | configuration | pass_share | removal_decisions | mean_removed_share |
|---|---|---|---|---|
| 2009 | H2_4of6 | 48.48% | 10 | 50.70% |
| 2009 | H2_5of6 | 18.18% | 12 | 82.56% |
| 2010 | H2_4of6 | 91.67% | 2 | 7.92% |
| 2010 | H2_5of6 | 27.78% | 11 | 71.49% |
| 2011 | H2_4of6 | 80.56% | 6 | 19.48% |
| 2011 | H2_5of6 | 47.22% | 9 | 53.78% |
| 2012 | H2_4of6 | 69.44% | 8 | 25.95% |
| 2012 | H2_5of6 | 38.89% | 12 | 58.17% |
| 2013 | H2_4of6 | 58.33% | 11 | 43.66% |
| 2013 | H2_5of6 | 33.33% | 12 | 68.04% |
| 2014 | H2_4of6 | 97.22% | 1 | 3.08% |
| 2014 | H2_5of6 | 47.22% | 10 | 50.91% |
| 2015 | H2_4of6 | 36.11% | 10 | 63.85% |
| 2015 | H2_5of6 | 13.89% | 12 | 86.74% |
| 2016 | H2_4of6 | 37.50% | 11 | 66.80% |
| 2016 | H2_5of6 | 21.88% | 12 | 79.95% |
| 2017 | H2_4of6 | 91.67% | 3 | 7.15% |
| 2017 | H2_5of6 | 72.22% | 6 | 25.99% |
| 2018 | H2_4of6 | 68.57% | 8 | 33.14% |
| 2018 | H2_5of6 | 34.29% | 12 | 64.34% |
| 2019 | H2_4of6 | 75.76% | 6 | 22.32% |
| 2019 | H2_5of6 | 21.21% | 12 | 78.98% |
| 2020 | H2_4of6 | 75.00% | 5 | 23.70% |
| 2020 | H2_5of6 | 30.56% | 12 | 66.93% |
| 2021 | H2_4of6 | 77.78% | 4 | 24.43% |
| 2021 | H2_5of6 | 50.00% | 10 | 54.33% |
| 2022 | H2_4of6 | 47.83% | 9 | 57.28% |
| 2022 | H2_5of6 | 21.74% | 11 | 79.57% |

## Status

The six configurations move from `registered_not_tested` to `computed_not_evaluated` (D023, item 9). The conditions are met: each configuration has a completed registered run on the approved vintage; the first completed N4 report over the final set of six runs, `20261008T174328-e5860d5cf2`, accepted them; the repeat comparison found all seven pairs equal; and no decision under protocol section 13 exists. The journal records no status event; the evidence is the records listed above.

The status means that the configuration has been computed once on the approved vintage and that the computation reproduces. It does not mean that the configuration is useful, rejected or promising, that any performance metric exists, or that any evaluation under protocol sections 11 and 13 has taken place. The sentence of D023, item 9, that gives the status at the time of that entry is historical. The statuses of N5 and N6 are defined at those stages. The attempt accounting required before N5 is in [experiments/README.md](../../experiments/README.md).

## Disclosures and limitations

- No return, risk, utility or USD-cost result of H1/H2 is published. These metrics, and the comparison with B0-B3 and REF_SPY, are first computed by the N5 code.
- Turnover and `cost_ratio`, together with the count of decisions and the mean target risky weight, are the only section 11 table items of H1/H2 published. None of them is a return, risk, utility, drawdown or USD-cost measure.
- The viewing restriction is procedural (D023, item 6). The run directories are storage read only by code. The published aggregates, combined with public prices, permit approximate inference about exposures, and per-decision values, which are not published, would permit approximate monthly returns.
- The restriction does not make 2014-2022 independent history. That period is familiar, and the N3 benchmarks for it are published (protocol section 9; D003). A single run of each configuration on a familiar period is not an out-of-sample test.
- The evaluation window starts in 2009 because of BIL availability and the common warm-up. Most of the 2008 crisis is outside the window, and the material limitation must not be obscured by splicing in index history (protocol line 141).
- Data limitations. The data are not point-in-time, and `available_at` is a modeling assumption. The seven issuer-based corrections have no independent confirmation (D016). The `confirmed_no_distributions` basis for GLD is weaker than a statement that distributions never occurred (D018). The completeness of DBC before 2007-12-17 is not proven by the issuer document (D017). The universe is retrospective. The readiness conditions and their disclosure: D019, D020.
- Costs are modeled at 10 bps per side, not measured, and Open is a modeled price; the runs do not reflect settlement, auction fills, liquidity or brokerage constraints.
- Known limitation of the warm-up check (D023, item 3): `require_warmup` counts history rows, not XNYS sessions, so a vintage with a missing interior session would pass the warm-up and shift the positional windows. The approved vintage holds all 4869 XNYS sessions from 2007-05-30 to 2026-10-05, checked on 8 October 2026 against `normalize.calendar`, so the limitation does not affect these runs. The check is not changed in N4.
- No run or report failed, and none ended `invariants_failed`. No run was repeated after a bug fix; the six repeats and the repeat report are the repeats with `--parent` of the registered procedure. No quantity excluded by D023, item 6 was shown, published or described during the runs, the reports or the preparation of this document.
- These are historical simulations on a retrospective universe. They do not establish an investable track record or an alpha.

## Post-run validation correction and D024 replacement campaign

The final review at `92dd78f` identified numerical error handling in report validation: a non-finite momentum/sigma intermediate could satisfy the relative score comparison, and malformed finite weights or q values could overflow a sum without an item-5 location. Commit `bd71fc0` rejects these cases under the existing rules. D024 records the correction; provider formulas, parameters, versions and tolerances are unchanged.

The corrected patch passed 610 tests, zero skipped, including the approved-vintage checks; the scoped correction review found no open issue. The source and test hashes were checked against that tested patch before committing. Historical input revalidation accepted both original report input sets and reproduced their permitted JSON/Markdown output bytes. The code-only check of the twelve original hypothesis runs found no non-finite derived score in 18,144 signal rows.

The required registered replacement campaign is now complete. All fourteen successful attempts below are `completed` without quality warnings. They share source tree `16ffaf71b09c540cdc094121d040deacdeb3dab9` and environment `5226dc9b0f21363873eb9a8420891733bbad1bc6c536262a3341eead520ce773`, use the approved D020 vintage and the original window/scenario, and start with clean provenance. Every successful hypothesis run passes all seven financial invariants; none freezes `metrics.json`. The journal commit follows each step before the next starts.

| Configuration / report | Role | Run ID | Parent | Source commit | Journal commit |
|---|---|---|---|---|---|
| H1_252_3 | Replacement | `20261008T192727-e5e184b7db` | `20261008T192545-3e84621fc4` | `ad9ec2f` | `65d53f5` |
| H1_252_4 | Replacement | `20261008T192731-0f8d083cb0` | `20261008T174343-bda6d756d5` | `65d53f5` | `b720eba` |
| H1_126_3 | Replacement | `20261008T192734-866ab4b3d7` | `20261008T174347-8fc8ed2441` | `b720eba` | `1ec5a69` |
| H1_126_4 | Replacement | `20261008T192737-45e578bd7c` | `20261008T174355-8d6580f98d` | `1ec5a69` | `71d53cc` |
| H2_4of6 | Replacement | `20261008T192740-f8be1b1ad3` | `20261008T174358-e5b5bd731e` | `71d53cc` | `26bf028` |
| H2_5of6 | Replacement | `20261008T192745-708215766a` | `20261008T174405-a2006cbd61` | `26bf028` | `1348f06` |
| Report | Replacement | `20261008T192750-922eb4e4b7` | `20261008T174417-e6157ee9c6` | `1348f06` | `22b6e31` |
| H1_252_3 | Repeat | `20261008T192753-ecbedef345` | `20261008T192727-e5e184b7db` | `22b6e31` | `0859cfd` |
| H1_252_4 | Repeat | `20261008T192757-ecb65a91e3` | `20261008T192731-0f8d083cb0` | `0859cfd` | `af1bd4d` |
| H1_126_3 | Repeat | `20261008T192801-cd2cf8da52` | `20261008T192734-866ab4b3d7` | `af1bd4d` | `5181bcc` |
| H1_126_4 | Repeat | `20261008T192804-5d7dda6b7e` | `20261008T192737-45e578bd7c` | `5181bcc` | `791c3a0` |
| H2_4of6 | Repeat | `20261008T192808-88c4261f87` | `20261008T192740-f8be1b1ad3` | `791c3a0` | `44f42ce` |
| H2_5of6 | Repeat | `20261008T192812-bf50777423` | `20261008T192745-708215766a` | `44f42ce` | `5d1fc57` |
| Report | Repeat | `20261008T192817-09e39bfc79` | `20261008T192750-922eb4e4b7` | `5d1fc57` | `f927314` |

All fourteen new manifests and their contents verify. The `files` dictionaries match for all seven new pairs and for all seven comparisons with the original repeat set. Thus the historical diagnostics and tables above also describe the replacement campaign without changing any published value. The original source tree, identifiers, hashes and table bytes above remain historical evidence, not rewritten receipts.

Failed launch `20261008T192545-3e84621fc4` (source commit `bd71fc0`, parent `20261008T174340-dfb6a1c558`) failed before loading the vintage: a relative root resolved to an unexpected nested directory. No output artifact was frozen. Its original two records were retained unchanged in the canonical journal and committed as `ad9ec2f`; the first successful replacement uses an absolute root and links to that failure. The commands and absolute-root reproduction form are in [REPRODUCIBILITY.md](../REPRODUCIBILITY.md).

Attempt accounting adds six successful bug-driven calculations, six repeats, two reports and one failed launch; none is a new candidate or an independent experiment. The original 94 journal events remain an unchanged byte prefix; 30 new events bring the total to 124 (58 N4 events). The last successful campaign journal commit is `f927314`. All original immutable artifacts remain retained.

The six configurations retain `computed_not_evaluated`. N4 verification is complete on `claude/n4-hypotheses`, which remains unmerged. No H1/H2 return, risk, utility or USD-cost result was computed or disclosed; the reserved period remains closed. Data remain local in this worktree. N5 is the next research stage.

## Integration receipt: 8 October 2026

The pre-integration state above is retained as historical evidence. [PR #1](https://github.com/oakridge-i/cross-asset-alpha-lab/pull/1) merged the verified head `a98a727` into `main` as `e7f50f40af1881595d202cd948a8ae8ddc1a84f2`. The merge preserves the campaign source and journal commits; its source and tests are identical to the verified head. No new research attempt or performance evaluation was made. Immutable local data remain in the existing N4 worktree.
