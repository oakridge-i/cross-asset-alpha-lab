# N0 report: feasibility and research specification

6 October 2026, Europe/Moscow. N0 assessed feasibility with a zero data budget and converted the general plan into a protocol before strategy results. H1/H2 returns, model selection and optimization were not run. This report records the state at N0; subsequent data validation and closure are documented in [N1_REPORT.md](../n1/N1_REPORT.md) and [STATUS.md](../../STATUS.md).

## Work completed

The source brief, master plan, setup specification and final AAPL documents were reviewed. A separate local repository was created with the required documents and an empty experiment register. Copies of the original brief, setup and plan were preserved, and the original repository instructions were copied exactly. The protocol specifies formulas, weights, cash treatment, timing, selection and standards for conclusions so that implementation cannot choose economic assumptions after observing results.

N0 produced a research specification and a focused source-quality assessment. The production Python package and stages N1–N8 had not been implemented at this point. A programming implementation plan remained a requirement for the next stage. The English edition and treatment of historical receipts are described in [DOCUMENTATION_EDITION.md](../DOCUMENTATION_EDITION.md).

## Sources and scope

The initial probe queried query1.finance.yahoo.com/v8/finance/chart directly, once per ETF, for daily data from 1990 through the exclusive end date 2026-10-06, with div/splits/capitalGains events. The last observed session was 2026-10-05 for every ETF. All initial responses were HTTP 200 and included Adj Close, USD and America/New_York. Returned rows contained no duplicate timestamps or nonnumeric/nonpositive OHLC values. These checks did not establish completeness of sessions between returned rows, market accuracy, volume accuracy or the full event history. The receipt is [source_probe.json](source_probe.json), with executable check [probe_sources.py](probe_sources.py). The repeated, extended receipt [source_probe_extended.json](source_probe_extended.json) adds OHLC relationships, volume fields, date ordering and annual action counts.

| ETF | First OHLC | Rows in initial response | Dividend events | Split events |
|---|---|---:|---:|---:|
| SPY | 1993-01-29 | 8478 | 136 | 0 |
| EFA | 2001-08-27 | 6313 | 47 | 1 |
| EEM | 2003-04-14 | 5907 | 47 | 2 |
| IEF | 2002-07-30 | 6085 | 291 | 0 |
| TLT | 2002-07-30 | 6085 | 289 | 0 |
| LQD | 2002-07-30 | 6085 | 290 | 0 |
| HYG | 2007-04-11 | 4903 | 233 | 0 |
| GLD | 2004-11-18 | 5503 | 0 | 0 |
| DBC | 2006-02-06 | 5198 | 9 | 0 |
| BIL | 2007-05-30 | 4869 | 128 | 1 |

The grain is one row per ticker/session, with events in a separate stream. Distribution counts do not establish completeness. BIL's sparse 128 events particularly required comparison with issuer distribution history and zero-payment months. Monthly distribution frequency was not interpreted as requiring a nonzero event every month.

The extended repeat exited with code 0. All ten series had 0 ordering, duplicate, positivity or Low<=Open/Close<=High violations; volume was populated and nonnegative. Their common intersection contained 4869 observed sessions. There were 402 prior returns at 2008-12-31, exceeding the required 252. BIL had no nonzero dividend events in 2010/2012–2015/2021; the source had not yet been reconciled with issuer zero payments. These years were not automatically classified as data errors. No exchange-calendar check was performed; valid OHLC in returned rows did not prove that sessions were complete.

The common start of 2007-05-30 constrains the annual warm-up. Full development starts in 2009, providing five prior complete years for yearly 2014 selection. This decision was based on source coverage rather than returns. The revised protocol retains the preliminary WF 2014–2022 and reserved 2023–2025 periods. The owner's answer about prior inspection, translated as "Unsure / do not remember", leaves exposure unknown; the reserved period is not described as an independent holdout.

## Issuer evidence

Current asset classes, mandates and inception dates were read from primary sources. Issuer performance figures were not used to select ETFs. These were current webpages rather than a complete archive of historical mandates.

- [SPY — SSGA](https://www.ssga.com/us/en/individual/etfs/state-street-spdr-sp-500-etf-trust-spy): S&P 500; inception 1993-01-22.
- [EFA — iShares](https://www.ishares.com/us/products/239623/ishares-msci-eafe-etf): developed equities outside the US/Canada; inception 2001-08-14.
- [EEM — iShares](https://www.ishares.com/us/products/239637/ishares-msci-emerging-markets-etf): emerging markets; inception 2003-04-07.
- [IEF — iShares](https://www.ishares.com/us/products/239456/ishares-710-year-treasury-bond-etf): 7–10-year Treasuries; inception 2002-07-22.
- [TLT — iShares](https://www.ishares.com/us/products/239454/ishares-20-year-treasury-bond-etf): 20+-year Treasuries; inception 2002-07-22.
- [LQD — iShares](https://www.ishares.com/us/products/239566/ishares-iboxx-investment-grade-corporate-bond-etf): investment-grade corporate bonds; inception 2002-07-22.
- [HYG — iShares](https://www.ishares.com/us/products/239565/ishares-iboxx-high-yield-corporate-bond-etf): high-yield corporate bonds; inception 2007-04-04.
- [GLD — issuer](https://www.spdrgoldshares.com/usa/gld/): physical gold less expenses; inception/listing 2004-11-18. The source also discloses replacement of the London PM Fix with the LBMA Gold Price PM from 2015-03-20.
- [DBC — Invesco](https://www.invesco.com/us/en/financial-products/etfs/invesco-db-commodity-index-tracking-fund.html): commodity futures plus collateral income. Inception 2006-02-03 was confirmed by a search result for the official page and the [issuer factsheet](https://www.invesco.com/us-rest/contentdetail?contentId=1fd207c649400410VgnVCM10000046f1bf0aRCRD). Direct factsheet access redirected to a country splash/404; a complete local PDF was not preserved. [Commodity ETFs and ETPs](https://www.invesco.com/us/en/solutions/invesco-etfs/commodity-investing.html) confirms a methodology update from 2025-11-10. The official product source also discloses a managing-owner change on 2015-02-23.
- [BIL — SSGA](https://www.ssga.com/us/en/intermediary/etfs/state-street-spdr-bloomberg-1-3-month-t-bill-etf-bil): 1–3-month T-bills; inception/listing 2007-05-25; monthly distributions.

For nine instruments, excluding GLD, the source's first date follows inception. These are gaps in initial coverage, not proof of defective subsequent history. Initial availability is determined by the actual table rather than assumed coverage from inception.

Public iShares distribution tables contain Ex-Date, Record Date, Payable Date and amount; see the Distributions section for [EFA](https://www.ishares.com/us/products/239623/ishares-msci-eafe-etf). Their availability at the time of review did not establish a complete archive of 2007–2026 payments. SSGA provides distribution schedules; archive depth for BIL/SPY had not yet been established.

## Limitations and responses at N0

| Risk | Evidence / confidence | Effect | Agreed response |
|---|---|---|---|
| No payable dates in chart | All nonzero dividend events contain only amount/date; high confidence | Ex-date cannot immediately create spendable cash | Receivables; actual dates where available; missing-date proxy of +10 calendar days; stress 0/30. |
| Split/price basis not certified | Receipt includes EEM 3:1 in 2008 and BIL 1:2 in 2017; high confidence in event presence, OHLC semantics unverified | Double application of splits or incorrect quantities can invalidate NAV | N1 blocks N2 pending reconciliation; auto_adjust=False is insufficient. |
| Sparse BIL actions | 128 nonzero events over 19 years; count established, cause unknown | Cash-reference returns may be incomplete | Annual event profiles and issuer reconciliation; do not automatically equate missing events with zero. |
| Retrospective vendor data | Snapshot acquired at review time; no archived historical vintages | Availability assumptions and historical revisions | Causal prefixes, hashes and vintages; no true point-in-time claim. |
| No opening-auction/spread archive | Daily Open; plan specifies 10 bps | Real execution differs | Modeled next-open execution, cost/lag/reserve stress; no real-trading claims. |
| Fixed survivors | Universe assembled at review time | Survivorship/selection bias | Conclusions limited to this sample; disclose excluded classes. |
| Mandate changes | DBC index 2025, owner 2015; GLD reference 2015 | A fixed ticker does not guarantee a fixed economic object | Document events, before/after analysis and exclusion of DBC; do not splice in an index. |
| Usage/distribution rights not fully established | yfinance README warns about personal use/terms; direct terms not read | Technical access does not establish a license | Local educational research only; raw data ignored by Git; publication/paid data require separate authorization. |
| Reserved-period independence unknown | Owner answered "Unsure / do not remember" | Limits strength of statistical conclusions | Reserved historical check and future prospective stream. |

N0 defined the consequences of these gaps without claiming to close them. Full QA with calendars, OHLC consistency, revisions, reference prices/events and stop rules belonged to N1. Unconfirmed zero distributions and split basis blocked economic conclusions at this stage.

## Adapter documentation and literature

The [official download reference](https://ranaroussi.github.io/yfinance/reference/api/yfinance.download.html) describes separate auto_adjust/actions/repair/keepna settings and an exclusive end date; defaults are therefore not accepted implicitly. The [yfinance README](https://github.com/ranaroussi/yfinance) describes educational/research use, personal use and the need to check Yahoo rights independently. The code license does not automatically grant data rights. Full Yahoo terms could not be accessed through the browser; this was recorded as unresolved rather than a favorable legal conclusion.

Research motivation: [Time Series Momentum](https://www.aqr.com/Insights/Research/Journal-Article/Time-Series-Momentum) and [Value and Momentum Everywhere](https://www.aqr.com/insights/research/journal-article/value-and-momentum-everywhere). Separate diagnostics for multiple searches: [Deflated Sharpe Ratio](https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf) and [Probability of Backtest Overfitting](https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf). These support comparison and selection discipline; they do not establish profitability of the six registered variants. No new hypotheses from the literature were added during N0.

## Next stage recorded at N0

N1 required a frozen Python environment and source adapter, DATA_CONTRACT.md, an immutable local snapshot with a manifest, coverage/calendar/action QA, EEM 2008 and BIL 2017 checks, and payable-date coverage with actual/proxy flags. Reference prices/events required issuer comparison; split basis, distribution completeness and material revisions required explicit verdicts. Production H1/H2 NAV, optimization and reserved-performance reports were outside N1.

N0 completion criteria and their results are recorded in [STATUS.md](../../STATUS.md); the final machine verification receipt is [verification.json](verification.json). N0 completed a specification with disclosed limitations. It did not certify the N1 dataset.
