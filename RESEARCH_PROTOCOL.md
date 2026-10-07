# Cross-Asset Alpha Lab Research Protocol — English edition 1.0-en.1

Research protocol version 1.0, dated 6 October 2026. This English edition is an editorial translation of research protocol 1.0 at baseline `4516269`; the economic rules are unchanged. See [Documentation edition](docs/DOCUMENTATION_EDITION.md) for provenance and hashes. Original N0 status: decisions were fixed before calculating H1/H2 results; technical validation of the data and engine remained pending. This does not establish that the hypotheses were tested or that every technical detail received individual approval. Current implementation status is recorded in [STATUS.md](STATUS.md).

## 1. Research question, scope, and success criteria

Test the incremental value of relative momentum over absolute trend, and of a persistence filter over a fixed momentum parent. Distinguish investment returns, risk reduction, the established momentum premium, cost savings, and alpha relative to a specified model.

One local Python package, a CLI, files, and a testable core; the data budget is zero. USD, long-only ETFs, daily data, monthly decisions, no leverage or short selling. Neural networks, brokerage integration, live trading, a web interface, and cloud infrastructure are outside the MVP. A successful engineering and research outcome may have a negative economic result.

## 2. Universe and provenance

A fixed sample of currently available ETFs; conclusions do not extend to the full historical ETF market. Issuer inception dates differ from the first available prices. The 6 October check is documented in [sources and limitations](docs/n0/N0_REPORT.md) and the [receipt](docs/n0/source_probe.json).

| Constraint group | ETF | Issuer inception | First Yahoo OHLC session |
|---|---|---|---|
| Equity | SPY | 1993-01-22 | 1993-01-29 |
| Equity | EFA | 2001-08-14 | 2001-08-27 |
| Equity | EEM | 2003-04-07 | 2003-04-14 |
| Treasury | IEF | 2002-07-22 | 2002-07-30 |
| Treasury | TLT | 2002-07-22 | 2002-07-30 |
| Credit | LQD | 2002-07-22 | 2002-07-30 |
| Credit | HYG | 2007-04-04 | 2007-04-11 |
| Real | GLD | 2004-11-18 | 2004-11-18 |
| Real | DBC | 2006-02-03 | 2006-02-06 |
| Cash proxy | BIL | 2007-05-25 | 2007-05-30 |

All ten responses reached 2026-10-05; this establishes availability, not full historical certification. The common observed history begins on 2007-05-30. No index history is spliced in before ETF inception. IEF/TLT currently trade on NASDAQ; the other instruments in the receipt trade on NYSE Arca. A common US regular-session calendar is permissible only after N1 reconciliation.

DBC holds commodity futures within the fund. The engine buys DBC shares, not individual futures; internal rolls and expenses are already reflected in the fund price. The index methodology change effective 2025-11-10 is disclosed as a structural change. GLD changed its gold reference in March 2015. No instrument is replaced on the basis of its return performance.

## 3. Data, cash, and timing

The initial N1 adapter is yfinance/Yahoo; alternative issuer sources verify corporate actions. Settings are explicit: interval=1d, auto_adjust=False, back_adjust=False, actions=True, repair=False, keepna=True; the version is pinned when the N1 environment is created. The exclusive request end is 2026-10-06. Historical opening-auction prices, point-in-time data, and price redistribution rights are not guaranteed.

Store original responses separately from normalized OHLCV/actions, total-return series, features, and results. Each observation contains session, currency, timezone, available_at, source, retrieved_at, adjustment_basis, and hash. Historical available_at is a modeling assumption, not a reconstructed Yahoo publication timestamp. Provider corrections receive a separate vintage.

auto_adjust=False does not establish that OHLC are expressed in the share units actually traded at the time: the source may already account for splits. N1 must establish the semantics using EEM 2008 and BIL 2017. Explicit portfolio accounting requires economic prices and quantities on the same basis. To reconstruct as-traded values from a split-adjusted series, multiply price and dividend by the product of subsequent split ratios; convert volume back to the same units only if the source semantics are confirmed. Do not apply a split again to an already consistent adjusted accounting basis. Uncertainty in this conversion blocks N2.

For features, T_i,t is a theoretical total-return index. After validating actions, construct it causally for each session: T_i,t/T_i,t-1 = s_i,t × (C_i,t + D_i,t)/C_i,t-1, where s is new shares / old shares, C is as-traded close, and D is the distribution per new share on the ex-date. Without an event, s=1, D=0. The source must express D on this basis. This is theoretical reinvestment for a feature, not a portfolio cash entry. Retain Adj Close for an independent reconciliation; ordinary Close must not silently substitute for T.

In the portfolio, a split changes quantity without creating wealth. Shares held before the ex-date earn the distribution entitlement; a purchase at the ex-date open does not. The receivable enters NAV on the ex-date; cash enters on the payable date. If a historical payable date is missing, the main disclosed approximation credits cash at the open of the first session no earlier than ex-date + 10 calendar days; sensitivities are +0/+30 calendar days. Independently confirmed actual dates take precedence. Each event is labeled actual/proxy. The H2 filter does not use a future payable date. A future payment date affects cash availability only when the event occurs, not the past signal.

Distributions must not enter NAV a second time through adjusted returns. Fund expenses are already included in the observed price; do not deduct the annual expense ratio again. Taxes, investor withholding, currency conversion, and actual settlement infrastructure are excluded.

BIL is an ETF that is actually purchased, with transaction costs and distributions. Residual USD is separate, non-interest-bearing cash. For Sharpe/utility, the reference is e_t = r_portfolio,t − r_BIL_TR,t; this is a return relative to BIL, not an established risk-free rate. Benchmark B0 has its own tradable NAV and differs from the theoretical BIL reference.

## 4. Calendar and feature eligibility

t is the last regular trading session of the month. The decision time is 18:00 America/New_York, including early-close days; later information is excluded. The scheduled bar must be complete. Execution occurs in the next common eligible regular session at the modeled Open price. For the prospective log, if actual retrieval is late, available_at is the actual timestamp and execution moves to the next open after it; backdating is prohibited.

Signals and risk use only history <=t. Each ETF requires 253 consecutive closes/252 returns, 63 returns for sigma, and 126 for covariance; the same complete warm-up applies to every comparison. H2 requires seven month-end T levels to obtain six complete monthly returns. Incomplete months are excluded.

Do not forward-fill missing values for execution. An unresolved gap in features, OHLC, actions, or valuation stops the common comparable run; the universe must not be reduced arbitrarily. First source dates serve as boundaries, not as gaps to be filled silently. Unresolved N1 defects require a documented decision before signal results. Do not trade at a stale Open. An existing order without an eligible bar is canceled with a recorded reason; a systemic defect in the common history requires research to stop.

## 5. Risk and common weight construction

r_i,d = T_i,d/T_i,d-1 − 1. sigma_i,t = sqrt(252) × sample_std of the latest 63 r_i (ddof=1). Zero, nonnumeric, or incomplete sigma is a quality/eligibility error, not an infinite score.

Sigma_t = 252 × sample_cov of the latest 126 daily excess returns of the nine ETFs relative to BIL (ddof=1). No shrinkage optimization. Check symmetry/PSD; a numerical negative variance below −1e-12 stops calculation, while a value from −1e-12 to 0 is rounded to 0.

For an inverse-volatility set S with m instruments and a predefined slot count K:

q_i = (m/K) × (1/sigma_i) / sum(j in S, 1/sigma_j).

An empty S implies zero risky weights. Unused slots remain in BIL; m<K does not increase the budget allocated to qualifying instruments. After calculating q_i:

1. v_i = min(q_i, 0.25).
2. If the sum of v within a group >0.50, reduce that group's weights proportionally to 0.50. Do not reallocate the removed weights.
3. V = sqrt(v' Sigma_t v). a = min(1, 0.10/V), with a=1 when V=0. w_i=a v_i.
4. w_BIL = 1 − sum(w_i).

Risky weight <=100%, ETF <=25%, group <=50%; the 10% target only reduces risk. These constraints apply to target weights at the decision time. Actual weights can drift and differ after gaps, costs, and rounding; disclose breaches without introducing daily rebalancing. The cash ETF is exempt from the risky 25%/50% limits. The caps often leave >=25% in the cash allocation for top-3; do not relax limits after reviewing results.

## 6. Benchmarks

All use the same capital, calendar, monthly frequency, warm-up, execution, and costs.

| ID | Exact rule |
|---|---|
| B0 | Target 100% BIL; reinvest distributions/free cash at the monthly decision. |
| B1 | q_i=1/9 for all nine risky ETFs; then apply the common cap/group/vol algorithm. |
| B2 | Inverse volatility of all nine, m=K=9; then apply the common risk algorithm. |
| B3 | Absolute trend: T_i,t/T_i,t-252 ÷ (T_BIL,t/T_BIL,t-252) −1 >0; qualifying instruments receive inverse-volatility weights with K=9; then apply the common risk algorithm. B3 does not exclude the latest 21 days. |
| REF_SPY | Supplementary SPY buy-and-hold, initial costs, and cash/distributions under the common model; cap=25% and the 10% target do not apply. This is an explicitly separate reference without risk controls, not the primary comparator. |

B1 has equal weights before common risk reduction. B3 is H1's primary comparator; B2 identifies the contribution of simple risk management. Publish realized volatility and cash rather than assuming equal risk from identical caps.

## 7. H1 and H2: exactly six configurations

H1's economic rationale: relative strength may persist because information is absorbed gradually and capital flows evolve. This is a testable explanation, not an established cause. Momentum literature from other markets does not establish the effect in this ETF sample. H2 tests whether a more consistent path distinguishes persistent strength from a single jump.

For H1, L in {126,252}, the window runs from t−L to t−21, containing exactly L−21 daily returns:

M_i,t(L) = (T_i,t-21/T_i,t-L) / (T_BIL,t-21/T_BIL,t-L) − 1.

S_i,t(L) = M_i,t(L)/sigma_i,t.

Eligibility is strictly S>0; sort by descending S, breaking exact ties by ticker in ASCII order. Select at most K in {3,4}. Do not fill missing slots with negative scores. Apply inverse volatility and the common risk rules in section 5. Volatility is measured through t even though momentum excludes the latest 21 sessions; this is available information and a predefined rule.

H2 always uses H1_252_3, including its selection, caps, and volatility scaling. For the latest six completed calendar months j:

E_i,j = (T_i,end(j)/T_i,end(j-1)) / (T_BIL,end(j)/T_BIL,end(j-1)) − 1.

F_i(h) = 1[sum(j, 1[E_i,j>0]) >= h], h in {4,5}.

w_i,H2 = w_i,H1_252_3 × F_i(h); the released weight is added to BIL. Do not rerank, select replacement ETFs, redistribute weights, or rescale exposure upward. Month t is included because it is complete by the decision time. E=0 is not positive.

| ID | Parameters | Role and primary comparison |
|---|---|---|
| H1_252_3 | L=252, K=3 | Primary H1; vs B3 |
| H1_252_4 | L=252, K=4 | Neighboring H1; vs B3 |
| H1_126_3 | L=126, K=3 | Neighboring H1; vs B3 |
| H1_126_4 | L=126, K=4 | Neighboring H1; vs B3 |
| H2_4of6 | fixed parent H1_252_3, h=4 | Primary H2; vs parent, with B3 supplementary |
| H2_5of6 | fixed parent H1_252_3, h=5 | Neighboring H2; vs parent, with B3 supplementary |

## 8. Execution: constraints N2 must implement

Initial capital is 100000 USD, with no open positions; NAV includes cash, positions, and receivables. At month-end, create integer target quantities Q_i=floor(0.99 × w_i × NAV_t / C_i,t), including BIL; orders are the difference from actual quantities. The 1% common reserve for costs/gaps is a fixed assumption. Do not size using an Open that is not yet known. A split converts positions and outstanding orders into consistent units; retain fractional residual shares until sale, while new target quantities are integers.

Execution sequence: pre-open events, then sales at Open with costs, then purchases. Sales are limited to held quantities. If cash is insufficient for all original purchases including costs, fill = min(1, available_cash / sum(requested_quantity × Open × (1+c))). Buy floor(fill × requested_quantity) for each ETF; keep the remainder in USD rather than assigning it to a favored ticker. Open limits actual order execution; it does not retrospectively create an ideal target. Cancel any unfilled portion after one open and retain the reason. Sale proceeds are immediately available: this simplifies settlement and does not model an actual cash account/settlement system.

Cost is c × abs(quantity) × Open: main c=0.001 (10 bps per side), including BIL, purchases, sales, and initial entry. The main scenario does not deduct the same costs again through an adverse execution-price adjustment. Sell+buy is two sides. Corporate actions do not themselves incur trading commissions. Slippage/spread are combined in c and are not measured. Cash-constrained partial fills are modeled; order-book depth/liquidity is not. Cash >=0, with a tolerance of 1e-8 USD for numerical residuals; a negative value beyond the tolerance is an error.

A new position earns returns after execution; an existing position carries overnight exposure through Open. The account is not reset at year-end; changing models causes actual trades. There is no forced liquidation on the last date. N2 must produce EXECUTION_MODEL.md and manual reconciliations before/after open, a split, ex/pay dates, a gap, and a two-sided ETF switch. A new economic rule requires a protocol version change, not an undocumented code decision.

## 9. Historical boundaries and prior exposure

On 6 October, prior exposure to H1/H2 results was reported as "Not sure / do not remember." AAPL/SPY/BIL and market events were already familiar. Full point-in-time and behavioral independence of the historical test is unestablished.

| Period | Purpose |
|---|---|
| 2007-05-30–2008-12-31 | Common history and warm-up; not a separate return-evaluation period. |
| 2009-01-01–2013-12-31 | Development: data/engine/benchmarks. First signal at the 2008-12-31 close; execution in the first eligible session of 2009. |
| 2014-01-01–2022-12-31 | Research yearly walk-forward; a protocol change after inspection designates affected history as development. |
| 2023-01-01–2025-12-31 | Reserved historical check with unknown prior exposure; opened once after freeze, not an independent holdout. |
| 2026-01-01–2026-10-05 | Separate recent historical segment with the same independence limitation, an incomplete year. Do not select a model on it. |
| After the final model is actually frozen | Prospective log of new inputs/decisions; the start date has not yet occurred. |

The preliminary start was changed from 2008 to 2009 because of BIL availability and the common warm-up, before reviewing strategy returns. This excludes evaluation of most of the 2008 crisis; the material limitation must not be obscured by splicing in index history.

N1 may inspect prices/actions throughout history, including the reserved period, but must not generate strategy tables, comparisons, rankings, or Sharpe there. Metadata/QA access is recorded in source/quality receipts. Final reserved-period performance remains closed until N6. If a data defect changes boundaries, first document availability and the reason; changes motivated by results are prohibited.

## 10. Separate adaptive policy P_A1

This is a separate policy to be evaluated, rather than a seventh signal configuration. Selection is restricted to the four H1 configurations; H2's parent remains fixed. Always show fixed H1_252_3 alongside it.

For year y>=2014, exactly five preceding calendar years y−5…y−1 are available; the first three provide training context, and the final two form chronological internal validation. Signals are deterministic; there are no additional fitted parameters. Each candidate has one continuous account over the internal two-year segment, starting in cash with full prior warm-up and the same execution/cost rules. The first three years do not enter the validation score. Random shuffling is prohibited.

Utility U = 252 × mean(e_daily) − (3/2) × 252 × sample_var(e_daily), ddof=1. The coefficient 3 is not optimized. Select maximum U on common validation. All candidates with U>=best_U−0.001 are treated as close; the preference order is H1_252_3, H1_252_4, H1_126_3, H1_126_4. This favors the original configuration, a longer window, and a smaller set; it is not an OOS ranking. If finite scores are unavailable for numerical reasons despite eligible data, use fixed fallback H1_252_3 with a warning; defective inputs stop calculation and are not concealed by fallback.

Selection is fixed before the year's first open using the available preceding close. The actual portfolio carries continuously between annual windows. For 2023–2025 simulation, freeze the algorithm before opening the entire test; it may automatically use a completed preceding year as it would in real time, without manual intervention or inspection of intermediate results. Settings are not fitted in advance on the entire reserved period.

## 11. Metrics, minimum effect, and uncertainty

Use identical dates and NAV observation conventions; return r_t=NAV_t/NAV_t-1−1 includes the first actual entry relative to initial NAV. CAGR=(NAV_end/NAV_start)^(252/n_returns)−1; show partial-year total return separately. Vol=sqrt(252) × sample_std(r), Sharpe_BIL=sqrt(252) × mean(e)/sample_std(e). Zero variance yields undefined, not infinity. Drawdown uses the running maximum including initial NAV. One-way turnover=sum(abs(trade_notional))/pretrade_NAV; this is not turnover divided by 2. Show costs in USD and as a fraction of NAV. The table also includes cash+BIL and receivables separately, risky weights, groups, the number of monthly decisions, and annual breakdowns.

Primary effect: DeltaU=U(candidate)−U(comparator). The minimum economically relevant effect is +0.01 utility per year (1 percentage point); this is a project judgment about the value of added complexity, not an estimated optimum. A positive difference in annualized mean excess return is also required. For H1, comparator=B3; for H2, comparator=fixed parent. H2 vs B3/B2 are mandatory supplementary comparisons and cannot replace an unsuccessful parent comparison.

Paired circular block bootstrap on aligned daily candidate/comparator/BIL series; 10000 replicates, seed=20261006, block lengths 21/63/126 sessions. The primary length is 63; show all three. Do not select a favorable length. Resampling common dates preserves joint movements. For DeltaU, the basic 95% CI is [2 DeltaU_hat − Q_0.975(DeltaU*), 2 DeltaU_hat − Q_0.025(DeltaU*)]. The scheduled one-sided p for H0: DeltaU<=0 is (1+count[DeltaU*−DeltaU_hat >= DeltaU_hat])/(10000+1), an approximate centered bootstrap, not an exact finite-sample test.

The family of six fixed DeltaU tests comprises four H1 vs B3 and two H2 vs parent. Apply Holm FWER 5% to the primary p values at length 63; lead conclusions concern H1_252_3 and H2_4of6. A neighboring configuration's result does not establish success for the primary configuration. Conditions and intervals on familiar history remain exploratory; adjustment does not restore independence. Statistical nonsignificance does not establish the absence of an effect.

Regressions use complete monthly returns, separately for WF and reserved; exclude incomplete October 2026. y=R_candidate−R_BIL. Model A: intercept + excess return of the primary comparator (B3 for H1, parent for H2). Model B: intercept + four class proxies. A class proxy is the mean monthly excess total return of instruments in the corresponding Equity/Treasury/Credit/Real group in section 2. Weights/composition are not optimized; these control exposures and are neither exact replications of academic factors nor tradable benchmarks with costs. Estimate A/B separately without duplicating B3 within the four-factor model. OLS, Newey-West HAC, lag=3 months with finite-sample correction. Annual alpha=12×monthly intercept; show 95% intervals and the number of months. Do not form an alpha conclusion with <36 complete months, rank deficiency, or condition number>1e8. Alpha/CIs are supplementary descriptions without a separate unadjusted confirmatory p-value claim. Even a positive intercept does not establish new universal alpha.

A bootstrap of fixed NAV is conditional on the model already selected. For P_A1, separately show annual validation scores, selections, and selection stability: resample only available internal validation using joint blocks of 63, 1000 replicates with seed=20261007, reselect the configuration under the same rule, and calculate selection frequencies. This diagnoses selection uncertainty; it is not a CI for the entire training/execution process. Label a bootstrap of realized P_A1 as conditional; no confirmatory p value is claimed for the full adaptive procedure. DSR/PBO are optional N5 diagnostics, with an explicit trial set and limitations; they do not replace the primary contract.

## 12. Prespecified scenarios

Do not select a winner or change parameters using these scenarios. Repeat the same informational decisions; when account state changes, size new orders causally from the current account. Retain P_A1's main annual selections rather than reselecting under stress.

- Full grid cost {0,10,20,50} bps × execution {next open, one extra session}: eight scenarios for each B0–B3, REF_SPY, the six configurations, and P_A1. Zero explains costs; 50 is an extreme scenario.
- Dividends: missing-pay-date proxy {0,10,30} calendar days, main 10; do not change actual dates. Order reserve {0%,1%,2%}, main 1%. Change one item at a time at main cost/lag.
- H1_252_3 without dividing the score by sigma, with other rules unchanged. Separately, equal weights in the selected set instead of inverse volatility with the score unchanged, to identify sizing effects.
- H2 without the filter = parent; H2 vs a causal exposure-matched parent: reduce the parent's risky weights to the sum of H2 risky weights at the current decision, putting the remainder in BIL. Do not use future realized volatility for sizing.
- H1 vs B3 and B2; identical caps and ex-ante risk rules, with actual risk reported separately. The same B2 result diagnoses performance without selection; it does not become a new candidate.
- Leave-one-class-out for four groups: remove the entire group without relaxing the remaining K/limits; B1/B2/B3 count slots against the original nine so removal does not automatically reallocate the budget. H1 K remains 3/4. A supplementary single-instrument exclusion diagnostic without DBC is also prespecified because of its known methodology change.
- Calendar blocks 2009–2013, 2014–2016, 2017–2019, 2020–2022, reserved 2023–2025, and recent 2026 separately; additionally, each year. Separately disclose periods before/after DBC's 2025-11-10 change; do not choose the break date from a strategy chart.
- Alternative class representatives and a second price source are deferred beyond the MVP until a specific gap is established or a separate decision is made; current robustness covers only this fixed sample. Do not select favorable replacements from results.

## 13. Hypothesis decisions and test opening

Causality or accounting errors, or material unresolved data defects, suspend all economic conclusions. If DeltaU<=0 or the effect disappears at 20 bps/an extra session, the hypothesis is unsupported within this scope. If point-estimate DeltaU>0 but <0.01, the economic value of added complexity is unestablished under the assigned criterion. If DeltaU>=0.01 but the interval is wide and includes 0, evidence is insufficient. Risk reduction without persuasive incremental value is described as risk management.

"Candidate for further research" for a primary fixed configuration requires all of the following: DeltaU>=0.01 and a positive mean excess-return difference in WF and reserved; the primary CI lower bound>0 and Holm p<0.05 in scheduled historical checks; DeltaU>0 at 20 bps plus an extra session; at least 3 of 4 leave-class-out DeltaU>0; a positive annual mean excess-return difference in >=5 of 9 WF years and >=2 of 3 reserved years. Among positive WF annual contributions to the sum of daily candidate−comparator returns, one year's share must be <=50%. A robustness failure is disclosed as effect concentration. These are joint criteria, not a promise of sufficient power from 36 months or proof of independent alpha. Describe alpha relative to the models separately.

N6 opening requires fixed git SHA, protocol/config hashes, data hashes, environment versions, all candidates/policies, selection decisions, QA, and N1–N5 tests. First record the final run_id and started status in the log, then create the entire reserved report once; recent 2026 receives a separate table. Do not change the procedure based on intermediate results. An error correction is permitted with a new version, retention of the old result, and explicit reopening disclosure. A negative result does not authorize a new optimum or a different test period.

## 14. Registry, reproducibility, and completion

Before the first N1 data run, experiments/EXPERIMENT_LOG.jsonl is empty: N0 metadata probes are documented separately and are not strategy-testing attempts. H1/H2 have status registered_not_tested. Rules for all data/strategy/replay/failed runs are in [experiments/README.md](experiments/README.md). Record started first, then completed/failed, without deletion. Errors and changes after inspection receive a parent/reason. Diagnostics are not hidden extra candidates; a strategy change motivated by a diagnostic becomes a new attempt.

N0 does not run a broad search/optimization. N1 DATA_CONTRACT/snapshot/QA, N2 EXECUTION_MODEL/financial invariants, and N3 B0–B3 precede H1/H2. Retain provenance for transfers from AAPL v0.6.0; the old next-close engine does not implement this next-open contract.

Protocol changes receive a new version, date, diff, and reason in DECISIONS.md; previously viewed results do not become independent because the document changed. After N7, actual N8 begins with immutable prospective receipts; the first 8–12 weeks test the process and do not establish alpha from monthly decisions. Historical backfill cannot replace observation of future data.
