# N5 report: walk-forward evaluation, adaptive policy P_A1 and statistics

Date: 10 October 2026. Branch `claude/n5-evaluation`, created from `main` at `7a8ba1d`; not merged into `main` at the time of writing.

## Purpose and boundaries

N5 computes, with code frozen before any figure existed, the section 11 metrics of the [research protocol](../../RESEARCH_PROTOCOL.md) for the six configurations registered in N4 (H1_252_3, H1_252_4, H1_126_3, H1_126_4, H2_4of6, H2_5of6), the separate adaptive policy P_A1 of protocol section 10, and the paired bootstrap comparisons, Holm adjustment and regressions for the walk-forward period 2014-2022. The design is in [the N5 specification](../superpowers/specs/2026-10-09-n5-evaluation-design.md); the interpretations that the protocol leaves open (P1 to P14), the viewing and freeze procedure, the registered campaign, the attempt accounting and the status after N5 are recorded in [D025](../../DECISIONS.md); the mechanics are described in [EXECUTION_MODEL.md](../../EXECUTION_MODEL.md).

N5 does not decide any hypothesis (specification section 1; D025, item 20):

- The decisions of protocol section 13 are not made. They need the cost and delay scenarios of protocol section 12, the leave-one-class-out variants and the reserved period, which belong to N6.
- The report states raw quantities and the two flags that follow mechanically from them for each comparison (`delta_u >= 0.01` and `mean_excess_difference > 0`, the minimum effect of protocol line 159; specification section 7.3). It uses no verdict wording.
- DSR and PBO are not implemented (D025, item 11). The utility difference of P_A1 against its comparator has intervals but no p-value (D025, item 13).
- Nothing after 2022-12-30 is computed. The reserved period 2023-2025, the recent segment of 2026 and the P_A1 selection for 2023 remain closed.

This document contains the run table, the reproducibility result, a statement of what was shown and when, the status of the configurations and P_A1, the disclosures, and the complete content of the first evaluation report, copied without change.

## Vintage, environment and commands

Vintage: `data/derived/20261006T172442-80ef993493` (D019, approved by D020), manifest SHA-256 `f89346107cf7da6ca052693d188b8a576a08d42024c86865b0a42a63b1d294f2`. Main scenario: cost 0.001 per side, lag 1, reserve 0.01, proxy payment lag 10 calendar days; initial cash 100000. The five benchmarks and the six configurations use the window 2008-12-31 to 2022-12-30; P_A1 and its comparator (the provider H1_252_3 started in cash on 2013-12-31, labeled `H1_252_3_WF` in the report; D025, item 2) use 2013-12-31 to 2022-12-30. The walk-forward statistics use 2014-01-02 to 2022-12-30 (D025, item 1). Environment manifest SHA-256 `5226dc9b0f21363873eb9a8420891733bbad1bc6c536262a3341eead520ce773`, the environment of the N3 and N4 runs.

Code: the freeze of D025, item 16 is commit `a2453b8`, `src` tree `058c72a492f78aa30f8defecbfab397eee37be96`, recorded in STATUS.md and D025 by commit `db43fb4`. All 28 attempts started from commits whose `src` tree is `058c72a492f78aa30f8defecbfab397eee37be96`; the commits between them change only the experiment journal.

The commands as executed, each with an absolute `--root`, are in [docs/REPRODUCIBILITY.md](../REPRODUCIBILITY.md), section "N5 evaluation runs: executed receipt". Each step ran on a clean tree, and its journal lines were committed before the next step. The directories `data/runs` and `data/reports` are not in Git.

## Registered runs

The 28 attempts below each have a `started` and a `completed` record (56 records); all terminal statuses are `completed`, and no record has `dirty_tree` true or a quality warning. The git SHA is the `git_sha` of the `started` record in the journal; the journal commit is the commit that added the step's two journal lines; the manifest column is the SHA-256 of `manifest.json` of the run or report directory, the value journaled as `data_sha256` of the terminal record.

First runs and first report (no parent):

| step | run | run id | git SHA at start | journal commit | manifest SHA-256 |
|---|---|---|---|---|---|
| 1 | B0 | 20261010T090706-d2f7f13f1c | db43fb4 | 508a467 | `6ad165c69d44a3a3e5e21483b67691a5b7699b0d9e6b50297d955aa290fe604d` |
| 2 | B1 | 20261010T090711-a0a3b5a215 | 508a467 | 5496daa | `d0339f7de599e3307de25503885ac2c5f6fa9c0d6509fa217205c40b49388911` |
| 3 | B2 | 20261010T090717-13ebf67877 | 5496daa | d70aa46 | `d6e15cbe540b4627993a96f6e9ee4ac6587ec7659b8375407d97735090e21c7c` |
| 4 | B3 | 20261010T090724-a39e6c5baa | d70aa46 | afc0251 | `69e60718fa8a4fd4558c5431db7cb91dde039426bb49719f2e28bd48ebf69eb7` |
| 5 | REF_SPY | 20261010T090732-dbf52ab9f8 | afc0251 | 51bcd6d | `5efda0c97d487060297004f7fd68bc0515256f174c88123da88be3c4fc49d693` |
| 6 | H1_252_3 | 20261010T090737-2d652c2127 | 51bcd6d | 3aad7af | `23328446fcb2d2571fa7425ec291500f77d29f76ce741d9c2ff2ae9125c67148` |
| 7 | H1_252_4 | 20261010T090745-899d5a7136 | 3aad7af | be570b5 | `459d3ea8bf0e84ad39c827fbfd89e93a210ab95b05ac2b216f971b97fd56b149` |
| 8 | H1_126_3 | 20261010T090752-9bd003f35b | be570b5 | d753994 | `7c1868d78b958f4d29d6b9a732301cfbde3e08bbd3d73fb95f71c404829a5bb5` |
| 9 | H1_126_4 | 20261010T090800-f78d0ee07b | d753994 | a7226f8 | `acf4a1058676b78153bf4806525e63e037df76444bb5fb6ab4f78a5403490dca` |
| 10 | H2_4of6 | 20261010T090807-af398ad6af | a7226f8 | b30f9c6 | `98d0d9d5e7dec4abfc69e05faa941028c9c1567111cf542f076e63411f0c7a3f` |
| 11 | H2_5of6 | 20261010T090820-2da0674722 | b30f9c6 | 5196b91 | `6acbe6b4d2b696b8be6d328faa1ce5c5d89bd6ae5af233b7f42dc01f8a28a79c` |
| 12 | P_A1 | 20261010T090831-aeca348964 | 5196b91 | 38cf563 | `57d52f36b58e323498fe1c53fe1cc26e84798a4d5b3b6a65fc97fbcaaa78a9a6` |
| 13 | H1_252_3_WF (P_A1 comparator) | 20261010T090913-3da4aae83e | 38cf563 | fc80142 | `43af1ac6868daf7df1a88a65e214cbc280056663658a95697da29edf1774ce27` |
| 14 | evaluation report | 20261010T091002-0c84d411ed | fc80142 | 1b3b9c5 | `1f43f8b7f5aabb94149ae8c210287961a44bcbed4047d2027ce1af0b84c1ef8d` |

Repeats (each with its first run as parent) and repeat report (over the thirteen repeat directories; parent: the first report):

| step | run | run id | parent | git SHA at start | journal commit | manifest SHA-256 |
|---|---|---|---|---|---|---|
| 15 | B0 | 20261010T091043-854900b5a7 | 20261010T090706-d2f7f13f1c | 1b3b9c5 | 15d89fb | `b138316e845db7e02f5b1b9b10451e61d60ca8f79629f97d0b4521c7907f1951` |
| 16 | B1 | 20261010T091046-24f1f2afc7 | 20261010T090711-a0a3b5a215 | 15d89fb | 2eb9411 | `688ec8fab24e2a0fbf837f1e2f91a1bc721a87bac90f9c682464b515d28c4c27` |
| 17 | B2 | 20261010T091048-b223f5975e | 20261010T090717-13ebf67877 | 2eb9411 | 08c8027 | `01a2852638bc582567b360d3471c6d16dda34cca19bf74a5137a39700804ef51` |
| 18 | B3 | 20261010T091051-e79c88c3a0 | 20261010T090724-a39e6c5baa | 08c8027 | a9c5d9d | `4b4100d026f8085096f03ec6436f864e2f975a989a1a59ca8470da2c44486fab` |
| 19 | REF_SPY | 20261010T091054-53e8829580 | 20261010T090732-dbf52ab9f8 | a9c5d9d | f2e591e | `83b9d97d66426a19d8d24fc04ac79fbabf457ba4b70912d5124479c1b7cd4b52` |
| 20 | H1_252_3 | 20261010T091056-79e7a8ffe3 | 20261010T090737-2d652c2127 | f2e591e | 43c059e | `b9b1c014fe340397579dd4868cab2064a195641dbac7841e7b797420cfeb28ad` |
| 21 | H1_252_4 | 20261010T091059-b17280952a | 20261010T090745-899d5a7136 | 43c059e | e08e7a0 | `ef688ecb97fcdfc3cc2af37dd516d491028a935dda5416bee937b901fa3df9aa` |
| 22 | H1_126_3 | 20261010T091102-c4fae89b36 | 20261010T090752-9bd003f35b | e08e7a0 | 74c2eb6 | `c2c8f856cbdd8b019489d870c150be56371a6a0e83fce5038b7b4c5a904225b0` |
| 23 | H1_126_4 | 20261010T091105-5dbd95499e | 20261010T090800-f78d0ee07b | 74c2eb6 | 48308f5 | `52b9094fc5809b48505ebdb167108a5d7ef663e79a48538a1dc395ee4e3a077e` |
| 24 | H2_4of6 | 20261010T091108-629ba2c4f0 | 20261010T090807-af398ad6af | 48308f5 | 874613c | `ccbded05fffdacafb0c1eab52e17e441caea4de169b59861febb8bd82504737d` |
| 25 | H2_5of6 | 20261010T091112-378ce2d464 | 20261010T090820-2da0674722 | 874613c | 50e0502 | `22ec5787e822ba4645fb7a962865a21ef6059dc80b20799e04565913ff1228d2` |
| 26 | P_A1 | 20261010T091116-4835a4063a | 20261010T090831-aeca348964 | 50e0502 | 703cbd9 | `c3426c86937ac7eeae5c79243a0be697551ef87982b0868adc69c70f96c96514` |
| 27 | H1_252_3_WF (P_A1 comparator) | 20261010T091131-75eab3df7b | 20261010T090913-3da4aae83e | 703cbd9 | e927071 | `bae0e389f098d69d25027f3f540ba72ca178dd5cc12b0ac9977bfccbaa899ef4` |
| 28 | evaluation report | 20261010T091133-9f91bb3c9c | 20261010T091002-0c84d411ed | e927071 | 7f6dac8 | `5abda8a2d4b4de62a85d99d2f08a8503cbcab47a0abff5c2894e493324af89b8` |

Journal purposes (D025, item 12): `N5 benchmark run` for B0-B3 and REF_SPY, `N5 hypothesis run` for the six configurations and the comparator, `N5 policy run` for P_A1 and `N5 evaluation report` for the two reports. Seeds: the P_A1 runs journal 20261007 (the selection stability bootstrap) and the reports journal 20261006 (the paired utility bootstrap); the benchmark and hypothesis runs journal a null seed with the existing reason. P_A1 recorded no fallback year and no quality warning.

## Reproducibility

The comparison of step 4 of the campaign (specification section 9) was run after the repeat report, with the script recorded in [docs/REPRODUCIBILITY.md](../REPRODUCIBILITY.md). It verifies every directory with `provenance.verify` and compares the `files` dictionaries of the manifests (per-file SHA-256), not the manifest bytes, which contain run identifiers. Its results:

- All fourteen pairs are equal: the thirteen runs and their repeats (9 files for each benchmark, 10 for each configuration and for the comparator, 11 for P_A1) and the two reports (2 files, `evaluation.json` and `evaluation.md`).
- Every file that N3 or N4 had already frozen has the same SHA-256 in the first N5 run: 99 of 99 shared files, that is, the 45 files of the five first N3 benchmark runs and the 54 shared files of the six N4 replacement runs `20261008T192727-e5e184b7db`, `20261008T192731-0f8d083cb0`, `20261008T192734-866ab4b3d7`, `20261008T192737-45e578bd7c`, `20261008T192740-f8be1b1ad3` and `20261008T192745-708215766a` (D023, item 10; D025, item 17). The only file an N5 hypothesis run adds is `metrics.json`.
- Each of the eleven reference manifests is tied to its journal record: exactly one terminal record, status `completed`, `data_sha256` equal to the SHA-256 of the manifest, purpose `N3 benchmark run` or `N4 hypothesis run`, and `candidate_ids` equal to the provider.
- The journal holds 56 N5 records for 28 attempts, each attempt with a `started` and a `completed` record; all terminal statuses are `completed`, none of the records has `dirty_tree` true, one environment manifest, and no other record with an N5 purpose. Each repeat names its first run as parent, and the repeat report names the first report.
- Checked separately: the 28 distinct starting commits have the single `src` tree `058c72a492f78aa30f8defecbfab397eee37be96`; the journal has 180 rows, and the SHA-256 of its first 124 rows, `2d0b5bf461088f48a6e63cd898a70d40a2e1dca406a26a5bbbdc92842e60995d`, equals the hash of the journal recorded at the freeze, so no earlier record was changed; no N5 record has a quality warning.

Before computing anything, each evaluation report also applied the checks of specification section 7.1 to its thirteen input directories, including the shared-file identity, the recomputation of `utility` and `total_return` from `daily.csv` within 1e-7 and the semantic checks of the P_A1 selection log. The two report files are identical in the first report and the repeat report: SHA-256 `06f8a47a8651d9961ad3b1bd7717eb3fc20ee901ffe212b3f91614c6b29714db` for `evaluation.json` and `e22ecf681edf6bbbe996d0c24ad9f11e705774a0f80c3fcb06a9fad5ff0b958c` for `evaluation.md`.

No `src` change was made after the first registered N5 run: there was no rerun after a bug fix, and the campaign had no failed attempt.

## What was shown and when

The viewing procedure is D025, item 16 and specification section 8.

- Before the first evaluation report of 10 October 2026, no H1/H2 or P_A1 return, risk, utility or selection figure had been shown. During development the code used synthetic markets. The real-vintage tests computed the N5 quantities in memory (the shared files of the six configurations, the P_A1 selection for 2014 to 2022 and the identity of the metrics) and printed only counts, flags and maximum differences. The N4 run directories were read only by code (manifests and hashes).
- The thirteen runs of 10 October 2026 froze `metrics.json` and, for P_A1, `selection.json`. These files were read only by the evaluation report code and by the hash comparison; no campaign step displayed a value, and no step failed.
- The first evaluation report, `20261010T091002-0c84d411ed` (started 09:10:02 UTC, completed 09:10:24 UTC on 10 October 2026), is the first time an H1/H2 or P_A1 figure is shown (specification section 8, item 3); the run files that contain such figures had been frozen minutes earlier and were not displayed. D023, item 6 is superseded for N5 outputs from that moment; its text is preserved.
- The report files were not opened until the repeat report `20261010T091133-9f91bb3c9c` had completed (09:11:50 UTC) and the comparison of step 4 had found all fourteen pairs equal and all 99 shared files unchanged. The figures were first read after that, on 10 October 2026, and are published below as they are.
- No rule, candidate, parameter, window, period or selection procedure was changed after the figures were seen. Any such change would be a new attempt with its own decision record, not an N5 repeat (protocol line 192).
- The reserved period remains closed.

## Status of the configurations and P_A1

The conditions of specification section 1, items 1 to 5, hold: the benchmarks and the six configurations were rerun on the frozen N5 code with every shared file unchanged; the six configurations and P_A1 have a frozen `metrics.json` produced by the same code as the benchmark metrics; P_A1 has a complete selection log for 2014 to 2022; one registered evaluation report states the T1 to T6 tables; and a repeat of every run and of the report reproduces the manifest `files` dictionaries. Item 6 holds as well: nothing after 2022-12-30 was computed. No decision under protocol section 13 exists.

Under D025, item 19 the status of H1_252_3, H1_252_4, H1_126_3, H1_126_4, H2_4of6, H2_5of6 and P_A1 is therefore `evaluated_walk_forward`, established by the first runs `20261010T090737-2d652c2127`, `20261010T090745-899d5a7136`, `20261010T090752-9bd003f35b`, `20261010T090800-f78d0ee07b`, `20261010T090807-af398ad6af`, `20261010T090820-2da0674722` and `20261010T090831-aeca348964`, the first report `20261010T091002-0c84d411ed`, and their repeats listed above. The status states that walk-forward figures exist. It does not state that a configuration or the policy is useful or rejected. The comparator run `20261010T090913-3da4aae83e` is not a candidate and has no status. The journal records no status event.

## Disclosures

The disclosures of specification section 7.4 are stated in T6 of the report below and apply to every figure in this document:

- All inferential figures are exploratory on familiar history, and the Holm adjustment does not restore independence (protocol line 163).
- 2014 to 2022 was the research period, and the project owner's prior exposure to it is non-zero and unquantified (G0; [docs/n5/ATTEMPT_ACCOUNTING.md](ATTEMPT_ACCOUNTING.md)). The multiple-testing caveat is unresolved in size; DSR and PBO are not computed.
- Each statistic is conditional on the model already selected (protocol line 167). The P_A1 intervals are conditional on the realized selections of P_A1, and no p-value is reported for P_A1.
- The window excludes most of the 2008 crisis (protocol line 141).
- The data limitations recorded in D016 to D020 apply.
- Costs are modeled at 10 basis points per side, in the main scenario only; the cost and delay scenarios of protocol section 12 have not been run.
- The walk-forward figures of the continuous accounts and those of P_A1 differ by the start state: P_A1 and its comparator start in cash on 2013-12-31, while the continuous accounts carry positions from earlier years (D025, items 1 and 2).
- Statistical non-significance does not establish the absence of an effect (protocol line 163).
- The results do not establish an investable track record.

The minimum-effect flags of T2 are stated for each comparison exactly as the report states them. They are mechanical properties of the point estimates, not decisions under protocol section 13, which also require the scenario, leave-one-class-out and reserved-period evidence of N6.

## Evaluation report

The remainder of this document, from the heading "N5 evaluation report" to the end, is the content of `data/reports/20261010T091002-0c84d411ed/evaluation.md`, the frozen Markdown file of the first evaluation report run `20261010T091002-0c84d411ed`, copied byte for byte (SHA-256 of the file: `e22ecf681edf6bbbe996d0c24ad9f11e705774a0f80c3fcb06a9fad5ff0b958c`). Its headings keep their original levels. The repeat report `20261010T091133-9f91bb3c9c` has an identical file. The directory is not in Git, so the copy below is the published record. Nothing in it has been rounded, relabeled or recomputed. Its tables are T1 (metrics by period and year, including group and weight breakdowns), T2 (comparisons on the walk-forward period), T3 (annual differences), T4 (regressions), T5 (the P_A1 selection log and stability frequencies) and T6 (disclosures). Percentages, multiples and decimal places are as formatted by the report code; `evaluation.json` holds the unformatted values.

# N5 evaluation report

Continuous accounts 2008-12-31 to 2022-12-30; P_A1 and its comparator 2013-12-31 to 2022-12-30; walk-forward statistics 2014-01-02 to 2022-12-30 (2266 daily returns, period 2014-01-01 to 2022-12-31). Initial cash 100000.00, scenario {"cost": 0.001, "lag": 1, "proxy_pay_days": 10, "reserve": 0.01}, vintage manifest f89346107cf7da6ca052693d188b8a576a08d42024c86865b0a42a63b1d294f2.

| run | provider version |
|---|---|
| B0 | 1 |
| B1 | 1 |
| B2 | 1 |
| B3 | 1 |
| REF_SPY | 1 |
| H1_252_3 | 1 |
| H1_252_4 | 1 |
| H1_126_3 | 1 |
| H1_126_4 | 1 |
| H2_4of6 | 1 |
| H2_5of6 | 1 |
| P_A1 | 1 |
| H1_252_3_WF | 1 |

## T1 Metrics

### full

| run | total_return | cagr | volatility | mean_excess | sharpe_bil | utility | max_drawdown | decisions | turnover_annual | costs_usd | cost_ratio | mean_cash_plus_bil | mean_receivables | mean_risky | mean_target_risky | mean_bil | mean_cash_usd | n_returns | turnover |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B0 | 5.92% | 0.41% | 0.30% | -0.02% | -0.358 | -0.000 | -0.44% | 168 | 0.07x | 104.89 | 0.10% | 99.99% | 0.01% | 0.00% | 0.00% | 98.94% | 1.05% | 3524 | 1.05x |
| B1 | 79.31% | 4.26% | 7.88% | 4.05% | 0.513 | 0.031 | -17.83% | 168 | 0.66x | 1316.57 | 0.93% | 7.89% | 0.06% | 92.06% | 93.39% | 6.50% | 1.38% | 3524 | 9.25x |
| B2 | 75.63% | 4.11% | 6.38% | 3.80% | 0.594 | 0.032 | -18.80% | 168 | 1.17x | 2434.75 | 1.63% | 4.80% | 0.06% | 95.15% | 96.58% | 3.36% | 1.44% | 3524 | 16.30x |
| B3 | 45.39% | 2.71% | 4.36% | 2.34% | 0.536 | 0.021 | -9.59% | 168 | 2.93x | 5153.11 | 4.09% | 36.41% | 0.05% | 63.54% | 64.51% | 35.06% | 1.35% | 3524 | 40.94x |
| REF_SPY | 385.27% | 11.96% | 16.84% | 12.28% | 0.729 | 0.080 | -29.95% | 1 | 0.07x | 99.21 | 0.10% | 8.11% | 0.20% | 91.69% | 100.00% | 0.00% | 8.11% | 3524 | 0.99x |
| H1_252_3 | 65.88% | 3.69% | 6.08% | 3.37% | 0.554 | 0.028 | -12.49% | 168 | 3.96x | 7437.19 | 5.54% | 36.94% | 0.05% | 63.00% | 63.79% | 35.76% | 1.19% | 3524 | 55.36x |
| H1_252_4 | 50.15% | 2.95% | 6.14% | 2.66% | 0.433 | 0.021 | -11.06% | 168 | 3.29x | 5927.82 | 4.60% | 28.65% | 0.05% | 71.30% | 72.26% | 27.40% | 1.25% | 3524 | 45.95x |
| H1_126_3 | 64.03% | 3.60% | 6.76% | 3.33% | 0.493 | 0.026 | -17.33% | 168 | 5.64x | 10394.73 | 7.88% | 38.55% | 0.05% | 61.40% | 62.25% | 37.39% | 1.16% | 3524 | 78.84x |
| H1_126_4 | 65.76% | 3.68% | 7.02% | 3.43% | 0.487 | 0.027 | -20.44% | 168 | 5.21x | 10114.08 | 7.29% | 31.12% | 0.05% | 68.83% | 69.79% | 29.91% | 1.21% | 3524 | 72.91x |
| H2_4of6 | 55.88% | 3.23% | 4.54% | 2.84% | 0.626 | 0.025 | -7.59% | 168 | 4.38x | 7783.08 | 6.13% | 56.73% | 0.04% | 43.23% | 43.79% | 55.58% | 1.14% | 3524 | 61.26x |
| H2_5of6 | 12.46% | 0.84% | 3.15% | 0.46% | 0.145 | 0.003 | -6.17% | 168 | 3.34x | 4895.57 | 4.66% | 78.25% | 0.03% | 21.72% | 22.01% | 77.14% | 1.11% | 3524 | 46.65x |

### full max_group

| run | Equity | Treasury | Credit | Real |
|---|---|---|---|---|
| B0 | 0.00% | 0.00% | 0.00% | 0.00% |
| B1 | 35.25% | 26.40% | 22.56% | 24.77% |
| B2 | 29.12% | 33.29% | 44.91% | 21.18% |
| B3 | 29.79% | 32.70% | 43.86% | 28.01% |
| REF_SPY | 99.33% | 0.00% | 0.00% | 0.00% |
| H1_252_3 | 51.26% | 49.48% | 50.50% | 53.04% |
| H1_252_4 | 51.39% | 45.01% | 50.22% | 52.82% |
| H1_126_3 | 51.34% | 49.48% | 50.07% | 50.28% |
| H1_126_4 | 51.00% | 45.79% | 50.06% | 49.69% |
| H2_4of6 | 51.33% | 46.68% | 50.43% | 49.09% |
| H2_5of6 | 49.87% | 44.69% | 49.73% | 41.56% |

### full max_weight

| run | DBC | EEM | EFA | GLD | HYG | IEF | LQD | SPY | TLT |
|---|---|---|---|---|---|---|---|---|---|
| B0 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| B1 | 12.95% | 12.10% | 12.11% | 13.02% | 11.26% | 12.97% | 11.48% | 11.75% | 13.45% |
| B2 | 13.23% | 8.84% | 10.90% | 13.62% | 25.05% | 24.75% | 25.37% | 13.33% | 10.93% |
| B3 | 12.65% | 7.20% | 11.06% | 15.36% | 25.05% | 24.68% | 25.20% | 13.72% | 10.69% |
| REF_SPY | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 99.33% | 0.00% |
| H1_252_3 | 27.76% | 23.85% | 26.03% | 28.92% | 25.64% | 26.15% | 26.23% | 26.12% | 24.80% |
| H1_252_4 | 27.35% | 14.25% | 24.75% | 27.50% | 25.62% | 26.39% | 26.27% | 26.15% | 24.75% |
| H1_126_3 | 27.98% | 22.52% | 26.24% | 26.57% | 25.35% | 25.68% | 25.38% | 26.06% | 25.19% |
| H1_126_4 | 28.02% | 17.72% | 25.14% | 25.19% | 25.46% | 25.64% | 25.66% | 26.00% | 25.11% |
| H2_4of6 | 27.88% | 19.24% | 24.90% | 27.94% | 25.61% | 25.29% | 25.41% | 26.05% | 22.08% |
| H2_5of6 | 28.07% | 17.87% | 24.42% | 24.65% | 25.37% | 25.05% | 25.47% | 25.69% | 21.31% |

### full mean_group

| run | Equity | Treasury | Credit | Real |
|---|---|---|---|---|
| B0 | 0.00% | 0.00% | 0.00% | 0.00% |
| B1 | 30.79% | 20.37% | 20.38% | 20.51% |
| B2 | 19.55% | 25.86% | 35.53% | 14.20% |
| B3 | 13.74% | 15.42% | 26.99% | 7.39% |
| REF_SPY | 91.69% | 0.00% | 0.00% | 0.00% |
| H1_252_3 | 17.05% | 15.64% | 21.96% | 8.35% |
| H1_252_4 | 17.23% | 17.19% | 28.01% | 8.86% |
| H1_126_3 | 17.64% | 13.86% | 21.18% | 8.71% |
| H1_126_4 | 18.63% | 15.33% | 25.52% | 9.35% |
| H2_4of6 | 12.68% | 6.83% | 18.53% | 5.20% |
| H2_5of6 | 7.18% | 2.00% | 10.28% | 2.27% |

### full mean_weight

| run | DBC | EEM | EFA | GLD | HYG | IEF | LQD | SPY | TLT |
|---|---|---|---|---|---|---|---|---|---|
| B0 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| B1 | 10.26% | 10.27% | 10.27% | 10.26% | 10.20% | 10.20% | 10.18% | 10.26% | 10.17% |
| B2 | 6.70% | 5.29% | 6.67% | 7.51% | 16.76% | 18.03% | 18.77% | 7.59% | 7.84% |
| B3 | 3.16% | 3.01% | 4.20% | 4.23% | 13.28% | 11.00% | 13.72% | 6.53% | 4.42% |
| REF_SPY | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 91.69% | 0.00% |
| H1_252_3 | 3.87% | 1.78% | 4.55% | 4.48% | 11.57% | 9.97% | 10.39% | 10.72% | 5.67% |
| H1_252_4 | 3.79% | 2.03% | 5.11% | 5.07% | 13.60% | 11.80% | 14.41% | 10.09% | 5.40% |
| H1_126_3 | 4.44% | 2.71% | 5.49% | 4.27% | 10.31% | 8.61% | 10.87% | 9.45% | 5.25% |
| H1_126_4 | 4.22% | 3.30% | 5.54% | 5.13% | 11.84% | 9.75% | 13.68% | 9.79% | 5.58% |
| H2_4of6 | 2.49% | 1.01% | 3.12% | 2.71% | 10.26% | 4.25% | 8.26% | 8.56% | 2.58% |
| H2_5of6 | 1.55% | 0.35% | 1.67% | 0.72% | 5.57% | 1.33% | 4.71% | 5.16% | 0.67% |

### development

| run | total_return | cagr | volatility | mean_excess | sharpe_bil | utility | max_drawdown | decisions | turnover_annual | costs_usd | cost_ratio | mean_cash_plus_bil | mean_receivables | mean_risky | mean_target_risky | mean_bil | mean_cash_usd | n_returns | turnover |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B0 | -0.17% | -0.03% | 0.39% | -0.05% | -0.448 | -0.000 | -0.24% | 60 | 0.20x | 99.45 | 0.10% | 100.00% | 0.00% | 0.00% | 0.00% | 98.99% | 1.01% | 1258 | 0.99x |
| B1 | 40.76% | 7.09% | 8.08% | 7.16% | 0.883 | 0.062 | -8.51% | 60 | 0.93x | 539.02 | 0.46% | 13.05% | 0.06% | 86.89% | 88.10% | 11.65% | 1.40% | 1258 | 4.65x |
| B2 | 43.29% | 7.47% | 6.21% | 7.39% | 1.183 | 0.068 | -7.57% | 60 | 1.31x | 784.11 | 0.66% | 6.45% | 0.07% | 93.49% | 94.91% | 4.98% | 1.47% | 1258 | 6.55x |
| B3 | 24.63% | 4.51% | 4.88% | 4.52% | 0.923 | 0.042 | -5.33% | 60 | 2.87x | 1589.26 | 1.43% | 29.10% | 0.05% | 70.85% | 71.91% | 27.72% | 1.38% | 1258 | 14.33x |
| REF_SPY | 118.07% | 16.90% | 18.53% | 17.33% | 0.933 | 0.122 | -26.95% | 1 | 0.20x | 99.21 | 0.10% | 4.17% | 0.22% | 95.61% | 100.00% | 0.00% | 4.17% | 1258 | 0.99x |
| H1_252_3 | 32.54% | 5.81% | 6.01% | 5.81% | 0.965 | 0.053 | -7.47% | 60 | 4.11x | 2264.43 | 2.05% | 33.82% | 0.05% | 66.13% | 66.95% | 32.59% | 1.23% | 1258 | 20.51x |
| H1_252_4 | 23.97% | 4.40% | 6.21% | 4.48% | 0.721 | 0.039 | -7.07% | 60 | 2.84x | 1526.13 | 1.42% | 24.01% | 0.06% | 75.93% | 76.96% | 22.70% | 1.31% | 1258 | 14.17x |
| H1_126_3 | 25.68% | 4.69% | 6.18% | 4.76% | 0.768 | 0.042 | -6.46% | 60 | 5.53x | 2955.11 | 2.76% | 36.52% | 0.06% | 63.42% | 64.34% | 35.34% | 1.18% | 1258 | 27.60x |
| H1_126_4 | 35.50% | 6.28% | 6.65% | 6.30% | 0.944 | 0.056 | -7.69% | 60 | 4.75x | 2673.87 | 2.37% | 27.95% | 0.06% | 71.99% | 73.05% | 26.69% | 1.26% | 1258 | 23.72x |
| H2_4of6 | 24.43% | 4.48% | 4.53% | 4.47% | 0.983 | 0.042 | -5.54% | 60 | 4.90x | 2668.34 | 2.45% | 53.29% | 0.05% | 46.67% | 47.30% | 52.12% | 1.17% | 1258 | 24.46x |
| H2_5of6 | 5.47% | 1.07% | 3.01% | 1.10% | 0.367 | 0.010 | -4.11% | 60 | 4.13x | 2087.60 | 2.06% | 77.79% | 0.02% | 22.19% | 22.54% | 76.68% | 1.11% | 1258 | 20.60x |

### development max_group

| run | Equity | Treasury | Credit | Real |
|---|---|---|---|---|
| B0 | 0.00% | 0.00% | 0.00% | 0.00% |
| B1 | 35.06% | 24.53% | 22.56% | 23.77% |
| B2 | 28.07% | 32.17% | 44.91% | 19.36% |
| B3 | 28.94% | 30.72% | 43.86% | 19.26% |
| REF_SPY | 99.33% | 0.00% | 0.00% | 0.00% |
| H1_252_3 | 51.10% | 46.62% | 50.50% | 46.33% |
| H1_252_4 | 51.39% | 45.01% | 50.22% | 40.52% |
| H1_126_3 | 51.34% | 49.18% | 50.07% | 50.28% |
| H1_126_4 | 49.88% | 41.32% | 50.06% | 34.06% |
| H2_4of6 | 44.36% | 46.62% | 50.43% | 41.51% |
| H2_5of6 | 25.69% | 44.69% | 49.73% | 41.56% |

### development max_weight

| run | DBC | EEM | EFA | GLD | HYG | IEF | LQD | SPY | TLT |
|---|---|---|---|---|---|---|---|---|---|
| B0 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| B1 | 11.76% | 12.10% | 11.73% | 13.02% | 11.26% | 11.86% | 11.48% | 11.66% | 12.84% |
| B2 | 13.23% | 7.04% | 9.32% | 11.60% | 23.02% | 22.12% | 25.37% | 13.33% | 10.93% |
| B3 | 10.01% | 6.88% | 9.60% | 11.22% | 23.04% | 21.84% | 25.20% | 13.72% | 9.93% |
| REF_SPY | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 99.33% | 0.00% |
| H1_252_3 | 26.36% | 17.74% | 26.03% | 28.92% | 25.64% | 25.18% | 26.23% | 25.31% | 22.43% |
| H1_252_4 | 20.69% | 12.70% | 19.14% | 27.50% | 25.62% | 25.30% | 26.27% | 25.32% | 20.42% |
| H1_126_3 | 24.98% | 22.46% | 26.24% | 25.46% | 25.33% | 25.56% | 25.38% | 25.65% | 24.09% |
| H1_126_4 | 16.17% | 17.44% | 22.44% | 20.71% | 25.46% | 25.60% | 25.66% | 25.46% | 17.47% |
| H2_4of6 | 17.99% | 17.80% | 20.17% | 27.94% | 25.61% | 25.21% | 25.41% | 25.77% | 21.80% |
| H2_5of6 | 17.98% | 0.00% | 15.05% | 24.65% | 25.37% | 25.05% | 25.47% | 25.69% | 20.39% |

### development mean_group

| run | Equity | Treasury | Credit | Real |
|---|---|---|---|---|
| B0 | 0.00% | 0.00% | 0.00% | 0.00% |
| B1 | 29.13% | 19.20% | 19.23% | 19.33% |
| B2 | 18.69% | 25.43% | 35.01% | 14.36% |
| B3 | 13.94% | 19.14% | 29.49% | 8.27% |
| REF_SPY | 95.61% | 0.00% | 0.00% | 0.00% |
| H1_252_3 | 11.19% | 15.33% | 30.30% | 9.31% |
| H1_252_4 | 11.93% | 18.52% | 36.22% | 9.26% |
| H1_126_3 | 15.64% | 14.26% | 26.44% | 7.07% |
| H1_126_4 | 16.23% | 15.78% | 31.67% | 8.31% |
| H2_4of6 | 8.29% | 5.83% | 25.89% | 6.66% |
| H2_5of6 | 3.42% | 1.94% | 13.97% | 2.87% |

### development mean_weight

| run | DBC | EEM | EFA | GLD | HYG | IEF | LQD | SPY | TLT |
|---|---|---|---|---|---|---|---|---|---|
| B0 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| B1 | 9.68% | 9.71% | 9.71% | 9.65% | 9.63% | 9.62% | 9.60% | 9.71% | 9.58% |
| B2 | 7.18% | 5.09% | 5.82% | 7.18% | 14.57% | 17.53% | 20.44% | 7.77% | 7.90% |
| B3 | 3.15% | 3.31% | 4.06% | 5.12% | 12.69% | 13.70% | 16.80% | 6.56% | 5.44% |
| REF_SPY | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 95.61% | 0.00% |
| H1_252_3 | 1.68% | 1.02% | 2.84% | 7.63% | 15.49% | 10.17% | 14.81% | 7.33% | 5.17% |
| H1_252_4 | 1.53% | 1.75% | 2.77% | 7.73% | 17.31% | 13.93% | 18.91% | 7.41% | 4.60% |
| H1_126_3 | 2.29% | 1.69% | 4.83% | 4.78% | 13.82% | 9.77% | 12.62% | 9.13% | 4.49% |
| H1_126_4 | 2.03% | 2.46% | 4.34% | 6.28% | 15.60% | 11.03% | 16.07% | 9.43% | 4.75% |
| H2_4of6 | 0.87% | 0.56% | 0.79% | 5.79% | 13.90% | 4.11% | 11.99% | 6.93% | 1.72% |
| H2_5of6 | 0.87% | 0.00% | 0.22% | 2.00% | 6.92% | 1.62% | 7.04% | 3.19% | 0.32% |

### walk_forward

| run | total_return | cagr | volatility | mean_excess | sharpe_bil | utility | max_drawdown | decisions | turnover_annual | costs_usd | cost_ratio | mean_cash_plus_bil | mean_receivables | mean_risky | mean_target_risky | mean_bil | mean_cash_usd | n_returns | turnover |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B0 | 6.10% | 0.66% | 0.24% | -0.01% | -3.266 | -0.000 | -0.24% | 108 | 0.01x | 5.44 | 0.01% | 99.99% | 0.01% | 0.00% | 0.00% | 98.92% | 1.07% | 2266 | 0.05x |
| B1 | 27.39% | 2.73% | 7.77% | 2.33% | 0.299 | 0.014 | -17.83% | 108 | 0.51x | 777.54 | 0.46% | 5.02% | 0.05% | 94.93% | 96.33% | 3.65% | 1.37% | 2266 | 4.60x |
| B2 | 22.57% | 2.29% | 6.47% | 1.80% | 0.279 | 0.012 | -18.80% | 108 | 1.08x | 1650.64 | 0.97% | 3.88% | 0.05% | 96.07% | 97.51% | 2.46% | 1.42% | 2266 | 9.75x |
| B3 | 16.65% | 1.73% | 4.03% | 1.13% | 0.279 | 0.009 | -9.59% | 108 | 2.96x | 3563.85 | 2.66% | 40.47% | 0.04% | 59.48% | 60.40% | 39.14% | 1.34% | 2266 | 26.61x |
| REF_SPY | 122.53% | 9.30% | 15.82% | 9.48% | 0.600 | 0.057 | -29.95% | 0 | 0.00x | 0.00 | 0.00% | 10.30% | 0.19% | 89.51% | n/a | 0.00% | 10.30% | 2266 | 0.00x |
| H1_252_3 | 25.15% | 2.53% | 6.11% | 2.01% | 0.330 | 0.015 | -12.49% | 108 | 3.88x | 5172.76 | 3.48% | 38.68% | 0.05% | 61.27% | 62.04% | 37.52% | 1.17% | 2266 | 34.85x |
| H1_252_4 | 21.12% | 2.15% | 6.10% | 1.65% | 0.270 | 0.011 | -11.06% | 108 | 3.53x | 4401.69 | 3.18% | 31.23% | 0.05% | 68.72% | 69.65% | 30.01% | 1.22% | 2266 | 31.78x |
| H1_126_3 | 30.52% | 3.01% | 7.06% | 2.54% | 0.361 | 0.018 | -17.33% | 108 | 5.70x | 7439.62 | 5.12% | 39.68% | 0.04% | 60.27% | 61.09% | 38.53% | 1.15% | 2266 | 51.25x |
| H1_126_4 | 22.33% | 2.27% | 7.22% | 1.84% | 0.254 | 0.011 | -20.44% | 108 | 5.47x | 7440.21 | 4.92% | 32.88% | 0.05% | 67.08% | 67.98% | 31.69% | 1.19% | 2266 | 49.19x |
| H2_4of6 | 25.27% | 2.54% | 4.54% | 1.94% | 0.428 | 0.016 | -7.59% | 108 | 4.09x | 5114.74 | 3.68% | 58.64% | 0.04% | 41.33% | 41.84% | 57.51% | 1.13% | 2266 | 36.80x |
| H2_5of6 | 6.63% | 0.72% | 3.23% | 0.10% | 0.030 | -0.001 | -6.17% | 108 | 2.90x | 2807.96 | 2.60% | 78.50% | 0.03% | 21.47% | 21.71% | 77.40% | 1.11% | 2266 | 26.05x |
| P_A1 | 27.70% | 2.76% | 6.97% | 2.30% | 0.329 | 0.016 | -17.33% | 108 | 4.80x | 4903.02 | 4.32% | 37.83% | 0.05% | 62.12% | 62.98% | 36.61% | 1.22% | 2266 | 43.19x |
| H1_252_3_WF | 25.50% | 2.56% | 6.11% | 2.04% | 0.335 | 0.015 | -12.47% | 108 | 3.97x | 3996.03 | 3.57% | 38.71% | 0.05% | 61.24% | 62.04% | 37.51% | 1.20% | 2266 | 35.67x |

### walk_forward max_group

| run | Equity | Treasury | Credit | Real |
|---|---|---|---|---|
| B0 | 0.00% | 0.00% | 0.00% | 0.00% |
| B1 | 35.25% | 26.40% | 22.46% | 24.77% |
| B2 | 29.12% | 33.29% | 43.54% | 21.18% |
| B3 | 29.79% | 32.70% | 41.95% | 28.01% |
| REF_SPY | 93.03% | 0.00% | 0.00% | 0.00% |
| H1_252_3 | 51.26% | 49.48% | 49.96% | 53.04% |
| H1_252_4 | 51.28% | 43.33% | 49.94% | 52.82% |
| H1_126_3 | 50.67% | 49.48% | 49.86% | 49.97% |
| H1_126_4 | 51.00% | 45.79% | 49.87% | 49.69% |
| H2_4of6 | 51.33% | 46.68% | 49.95% | 49.09% |
| H2_5of6 | 49.87% | 43.83% | 25.39% | 28.07% |
| P_A1 | 50.68% | 49.45% | 49.95% | 53.07% |
| H1_252_3_WF | 51.32% | 49.45% | 49.95% | 53.08% |

### walk_forward max_weight

| run | DBC | EEM | EFA | GLD | HYG | IEF | LQD | SPY | TLT |
|---|---|---|---|---|---|---|---|---|---|
| B0 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| B1 | 12.95% | 11.95% | 12.11% | 12.59% | 11.25% | 12.97% | 11.35% | 11.75% | 13.45% |
| B2 | 10.72% | 8.84% | 10.90% | 13.62% | 25.05% | 24.75% | 24.90% | 12.57% | 10.78% |
| B3 | 12.65% | 7.20% | 11.06% | 15.36% | 25.05% | 24.68% | 23.14% | 12.84% | 10.69% |
| REF_SPY | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 93.03% | 0.00% |
| H1_252_3 | 27.76% | 23.85% | 25.23% | 26.64% | 25.24% | 26.15% | 25.38% | 26.12% | 24.80% |
| H1_252_4 | 27.35% | 14.25% | 24.75% | 25.64% | 25.19% | 26.39% | 25.40% | 26.15% | 24.75% |
| H1_126_3 | 27.98% | 22.52% | 25.39% | 26.57% | 25.35% | 25.68% | 25.31% | 26.06% | 25.19% |
| H1_126_4 | 28.02% | 17.72% | 25.14% | 25.19% | 25.43% | 25.64% | 25.66% | 26.00% | 25.11% |
| H2_4of6 | 27.88% | 19.24% | 24.90% | 25.21% | 25.21% | 25.29% | 25.31% | 26.05% | 22.08% |
| H2_5of6 | 28.07% | 17.87% | 24.42% | 0.00% | 25.18% | 24.82% | 25.39% | 25.01% | 21.31% |
| P_A1 | 27.76% | 22.36% | 25.33% | 26.57% | 25.35% | 26.12% | 25.36% | 26.09% | 25.11% |
| H1_252_3_WF | 27.76% | 23.86% | 25.18% | 26.65% | 25.13% | 26.12% | 25.36% | 26.21% | 24.77% |

### walk_forward mean_group

| run | Equity | Treasury | Credit | Real |
|---|---|---|---|---|
| B0 | 0.00% | 0.00% | 0.00% | 0.00% |
| B1 | 31.71% | 21.02% | 21.02% | 21.17% |
| B2 | 20.03% | 26.10% | 35.81% | 14.12% |
| B3 | 13.63% | 13.35% | 25.60% | 6.90% |
| REF_SPY | 89.51% | 0.00% | 0.00% | 0.00% |
| H1_252_3 | 20.31% | 15.81% | 17.34% | 7.82% |
| H1_252_4 | 20.18% | 16.46% | 23.45% | 8.64% |
| H1_126_3 | 18.75% | 13.64% | 18.26% | 9.62% |
| H1_126_4 | 19.96% | 15.08% | 22.11% | 9.93% |
| H2_4of6 | 15.12% | 7.38% | 14.44% | 4.39% |
| H2_5of6 | 9.26% | 2.04% | 8.23% | 1.93% |
| P_A1 | 20.88% | 14.90% | 16.68% | 9.66% |
| H1_252_3_WF | 20.29% | 15.80% | 17.33% | 7.82% |

### walk_forward mean_weight

| run | DBC | EEM | EFA | GLD | HYG | IEF | LQD | SPY | TLT |
|---|---|---|---|---|---|---|---|---|---|
| B0 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| B1 | 10.58% | 10.58% | 10.58% | 10.59% | 10.52% | 10.52% | 10.50% | 10.56% | 10.50% |
| B2 | 6.43% | 5.40% | 7.14% | 7.69% | 17.97% | 18.30% | 17.84% | 7.49% | 7.80% |
| B3 | 3.16% | 2.85% | 4.28% | 3.74% | 13.60% | 9.49% | 12.00% | 6.51% | 3.85% |
| REF_SPY | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 89.51% | 0.00% |
| H1_252_3 | 5.08% | 2.21% | 5.50% | 2.74% | 9.39% | 9.86% | 7.94% | 12.60% | 5.95% |
| H1_252_4 | 5.05% | 2.18% | 6.42% | 3.60% | 11.53% | 10.61% | 11.91% | 11.58% | 5.84% |
| H1_126_3 | 5.64% | 3.28% | 5.85% | 3.99% | 8.36% | 7.97% | 9.89% | 9.62% | 5.67% |
| H1_126_4 | 5.43% | 3.77% | 6.21% | 4.50% | 9.75% | 9.04% | 12.36% | 9.98% | 6.04% |
| H2_4of6 | 3.39% | 1.25% | 4.41% | 1.00% | 8.25% | 4.32% | 6.19% | 9.46% | 3.06% |
| H2_5of6 | 1.93% | 0.54% | 2.47% | 0.00% | 4.83% | 1.17% | 3.41% | 6.24% | 0.87% |
| P_A1 | 5.87% | 2.09% | 5.87% | 3.79% | 9.39% | 8.69% | 7.28% | 12.91% | 6.21% |
| H1_252_3_WF | 5.08% | 2.20% | 5.50% | 2.74% | 9.39% | 9.86% | 7.94% | 12.59% | 5.94% |

### 2014-2016

| run | total_return | cagr | volatility | mean_excess | sharpe_bil | utility | max_drawdown | decisions | turnover_annual | costs_usd | cost_ratio | mean_cash_plus_bil | mean_receivables | mean_risky | mean_target_risky | mean_bil | mean_cash_usd | n_returns | turnover |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B0 | -0.09% | -0.03% | 0.27% | 0.00% | 0.108 | 0.000 | -0.24% | 36 | 0.00x | 0.00 | 0.00% | 100.00% | 0.00% | 0.00% | 0.00% | 98.99% | 1.01% | 756 | 0.00x |
| B1 | 2.82% | 0.93% | 6.63% | 1.17% | 0.177 | 0.005 | -14.81% | 36 | 0.27x | 115.89 | 0.08% | 1.39% | 0.06% | 98.56% | 100.00% | 0.00% | 1.39% | 756 | 0.81x |
| B2 | 4.64% | 1.52% | 5.02% | 1.67% | 0.332 | 0.013 | -10.44% | 36 | 0.85x | 378.77 | 0.26% | 1.64% | 0.06% | 98.31% | 99.78% | 0.21% | 1.42% | 756 | 2.56x |
| B3 | 0.91% | 0.30% | 3.31% | 0.38% | 0.116 | 0.002 | -4.94% | 36 | 3.18x | 1211.15 | 0.95% | 40.62% | 0.04% | 59.34% | 60.13% | 39.31% | 1.31% | 756 | 9.55x |
| REF_SPY | 25.87% | 7.97% | 12.13% | 8.43% | 0.694 | 0.062 | -11.82% | 0 | 0.00x | 0.00 | 0.00% | 8.58% | 0.21% | 91.21% | n/a | 0.00% | 8.58% | 756 | 0.00x |
| H1_252_3 | 4.37% | 1.44% | 4.75% | 1.57% | 0.330 | 0.012 | -5.98% | 36 | 3.82x | 1610.14 | 1.15% | 36.61% | 0.05% | 63.34% | 64.24% | 35.40% | 1.20% | 756 | 11.46x |
| H1_252_4 | 2.53% | 0.84% | 4.48% | 0.96% | 0.214 | 0.007 | -5.97% | 36 | 4.04x | 1554.39 | 1.21% | 30.02% | 0.06% | 69.92% | 70.90% | 28.75% | 1.27% | 756 | 12.13x |
| H1_126_3 | 3.42% | 1.13% | 5.46% | 1.30% | 0.238 | 0.009 | -11.86% | 36 | 4.96x | 1907.74 | 1.49% | 37.11% | 0.05% | 62.84% | 63.76% | 35.94% | 1.17% | 756 | 14.88x |
| H1_126_4 | 0.03% | 0.01% | 5.50% | 0.19% | 0.034 | -0.003 | -12.23% | 36 | 4.83x | 1976.63 | 1.45% | 28.84% | 0.05% | 71.11% | 72.18% | 27.63% | 1.21% | 756 | 14.48x |
| H2_4of6 | 2.80% | 0.93% | 3.53% | 1.01% | 0.288 | 0.008 | -5.90% | 36 | 3.37x | 1310.79 | 1.01% | 64.30% | 0.03% | 35.67% | 36.31% | 63.20% | 1.10% | 756 | 10.11x |
| H2_5of6 | -1.38% | -0.46% | 2.03% | -0.41% | -0.204 | -0.005 | -4.09% | 36 | 3.47x | 1094.73 | 1.04% | 82.70% | 0.02% | 17.27% | 17.66% | 81.64% | 1.07% | 756 | 10.42x |
| P_A1 | 4.66% | 1.53% | 4.73% | 1.66% | 0.350 | 0.013 | -5.98% | 36 | 4.10x | 1302.66 | 1.23% | 36.64% | 0.05% | 63.31% | 64.24% | 35.39% | 1.25% | 756 | 12.31x |
| H1_252_3_WF | 4.66% | 1.53% | 4.73% | 1.66% | 0.350 | 0.013 | -5.98% | 36 | 4.10x | 1302.66 | 1.23% | 36.64% | 0.05% | 63.31% | 64.24% | 35.39% | 1.25% | 756 | 12.31x |

### 2014-2016 max_group

| run | Equity | Treasury | Credit | Real |
|---|---|---|---|---|
| B0 | 0.00% | 0.00% | 0.00% | 0.00% |
| B1 | 34.67% | 23.69% | 22.36% | 23.03% |
| B2 | 24.75% | 32.29% | 43.54% | 17.43% |
| B3 | 21.73% | 27.07% | 40.80% | 13.42% |
| REF_SPY | 93.03% | 0.00% | 0.00% | 0.00% |
| H1_252_3 | 44.67% | 49.48% | 49.93% | 19.01% |
| H1_252_4 | 30.93% | 43.33% | 49.68% | 15.49% |
| H1_126_3 | 49.55% | 49.44% | 49.58% | 25.56% |
| H1_126_4 | 49.70% | 45.79% | 49.83% | 24.74% |
| H2_4of6 | 44.72% | 45.49% | 49.88% | 0.00% |
| H2_5of6 | 37.36% | 21.31% | 25.18% | 0.00% |
| P_A1 | 44.69% | 49.45% | 49.95% | 19.01% |
| H1_252_3_WF | 44.69% | 49.45% | 49.95% | 19.01% |

### 2014-2016 max_weight

| run | DBC | EEM | EFA | GLD | HYG | IEF | LQD | SPY | TLT |
|---|---|---|---|---|---|---|---|---|---|
| B0 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| B1 | 11.79% | 11.95% | 11.64% | 12.32% | 11.25% | 11.74% | 11.35% | 11.75% | 11.95% |
| B2 | 10.72% | 7.04% | 8.98% | 10.67% | 24.89% | 22.59% | 24.90% | 10.58% | 10.08% |
| B3 | 8.35% | 6.18% | 8.25% | 7.61% | 24.70% | 19.68% | 22.19% | 9.89% | 8.33% |
| REF_SPY | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 93.03% | 0.00% |
| H1_252_3 | 0.00% | 0.00% | 22.37% | 19.01% | 25.24% | 26.11% | 25.38% | 25.53% | 24.80% |
| H1_252_4 | 0.00% | 0.00% | 15.46% | 15.49% | 25.19% | 25.76% | 25.15% | 24.97% | 18.64% |
| H1_126_3 | 25.56% | 21.09% | 24.91% | 17.16% | 25.18% | 25.68% | 25.31% | 26.06% | 24.79% |
| H1_126_4 | 23.91% | 17.42% | 20.43% | 17.02% | 25.43% | 25.64% | 25.30% | 21.40% | 21.10% |
| H2_4of6 | 0.00% | 0.00% | 22.35% | 0.00% | 25.21% | 24.95% | 25.31% | 24.63% | 21.31% |
| H2_5of6 | 0.00% | 0.00% | 18.38% | 0.00% | 25.18% | 0.00% | 25.01% | 22.61% | 21.31% |
| P_A1 | 0.00% | 0.00% | 22.33% | 19.01% | 25.13% | 26.12% | 25.36% | 25.56% | 24.77% |
| H1_252_3_WF | 0.00% | 0.00% | 22.33% | 19.01% | 25.13% | 26.12% | 25.36% | 25.56% | 24.77% |

### 2014-2016 mean_group

| run | Equity | Treasury | Credit | Real |
|---|---|---|---|---|
| B0 | 0.00% | 0.00% | 0.00% | 0.00% |
| B1 | 32.90% | 21.89% | 21.87% | 21.90% |
| B2 | 20.11% | 26.20% | 38.06% | 13.93% |
| B3 | 11.73% | 19.26% | 25.82% | 2.53% |
| REF_SPY | 91.21% | 0.00% | 0.00% | 0.00% |
| H1_252_3 | 17.89% | 24.60% | 19.88% | 0.98% |
| H1_252_4 | 15.31% | 25.30% | 27.34% | 1.98% |
| H1_126_3 | 12.91% | 20.48% | 26.82% | 2.63% |
| H1_126_4 | 15.59% | 24.04% | 28.09% | 3.38% |
| H2_4of6 | 11.23% | 6.56% | 17.87% | 0.00% |
| H2_5of6 | 6.18% | 1.56% | 9.53% | 0.00% |
| P_A1 | 17.87% | 24.59% | 19.88% | 0.98% |
| H1_252_3_WF | 17.87% | 24.59% | 19.88% | 0.98% |

### 2014-2016 mean_weight

| run | DBC | EEM | EFA | GLD | HYG | IEF | LQD | SPY | TLT |
|---|---|---|---|---|---|---|---|---|---|
| B0 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| B1 | 10.88% | 10.96% | 10.96% | 11.01% | 10.94% | 10.96% | 10.93% | 10.98% | 10.94% |
| B2 | 7.09% | 5.31% | 6.78% | 6.85% | 17.76% | 18.27% | 20.30% | 8.02% | 7.94% |
| B3 | 0.62% | 2.33% | 2.89% | 1.91% | 11.39% | 13.89% | 14.43% | 6.50% | 5.37% |
| REF_SPY | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 91.21% | 0.00% |
| H1_252_3 | 0.00% | 0.00% | 4.33% | 0.98% | 8.26% | 13.85% | 11.62% | 13.56% | 10.74% |
| H1_252_4 | 0.00% | 0.00% | 3.47% | 1.98% | 9.52% | 16.45% | 17.81% | 11.84% | 8.85% |
| H1_126_3 | 1.49% | 2.80% | 3.45% | 1.13% | 9.67% | 12.25% | 17.14% | 6.66% | 8.23% |
| H1_126_4 | 1.33% | 3.21% | 3.66% | 2.05% | 9.69% | 14.35% | 18.39% | 8.73% | 9.69% |
| H2_4of6 | 0.00% | 0.00% | 3.80% | 0.00% | 8.26% | 2.03% | 9.62% | 7.43% | 4.53% |
| H2_5of6 | 0.00% | 0.00% | 0.92% | 0.00% | 6.14% | 0.00% | 3.39% | 5.26% | 1.56% |
| P_A1 | 0.00% | 0.00% | 4.32% | 0.98% | 8.26% | 13.84% | 11.62% | 13.55% | 10.74% |
| H1_252_3_WF | 0.00% | 0.00% | 4.32% | 0.98% | 8.26% | 13.84% | 11.62% | 13.55% | 10.74% |

### 2017-2019

| run | total_return | cagr | volatility | mean_excess | sharpe_bil | utility | max_drawdown | decisions | turnover_annual | costs_usd | cost_ratio | mean_cash_plus_bil | mean_receivables | mean_risky | mean_target_risky | mean_bil | mean_cash_usd | n_returns | turnover |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B0 | 4.46% | 1.47% | 0.23% | -0.02% | -6.971 | -0.000 | -0.04% | 36 | 0.01x | 4.16 | 0.00% | 99.98% | 0.02% | 0.00% | 0.00% | 98.84% | 1.13% | 754 | 0.04x |
| B1 | 25.67% | 7.94% | 5.54% | 6.31% | 1.139 | 0.059 | -10.06% | 36 | 0.22x | 104.75 | 0.06% | 1.39% | 0.06% | 98.56% | 100.00% | 0.00% | 1.39% | 754 | 0.65x |
| B2 | 23.75% | 7.38% | 4.10% | 5.73% | 1.399 | 0.055 | -5.80% | 36 | 1.06x | 526.74 | 0.32% | 1.73% | 0.06% | 98.21% | 99.70% | 0.30% | 1.43% | 754 | 3.18x |
| B3 | 12.70% | 4.08% | 3.49% | 2.58% | 0.738 | 0.024 | -6.19% | 36 | 3.25x | 1299.25 | 0.97% | 36.16% | 0.06% | 63.79% | 64.77% | 34.81% | 1.35% | 754 | 9.72x |
| REF_SPY | 45.50% | 13.35% | 11.35% | 11.70% | 1.031 | 0.098 | -17.25% | 0 | 0.00x | 0.00 | 0.00% | 10.84% | 0.20% | 88.97% | n/a | 0.00% | 10.84% | 754 | 0.00x |
| H1_252_3 | 11.11% | 3.58% | 5.55% | 2.20% | 0.396 | 0.017 | -12.49% | 36 | 4.42x | 1924.38 | 1.32% | 36.95% | 0.06% | 62.99% | 63.58% | 35.79% | 1.16% | 754 | 13.21x |
| H1_252_4 | 16.75% | 5.31% | 5.73% | 3.86% | 0.673 | 0.034 | -11.01% | 36 | 3.45x | 1416.64 | 1.03% | 27.09% | 0.07% | 72.84% | 73.72% | 25.90% | 1.19% | 754 | 10.31x |
| H1_126_3 | 21.28% | 6.66% | 5.38% | 5.11% | 0.951 | 0.047 | -8.88% | 36 | 6.03x | 2587.80 | 1.81% | 37.12% | 0.05% | 62.82% | 63.55% | 35.94% | 1.18% | 754 | 18.05x |
| H1_126_4 | 18.67% | 5.89% | 5.52% | 4.40% | 0.796 | 0.039 | -8.15% | 36 | 5.25x | 2343.51 | 1.57% | 29.05% | 0.05% | 70.90% | 71.68% | 27.82% | 1.23% | 754 | 15.72x |
| H2_4of6 | 14.95% | 4.77% | 4.41% | 3.28% | 0.744 | 0.030 | -7.50% | 36 | 5.28x | 2195.04 | 1.58% | 50.83% | 0.06% | 49.12% | 49.64% | 49.65% | 1.18% | 754 | 15.80x |
| H2_5of6 | 7.14% | 2.33% | 2.99% | 0.87% | 0.293 | 0.007 | -6.17% | 36 | 2.49x | 806.49 | 0.74% | 72.36% | 0.05% | 27.59% | 27.89% | 71.19% | 1.17% | 754 | 7.44x |
| P_A1 | 17.12% | 5.42% | 5.30% | 3.94% | 0.745 | 0.035 | -8.88% | 36 | 5.60x | 1883.09 | 1.68% | 36.55% | 0.06% | 63.39% | 64.09% | 35.32% | 1.23% | 754 | 16.75x |
| H1_252_3_WF | 11.14% | 3.59% | 5.54% | 2.21% | 0.398 | 0.017 | -12.47% | 36 | 4.42x | 1455.54 | 1.32% | 36.97% | 0.06% | 62.97% | 63.58% | 35.79% | 1.18% | 754 | 13.21x |

### 2017-2019 max_group

| run | Equity | Treasury | Credit | Real |
|---|---|---|---|---|
| B0 | 0.00% | 0.00% | 0.00% | 0.00% |
| B1 | 34.54% | 23.40% | 22.46% | 22.85% |
| B2 | 29.12% | 32.95% | 42.90% | 17.15% |
| B3 | 29.79% | 26.31% | 41.95% | 23.11% |
| REF_SPY | 90.10% | 0.00% | 0.00% | 0.00% |
| H1_252_3 | 51.26% | 49.28% | 49.86% | 25.66% |
| H1_252_4 | 51.28% | 41.19% | 49.81% | 25.61% |
| H1_126_3 | 50.67% | 49.48% | 49.86% | 49.97% |
| H1_126_4 | 51.00% | 43.37% | 49.87% | 49.69% |
| H2_4of6 | 51.33% | 46.68% | 49.91% | 25.62% |
| H2_5of6 | 49.87% | 0.00% | 25.39% | 25.60% |
| P_A1 | 50.68% | 49.41% | 49.94% | 49.95% |
| H1_252_3_WF | 51.32% | 49.22% | 49.94% | 25.64% |

### 2017-2019 max_weight

| run | DBC | EEM | EFA | GLD | HYG | IEF | LQD | SPY | TLT |
|---|---|---|---|---|---|---|---|---|---|
| B0 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| B1 | 11.63% | 11.78% | 11.45% | 11.79% | 11.22% | 11.48% | 11.33% | 11.37% | 12.12% |
| B2 | 8.57% | 7.61% | 10.90% | 10.63% | 24.88% | 22.97% | 24.90% | 12.57% | 10.78% |
| B3 | 11.18% | 7.20% | 11.06% | 12.29% | 25.05% | 18.14% | 23.14% | 12.84% | 10.69% |
| REF_SPY | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 90.10% | 0.00% |
| H1_252_3 | 25.66% | 23.85% | 25.23% | 15.17% | 25.11% | 25.22% | 24.91% | 26.12% | 24.48% |
| H1_252_4 | 25.61% | 14.25% | 24.75% | 16.07% | 25.07% | 25.00% | 25.40% | 26.15% | 16.54% |
| H1_126_3 | 25.78% | 22.52% | 25.39% | 24.72% | 25.00% | 25.10% | 25.13% | 26.05% | 25.14% |
| H1_126_4 | 25.60% | 15.39% | 25.14% | 24.76% | 25.03% | 25.10% | 25.09% | 26.00% | 25.11% |
| H2_4of6 | 25.62% | 19.24% | 24.90% | 0.00% | 25.05% | 25.29% | 24.94% | 26.05% | 22.08% |
| H2_5of6 | 25.60% | 17.87% | 24.42% | 0.00% | 24.94% | 0.00% | 25.39% | 25.01% | 0.00% |
| P_A1 | 25.78% | 22.36% | 25.33% | 24.71% | 25.02% | 25.11% | 25.16% | 26.09% | 25.11% |
| H1_252_3_WF | 25.64% | 23.86% | 25.18% | 15.19% | 25.05% | 25.24% | 24.97% | 26.21% | 24.46% |

### 2017-2019 mean_group

| run | Equity | Treasury | Credit | Real |
|---|---|---|---|---|
| B0 | 0.00% | 0.00% | 0.00% | 0.00% |
| B1 | 32.94% | 21.84% | 21.84% | 21.93% |
| B2 | 20.72% | 26.12% | 37.58% | 13.80% |
| B3 | 17.24% | 9.08% | 29.48% | 7.98% |
| REF_SPY | 88.97% | 0.00% | 0.00% | 0.00% |
| H1_252_3 | 27.79% | 10.83% | 18.58% | 5.79% |
| H1_252_4 | 29.82% | 10.68% | 25.04% | 7.31% |
| H1_126_3 | 25.72% | 10.77% | 15.79% | 10.55% |
| H1_126_4 | 26.68% | 11.97% | 20.72% | 11.53% |
| H2_4of6 | 23.48% | 7.32% | 15.25% | 3.07% |
| H2_5of6 | 15.08% | 0.00% | 11.10% | 1.41% |
| P_A1 | 24.32% | 10.76% | 17.91% | 10.40% |
| H1_252_3_WF | 27.77% | 10.82% | 18.58% | 5.79% |

### 2017-2019 mean_weight

| run | DBC | EEM | EFA | GLD | HYG | IEF | LQD | SPY | TLT |
|---|---|---|---|---|---|---|---|---|---|
| B0 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| B1 | 10.96% | 11.00% | 10.98% | 10.97% | 10.93% | 10.92% | 10.92% | 10.95% | 10.92% |
| B2 | 6.05% | 5.08% | 7.77% | 7.74% | 18.82% | 18.13% | 18.76% | 7.86% | 7.99% |
| B3 | 3.90% | 3.55% | 5.88% | 4.08% | 17.02% | 5.95% | 12.45% | 7.81% | 3.14% |
| REF_SPY | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 88.97% | 0.00% |
| H1_252_3 | 5.40% | 5.94% | 7.50% | 0.39% | 12.37% | 7.54% | 6.21% | 14.35% | 3.28% |
| H1_252_4 | 5.81% | 5.34% | 10.17% | 1.50% | 15.56% | 7.49% | 9.48% | 14.32% | 3.19% |
| H1_126_3 | 7.29% | 4.55% | 8.79% | 3.25% | 7.42% | 6.87% | 8.37% | 12.38% | 3.90% |
| H1_126_4 | 7.36% | 4.72% | 9.37% | 4.16% | 10.28% | 7.53% | 10.44% | 12.59% | 4.44% |
| H2_4of6 | 3.07% | 3.07% | 6.07% | 0.00% | 9.69% | 4.70% | 5.56% | 14.33% | 2.62% |
| H2_5of6 | 1.41% | 0.95% | 4.89% | 0.00% | 6.26% | 0.00% | 4.85% | 9.24% | 0.00% |
| P_A1 | 7.15% | 3.49% | 6.18% | 3.25% | 11.00% | 6.87% | 6.91% | 14.65% | 3.89% |
| H1_252_3_WF | 5.40% | 5.94% | 7.50% | 0.40% | 12.37% | 7.54% | 6.21% | 14.34% | 3.28% |

### 2020-2022

| run | total_return | cagr | volatility | mean_excess | sharpe_bil | utility | max_drawdown | decisions | turnover_annual | costs_usd | cost_ratio | mean_cash_plus_bil | mean_receivables | mean_risky | mean_target_risky | mean_bil | mean_cash_usd | n_returns | turnover |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B0 | 1.66% | 0.55% | 0.20% | -0.01% | -3.136 | -0.000 | -0.21% | 36 | 0.00x | 1.28 | 0.00% | 99.99% | 0.01% | 0.00% | 0.00% | 98.92% | 1.07% | 756 | 0.01x |
| B1 | -1.41% | -0.47% | 10.32% | -0.50% | -0.048 | -0.021 | -17.83% | 36 | 1.05x | 556.90 | 0.31% | 12.28% | 0.04% | 87.68% | 88.99% | 10.93% | 1.35% | 756 | 3.14x |
| B2 | -5.35% | -1.82% | 9.13% | -1.97% | -0.216 | -0.032 | -18.80% | 36 | 1.34x | 745.13 | 0.40% | 8.26% | 0.04% | 91.69% | 93.06% | 6.87% | 1.40% | 756 | 4.01x |
| B3 | 2.58% | 0.85% | 5.06% | 0.42% | 0.083 | 0.000 | -9.59% | 36 | 2.45x | 1053.45 | 0.73% | 44.63% | 0.03% | 55.33% | 56.30% | 43.28% | 1.35% | 756 | 7.34x |
| REF_SPY | 21.51% | 6.71% | 21.78% | 8.32% | 0.382 | 0.012 | -29.95% | 0 | 0.00x | 0.00 | 0.00% | 11.48% | 0.16% | 88.36% | n/a | 0.00% | 11.48% | 756 | 0.00x |
| H1_252_3 | 7.92% | 2.57% | 7.67% | 2.28% | 0.297 | 0.014 | -8.63% | 36 | 3.39x | 1638.24 | 1.02% | 42.48% | 0.03% | 57.48% | 58.29% | 41.35% | 1.13% | 756 | 10.17x |
| H1_252_4 | 1.18% | 0.39% | 7.67% | 0.13% | 0.017 | -0.008 | -11.06% | 36 | 3.11x | 1430.65 | 0.93% | 36.55% | 0.03% | 63.42% | 64.32% | 35.36% | 1.19% | 756 | 9.34x |
| H1_126_3 | 4.06% | 1.34% | 9.53% | 1.23% | 0.129 | -0.001 | -17.33% | 36 | 6.11x | 2944.08 | 1.83% | 44.80% | 0.03% | 55.17% | 55.97% | 43.70% | 1.10% | 756 | 18.32x |
| H1_126_4 | 3.05% | 1.01% | 9.79% | 0.93% | 0.095 | -0.005 | -20.44% | 36 | 6.33x | 3120.07 | 1.90% | 40.73% | 0.03% | 59.24% | 60.07% | 39.61% | 1.12% | 756 | 18.98x |
| H2_4of6 | 6.00% | 1.96% | 5.48% | 1.54% | 0.281 | 0.011 | -7.59% | 36 | 3.63x | 1608.92 | 1.09% | 60.77% | 0.02% | 39.21% | 39.57% | 59.66% | 1.11% | 756 | 10.89x |
| H2_5of6 | 0.91% | 0.30% | 4.27% | -0.16% | -0.038 | -0.004 | -5.36% | 36 | 2.73x | 906.74 | 0.82% | 80.43% | 0.02% | 19.55% | 19.59% | 79.35% | 1.08% | 756 | 8.19x |
| P_A1 | 4.18% | 1.38% | 9.77% | 1.29% | 0.132 | -0.001 | -17.33% | 36 | 4.71x | 1717.27 | 1.41% | 40.31% | 0.04% | 59.65% | 60.60% | 39.12% | 1.20% | 756 | 14.13x |
| H1_252_3_WF | 7.90% | 2.57% | 7.67% | 2.27% | 0.296 | 0.014 | -8.63% | 36 | 3.38x | 1237.83 | 1.02% | 42.52% | 0.03% | 57.45% | 58.29% | 41.34% | 1.17% | 756 | 10.15x |

### 2020-2022 max_group

| run | Equity | Treasury | Credit | Real |
|---|---|---|---|---|
| B0 | 0.00% | 0.00% | 0.00% | 0.00% |
| B1 | 35.25% | 26.40% | 22.26% | 24.77% |
| B2 | 23.99% | 33.29% | 41.29% | 21.18% |
| B3 | 23.81% | 32.70% | 41.50% | 28.01% |
| REF_SPY | 90.06% | 0.00% | 0.00% | 0.00% |
| H1_252_3 | 50.07% | 43.44% | 49.96% | 53.04% |
| H1_252_4 | 48.56% | 40.91% | 49.94% | 52.82% |
| H1_126_3 | 50.34% | 45.85% | 49.76% | 49.50% |
| H1_126_4 | 50.63% | 40.41% | 49.61% | 43.53% |
| H2_4of6 | 49.41% | 43.52% | 49.95% | 49.09% |
| H2_5of6 | 43.18% | 43.83% | 25.15% | 28.07% |
| P_A1 | 50.29% | 44.52% | 49.54% | 53.07% |
| H1_252_3_WF | 49.85% | 43.44% | 49.94% | 53.08% |

### 2020-2022 max_weight

| run | DBC | EEM | EFA | GLD | HYG | IEF | LQD | SPY | TLT |
|---|---|---|---|---|---|---|---|---|---|
| B0 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| B1 | 12.95% | 11.83% | 12.11% | 12.59% | 11.15% | 12.97% | 11.26% | 11.61% | 13.45% |
| B2 | 9.38% | 8.84% | 9.06% | 13.62% | 25.05% | 24.75% | 21.76% | 9.69% | 9.43% |
| B3 | 12.65% | 7.03% | 10.58% | 15.36% | 24.90% | 24.68% | 17.90% | 10.82% | 10.60% |
| REF_SPY | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 90.06% | 0.00% |
| H1_252_3 | 27.76% | 12.98% | 25.11% | 26.64% | 25.02% | 26.15% | 25.31% | 25.33% | 18.87% |
| H1_252_4 | 27.35% | 11.87% | 20.14% | 25.64% | 24.89% | 26.39% | 25.37% | 24.00% | 24.75% |
| H1_126_3 | 27.98% | 21.27% | 25.21% | 26.57% | 25.35% | 25.07% | 24.96% | 25.36% | 25.19% |
| H1_126_4 | 28.02% | 17.72% | 20.99% | 25.19% | 25.38% | 24.94% | 25.66% | 24.59% | 18.75% |
| H2_4of6 | 27.88% | 13.00% | 24.86% | 25.21% | 25.02% | 25.00% | 25.28% | 25.18% | 18.94% |
| H2_5of6 | 28.07% | 12.99% | 23.07% | 0.00% | 25.02% | 24.82% | 25.15% | 20.21% | 19.26% |
| P_A1 | 27.76% | 21.27% | 24.99% | 26.57% | 25.35% | 24.88% | 24.87% | 25.17% | 20.90% |
| H1_252_3_WF | 27.76% | 12.96% | 25.11% | 26.65% | 25.00% | 26.05% | 25.27% | 25.28% | 18.91% |

### 2020-2022 mean_group

| run | Equity | Treasury | Credit | Real |
|---|---|---|---|---|
| B0 | 0.00% | 0.00% | 0.00% | 0.00% |
| B1 | 29.30% | 19.34% | 19.36% | 19.69% |
| B2 | 19.28% | 25.99% | 31.80% | 14.62% |
| B3 | 11.93% | 11.69% | 21.53% | 10.19% |
| REF_SPY | 88.36% | 0.00% | 0.00% | 0.00% |
| H1_252_3 | 15.27% | 11.99% | 13.54% | 16.68% |
| H1_252_4 | 15.43% | 13.38% | 17.97% | 16.64% |
| H1_126_3 | 17.64% | 9.67% | 12.16% | 15.69% |
| H1_126_4 | 17.62% | 9.21% | 17.53% | 14.87% |
| H2_4of6 | 10.66% | 8.27% | 10.19% | 10.08% |
| H2_5of6 | 6.55% | 4.56% | 4.07% | 4.38% |
| P_A1 | 20.45% | 9.34% | 12.25% | 17.61% |
| H1_252_3_WF | 15.26% | 11.98% | 13.53% | 16.68% |

### 2020-2022 mean_weight

| run | DBC | EEM | EFA | GLD | HYG | IEF | LQD | SPY | TLT |
|---|---|---|---|---|---|---|---|---|---|
| B0 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| B1 | 9.90% | 9.77% | 9.79% | 9.79% | 9.69% | 9.69% | 9.66% | 9.74% | 9.64% |
| B2 | 6.15% | 5.82% | 6.87% | 8.47% | 17.35% | 18.51% | 14.46% | 6.60% | 7.48% |
| B3 | 4.97% | 2.67% | 4.05% | 5.21% | 12.40% | 8.64% | 9.12% | 5.21% | 3.05% |
| REF_SPY | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 88.36% | 0.00% |
| H1_252_3 | 9.85% | 0.69% | 4.68% | 6.83% | 7.55% | 8.18% | 5.99% | 9.90% | 3.81% |
| H1_252_4 | 9.34% | 1.21% | 5.62% | 7.30% | 9.52% | 7.90% | 8.44% | 8.59% | 5.48% |
| H1_126_3 | 8.13% | 2.48% | 5.33% | 7.57% | 8.00% | 4.79% | 4.16% | 9.83% | 4.88% |
| H1_126_4 | 7.60% | 3.38% | 5.61% | 7.27% | 9.28% | 5.24% | 8.25% | 8.63% | 3.97% |
| H2_4of6 | 7.10% | 0.69% | 3.35% | 2.98% | 6.80% | 6.24% | 3.39% | 6.63% | 2.03% |
| H2_5of6 | 4.38% | 0.69% | 1.62% | 0.00% | 2.08% | 3.52% | 1.98% | 4.24% | 1.04% |
| P_A1 | 10.47% | 2.79% | 7.11% | 7.14% | 8.92% | 5.36% | 3.33% | 10.55% | 3.98% |
| H1_252_3_WF | 9.85% | 0.69% | 4.69% | 6.83% | 7.55% | 8.17% | 5.98% | 9.88% | 3.80% |

### 2009

| run | total_return | cagr | volatility | mean_excess | sharpe_bil | utility | max_drawdown | decisions | turnover_annual | costs_usd | cost_ratio | mean_cash_plus_bil | mean_receivables | mean_risky | mean_target_risky | mean_bil | mean_cash_usd | n_returns | turnover |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B0 | 0.04% | 0.04% | 0.70% | -0.23% | -1.010 | -0.002 | -0.24% | 12 | 0.99x | 99.40 | 0.10% | 100.00% | 0.00% | 0.00% | 0.00% | 98.99% | 1.01% | 252 | 0.99x |
| B1 | 10.35% | 10.35% | 6.92% | 9.82% | 1.407 | 0.091 | -4.87% | 12 | 2.07x | 211.26 | 0.21% | 46.02% | 0.04% | 53.94% | 54.42% | 44.62% | 1.41% | 252 | 2.07x |
| B2 | 8.87% | 8.87% | 6.87% | 8.46% | 1.218 | 0.077 | -6.35% | 12 | 2.52x | 254.04 | 0.25% | 24.81% | 0.06% | 75.13% | 76.08% | 23.36% | 1.45% | 252 | 2.52x |
| B3 | 0.22% | 0.22% | 4.27% | 0.04% | 0.009 | -0.002 | -4.57% | 12 | 3.49x | 343.88 | 0.35% | 55.18% | 0.03% | 44.79% | 45.37% | 53.91% | 1.28% | 252 | 3.49x |
| REF_SPY | 25.33% | 25.33% | 26.27% | 25.75% | 0.978 | 0.153 | -26.95% | 1 | 0.99x | 99.21 | 0.10% | 1.31% | 0.21% | 98.48% | 100.00% | 0.00% | 1.31% | 252 | 0.99x |
| H1_252_3 | 2.92% | 2.92% | 6.49% | 2.81% | 0.433 | 0.022 | -7.47% | 12 | 4.46x | 437.50 | 0.45% | 38.36% | 0.04% | 61.60% | 62.38% | 37.12% | 1.24% | 252 | 4.46x |
| H1_252_4 | 3.38% | 3.38% | 6.83% | 3.28% | 0.481 | 0.026 | -7.07% | 12 | 3.05x | 300.78 | 0.31% | 33.06% | 0.04% | 66.90% | 67.66% | 31.75% | 1.31% | 252 | 3.05x |
| H1_126_3 | 1.69% | 1.69% | 6.95% | 1.64% | 0.235 | 0.009 | -6.46% | 12 | 6.64x | 645.25 | 0.66% | 44.84% | 0.04% | 55.12% | 56.02% | 43.63% | 1.21% | 252 | 6.64x |
| H1_126_4 | 1.44% | 1.44% | 7.30% | 1.43% | 0.194 | 0.006 | -7.69% | 12 | 5.10x | 495.45 | 0.51% | 39.04% | 0.05% | 60.91% | 61.80% | 37.81% | 1.24% | 252 | 5.10x |
| H2_4of6 | 2.06% | 2.06% | 4.00% | 1.85% | 0.462 | 0.016 | -5.54% | 12 | 4.34x | 424.82 | 0.43% | 69.37% | 0.02% | 30.61% | 31.26% | 68.20% | 1.17% | 252 | 4.34x |
| H2_5of6 | 0.65% | 0.65% | 1.72% | 0.39% | 0.250 | 0.004 | -1.12% | 12 | 2.39x | 240.02 | 0.24% | 87.73% | 0.01% | 12.26% | 12.32% | 86.62% | 1.11% | 252 | 2.39x |

### 2009 max_group

| run | Equity | Treasury | Credit | Real |
|---|---|---|---|---|
| B0 | 0.00% | 0.00% | 0.00% | 0.00% |
| B1 | 29.77% | 19.05% | 19.64% | 19.49% |
| B2 | 23.36% | 32.17% | 33.01% | 18.70% |
| B3 | 21.19% | 28.30% | 32.57% | 14.95% |
| REF_SPY | 99.33% | 0.00% | 0.00% | 0.00% |
| H1_252_3 | 13.14% | 46.62% | 49.35% | 26.81% |
| H1_252_4 | 12.56% | 45.01% | 50.00% | 23.43% |
| H1_126_3 | 23.58% | 46.62% | 49.29% | 26.66% |
| H1_126_4 | 32.89% | 41.32% | 49.42% | 24.91% |
| H2_4of6 | 0.00% | 46.62% | 49.14% | 26.88% |
| H2_5of6 | 0.00% | 0.00% | 47.06% | 0.00% |

### 2009 max_weight

| run | DBC | EEM | EFA | GLD | HYG | IEF | LQD | SPY | TLT |
|---|---|---|---|---|---|---|---|---|---|
| B0 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| B1 | 9.81% | 10.00% | 9.92% | 9.86% | 10.05% | 9.63% | 9.64% | 9.99% | 9.42% |
| B2 | 7.23% | 6.18% | 7.86% | 11.60% | 13.34% | 22.12% | 19.98% | 9.34% | 10.15% |
| B3 | 6.07% | 5.75% | 7.32% | 10.74% | 13.15% | 21.84% | 19.53% | 8.59% | 9.14% |
| REF_SPY | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 99.33% | 0.00% |
| H1_252_3 | 0.00% | 13.14% | 0.00% | 26.81% | 25.25% | 25.18% | 25.35% | 0.00% | 22.43% |
| H1_252_4 | 0.00% | 12.56% | 0.00% | 23.43% | 25.62% | 25.30% | 25.30% | 0.00% | 20.42% |
| H1_126_3 | 13.33% | 12.80% | 20.16% | 19.77% | 25.22% | 25.01% | 24.84% | 19.82% | 21.80% |
| H1_126_4 | 11.66% | 8.75% | 14.77% | 18.12% | 25.18% | 24.96% | 24.49% | 18.18% | 17.47% |
| H2_4of6 | 0.00% | 0.00% | 0.00% | 26.88% | 25.26% | 25.01% | 25.39% | 0.00% | 21.80% |
| H2_5of6 | 0.00% | 0.00% | 0.00% | 0.00% | 22.77% | 0.00% | 24.95% | 0.00% | 0.00% |

### 2009 mean_group

| run | Equity | Treasury | Credit | Real |
|---|---|---|---|---|
| B0 | 0.00% | 0.00% | 0.00% | 0.00% |
| B1 | 18.32% | 11.70% | 11.87% | 12.04% |
| B2 | 14.61% | 23.63% | 23.78% | 13.10% |
| B3 | 4.43% | 22.79% | 11.45% | 6.11% |
| REF_SPY | 98.48% | 0.00% | 0.00% | 0.00% |
| H1_252_3 | 1.13% | 31.37% | 18.47% | 10.63% |
| H1_252_4 | 1.89% | 32.99% | 18.05% | 13.96% |
| H1_126_3 | 10.43% | 16.23% | 23.22% | 5.24% |
| H1_126_4 | 13.14% | 15.76% | 25.01% | 6.99% |
| H2_4of6 | 0.00% | 5.16% | 18.49% | 6.96% |
| H2_5of6 | 0.00% | 0.00% | 12.26% | 0.00% |

### 2009 mean_weight

| run | DBC | EEM | EFA | GLD | HYG | IEF | LQD | SPY | TLT |
|---|---|---|---|---|---|---|---|---|---|
| B0 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| B1 | 6.04% | 6.20% | 6.07% | 6.00% | 5.97% | 5.90% | 5.90% | 6.05% | 5.81% |
| B2 | 5.35% | 3.87% | 4.89% | 7.75% | 8.18% | 15.73% | 15.61% | 5.85% | 7.90% |
| B3 | 0.52% | 1.34% | 1.71% | 5.60% | 2.87% | 15.89% | 8.58% | 1.38% | 6.90% |
| REF_SPY | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 98.48% | 0.00% |
| H1_252_3 | 0.00% | 1.13% | 0.00% | 10.63% | 6.07% | 19.66% | 12.40% | 0.00% | 11.71% |
| H1_252_4 | 0.00% | 1.89% | 0.00% | 13.96% | 5.66% | 20.52% | 12.39% | 0.00% | 12.48% |
| H1_126_3 | 1.12% | 3.60% | 5.11% | 4.12% | 9.68% | 9.64% | 13.54% | 1.71% | 6.58% |
| H1_126_4 | 0.99% | 2.47% | 4.79% | 6.01% | 10.06% | 9.49% | 14.95% | 5.88% | 6.28% |
| H2_4of6 | 0.00% | 0.00% | 0.00% | 6.96% | 6.07% | 1.97% | 12.42% | 0.00% | 3.19% |
| H2_5of6 | 0.00% | 0.00% | 0.00% | 0.00% | 1.96% | 0.00% | 10.30% | 0.00% | 0.00% |

### 2010

| run | total_return | cagr | volatility | mean_excess | sharpe_bil | utility | max_drawdown | decisions | turnover_annual | costs_usd | cost_ratio | mean_cash_plus_bil | mean_receivables | mean_risky | mean_target_risky | mean_bil | mean_cash_usd | n_returns | turnover |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B0 | -0.04% | -0.04% | 0.29% | 0.00% | 0.137 | 0.000 | -0.06% | 12 | 0.00x | 0.05 | 0.00% | 100.00% | 0.00% | 0.00% | 0.00% | 98.99% | 1.01% | 252 | 0.00x |
| B1 | 13.26% | 13.26% | 9.34% | 12.93% | 1.378 | 0.116 | -5.78% | 12 | 0.85x | 95.26 | 0.08% | 4.41% | 0.07% | 95.53% | 97.01% | 2.95% | 1.46% | 252 | 0.85x |
| B2 | 13.43% | 13.43% | 6.36% | 12.85% | 2.005 | 0.122 | -3.76% | 12 | 1.01x | 116.55 | 0.10% | 1.82% | 0.08% | 98.10% | 99.71% | 0.30% | 1.53% | 252 | 1.01x |
| B3 | 9.78% | 9.78% | 6.71% | 9.60% | 1.423 | 0.089 | -4.76% | 12 | 2.88x | 295.18 | 0.29% | 11.64% | 0.07% | 88.29% | 89.40% | 10.16% | 1.48% | 252 | 2.88x |
| REF_SPY | 14.51% | 14.51% | 17.38% | 15.10% | 0.867 | 0.106 | -15.25% | 0 | 0.00x | 0.00 | 0.00% | 2.90% | 0.22% | 96.89% | n/a | 0.00% | 2.90% | 252 | 0.00x |
| H1_252_3 | 6.70% | 6.70% | 6.39% | 6.73% | 1.050 | 0.061 | -5.37% | 12 | 3.78x | 397.67 | 0.38% | 33.04% | 0.07% | 66.89% | 67.74% | 31.72% | 1.32% | 252 | 3.78x |
| H1_252_4 | 3.83% | 3.83% | 7.24% | 4.07% | 0.559 | 0.033 | -5.97% | 12 | 2.82x | 290.21 | 0.28% | 21.28% | 0.07% | 78.65% | 79.61% | 19.93% | 1.35% | 252 | 2.82x |
| H1_126_3 | 0.95% | 0.95% | 6.62% | 1.21% | 0.182 | 0.005 | -5.09% | 12 | 5.64x | 584.50 | 0.56% | 31.42% | 0.07% | 68.51% | 69.46% | 30.21% | 1.21% | 252 | 5.64x |
| H1_126_4 | 3.91% | 3.91% | 7.38% | 4.15% | 0.559 | 0.033 | -4.90% | 12 | 4.65x | 483.94 | 0.46% | 21.72% | 0.08% | 78.21% | 79.30% | 20.42% | 1.30% | 252 | 4.65x |
| H2_4of6 | 6.19% | 6.19% | 5.66% | 6.21% | 1.091 | 0.057 | -4.37% | 12 | 5.45x | 556.75 | 0.54% | 38.11% | 0.06% | 61.83% | 62.30% | 36.88% | 1.23% | 252 | 5.45x |
| H2_5of6 | -0.53% | -0.53% | 3.70% | -0.42% | -0.113 | -0.006 | -3.74% | 12 | 6.01x | 595.36 | 0.60% | 80.90% | 0.01% | 19.09% | 19.43% | 79.84% | 1.06% | 252 | 6.01x |

### 2010 max_group

| run | Equity | Treasury | Credit | Real |
|---|---|---|---|---|
| B0 | 0.00% | 0.00% | 0.00% | 0.00% |
| B1 | 34.71% | 24.16% | 22.19% | 22.65% |
| B2 | 23.56% | 31.18% | 41.38% | 19.36% |
| B3 | 23.65% | 30.72% | 43.62% | 19.26% |
| REF_SPY | 97.66% | 0.00% | 0.00% | 0.00% |
| H1_252_3 | 42.36% | 24.93% | 50.50% | 22.84% |
| H1_252_4 | 43.42% | 25.01% | 49.80% | 17.00% |
| H1_126_3 | 25.65% | 49.18% | 50.07% | 46.41% |
| H1_126_4 | 25.81% | 39.39% | 50.06% | 33.49% |
| H2_4of6 | 42.55% | 24.94% | 50.43% | 22.87% |
| H2_5of6 | 18.05% | 25.05% | 49.42% | 22.22% |

### 2010 max_weight

| run | DBC | EEM | EFA | GLD | HYG | IEF | LQD | SPY | TLT |
|---|---|---|---|---|---|---|---|---|---|
| B0 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| B1 | 11.76% | 11.70% | 11.67% | 11.82% | 10.95% | 11.86% | 11.45% | 11.46% | 12.30% |
| B2 | 8.08% | 6.54% | 7.06% | 11.32% | 22.63% | 21.08% | 25.02% | 10.01% | 10.93% |
| B3 | 8.07% | 6.56% | 7.07% | 11.22% | 22.65% | 21.14% | 25.01% | 10.08% | 9.62% |
| REF_SPY | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 97.66% | 0.00% |
| H1_252_3 | 0.00% | 17.74% | 0.00% | 22.84% | 25.64% | 24.93% | 25.43% | 25.19% | 0.00% |
| H1_252_4 | 0.00% | 11.90% | 13.74% | 17.00% | 25.25% | 25.01% | 25.65% | 21.07% | 0.00% |
| H1_126_3 | 22.54% | 0.00% | 0.00% | 24.20% | 25.33% | 25.24% | 25.38% | 25.65% | 24.09% |
| H1_126_4 | 16.17% | 10.89% | 0.00% | 20.71% | 25.46% | 24.93% | 25.66% | 22.41% | 14.50% |
| H2_4of6 | 0.00% | 17.80% | 0.00% | 22.87% | 25.61% | 24.94% | 25.40% | 25.28% | 0.00% |
| H2_5of6 | 0.00% | 0.00% | 0.00% | 22.22% | 24.50% | 25.05% | 25.47% | 18.05% | 0.00% |

### 2010 mean_group

| run | Equity | Treasury | Credit | Real |
|---|---|---|---|---|
| B0 | 0.00% | 0.00% | 0.00% | 0.00% |
| B1 | 32.25% | 20.93% | 21.02% | 21.33% |
| B2 | 18.24% | 27.49% | 37.82% | 14.55% |
| B3 | 18.13% | 18.38% | 38.30% | 13.47% |
| REF_SPY | 96.89% | 0.00% | 0.00% | 0.00% |
| H1_252_3 | 12.24% | 4.25% | 41.07% | 9.33% |
| H1_252_4 | 13.29% | 12.21% | 43.56% | 9.59% |
| H1_126_3 | 8.79% | 17.07% | 30.92% | 11.73% |
| H1_126_4 | 10.60% | 17.88% | 38.69% | 11.04% |
| H2_4of6 | 11.10% | 2.16% | 39.22% | 9.34% |
| H2_5of6 | 1.37% | 2.17% | 12.20% | 3.34% |

### 2010 mean_weight

| run | DBC | EEM | EFA | GLD | HYG | IEF | LQD | SPY | TLT |
|---|---|---|---|---|---|---|---|---|---|
| B0 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| B1 | 10.67% | 10.77% | 10.76% | 10.66% | 10.52% | 10.51% | 10.49% | 10.72% | 10.43% |
| B2 | 6.73% | 5.15% | 5.53% | 7.82% | 15.59% | 18.71% | 22.23% | 7.56% | 8.79% |
| B3 | 5.60% | 5.22% | 5.21% | 7.87% | 15.88% | 13.76% | 22.42% | 7.70% | 4.62% |
| REF_SPY | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 96.89% | 0.00% |
| H1_252_3 | 0.00% | 3.95% | 0.00% | 9.33% | 22.44% | 4.25% | 18.63% | 8.28% | 0.00% |
| H1_252_4 | 0.00% | 4.11% | 1.01% | 9.59% | 22.69% | 12.21% | 20.86% | 8.17% | 0.00% |
| H1_126_3 | 1.86% | 0.00% | 0.00% | 9.87% | 16.34% | 12.51% | 14.59% | 8.79% | 4.56% |
| H1_126_4 | 1.33% | 2.47% | 0.00% | 9.70% | 16.11% | 12.48% | 22.58% | 8.13% | 5.40% |
| H2_4of6 | 0.00% | 2.81% | 0.00% | 9.34% | 20.61% | 2.16% | 18.60% | 8.29% | 0.00% |
| H2_5of6 | 0.00% | 0.00% | 0.00% | 3.34% | 1.91% | 2.17% | 10.29% | 1.37% | 0.00% |

### 2011

| run | total_return | cagr | volatility | mean_excess | sharpe_bil | utility | max_drawdown | decisions | turnover_annual | costs_usd | cost_ratio | mean_cash_plus_bil | mean_receivables | mean_risky | mean_target_risky | mean_bil | mean_cash_usd | n_returns | turnover |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B0 | -0.04% | -0.04% | 0.26% | 0.00% | 0.147 | 0.000 | -0.09% | 12 | 0.00x | 0.00 | 0.00% | 100.00% | 0.00% | 0.00% | 0.00% | 98.99% | 1.01% | 252 | 0.00x |
| B1 | 4.60% | 4.60% | 9.70% | 5.01% | 0.515 | 0.036 | -6.23% | 12 | 0.73x | 95.17 | 0.07% | 5.84% | 0.07% | 94.09% | 95.50% | 4.46% | 1.38% | 252 | 0.73x |
| B2 | 7.90% | 7.90% | 6.78% | 7.87% | 1.158 | 0.072 | -4.23% | 12 | 1.04x | 134.67 | 0.10% | 2.18% | 0.07% | 97.75% | 99.29% | 0.69% | 1.49% | 252 | 1.04x |
| B3 | 5.32% | 5.32% | 5.86% | 5.39% | 0.920 | 0.049 | -4.15% | 12 | 2.14x | 244.74 | 0.21% | 8.93% | 0.07% | 91.00% | 92.39% | 7.45% | 1.48% | 252 | 2.14x |
| REF_SPY | 1.78% | 1.78% | 21.86% | 4.19% | 0.192 | -0.030 | -17.77% | 0 | 0.00x | 0.00 | 0.00% | 4.36% | 0.22% | 95.42% | n/a | 0.00% | 4.36% | 252 | 0.00x |
| H1_252_3 | 3.73% | 3.73% | 7.59% | 3.99% | 0.524 | 0.031 | -6.49% | 12 | 6.28x | 706.53 | 0.63% | 32.29% | 0.05% | 67.66% | 68.55% | 31.14% | 1.15% | 252 | 6.28x |
| H1_252_4 | 0.82% | 0.82% | 7.06% | 1.11% | 0.157 | 0.004 | -6.42% | 12 | 4.19x | 460.78 | 0.42% | 22.62% | 0.07% | 77.32% | 78.48% | 21.38% | 1.24% | 252 | 4.19x |
| H1_126_3 | 8.84% | 8.84% | 6.93% | 8.75% | 1.261 | 0.080 | -4.46% | 12 | 5.28x | 557.64 | 0.53% | 34.11% | 0.05% | 65.83% | 66.70% | 32.97% | 1.15% | 252 | 5.28x |
| H1_126_4 | 13.01% | 13.01% | 8.04% | 12.60% | 1.564 | 0.116 | -4.21% | 12 | 3.98x | 433.73 | 0.40% | 23.09% | 0.06% | 76.85% | 77.94% | 21.83% | 1.26% | 252 | 3.98x |
| H2_4of6 | 4.60% | 4.60% | 6.10% | 4.72% | 0.771 | 0.042 | -3.76% | 12 | 6.24x | 694.01 | 0.62% | 45.89% | 0.05% | 54.06% | 54.81% | 44.71% | 1.19% | 252 | 6.24x |
| H2_5of6 | 1.87% | 1.87% | 4.65% | 2.00% | 0.428 | 0.017 | -3.61% | 12 | 4.89x | 497.31 | 0.49% | 69.00% | 0.04% | 30.97% | 31.52% | 67.85% | 1.15% | 252 | 4.89x |

### 2011 max_group

| run | Equity | Treasury | Credit | Real |
|---|---|---|---|---|
| B0 | 0.00% | 0.00% | 0.00% | 0.00% |
| B1 | 33.60% | 24.53% | 22.50% | 23.77% |
| B2 | 26.53% | 30.62% | 43.84% | 19.15% |
| B3 | 26.59% | 30.66% | 43.86% | 19.21% |
| REF_SPY | 96.37% | 0.00% | 0.00% | 0.00% |
| H1_252_3 | 25.31% | 46.56% | 50.42% | 46.33% |
| H1_252_4 | 21.81% | 37.81% | 50.22% | 40.52% |
| H1_126_3 | 43.28% | 46.03% | 25.21% | 50.28% |
| H1_126_4 | 39.88% | 40.61% | 47.77% | 34.06% |
| H2_4of6 | 25.24% | 46.31% | 49.42% | 41.51% |
| H2_5of6 | 25.37% | 24.80% | 25.37% | 41.56% |

### 2011 max_weight

| run | DBC | EEM | EFA | GLD | HYG | IEF | LQD | SPY | TLT |
|---|---|---|---|---|---|---|---|---|---|
| B0 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| B1 | 11.46% | 11.59% | 11.41% | 13.02% | 11.20% | 11.86% | 11.42% | 11.37% | 12.84% |
| B2 | 10.45% | 6.81% | 7.83% | 10.39% | 23.02% | 21.71% | 25.37% | 12.06% | 9.91% |
| B3 | 10.01% | 6.81% | 7.84% | 10.44% | 23.04% | 20.99% | 25.20% | 12.08% | 9.93% |
| REF_SPY | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 96.37% | 0.00% |
| H1_252_3 | 26.36% | 0.00% | 0.00% | 28.92% | 25.43% | 25.07% | 26.23% | 25.31% | 21.52% |
| H1_252_4 | 20.69% | 0.00% | 0.00% | 27.50% | 25.29% | 25.23% | 26.27% | 21.81% | 12.58% |
| H1_126_3 | 24.98% | 18.17% | 0.00% | 25.46% | 25.21% | 25.56% | 25.06% | 25.50% | 21.35% |
| H1_126_4 | 15.61% | 15.25% | 14.93% | 20.44% | 25.31% | 25.08% | 25.23% | 25.28% | 16.03% |
| H2_4of6 | 17.99% | 0.00% | 0.00% | 27.94% | 25.41% | 24.89% | 25.41% | 25.24% | 21.49% |
| H2_5of6 | 17.98% | 0.00% | 0.00% | 24.65% | 25.37% | 24.80% | 0.00% | 25.37% | 0.00% |

### 2011 mean_group

| run | Equity | Treasury | Credit | Real |
|---|---|---|---|---|
| B0 | 0.00% | 0.00% | 0.00% | 0.00% |
| B1 | 30.93% | 21.22% | 20.92% | 21.02% |
| B2 | 19.41% | 25.07% | 38.37% | 14.90% |
| B3 | 16.76% | 23.41% | 36.52% | 14.31% |
| REF_SPY | 95.42% | 0.00% | 0.00% | 0.00% |
| H1_252_3 | 9.45% | 8.85% | 24.65% | 24.71% |
| H1_252_4 | 8.63% | 9.98% | 38.81% | 19.90% |
| H1_126_3 | 13.45% | 16.33% | 20.69% | 15.37% |
| H1_126_4 | 13.19% | 18.00% | 26.34% | 19.32% |
| H2_4of6 | 7.40% | 8.87% | 22.64% | 15.14% |
| H2_5of6 | 5.44% | 2.03% | 12.51% | 10.99% |

### 2011 mean_weight

| run | DBC | EEM | EFA | GLD | HYG | IEF | LQD | SPY | TLT |
|---|---|---|---|---|---|---|---|---|---|
| B0 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| B1 | 10.45% | 10.28% | 10.27% | 10.58% | 10.42% | 10.57% | 10.50% | 10.38% | 10.65% |
| B2 | 6.98% | 5.39% | 5.68% | 7.92% | 16.35% | 17.04% | 22.01% | 8.34% | 8.03% |
| B3 | 6.66% | 4.22% | 4.43% | 7.65% | 14.99% | 16.33% | 21.54% | 8.11% | 7.08% |
| REF_SPY | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 95.42% | 0.00% |
| H1_252_3 | 8.40% | 0.00% | 0.00% | 16.31% | 16.31% | 6.13% | 8.33% | 9.45% | 2.72% |
| H1_252_4 | 7.66% | 0.00% | 0.00% | 12.24% | 16.32% | 8.09% | 22.49% | 8.63% | 1.89% |
| H1_126_3 | 7.28% | 1.41% | 0.00% | 8.09% | 10.39% | 12.50% | 10.30% | 12.04% | 3.83% |
| H1_126_4 | 6.78% | 1.18% | 1.33% | 12.55% | 13.99% | 12.45% | 12.35% | 10.68% | 5.54% |
| H2_4of6 | 4.34% | 0.00% | 0.00% | 10.81% | 16.31% | 6.15% | 6.33% | 7.40% | 2.72% |
| H2_5of6 | 4.34% | 0.00% | 0.00% | 6.65% | 12.51% | 2.03% | 0.00% | 5.44% | 0.00% |

### 2012

| run | total_return | cagr | volatility | mean_excess | sharpe_bil | utility | max_drawdown | decisions | turnover_annual | costs_usd | cost_ratio | mean_cash_plus_bil | mean_receivables | mean_risky | mean_target_risky | mean_bil | mean_cash_usd | n_returns | turnover |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B0 | -0.04% | -0.04% | 0.23% | 0.00% | 0.191 | 0.000 | -0.04% | 12 | 0.00x | 0.00 | 0.00% | 100.00% | 0.00% | 0.00% | 0.00% | 98.99% | 1.01% | 250 | 0.00x |
| B1 | 8.89% | 8.96% | 6.48% | 8.84% | 1.355 | 0.082 | -5.58% | 12 | 0.76x | 102.67 | 0.08% | 7.56% | 0.06% | 92.38% | 93.59% | 6.15% | 1.41% | 250 | 0.76x |
| B2 | 8.46% | 8.53% | 4.66% | 8.34% | 1.772 | 0.080 | -3.82% | 12 | 0.96x | 132.02 | 0.09% | 1.95% | 0.06% | 97.99% | 99.48% | 0.49% | 1.46% | 250 | 0.95x |
| B3 | 5.09% | 5.13% | 2.58% | 5.08% | 1.950 | 0.050 | -1.69% | 12 | 2.81x | 335.39 | 0.28% | 30.85% | 0.05% | 69.09% | 70.37% | 29.45% | 1.40% | 250 | 2.79x |
| REF_SPY | 15.03% | 15.16% | 11.97% | 14.88% | 1.239 | 0.127 | -9.15% | 0 | 0.00x | 0.00 | 0.00% | 5.73% | 0.22% | 94.05% | n/a | 0.00% | 5.73% | 250 | 0.00x |
| H1_252_3 | 6.57% | 6.63% | 3.93% | 6.54% | 1.667 | 0.063 | -2.45% | 12 | 3.20x | 376.49 | 0.32% | 34.53% | 0.04% | 65.43% | 66.34% | 33.30% | 1.23% | 250 | 3.18x |
| H1_252_4 | 6.47% | 6.53% | 3.60% | 6.43% | 1.783 | 0.062 | -2.99% | 12 | 1.23x | 135.83 | 0.12% | 18.81% | 0.05% | 81.14% | 82.43% | 17.39% | 1.42% | 250 | 1.22x |
| H1_126_3 | 4.03% | 4.06% | 3.98% | 4.11% | 1.024 | 0.039 | -3.59% | 12 | 5.02x | 567.37 | 0.50% | 33.27% | 0.05% | 66.68% | 67.60% | 32.03% | 1.23% | 250 | 4.98x |
| H1_126_4 | 6.05% | 6.10% | 4.17% | 6.05% | 1.434 | 0.058 | -2.76% | 12 | 4.38x | 532.05 | 0.43% | 19.70% | 0.06% | 80.24% | 81.35% | 18.35% | 1.35% | 250 | 4.35x |
| H2_4of6 | 4.06% | 4.10% | 2.63% | 4.09% | 1.558 | 0.040 | -1.75% | 12 | 4.54x | 521.39 | 0.45% | 51.71% | 0.03% | 48.26% | 49.18% | 50.58% | 1.14% | 250 | 4.50x |
| H2_5of6 | 1.62% | 1.64% | 1.79% | 1.68% | 0.942 | 0.016 | -1.23% | 12 | 4.89x | 497.14 | 0.49% | 72.42% | 0.02% | 27.56% | 28.02% | 71.30% | 1.12% | 250 | 4.85x |

### 2012 max_group

| run | Equity | Treasury | Credit | Real |
|---|---|---|---|---|
| B0 | 0.00% | 0.00% | 0.00% | 0.00% |
| B1 | 34.33% | 24.16% | 22.54% | 22.63% |
| B2 | 22.43% | 29.60% | 40.83% | 17.38% |
| B3 | 19.87% | 26.20% | 39.06% | 14.54% |
| REF_SPY | 94.85% | 0.00% | 0.00% | 0.00% |
| H1_252_3 | 18.37% | 44.49% | 50.07% | 23.37% |
| H1_252_4 | 13.86% | 37.61% | 49.69% | 13.07% |
| H1_126_3 | 21.76% | 44.46% | 49.55% | 23.38% |
| H1_126_4 | 28.97% | 38.09% | 49.89% | 13.45% |
| H2_4of6 | 18.37% | 44.51% | 49.69% | 23.33% |
| H2_5of6 | 15.82% | 44.69% | 49.73% | 0.00% |

### 2012 max_weight

| run | DBC | EEM | EFA | GLD | HYG | IEF | LQD | SPY | TLT |
|---|---|---|---|---|---|---|---|---|---|
| B0 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| B1 | 11.62% | 11.62% | 11.51% | 11.38% | 11.21% | 11.74% | 11.48% | 11.29% | 12.43% |
| B2 | 9.22% | 6.11% | 6.23% | 8.27% | 17.84% | 21.46% | 25.02% | 11.04% | 8.14% |
| B3 | 6.48% | 5.86% | 5.99% | 8.13% | 16.88% | 19.04% | 23.72% | 9.05% | 7.17% |
| REF_SPY | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 94.85% | 0.00% |
| H1_252_3 | 0.00% | 0.00% | 0.00% | 23.37% | 25.35% | 25.00% | 25.14% | 18.37% | 20.38% |
| H1_252_4 | 0.00% | 0.00% | 0.00% | 13.07% | 24.89% | 25.14% | 25.18% | 13.86% | 12.86% |
| H1_126_3 | 0.00% | 0.00% | 13.21% | 23.38% | 25.14% | 25.08% | 25.20% | 21.76% | 20.35% |
| H1_126_4 | 0.00% | 10.80% | 11.46% | 13.45% | 25.04% | 25.60% | 25.11% | 19.63% | 13.31% |
| H2_4of6 | 0.00% | 0.00% | 0.00% | 23.33% | 25.05% | 25.21% | 25.31% | 18.37% | 20.37% |
| H2_5of6 | 0.00% | 0.00% | 0.00% | 0.00% | 24.89% | 24.66% | 25.23% | 15.82% | 20.39% |

### 2012 mean_group

| run | Equity | Treasury | Credit | Real |
|---|---|---|---|---|
| B0 | 0.00% | 0.00% | 0.00% | 0.00% |
| B1 | 30.96% | 20.42% | 20.48% | 20.52% |
| B2 | 18.80% | 26.20% | 38.54% | 14.45% |
| B3 | 9.43% | 21.95% | 32.84% | 4.87% |
| REF_SPY | 94.05% | 0.00% | 0.00% | 0.00% |
| H1_252_3 | 2.77% | 30.16% | 30.69% | 1.81% |
| H1_252_4 | 3.14% | 33.25% | 41.97% | 2.79% |
| H1_126_3 | 5.97% | 21.74% | 37.16% | 1.81% |
| H1_126_4 | 7.65% | 25.20% | 44.28% | 3.11% |
| H2_4of6 | 2.77% | 13.00% | 30.68% | 1.80% |
| H2_5of6 | 1.25% | 5.51% | 20.81% | 0.00% |

### 2012 mean_weight

| run | DBC | EEM | EFA | GLD | HYG | IEF | LQD | SPY | TLT |
|---|---|---|---|---|---|---|---|---|---|
| B0 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| B1 | 10.28% | 10.34% | 10.33% | 10.25% | 10.25% | 10.23% | 10.23% | 10.29% | 10.19% |
| B2 | 7.44% | 5.08% | 5.59% | 7.02% | 15.28% | 18.94% | 23.26% | 8.12% | 7.26% |
| B3 | 1.03% | 0.90% | 1.71% | 3.84% | 12.90% | 15.89% | 19.94% | 6.82% | 6.07% |
| REF_SPY | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 94.05% | 0.00% |
| H1_252_3 | 0.00% | 0.00% | 0.00% | 1.81% | 8.02% | 18.70% | 22.67% | 2.77% | 11.46% |
| H1_252_4 | 0.00% | 0.00% | 0.00% | 2.79% | 17.32% | 24.61% | 24.64% | 3.14% | 8.64% |
| H1_126_3 | 0.00% | 0.00% | 1.05% | 1.81% | 14.45% | 14.24% | 22.71% | 4.92% | 7.50% |
| H1_126_4 | 0.00% | 1.61% | 0.90% | 3.11% | 19.60% | 18.65% | 24.68% | 5.14% | 6.55% |
| H2_4of6 | 0.00% | 0.00% | 0.00% | 1.80% | 8.00% | 10.32% | 22.68% | 2.77% | 2.68% |
| H2_5of6 | 0.00% | 0.00% | 0.00% | 0.00% | 6.12% | 3.90% | 14.69% | 1.25% | 1.60% |

### 2013

| run | total_return | cagr | volatility | mean_excess | sharpe_bil | utility | max_drawdown | decisions | turnover_annual | costs_usd | cost_ratio | mean_cash_plus_bil | mean_receivables | mean_risky | mean_target_risky | mean_bil | mean_cash_usd | n_returns | turnover |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B0 | -0.09% | -0.09% | 0.25% | 0.00% | 0.345 | 0.000 | -0.11% | 12 | 0.00x | 0.00 | 0.00% | 100.00% | 0.00% | 0.00% | 0.00% | 98.99% | 1.01% | 252 | 0.00x |
| B1 | -1.12% | -1.12% | 7.45% | -0.76% | -0.102 | -0.016 | -8.51% | 12 | 0.25x | 34.67 | 0.02% | 1.36% | 0.06% | 98.57% | 100.00% | 0.00% | 1.36% | 252 | 0.25x |
| B2 | -0.85% | -0.85% | 6.12% | -0.58% | -0.094 | -0.011 | -7.57% | 12 | 1.03x | 146.83 | 0.10% | 1.43% | 0.06% | 98.50% | 100.00% | 0.00% | 1.43% | 252 | 1.03x |
| B3 | 2.34% | 2.34% | 3.88% | 2.48% | 0.640 | 0.023 | -5.33% | 12 | 3.04x | 370.08 | 0.30% | 38.90% | 0.05% | 61.05% | 62.04% | 37.64% | 1.26% | 252 | 3.04x |
| REF_SPY | 29.79% | 29.79% | 10.32% | 26.71% | 2.592 | 0.251 | -5.19% | 0 | 0.00x | 0.00 | 0.00% | 6.58% | 0.22% | 93.20% | n/a | 0.00% | 6.58% | 252 | 0.00x |
| H1_252_3 | 9.17% | 9.17% | 5.01% | 8.99% | 1.796 | 0.086 | -4.43% | 12 | 2.81x | 346.24 | 0.28% | 30.87% | 0.08% | 69.06% | 69.74% | 29.67% | 1.19% | 252 | 2.81x |
| H1_252_4 | 7.58% | 7.58% | 5.60% | 7.55% | 1.350 | 0.071 | -5.63% | 12 | 2.89x | 338.54 | 0.29% | 24.22% | 0.08% | 75.70% | 76.62% | 23.00% | 1.22% | 252 | 2.89x |
| H1_126_3 | 8.12% | 8.12% | 5.91% | 8.07% | 1.368 | 0.076 | -4.79% | 12 | 5.07x | 600.35 | 0.51% | 38.94% | 0.06% | 61.00% | 61.91% | 37.84% | 1.09% | 252 | 5.07x |
| H1_126_4 | 7.26% | 7.26% | 5.59% | 7.25% | 1.300 | 0.068 | -5.35% | 12 | 5.64x | 728.70 | 0.56% | 36.13% | 0.07% | 63.80% | 64.85% | 34.99% | 1.13% | 252 | 5.64x |
| H2_4of6 | 5.48% | 5.48% | 3.29% | 5.48% | 1.668 | 0.053 | -2.68% | 12 | 3.93x | 471.37 | 0.39% | 61.34% | 0.06% | 38.59% | 38.94% | 60.20% | 1.14% | 252 | 3.93x |
| H2_5of6 | 1.77% | 1.77% | 1.98% | 1.86% | 0.946 | 0.018 | -1.91% | 12 | 2.45x | 257.77 | 0.25% | 78.85% | 0.03% | 21.12% | 21.44% | 77.74% | 1.11% | 252 | 2.45x |

### 2013 max_group

| run | Equity | Treasury | Credit | Real |
|---|---|---|---|---|
| B0 | 0.00% | 0.00% | 0.00% | 0.00% |
| B1 | 35.06% | 23.00% | 22.56% | 23.21% |
| B2 | 28.07% | 28.04% | 44.91% | 19.00% |
| B3 | 28.94% | 24.45% | 40.51% | 14.63% |
| REF_SPY | 93.59% | 0.00% | 0.00% | 0.00% |
| H1_252_3 | 51.10% | 24.79% | 49.65% | 0.00% |
| H1_252_4 | 51.39% | 24.88% | 49.55% | 0.00% |
| H1_126_3 | 51.34% | 0.00% | 49.63% | 14.48% |
| H1_126_4 | 49.88% | 24.83% | 49.82% | 12.77% |
| H2_4of6 | 44.36% | 0.00% | 24.98% | 0.00% |
| H2_5of6 | 25.69% | 0.00% | 24.94% | 0.00% |

### 2013 max_weight

| run | DBC | EEM | EFA | GLD | HYG | IEF | LQD | SPY | TLT |
|---|---|---|---|---|---|---|---|---|---|
| B0 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| B1 | 11.48% | 12.10% | 11.73% | 11.73% | 11.26% | 11.33% | 11.36% | 11.66% | 11.68% |
| B2 | 13.23% | 7.04% | 9.32% | 7.77% | 21.98% | 19.65% | 24.01% | 13.33% | 9.13% |
| B3 | 9.43% | 6.88% | 9.60% | 7.75% | 21.55% | 17.75% | 23.86% | 13.72% | 6.87% |
| REF_SPY | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 93.59% | 0.00% |
| H1_252_3 | 0.00% | 0.00% | 26.03% | 0.00% | 24.89% | 24.79% | 24.92% | 25.27% | 0.00% |
| H1_252_4 | 0.00% | 12.70% | 19.14% | 0.00% | 24.91% | 24.88% | 24.94% | 25.32% | 0.00% |
| H1_126_3 | 14.48% | 22.46% | 26.24% | 0.00% | 25.10% | 0.00% | 24.64% | 25.48% | 0.00% |
| H1_126_4 | 12.77% | 17.44% | 22.44% | 0.00% | 24.94% | 24.83% | 25.01% | 25.46% | 0.00% |
| H2_4of6 | 0.00% | 0.00% | 20.17% | 0.00% | 24.98% | 0.00% | 0.00% | 25.77% | 0.00% |
| H2_5of6 | 0.00% | 0.00% | 15.05% | 0.00% | 24.94% | 0.00% | 0.00% | 25.69% | 0.00% |

### 2013 mean_group

| run | Equity | Treasury | Credit | Real |
|---|---|---|---|---|
| B0 | 0.00% | 0.00% | 0.00% | 0.00% |
| B1 | 33.23% | 21.71% | 21.87% | 21.75% |
| B2 | 22.37% | 24.77% | 36.58% | 14.78% |
| B3 | 20.90% | 9.20% | 28.37% | 2.57% |
| REF_SPY | 93.20% | 0.00% | 0.00% | 0.00% |
| H1_252_3 | 30.29% | 2.16% | 36.61% | 0.00% |
| H1_252_4 | 32.64% | 4.29% | 38.77% | 0.00% |
| H1_126_3 | 39.52% | 0.00% | 20.31% | 1.18% |
| H1_126_4 | 36.52% | 2.12% | 24.12% | 1.04% |
| H2_4of6 | 20.14% | 0.00% | 18.45% | 0.00% |
| H2_5of6 | 9.01% | 0.00% | 12.11% | 0.00% |

### 2013 mean_weight

| run | DBC | EEM | EFA | GLD | HYG | IEF | LQD | SPY | TLT |
|---|---|---|---|---|---|---|---|---|---|
| B0 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| B1 | 10.97% | 10.99% | 11.13% | 10.78% | 10.97% | 10.90% | 10.90% | 11.11% | 10.81% |
| B2 | 9.39% | 5.97% | 7.40% | 5.39% | 17.47% | 17.25% | 19.11% | 9.00% | 7.52% |
| B3 | 1.93% | 4.85% | 7.24% | 0.64% | 16.81% | 6.67% | 11.56% | 8.81% | 2.53% |
| REF_SPY | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 93.20% | 0.00% |
| H1_252_3 | 0.00% | 0.00% | 14.18% | 0.00% | 24.56% | 2.16% | 12.05% | 16.11% | 0.00% |
| H1_252_4 | 0.00% | 2.74% | 12.80% | 0.00% | 24.57% | 4.29% | 14.20% | 17.10% | 0.00% |
| H1_126_3 | 1.18% | 3.42% | 17.95% | 0.00% | 18.26% | 0.00% | 2.04% | 18.15% | 0.00% |
| H1_126_4 | 1.04% | 4.55% | 14.66% | 0.00% | 18.28% | 2.12% | 5.84% | 17.31% | 0.00% |
| H2_4of6 | 0.00% | 0.00% | 3.96% | 0.00% | 18.45% | 0.00% | 0.00% | 16.18% | 0.00% |
| H2_5of6 | 0.00% | 0.00% | 1.12% | 0.00% | 12.11% | 0.00% | 0.00% | 7.89% | 0.00% |

### 2014

| run | total_return | cagr | volatility | mean_excess | sharpe_bil | utility | max_drawdown | decisions | turnover_annual | costs_usd | cost_ratio | mean_cash_plus_bil | mean_receivables | mean_risky | mean_target_risky | mean_bil | mean_cash_usd | n_returns | turnover |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B0 | -0.06% | -0.06% | 0.24% | 0.00% | 0.263 | 0.000 | -0.11% | 12 | 0.00x | 0.00 | 0.00% | 100.00% | 0.00% | 0.00% | 0.00% | 98.99% | 1.01% | 252 | 0.00x |
| B1 | 1.44% | 1.44% | 5.04% | 1.62% | 0.321 | 0.012 | -6.27% | 12 | 0.21x | 30.83 | 0.02% | 1.33% | 0.06% | 98.61% | 100.00% | 0.00% | 1.33% | 252 | 0.21x |
| B2 | 2.63% | 2.63% | 3.91% | 2.73% | 0.699 | 0.025 | -4.26% | 12 | 0.85x | 126.62 | 0.09% | 1.82% | 0.06% | 98.12% | 99.61% | 0.38% | 1.44% | 252 | 0.85x |
| B3 | 1.71% | 1.71% | 2.80% | 1.80% | 0.644 | 0.017 | -1.95% | 12 | 2.39x | 300.61 | 0.24% | 35.03% | 0.05% | 64.92% | 65.57% | 33.71% | 1.32% | 252 | 2.39x |
| REF_SPY | 12.42% | 12.42% | 10.40% | 12.31% | 1.183 | 0.107 | -6.71% | 0 | 0.00x | 0.00 | 0.00% | 7.24% | 0.20% | 92.56% | n/a | 0.00% | 7.24% | 252 | 0.00x |
| H1_252_3 | 4.82% | 4.82% | 4.30% | 4.87% | 1.130 | 0.046 | -2.59% | 12 | 2.11x | 287.37 | 0.21% | 37.34% | 0.07% | 62.59% | 63.38% | 36.14% | 1.20% | 252 | 2.11x |
| H1_252_4 | 4.13% | 4.13% | 3.59% | 4.18% | 1.163 | 0.040 | -2.09% | 12 | 3.09x | 388.37 | 0.31% | 31.93% | 0.07% | 68.01% | 68.75% | 30.67% | 1.26% | 252 | 3.09x |
| H1_126_3 | 3.57% | 3.57% | 3.92% | 3.65% | 0.933 | 0.034 | -2.59% | 12 | 3.25x | 415.59 | 0.33% | 35.89% | 0.06% | 64.05% | 64.82% | 34.72% | 1.17% | 252 | 3.25x |
| H1_126_4 | 4.02% | 4.02% | 4.00% | 4.08% | 1.023 | 0.038 | -2.87% | 12 | 4.18x | 572.89 | 0.42% | 24.91% | 0.07% | 75.03% | 76.02% | 23.64% | 1.27% | 252 | 4.18x |
| H2_4of6 | 4.86% | 4.86% | 4.15% | 4.90% | 1.176 | 0.046 | -2.60% | 12 | 2.06x | 263.19 | 0.21% | 39.53% | 0.07% | 60.40% | 61.29% | 38.30% | 1.23% | 252 | 2.06x |
| H2_5of6 | 0.65% | 0.65% | 2.55% | 0.75% | 0.296 | 0.007 | -1.95% | 12 | 3.96x | 416.48 | 0.40% | 70.47% | 0.04% | 29.49% | 29.97% | 69.31% | 1.16% | 252 | 3.96x |
| P_A1 | 5.12% | 5.12% | 4.27% | 5.15% | 1.203 | 0.049 | -2.59% | 12 | 2.95x | 301.92 | 0.30% | 37.39% | 0.06% | 62.55% | 63.38% | 36.13% | 1.26% | 252 | 2.95x |
| H1_252_3_WF | 5.12% | 5.12% | 4.27% | 5.15% | 1.203 | 0.049 | -2.59% | 12 | 2.95x | 301.92 | 0.30% | 37.39% | 0.06% | 62.55% | 63.38% | 36.13% | 1.26% | 252 | 2.95x |

### 2014 max_group

| run | Equity | Treasury | Credit | Real |
|---|---|---|---|---|
| B0 | 0.00% | 0.00% | 0.00% | 0.00% |
| B1 | 33.54% | 23.17% | 22.29% | 22.75% |
| B2 | 23.39% | 30.31% | 43.54% | 15.93% |
| B3 | 21.45% | 26.84% | 40.80% | 13.38% |
| REF_SPY | 93.03% | 0.00% | 0.00% | 0.00% |
| H1_252_3 | 44.67% | 42.78% | 49.93% | 0.00% |
| H1_252_4 | 30.93% | 40.54% | 49.63% | 0.00% |
| H1_126_3 | 43.97% | 42.67% | 49.58% | 0.00% |
| H1_126_4 | 49.70% | 40.46% | 49.60% | 0.00% |
| H2_4of6 | 44.72% | 21.31% | 49.88% | 0.00% |
| H2_5of6 | 37.36% | 0.00% | 25.18% | 0.00% |
| P_A1 | 44.69% | 42.82% | 49.95% | 0.00% |
| H1_252_3_WF | 44.69% | 42.82% | 49.95% | 0.00% |

### 2014 max_weight

| run | DBC | EEM | EFA | GLD | HYG | IEF | LQD | SPY | TLT |
|---|---|---|---|---|---|---|---|---|---|
| B0 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| B1 | 11.33% | 11.44% | 11.30% | 11.70% | 11.13% | 11.41% | 11.28% | 11.29% | 11.76% |
| B2 | 10.72% | 6.58% | 8.55% | 8.16% | 24.89% | 20.87% | 22.59% | 8.82% | 9.45% |
| B3 | 8.35% | 6.04% | 8.25% | 5.08% | 24.70% | 18.51% | 20.87% | 8.03% | 8.33% |
| REF_SPY | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 93.03% | 0.00% |
| H1_252_3 | 0.00% | 0.00% | 22.37% | 0.00% | 25.24% | 24.78% | 25.38% | 22.48% | 21.33% |
| H1_252_4 | 0.00% | 0.00% | 15.46% | 0.00% | 25.19% | 24.88% | 25.15% | 16.06% | 15.66% |
| H1_126_3 | 0.00% | 19.28% | 18.40% | 0.00% | 25.18% | 24.97% | 24.95% | 25.05% | 17.98% |
| H1_126_4 | 0.00% | 16.01% | 18.22% | 0.00% | 25.43% | 25.17% | 24.94% | 21.40% | 17.16% |
| H2_4of6 | 0.00% | 0.00% | 22.35% | 0.00% | 25.21% | 0.00% | 25.31% | 22.53% | 21.31% |
| H2_5of6 | 0.00% | 0.00% | 18.38% | 0.00% | 25.18% | 0.00% | 0.00% | 22.61% | 0.00% |
| P_A1 | 0.00% | 0.00% | 22.33% | 0.00% | 25.13% | 24.82% | 25.36% | 22.52% | 21.29% |
| H1_252_3_WF | 0.00% | 0.00% | 22.33% | 0.00% | 25.13% | 24.82% | 25.36% | 22.52% | 21.29% |

### 2014 mean_group

| run | Equity | Treasury | Credit | Real |
|---|---|---|---|---|
| B0 | 0.00% | 0.00% | 0.00% | 0.00% |
| B1 | 32.80% | 22.02% | 21.89% | 21.89% |
| B2 | 19.50% | 23.94% | 40.12% | 14.56% |
| B3 | 15.73% | 13.40% | 34.01% | 1.77% |
| REF_SPY | 92.56% | 0.00% | 0.00% | 0.00% |
| H1_252_3 | 28.36% | 5.28% | 28.95% | 0.00% |
| H1_252_4 | 23.10% | 7.66% | 37.25% | 0.00% |
| H1_126_3 | 16.24% | 12.79% | 35.02% | 0.00% |
| H1_126_4 | 21.79% | 16.37% | 36.87% | 0.00% |
| H2_4of6 | 28.35% | 3.12% | 28.93% | 0.00% |
| H2_5of6 | 15.20% | 0.00% | 14.29% | 0.00% |
| P_A1 | 28.34% | 5.28% | 28.93% | 0.00% |
| H1_252_3_WF | 28.34% | 5.28% | 28.93% | 0.00% |

### 2014 mean_weight

| run | DBC | EEM | EFA | GLD | HYG | IEF | LQD | SPY | TLT |
|---|---|---|---|---|---|---|---|---|---|
| B0 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| B1 | 10.83% | 10.94% | 10.89% | 11.06% | 10.93% | 10.99% | 10.96% | 10.97% | 11.03% |
| B2 | 8.83% | 5.10% | 6.92% | 5.73% | 21.50% | 16.37% | 18.63% | 7.49% | 7.57% |
| B3 | 1.33% | 3.09% | 6.09% | 0.44% | 18.87% | 9.37% | 15.14% | 6.55% | 4.03% |
| REF_SPY | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 92.56% | 0.00% |
| H1_252_3 | 0.00% | 0.00% | 11.42% | 0.00% | 20.64% | 2.15% | 8.31% | 16.94% | 3.13% |
| H1_252_4 | 0.00% | 0.00% | 9.43% | 0.00% | 20.65% | 4.01% | 16.60% | 13.67% | 3.65% |
| H1_126_3 | 0.00% | 3.00% | 2.79% | 0.00% | 16.35% | 6.28% | 18.67% | 10.45% | 6.52% |
| H1_126_4 | 0.00% | 3.23% | 5.41% | 0.00% | 16.37% | 8.33% | 20.50% | 13.15% | 8.04% |
| H2_4of6 | 0.00% | 0.00% | 11.41% | 0.00% | 20.64% | 0.00% | 8.29% | 16.94% | 3.12% |
| H2_5of6 | 0.00% | 0.00% | 2.76% | 0.00% | 14.29% | 0.00% | 0.00% | 12.44% | 0.00% |
| P_A1 | 0.00% | 0.00% | 11.41% | 0.00% | 20.63% | 2.16% | 8.30% | 16.93% | 3.13% |
| H1_252_3_WF | 0.00% | 0.00% | 11.41% | 0.00% | 20.63% | 2.16% | 8.30% | 16.93% | 3.13% |

### 2015

| run | total_return | cagr | volatility | mean_excess | sharpe_bil | utility | max_drawdown | decisions | turnover_annual | costs_usd | cost_ratio | mean_cash_plus_bil | mean_receivables | mean_risky | mean_target_risky | mean_bil | mean_cash_usd | n_returns | turnover |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B0 | -0.13% | -0.13% | 0.26% | 0.00% | 0.497 | 0.000 | -0.15% | 12 | 0.00x | 0.00 | 0.00% | 100.00% | 0.00% | 0.00% | 0.00% | 98.99% | 1.01% | 252 | 0.00x |
| B1 | -6.49% | -6.49% | 7.22% | -6.32% | -0.876 | -0.071 | -10.79% | 12 | 0.33x | 46.84 | 0.03% | 1.44% | 0.06% | 98.51% | 100.00% | 0.00% | 1.44% | 252 | 0.33x |
| B2 | -4.75% | -4.75% | 5.61% | -4.58% | -0.817 | -0.051 | -8.86% | 12 | 0.93x | 136.82 | 0.09% | 1.41% | 0.06% | 98.53% | 100.00% | 0.00% | 1.41% | 252 | 0.93x |
| B3 | -0.73% | -0.73% | 3.44% | -0.55% | -0.159 | -0.007 | -3.21% | 12 | 4.52x | 574.71 | 0.45% | 45.69% | 0.04% | 54.27% | 55.56% | 44.40% | 1.29% | 252 | 4.52x |
| REF_SPY | 1.13% | 1.13% | 14.05% | 2.24% | 0.160 | -0.007 | -10.89% | 0 | 0.00x | 0.00 | 0.00% | 8.46% | 0.21% | 91.33% | n/a | 0.00% | 8.46% | 252 | 0.00x |
| H1_252_3 | 1.21% | 1.21% | 4.94% | 1.46% | 0.295 | 0.011 | -3.82% | 12 | 3.30x | 471.30 | 0.33% | 32.26% | 0.05% | 67.69% | 68.62% | 31.06% | 1.20% | 252 | 3.30x |
| H1_252_4 | -0.86% | -0.86% | 4.85% | -0.61% | -0.127 | -0.010 | -4.88% | 12 | 2.61x | 335.85 | 0.26% | 25.62% | 0.06% | 74.32% | 75.40% | 24.38% | 1.24% | 252 | 2.61x |
| H1_126_3 | -6.95% | -6.95% | 7.28% | -6.81% | -0.936 | -0.076 | -11.86% | 12 | 8.30x | 1063.75 | 0.83% | 39.85% | 0.04% | 60.11% | 61.24% | 38.74% | 1.11% | 252 | 8.30x |
| H1_126_4 | -7.51% | -7.51% | 6.81% | -7.44% | -1.093 | -0.081 | -12.23% | 12 | 5.80x | 786.51 | 0.58% | 35.01% | 0.05% | 64.94% | 66.17% | 33.88% | 1.13% | 252 | 5.80x |
| H2_4of6 | -1.87% | -1.87% | 4.05% | -1.68% | -0.416 | -0.019 | -5.87% | 12 | 4.36x | 574.69 | 0.44% | 76.13% | 0.01% | 23.87% | 24.85% | 75.12% | 1.01% | 252 | 4.36x |
| H2_5of6 | -1.89% | -1.89% | 2.00% | -1.76% | -0.882 | -0.018 | -3.46% | 12 | 3.60x | 381.08 | 0.36% | 91.38% | 0.00% | 8.61% | 9.18% | 90.39% | 0.99% | 252 | 3.60x |
| P_A1 | 1.21% | 1.21% | 4.94% | 1.45% | 0.294 | 0.011 | -3.82% | 12 | 3.31x | 357.07 | 0.33% | 32.27% | 0.05% | 67.68% | 68.62% | 31.05% | 1.21% | 252 | 3.31x |
| H1_252_3_WF | 1.21% | 1.21% | 4.94% | 1.45% | 0.294 | 0.011 | -3.82% | 12 | 3.31x | 357.07 | 0.33% | 32.27% | 0.05% | 67.68% | 68.62% | 31.05% | 1.21% | 252 | 3.31x |

### 2015 max_group

| run | Equity | Treasury | Credit | Real |
|---|---|---|---|---|
| B0 | 0.00% | 0.00% | 0.00% | 0.00% |
| B1 | 34.67% | 23.40% | 22.36% | 22.88% |
| B2 | 24.75% | 30.44% | 41.47% | 17.43% |
| B3 | 21.73% | 27.03% | 34.71% | 4.83% |
| REF_SPY | 92.20% | 0.00% | 0.00% | 0.00% |
| H1_252_3 | 25.53% | 49.46% | 24.72% | 0.00% |
| H1_252_4 | 22.11% | 43.33% | 24.85% | 0.00% |
| H1_126_3 | 49.55% | 48.08% | 25.08% | 25.56% |
| H1_126_4 | 49.46% | 42.37% | 24.91% | 23.91% |
| H2_4of6 | 24.63% | 45.49% | 24.80% | 0.00% |
| H2_5of6 | 0.00% | 21.31% | 24.81% | 0.00% |
| P_A1 | 25.56% | 49.42% | 24.73% | 0.00% |
| H1_252_3_WF | 25.56% | 49.42% | 24.73% | 0.00% |

### 2015 max_weight

| run | DBC | EEM | EFA | GLD | HYG | IEF | LQD | SPY | TLT |
|---|---|---|---|---|---|---|---|---|---|
| B0 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| B1 | 11.60% | 11.77% | 11.64% | 12.05% | 11.12% | 11.60% | 11.33% | 11.59% | 11.81% |
| B2 | 7.05% | 7.04% | 8.79% | 10.67% | 23.01% | 20.66% | 24.30% | 10.58% | 10.08% |
| B3 | 0.00% | 6.18% | 7.69% | 4.83% | 20.27% | 18.89% | 20.85% | 9.89% | 8.14% |
| REF_SPY | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 92.20% | 0.00% |
| H1_252_3 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 25.44% | 24.72% | 25.53% | 24.59% |
| H1_252_4 | 0.00% | 0.00% | 0.00% | 0.00% | 24.63% | 25.57% | 24.85% | 22.11% | 18.47% |
| H1_126_3 | 25.56% | 21.09% | 24.91% | 0.00% | 25.08% | 25.68% | 24.72% | 26.06% | 23.42% |
| H1_126_4 | 23.91% | 17.42% | 20.43% | 0.00% | 24.91% | 25.64% | 24.89% | 20.24% | 17.54% |
| H2_4of6 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 24.95% | 24.80% | 24.63% | 21.23% |
| H2_5of6 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 24.81% | 0.00% | 21.31% |
| P_A1 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 25.47% | 24.73% | 25.56% | 24.63% |
| H1_252_3_WF | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 25.47% | 24.73% | 25.56% | 24.63% |

### 2015 mean_group

| run | Equity | Treasury | Credit | Real |
|---|---|---|---|---|
| B0 | 0.00% | 0.00% | 0.00% | 0.00% |
| B1 | 33.03% | 21.85% | 21.86% | 21.77% |
| B2 | 21.01% | 25.07% | 38.40% | 14.05% |
| B3 | 10.21% | 21.51% | 22.20% | 0.35% |
| REF_SPY | 91.33% | 0.00% | 0.00% | 0.00% |
| H1_252_3 | 16.95% | 40.79% | 9.94% | 0.00% |
| H1_252_4 | 15.09% | 38.85% | 20.38% | 0.00% |
| H1_126_3 | 18.76% | 26.90% | 12.40% | 2.04% |
| H1_126_4 | 18.77% | 30.00% | 14.25% | 1.92% |
| H2_4of6 | 2.01% | 13.84% | 8.02% | 0.00% |
| H2_5of6 | 0.00% | 4.69% | 3.92% | 0.00% |
| P_A1 | 16.96% | 40.77% | 9.95% | 0.00% |
| H1_252_3_WF | 16.96% | 40.77% | 9.95% | 0.00% |

### 2015 mean_weight

| run | DBC | EEM | EFA | GLD | HYG | IEF | LQD | SPY | TLT |
|---|---|---|---|---|---|---|---|---|---|
| B0 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| B1 | 10.79% | 10.98% | 11.05% | 10.97% | 10.93% | 10.95% | 10.93% | 11.00% | 10.90% |
| B2 | 6.24% | 5.78% | 7.04% | 7.81% | 18.59% | 17.58% | 19.81% | 8.19% | 7.49% |
| B3 | 0.00% | 1.90% | 1.63% | 0.35% | 8.80% | 15.07% | 13.40% | 6.68% | 6.43% |
| REF_SPY | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 91.33% | 0.00% |
| H1_252_3 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 20.77% | 9.94% | 16.95% | 20.03% |
| H1_252_4 | 0.00% | 0.00% | 0.00% | 0.00% | 2.04% | 24.68% | 18.35% | 15.09% | 14.17% |
| H1_126_3 | 2.04% | 3.36% | 7.56% | 0.00% | 2.16% | 16.26% | 10.24% | 7.84% | 10.64% |
| H1_126_4 | 1.92% | 3.80% | 5.57% | 0.00% | 2.16% | 20.51% | 12.10% | 9.40% | 9.49% |
| H2_4of6 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 6.09% | 8.02% | 2.01% | 7.75% |
| H2_5of6 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 3.92% | 0.00% | 4.69% |
| P_A1 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 20.75% | 9.95% | 16.96% | 20.02% |
| H1_252_3_WF | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 20.75% | 9.95% | 16.96% | 20.02% |

### 2016

| run | total_return | cagr | volatility | mean_excess | sharpe_bil | utility | max_drawdown | decisions | turnover_annual | costs_usd | cost_ratio | mean_cash_plus_bil | mean_receivables | mean_risky | mean_target_risky | mean_bil | mean_cash_usd | n_returns | turnover |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B0 | 0.11% | 0.11% | 0.29% | -0.00% | -0.369 | -0.000 | -0.09% | 12 | 0.00x | 0.00 | 0.00% | 100.00% | 0.00% | 0.00% | 0.00% | 98.98% | 1.02% | 252 | 0.00x |
| B1 | 8.40% | 8.40% | 7.36% | 8.23% | 1.120 | 0.074 | -5.81% | 12 | 0.27x | 38.22 | 0.03% | 1.39% | 0.06% | 98.56% | 100.00% | 0.00% | 1.39% | 252 | 0.27x |
| B2 | 7.05% | 7.05% | 5.38% | 6.85% | 1.277 | 0.064 | -5.15% | 12 | 0.78x | 115.34 | 0.08% | 1.68% | 0.06% | 98.26% | 99.73% | 0.26% | 1.42% | 252 | 0.78x |
| B3 | -0.05% | -0.05% | 3.65% | -0.10% | -0.027 | -0.003 | -4.94% | 12 | 2.64x | 335.83 | 0.26% | 41.14% | 0.04% | 58.82% | 59.26% | 39.83% | 1.31% | 252 | 2.64x |
| REF_SPY | 10.71% | 10.71% | 11.71% | 10.75% | 0.917 | 0.087 | -9.30% | 0 | 0.00x | 0.00 | 0.00% | 10.03% | 0.22% | 89.74% | n/a | 0.00% | 10.03% | 252 | 0.00x |
| H1_252_3 | -1.62% | -1.62% | 4.97% | -1.62% | -0.327 | -0.020 | -5.98% | 12 | 6.05x | 851.46 | 0.61% | 40.22% | 0.04% | 59.74% | 60.73% | 39.00% | 1.22% | 252 | 6.05x |
| H1_252_4 | -0.69% | -0.69% | 4.89% | -0.68% | -0.139 | -0.010 | -5.97% | 12 | 6.43x | 830.17 | 0.64% | 32.51% | 0.04% | 67.45% | 68.55% | 31.21% | 1.31% | 252 | 6.43x |
| H1_126_3 | 7.31% | 7.31% | 4.56% | 7.05% | 1.544 | 0.067 | -3.36% | 12 | 3.32x | 428.39 | 0.33% | 35.60% | 0.04% | 64.35% | 65.21% | 34.37% | 1.24% | 252 | 3.32x |
| H1_126_4 | 3.97% | 3.97% | 5.33% | 3.92% | 0.737 | 0.035 | -5.56% | 12 | 4.50x | 617.23 | 0.45% | 26.61% | 0.04% | 73.35% | 74.36% | 25.36% | 1.25% | 252 | 4.50x |
| H2_4of6 | -0.09% | -0.09% | 1.95% | -0.18% | -0.094 | -0.002 | -1.97% | 12 | 3.69x | 472.90 | 0.37% | 77.24% | 0.02% | 22.74% | 22.78% | 76.19% | 1.05% | 252 | 3.69x |
| H2_5of6 | -0.13% | -0.13% | 1.37% | -0.23% | -0.170 | -0.003 | -1.10% | 12 | 2.86x | 297.17 | 0.29% | 86.26% | 0.02% | 13.72% | 13.82% | 85.22% | 1.05% | 252 | 2.86x |
| P_A1 | -1.62% | -1.62% | 4.97% | -1.62% | -0.327 | -0.020 | -5.98% | 12 | 6.05x | 643.66 | 0.60% | 40.27% | 0.04% | 59.69% | 60.73% | 39.00% | 1.27% | 252 | 6.05x |
| H1_252_3_WF | -1.62% | -1.62% | 4.97% | -1.62% | -0.327 | -0.020 | -5.98% | 12 | 6.05x | 643.66 | 0.60% | 40.27% | 0.04% | 59.69% | 60.73% | 39.00% | 1.27% | 252 | 6.05x |

### 2016 max_group

| run | Equity | Treasury | Credit | Real |
|---|---|---|---|---|
| B0 | 0.00% | 0.00% | 0.00% | 0.00% |
| B1 | 34.53% | 23.69% | 22.36% | 23.03% |
| B2 | 23.80% | 32.29% | 38.75% | 15.19% |
| B3 | 21.22% | 27.07% | 35.25% | 13.42% |
| REF_SPY | 90.24% | 0.00% | 0.00% | 0.00% |
| H1_252_3 | 41.83% | 49.48% | 49.84% | 19.01% |
| H1_252_4 | 26.30% | 43.31% | 49.68% | 15.49% |
| H1_126_3 | 20.43% | 49.44% | 49.53% | 17.16% |
| H1_126_4 | 29.05% | 45.79% | 49.83% | 24.74% |
| H2_4of6 | 22.15% | 16.60% | 49.44% | 0.00% |
| H2_5of6 | 22.15% | 0.00% | 25.01% | 0.00% |
| P_A1 | 41.79% | 49.45% | 49.86% | 19.01% |
| H1_252_3_WF | 41.79% | 49.45% | 49.86% | 19.01% |

### 2016 max_weight

| run | DBC | EEM | EFA | GLD | HYG | IEF | LQD | SPY | TLT |
|---|---|---|---|---|---|---|---|---|---|
| B0 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| B1 | 11.79% | 11.95% | 11.40% | 12.32% | 11.25% | 11.74% | 11.35% | 11.75% | 11.95% |
| B2 | 6.90% | 5.69% | 8.98% | 8.99% | 15.69% | 22.59% | 24.90% | 9.94% | 9.91% |
| B3 | 6.22% | 5.43% | 6.95% | 7.61% | 14.14% | 19.68% | 22.19% | 9.28% | 7.94% |
| REF_SPY | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 90.24% | 0.00% |
| H1_252_3 | 0.00% | 0.00% | 21.40% | 19.01% | 25.11% | 26.11% | 24.85% | 24.96% | 24.80% |
| H1_252_4 | 0.00% | 0.00% | 13.42% | 15.49% | 24.94% | 25.76% | 25.10% | 24.97% | 18.64% |
| H1_126_3 | 14.24% | 12.97% | 0.00% | 17.16% | 24.99% | 25.04% | 25.31% | 20.43% | 24.79% |
| H1_126_4 | 12.47% | 10.79% | 0.00% | 17.02% | 25.29% | 25.26% | 25.30% | 18.30% | 21.10% |
| H2_4of6 | 0.00% | 0.00% | 0.00% | 0.00% | 24.92% | 0.00% | 25.24% | 22.15% | 16.60% |
| H2_5of6 | 0.00% | 0.00% | 0.00% | 0.00% | 24.90% | 0.00% | 25.01% | 22.15% | 0.00% |
| P_A1 | 0.00% | 0.00% | 21.39% | 19.01% | 25.12% | 26.12% | 24.80% | 24.84% | 24.77% |
| H1_252_3_WF | 0.00% | 0.00% | 21.39% | 19.01% | 25.12% | 26.12% | 24.80% | 24.84% | 24.77% |

### 2016 mean_group

| run | Equity | Treasury | Credit | Real |
|---|---|---|---|---|
| B0 | 0.00% | 0.00% | 0.00% | 0.00% |
| B1 | 32.86% | 21.81% | 21.85% | 22.04% |
| B2 | 19.82% | 29.60% | 35.65% | 13.19% |
| B3 | 9.24% | 22.87% | 21.25% | 5.46% |
| REF_SPY | 89.74% | 0.00% | 0.00% | 0.00% |
| H1_252_3 | 8.35% | 27.71% | 20.75% | 2.93% |
| H1_252_4 | 7.74% | 29.39% | 24.38% | 5.94% |
| H1_126_3 | 3.74% | 21.74% | 33.03% | 5.84% |
| H1_126_4 | 6.23% | 25.76% | 33.13% | 8.24% |
| H2_4of6 | 3.34% | 2.72% | 16.67% | 0.00% |
| H2_5of6 | 3.34% | 0.00% | 10.38% | 0.00% |
| P_A1 | 8.31% | 27.71% | 20.75% | 2.93% |
| H1_252_3_WF | 8.31% | 27.71% | 20.75% | 2.93% |

### 2016 mean_weight

| run | DBC | EEM | EFA | GLD | HYG | IEF | LQD | SPY | TLT |
|---|---|---|---|---|---|---|---|---|---|
| B0 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| B1 | 11.04% | 10.96% | 10.93% | 11.00% | 10.95% | 10.93% | 10.90% | 10.96% | 10.88% |
| B2 | 6.19% | 5.06% | 6.38% | 7.00% | 13.19% | 20.85% | 22.46% | 8.39% | 8.75% |
| B3 | 0.51% | 2.01% | 0.96% | 4.95% | 6.49% | 17.21% | 14.76% | 6.28% | 5.66% |
| REF_SPY | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 89.74% | 0.00% |
| H1_252_3 | 0.00% | 0.00% | 1.56% | 2.93% | 4.14% | 18.64% | 16.61% | 6.79% | 9.08% |
| H1_252_4 | 0.00% | 0.00% | 0.97% | 5.94% | 5.89% | 20.66% | 18.49% | 6.77% | 8.73% |
| H1_126_3 | 2.44% | 2.06% | 0.00% | 3.40% | 10.51% | 14.20% | 22.53% | 1.69% | 7.54% |
| H1_126_4 | 2.09% | 2.59% | 0.00% | 6.15% | 10.55% | 14.21% | 22.58% | 3.64% | 11.55% |
| H2_4of6 | 0.00% | 0.00% | 0.00% | 0.00% | 4.13% | 0.00% | 12.54% | 3.34% | 2.72% |
| H2_5of6 | 0.00% | 0.00% | 0.00% | 0.00% | 4.12% | 0.00% | 6.26% | 3.34% | 0.00% |
| P_A1 | 0.00% | 0.00% | 1.56% | 2.93% | 4.14% | 18.63% | 16.61% | 6.75% | 9.08% |
| H1_252_3_WF | 0.00% | 0.00% | 1.56% | 2.93% | 4.14% | 18.63% | 16.61% | 6.75% | 9.08% |

### 2017

| run | total_return | cagr | volatility | mean_excess | sharpe_bil | utility | max_drawdown | decisions | turnover_annual | costs_usd | cost_ratio | mean_cash_plus_bil | mean_receivables | mean_risky | mean_target_risky | mean_bil | mean_cash_usd | n_returns | turnover |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B0 | 0.68% | 0.68% | 0.30% | -0.01% | -2.426 | -0.000 | -0.04% | 12 | 0.01x | 0.50 | 0.00% | 99.98% | 0.02% | 0.00% | 0.00% | 98.92% | 1.06% | 251 | 0.01x |
| B1 | 13.53% | 13.58% | 4.34% | 12.14% | 2.793 | 0.119 | -2.27% | 12 | 0.16x | 23.80 | 0.02% | 1.37% | 0.06% | 98.58% | 100.00% | 0.00% | 1.37% | 251 | 0.15x |
| B2 | 10.65% | 10.70% | 3.63% | 9.54% | 2.614 | 0.093 | -2.05% | 12 | 0.87x | 136.63 | 0.09% | 1.41% | 0.06% | 98.53% | 100.00% | 0.00% | 1.41% | 251 | 0.87x |
| B3 | 8.71% | 8.74% | 3.10% | 7.74% | 2.493 | 0.076 | -1.60% | 12 | 3.27x | 427.58 | 0.33% | 26.28% | 0.06% | 73.66% | 75.00% | 24.98% | 1.30% | 251 | 3.26x |
| REF_SPY | 19.24% | 19.32% | 6.04% | 17.16% | 2.847 | 0.166 | -2.34% | 0 | 0.00x | 0.00 | 0.00% | 10.24% | 0.21% | 89.55% | n/a | 0.00% | 10.24% | 251 | 0.00x |
| H1_252_3 | 8.58% | 8.62% | 3.77% | 7.65% | 2.032 | 0.074 | -1.27% | 12 | 5.02x | 717.25 | 0.50% | 33.33% | 0.07% | 66.60% | 67.23% | 32.19% | 1.14% | 251 | 5.00x |
| H1_252_4 | 11.08% | 11.12% | 4.23% | 9.95% | 2.355 | 0.097 | -1.44% | 12 | 2.82x | 363.53 | 0.28% | 22.93% | 0.08% | 76.99% | 78.12% | 21.78% | 1.15% | 251 | 2.80x |
| H1_126_3 | 12.20% | 12.25% | 4.05% | 10.95% | 2.707 | 0.107 | -1.66% | 12 | 6.47x | 884.50 | 0.64% | 35.14% | 0.06% | 64.80% | 65.61% | 34.03% | 1.11% | 251 | 6.44x |
| H1_126_4 | 11.32% | 11.37% | 4.15% | 10.16% | 2.439 | 0.099 | -1.62% | 12 | 4.77x | 679.51 | 0.48% | 23.15% | 0.06% | 76.79% | 77.84% | 21.97% | 1.18% | 251 | 4.75x |
| H2_4of6 | 8.80% | 8.83% | 3.52% | 7.84% | 2.234 | 0.077 | -1.27% | 12 | 4.47x | 593.14 | 0.45% | 38.26% | 0.07% | 61.67% | 62.18% | 37.08% | 1.18% | 251 | 4.46x |
| H2_5of6 | 6.19% | 6.21% | 2.97% | 5.38% | 1.836 | 0.053 | -1.27% | 12 | 4.13x | 440.44 | 0.41% | 50.48% | 0.06% | 49.47% | 49.48% | 49.30% | 1.18% | 251 | 4.11x |
| P_A1 | 8.57% | 8.61% | 3.77% | 7.64% | 2.032 | 0.074 | -1.27% | 12 | 5.02x | 542.59 | 0.50% | 33.36% | 0.07% | 66.57% | 67.23% | 32.20% | 1.16% | 251 | 5.00x |
| H1_252_3_WF | 8.57% | 8.61% | 3.77% | 7.64% | 2.032 | 0.074 | -1.27% | 12 | 5.02x | 542.59 | 0.50% | 33.36% | 0.07% | 66.57% | 67.23% | 32.20% | 1.16% | 251 | 5.00x |

### 2017 max_group

| run | Equity | Treasury | Credit | Real |
|---|---|---|---|---|
| B0 | 0.00% | 0.00% | 0.00% | 0.00% |
| B1 | 33.89% | 22.35% | 22.01% | 22.41% |
| B2 | 29.12% | 27.43% | 38.65% | 15.47% |
| B3 | 29.79% | 25.58% | 38.00% | 15.19% |
| REF_SPY | 89.99% | 0.00% | 0.00% | 0.00% |
| H1_252_3 | 49.86% | 0.00% | 49.62% | 20.62% |
| H1_252_4 | 50.33% | 0.00% | 49.81% | 15.91% |
| H1_126_3 | 50.23% | 0.00% | 24.80% | 25.04% |
| H1_126_4 | 50.45% | 24.76% | 49.23% | 18.37% |
| H2_4of6 | 49.84% | 0.00% | 24.84% | 19.68% |
| H2_5of6 | 49.87% | 0.00% | 24.94% | 0.00% |
| P_A1 | 49.77% | 0.00% | 49.64% | 20.62% |
| H1_252_3_WF | 49.77% | 0.00% | 49.64% | 20.62% |

### 2017 max_weight

| run | DBC | EEM | EFA | GLD | HYG | IEF | LQD | SPY | TLT |
|---|---|---|---|---|---|---|---|---|---|
| B0 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| B1 | 11.37% | 11.58% | 11.37% | 11.36% | 11.02% | 11.08% | 11.07% | 11.21% | 11.32% |
| B2 | 7.66% | 6.53% | 10.90% | 7.89% | 21.84% | 19.28% | 18.49% | 12.57% | 8.95% |
| B3 | 7.52% | 6.53% | 11.06% | 8.05% | 21.42% | 18.12% | 19.69% | 12.84% | 7.48% |
| REF_SPY | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 89.99% | 0.00% |
| H1_252_3 | 20.62% | 19.26% | 24.43% | 0.00% | 24.84% | 0.00% | 24.84% | 25.46% | 0.00% |
| H1_252_4 | 15.91% | 13.13% | 23.30% | 0.00% | 24.96% | 0.00% | 24.88% | 24.77% | 0.00% |
| H1_126_3 | 25.04% | 22.52% | 25.39% | 0.00% | 24.76% | 0.00% | 24.80% | 25.42% | 0.00% |
| H1_126_4 | 18.37% | 13.12% | 24.12% | 0.00% | 24.80% | 24.76% | 24.80% | 25.26% | 0.00% |
| H2_4of6 | 19.68% | 19.24% | 24.43% | 0.00% | 24.84% | 0.00% | 0.00% | 25.33% | 0.00% |
| H2_5of6 | 0.00% | 17.87% | 24.42% | 0.00% | 24.94% | 0.00% | 0.00% | 24.97% | 0.00% |
| P_A1 | 20.62% | 19.24% | 24.42% | 0.00% | 24.86% | 0.00% | 24.85% | 25.40% | 0.00% |
| H1_252_3_WF | 20.62% | 19.24% | 24.42% | 0.00% | 24.86% | 0.00% | 24.85% | 25.40% | 0.00% |

### 2017 mean_group

| run | Equity | Treasury | Credit | Real |
|---|---|---|---|---|
| B0 | 0.00% | 0.00% | 0.00% | 0.00% |
| B1 | 33.11% | 21.86% | 21.79% | 21.83% |
| B2 | 25.88% | 24.32% | 35.32% | 13.00% |
| B3 | 25.69% | 3.88% | 34.96% | 9.12% |
| REF_SPY | 89.55% | 0.00% | 0.00% | 0.00% |
| H1_252_3 | 41.00% | 0.00% | 22.60% | 3.00% |
| H1_252_4 | 45.45% | 0.00% | 28.36% | 3.19% |
| H1_126_3 | 45.14% | 0.00% | 16.23% | 3.43% |
| H1_126_4 | 45.32% | 1.95% | 24.74% | 4.78% |
| H2_4of6 | 39.56% | 0.00% | 20.64% | 1.47% |
| H2_5of6 | 30.67% | 0.00% | 18.80% | 0.00% |
| P_A1 | 40.97% | 0.00% | 22.60% | 3.00% |
| H1_252_3_WF | 40.97% | 0.00% | 22.60% | 3.00% |

### 2017 mean_weight

| run | DBC | EEM | EFA | GLD | HYG | IEF | LQD | SPY | TLT |
|---|---|---|---|---|---|---|---|---|---|
| B0 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| B1 | 10.90% | 11.13% | 11.03% | 10.93% | 10.88% | 10.90% | 10.91% | 10.95% | 10.95% |
| B2 | 5.88% | 5.82% | 9.44% | 7.13% | 17.81% | 16.83% | 17.51% | 10.63% | 7.49% |
| B3 | 4.97% | 5.76% | 9.37% | 4.15% | 17.61% | 2.76% | 17.36% | 10.56% | 1.12% |
| REF_SPY | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 89.55% | 0.00% |
| H1_252_3 | 3.00% | 7.03% | 10.51% | 0.00% | 20.64% | 0.00% | 1.97% | 23.45% | 0.00% |
| H1_252_4 | 3.19% | 8.85% | 15.51% | 0.00% | 24.53% | 0.00% | 3.83% | 21.08% | 0.00% |
| H1_126_3 | 3.43% | 10.21% | 18.33% | 0.00% | 9.87% | 0.00% | 6.37% | 16.60% | 0.00% |
| H1_126_4 | 4.78% | 8.70% | 18.91% | 0.00% | 16.32% | 1.95% | 8.42% | 17.71% | 0.00% |
| H2_4of6 | 1.47% | 5.60% | 10.51% | 0.00% | 20.64% | 0.00% | 0.00% | 23.45% | 0.00% |
| H2_5of6 | 0.00% | 2.85% | 10.51% | 0.00% | 18.80% | 0.00% | 0.00% | 17.31% | 0.00% |
| P_A1 | 3.00% | 7.03% | 10.51% | 0.00% | 20.64% | 0.00% | 1.97% | 23.44% | 0.00% |
| H1_252_3_WF | 3.00% | 7.03% | 10.51% | 0.00% | 20.64% | 0.00% | 1.97% | 23.44% | 0.00% |

### 2018

| run | total_return | cagr | volatility | mean_excess | sharpe_bil | utility | max_drawdown | decisions | turnover_annual | costs_usd | cost_ratio | mean_cash_plus_bil | mean_receivables | mean_risky | mean_target_risky | mean_bil | mean_cash_usd | n_returns | turnover |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B0 | 1.72% | 1.72% | 0.18% | -0.02% | -9.841 | -0.000 | -0.02% | 12 | 0.01x | 1.46 | 0.00% | 99.97% | 0.03% | 0.00% | 0.00% | 98.83% | 1.15% | 251 | 0.01x |
| B1 | -5.66% | -5.68% | 6.78% | -7.35% | -1.082 | -0.080 | -10.06% | 12 | 0.21x | 34.64 | 0.02% | 1.41% | 0.06% | 98.53% | 100.00% | 0.00% | 1.41% | 251 | 0.21x |
| B2 | -2.62% | -2.63% | 4.51% | -4.30% | -0.954 | -0.046 | -5.80% | 12 | 1.16x | 188.37 | 0.12% | 2.12% | 0.06% | 97.82% | 99.33% | 0.69% | 1.43% | 251 | 1.15x |
| B3 | -3.72% | -3.73% | 4.41% | -5.44% | -1.230 | -0.057 | -6.19% | 12 | 3.08x | 413.29 | 0.31% | 41.78% | 0.05% | 58.17% | 59.13% | 40.40% | 1.37% | 251 | 3.07x |
| REF_SPY | -3.97% | -3.98% | 15.12% | -4.65% | -0.308 | -0.081 | -17.25% | 0 | 0.00x | 0.00 | 0.00% | 10.69% | 0.19% | 89.13% | n/a | 0.00% | 10.69% | 251 | 0.00x |
| H1_252_3 | -7.41% | -7.44% | 7.84% | -9.15% | -1.165 | -0.101 | -12.49% | 12 | 3.52x | 519.21 | 0.35% | 41.52% | 0.06% | 58.42% | 58.99% | 40.40% | 1.12% | 251 | 3.50x |
| H1_252_4 | -5.93% | -5.95% | 7.82% | -7.56% | -0.965 | -0.085 | -11.01% | 12 | 3.17x | 445.81 | 0.32% | 33.20% | 0.07% | 66.73% | 67.64% | 32.04% | 1.16% | 251 | 3.15x |
| H1_126_3 | -2.92% | -2.93% | 7.19% | -4.45% | -0.619 | -0.052 | -8.88% | 12 | 6.20x | 895.60 | 0.62% | 41.24% | 0.07% | 58.69% | 59.27% | 40.05% | 1.19% | 251 | 6.17x |
| H1_126_4 | -2.62% | -2.63% | 7.37% | -4.12% | -0.559 | -0.049 | -8.15% | 12 | 5.95x | 890.95 | 0.59% | 37.29% | 0.06% | 62.65% | 63.20% | 36.07% | 1.22% | 251 | 5.93x |
| H2_4of6 | -2.30% | -2.31% | 5.91% | -3.89% | -0.658 | -0.044 | -7.50% | 12 | 4.37x | 608.86 | 0.44% | 62.44% | 0.05% | 37.51% | 38.00% | 61.28% | 1.16% | 251 | 4.35x |
| H2_5of6 | -2.26% | -2.27% | 4.08% | -3.94% | -0.966 | -0.042 | -6.17% | 12 | 2.34x | 258.04 | 0.23% | 81.11% | 0.05% | 18.84% | 19.60% | 79.94% | 1.17% | 251 | 2.33x |
| P_A1 | -3.12% | -3.13% | 7.17% | -4.65% | -0.649 | -0.054 | -8.88% | 12 | 6.34x | 712.00 | 0.63% | 41.29% | 0.07% | 58.64% | 59.27% | 40.04% | 1.25% | 251 | 6.31x |
| H1_252_3_WF | -7.39% | -7.42% | 7.83% | -9.13% | -1.164 | -0.101 | -12.47% | 12 | 3.51x | 392.66 | 0.35% | 41.56% | 0.06% | 58.38% | 58.99% | 40.40% | 1.15% | 251 | 3.50x |

### 2018 max_group

| run | Equity | Treasury | Credit | Real |
|---|---|---|---|---|
| B0 | 0.00% | 0.00% | 0.00% | 0.00% |
| B1 | 34.54% | 23.35% | 22.46% | 22.85% |
| B2 | 27.16% | 32.50% | 42.90% | 17.15% |
| B3 | 27.12% | 24.47% | 41.95% | 23.11% |
| REF_SPY | 90.10% | 0.00% | 0.00% | 0.00% |
| H1_252_3 | 51.26% | 0.00% | 24.92% | 25.66% |
| H1_252_4 | 51.28% | 0.00% | 25.40% | 25.61% |
| H1_126_3 | 50.67% | 25.14% | 24.89% | 49.97% |
| H1_126_4 | 51.00% | 25.11% | 49.57% | 49.69% |
| H2_4of6 | 51.33% | 0.00% | 24.76% | 25.62% |
| H2_5of6 | 37.04% | 0.00% | 0.00% | 25.60% |
| P_A1 | 50.68% | 25.11% | 24.87% | 49.95% |
| H1_252_3_WF | 51.32% | 0.00% | 24.93% | 25.64% |

### 2018 max_weight

| run | DBC | EEM | EFA | GLD | HYG | IEF | LQD | SPY | TLT |
|---|---|---|---|---|---|---|---|---|---|
| B0 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| B1 | 11.47% | 11.78% | 11.43% | 11.79% | 11.22% | 11.48% | 11.33% | 11.34% | 11.87% |
| B2 | 8.57% | 5.36% | 10.45% | 9.33% | 24.88% | 22.31% | 22.41% | 11.35% | 10.19% |
| B3 | 11.18% | 5.60% | 10.47% | 12.29% | 25.05% | 18.14% | 23.14% | 11.31% | 10.69% |
| REF_SPY | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 90.10% | 0.00% |
| H1_252_3 | 25.66% | 23.85% | 25.23% | 0.00% | 24.92% | 0.00% | 0.00% | 25.33% | 0.00% |
| H1_252_4 | 25.61% | 14.25% | 24.75% | 0.00% | 24.98% | 0.00% | 25.40% | 25.48% | 0.00% |
| H1_126_3 | 25.78% | 22.36% | 25.32% | 24.72% | 24.89% | 0.00% | 0.00% | 25.75% | 25.14% |
| H1_126_4 | 25.60% | 15.39% | 25.14% | 24.76% | 25.03% | 0.00% | 24.94% | 25.69% | 25.11% |
| H2_4of6 | 25.62% | 16.42% | 24.90% | 0.00% | 24.76% | 0.00% | 0.00% | 25.40% | 0.00% |
| H2_5of6 | 25.60% | 0.00% | 18.59% | 0.00% | 0.00% | 0.00% | 0.00% | 25.01% | 0.00% |
| P_A1 | 25.78% | 22.36% | 25.33% | 24.69% | 24.87% | 0.00% | 0.00% | 25.59% | 25.11% |
| H1_252_3_WF | 25.64% | 23.86% | 25.18% | 0.00% | 24.93% | 0.00% | 0.00% | 25.24% | 0.00% |

### 2018 mean_group

| run | Equity | Treasury | Credit | Real |
|---|---|---|---|---|
| B0 | 0.00% | 0.00% | 0.00% | 0.00% |
| B1 | 32.76% | 21.91% | 21.91% | 21.96% |
| B2 | 17.12% | 27.49% | 39.32% | 13.90% |
| B3 | 17.75% | 3.45% | 25.43% | 11.55% |
| REF_SPY | 89.13% | 0.00% | 0.00% | 0.00% |
| H1_252_3 | 39.01% | 0.00% | 6.19% | 13.22% |
| H1_252_4 | 40.31% | 0.00% | 12.17% | 14.25% |
| H1_126_3 | 28.25% | 3.62% | 6.20% | 20.62% |
| H1_126_4 | 29.33% | 3.51% | 8.27% | 21.54% |
| H2_4of6 | 27.50% | 0.00% | 2.25% | 7.76% |
| H2_5of6 | 14.61% | 0.00% | 0.00% | 4.23% |
| P_A1 | 28.22% | 3.61% | 6.19% | 20.62% |
| H1_252_3_WF | 38.97% | 0.00% | 6.20% | 13.22% |

### 2018 mean_weight

| run | DBC | EEM | EFA | GLD | HYG | IEF | LQD | SPY | TLT |
|---|---|---|---|---|---|---|---|---|---|
| B0 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| B1 | 10.95% | 10.90% | 10.93% | 11.01% | 10.97% | 10.98% | 10.94% | 10.93% | 10.93% |
| B2 | 5.95% | 3.97% | 6.53% | 7.94% | 20.58% | 19.43% | 18.74% | 6.62% | 8.05% |
| B3 | 6.76% | 3.35% | 6.36% | 4.80% | 18.99% | 1.49% | 6.44% | 8.03% | 1.95% |
| REF_SPY | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 89.13% | 0.00% |
| H1_252_3 | 13.22% | 10.81% | 12.03% | 0.00% | 6.19% | 0.00% | 0.00% | 16.17% | 0.00% |
| H1_252_4 | 14.25% | 7.19% | 15.03% | 0.00% | 8.23% | 0.00% | 3.94% | 18.10% | 0.00% |
| H1_126_3 | 18.48% | 3.47% | 8.06% | 2.14% | 6.20% | 0.00% | 0.00% | 16.71% | 3.62% |
| H1_126_4 | 17.35% | 5.49% | 9.24% | 4.19% | 6.20% | 0.00% | 2.07% | 14.61% | 3.51% |
| H2_4of6 | 7.76% | 3.64% | 7.72% | 0.00% | 2.25% | 0.00% | 0.00% | 16.13% | 0.00% |
| H2_5of6 | 4.23% | 0.00% | 4.17% | 0.00% | 0.00% | 0.00% | 0.00% | 10.44% | 0.00% |
| P_A1 | 18.48% | 3.47% | 8.06% | 2.14% | 6.19% | 0.00% | 0.00% | 16.69% | 3.61% |
| H1_252_3_WF | 13.22% | 10.80% | 12.02% | 0.00% | 6.20% | 0.00% | 0.00% | 16.15% | 0.00% |

### 2019

| run | total_return | cagr | volatility | mean_excess | sharpe_bil | utility | max_drawdown | decisions | turnover_annual | costs_usd | cost_ratio | mean_cash_plus_bil | mean_receivables | mean_risky | mean_target_risky | mean_bil | mean_cash_usd | n_returns | turnover |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B0 | 2.00% | 2.00% | 0.19% | -0.03% | -11.434 | -0.000 | -0.02% | 12 | 0.02x | 2.19 | 0.00% | 99.97% | 0.03% | 0.00% | 0.00% | 98.78% | 1.18% | 252 | 0.02x |
| B1 | 17.34% | 17.34% | 5.13% | 14.11% | 2.753 | 0.137 | -2.07% | 12 | 0.28x | 46.32 | 0.03% | 1.38% | 0.06% | 98.56% | 100.00% | 0.00% | 1.38% | 252 | 0.28x |
| B2 | 14.85% | 14.85% | 4.04% | 11.92% | 2.956 | 0.117 | -1.36% | 12 | 1.16x | 201.74 | 0.12% | 1.66% | 0.06% | 98.29% | 99.78% | 0.21% | 1.45% | 252 | 1.16x |
| B3 | 7.68% | 7.68% | 2.70% | 5.42% | 2.020 | 0.053 | -1.52% | 12 | 3.39x | 458.38 | 0.34% | 40.40% | 0.06% | 59.55% | 60.18% | 39.01% | 1.38% | 252 | 3.39x |
| REF_SPY | 27.07% | 27.07% | 11.01% | 22.56% | 2.052 | 0.207 | -5.86% | 0 | 0.00x | 0.00 | 0.00% | 11.57% | 0.19% | 88.24% | n/a | 0.00% | 11.57% | 252 | 0.00x |
| H1_252_3 | 10.51% | 10.51% | 4.02% | 8.07% | 2.007 | 0.078 | -2.70% | 12 | 4.71x | 687.92 | 0.47% | 36.00% | 0.05% | 63.95% | 64.52% | 34.78% | 1.22% | 252 | 4.71x |
| H1_252_4 | 11.73% | 11.73% | 4.38% | 9.18% | 2.098 | 0.089 | -3.19% | 12 | 4.35x | 607.31 | 0.44% | 25.15% | 0.06% | 74.79% | 75.38% | 23.89% | 1.26% | 252 | 4.35x |
| H1_126_3 | 11.34% | 11.34% | 4.29% | 8.82% | 2.056 | 0.085 | -2.77% | 12 | 5.44x | 807.70 | 0.54% | 34.99% | 0.04% | 64.97% | 65.77% | 33.74% | 1.25% | 252 | 5.44x |
| H1_126_4 | 9.47% | 9.47% | 4.43% | 7.13% | 1.610 | 0.068 | -3.19% | 12 | 5.04x | 773.05 | 0.50% | 26.70% | 0.04% | 73.26% | 74.01% | 25.43% | 1.28% | 252 | 5.04x |
| H2_4of6 | 8.15% | 8.15% | 3.28% | 5.88% | 1.794 | 0.057 | -2.05% | 12 | 7.00x | 993.04 | 0.70% | 51.78% | 0.05% | 48.17% | 48.76% | 50.57% | 1.21% | 252 | 7.00x |
| H2_5of6 | 3.23% | 3.23% | 1.14% | 1.18% | 1.044 | 0.012 | -0.72% | 12 | 1.00x | 108.02 | 0.10% | 85.45% | 0.05% | 14.50% | 14.58% | 84.29% | 1.17% | 252 | 1.00x |
| P_A1 | 11.34% | 11.34% | 4.29% | 8.83% | 2.057 | 0.086 | -2.77% | 12 | 5.44x | 628.50 | 0.54% | 35.00% | 0.04% | 64.96% | 65.77% | 33.73% | 1.27% | 252 | 5.44x |
| H1_252_3_WF | 10.53% | 10.53% | 4.01% | 8.08% | 2.012 | 0.078 | -2.70% | 12 | 4.71x | 520.30 | 0.47% | 36.01% | 0.05% | 63.94% | 64.52% | 34.78% | 1.23% | 252 | 4.71x |

### 2019 max_group

| run | Equity | Treasury | Credit | Real |
|---|---|---|---|---|
| B0 | 0.00% | 0.00% | 0.00% | 0.00% |
| B1 | 34.23% | 23.40% | 22.22% | 22.53% |
| B2 | 25.50% | 32.95% | 39.91% | 16.22% |
| B3 | 24.15% | 26.31% | 38.26% | 8.18% |
| REF_SPY | 88.76% | 0.00% | 0.00% | 0.00% |
| H1_252_3 | 26.12% | 49.28% | 49.86% | 15.17% |
| H1_252_4 | 26.15% | 41.19% | 49.58% | 16.07% |
| H1_126_3 | 26.05% | 49.48% | 49.86% | 24.69% |
| H1_126_4 | 26.00% | 43.37% | 49.87% | 18.53% |
| H2_4of6 | 26.05% | 46.68% | 49.91% | 0.00% |
| H2_5of6 | 0.00% | 0.00% | 25.39% | 0.00% |
| P_A1 | 26.09% | 49.41% | 49.94% | 24.71% |
| H1_252_3_WF | 26.21% | 49.22% | 49.94% | 15.19% |

### 2019 max_weight

| run | DBC | EEM | EFA | GLD | HYG | IEF | LQD | SPY | TLT |
|---|---|---|---|---|---|---|---|---|---|
| B0 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| B1 | 11.63% | 11.57% | 11.45% | 11.79% | 11.15% | 11.47% | 11.26% | 11.37% | 12.12% |
| B2 | 7.90% | 7.61% | 9.15% | 10.63% | 24.74% | 22.97% | 24.90% | 8.86% | 10.78% |
| B3 | 0.00% | 7.20% | 8.60% | 8.18% | 24.81% | 17.64% | 19.51% | 8.42% | 8.69% |
| REF_SPY | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 88.76% | 0.00% |
| H1_252_3 | 0.00% | 0.00% | 0.00% | 15.17% | 25.11% | 25.22% | 24.91% | 26.12% | 24.48% |
| H1_252_4 | 0.00% | 0.00% | 0.00% | 16.07% | 25.07% | 25.00% | 24.93% | 26.15% | 16.54% |
| H1_126_3 | 0.00% | 0.00% | 0.00% | 24.69% | 25.00% | 25.10% | 25.13% | 26.05% | 24.80% |
| H1_126_4 | 0.00% | 0.00% | 0.00% | 18.53% | 25.01% | 25.10% | 25.09% | 26.00% | 18.70% |
| H2_4of6 | 0.00% | 0.00% | 0.00% | 0.00% | 25.05% | 25.29% | 24.94% | 26.05% | 22.08% |
| H2_5of6 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 25.39% | 0.00% | 0.00% |
| P_A1 | 0.00% | 0.00% | 0.00% | 24.71% | 25.02% | 25.11% | 25.16% | 26.09% | 24.74% |
| H1_252_3_WF | 0.00% | 0.00% | 0.00% | 15.19% | 25.05% | 25.24% | 24.97% | 26.21% | 24.46% |

### 2019 mean_group

| run | Equity | Treasury | Credit | Real |
|---|---|---|---|---|
| B0 | 0.00% | 0.00% | 0.00% | 0.00% |
| B1 | 32.95% | 21.77% | 21.84% | 22.00% |
| B2 | 19.15% | 26.56% | 38.08% | 14.50% |
| B3 | 8.32% | 19.88% | 28.05% | 3.30% |
| REF_SPY | 88.24% | 0.00% | 0.00% | 0.00% |
| H1_252_3 | 3.46% | 32.40% | 26.91% | 1.18% |
| H1_252_4 | 3.81% | 31.95% | 34.55% | 4.49% |
| H1_126_3 | 3.86% | 28.61% | 24.89% | 7.60% |
| H1_126_4 | 5.48% | 30.39% | 29.10% | 8.28% |
| H2_4of6 | 3.45% | 21.90% | 22.82% | 0.00% |
| H2_5of6 | 0.00% | 0.00% | 14.50% | 0.00% |
| P_A1 | 3.86% | 28.60% | 24.90% | 7.60% |
| H1_252_3_WF | 3.47% | 32.37% | 26.91% | 1.18% |

### 2019 mean_weight

| run | DBC | EEM | EFA | GLD | HYG | IEF | LQD | SPY | TLT |
|---|---|---|---|---|---|---|---|---|---|
| B0 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| B1 | 11.03% | 10.99% | 10.99% | 10.97% | 10.93% | 10.88% | 10.91% | 10.97% | 10.88% |
| B2 | 6.34% | 5.46% | 7.35% | 8.16% | 18.07% | 18.13% | 20.01% | 6.34% | 8.43% |
| B3 | 0.00% | 1.54% | 1.94% | 3.30% | 14.48% | 13.56% | 13.56% | 4.85% | 6.31% |
| REF_SPY | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 88.24% | 0.00% |
| H1_252_3 | 0.00% | 0.00% | 0.00% | 1.18% | 10.28% | 22.57% | 16.63% | 3.46% | 9.83% |
| H1_252_4 | 0.00% | 0.00% | 0.00% | 4.49% | 13.94% | 22.41% | 20.61% | 3.81% | 9.54% |
| H1_126_3 | 0.00% | 0.00% | 0.00% | 7.60% | 6.19% | 20.56% | 18.70% | 3.86% | 8.05% |
| H1_126_4 | 0.00% | 0.00% | 0.00% | 8.28% | 8.32% | 20.59% | 20.79% | 5.48% | 9.81% |
| H2_4of6 | 0.00% | 0.00% | 0.00% | 0.00% | 6.18% | 14.07% | 16.64% | 3.45% | 7.83% |
| H2_5of6 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 14.50% | 0.00% | 0.00% |
| P_A1 | 0.00% | 0.00% | 0.00% | 7.60% | 6.19% | 20.56% | 18.71% | 3.86% | 8.05% |
| H1_252_3_WF | 0.00% | 0.00% | 0.00% | 1.18% | 10.28% | 22.57% | 16.63% | 3.47% | 9.80% |

### 2020

| run | total_return | cagr | volatility | mean_excess | sharpe_bil | utility | max_drawdown | decisions | turnover_annual | costs_usd | cost_ratio | mean_cash_plus_bil | mean_receivables | mean_risky | mean_target_risky | mean_bil | mean_cash_usd | n_returns | turnover |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B0 | 0.39% | 0.39% | 0.18% | -0.00% | -2.402 | -0.000 | -0.09% | 12 | 0.01x | 0.55 | 0.00% | 100.00% | 0.00% | 0.00% | 0.00% | 98.94% | 1.05% | 253 | 0.01x |
| B1 | 4.69% | 4.67% | 12.43% | 4.95% | 0.398 | 0.026 | -17.83% | 12 | 2.14x | 371.41 | 0.21% | 24.58% | 0.04% | 75.38% | 76.39% | 23.33% | 1.25% | 253 | 2.15x |
| B2 | 5.18% | 5.16% | 10.66% | 5.21% | 0.488 | 0.035 | -16.35% | 12 | 1.93x | 353.46 | 0.19% | 14.91% | 0.04% | 85.06% | 86.27% | 13.54% | 1.36% | 253 | 1.94x |
| B3 | 1.96% | 1.95% | 6.34% | 1.74% | 0.273 | 0.011 | -9.59% | 12 | 3.02x | 427.06 | 0.30% | 31.10% | 0.03% | 68.87% | 69.92% | 29.72% | 1.38% | 253 | 3.03x |
| REF_SPY | 15.85% | 15.78% | 28.90% | 18.46% | 0.639 | 0.059 | -29.95% | 0 | 0.00x | 0.00 | 0.00% | 12.06% | 0.18% | 87.75% | n/a | 0.00% | 12.06% | 253 | 0.00x |
| H1_252_3 | 4.82% | 4.80% | 7.91% | 4.60% | 0.582 | 0.037 | -8.63% | 12 | 3.31x | 516.11 | 0.33% | 35.64% | 0.02% | 64.35% | 65.14% | 34.48% | 1.16% | 253 | 3.32x |
| H1_252_4 | 4.64% | 4.62% | 8.24% | 4.46% | 0.541 | 0.034 | -9.69% | 12 | 2.57x | 384.66 | 0.26% | 26.63% | 0.02% | 73.35% | 74.34% | 25.35% | 1.27% | 253 | 2.58x |
| H1_126_3 | 0.44% | 0.44% | 13.16% | 0.91% | 0.069 | -0.017 | -17.33% | 12 | 7.36x | 1114.82 | 0.74% | 36.18% | 0.03% | 63.79% | 64.69% | 35.11% | 1.07% | 253 | 7.39x |
| H1_126_4 | 1.08% | 1.08% | 14.02% | 1.66% | 0.119 | -0.013 | -20.44% | 12 | 7.49x | 1159.93 | 0.75% | 28.48% | 0.04% | 71.48% | 72.24% | 27.43% | 1.05% | 253 | 7.52x |
| H2_4of6 | -1.61% | -1.60% | 5.12% | -1.88% | -0.367 | -0.023 | -7.59% | 12 | 3.99x | 579.02 | 0.40% | 51.35% | 0.01% | 48.63% | 49.44% | 50.20% | 1.15% | 253 | 4.00x |
| H2_5of6 | -1.04% | -1.04% | 3.58% | -1.38% | -0.384 | -0.016 | -5.36% | 12 | 2.90x | 322.78 | 0.29% | 78.96% | 0.01% | 21.03% | 21.24% | 77.86% | 1.10% | 253 | 2.91x |
| P_A1 | 0.45% | 0.45% | 13.15% | 0.92% | 0.070 | -0.017 | -17.33% | 12 | 7.36x | 866.70 | 0.74% | 36.18% | 0.03% | 63.78% | 64.69% | 35.09% | 1.09% | 253 | 7.39x |
| H1_252_3_WF | 4.80% | 4.78% | 7.90% | 4.59% | 0.580 | 0.036 | -8.63% | 12 | 3.30x | 389.72 | 0.33% | 35.69% | 0.02% | 64.29% | 65.14% | 34.47% | 1.22% | 253 | 3.31x |

### 2020 max_group

| run | Equity | Treasury | Credit | Real |
|---|---|---|---|---|
| B0 | 0.00% | 0.00% | 0.00% | 0.00% |
| B1 | 35.25% | 26.40% | 22.26% | 22.71% |
| B2 | 23.99% | 33.29% | 40.26% | 20.55% |
| B3 | 23.81% | 32.70% | 39.87% | 15.98% |
| REF_SPY | 88.93% | 0.00% | 0.00% | 0.00% |
| H1_252_3 | 19.67% | 43.44% | 49.96% | 26.64% |
| H1_252_4 | 29.73% | 40.91% | 49.94% | 21.71% |
| H1_126_3 | 50.34% | 44.48% | 49.62% | 26.57% |
| H1_126_4 | 50.63% | 38.69% | 47.75% | 22.36% |
| H2_4of6 | 19.67% | 43.52% | 49.95% | 25.21% |
| H2_5of6 | 18.05% | 43.83% | 25.15% | 0.00% |
| P_A1 | 50.29% | 44.52% | 49.54% | 26.57% |
| H1_252_3_WF | 19.71% | 43.44% | 49.94% | 26.65% |

### 2020 max_weight

| run | DBC | EEM | EFA | GLD | HYG | IEF | LQD | SPY | TLT |
|---|---|---|---|---|---|---|---|---|---|
| B0 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| B1 | 11.56% | 11.60% | 12.11% | 12.59% | 11.00% | 12.97% | 11.26% | 11.61% | 13.45% |
| B2 | 9.38% | 7.05% | 8.89% | 11.38% | 24.40% | 24.75% | 21.76% | 9.69% | 8.99% |
| B3 | 7.37% | 7.03% | 8.27% | 11.12% | 24.41% | 24.68% | 17.90% | 8.58% | 8.08% |
| REF_SPY | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 88.93% | 0.00% |
| H1_252_3 | 0.00% | 0.00% | 0.00% | 26.64% | 24.75% | 26.15% | 25.31% | 19.67% | 18.87% |
| H1_252_4 | 0.00% | 0.00% | 14.46% | 21.71% | 24.76% | 26.39% | 25.37% | 16.65% | 14.93% |
| H1_126_3 | 0.00% | 21.27% | 24.03% | 26.57% | 25.35% | 24.84% | 24.85% | 25.19% | 20.89% |
| H1_126_4 | 16.35% | 17.17% | 18.78% | 22.36% | 25.38% | 24.74% | 25.66% | 22.57% | 16.19% |
| H2_4of6 | 0.00% | 0.00% | 0.00% | 25.21% | 24.75% | 25.00% | 25.28% | 19.67% | 18.94% |
| H2_5of6 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 24.82% | 25.15% | 18.05% | 19.26% |
| P_A1 | 0.00% | 21.27% | 24.02% | 26.57% | 25.35% | 24.88% | 24.87% | 25.17% | 20.90% |
| H1_252_3_WF | 0.00% | 0.00% | 0.00% | 26.65% | 24.75% | 26.05% | 25.27% | 19.71% | 18.91% |

### 2020 mean_group

| run | Equity | Treasury | Credit | Real |
|---|---|---|---|---|
| B0 | 0.00% | 0.00% | 0.00% | 0.00% |
| B1 | 25.29% | 16.70% | 16.59% | 16.80% |
| B2 | 16.35% | 27.03% | 27.14% | 14.53% |
| B3 | 9.75% | 27.82% | 23.22% | 8.08% |
| REF_SPY | 87.75% | 0.00% | 0.00% | 0.00% |
| H1_252_3 | 2.92% | 30.99% | 18.11% | 12.32% |
| H1_252_4 | 3.66% | 31.41% | 25.44% | 12.84% |
| H1_126_3 | 15.98% | 23.21% | 12.16% | 12.44% |
| H1_126_4 | 16.76% | 19.73% | 22.15% | 12.84% |
| H2_4of6 | 2.91% | 24.71% | 14.02% | 6.99% |
| H2_5of6 | 1.48% | 13.62% | 5.93% | 0.00% |
| P_A1 | 15.98% | 23.22% | 12.15% | 12.44% |
| H1_252_3_WF | 2.91% | 30.98% | 18.09% | 12.31% |

### 2020 mean_weight

| run | DBC | EEM | EFA | GLD | HYG | IEF | LQD | SPY | TLT |
|---|---|---|---|---|---|---|---|---|---|
| B0 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| B1 | 8.34% | 8.47% | 8.41% | 8.46% | 8.29% | 8.35% | 8.29% | 8.41% | 8.35% |
| B2 | 6.75% | 5.04% | 5.79% | 7.78% | 13.31% | 19.65% | 13.83% | 5.52% | 7.37% |
| B3 | 0.59% | 2.62% | 2.59% | 7.49% | 10.01% | 20.71% | 13.21% | 4.54% | 7.11% |
| REF_SPY | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 87.75% | 0.00% |
| H1_252_3 | 0.00% | 0.00% | 0.00% | 12.32% | 3.89% | 20.76% | 14.22% | 2.92% | 10.23% |
| H1_252_4 | 0.00% | 0.00% | 1.19% | 12.84% | 3.89% | 19.91% | 21.55% | 2.47% | 11.50% |
| H1_126_3 | 0.00% | 4.71% | 4.79% | 12.44% | 5.88% | 12.34% | 6.28% | 6.49% | 10.87% |
| H1_126_4 | 1.26% | 5.60% | 4.18% | 11.57% | 5.65% | 11.67% | 16.50% | 6.98% | 8.07% |
| H2_4of6 | 0.00% | 0.00% | 0.00% | 6.99% | 3.89% | 18.63% | 10.13% | 2.91% | 6.08% |
| H2_5of6 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 10.51% | 5.93% | 1.48% | 3.11% |
| P_A1 | 0.00% | 4.70% | 4.79% | 12.44% | 5.87% | 12.35% | 6.28% | 6.49% | 10.87% |
| H1_252_3_WF | 0.00% | 0.00% | 0.00% | 12.31% | 3.89% | 20.74% | 14.20% | 2.91% | 10.23% |

### 2021

| run | total_return | cagr | volatility | mean_excess | sharpe_bil | utility | max_drawdown | decisions | turnover_annual | costs_usd | cost_ratio | mean_cash_plus_bil | mean_receivables | mean_risky | mean_target_risky | mean_bil | mean_cash_usd | n_returns | turnover |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B0 | -0.10% | -0.10% | 0.14% | 0.00% | 0.707 | 0.000 | -0.11% | 12 | 0.00x | 0.00 | 0.00% | 100.00% | 0.00% | 0.00% | 0.00% | 98.96% | 1.04% | 252 | 0.00x |
| B1 | 6.91% | 6.91% | 6.87% | 7.02% | 1.022 | 0.063 | -3.62% | 12 | 0.25x | 49.08 | 0.03% | 1.35% | 0.04% | 98.61% | 100.00% | 0.00% | 1.35% | 252 | 0.25x |
| B2 | 4.00% | 4.00% | 5.21% | 4.16% | 0.798 | 0.037 | -3.28% | 12 | 0.96x | 188.76 | 0.10% | 2.67% | 0.04% | 97.29% | 98.70% | 1.29% | 1.38% | 252 | 0.96x |
| B3 | 2.58% | 2.58% | 4.61% | 2.75% | 0.597 | 0.024 | -3.04% | 12 | 1.81x | 260.30 | 0.18% | 27.41% | 0.04% | 72.55% | 73.97% | 25.96% | 1.45% | 252 | 1.81x |
| REF_SPY | 25.32% | 25.32% | 11.60% | 23.35% | 2.014 | 0.213 | -4.59% | 0 | 0.00x | 0.00 | 0.00% | 10.41% | 0.14% | 89.45% | n/a | 0.00% | 10.41% | 252 | 0.00x |
| H1_252_3 | 3.94% | 3.94% | 6.01% | 4.15% | 0.691 | 0.036 | -3.40% | 12 | 4.17x | 671.51 | 0.42% | 38.30% | 0.05% | 61.65% | 62.34% | 37.22% | 1.08% | 252 | 4.17x |
| H1_252_4 | 4.14% | 4.14% | 5.93% | 4.33% | 0.731 | 0.038 | -3.38% | 12 | 2.77x | 426.98 | 0.28% | 31.08% | 0.05% | 68.87% | 69.74% | 29.92% | 1.16% | 252 | 2.77x |
| H1_126_3 | 9.26% | 9.26% | 6.31% | 9.16% | 1.453 | 0.086 | -2.85% | 12 | 5.89x | 979.20 | 0.59% | 34.33% | 0.04% | 65.63% | 66.28% | 33.19% | 1.14% | 252 | 5.89x |
| H1_126_4 | 8.03% | 8.03% | 6.39% | 8.03% | 1.257 | 0.074 | -2.82% | 12 | 5.81x | 991.35 | 0.58% | 27.40% | 0.04% | 72.56% | 73.45% | 26.17% | 1.22% | 252 | 5.81x |
| H2_4of6 | 4.52% | 4.52% | 4.92% | 4.64% | 0.945 | 0.043 | -2.74% | 12 | 3.84x | 561.47 | 0.38% | 53.12% | 0.03% | 46.84% | 46.88% | 52.01% | 1.11% | 252 | 3.84x |
| H2_5of6 | -0.26% | -0.26% | 3.68% | -0.10% | -0.027 | -0.003 | -2.12% | 12 | 4.19x | 462.53 | 0.42% | 72.54% | 0.02% | 27.44% | 27.55% | 71.39% | 1.15% | 252 | 4.19x |
| P_A1 | 4.81% | 4.81% | 5.97% | 4.97% | 0.834 | 0.044 | -3.36% | 12 | 3.52x | 433.83 | 0.35% | 31.20% | 0.05% | 68.75% | 69.74% | 29.91% | 1.30% | 252 | 3.52x |
| H1_252_3_WF | 3.94% | 3.94% | 6.00% | 4.14% | 0.691 | 0.036 | -3.39% | 12 | 4.17x | 507.36 | 0.42% | 38.34% | 0.05% | 61.61% | 62.34% | 37.22% | 1.12% | 252 | 4.17x |

### 2021 max_group

| run | Equity | Treasury | Credit | Real |
|---|---|---|---|---|
| B0 | 0.00% | 0.00% | 0.00% | 0.00% |
| B1 | 34.39% | 22.77% | 22.25% | 22.86% |
| B2 | 23.28% | 31.64% | 41.29% | 13.49% |
| B3 | 23.71% | 30.48% | 41.50% | 14.42% |
| REF_SPY | 90.06% | 0.00% | 0.00% | 0.00% |
| H1_252_3 | 50.07% | 40.19% | 25.02% | 24.01% |
| H1_252_4 | 48.56% | 38.49% | 24.89% | 12.51% |
| H1_126_3 | 50.05% | 25.19% | 49.76% | 26.12% |
| H1_126_4 | 50.59% | 24.73% | 49.61% | 21.68% |
| H2_4of6 | 42.87% | 0.00% | 25.02% | 24.19% |
| H2_5of6 | 43.18% | 0.00% | 25.02% | 12.78% |
| P_A1 | 48.62% | 38.29% | 24.91% | 12.51% |
| H1_252_3_WF | 49.85% | 40.13% | 25.00% | 24.00% |

### 2021 max_weight

| run | DBC | EEM | EFA | GLD | HYG | IEF | LQD | SPY | TLT |
|---|---|---|---|---|---|---|---|---|---|
| B0 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| B1 | 12.33% | 11.83% | 11.42% | 11.55% | 11.15% | 11.28% | 11.22% | 11.37% | 11.58% |
| B2 | 8.19% | 6.75% | 9.06% | 8.02% | 25.05% | 23.80% | 18.18% | 8.93% | 8.72% |
| B3 | 8.21% | 6.87% | 9.68% | 8.54% | 24.90% | 22.87% | 17.31% | 8.40% | 7.61% |
| REF_SPY | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 90.06% | 0.00% |
| H1_252_3 | 24.01% | 12.98% | 25.11% | 0.00% | 25.02% | 24.70% | 24.70% | 25.09% | 15.52% |
| H1_252_4 | 12.51% | 11.87% | 20.14% | 11.08% | 24.89% | 24.86% | 24.77% | 18.18% | 13.78% |
| H1_126_3 | 26.12% | 21.15% | 25.21% | 0.00% | 24.90% | 0.00% | 24.96% | 25.36% | 25.19% |
| H1_126_4 | 21.68% | 17.72% | 20.99% | 0.00% | 24.84% | 24.73% | 24.89% | 24.19% | 18.75% |
| H2_4of6 | 24.19% | 13.00% | 22.97% | 0.00% | 25.02% | 0.00% | 0.00% | 25.18% | 0.00% |
| H2_5of6 | 12.78% | 12.99% | 23.07% | 0.00% | 25.02% | 0.00% | 0.00% | 20.21% | 0.00% |
| P_A1 | 12.51% | 11.88% | 20.14% | 10.93% | 24.91% | 24.72% | 24.59% | 18.15% | 13.71% |
| H1_252_3_WF | 24.00% | 12.96% | 25.11% | 0.00% | 25.00% | 24.68% | 24.68% | 24.87% | 15.48% |

### 2021 mean_group

| run | Equity | Treasury | Credit | Real |
|---|---|---|---|---|
| B0 | 0.00% | 0.00% | 0.00% | 0.00% |
| B1 | 33.08% | 21.72% | 21.76% | 22.05% |
| B2 | 20.22% | 26.43% | 38.62% | 12.02% |
| B3 | 20.30% | 6.23% | 37.74% | 8.28% |
| REF_SPY | 89.45% | 0.00% | 0.00% | 0.00% |
| H1_252_3 | 29.27% | 4.85% | 22.45% | 5.08% |
| H1_252_4 | 31.82% | 4.72% | 24.57% | 7.76% |
| H1_126_3 | 29.73% | 2.11% | 22.43% | 11.36% |
| H1_126_4 | 28.33% | 4.65% | 28.51% | 11.08% |
| H2_4of6 | 25.26% | 0.00% | 16.50% | 5.09% |
| H2_5of6 | 18.16% | 0.00% | 6.25% | 3.02% |
| P_A1 | 31.75% | 4.71% | 24.55% | 7.75% |
| H1_252_3_WF | 29.25% | 4.84% | 22.43% | 5.08% |

### 2021 mean_weight

| run | DBC | EEM | EFA | GLD | HYG | IEF | LQD | SPY | TLT |
|---|---|---|---|---|---|---|---|---|---|
| B0 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| B1 | 11.16% | 10.98% | 11.07% | 10.89% | 10.90% | 10.87% | 10.86% | 11.03% | 10.84% |
| B2 | 5.44% | 5.37% | 7.26% | 6.58% | 23.28% | 19.28% | 15.34% | 7.59% | 7.15% |
| B3 | 4.94% | 5.39% | 7.33% | 3.34% | 23.63% | 5.13% | 14.11% | 7.58% | 1.09% |
| REF_SPY | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 89.45% | 0.00% |
| H1_252_3 | 5.08% | 2.07% | 10.26% | 0.00% | 18.75% | 3.70% | 3.69% | 16.95% | 1.15% |
| H1_252_4 | 6.95% | 3.64% | 12.75% | 0.81% | 20.88% | 3.70% | 3.70% | 15.43% | 1.02% |
| H1_126_3 | 11.36% | 2.73% | 11.18% | 0.00% | 16.26% | 0.00% | 6.16% | 15.81% | 2.11% |
| H1_126_4 | 11.08% | 4.53% | 11.19% | 0.00% | 20.33% | 2.04% | 8.18% | 12.61% | 2.60% |
| H2_4of6 | 5.09% | 2.06% | 8.11% | 0.00% | 16.50% | 0.00% | 0.00% | 15.09% | 0.00% |
| H2_5of6 | 3.02% | 2.06% | 4.85% | 0.00% | 6.25% | 0.00% | 0.00% | 11.25% | 0.00% |
| P_A1 | 6.95% | 3.64% | 12.75% | 0.80% | 20.88% | 3.69% | 3.68% | 15.36% | 1.02% |
| H1_252_3_WF | 5.08% | 2.06% | 10.27% | 0.00% | 18.74% | 3.70% | 3.69% | 16.92% | 1.14% |

### 2022

| run | total_return | cagr | volatility | mean_excess | sharpe_bil | utility | max_drawdown | decisions | turnover_annual | costs_usd | cost_ratio | mean_cash_plus_bil | mean_receivables | mean_risky | mean_target_risky | mean_bil | mean_cash_usd | n_returns | turnover |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B0 | 1.36% | 1.37% | 0.24% | -0.02% | -5.920 | -0.000 | -0.03% | 12 | 0.01x | 0.73 | 0.00% | 99.98% | 0.02% | 0.00% | 0.00% | 98.86% | 1.12% | 251 | 0.01x |
| B1 | -11.92% | -11.96% | 10.85% | -13.53% | -1.248 | -0.153 | -16.83% | 12 | 0.75x | 136.41 | 0.07% | 10.84% | 0.05% | 89.11% | 90.57% | 9.40% | 1.44% | 251 | 0.74x |
| B2 | -13.47% | -13.52% | 10.43% | -15.36% | -1.475 | -0.170 | -18.32% | 12 | 1.12x | 202.90 | 0.11% | 7.18% | 0.05% | 92.77% | 94.21% | 5.74% | 1.45% | 251 | 1.11x |
| B3 | -1.92% | -1.93% | 3.93% | -3.25% | -0.832 | -0.035 | -3.56% | 12 | 2.51x | 366.09 | 0.25% | 75.57% | 0.03% | 24.41% | 25.00% | 74.34% | 1.22% | 251 | 2.50x |
| REF_SPY | -16.31% | -16.37% | 21.28% | -16.99% | -0.798 | -0.238 | -21.95% | 0 | 0.00x | 0.00 | 0.00% | 11.96% | 0.16% | 87.88% | n/a | 0.00% | 11.96% | 251 | 0.00x |
| H1_252_3 | -0.94% | -0.95% | 8.86% | -1.94% | -0.219 | -0.031 | -7.48% | 12 | 2.69x | 450.62 | 0.27% | 53.58% | 0.03% | 46.38% | 47.38% | 52.43% | 1.16% | 251 | 2.68x |
| H1_252_4 | -7.15% | -7.18% | 8.57% | -8.45% | -0.989 | -0.096 | -11.06% | 12 | 4.01x | 619.01 | 0.40% | 52.04% | 0.03% | 47.92% | 48.89% | 50.89% | 1.15% | 251 | 3.99x |
| H1_126_3 | -5.18% | -5.20% | 7.70% | -6.42% | -0.836 | -0.073 | -7.83% | 12 | 5.05x | 850.06 | 0.50% | 64.00% | 0.03% | 35.97% | 36.93% | 62.92% | 1.08% | 251 | 5.03x |
| H1_126_4 | -5.63% | -5.65% | 7.05% | -6.95% | -0.990 | -0.077 | -7.56% | 12 | 5.68x | 968.79 | 0.57% | 66.46% | 0.03% | 33.51% | 34.53% | 65.38% | 1.08% | 251 | 5.66x |
| H2_4of6 | 3.07% | 3.08% | 6.31% | 1.86% | 0.295 | 0.013 | -5.00% | 12 | 3.06x | 468.43 | 0.30% | 77.93% | 0.03% | 22.05% | 22.39% | 76.87% | 1.06% | 251 | 3.05x |
| H2_5of6 | 2.24% | 2.25% | 5.33% | 0.99% | 0.187 | 0.006 | -5.00% | 12 | 1.10x | 121.44 | 0.11% | 89.84% | 0.02% | 10.14% | 9.99% | 88.84% | 0.99% | 251 | 1.09x |
| P_A1 | -1.04% | -1.04% | 8.85% | -2.03% | -0.230 | -0.032 | -7.47% | 12 | 3.23x | 416.74 | 0.32% | 53.62% | 0.03% | 46.35% | 47.38% | 52.42% | 1.20% | 251 | 3.22x |
| H1_252_3_WF | -0.95% | -0.95% | 8.86% | -1.94% | -0.219 | -0.031 | -7.47% | 12 | 2.69x | 340.76 | 0.27% | 53.58% | 0.03% | 46.38% | 47.38% | 52.41% | 1.17% | 251 | 2.67x |

### 2022 max_group

| run | Equity | Treasury | Credit | Real |
|---|---|---|---|---|
| B0 | 0.00% | 0.00% | 0.00% | 0.00% |
| B1 | 33.54% | 22.78% | 22.25% | 24.77% |
| B2 | 23.82% | 29.51% | 38.50% | 21.18% |
| B3 | 19.33% | 10.60% | 23.02% | 28.01% |
| REF_SPY | 89.91% | 0.00% | 0.00% | 0.00% |
| H1_252_3 | 49.57% | 0.00% | 0.00% | 53.04% |
| H1_252_4 | 35.84% | 24.75% | 24.68% | 52.82% |
| H1_126_3 | 25.17% | 45.85% | 24.70% | 49.50% |
| H1_126_4 | 34.79% | 40.41% | 24.67% | 43.53% |
| H2_4of6 | 49.41% | 0.00% | 0.00% | 49.09% |
| H2_5of6 | 0.00% | 0.00% | 0.00% | 28.07% |
| P_A1 | 49.57% | 0.00% | 0.00% | 53.07% |
| H1_252_3_WF | 49.65% | 0.00% | 0.00% | 53.08% |

### 2022 max_weight

| run | DBC | EEM | EFA | GLD | HYG | IEF | LQD | SPY | TLT |
|---|---|---|---|---|---|---|---|---|---|
| B0 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| B1 | 12.95% | 11.43% | 11.23% | 11.82% | 11.10% | 11.42% | 11.22% | 11.53% | 11.37% |
| B2 | 9.32% | 8.84% | 8.70% | 13.62% | 23.03% | 20.09% | 16.20% | 7.75% | 9.43% |
| B3 | 12.65% | 0.00% | 10.58% | 15.36% | 23.02% | 0.00% | 0.00% | 10.82% | 10.60% |
| REF_SPY | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 89.91% | 0.00% |
| H1_252_3 | 27.76% | 0.00% | 24.97% | 25.29% | 0.00% | 0.00% | 0.00% | 25.33% | 0.00% |
| H1_252_4 | 27.35% | 0.00% | 19.38% | 25.64% | 24.68% | 0.00% | 0.00% | 24.00% | 24.75% |
| H1_126_3 | 27.98% | 0.00% | 0.00% | 25.27% | 24.70% | 25.07% | 0.00% | 25.17% | 20.83% |
| H1_126_4 | 28.02% | 0.00% | 19.44% | 25.19% | 24.67% | 24.94% | 0.00% | 24.59% | 15.52% |
| H2_4of6 | 27.88% | 0.00% | 24.86% | 24.76% | 0.00% | 0.00% | 0.00% | 24.59% | 0.00% |
| H2_5of6 | 28.07% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| P_A1 | 27.76% | 0.00% | 24.99% | 25.32% | 0.00% | 0.00% | 0.00% | 25.17% | 0.00% |
| H1_252_3_WF | 27.76% | 0.00% | 25.00% | 25.33% | 0.00% | 0.00% | 0.00% | 25.28% | 0.00% |

### 2022 mean_group

| run | Equity | Treasury | Credit | Real |
|---|---|---|---|---|
| B0 | 0.00% | 0.00% | 0.00% | 0.00% |
| B1 | 29.56% | 19.60% | 19.74% | 20.21% |
| B2 | 21.29% | 24.51% | 29.65% | 17.32% |
| B3 | 5.73% | 0.92% | 3.54% | 14.22% |
| REF_SPY | 87.88% | 0.00% | 0.00% | 0.00% |
| H1_252_3 | 13.66% | 0.00% | 0.00% | 32.73% |
| H1_252_4 | 10.84% | 3.91% | 3.80% | 29.37% |
| H1_126_3 | 7.19% | 3.61% | 1.85% | 23.32% |
| H1_126_4 | 7.74% | 3.19% | 1.85% | 20.73% |
| H2_4of6 | 3.83% | 0.00% | 0.00% | 18.22% |
| H2_5of6 | 0.00% | 0.00% | 0.00% | 10.14% |
| P_A1 | 13.62% | 0.00% | 0.00% | 32.72% |
| H1_252_3_WF | 13.66% | 0.00% | 0.00% | 32.73% |

### 2022 mean_weight

| run | DBC | EEM | EFA | GLD | HYG | IEF | LQD | SPY | TLT |
|---|---|---|---|---|---|---|---|---|---|
| B0 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| B1 | 10.20% | 9.87% | 9.90% | 10.02% | 9.90% | 9.87% | 9.84% | 9.79% | 9.74% |
| B2 | 6.26% | 7.05% | 7.55% | 11.07% | 15.46% | 16.58% | 14.20% | 6.69% | 7.93% |
| B3 | 9.42% | 0.00% | 2.23% | 4.81% | 3.54% | 0.00% | 0.00% | 3.50% | 0.92% |
| REF_SPY | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 87.88% | 0.00% |
| H1_252_3 | 24.57% | 0.00% | 3.81% | 8.16% | 0.00% | 0.00% | 0.00% | 9.85% | 0.00% |
| H1_252_4 | 21.14% | 0.00% | 2.94% | 8.23% | 3.80% | 0.00% | 0.00% | 7.90% | 3.91% |
| H1_126_3 | 13.07% | 0.00% | 0.00% | 10.25% | 1.85% | 1.98% | 0.00% | 7.19% | 1.63% |
| H1_126_4 | 10.49% | 0.00% | 1.45% | 10.24% | 1.85% | 1.97% | 0.00% | 6.29% | 1.22% |
| H2_4of6 | 16.27% | 0.00% | 1.95% | 1.95% | 0.00% | 0.00% | 0.00% | 1.88% | 0.00% |
| H2_5of6 | 10.14% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| P_A1 | 24.57% | 0.00% | 3.81% | 8.16% | 0.00% | 0.00% | 0.00% | 9.82% | 0.00% |
| H1_252_3_WF | 24.56% | 0.00% | 3.81% | 8.16% | 0.00% | 0.00% | 0.00% | 9.85% | 0.00% |

## T2 Comparisons (walk-forward period)

Paired circular block bootstrap, 10000 replicates, seed 20261006, block lengths 21, 63, 126, primary length 63; Holm adjustment over the primary family at L=63.

| group | candidate | comparator | delta_u | mean_excess_difference | delta_u >= 0.01 | mean_excess_difference > 0 | interval L=21 | interval L=63 | interval L=126 | p L=21 | p L=63 | p L=126 | Holm p L=63 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| primary | H1_252_3 | B3 | 0.005710 | 0.008879 | false | true | [-0.014151, 0.025904] | [-0.013616, 0.024929] | [-0.012683, 0.023608] | 0.2871 | 0.2714 | 0.2629 | 1.0000 |
| primary | H1_252_4 | B3 | 0.002084 | 0.005232 | false | true | [-0.016937, 0.021077] | [-0.016481, 0.021597] | [-0.017112, 0.021908] | 0.4173 | 0.4196 | 0.4212 | 1.0000 |
| primary | H1_126_3 | B3 | 0.009146 | 0.014180 | false | true | [-0.019799, 0.041371] | [-0.021929, 0.043540] | [-0.024133, 0.045003] | 0.2881 | 0.3027 | 0.3143 | 1.0000 |
| primary | H1_126_4 | B3 | 0.001702 | 0.007091 | false | true | [-0.028835, 0.037386] | [-0.030670, 0.037680] | [-0.033476, 0.037666] | 0.4873 | 0.4814 | 0.4747 | 1.0000 |
| primary | H2_4of6 | H1_252_3 | 0.001787 | -0.000733 | false | false | [-0.017560, 0.021360] | [-0.017250, 0.020732] | [-0.016465, 0.019508] | 0.4233 | 0.4324 | 0.4330 | 1.0000 |
| primary | H2_5of6 | H1_252_3 | -0.015110 | -0.019164 | false | false | [-0.040564, 0.010084] | [-0.038965, 0.008284] | [-0.038449, 0.007914] | 0.8763 | 0.8944 | 0.9013 | 1.0000 |
| supplementary | H2_4of6 | B3 | 0.007497 | 0.008145 | false | true | [-0.011316, 0.025958] | [-0.011092, 0.024933] | [-0.010590, 0.023271] | 0.2184 | 0.2022 | 0.1941 | n/a |
| supplementary | H2_5of6 | B3 | -0.009400 | -0.010286 | false | false | [-0.028712, 0.009895] | [-0.027301, 0.007640] | [-0.025632, 0.006326] | 0.8364 | 0.8515 | 0.8857 | n/a |
| supplementary | H2_4of6 | B2 | 0.004547 | 0.001363 | false | true | [-0.035581, 0.044351] | [-0.036351, 0.044117] | [-0.039194, 0.043951] | 0.4058 | 0.3978 | 0.4022 | n/a |
| supplementary | H2_5of6 | B2 | -0.012350 | -0.017068 | false | false | [-0.056112, 0.029300] | [-0.056284, 0.029756] | [-0.057924, 0.029432] | 0.7081 | 0.6984 | 0.7058 | n/a |
| policy | P_A1 | H1_252_3_WF | 0.000807 | 0.002511 | false | true | [-0.024686, 0.032225] | [-0.026799, 0.035262] | [-0.025722, 0.033816] | n/a | n/a | n/a | n/a |

P_A1 vs H1_252_3_WF: intervals conditional on the realized selections of P_A1; no p-value is reported (P13).

## T3 Annual differences (sum of daily candidate minus comparator returns)

| group | candidate | comparator | 2014 | 2015 | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | positive years | largest positive share |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| primary | H1_252_3 | B3 | 0.030710 | 0.020044 | -0.015273 | -0.000937 | -0.036971 | 0.026467 | 0.028777 | 0.013960 | 0.013060 | 6 | 0.2309 |
| primary | H1_252_4 | B3 | 0.023810 | -0.000665 | -0.005828 | 0.022002 | -0.021157 | 0.037590 | 0.027357 | 0.015799 | -0.051857 | 5 | 0.2970 |
| primary | H1_126_3 | B3 | 0.018506 | -0.062589 | 0.071516 | 0.032002 | 0.009859 | 0.034011 | -0.008290 | 0.064067 | -0.031573 | 6 | 0.3110 |
| primary | H1_126_4 | B3 | 0.022856 | -0.068914 | 0.040182 | 0.024131 | 0.013124 | 0.017127 | -0.000713 | 0.052804 | -0.036831 | 6 | 0.3102 |
| primary | H2_4of6 | H1_252_3 | 0.000269 | -0.031337 | 0.014443 | 0.001910 | 0.052371 | -0.021936 | -0.065073 | 0.004941 | 0.037817 | 6 | 0.4686 |
| primary | H2_5of6 | H1_252_3 | -0.041189 | -0.032142 | 0.013941 | -0.022553 | 0.051840 | -0.068928 | -0.060025 | -0.042457 | 0.029186 | 3 | 0.5459 |
| supplementary | H2_4of6 | B3 | 0.030978 | -0.011292 | -0.000830 | 0.000973 | 0.015400 | 0.004531 | -0.036296 | 0.018901 | 0.050877 | 6 | 0.4182 |
| supplementary | H2_5of6 | B3 | -0.010479 | -0.012098 | -0.001332 | -0.023490 | 0.014870 | -0.042461 | -0.031248 | -0.028497 | 0.042246 | 2 | 0.7397 |
| supplementary | H2_4of6 | B2 | 0.021609 | 0.029063 | -0.070261 | -0.016964 | 0.004057 | -0.060473 | -0.071148 | 0.004854 | 0.171515 | 5 | 0.7422 |
| supplementary | H2_5of6 | B2 | -0.019848 | 0.028257 | -0.070764 | -0.041427 | 0.003526 | -0.107465 | -0.066100 | -0.042544 | 0.162884 | 3 | 0.8367 |
| policy | P_A1 | H1_252_3_WF | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.044597 | 0.007438 | -0.036821 | 0.008304 | -0.000936 | 3 | 0.7391 |

## T4 Regressions (complete months of the walk-forward period)

annual_alpha: 12 x monthly intercept; covariance: Newey-West, Bartlett kernel; finite_sample_factor: n/(n-k), k counting the intercept; gates: months < 36, rank deficiency, condition number > 1e8; interval: asymptotic normal, estimate +/- 1.96 standard errors; lag: 3.

| candidate | model | regressors | months | k | rank | cond | coefficients | HAC standard errors | annual alpha | alpha se | alpha interval | reason |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| H1_252_3 | model_a | intercept, B3 | 108 | 2 | 2 | 1.030e+02 | intercept 0.000545; B3 1.168708 | intercept 0.000772; B3 0.117317 | 0.006535 | 0.009263 | [-0.011619, 0.024690] | n/a |
| H1_252_3 | model_b | intercept, Equity, Treasury, Credit, Real | 108 | 5 | 5 | 1.161e+02 | intercept 0.000582; Equity 0.189867; Treasury 0.246150; Credit -0.197576; Real 0.103741 | intercept 0.001045; Equity 0.062386; Treasury 0.073564; Credit 0.114505; Real 0.043058 | 0.006989 | 0.012538 | [-0.017585, 0.031563] | n/a |
| H1_252_4 | model_a | intercept, B3 | 108 | 2 | 2 | 1.030e+02 | intercept 0.000174; B3 1.253212 | intercept 0.000806; B3 0.120678 | 0.002088 | 0.009668 | [-0.016862, 0.021038] | n/a |
| H1_252_4 | model_b | intercept, Equity, Treasury, Credit, Real | 108 | 5 | 5 | 1.161e+02 | intercept 0.000164; Equity 0.200938; Treasury 0.274283; Credit -0.142301; Real 0.080820 | intercept 0.000997; Equity 0.067439; Treasury 0.075216; Credit 0.117886; Real 0.034122 | 0.001973 | 0.011962 | [-0.021473, 0.025419] | n/a |
| H1_126_3 | model_a | intercept, B3 | 108 | 2 | 2 | 1.030e+02 | intercept 0.000788; B3 1.379099 | intercept 0.001313; B3 0.158108 | 0.009457 | 0.015751 | [-0.021416, 0.040330] | n/a |
| H1_126_3 | model_b | intercept, Equity, Treasury, Credit, Real | 108 | 5 | 5 | 1.161e+02 | intercept 0.000815; Equity 0.135733; Treasury 0.136255; Credit 0.072100; Real 0.158117 | intercept 0.001368; Equity 0.084792; Treasury 0.109749; Credit 0.191602; Real 0.029909 | 0.009783 | 0.016417 | [-0.022393, 0.041960] | n/a |
| H1_126_4 | model_a | intercept, B3 | 108 | 2 | 2 | 1.030e+02 | intercept 0.000138; B3 1.447477 | intercept 0.001337; B3 0.168910 | 0.001658 | 0.016048 | [-0.029797, 0.033113] | n/a |
| H1_126_4 | model_b | intercept, Equity, Treasury, Credit, Real | 108 | 5 | 5 | 1.161e+02 | intercept 0.000126; Equity 0.177459; Treasury 0.142519; Credit 0.047076; Real 0.138879 | intercept 0.001366; Equity 0.089550; Treasury 0.122722; Credit 0.224034; Real 0.034122 | 0.001515 | 0.016393 | [-0.030616, 0.033645] | n/a |
| H2_4of6 | model_a | intercept, H1_252_3 | 108 | 2 | 2 | 7.257e+01 | intercept 0.000492; H1_252_3 0.682846 | intercept 0.000653; H1_252_3 0.062010 | 0.005901 | 0.007835 | [-0.009455, 0.021257] | n/a |
| H2_4of6 | model_b | intercept, Equity, Treasury, Credit, Real | 108 | 5 | 5 | 1.161e+02 | intercept 0.000894; Equity 0.117366; Treasury 0.135101; Credit -0.136595; Real 0.112262 | intercept 0.000949; Equity 0.065715; Treasury 0.066155; Credit 0.103997; Real 0.037244 | 0.010724 | 0.011382 | [-0.011586, 0.033033] | n/a |
| H2_5of6 | model_a | intercept, H1_252_3 | 108 | 2 | 2 | 7.257e+01 | intercept -0.000473; H1_252_3 0.331586 | intercept 0.000544; H1_252_3 0.047698 | -0.005677 | 0.006527 | [-0.018470, 0.007116] | n/a |
| H2_5of6 | model_b | intercept, Equity, Treasury, Credit, Real | 108 | 5 | 5 | 1.161e+02 | intercept -0.000234; Equity 0.046436; Treasury 0.033377; Credit -0.030062; Real 0.046653 | intercept 0.000669; Equity 0.048267; Treasury 0.044351; Credit 0.090601; Real 0.021471 | -0.002814 | 0.008028 | [-0.018548, 0.012921] | n/a |
| P_A1 | model_a | intercept, H1_252_3_WF | 108 | 2 | 2 | 7.278e+01 | intercept 0.000314; H1_252_3_WF 0.933718 | intercept 0.001207; H1_252_3_WF 0.078485 | 0.003766 | 0.014490 | [-0.024635, 0.032166] | n/a |
| P_A1 | model_b | intercept, Equity, Treasury, Credit, Real | 108 | 5 | 5 | 1.161e+02 | intercept 0.000616; Equity 0.154241; Treasury 0.144105; Credit 0.040260; Real 0.138890 | intercept 0.001305; Equity 0.074269; Treasury 0.111114; Credit 0.196671; Real 0.049602 | 0.007397 | 0.015660 | [-0.023297, 0.038092] | n/a |

## T5 P_A1 selection log

| year | selection date | validation segment | decisions | returns | U H1_252_3 | U H1_252_4 | U H1_126_3 | U H1_126_4 | best U | close set | chosen | fallback | warning | frequency H1_252_3 | frequency H1_252_4 | frequency H1_126_3 | frequency H1_126_4 | fallback replicates |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2014 | 2013-12-31 | 2011-12-30 to 2013-12-31 | 24 | 502 | 0.075957 | 0.066890 | 0.058536 | 0.063058 | 0.075957 | H1_252_3 | H1_252_3 | false | n/a | 0.696 | 0.062 | 0.141 | 0.101 | 0 |
| 2015 | 2014-12-31 | 2012-12-31 to 2014-12-31 | 24 | 504 | 0.063040 | 0.053698 | 0.052555 | 0.050461 | 0.063040 | H1_252_3 | H1_252_3 | false | n/a | 0.698 | 0.061 | 0.196 | 0.045 | 0 |
| 2016 | 2015-12-31 | 2013-12-31 to 2015-12-31 | 24 | 504 | 0.029785 | 0.017476 | -0.019554 | -0.019143 | 0.029785 | H1_252_3 | H1_252_3 | false | n/a | 0.978 | 0.003 | 0.013 | 0.006 | 0 |
| 2017 | 2016-12-30 | 2014-12-31 to 2016-12-30 | 24 | 504 | -0.005610 | -0.011230 | -0.005318 | -0.024343 | -0.005318 | H1_252_3, H1_126_3 | H1_252_3 | false | n/a | 0.430 | 0.054 | 0.511 | 0.005 | 0 |
| 2018 | 2017-12-29 | 2015-12-31 to 2017-12-29 | 24 | 503 | 0.026370 | 0.042412 | 0.084992 | 0.065093 | 0.084992 | H1_126_3 | H1_126_3 | false | n/a | 0.001 | 0.016 | 0.970 | 0.013 | 0 |
| 2019 | 2018-12-31 | 2016-12-30 to 2018-12-31 | 24 | 502 | -0.013757 | 0.006099 | 0.026336 | 0.023914 | 0.026336 | H1_126_3 | H1_126_3 | false | n/a | 0.003 | 0.221 | 0.503 | 0.273 | 0 |
| 2020 | 2019-12-31 | 2017-12-29 to 2019-12-31 | 24 | 503 | -0.013013 | -0.000001 | 0.013912 | 0.007241 | 0.013912 | H1_126_3 | H1_126_3 | false | n/a | 0.036 | 0.275 | 0.568 | 0.121 | 0 |
| 2021 | 2020-12-31 | 2018-12-31 to 2020-12-31 | 24 | 505 | 0.060309 | 0.064500 | 0.033947 | 0.027433 | 0.064500 | H1_252_4 | H1_252_4 | false | n/a | 0.200 | 0.435 | 0.236 | 0.129 | 0 |
| 2022 | 2021-12-31 | 2019-12-31 to 2021-12-31 | 24 | 505 | 0.034866 | 0.034626 | 0.032705 | 0.029017 | 0.034866 | H1_252_3, H1_252_4 | H1_252_3 | false | n/a | 0.233 | 0.259 | 0.259 | 0.249 | 0 |

## T6 Disclosures

- All inferential figures are exploratory on familiar history, and the Holm adjustment does not restore independence (protocol line 163).
- The years 2014 to 2022 were the research period, and the project owner's prior exposure to them is non-zero and unquantified (G0).
- Each statistic is conditional on the model already selected (protocol line 167).
- The window excludes most of the 2008 crisis (protocol line 141).
- The data limitations recorded in D016 to D020 apply.
- Costs are modeled at 10 basis points per side.
- The walk-forward comparison with the continuous accounts differs from P_A1 by the start state: P_A1 and its comparator start in cash at 2013-12-31 (P2).
- Statistical non-significance does not establish the absence of an effect (protocol line 163).
- The results do not establish an investable track record.
