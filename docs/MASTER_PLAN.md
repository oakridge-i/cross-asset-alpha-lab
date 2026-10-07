# Research Plan: AAPL Completion and Cross-Asset Alpha Lab

Prepared on 5 October 2026; historical status updated on 6 October 2026. At that planning date, AAPL A0–A5 were complete and the new project was at the planning stage, before N0. This English edition preserves the original plan and preliminary assumptions; it is not a current implementation report. [STATUS.md](../STATUS.md) records current N1 status. [RESEARCH_PROTOCOL.md](../RESEARCH_PROTOCOL.md) governs final research decisions and supersedes the preliminary historical boundaries below. See [Documentation edition](DOCUMENTATION_EDITION.md) for editorial provenance at baseline `4516269`.

## Historical status and available materials

- AAPL: release v0.6.0, commit 4d69932382af4a7bcaddfb4621f0973ea2d820c2. [PR 3](https://github.com/oakridge-i/aapl-sma-backtest/pull/3) was merged into main on 6 October 2026; merge commit ed4fd39518f1f58ad4065512bec8223443186bf3. Local main in C:\Quantitive\model 1 aapl was synchronized. Branch codex/aapl-final-release and the annotated tag were retained.
- Completed-release working directory: <workspace>\aapl-finalization.
- Final report: docs/final/research_report.md; reproduction: docs/final/reproduction.md; independent review and resolution: docs/final/review.md; execution evidence: docs/final/execution_record.md. These paths refer to the AAPL release.
- Verified: 149 tests; the full search on historical and updated snapshots; matching results from two offline replays; 72 cost/delay scenarios per snapshot; independent reconciliation of 202,320 daily rows. Updated-snapshot history ends on 2026-10-05.
- AAPL conclusion: persuasive alpha was not established. For example, over the updated common period, nested-ensemble CAGR was 4.74%, versus 11.43% for the reference with 50% AAPL. The new project must test incremental value over simple strategies under consistent risk and execution rules.
- This plan and project setup materials were available for the new project. Completed AAPL supplies verified formulas, test cases, configurations, snapshot controls, and reporting for selective transfer. Its close-execution engine is not a completed next-open engine for multiple ETFs.
- At the planning date, the new repository, final RESEARCH_PROTOCOL.md, new data, engine, and experiments had not been created. The historical boundaries below were preliminary; N0 still had to assess the independence of the reserved period.
- Raw AAPL snapshots were retained locally and excluded from the current published tree; exact reproduction of their version requires those input files. Compact derived results were published. Older raw downloads remain in earlier Git history.

Section 3 preserves the original AAPL completion plan as a description of stages already completed. At that historical point, the next work was N0 in a separate project.

## 1. Decision and scope

Complete AAPL as a standalone reproducible research case, then establish Cross-Asset Alpha Lab in a separate repository and transfer verified components selectively. Keep each project's objectives, state, and acceptance criteria in its own repository.

The new project aims to formulate economic hypotheses, build a correct simulation, and test incremental returns after costs and explainable risk factors. Positive alpha is a possible research outcome, not a condition for completion.

Working assumptions: one developer, a second-year student, a standard computer, approximately 8–12 hours per week, and an initial data/infrastructure budget of zero. This is a research software plan. Brokerage integration and trading with real capital are excluded. Schedule estimates are not commitments.

Dependency order:

1. Complete the AAPL validation and publish its report.
2. Fix the new research protocol.
3. Prepare data and validate the engine.
4. Reproduce simple benchmarks.
5. Test a limited set of new hypotheses.
6. Conduct the final historical check once.
7. Produce a research release and begin observing future signals.

Original audit material on 5 October: C:\Quantitive\model 1 aapl, branch feature/m3-overlays, HEAD 694ae618828a7480ff5afeb941498d42832abb34, commit message minor fixes. This is a historical reference point, not the current release. Use completed v0.6.0 identified above for transfers, and inspect its directory state before work.

Older outputs_v6_preview relate to 91e769e and data through 2026-06-10. They were retained as an archive and compared with the corrected calculation in the final report. The earlier 117 tests belonged to the original stage; the completed release passed 149 tests.

## 2. Success criteria

Three separate outcomes:

- Engineering: simulation is reproducible, trades and capital reconcile, and future data do not change past decisions.
- Research: testable hypotheses, substantive benchmarks, a record of all attempts, and explicit uncertainty.
- Economic: a persistent effect after realistic costs that cannot be adequately explained by prespecified benchmarks and factors. This outcome is not guaranteed.

Reports must distinguish positive returns, risk reduction, capture of the established momentum premium, cost savings, and estimated alpha relative to a specific model. All five may be useful but have different meanings.

No target Sharpe is a project acceptance condition. The project may conclude that the available data do not establish a persuasive advantage.

## 3. AAPL completion: bounded scope

The completion task is to establish one credible final research result. New strategy families, expanded parameter grids, and development of a trading application are excluded from this stage.

### A0. Record the baseline — 2–3 hours

- Inspect the branch, HEAD, uncommitted changes, available data snapshot, and configurations.
- Retain identifiers for old results and label them historical.
- Create a register of known limitations with files, impact, and verification methods.
- Fix signals and existing grids; do not change them to improve returns.
- Describe which historical periods have already been studied. They cannot subsequently be called an independent holdout.

Deliverable: BASELINE_AUDIT.md and a baseline manifest.

### A1. Correct material methodological limitations — 10–16 hours

1. **Weight drift and costs.** Calculate trades against actual weights before rebalancing. A price change can require trades to restore previous target weights even when the signal is unchanged. Specify whether bps is a cost per side; moving between two risky assets involves a sale and a purchase. Include cash-ETF costs if it is treated as a tradable asset.
2. **Execution timing.** Explicitly connect signal availability and execution. For the bounded AAPL completion, a simple documented convention is acceptable: signal after close t, execution at the next close t+1, and new-position returns begin after execution. Compare with the old assumption without selecting the more favorable result. A more detailed next-open model belongs to the new project.
3. **State across windows.** Build a continuous simulation of the policy selected across windows, carrying cash and positions. Include transitions to new models and trading costs. Retain independent-window summaries as a separate diagnostic, explicitly distinguished from a continuous account.
4. **Fallback model.** Eliminate the possibility of an early-window fallback selected from later data in the full training period. Fix fallback in advance or select it within the window's available history. A potential path was identified; its effect on the old preview was unestablished.
5. **Consistent metrics.** Use the same definitions of annualized return, Sharpe, cash return, and calendar in every table. Separate an investable cash proxy from a statistical risk-free rate. Align dates for excess-return series.
6. **Historical warm-up.** Check consistent rules for the primary and legacy comparators. Indicators use past data; training returns do not enter evaluation.
7. **Price quality.** Do not substitute ordinary Close for Adj Close without explicit status and corporate-action verification. A missing price must not automatically become an ordinary zero return without explaining why.
8. **Statistical scope.** Label PBO for its applicable grid; do not present DSR as the probability of true alpha. Disclose the incomplete historical attempt log. The proportion of negative bootstrap replicates is not the probability of future loss.

AAPL does not need a universal platform. Corrections must support one final reproducible check.

### A2. Verify financial mechanics — 4–6 hours

Mandatory small scenarios reconciled manually:

- Constant price, no trades: capital is unchanged at a zero cash rate.
- One entry and one exit: costs occur on each side and on the correct day.
- A 50/50 portfolio with a stock-price change: actual weight drifts; rebalancing produces turnover.
- Model change at year-end: positions and capital persist; the transition is one sequence of trades.
- A signal after close: the new position earns no return before eligible execution.
- Changed future prices: past signals, models, and orders remain unchanged.
- Fallback model: force a case with no candidates passing filters.
- One return series across reports: Sharpe, CAGR, and drawdown agree within specified rounding.

Then run the complete existing test suite. Checks compare economic invariants and independent manual calculations rather than merely repeating implementation formulas.

### A3. One control recalculation — 4–6 hours of active work

First use the old snapshot through 2026-06-10 to separate methodological corrections from new data. After reconciliation, run the updated snapshot separately and record its date and the status of previously inspected periods.

Comparisons:

- AAPL buy-and-hold.
- Prespecified 25/75, 50/50, and 75/25 AAPL/cash-instrument mixes with common rebalancing frequency.
- Fixed SMA 20/100.
- Selected v3 and selected v6.
- Continuous nested walk-forward policy.

All use the same calendar, costs, execution, cash returns, and warm-up rules. Main cost scenario: 10 bps per side of turnover; stress: 20 bps; retain 0 and 50 bps as diagnostic extremes. These are research assumptions, not measured brokerage fees.

Show an "old calculation → corrected calculation" table and explain material differences. A data update does not automatically create a new independent test. If there is no persuasive effect, complete the research with that result.

### A4. Produce the final research report — 4–6 hours

The report must include:

1. The original question and a brief development history.
2. Data, dates, sources, corporate actions, and limitations.
3. A formal description of strategy and execution.
4. What was selected from data and which periods had already been used.
5. A final table after costs and comparisons at comparable risk.
6. Charts of equity, drawdown, risky allocation, and turnover.
7. Period results and cost/delay sensitivity.
8. Statistical uncertainty and selection limitations.
9. Negative findings and reasons to reject the hypothesis, if applicable.
10. Unambiguous reproduction commands.

### A5. Close the release — 2–3 hours

- Check reproducibility in a clean environment with pinned dependencies.
- Update README with one recommended run, the current table, limitations, and a report link.
- Retain compact configurations, the report, and manifests; do not expand Git with every intermediate download. Check raw-data redistribution terms separately.
- Update the changelog and prepare final commits and publication to the agreed branch under the applicable release authorization; do not force-push or merge automatically on the basis of earlier authorization for an ordinary push.
- Choose the release name after inspecting existing tags; mark the research complete.

**AAPL Definition of Done:** a clean reproducible run, corrected financial mechanics, an updated final report, explicit material limitations, and no added indicators. The result must be understandable from the repository documentation.

## 4. New project: Cross-Asset Alpha Lab

### 4.1. Primary question

Can liquid exchange-traded instruments produce persistent incremental returns over simple diversified and trend strategies after accounting for risk, costs, and execution delay?

First-release scope: long-only ETFs, daily data, month-end signals, execution at the next available open, USD base currency, no leverage or short selling. Define the cash allocation explicitly. If available data cannot establish realistic open execution, disclose it as an assumption and test a delay; do not promise an exact execution price.

This direction uses existing research skills and broadens market coverage while avoiding tick-data costs, futures-roll modeling, and stock-borrow modeling. Established trend/momentum premiums serve as benchmarks. Reproducing them does not itself discover new alpha.

### 4.2. Initial universe

Preliminary data-verification list, not an investment recommendation:

| Group | Candidates | Purpose |
|---|---|---|
| Equity | SPY, EFA, EEM | US, developed markets outside the US, emerging markets |
| Government bonds | IEF, TLT | Different interest-rate sensitivities |
| Corporate bonds | LQD, HYG | Different interest-rate and credit-risk composition |
| Real assets | GLD, DBC | Gold and broad commodity exposure |
| Cash instrument | BIL | An investable cash allocation |

Approve the final list based on asset-class coverage, availability, and data quality before reviewing signal results. Check issuer mandates, histories, inception dates, and fund changes. ETF history begins with actual existence; earlier index data form a separate hypothetical experiment and must not be silently spliced into ETF history.

This fixed set of current ETFs remains a sample selected today. It is not a survivorship-bias-free study of the full fund market. Do not generalize results to every ETF that has existed. Test robustness using prespecified class exclusions and alternative representatives rather than selecting favorable replacements from returns.

### 4.3. Data and budget

MVP: a local Python project and publicly accessible data, without cloud infrastructure or mandatory paid APIs. yfinance is an acceptable initial adapter, not a quality guarantee. Verify syntax and parameters against official documentation during implementation and pin versions.

Store separately:

- Original OHLCV, dividends, splits, and source metadata.
- Normalized data with units, timezone, and trading calendar.
- Total-return prices for features.
- Execution prices and corporate actions for portfolio accounting.
- Research features with availability timestamps.
- Results of every run.

For execution, prefer unadjusted prices with explicit splits and dividends. Recognize a dividend in portfolio value through an entitlement receivable; the payable date determines cash availability for reinvestment. If payment dates are unavailable, choose and disclose an approximation, and separately assess sensitivity to credit delay. Do not receive dividends through adjusted returns and again through a cash entry.

Quality checks: unique dates, temporal order, gaps, trading sessions, OHLC consistency, anomalous jumps, splits, dividends, no pre-inception history, and cross-source discrepancies on control dates. Do not buy at a stale forward-filled price. Material defects stop calculation or exclude an observation under a predefined rule with a recorded reason.

Consider paid data only to address a specific established gap. Before choosing a provider, separately examine licensing, corporate actions, histories of excluded instruments, cost, and terms of use. Procurement is outside this plan.

### 4.4. Architecture

One repository, one Python package, CLI, and local files. Notebooks may explain results or support one-off analysis; the calculation core belongs in testable modules.

| Component | Responsibility |
|---|---|
| data | Acquisition, calendar, corporate actions, quality control, and snapshots |
| features | Causal features using only information available at the date |
| signals | Scores and signals without their own trade model |
| portfolio | Target positions, constraints, cash allocation |
| execution | Orders, execution prices, costs, actual positions |
| research | Temporal splits, candidate selection, experiment log |
| evaluation | Benchmarks, metrics, statistics, attribution |
| reporting | Reproducible reports from retained results |

Data contracts: observations have a date and availability time; signals have a creation time; orders have an earliest eligible execution time; trades have price, quantity, and costs; portfolios have positions, cash, distributions, and NAV. Calculations must not receive future data through a shared context object.

Order size uses information available when the order is created. An unknown next-open price cannot retrospectively determine an ideal share quantity. Fix rounding, fractional-share, cash-reserve, gap, partial-fill, and insufficient-funds rules in EXECUTION_MODEL.md. One transparent MVP approximation is sufficient if it prohibits negative cash and separately tests sensitivity.

Minimum technology: Python, NumPy/pandas, Parquet, YAML, pytest, a simple CLI, and charts. Pin the environment in a lock file. Add a database when needed; microservices, Kubernetes, distributed queues, and a web interface are unnecessary for the first result.

Transfer AAPL modules individually after validation: configuration interfaces, snapshots and manifests, some signals, verified formulas, and test scenarios. Do not copy the trading engine or pipeline coordination without rechecking contracts. Retain provenance for transferred code. Do not create a shared library for both repositories in advance.

### 4.5. Benchmarks before searching for improvements

- B0: the cash instrument.
- B1: equal-weight risky ETFs with monthly rebalancing.
- B2: inverse historical-volatility weights with fixed concentration limits.
- B3: a simple 12-month trend relative to the cash return, with the same risk and execution constraints as new hypotheses.
- SPY buy-and-hold: a supplementary reference, not the sole criterion for a multi-asset portfolio.

B3 is the primary comparator for new signals. B2 helps identify whether improvement is explained by simple risk management. Report realized risk and cash allocation as well as returns.

Common preliminary constraints: estimate individual-asset volatility over 63 trading days and portfolio covariance over 126 days; maximum 25% NAV in a risky ETF and 50% in a group; total risky weights no greater than 100%; the 10% volatility target only reduces exposure, without leverage. Allocate the remainder to the cash instrument. These are explicit project settings, not estimated optima. If limits leave substantial cash, do not relax them after inspecting results.

Main cost: 10 bps per side; stress: 20 bps; extreme scenario: 50 bps. Separately test a one-session delay. Zero costs are shown only to explain the source of losses. If measured data become available, replace assumptions with calibration and issue a new protocol version.

### 4.6. First research campaign: two hypotheses

**H1. Relative momentum normalized for risk.**

Hypothesis: relative strength persists across market instruments and may add value over simple absolute trend. This is a predictability hypothesis, not an established fact for the selected ETFs.

- Signal: cumulative total return relative to the cash instrument over a window ending 21 trading days ago, divided by historical annualized volatility.
- Two window lengths: 126 and 252 trading days from the signal date; exclude the latest 21 days. The actual return interval therefore contains L−21 days. Fix the definition as a formula in the specification.
- Select top-3 or top-4 instruments with positive signals. Fewer qualifying instruments imply more cash, not a lower threshold.
- Use inverse-volatility weights and common limits; rebalance monthly.
- Four variants in total: two lengths × two set sizes.
- Prespecified primary variant: 252 days, top-3. The others support robustness checks and possible selection only within the training procedure.

**H2. Momentum persistence over time.**

Hypothesis: equal cumulative returns may have different paths, such as gradual movement or one jump. Test whether persistence adds value after accounting for ordinary momentum.

- Use fixed H1 parent: 252 days, top-3.
- Additional condition: positive monthly excess return in at least 4 of the latest 6 completed months.
- Only neighboring check: 5 of 6 months.
- Allocation failing the filter remains in the cash instrument; do not relax the filter dynamically.
- Two variants in total. Do not retrospectively replace the parent with the best H1 variant.
- Compare primarily with the H1 parent to assess whether the effect is explained by reduced exposure and increased cash.

Six configurations in total beyond the benchmarks. Costs, delays, and prespecified ablation checks are diagnostic scenarios, not additional candidates from which to choose the best report. A resulting strategy change is a new attempt and log entry.

Automatic configuration selection is itself a separate researched policy. Record it alongside fixed variants; six counts signal configurations, not the entire history of statistical trials.

After the first campaign, do not automatically add RSI, MACD, dozens of filters, or ML. A new campaign starts with a new economic hypothesis, information source, or clear diagnostic rationale. A new hypothesis cannot reuse the old final test as an independent check.

### 4.7. Research protocol

Before calculating results, register hypotheses, universe, parameters, benchmarks, costs, constraints, temporal boundaries, selection criteria, and rules for rejecting a hypothesis.

Preliminary structure, conditional on sufficient coverage:

- 2008–2013: develop benchmarks and mechanics on historical data; synthetic manual examples are also preferred for debugging.
- 2014–2022: research walk-forward, with each selection using only the past. If the protocol changes after inspecting these windows, they become development.
- 2023–2025: reserved historical check only if results for these specific hypotheses have not already been studied. The period is not entirely unfamiliar: its market events and some assets are already familiar from AAPL.
- 2026: a separately identified recent historical period; its status depends on actual prior inspection. Do not automatically declare it independent.
- After fixing the final model: prospective observation of future signals with immutable records.

If instrument coverage does not support this structure, change boundaries based on data availability before inspecting strategy returns and record the reason. Do not choose dates to favor results. If all history has been used, treat it as exploratory and rely on future data for a genuinely new check.

For yearly walk-forward, fix the configuration before the year begins, with at least five preceding years available. Within that history, use chronological training/validation blocks rather than random shuffling. Estimate normalization parameters and any fitted models only on available history. Future ML labels with overlapping horizons require purging overlapping observations and an explicitly justified temporal gap.

Primary ranking criterion if adaptive selection is needed: one prespecified utility measure on internal validation segments, for example annualized mean excess return − (3/2) × annualized variance. Fix coefficient 3 as a risk-preference assumption rather than optimizing it. For close results, choose the simpler variant under a predefined rule. Always report the fixed primary variant alongside adaptive selection to expose the cost of selection complexity.

Open the final historical test once after freezing the procedure. A negative result does not authorize parameter changes and reuse of the same period as a holdout. Correcting a software error is permitted, but requires a new version, a recorded reason, and disclosure of repeated inspection.

### 4.8. Alpha and robustness assessment

Each candidate's table: CAGR, annualized volatility, Sharpe on aligned excess returns, maximum drawdown, turnover, costs, cash allocation, concentration, number of rebalancing decisions, and annual results.

The main economic question is the utility and return difference relative to B3 under comparable constraints. Additionally estimate regression alpha relative to B3 and a compact model of relevant risk classes. Fix factors, frequency, and standard-error methods before the final test. US equity factors alone must not automatically be treated as an adequate risk model for cross-asset ETFs.

A regression describes performance relative to its chosen model. A positive intercept does not establish universal market inefficiency. Do not include many nearly duplicate factors in a short monthly sample.

Uncertainty: paired block bootstrap preserving strategy/benchmark date alignment; prespecify block lengths, for example 21/63/126 trading days, and show all. Regression errors must account for autocorrelation and heteroskedasticity. Assess uncertainty of a fixed strategy separately from that of the full selection procedure; bootstrapping an already selected series does not rerun the entire search.

Use DSR/PBO as supplementary diagnostics for a clearly identified trial set. Account for configuration correlation and all known attempts. Disclose any inability to reconstruct past manual trials. Daily observations do not turn a short history of infrequent decisions into thousands of independent experiments.

Mandatory ablations: remove risk normalization, remove the persistence filter, compare with simple trend, compare with baseline exposure without selection, and show costs separately. Change one component at a time. Test results excluding each asset class and within predefined calendar blocks. These diagnose effect concentration and must not be used to choose the best subset.

### 4.9. Decisions from results

| Status | Basis | Next step |
|---|---|---|
| Research error | Leakage, incorrect trades, data defects | Correct and revalidate mechanics; suspend return conclusions |
| Hypothesis unsupported | No incremental value, or it disappears under reasonable costs | Record the negative result and close the campaign |
| Insufficient data | Positive estimate, but a wide interval includes no effect | Retain the model and continue observation without fitting it further |
| Useful risk management | Risk improves, but new alpha is unestablished | Present the result as risk management |
| Candidate for further research | Persistent effect after costs, limited concentration, and confirmation on reserved data | Freeze the model, observe prospectively, and seek independent verification |

Do not make Sharpe > 1 or p < 0.05 the sole acceptance threshold. Prespecify the error rate and multiple-hypothesis correction for formal testing; separately define the minimum economically relevant effect. Statistical nonsignificance alone does not establish a zero effect.

### 4.10. Prospective observation

Starts after code, training data, and parameters are fixed. Retain dates, inputs, signals, target positions, intended orders, and subsequent simulated execution. Data corrections must not overwrite an old decision without a trace: preserve the original log and append a corrective entry.

The first 8–12 weeks test acquisition, calendar, calculations, and decision recording. At monthly frequency this represents only a few decisions and does not establish alpha. Longer observation may continue after development ends.

## 5. New-project implementation stages

| Stage | Work | Artifact and exit criterion | Estimated hours |
|---|---|---|---:|
| N0 | Protocol and constraints | RESEARCH_PROTOCOL.md, approved hypotheses, attempt registry | 4–6 |
| N1 | Data and quality control | Snapshot, DATA_CONTRACT.md, coverage and defect report | 10–15 |
| N2 | Portfolio and execution | Validated engine, trade log, manual reconciliation | 16–24 |
| N3 | Benchmarks | Reproducible B0–B3 report | 8–12 |
| N4 | H1 and H2 | Six configurations, causal features, experiment records | 10–15 |
| N5 | Walk-forward and statistics | Complete available selection log, consistent metrics and intervals | 10–15 |
| N6 | Robustness and final test | Report of all assigned scenarios and hypothesis decisions | 12–18 |
| N7 | Documentation and release | README, final report, clean reproduction | 6–10 |
| N8 | Prospective log | Initial signal records and operational-process verification | 4–6 |

New-project estimate: approximately 80–120 hours of core work, with possible additional data/corporate-action work. AAPL: approximately 25–40 hours. Combined estimate: 110–160 hours; at 8–12 hours per week, approximately 3–5 months. Full scope exceeds the initial 6–8-week outline. The prospective-observation calendar runs separately.

## 6. Priorities and scope limits

P0 before any conclusions: data availability timing, corporate actions, correct portfolio accounting, costs, leakage prevention, reproducibility.

P1 for a completed study: benchmarks, attempt log, walk-forward, uncertainty intervals, a consistent report, hypothesis-rejection rules.

P2 after the first release: an alternative data source, additional markets, event features, a compact ML model if data suffice, automated report generation.

Exclude from the first version: deep learning, reinforcement learning, a neural network predicting the next candle's direction, autonomous search across thousands of strategies, HFT, options, futures rolls, leverage, short selling, live trading, and a large interface.

If work falls behind, reduce hypotheses and optional charts. Do not save time by skipping financial invariants or using the test for accelerated tuning.

## 7. Reproducibility and documentation

Every run records run_id, start time, git SHA, uncommitted-change status or patch hash, config hash, data hash, dependency versions, seed, universe, temporal splits, tested models, selected models, quality warnings, signals, trades, positions, NAV, and metrics.

Failed runs remain in the log. Repeating an identical experiment does not create a new independent check. Revising a hypothesis after inspecting results receives a new ID linked to its parent.

Research documents:

- README.md: question, brief result, setup, reproduction.
- RESEARCH_PROTOCOL.md: all research decisions before final evaluation.
- DATA_CONTRACT.md: field semantics, timing, adjustments, missing values.
- EXECUTION_MODEL.md: event order, trades, costs, constraints.
- EXPERIMENT_LOG: machine-readable log with readable documentation.
- DECISIONS.md: decisions and rationale.
- STATUS.md: completed work, current stage, next task.
- FINAL_REPORT.md: results, uncertainty, negative findings.

The first release is ready when another researcher can reproduce the main result from documentation, check several trades manually, and understand the limits of the conclusions.

## 8. Project governance and transfer

Keep AAPL and Cross-Asset Alpha Lab in separate repositories with separate objectives, status records, files, and acceptance criteria. This separation does not erase prior data exposure or establish research independence.

Retain this plan, the AAPL final report, the list of transferable components, and the final AAPL status as transfer evidence. Work in bounded tasks that close a stage or a specific defect, with project state recorded in the repository.

Research scope, hypotheses, and test periods must not expand automatically. A change requires an explicit research decision and a registered attempt; a more favorable test period cannot replace the original one after results are inspected.

## 9. Initial tasks in the historical plan

1. AAPL A0–A5 were complete: retain the release and final report as a completed research case.
2. Use AAPL v0.6.0 for selective transfer and separately verify compliance with the new data and execution contracts.
3. Retain this plan and the AAPL final report as project provenance.
4. Review the source documents, verify directory and data availability, and prepare N0. Do not begin with strategy optimization.
5. Complete N1–N3; proceed to H1/H2 only after validating the basic mechanics.

## 10. Sources and rationale

These project recommendations derive from the AAPL audit and the sources below. The literature supports hypothesis investigation and validation discipline; it does not establish profitability of the six proposed configurations.

1. [Moskowitz, Ooi, Pedersen — Time Series Momentum](https://www.aqr.com/Insights/Research/Journal-Article/Time-Series-Momentum): original trend research across markets. This ETF project is not an exact replication of the futures sample.
2. [Asness, Moskowitz, Pedersen — Value and Momentum Everywhere](https://www.aqr.com/insights/research/journal-article/value-and-momentum-everywhere): premiums and common factors across markets. Separate established momentum from a new contribution.
3. [Bailey, López de Prado — Deflated Sharpe Ratio](https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf): multiple search, return distributions, and trial accounting.
4. [Bailey et al. — Probability of Backtest Overfitting](https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf): conventional validation limitations and selection diagnostics.
5. [Cederburg et al. — On the Performance of Volatility-Managed Portfolios](https://www.lehigh.edu/~xuy219/research/COWY.pdf): the need to test volatility management under realistic sequential selection.
6. [Frazzini, Israel, Moskowitz — Trading Costs of Asset Pricing Anomalies](https://www.aqr.com/insights/research/working-paper/trading-costs-of-asset-pricing-anomalies): implementability depends on trading costs.
7. [yfinance.download — official documentation](https://ranaroussi.github.io/yfinance/reference/api/yfinance.download.html): download and adjustment parameters; explicit settings and versions are required for reproduction.

This document records the research sequence and deliverables; implementation status and results require their own evidence.
