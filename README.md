# Cross-Asset Alpha Lab

An auditable study of whether relative momentum and persistence of returns can improve a simple multi-asset allocation after trading costs and risk controls.

The research is intended to distinguish a useful allocation rule from a result explained by familiar market exposures, favorable execution assumptions, or repeated testing. Its value will depend on evidence against transparent baselines, including the possibility that added complexity has no economic benefit.

**Stage as of 7 October 2026: data preparation complete; strategy performance untested.** The approved dataset is ready for portfolio-engine development under D020. The `main` branch implements the N1 data pipeline; it contains no portfolio engine, strategy backtest, or H1/H2 performance results. No positive alpha or investable track record has been established.

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

## What would justify further attention

| Milestone | Evidence required |
|---|---|
| N2: portfolio and execution | Tested accounting, cash constraints, corporate actions, and manual reconciliation |
| N3-N5: baselines and hypotheses | Comparable net returns, full attempt history, risk attribution, uncertainty, and cost/delay robustness |
| N6: reserved historical check | Frozen procedure, one recorded opening, and disclosure of historical familiarity |
| N7-N8: conclusions and prospective observation | A reproducible report, explicit rejection criteria, and receipts for genuinely future observations |

The protocol requires both economic relevance and statistical support, together with robustness across costs, execution delays, asset classes, and years. A negative result is a valid outcome; a favorable backtest alone is insufficient.

## Material limitations

The universe was chosen retrospectively. Yahoo and issuer histories may be revised; `available_at` is a modeling assumption. The seven corrections rely on issuer records without independent confirmation. GLD's no-distribution classification rests on qualified documentary evidence, and issuer evidence does not establish DBC's completeness before 17 December 2007. The distribution tolerance was chosen after inspecting rounding differences. The original Yahoo acquisition used uncommitted code, whose patch hash is retained in the journal.

Execution remains a research model: settlement, auction fills, liquidity, and real brokerage constraints require further assessment. BIL is a traded ETF; idle USD earns zero in the proposed accounting model. Data rights and redistribution permissions have not been established. Raw market data and issuer captures are excluded from Git.

## Inspect and reproduce

- [Current status and historical checks](STATUS.md)
- [Research protocol](RESEARCH_PROTOCOL.md) and [decision history](DECISIONS.md)
- [N1 data report](docs/n1/N1_REPORT.md), [source evidence](docs/n1/source_evidence.json), and [run record](docs/n1/execution_record.md)
- [Environment, replay commands, and reproduction limits](docs/REPRODUCIBILITY.md)
- [Experiment journal](experiments/EXPERIMENT_LOG.jsonl) and [recording rules](experiments/README.md)
- [N0 source assessment](docs/n0/N0_REPORT.md) and [prior-project reuse audit](docs/n0/AAPL_REUSE_AUDIT.md)
- [English documentation edition and historical receipts](docs/DOCUMENTATION_EDITION.md)
- [Historical commit mapping](docs/HISTORY_REWRITE.md)

Code and documentation are licensed under [MIT](LICENSE). That license does not cover market data or issuer materials.
