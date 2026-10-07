# Material decisions

Entries are retained; a reversal requires a new entry. H1/H2 had no performance results when these decisions were made. This is the [English editorial edition](docs/DOCUMENTATION_EDITION.md); the N0 receipts certify earlier bytes, not this edition. Historical commit identifiers are mapped in [HISTORY_REWRITE.md](docs/HISTORY_REWRITE.md).

## D001 — 2026-10-06: separate project and initial scope

A separate project was created at `<workspace>/cross-asset-alpha-lab`, with a local Git `main` branch and no remote at that time. The initial scope was N0 assessment; N1-N8 remained subsequent stages. Continuing within AAPL was rejected because the projects and execution assumptions differ. AAPL was read as a source without modification. The initial scope did not authorize publication, purchases, or live trading. The repository was subsequently published on 7 October 2026; see STATUS.md for that later event.

## D002 — 2026-10-06: common evaluation start in 2009

The source was available for all ten ETFs through 2026-10-05; the common OHLC start was 2007-05-30, determined by BIL. A full year of BIL warmup was unavailable at the start of 2008. Development was therefore assigned to 2009-2013, walk-forward evaluation to 2014-2022, and warmup to 2007-2008. Alternatives were a mid-2008 start or a spliced cash index. Whole years support the predetermined annual selection schedule; splicing changes the traded instrument. Much of the 2008 crisis is excluded from evaluation, even where shorter features might be available. The change followed availability checks before strategy results.

## D003 — 2026-10-06: historical independence is unestablished

Prior inspection of H1/H2 history could not be recalled with certainty. The 2023-2025 period is reserved for a single historical check; 2026 is reported separately. Neither is called an independent holdout. Assuming untouched history would overstate the evidence. Prospective testing begins only after an actual model freeze; its date is not invented in advance.

## D004 — 2026-10-06: exact signals and risk controls

H1 uses relative geometric wealth against BIL over `t-L...t-21`, divided by `sigma63`, with `L=126/252` and `K=3/4`. H2 uses the fixed parent `H1_252_3` and requires at least 4/6 or 5/6 positive full calendar months. A zero month is not positive; excluded weights remain in BIL. Common controls are 25%/50% caps, `cov126`, and a 10% volatility target that only scales risk downward. Weights are not redistributed after clipping. Renormalizing survivors to 100% was rejected because it conceals the filter's allocation cost and expands risk. The six configurations remain fixed.

## D005 — 2026-10-06: BIL and corporate actions

BIL is purchased and incurs expenses; free USD receives no synthetic BIL return. Features and the statistical reference use theoretical total return, labeled BIL-relative rather than a guaranteed risk-free rate. Yahoo actions omit payable dates. Actual issuer dates take precedence; otherwise use ex-date plus 10 calendar days, with ex+0/30 scenarios reported separately. Receivables enter accounting on ex-date; cash enters only on payment. `auto_adjust=False` does not establish as-traded units. The BIL 1:2 reverse split in 2017 and EEM 3:1 split in 2008 are mandatory N1 controls. Undisclosed immediate credit and double counting adjusted prices plus cash dividends were rejected.

## D006 — 2026-10-06: research execution model

Orders are sized at the close with USD 100,000 initial capital, integer new order quantities, a 1% reserve, and execution at the next open. Sales precede proportionally reduced purchase fills. Cash cannot be negative; residual USD earns 0%. Immediate use of sale proceeds is a disclosed settlement simplification. Base cost is 10 bps one-way for every ETF; the scenario grid is 0/10/20/50 bps by 1/2-session lag. Sizing ideal weights using the future open violates the information contract. The model does not promise auction prices or brokerage execution. Reserves of 0% and 2% are diagnostics, not tuning candidates.

## D007 — 2026-10-06: selection and economic relevance

`P_A1` is separate from the six signals, selects only among the four H1 configurations, and uses rolling five-year history with the last two years for validation. Utility is `U = 252*mean(excess) - 1.5*252*var(excess)`. The near-tie threshold is 0.001; ordering is fixed with the primary H1 first. The minimum economically interesting `DeltaU` is 0.01 per year. Selection by final-period Sharpe or a dynamic H2 parent was rejected because it changes the research question or introduces leakage. Adaptive selection is not treated as an independent trial without disclosure.

## D008 — 2026-10-06: statistics and hypothesis rejection

All six fixed `DeltaU` values are compared with their assigned competitors. The primary bootstrap block is 63 sessions, with 21/126 alternatives, 10,000 repetitions, and Holm adjustment at 5%. Regression alpha uses monthly HAC(3) and two compact specifications; the second includes four asset-class proxies. A conditional bootstrap of the selected NAV does not test the whole selection pipeline. Separate bootstrap selection frequencies for `P_A1` are diagnostic, not confirmatory p-values. A positive intercept alone does not establish new alpha. Short reserved history and prior familiarity limit inference.

## D009 — 2026-10-06: structural fund changes

Issuer materials report a commodity-index methodology change from 2025-11-10 and a DBC managing-owner change in 2015; GLD's reference changed in 2015. DBC stays in the original universe, these events are disclosed, and a single scenario excluding DBC is registered before results. Replacing a fund because its chart is more convenient would add selection. Current mandates were checked; the completeness of every historical mandate transition is not certified.

## D010 — 2026-10-06: rights, reproducibility, and reuse

The yfinance license is not a license to Yahoo data. Personal/research-use wording was verified in the official README; direct access to the full Yahoo terms was unsuccessful. No legal conclusion or redistribution right was established. Raw data are excluded from Git; procurement and publication of data require separate authorization. N0 retained compact metadata receipts and hashes, not the original market-data vintage. N1 must preserve an immutable local snapshot. AAPL formulas, tests, configuration conventions, and hashing patterns were considered for reuse; its next-close engine is unsuitable for this next-open contract. No code had been transferred at this decision.

## D011 — 2026-10-06: byte-level document registration

`.gitattributes` disables automatic line-ending normalization, preserving exact source Markdown copies and protocol SHA-256 values across checkouts. General auto-CRLF conversion would change hashes without changing research decisions. Any subsequent substantive normalization requires a new hash/version; the protocol is not edited to force a hash match.

A staged whitespace check initially flagged CRLF as trailing whitespace. The cause was reproduced; a one-time `cr-at-eol` setting removed those specific findings. The file whitespace attribute permits CRLF while preserving checks for actual trailing spaces and blank lines. Original copies and economic rules were unchanged at that time. The later English edition records new documentation hashes separately.

## D012 — 2026-10-06: reconcile all distributing ETFs and rerun committed code

DATA_CONTRACT prohibits unknown distribution amounts or bases for every ETF. Issuer reconciliation was expanded from unusual BIL events to all distributing funds. Sources were SSGA workbooks for SPY/BIL, iShares product pages for EFA/EEM/IEF/TLT/LQD/HYG, and PHLX 1410-08 and Form 8937 for the EEM 2008 and BIL 2017 splits. Distribution sources declare `amount_basis`: SSGA is `as_traded`, iShares is `current_units`. Current-unit amounts are converted with the same `future_split_factor` as Yahoo. For EEM on 2007-12-24, iShares 0.648931 multiplied by 3 is approximately 1.9468, against Yahoo's as-traded 1.947. Comparing unconverted `source_dividend` mixes bases; treating the resulting EEM differences as errors produces false defects.

At this stage DBC and GLD lacked issuer sources. Invesco returned HTTP 406 to non-browser clients; the code did not bypass that restriction. Both were `unverified_no_issuer_source`.

Evidence run `20261006T103625-5202b05cbc` and reconciliation `20261006T104437-36dd8f9b4a` used uncommitted code. Clean-tree runs `20261006T122017-3048321309` and `20261006T122119-c6bfb5c69b`, on commits `590281e` and `c78a319`, superseded them while retaining them as parents. Reconciliation results can be reproduced from Git and local snapshots.

## D013 — 2026-10-06: distribution amount tolerance

Tolerance is USD 0.0005 per share in as-traded units, multiplied by `max(1, future_split_factor)`. Yahoo rounds dividends to 0.001 in either as-traded units (BIL) or post-split units (EEM); the as-traded rounding bound therefore grows with the factor. The tolerance was chosen after observing BIL 2009 and EEM rounding discrepancies. Its justification is source precision, rather than the reconciliation outcome. Materiality in bps is reported by ticker and event so small discrepancies remain visible. Exact equality would label every rounding difference a defect; a relative tolerance could miss errors in small BIL payments. The tolerance did not change after run `20261006T122119-c6bfb5c69b`.

## D014 — 2026-10-06: proposed N1 readiness verdict

Proposed verdict: data not ready for N2. Technical reproducibility, calendar completeness, and the EEM 2008/BIL 2017 split bases were confirmed. Distributions were confirmed only for EFA, EEM, and IEF. Unresolved items were Yahoo's missing HYG/LQD/TLT distributions on 2012-11-01; BIL on 2022-03-01 (Yahoo 0.022, SSGA 0); discrepancies below 0.1 bps for SPY 2021-12-17, BIL 2022-09-01, and HYG 2023-12-14; and absent issuer sources for DBC/GLD. Details and options are in [N1_REPORT.md](docs/n1/N1_REPORT.md). This was a proposed verdict, subject to a separate approval entry.

## D015 — 2026-10-06: initial N1 verdict approved

D014 was approved unchanged: data not ready for N2. The readiness rule preceded reconciliation; the five unresolved categories did not satisfy it. The protocol forbids relaxing that rule after inspecting results. Final review found no errors in as-traded calculations, total return, snapshots, journaling, or reconciliation. Replay `20261006T131812-09887a01da` on `977eaf6`, following corrections, reported `replay_equal=true`.

Resolution required choosing an authoritative source for 2012-11-01 and BIL 2022-03-01, deciding how to handle discrepancies below 0.1 bps, and obtaining DBC history and GLD documentation. Corrections would create a separate derived vintage with evidence, preserving the source snapshot. The alternative of approval with disclosure alone was rejected because DATA_CONTRACT prohibits unknown distribution amounts.

## D016 — 2026-10-06: issuer authority and three correction rules

The research owner approved issuer records as authoritative for events outside D013's Yahoo tolerance on 6 October 2026. Rules: add `issuer_only` events using issuer as-traded amounts; replace `amount_mismatch` amounts; remove `yahoo_only` events only where the issuer explicitly records zero on that ex-date, otherwise retain an unresolved status. Matched events retain Yahoo amounts. A separate vintage stores `corrections.json` with event-level sources and normalized columns `dividend_basis` and `dividend_correction_source`; `source_dividend` stays unchanged. The original Yahoo snapshot, prices, splits, and other rows are preserved. Corrections to matched events, unknown dates, or inconsistent `yahoo_amount` values are rejected.

Alternatives were Yahoo authority, which retains missing monthly payments and a BIL payment not confirmed by the issuer, or accepting sub-0.1-bps discrepancies without a source-selection rule. Seven events changed: add HYG/LQD/TLT on 2012-11-01; replace SPY 2021-12-17, BIL 2022-09-01, HYG 2023-12-14; remove BIL 2022-03-01. Theoretical total return changes from each correction date, with cutoff differences from -0.025% to +0.55%. Causes of the Yahoo errors are unknown. The rule uses no strategy results.

Corrected rows retain `available_at=18:00 America/New_York` on ex-date under the same `historical_model_assumption`. Issuer amounts obtained in October 2026 may be revised history rather than contemporaneously announced values. Distribution amounts are declared no later than ex-date, but that fact does not prove the retrieved values were available then. A pipeline relying on Yahoo at the time would have observed the uncorrected values.

## D017 — 2026-10-06: local browser capture of DBC issuer history

Invesco returns HTTP 406 to non-browser clients; no protection bypass was added to the code. Acquisition was authorized on 6 October 2026. A `fetch()` request in the issuer page's browser context retrieved the file, which was saved unchanged. SHA-256 `7337eeb71802061102d85c051178c059507b8c07a75fea7a9718e775f374ae41` was computed in the browser and verified on disk. `data/manual/dbc-invesco-distribution.json` and its capture metadata (URL, page, time, and method) are local and excluded from Git. Source type `invesco_json` reads that file relative to the project root without network access. A declared-hash mismatch fails evidence acquisition and preserves the partial snapshot.

Alternatives were annual reports, requiring more manual work with different reporting units, or leaving DBC unverified and blocking N2. DBC became confirmed, with all 8 events matched. This is one source and one capture. Issuer history starts on 2007-12-17, so completeness before that date is unproven. Redistribution rights are unestablished.

## D018 — 2026-10-06: basis for GLD's no-distribution classification

No issuer statement explicitly saying that distributions have never occurred was found. `confirmed_no_distributions` rests on the SPDR Gold Trust prospectus, page 9 (shareholders do not receive dividends) and page 30 (distributions are provided for where excess cash over 12 months exceeds USD 0.01 per share, or the trust terminates and liquidates); the GLD FAQ on ssga.com, page 3 (proceeds from gold sales are not distributed, in a Form 1099-B explanation about small gold sales to pay expenses); zero Yahoo events in the window; and the trust's continued operation, which was not independently documented. The FAQ statement concerns those sale proceeds, rather than every possible shareholder distribution. Statements and pages are recorded in evidence and `docs/n1/source_evidence.json`. A `document` source stores `no_distributions`, `statements`, and `basis`; classification requires zero Yahoo events, otherwise the status is unresolved.

Leaving GLD unverified would block N2 despite neither the documents nor Yahoo showing distributions. The adopted basis remains no stronger than the evidence above, and the N1 report discloses it. SEC EDGAR was not used because it requires a personal contact User-Agent. The `notes` field in `configs/n1_evidence.json` overstates the documentary basis. That configuration was retained because its hash is registered in the evidence run; this decision and N1_REPORT supply the qualified interpretation.

## D019 — 2026-10-06: proposed readiness after resolving blockers

The unchanged readiness rule from D014/D015 requires both splits to be confirmed and every ETF to have `confirmed` or `confirmed_no_distributions` status on the corrected vintage. EEM 2008 and BIL 2017 were confirmed with unchanged document hashes. On `data/derived/20261006T172442-80ef993493`, SPY/EFA/EEM/IEF/TLT/LQD/HYG/BIL/DBC were confirmed and GLD was `confirmed_no_distributions`. QA reported `technical_pass=true` with 4,869/4,869 sessions; replay `20261006T172504-6b932ef79b` reported equality.

Approval was proposed only for that vintage with its `corrections.json`, disclosing D018's GLD basis, D017's pre-2007-12-17 DBC coverage gap, D016's seven corrections, no independent confirmation of corrected events, and the existing limitations: non-point-in-time history, data rights, D013 tolerance, and dirty-tree Yahoo acquisition. The earlier derived snapshot `20261006T122144-73228a71eb` is not reproduced by current code because its schema changed; its exact replay is recorded in `20261006T131812-09887a01da` on `977eaf6`. It is not approved for N2.

At entry creation this verdict was proposed, pending approval. Tolerance, thresholds, and reconciliation code did not change during blocker resolution. Requiring a second source for the seven corrections and DBC was considered beyond the existing readiness rule. D020 subsequently approved the proposal.

## D020 — 2026-10-07: corrected vintage approved for N2

D019 was approved without changing its conditions: only `data/derived/20261006T172442-80ef993493`, including its `corrections.json`, is ready for N2. D016-D019 limitations remain and must be disclosed in N2 reports. The D014 readiness rule is satisfied. The [initial review](docs/reviews/2026-10-06-n1-review.md), R1-R4, and [follow-up review](docs/reviews/2026-10-07-n1-rereview.md), RR1-RR2, identified input-validation defects, rather than errors in the final vintage. Findings were addressed with regression tests on commits `6e33721`, `5a8eac5`, and `591352a`. Review of the RR1-RR2 fixes reported no Critical/Important findings. On `591352a`, 149 tests passed and replay `20261007T064823-b7b806e0ce` reported `replay_equal=true`.

Requiring independent sources for the seven corrected events and DBC before N2 was rejected because D014 does not require them. Tightening the rule after results is no more justified than relaxing it; missing independent confirmation remains disclosed. N2 may proceed on the approved vintage. A new snapshot or correction requires fresh reconciliation, QA, and a separate decision.
