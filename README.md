# Cross-Asset Alpha Lab

An auditable study of whether relative momentum and persistence of returns can improve a simple multi-asset allocation after trading costs and risk controls.

The research is intended to distinguish a useful allocation rule from a result explained by familiar market exposures, favorable execution assumptions, or repeated testing. Its value will depend on evidence against transparent baselines, including the possibility that added complexity has no economic benefit.

**Stage as of 10 October 2026: data preparation, the account and execution engine (N2), the benchmarks (N3), the six H1/H2 configurations (N4) and the walk-forward evaluation (N5) are complete. Results for B0-B3 and REF_SPY are in the [N3 report](docs/n3/N3_REPORT.md); the N4 runs are documented in the [N4 report](docs/n4/N4_REPORT.md). N5 froze its code, ran a registered and repeated campaign, and published the first H1/H2 and adaptive-policy (P_A1) return, risk, utility and comparison figures for the walk-forward period 2014-2022 in the [N5 report](docs/n5/N5_REPORT.md). The six configurations and P_A1 have the status `evaluated_walk_forward`: walk-forward figures exist, and no hypothesis has been decided. The cost and delay scenarios, the reserved historical period and the decisions of protocol section 13 belong to N6.** The approved dataset was released for portfolio-engine development under D020. The repository implements the N1 data pipeline, the N2 engine for positions, cash, orders, costs, splits and distributions, the benchmarks, the six H1/H2 weight providers, the adaptive policy P_A1 and the N5 inference and evaluation report. The N2 engine was exercised with a test weight provider that is not a strategy, and no returns or NAV from that run are published. N3 adds the baselines B0-B3 and REF_SPY, whose results are reported without comparison to any candidate. N4 adds the six H1/H2 runs, whose permitted diagnostics are published without any performance metric. N5 adds the walk-forward metrics, intervals, tests and regressions of the six configurations and P_A1, computed by code frozen before any of these figures existed. All N5 inferential figures are exploratory on familiar history. No positive alpha or investable track record has been established.

## Research design

The proposed strategy uses daily USD data, monthly allocation decisions, long-only ETF positions, and no leverage. Orders are sized from information available at the decision close and modeled for execution at the next open, subject to cash availability and explicit trading costs.

| Exposure | ETFs |
|---|---|
| Equities | SPY, EFA, EEM |
| Government bonds | IEF, TLT |
| Corporate credit | LQD, HYG |
| Gold and commodities | GLD, DBC |
| Treasury-bill allocation | BIL |

Four fixed H1 configurations measure momentum relative to BIL and test the resulting allocation against the absolute-trend benchmark B3. Two H2 configurations test whether persistence across six calendar months adds value to a fixed H1 parent. A separate adaptive selection policy is registered independently. Comparisons, risk limits, cost scenarios, and statistical tests are specified in the [research protocol](RESEARCH_PROTOCOL.md).

The historical schedule uses 2007-2008 for warmup, 2009-2013 for development, and 2014-2022 for walk-forward evaluation. The reserved 2023-2025 period and the separate 2026 period are not established as independent tests: prior exposure to this history is uncertain. A prospective test requires a future model freeze.

## Evidence available today

N1 preserves immutable source snapshots, normalizes prices and corporate actions to as-traded units, reconciles distributions against issuer materials, records corrections with provenance, and supports offline replay.

- The approved vintage, `data/derived/20261006T172442-80ef993493`, covers 4,869 common sessions through 5 October 2026. Calendar QA passed with no reported adjustment breaks.
- EEM's 2008 split and BIL's 2017 reverse split were checked against documents. Distribution checks passed under the documented readiness rule for all ten ETFs after seven issuer-based corrections.
- Recorded offline reconstruction reproduced all 13 files by SHA-256. Input-validation defects identified in review were corrected; the historical verification record is in [STATUS.md](STATUS.md).

These results establish a usable research input under stated limitations. They do not verify every price, establish historical point-in-time availability, or demonstrate strategy returns. The evidence and initial rejection followed by approval are documented in the [N1 report](docs/n1/N1_REPORT.md) and [decisions D012-D020](DECISIONS.md).

N2 adds an engine for accounting and execution, described in [EXECUTION_MODEL.md](EXECUTION_MODEL.md), with seventeen protocol interpretations recorded in [D021](DECISIONS.md) and manual reconciliations in [docs/n2/manual_reconciliation.md](docs/n2/manual_reconciliation.md).

- A registered run and its repeat on the approved vintage (`20261007T140216-1814c4deb7` and `20261007T140236-ff53aee6df`, window 2007-05-31 to 2022-12-30) passed all seven financial invariants and produced identical output file hashes.
- The run used the test provider `invariant_rotation`, which exists only to exercise orders, splits and payouts. It covered the EEM and BIL splits and the single proxy payout, with 187 decisions and 1,870 orders. The [N2 report](docs/n2/N2_REPORT.md) states the counts and limitations.
- The run command is in [docs/REPRODUCIBILITY.md](docs/REPRODUCIBILITY.md).

These results establish that the accounting mechanics hold on real data under the stated interpretations. They say nothing about strategy behavior.

N3 computes the protocol benchmarks B0 (BIL only), B1 (equal weights), B2 (inverse volatility), B3 (absolute trend) and the reference REF_SPY (a single SPY purchase) on the approved vintage, with the interpretations recorded in [D022](DECISIONS.md).

- Registered runs of the five benchmarks (window 2008-12-31 to 2022-12-30, 168 monthly decisions for B0-B3) passed all seven financial invariants, and a report over them verifies those results. A repeat of every run and of the report produced identical output file hashes.
- The [N3 report](docs/n3/N3_REPORT.md) publishes the section 11 metrics for 2009-2022 by period and by year, with weight-construction diagnostics. Realized volatility and cash shares differ across the benchmarks, and the actual weights of B2 and B3 drift above the 25% target cap between decisions.
- The benchmarks are baselines. The report does not compare candidates, does not state which benchmark is better, and computes nothing for H1/H2 or after 2022-12-30. The branch `claude/n3-benchmarks` was merged into `main` on 8 October 2026.

N4 implements the six H1/H2 configurations as weight providers on the approved vintage, with causal signal records and the interpretations recorded in [D023](DECISIONS.md). Its original registered campaign and the D024 correction campaign were completed on `claude/n4-hypotheses`, merged into `main` on 8 October 2026 through PR #1 (merge commit `e7f50f4`). The post-run report-validation correction of D024 is committed, and its replacement campaign and repeats are complete on the corrected source. All seven pairs reproduce, and their output hashes match the original campaign. The retained failed launch and its retry are disclosed in the N4 report.

- One registered run of each configuration (window 2008-12-31 to 2022-12-30, 168 monthly decisions) passed all seven financial invariants, and a report over the six runs accepted them. A repeat of every run and of the report produced identical output file hashes. After N4 the six configurations had the status `computed_not_evaluated`: computed once on the approved vintage, reproduced, and not evaluated (replaced by `evaluated_walk_forward` in N5).
- The [N4 report](docs/n4/N4_REPORT.md) lists the run identifiers and publishes only counts, selection and target-weight aggregates, turnover and a cost ratio. No return, volatility, drawdown, utility or USD-cost figure of H1/H2 is computed or published, and the configurations are not compared with each other or with B0-B3. These metrics were first computed in N5 by code that was frozen beforehand.
- The restriction on viewing the results is procedural. The published aggregates, combined with public prices, permit approximate inference about exposures, and 2014-2022 remains familiar history rather than an independent test.

N5 evaluates the six configurations and the adaptive policy P_A1 on the walk-forward period 2014-2022, with the interpretations, viewing procedure and status rule recorded in [D025](DECISIONS.md). The code was frozen on 10 October 2026 after the full test suite passed and a whole-branch review found no critical or important defect; the registered campaign ran the same day on the branch `claude/n5-evaluation`.

- Thirteen registered runs (the five benchmarks, the six configurations, P_A1 and a fixed H1_252_3 comparator that starts with P_A1 in cash on 2013-12-31), one evaluation report, and a repeat of each: 28 attempts, all completed, with no failure and no rerun after a bug fix. All fourteen repeat pairs reproduce their output file hashes, and the 99 files that N3 or N4 had already frozen are unchanged.
- The [N5 report](docs/n5/N5_REPORT.md) copies the evaluation report without change: the section 11 metrics by period and year, the paired block-bootstrap comparisons with the Holm adjustment over the six-member primary family, annual differences, regressions on the comparator and on four asset-class proxies with Newey-West standard errors, and the P_A1 selection log with stability frequencies. For each comparison the report states the protocol's minimum-effect flags; it states no verdict.
- The six configurations and P_A1 have the status `evaluated_walk_forward`. The status records that walk-forward figures exist; it does not state that any of them is useful or rejected. The decisions of protocol section 13 require the N6 evidence.
- The limits of this evidence are material. The years 2014-2022 were the research period, and the project owner's prior exposure to them is non-zero and unquantified, so the intervals, p-values and Holm adjustment are exploratory rather than confirmatory; DSR and PBO are not computed. Only the main scenario (costs of 10 basis points per side, lag 1) has been run. The reserved period 2023-2025 remains closed.

## What would justify further attention

| Milestone | Evidence required |
|---|---|
| N2: portfolio and execution | Tested accounting, cash constraints, corporate actions, and manual reconciliation (implemented; see [N2 report](docs/n2/N2_REPORT.md)) |
| N3: baselines | Benchmarks B0-B3 and REF_SPY with comparable net returns and a registered, reproduced run (implemented; see [N3 report](docs/n3/N3_REPORT.md)) |
| N4: hypotheses | Six registered configurations with causal signals and a registered, reproduced run for each, with only permitted diagnostics published (original and D024 replacement campaigns complete and merged into `main` through PR #1; see [N4 report](docs/n4/N4_REPORT.md)) |
| N5: walk-forward and statistics | Comparable net returns, full attempt history, risk attribution, and uncertainty (registered campaign complete on `claude/n5-evaluation`; figures published in the [N5 report](docs/n5/N5_REPORT.md); exploratory on familiar history, no hypothesis decided) |
| N6: robustness and reserved historical check | Cost and delay scenarios of protocol section 12, a frozen procedure, one recorded opening, and disclosure of historical familiarity |
| N7-N8: conclusions and prospective observation | A reproducible report, explicit rejection criteria, and receipts for genuinely future observations |

The protocol requires both economic relevance and statistical support, together with robustness across costs, execution delays, asset classes, and years. A negative result is a valid outcome; a favorable backtest alone is insufficient.

## Material limitations

The universe was chosen retrospectively. Yahoo and issuer histories may be revised; `available_at` is a modeling assumption. The seven corrections rely on issuer records without independent confirmation. GLD's no-distribution classification rests on qualified documentary evidence, and issuer evidence does not establish DBC's completeness before 17 December 2007. The distribution tolerance was chosen after inspecting rounding differences. The original Yahoo acquisition used uncommitted code, whose patch hash is retained in the journal.

The walk-forward period 2014-2022 is familiar history rather than an independent test, and prior exposure to it is non-zero and unquantified; the N5 statistics are exploratory and conditional on the models already selected. The cost and delay scenarios of protocol section 12 and the reserved period are not yet evaluated.

Execution remains a research model: settlement, auction fills, liquidity, and real brokerage constraints require further assessment. BIL is a traded ETF; idle USD earns zero in the proposed accounting model. Data rights and redistribution permissions have not been established. Raw market data and issuer captures are excluded from Git.

## Inspect and reproduce

- [Current status and historical checks](STATUS.md)
- [Research protocol](RESEARCH_PROTOCOL.md) and [decision history](DECISIONS.md)
- [N1 data report](docs/n1/N1_REPORT.md), [source evidence](docs/n1/source_evidence.json), and [run record](docs/n1/execution_record.md)
- [N2 execution model](EXECUTION_MODEL.md), [N2 report](docs/n2/N2_REPORT.md), and [manual reconciliations](docs/n2/manual_reconciliation.md)
- [N3 benchmark report](docs/n3/N3_REPORT.md) and [decision D022](DECISIONS.md)
- [N4 hypothesis report](docs/n4/N4_REPORT.md) and [decision D023](DECISIONS.md)
- [N5 evaluation report](docs/n5/N5_REPORT.md), [attempt accounting](docs/n5/ATTEMPT_ACCOUNTING.md) and [decision D025](DECISIONS.md)
- [Environment, replay commands, and reproduction limits](docs/REPRODUCIBILITY.md)
- [Experiment journal](experiments/EXPERIMENT_LOG.jsonl) and [recording rules](experiments/README.md)
- [N0 source assessment](docs/n0/N0_REPORT.md) and [prior-project reuse audit](docs/n0/AAPL_REUSE_AUDIT.md)
- [English documentation edition and historical receipts](docs/DOCUMENTATION_EDITION.md)
- [Historical commit mapping](docs/HISTORY_REWRITE.md)

Code and documentation are licensed under [MIT](LICENSE). That license does not cover market data or issuer materials.
