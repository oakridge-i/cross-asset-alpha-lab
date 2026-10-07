# N1 report: data

Report dated 6 October 2026, with approval updated on 7 October 2026. The initial sections record branch codex/n1-data before closure; the closure sections record claude/n1-closure. D015, "not ready for N2", was approved and remains a historical verdict. The subsequent D019 readiness verdict was approved by D020 on 7 October 2026. Findings in the initial sections describe the state before closure.

## Scope

The ten protocol ETFs are SPY, EFA, EEM, IEF, TLT, LQD, HYG, GLD, DBC and BIL, in USD with daily regular sessions. The validation window runs from the common start 2007-05-30 through cutoff 2026-10-05 inclusive, comprising 4869 XNYS sessions. Yahoo snapshot 20261006T103809-a4a22ec667 (yfinance 1.7.0, auto_adjust=False, actions=True, repair=False) was acquired once and not refreshed. Issuer evidence was acquired separately as snapshot 20261006T122017-3048321309.

Price and action validation covered the entire history, including reserved 2023–2025 and 2026, as permitted by RESEARCH_PROTOCOL §9. Strategy returns, comparison tables, rankings and Sharpe ratios were not calculated for any period.

Run IDs, parents, git SHAs and exact commands are recorded in [execution_record.md](execution_record.md). Sources and reconciliation are summarized in [source_evidence.json](source_evidence.json). Full corrected-vintage QA is in [quality.json](quality.json), a byte copy of data/derived/20261006T172442-80ef993493/quality.json, sha256 51eae6705c56b9cd152efc1f84fb514ed18b24685da081f5d0ab25525dc569c3. QA for the former vintage 20261006T122144-73228a71eb (sha256 8355d70b…) remains in Git history. Original commit hashes are mapped in [HISTORY_REWRITE.md](../HISTORY_REWRITE.md); receipt preservation and the English edition are described in [DOCUMENTATION_EDITION.md](../DOCUMENTATION_EDITION.md).

## Validation methods

| Check | Method | Run |
|---|---|---|
| Snapshot immutability | manifest.json and manifest.sha256 in each directory, verified before use | All runs |
| Calendar, OHLC, actions, Adj Close reconciliation | `alpha_lab audit` (normalize + quality) | 20261006T122144-73228a71eb |
| Distributions against issuer | `alpha_lab reconcile`: SSGA xlsx (SPY, BIL), iShares pages (EFA, EEM, IEF, TLT, LQD, HYG) | 20261006T122119-c6bfb5c69b |
| EEM 2008 and BIL 2017 split basis | Documents in evidence snapshot, normalized table and reconciliation results | Manual assessment in this report |
| Reproducibility | `alpha_lab replay`: offline renormalization and byte comparison | 20261006T122200-a9fd9ddbda |

Reconciliation matches each Yahoo event with dividend > 0 within the window to an issuer record by ex-date. Amounts are compared in as-traded units. iShares amounts use current share units (`current_units`) and are multiplied by the same future_split_factor as Yahoo. Tolerance is 0.0005 USD × max(1, future_split_factor). Ticker materiality sums |diff| / previous as-traded close × 10⁴ across all matched-date events, including residuals within tolerance. A ticker is `confirmed` only if no event falls outside the matched classes.

## Initial results

### Technical reproducibility

All four committed-code reruns completed with status `completed` on clean trees. Replay returned `replay_equal: true`: rebuilt files matched the frozen derived snapshot byte for byte. The shared data_sha256 of replay and QA (f960251363f8105a2089a07ea5961327a60cd57cb2e2b2b64347934b663f3489) follows by construction, because replay records the hash of the snapshot being checked; it is not separate evidence. quality.json reported technical_pass true and an empty defective_assets list.

Limitation: the Yahoo snapshot was acquired with uncommitted code changes (git 1643651, dirty_tree true, patch hash in the journal). Its bytes are verified against the manifest. The acquisition code was not preserved in Git: the journal's patch hash can validate a supplied candidate patch but cannot reconstruct its contents.

### Calendar completeness

Each of the ten ETFs has 4869 rows in the window, with empty missing_sessions and unexpected_sessions. All have adjustment_breaks 0. The largest Adj Close factor residual is 2.25e-6 (TLT), against tolerance 5e-5. Adj Close reconciliation uses the same vendor and is not independent confirmation.

### Split basis

| Event | Document | Yahoo | Prices (as-traded close) | Distributions | Verdict |
|---|---|---|---|---|---|
| EEM 2008-07-24, 3:1 | PHLX series adjustment 1410-08 dated 2008-07-21: "3 for 1 Stock Split", ex-distribution date 7/24/2008; 82 pre-split EEM option series with strikes 70–185 (Aug 2008: 95–165; Sep and Dec 2008: 90–185; Jan 2009: 70–180; Mar 2009: 105–155) | 3:1 split on 2008-07-24 | 2008-07-23: 131.77 (source_close 43.92); 2008-07-24: 42.30. Ratio 3.115; relative to a split ratio of 3, this implies a session price change of −3.7% | 2007-12-24: iShares 0.648931 × 3 = 1.946793, Yahoo 1.947; 2008-06-25: 0.517255 × 3 = 1.551765, Yahoo 1.551999. Both matched | confirmed |
| BIL 2017-11-30, 1:2 | SSGA IRS Form 8937: action date November 30, 2017, "1:2 Reverse Share Split"; every two shares converted into one | 1:2 split on 2017-11-30 | 2017-11-29: 45.74 (source_close 91.48); 2017-11-30: 91.48. Ratio 2.0000 | 43 pre-split events in the window matched SSGA as-traded amounts after multiplying by 0.5 (2017-11-01: Yahoo raw 0.07 → 0.035, SSGA 0.034618); no pre-split discrepancies | confirmed |

The BIL PDF is a scan: pypdf could not extract text, so the page was read as an image. EEM PDF text was extracted with pypdf. The close ratios around the splits (EEM 3.115 with factor 3; BIL 2.0000 with factor 2) are not independent validation. as-traded close is source_close × future_split_factor, so the ratios demonstrate only the absence of a jump in Yahoo's split-adjusted series on the split date. The verdict relies on the documents, agreement of dates/ratios with Yahoo events, and agreement of pre-split issuer distributions after conversion. Pre-split EEM strikes of 70–185 are consistent with an as-traded close near 132. Issuer pre-split amounts match Yahoo after the same conversion, confirming distribution-unit conversion as well. The EEM split on 2005-06-09 lies before the window and was not document-verified.

### Initial distribution completeness

| Ticker | Status | Yahoo | Issuer | matched | mismatch | issuer_only | yahoo_only | Outside coverage | Materiality, bps |
|---|---|---|---|---|---|---|---|---|---|
| SPY | unresolved | 78 | 78 | 77 | 1 | 0 | 0 | 0 | 1.01 |
| EFA | confirmed | 39 | 39 | 39 | 0 | 0 | 0 | 0 | 1.55 |
| EEM | confirmed | 42 | 42 | 42 | 0 | 0 | 0 | 0 | 2.18 |
| IEF | confirmed | 233 | 233 | 233 | 0 | 0 | 0 | 0 | 5.74 |
| TLT | unresolved | 232 | 233 | 232 | 0 | 1 | 0 | 0 | 26.88 |
| LQD | unresolved | 232 | 233 | 232 | 0 | 1 | 0 | 0 | 36.02 |
| HYG | unresolved | 232 | 233 | 231 | 1 | 1 | 0 | 0 | 61.80 |
| BIL | unresolved | 128 | 127 (+105 zero rows) | 126 | 1 | 0 | 1 | 0 | 7.10 |
| DBC | unverified_no_issuer_source | 8 | — | — | — | — | — | — | — |
| GLD | unverified_no_issuer_source | 0 | — | — | — | — | — | — | — |

Unresolved events at the initial review:

| Ticker | ex-date | Class | Yahoo | Issuer | diff | bps | Explanation |
|---|---|---|---|---|---|---|---|
| HYG | 2012-11-01 | issuer_only | — | 0.510521 | −0.510521 | 55.14 | Yahoo lacks the November 2012 payment for HYG, LQD and TLT; adjacent 2012-10-01, 2012-12-03 and 2012-12-26 events are present. Ex-date follows the market closure of 29–30 October 2012. IEF has a Yahoo event on 2012-11-01. Vendor omission; cause unestablished. |
| LQD | 2012-11-01 | issuer_only | — | 0.378397 | −0.378397 | 30.76 | Same omission. |
| TLT | 2012-11-01 | issuer_only | — | 0.269553 | −0.269553 | 21.85 | Same omission. |
| BIL | 2022-03-01 | yahoo_only | 0.022 | 0.000000 | 0.022 | 2.41 | SSGA has a zero row, as in adjacent 2022-02…2022-05. Sources disagree; cause unestablished. |
| SPY | 2021-12-17 | amount_mismatch | 1.633 | 1.636431 | −0.003431 | 0.07 | SSGA lists only a dividend, capital gains 0; no split. Cause unestablished. |
| BIL | 2022-09-01 | amount_mismatch | 0.139 | 0.138459 | 0.000541 | 0.06 | Rounding the issuer amount to 0.001 gives 0.138, not 0.139. |
| HYG | 2023-12-14 | amount_mismatch | 0.379 | 0.37847 | 0.00053 | 0.07 | Rounding gives 0.378. |

Materiality includes residuals within tolerance: HYG's 61.80 bps comprises 55.14 for the omission, 0.07 for the mismatch and approximately 6.6 across 231 matched events. For TLT, LQD and HYG, the 2012-11-01 omission understates one monthly distribution in theoretical TR and N2 cash accounting.

At this stage, Invesco returned HTTP 406 to nonbrowser clients; no protection bypass was used. Yahoo lists 8 DBC events in the window: 2007-12-17, 2008-12-15, 2018-12-24, 2019-12-23, 2022-12-19, 2023-12-18, 2024-12-23 and 2025-12-22. Their amounts and completeness were initially unverified. Yahoo has no GLD distributions, and the initial evidence snapshot contained no issuer document establishing their absence.

### Initial payable dates

Actual payable dates came from reconciliation payable.json, only for matched events with payable_date no earlier than ex-date. Other events used ex-date + 10 calendar days as a proxy.

| Ticker | Events in window | actual | proxy |
|---|---|---|---|
| SPY | 78 | 77 | 1 (2021-12-17) |
| EFA | 39 | 39 | 0 |
| EEM | 42 | 42 | 0 |
| IEF | 233 | 233 | 0 |
| TLT | 232 | 232 | 0 |
| LQD | 232 | 232 | 0 |
| HYG | 232 | 231 | 1 (2023-12-14) |
| GLD | 0 | 0 | 0 |
| DBC | 8 | 0 | 8 |
| BIL | 128 | 125 | 3 (2008-03-03, 2022-03-01, 2022-09-01) |

BIL 2008-03-03 matched by amount, but its SSGA row has record date 2008-02-05 and payable date 2008-02-11, both earlier than ex-date. These dates repeat the 2008-02-01 row, whose amount differs: 0.086739 versus 0.115251. The issuer date was rejected.

## General limitations

- The data is not point-in-time. available_at at 18:00 America/New_York is a modeling assumption.
- Yahoo and issuers may revise history. Snapshots preserve the state at 2026-10-06; iShares publishes pre-split amounts restated in current share units.
- Volume remains in source units, marked unconfirmed, and is not used.
- The sample is retrospective: ten ETFs were selected in 2026, all surviving at cutoff.
- The 0.0005 USD tolerance was selected after observing BIL 2009 discrepancies (DECISIONS D013).
- iShares totalDistribution includes income, capital gains and return of capital; component classification was not verified.
- Yahoo data redistribution rights are unestablished; snapshots are excluded from Git.

## Initial verdict (approved, DECISIONS D015)

| N2 criterion | Result | Basis |
|---|---|---|
| Technical reproducibility | Passed | replay_equal true; evidence, reconciliation, QA and replay ran on clean trees; Yahoo snapshot 20261006T103809 was acquired on a dirty tree (1643651, dirty_tree true) |
| Calendar completeness | Passed | 4869/4869 sessions for all ten ETFs |
| EEM 2008 and BIL 2017 split basis | Passed | Both events confirmed |
| Distribution completeness and units | Failed | Only EFA, EEM and IEF confirmed; SPY, TLT, LQD, HYG and BIL unresolved; DBC and GLD unverified |
| Payable dates | Nonblocking | Protocol permits proxy dates; shares shown above |

Historical verdict: data was not ready for N2. The readiness requirement, both splits confirmed and every distributing ticker confirmed, was not met.

Blocking items at that time:

1. DBC: no issuer source; 8 unconfirmed events.
2. GLD: no document confirming absence of distributions.
3. HYG, LQD, TLT: missing Yahoo payment on 2012-11-01 (55, 31 and 22 bps).
4. BIL 2022-03-01: Yahoo 0.022 versus SSGA zero (2.4 bps).
5. SPY 2021-12-17, BIL 2022-09-01 and HYG 2023-12-14: amount discrepancies from 0.0005 to 0.0034 USD, each below 0.1 bps.

Options recorded for the owner's decision:

- DBC: obtain the Invesco distribution history in a browser and supply the file. Acceptance required a parser and a local-file-with-hash source type, a separate implementation task. An alternative was comparison with annual fund reports' distributions per share.
- GLD: add an issuer document stating the trust's distribution policy, such as the SPDR Gold Trust prospectus or annual report, to evidence as document.
- Missing 2012-11-01 events and BIL 2022-03-01: decide which source is authoritative. The plan permits corrections only in a separate derived vintage with evidence, preserving the original snapshot.
- Discrepancies below 0.1 bps: decide between acceptance with disclosure and replacement by issuer amounts in a separate vintage.

No threshold, tolerance or code was changed to make the initial reconciliation pass.

## Closure of blocking items

6 October 2026, branch claude/n1-closure. The five D015 blocking items were closed in three steps: issuer sources were added for DBC and GLD, unconfirmed Yahoo events were recorded in an explicit corrections file, and normalization applied it as a separate derived vintage. Yahoo snapshot 20261006T103809-a4a22ec667 was unchanged and not reacquired. The 0.0005 USD tolerance, materiality rule and readiness criterion were unchanged. IDs, parents, git SHAs and commands are in [execution_record.md](execution_record.md).

| Step | Run | Result |
|---|---|---|
| Issuer evidence | 20261006T172354-1c0a8ca2d8 | 12 sources completed |
| Reconciliation of original Yahoo data | 20261006T172415-ce65adb53e | confirmed: EFA, EEM, IEF, DBC; confirmed_no_distributions: GLD; unresolved: SPY, TLT, LQD, HYG, BIL (the same seven D015 events) |
| Corrections | 20261006T172434-fbb5c9f554 | 7 events: 3 add, 3 replace, 1 remove |
| Corrected-vintage QA | 20261006T172442-80ef993493 | technical_pass true, 4869/4869 sessions, adjustment_breaks 0 |
| Corrected-vintage reconciliation | 20261006T172453-4d72af092f | All ten tickers confirmed or confirmed_no_distributions |
| Replay | 20261006T172504-6b932ef79b | replay_equal true |

The former derived snapshot 20261006T122144-73228a71eb cannot be reproduced with current code: normalized tables gained dividend_basis and dividend_correction_source, and corrections.json became part of the derived snapshot. Its exact reproduction was recorded before this change in run 20261006T131812-09887a01da on commit 977eaf6, replay_equal true. It was not replayed again after the format change and is not passed to N2.

### Correction rule (D016)

The owner's decision of 6 October 2026 treats issuer data as authoritative for events that did not match Yahoo. Rules apply only outside the matched class:

- issuer_only: add the issuer amount in as-traded units;
- amount_mismatch: replace Yahoo's amount with the issuer amount;
- yahoo_only: remove only when the issuer explicitly lists a zero-amount row for that ex-date; otherwise leave unresolved.

Events matching within tolerance retain Yahoo amounts, rounded to 0.001. Prices, splits and other rows are unchanged. dividend holds the issuer amount (0 for removal), dividend_basis is `issuer_correction`, source_dividend retains the original Yahoo value, and dividend_correction_source references the source. A correction targeting an already matched date, an unknown date or an event with a nonmatching yahoo_amount is rejected.

### Event corrections

Sources are in data/evidence/20261006T172354-1c0a8ca2d8. HYG, LQD and TLT have no splits at these dates (factor 1.0), so iShares current-unit amounts equal as-traded amounts.

| Ticker | ex-date | Action | Yahoo | Issuer | Payable date | Source (file, sha256) |
|---|---|---|---|---|---|---|
| HYG | 2012-11-01 | add | No event | 0.510521 | 2012-11-07 | ishares-hyg.html, f6c39eed… |
| LQD | 2012-11-01 | add | No event | 0.378397 | 2012-11-07 | ishares-lqd.html, 96a13a36… |
| TLT | 2012-11-01 | add | No event | 0.269553 | 2012-11-07 | ishares-tlt.html, e29ba7e4… |
| BIL | 2022-03-01 | remove | 0.022 | 0 (explicit zero row) | None | ssga-distributions.xlsx, b162dd17… |
| SPY | 2021-12-17 | replace | 1.633 | 1.636431 | 2022-01-31 | ssga-distributions.xlsx, b162dd17… |
| BIL | 2022-09-01 | replace | 0.139 | 0.138459 | 2022-09-08 | ssga-distributions.xlsx, b162dd17… |
| HYG | 2023-12-14 | replace | 0.379 | 0.37847 | 2023-12-20 | ishares-hyg.html, f6c39eed… |

Full references, including URL and snapshot path/hash, are recorded for each event in corrections.json and [source_evidence.json](source_evidence.json). The causes of Yahoo discrepancies are unknown. Corrections implement the owner's issuer-authority decision rather than an established explanation of vendor error.

Effect on theoretical TR, measured as the 2026-10-05 index relative to the former vintage: SPY +0.0007%, TLT +0.22%, LQD +0.31%, HYG +0.55%, BIL −0.025%. The index is unchanged before each correction date. Comparing both vintages found identical OHLC, Volume, source_close, source_adj_close and split_ratio. dividend changes in exactly seven rows: HYG two, BIL two, SPY/LQD/TLT one each. Their dividend_basis is `issuer_correction`; all other rows are `source`.

### DBC issuer source

Invesco's JSON interface serves the distribution history of Invesco DB Commodity Index Tracking Fund. Nonbrowser clients receive HTTP 406. On 6 October 2026 the file was obtained by fetch() in a browser page context. The response was saved unchanged. Its sha256, 7337eeb71802061102d85c051178c059507b8c07a75fea7a9718e775f374ae41 (2521 bytes), was calculated in the browser and rechecked on disk. The owner authorized acquisition on 6 October 2026. The code contains no protection bypass. The file is read from data/manual/dbc-invesco-distribution.json and referenced by configs/n1_evidence.json. Evidence acquisition fails if sha256 differs; otherwise the file is copied into the evidence snapshot. Capture metadata (URL, page, timestamp and method) is preserved in data/manual/dbc-invesco-distribution.capture.json.

The history has 8 rows, with ex-dates from 2007-12-17 to 2025-12-22. All 8 match Yahoo within tolerance (largest difference 0.00047 on 2018-12-24), with no events unique to either source; materiality is 0.86 bps. Status: confirmed. Limitations: the issuer list starts on 2007-12-17, so issuer documentation does not establish completeness from 2007-05-30 through that date (Yahoo has no events in the interval). Amount components were not reconciled. The file was obtained once by one method and is excluded from Git because redistribution rights are unestablished.

### GLD no-distribution evidence

The snapshot contains two SSGA documents, both acquired over the network. Their sha256 values, verbatim quotations and page references are in [source_evidence.json](source_evidence.json). The documents state:

- SPDR Gold Trust prospectus, p. 9: shareholders do not receive dividends.
- Prospectus, p. 30, distributions section: the Trust Indenture permits shareholder distributions only in two cases, excess cash over 12 months exceeding $0.01 per share, and trust termination/liquidation.
- GLD FAQ, p. 3: the trust does not distribute gold-sale proceeds to shareholders. This appears in an answer about Form 1099-B for small gold sales to pay trust expenses. Its scope is those sale proceeds, rather than all shareholder distributions.

Neither document states that distributions have never occurred. confirmed_no_distributions rests on four considerations together: the narrow Trust Indenture conditions, the FAQ answer, zero Yahoo GLD events in the window, and the trust operating without termination during the window. The last point was not checked against a separate document; GLD quotes on all 4869 sessions support it indirectly.

### Closure reconciliation results

| Ticker | Original Yahoo data | bps | Corrected vintage | Yahoo | Issuer | matched | bps |
|---|---|---|---|---|---|---|---|
| SPY | unresolved | 1.01 | confirmed | 78 | 78 | 78 | 0.94 |
| EFA | confirmed | 1.55 | confirmed | 39 | 39 | 39 | 1.55 |
| EEM | confirmed | 2.18 | confirmed | 42 | 42 | 42 | 2.18 |
| IEF | confirmed | 5.74 | confirmed | 233 | 233 | 233 | 5.74 |
| TLT | unresolved | 26.88 | confirmed | 233 | 233 | 233 | 5.03 |
| LQD | unresolved | 36.02 | confirmed | 233 | 233 | 233 | 5.26 |
| HYG | unresolved | 61.80 | confirmed | 233 | 233 | 233 | 6.59 |
| BIL | unresolved | 7.10 | confirmed | 127 | 127 (+105 zero rows) | 127 | 4.64 |
| DBC | confirmed | 0.86 | confirmed | 8 | 8 | 8 | 0.86 |
| GLD | confirmed_no_distributions | N/A | confirmed_no_distributions | 0 | Documents | N/A | N/A |

Corrected-vintage materiality comprises Yahoo rounding residuals in matched events. Reconciliation confirms application of corrections and the absence of other discrepancies. It provides no independent source for the seven corrected events, which match issuer amounts by construction.

### Closure payable dates

Actual dates come from the corrections vintage's payable.json. Within the window only BIL 2008-03-03 retains a proxy because its SSGA record/payable dates precede ex-date, as explained above. All 8 DBC events now have actual dates, previously proxy. Corrections add actual dates for SPY 2021-12-17, BIL 2022-09-01, HYG 2023-12-14 and HYG/LQD/TLT 2012-11-01. Events before 2007-05-30 lie outside the validation window and retain proxies.

### Corrected-vintage limitations

- General limitations above remain: data is not point-in-time, the sample is retrospective, Yahoo data rights are unestablished, tolerance was selected after observing discrepancies (D013), and acquisition used uncommitted code.
- Matched-event amounts retain Yahoo's rounding to 0.001 and residual differences within tolerance, shown in the materiality table.
- Causes of the HYG/LQD/TLT 2012-11-01 omissions, BIL 2022-03-01 zero row and three amount discrepancies are unestablished.
- There is no second source independent of the issuer; issuer authority follows the owner's decision.
- Corrected rows retain available_at = 18:00 America/New_York on ex-date under the same historical_model_assumption. Issuer amounts were obtained in October 2026 and may be revised values rather than the amounts announced on the original date. Issuers announce amounts no later than ex-date, so the correction does not add information beyond the event itself, but a pipeline relying on Yahoo at that time would have seen the uncorrected values.
- In corrected-vintage comparison.json, yahoo_amount holds the corrected amount. Original Yahoo amounts remain in corrections.json (yahoo_amount) and the original-data reconciliation.
- quality.json has data_ready_for_n2 false because QA writes it as a constant. Readiness is determined by this report and decision D019.

### Final verdict (DECISIONS D019, approved by D020 on 7 October 2026)

The readiness rule was defined before reconciliation and remained unchanged: both splits confirmed, and every distributing ticker confirmed or confirmed_no_distributions on the corrected vintage.

| N2 criterion | Result | Basis |
|---|---|---|
| Technical reproducibility | Passed | replay_equal true for 20261006T172442-80ef993493; six closure runs on clean trees; Yahoo acquired on a dirty tree (1643651), with bytes verified against manifest |
| Calendar completeness | Passed | 4869/4869 sessions for all ten ETFs, adjustment_breaks 0, largest Adj Close residual 2.25e-6 (TLT) |
| EEM 2008 and BIL 2017 split basis | Passed | Both confirmed in Split basis; document sha256 values in new evidence match the former snapshot |
| Distribution completeness and units | Passed | Nine tickers confirmed (SPY, EFA, EEM, IEF, TLT, LQD, HYG, BIL, DBC), GLD confirmed_no_distributions, on vintage 20261006T172442-80ef993493 |
| Payable dates | Nonblocking | One proxy event in the window, BIL 2008-03-03 |

Approved verdict: the data is ready for N2 provided that N2 uses only corrected vintage data/derived/20261006T172442-80ef993493 with its corrections.json and discloses its limitations, particularly the GLD evidence basis and unverified DBC completeness before 2007-12-17. Uncorrected Yahoo data and vintage 20261006T122144-73228a71eb are not N2 inputs. Strategy returns were not calculated.
