# Project status

As of 8 October 2026, N0 assessment and N1 data preparation are complete. D020 approves D019's corrected vintage for N2 under its stated conditions. D015's earlier rejection remains part of the record. The six H1/H2 configurations have the status `computed_not_evaluated` after the N4 runs on the branch `claude/n4-hypotheses` (not merged into `main`); reserved strategy performance has not been opened. The N2 account and execution engine is implemented, reviewed and merged into `main` (fast-forward from the branch `claude/n2-execution`, 7 October 2026); a registered run on the approved vintage passed all seven financial invariants. N3 (the benchmarks) is implemented, reviewed and merged into `main` (fast-forward from the branch `claude/n3-benchmarks`, 8 October 2026); the results of B0-B3 and REF_SPY for 2009-2022 are published in the [N3 report](docs/n3/N3_REPORT.md). N4 (the six H1/H2 configurations) is implemented, run, repeated and reported on the branch `claude/n4-hypotheses`, which has not been merged; its diagnostics are published in the [N4 report](docs/n4/N4_REPORT.md). No H1/H2 return, risk or utility result is computed or published, and the reserved period remains closed.

This is the [English editorial edition](docs/DOCUMENTATION_EDITION.md). Historical receipts and test results refer to their original versions. Commit identifiers retained below and in the journal may predate publication history rewriting; consult the [commit mapping](docs/HISTORY_REWRITE.md). Test counts below are historical records, not a new execution of the current suite.

## Documentation update: 7 October 2026

English edition 1.0-en.1 replaces the public documentation at baseline `4516269` with an investor-facing overview and separate reproduction instructions. Workspace-specific instructions and execution checklists are excluded from version control. Review checked the protocol's economic rules and identifiers, the N0 hash lineage, all 51 historical commit mappings, and local documentation links. The 16 public Markdown documents contain no Cyrillic text. Source code, tests, runtime configuration, historical receipts and the experiment journal are unchanged; application tests and research runs were not repeated for this editorial update.

The N2 documentation (EXECUTION_MODEL.md, docs/n2, the N2 specification, D021, and the N2 text in README, REPRODUCIBILITY and experiments/README) was added in English after edition 1.0-en.1. [docs/DOCUMENTATION_EDITION.md](docs/DOCUMENTATION_EDITION.md) remains the unchanged record of that edition, which did not include N2.

## Completed data work

`src/alpha_lab` implements Yahoo acquisition with immutable snapshots and a run journal; normalization into as-traded units; calendar and corporate-action QA; issuer-document acquisition; distribution reconciliation; provenance-bearing corrections; and offline replay. CLI commands are `acquire`, `evidence`, `reconcile`, `corrections`, `audit`, and `replay`.

| Record | Identifier and scope |
|---|---|
| Original Yahoo snapshot | `20261006T103809-a4a22ec667`: ten ETFs through 2026-10-05 |
| Initial issuer evidence | `20261006T122017-3048321309`: SSGA workbooks, six iShares pages, EEM 2008 and BIL 2017 split documents |
| Initial reconciliation | `20261006T122119-c6bfb5c69b` |
| Initial QA with actual payable dates | `20261006T122144-73228a71eb` |
| Initial replay | `20261006T122200-a9fd9ddbda` |
| Replay after final-review fixes | `20261006T131812-09887a01da` on `977eaf6` |

The initial N1 review added rejection of tampered replay inputs, preservation of partial Yahoo downloads after failure, journaling of unreadable inputs, and input-manifest hashes. The original verdict was not ready for N2 (D014/D015).

## Blocker resolution and approved vintage

On 6 October 2026, DBC issuer evidence was obtained by a local browser capture of Invesco JSON (SHA-256 `7337eeb7...`, full hash in D017). GLD evidence came from the SSGA prospectus and FAQ (D018). No new Yahoo acquisition was made.

| Record | Identifier and result |
|---|---|
| Expanded evidence | `20261006T172354-1c0a8ca2d8`: 12 sources |
| Original-data reconciliation | `20261006T172415-ce65adb53e`: EFA/EEM/IEF/DBC confirmed; GLD confirmed_no_distributions; SPY/TLT/LQD/HYG/BIL unresolved |
| Issuer-based corrections | `20261006T172434-fbb5c9f554`: 3 additions, 3 replacements, 1 removal under D016 |
| Approved derived vintage | `20261006T172442-80ef993493`: technical_pass true; 4,869/4,869 sessions for each ETF; adjustment_breaks 0 |
| Corrected-data reconciliation | `20261006T172453-4d72af092f`: all ten ETFs confirmed or confirmed_no_distributions |
| Corrected-vintage replay | `20261006T172504-6b932ef79b`: replay_equal true |
| Subsequent clean-tree replay | `20261007T064823-b7b806e0ce` on `591352a`: replay_equal true |

Both EEM 2008-07-24 (3:1) and BIL 2017-11-30 (1:2) split bases are confirmed. Actual payable dates are available for issuer-matched events; a fallback assumption applies elsewhere.

The older derived snapshot `20261006T122144-73228a71eb` cannot be reproduced with the current schema: `dividend_basis`, `dividend_correction_source`, and `corrections.json` were added. Its recorded exact replay is `20261006T131812-09887a01da` on `977eaf6` (snapshot hash beginning `f9602513`). N2 must use the approved corrected vintage and its corrections file.

Evidence is published in the [N1 report](docs/n1/N1_REPORT.md), [source evidence](docs/n1/source_evidence.json), [quality summary](docs/n1/quality.json), and [execution record](docs/n1/execution_record.md). Decisions D012-D020 explain the initial rejection, source selection, corrections, and final approval.

## Review and historical verification

| Verification point | Recorded result |
|---|---|
| N0 receipt | 35/35 checks at the N0 commit; `docs/n0/verification.json` |
| Early clean environment | Python 3.14.0, install from requirements.lock, pip freeze --all matched the lock, pip check passed, 66 tests passed |
| `977eaf6` | 79 tests passed; earlier-vintage replay equal |
| Final-review fixes, including `02af65e` | 122 tests passed |
| `6e33721`, R1-R4 fixes | 130 tests passed |
| `5a8eac5`, RR1-RR2 fixes | 145 tests passed |
| `591352a`, additional validation fixes | 149 tests passed; clean-tree corrected-vintage replay equal |
| Publication checkout `6c18d28` | 149 tests passed; offline build matched all 13 approved-vintage files by SHA-256 |

Recorded package and whitespace checks passed at the review checkpoints. The working environment's extra `openpyxl 3.1.5` and `et_xmlfile 2.0.0` packages were removed on 6 October 2026; they were unused by committed code and absent from the lock. Earlier N1 environment hashes retain them. See [reproduction instructions](docs/REPRODUCIBILITY.md) for commands and limits.

The [6 October review](docs/reviews/2026-10-06-n1-review.md) inspected `0a0e865` and changes after `80f75c9`, including closure work based on `799eef9`. It recorded 122 passing tests and byte-identical offline reconstruction of all 13 final-vintage files. Four P2 findings did not affect the seven saved corrections:

- R1: empty SSGA amount rows could justify removal. Rows with no amount in any of the three monetary columns are now rejected; an explicit zero remains valid.
- R2: corrections could lose a known payable date when no separate payable input existed. Add/replace dates are now retained as actual; conflicting actual dates are rejected.
- R3: reconciliation did not check correction lineage against the source snapshot. It now calls the lineage validator and journals inconsistent inputs as failed.
- R4: document-based no-distribution classification did not verify the PDF against the evidence manifest. File and hash integrity are now checked before classification.

Fix commit `6e33721` increased the suite from 122 to 130 cases. The real SSGA workbook parsed, GLD documents were present in the evidence manifest, correction lineage passed, and the approved vintage remained unchanged across all 13 hashes.

The [7 October follow-up review](docs/reviews/2026-10-07-n1-rereview.md) inspected `ae2cd38..6e33721` at documentation-only HEAD `a2019d7`. All eight added cases failed when the corresponding old modules were restored. The suite passed 130 tests in 35.37 seconds, and offline reconstruction again matched 13/13 files without changing the real data or journal. Two further findings were identified:

- RR1 (P2): reconciliation with `corrections.json` copied into a derived snapshot raised `KeyError`. The validator now accepts that form only when source lineage and byte identity with the referenced correction vintage are verified. Other payable snapshots and unsupported manifest types are rejected.
- RR2 (P3): invalid empty payable-date values were accepted as absent. Add/replace dates now require an absent value, null, or a valid ISO-date string. False, zero, empty strings, lists, dictionaries, and invalid dates are rejected.

Fix commit `5a8eac5` increased tests from 130 to 145. Each new regression case failed before its fix; the cross-snapshot payable check was also tested by disabling its condition. Both manifest forms passed on real inputs, the build matched 13/13 hashes, and the journal hash was unchanged. Review of `0266896..5a8eac5` found no Critical/Important issues; minor recursion/type handling for forged `corrections_vintage` references was corrected in `591352a`, reaching 149 tests. D020 approved readiness after these checks.

## Publication and receipt scope

The [public repository](https://github.com/oakridge-i/cross-asset-alpha-lab) was published under MIT on 7 October 2026, with `main` at `6c18d28` at that checkpoint. Before publication, historical email addresses and local paths were sanitized, including one journal path field, as documented in HISTORY_REWRITE.md. A local history bundle was retained separately. A fresh clone was checked across 52 commits for the removed personal email and local paths. Historical references remain material provenance; current English document hashes are registered separately.

The N0 verifier is specific to the original N0 layout and state. It requires sibling source directories, historical copies, and an empty experiment journal. It failed in a worktree where the expected sibling project was absent and is not a current N1 verification command. Its receipt is retained as historical evidence, rather than recertified against this edition.

## N2: account and execution engine

Branch `claude/n2-execution`, created from `main` at `4516269`, merged into `main` by fast-forward on 7 October 2026. The stage boundary is execution only: the section 5 weights, the section 11 metrics, B0-B3 and REF_SPY belong to N3. The design is in [the N2 specification](docs/superpowers/specs/2026-10-07-n2-execution-design.md). The mechanics are described in [EXECUTION_MODEL.md](EXECUTION_MODEL.md), the interpretations in D021, the hand calculations in [manual_reconciliation.md](docs/n2/manual_reconciliation.md), and the run results in the [N2 report](docs/n2/N2_REPORT.md).

Implemented, with commits:

- `src/alpha_lab/market.py`, vintage loader and payable-date contract: `89a3469`.
- `src/alpha_lab/ledger.py`, account state and events: `e034e62`, `0f48dc4`.
- `src/alpha_lab/engine.py`, day loop, scenarios and invariants, with manual reconciliations (cases 1, 2, 2b, 3, 3b, 4, 5, 6, 6b) in `tests/test_engine.py` and docs/n2/manual_reconciliation.md: `8f1a94b`, `1a43325`. Guard tests for the closed period and the end of the window, the 3:1 split case, and `ValueError` for non-numeric weights were added in the second commit.
- Result files, journaled run, the `simulate` command and the test provider `invariant_rotation`: `c1765e9`.
- EXECUTION_MODEL.md, decision D021, README links: `97cefa5`.
- Registered run and repeat on real data, report docs/n2/N2_REPORT.md. Run 1 `20261007T140216-1814c4deb7` (git_sha `4b7a618`, dirty_tree false, journal lines `9a20161`), run 2 `20261007T140236-ff53aee6df` (parent: run 1, git_sha `9a20161`, dirty_tree false, journal lines `24810ff`). Both `completed`; the 7 manifest files are identical. After run 1 the command failed with `UnicodeEncodeError` when printing a path containing Cyrillic on a cp1252 console (the run was journaled before the failure); run 2 was executed with `PYTHONIOENCODING=utf-8`. Fixed in `ad5debd`: `simulate` prints the path relative to the project, and `main()` escapes characters that cannot be represented.

Checks: pytest 261 passed on `4b7a618`. All seven invariants in `invariants.json` passed in both runs; 187 decisions, 1870 orders (1869 filled, 1 partial with the remainder cancelled as `fractional_quantity`, 0 cancelled), 1870 trades, 965 payouts (964 paid, 1 receivable); the EEM split of 2008-07-24 and the BIL split of 2017-11-30, and the single BIL proxy payout (ex-date 2008-03-03, payment 2008-03-13), passed through the engine. The only `receivable` row is SPY, ex-date 2022-12-16, payment 2023-01-31 (actual), 80.145, later than the window end of 2022-12-30. The last verified commit of the runs is `24810ff` (only documents and journal lines changed after `4b7a618`). NAV and returns are not published.

Interpretation choices made during implementation are recorded in D021: `execute_orders` returns `buy_fill`; default decision dates are the last XNYS session of a month whose execution is no later than the window end; the `proxy_payouts` list in `invariants.json`; the payable-date contract is checked only from 2007-05-30; a fractional purchase remainder after a split is cancelled with reason `fractional_quantity`; an invariant violation gives journal status `invariants_failed`, the result is frozen, and the command exits with code 0; the ticker index in `invariant_rotation` counts from zero. (Note: D022, item 1, changed the exit code of `simulate` on `invariants_failed` from 0 to 3; the text above is the historical N2 record.)

Review of the whole branch (`4516269..af59031`) found no Critical issues, 3 Important and 7 Minor. Fixes `af59031..fa9da85` (6 commits) addressed the Important items; pytest 265 passed on `fa9da85`, including with TEMP/TMP set to a directory with a Cyrillic name. The merge of `main` at `02beaee` and the English translation of the N2 documents changed no source code or tests; the full suite was run again after the merge: 265 passed.

Minor review findings deferred (examined at the final review; some are carried to the "Deferred" list below):

- market: `Market.index` searches for a session linearly; malformed tables raise `TypeError` or `KeyError` rather than `ValueError`; an event on a session dropped from the common calendar is lost silently (the current vintage has none); no tests for the scope of validation before the start date or for the source Market staying unchanged after `history()`.
- ledger: no boundary test of the cash tolerance (-1e-9 and -2e-8); the required purchase amount counts the full fractional order quantity; the parameter `nav` in `size_orders` shadows the function `nav`.
- engine: three of the seven invariants have no negative tests; `initial_cash = 0` raises `ZeroDivisionError`; `finite_number` rejects numpy int and float32, which matters for N3 weight providers (fixed in N3, `874beb2`); no test of a split and a dividend in the same session, or of an `actual` row under proxy 0 and 30.
- run: rejections before a Run exists (a scenario outside the grid, an unknown provider) are not journaled and an unknown provider raises `KeyError`; the CSV files with the `%.10g` format do not match the vintage bit for bit; the command exits with code 0 on `invariants_failed` (changed to code 3 by D022, item 1); `config.json` differs for 0 and 0.0; duplicated test helpers; no file-level check for partially filled and cancelled orders.

## N3: benchmarks

Branch `claude/n3-benchmarks`, created from `main` at `d8458b4`, merged into `main` by fast-forward on 8 October 2026. The stage boundary is the benchmarks only: B0-B3 and REF_SPY with the section 11 metrics for 2009-2022. H1/H2 are not computed. The design is in [the N3 specification](docs/superpowers/specs/2026-10-07-n3-benchmarks-design.md), the interpretations in D022, the account mechanics in [EXECUTION_MODEL.md](EXECUTION_MODEL.md), and the results in the [N3 report](docs/n3/N3_REPORT.md).

Implemented, with commits:

- Specification: `e9130a4`, `eb8ff6d`.
- N2 deferred items closed first: events and payments on sessions outside the common calendar are rejected, `9b8a721`; numeric (NumPy) weights accepted and non-positive initial cash rejected, `874beb2`; exit code 3 on `invariants_failed` and `quality_failed`, `74af51a`.
- `src/alpha_lab/features.py`, total-return index, sigma and covariance: `e6d1b2b`.
- `src/alpha_lab/portfolio.py`, inverse volatility and the common risk construction of section 5: `ccbcc4c`.
- `src/alpha_lab/benchmarks.py`, the weight providers B0, B1, B2, B3 and REF_SPY: `b14ec94`; provider registry and frozen target weights (`weights.csv`): `a0ef96a`.
- `src/alpha_lab/metrics.py`, section 11 metrics per period: `918d6fa`.
- `src/alpha_lab/report.py` and the `report` command, journaled: `7e8f2e6`; rejection tests and `ValueError` on malformed runs: `6e4c600`; identical code and environment required across runs: `a28836d`; initial cash normalised and report units clarified: `5a3dc72`.
- Provider checks on the approved vintage: `86b67dd`.
- D022 and the update of EXECUTION_MODEL.md: `282c1c4`; run sequence and D022 wording: `dfebc42`.

Checks: pytest 378 passed on `dfebc42`; the `src` tree is unchanged after that commit (later commits are journal lines and documents). An independent recomputation of the target weights over all 168 decision dates matched the providers to within 6e-15.

Registered runs on the approved vintage, window 2008-12-31 to 2022-12-30, main scenario, all `completed` with `dirty_tree` false and journal lines committed after each run:

| | First run | Repeat (parent: first run) |
|---|---|---|
| B0 | `20261007T180004-12aae80084` (git `dfebc42`, journal `a94a77e`) | `20261007T200819-ff620c4546` (git `bd42479`, journal `93544be`) |
| B1 | `20261007T180018-b6c98bd0aa` (git `a94a77e`, journal `50d4f33`) | `20261007T200822-68dc462b5f` (git `93544be`, journal `c1c63ca`) |
| B2 | `20261007T180026-dffe07154c` (git `50d4f33`, journal `1623de9`) | `20261007T200827-b8f9da8b3f` (git `c1c63ca`, journal `6daf373`) |
| B3 | `20261007T180033-bba99392df` (git `1623de9`, journal `8c6c220`) | `20261007T200831-bcab64c3eb` (git `6daf373`, journal `f198b69`) |
| REF_SPY | `20261007T180039-be7dd8f43a` (git `8c6c220`, journal `5b5fea4`) | `20261007T200835-3df74a38e0` (git `f198b69`, journal `132900c`) |
| Report | `20261007T200805-c75aa41980` (git `a72313d`, journal `bd42479`) | `20261007T200847-cf60a2b2d9` (git `132900c`, journal `5dce670`) |

Summary: all seven invariants passed in every run; 168 decisions for B0-B3 and one for REF_SPY; no cancellations; the only `receivable` row is SPY, ex-date 2022-12-16, payment 2023-01-31 (actual), later than the window end. The `files` dictionaries of the manifests are identical for all five benchmark pairs and for the two reports. The B0-B3 and REF_SPY results for 2009-2022 are published in the [N3 report](docs/n3/N3_REPORT.md) together with the weight-construction diagnostics and the disclosures (cash shares and realized volatility differ across benchmarks; actual ETF weights of B2 and B3 drift above the 25% target cap between decisions; REF_SPY holds cash because distributions are not reinvested; the Sharpe ratios of B0 are not meaningful). The report contains no candidate comparison and no statement about which benchmark is better.

N2 deferred items closed by N3: (a) events and payments outside the common calendar, `9b8a721`; numeric weights and non-positive initial cash, `874beb2`; exit code 3 on failed checks, `74af51a` (D022, items 1-5).

## N4: hypotheses H1/H2 (runs registered; branch not merged)

Branch `claude/n4-hypotheses`, created from `main` at `a1d734e`; not merged. The design is in [the N4 specification](docs/superpowers/specs/2026-10-08-n4-hypotheses-design.md); the interpretations are recorded in D023; the registered runs, the permitted diagnostics and the disclosures are published in the [N4 report](docs/n4/N4_REPORT.md). The six configurations H1_252_3, H1_252_4, H1_126_3, H1_126_4, H2_4of6 and H2_5of6 have the status `computed_not_evaluated` (D023, item 9).

Completed, with commits:

- Specification: `ce45e89` to `4616b06`.
- Turnover denominator check and N3 report corrections: `3256697` (values in D023 item 1).
- Momentum and month-end features: `68dd450`; cached XNYS month-end lookup: `199d3b5`.
- `common_risk` split into `capped` and `risk_detail` with bit-identical results: `8b224b4`.
- H1 and H2 providers with signal records: `1ae1eaf`.
- Engine integration (hypothesis kind, `parameters`, `signals.csv`, no `metrics.json`, withheld failure messages, engine-level causality tests): `fc2fe0e`, `4dc77a7`.
- Real-vintage checks: N3 regression of 45 benchmark file hashes and an independent recomputation of the target weights of six configurations at 168 decisions: `d6a1b2f`.
- Shared report checks parameterized with N3 report bytes unchanged: `d6eb037`.
- N4 report verification (spec section 7): `dd2c3e3`; diagnostics document, Markdown and the `hypothesis-report` command: `d5d6b3a`.
- D023, EXECUTION_MODEL.md, experiments/README.md and the N4 procedure in docs/REPRODUCIBILITY.md: `54100ac`.
- Amended report contract before the runs (spec sections 6.4 and 7, D023 items 1, 3, 6, 7 and 10): `d95bffc`, `9b962e3`.
- Report checks for all seven invariant flags, capped weights recomputed from `q`, turnover and `buy_fill` bounds, a clean report tree and value-free messages: `64ef609`; withheld serialization and freeze errors, month-end and test fixes: `2bbf709` to `ca54711`; H2 scale note, D023 provenance, `Provider` fields and real-vintage failure output: `bbf7640`.
- Pre-run state recorded in STATUS: `353196a`.
- Registered runs, report, repeats and repeat report on 8 October 2026 (journal lines committed after each step, `ae629c4` to `f921b41`), listed below. The N4 report and the updates of README.md, docs/REPRODUCIBILITY.md, experiments/README.md and EXECUTION_MODEL.md are in the publication commit that follows `f921b41`.

Registered runs on the approved vintage, window 2008-12-31 to 2022-12-30, main scenario, run from the root of the branch's working copy with `../../.venv/Scripts/python`; all `completed` without quality warnings:

| | First run | Repeat (parent: first run) |
|---|---|---|
| H1_252_3 | `20261008T174218-4053e6ea58` (git `353196a`, journal `ae629c4`) | `20261008T174340-dfb6a1c558` (git `6498f44`, journal `6244b39`) |
| H1_252_4 | `20261008T174253-cbb9ce2219` (git `ae629c4`, journal `23a157c`) | `20261008T174343-bda6d756d5` (git `6244b39`, journal `85cf34a`) |
| H1_126_3 | `20261008T174300-8531bbf3ae` (git `23a157c`, journal `2d9f24a`) | `20261008T174347-8fc8ed2441` (git `85cf34a`, journal `3d17051`) |
| H1_126_4 | `20261008T174303-337a7c2114` (git `2d9f24a`, journal `73501bc`) | `20261008T174355-8d6580f98d` (git `3d17051`, journal `52d5daf`) |
| H2_4of6 | `20261008T174309-3f0ab95aeb` (git `73501bc`, journal `f857975`) | `20261008T174358-e5b5bd731e` (git `52d5daf`, journal `9504121`) |
| H2_5of6 | `20261008T174315-44f030c165` (git `f857975`, journal `b938f40`) | `20261008T174405-a2006cbd61` (git `9504121`, journal `d0de40d`) |
| Report | `20261008T174328-e5860d5cf2` (git `b938f40`, journal `6498f44`) | `20261008T174417-e6157ee9c6` (git `d0de40d`, journal `f921b41`) |

Checks performed in this stage (8 October 2026):

- Before the runs: pytest 602 passed, 0 skipped, on `bbf7640` in an isolated copy (`git archive`) with the approved vintage; this includes both real-vintage tests (N3 regression of 45 benchmark file hashes; independent recomputation of the H1/H2 target weights at 168 decisions). The `src` tree of `bbf7640` (`b2791448e4888b9a8cc3677458b3bd5a28afd9ae`) is the `src` tree of all 14 N4 records. A review of the whole branch before the runs found no critical or important defect.
- All 14 records (six runs, report, six repeats, repeat report) are `completed` without quality warnings; the journal holds 28 N4 records, 94 in total. The first report accepted the six runs, and the seven financial invariants passed in every run.
- The `files` dictionaries of the manifests are equal for all seven pairs (nine files for each configuration, two files for the reports).
- Historical, earlier in this stage: pytest 556 passed on `d5d6b3a`; at `d6a1b2f` the real-vintage tests found 45 of 45 N3 file hashes equal and no selection difference in the recomputation (maximum absolute weight difference 2.2e-16).
- These checks evaluate target weights, benchmark files, journal records and file hashes only. No H1/H2 return, risk or utility figure was computed, and no excluded quantity of D023 item 6 was shown.

Limitations: the viewing restriction is procedural; the published aggregates combined with public prices permit approximate inference about exposures, and 2014-2022 is familiar history, not an independent test. The window excludes most of the 2008 crisis (protocol line 141). `require_warmup` counts rows, not XNYS sessions (D023 item 3); the approved vintage holds all 4869 sessions. The data limitations of D016-D020 apply. The status `computed_not_evaluated` states neither that a configuration is useful nor that it is rejected.

Next action: after authorization to commit, record the corrected source on a clean tree and complete the replacement campaign required by D023, item 8, with parent-linked runs, reports, repeats and all seven pair comparisons. Review that evidence before any authorized merge, push or transfer of `data/runs` and `data/reports`; then N5 computes the section 11 metrics of H1/H2 with its own frozen code.

Verified commit: `f921b41`, the last journal commit of the runs (the source tree is that of `bbf7640`). Publication commits: `81f7772` (N4 report and document updates), `48ae9ad` (one accounting line per repeat; the executed comparison script in docs/REPRODUCIBILITY.md), `5e574ca` (code block fix); they change documents only. The final review at `92dd78f` found one important report-validation defect and one minor documentation contradiction; the working-copy correction is described below.

## Post-review correction and completed replacement campaign

The final review of `a1d734e..92dd78f` independently checked the journal, approved vintage, source/environment identity, all seven original repeat pairs, both frozen report outputs and the publication tables. Its full suite passed 602 tests, zero skipped, at the unchanged `92dd78f`; this is the pre-fix historical baseline.

Commit `bd71fc0` corrects non-finite score intermediates and overflowing sums in N4 report validation, with synthetic regression cases and value-free rule/configuration/session errors. It also replaces the stale sentence in EXECUTION_MODEL.md that stated no H1/H2 run had been executed. D024 and the dated addition to the N4 report disclose the correction. Provider formulas, parameters, versions and tolerances are unchanged.

Full-suite result for the corrected uncommitted patch based on `92dd78f`: 610 passed, zero skipped, in 463.22 seconds; pytest exited with code 0. This includes the approved-vintage N3 regression and independent H1/H2 target checks. The new regressions failed on the old implementation (five failed, three already passed) and passed after the correction; the focused verification passed eleven cases. The scoped review of the fix passed both requirements and code-quality checks. Read-only revalidation with the corrected validator accepted both historical report input sets and reproduced their two output files byte-for-byte. At that pre-commit checkpoint, the historical experiment journal, all fourteen original attempt manifests and their file hashes, and the run/report directory inventories were unchanged; no replacement attempt had started. This revalidation is not a registered report on the corrected source.

After the correction checkpoint above, the replacement campaign and repeats were completed on committed clean source. All fourteen successful attempts are `completed` without warnings; all seven repeat pairs and all seven comparisons with the original repeat set have identical file hashes. Every successful run passes all seven financial invariants. The source tree is `16ffaf71b09c540cdc094121d040deacdeb3dab9`; the environment remains `5226dc9b0f21363873eb9a8420891733bbad1bc6c536262a3341eead520ce773`. The journal retains its original 94-row prefix and now holds 124 rows, including one failed launch and the fourteen successful replacement/repeat attempts.

Failed launch `20261008T192545-3e84621fc4` used a relative root that resolved to an unexpected nested directory and failed before loading the vintage. Its original two journal records were retained byte-for-byte in the canonical journal and committed as `ad9ec2f`; no data artifact was frozen. Successful retry `20261008T192727-e5e184b7db` uses an absolute root and links to that failure. The complete campaign receipt is in the [N4 report](docs/n4/N4_REPORT.md).

The last verified campaign journal commit is `f927314`; the source/test files remain exactly those of the patch that passed 610 tests with zero skips. The six configurations retain `computed_not_evaluated`. The final scoped campaign and publication review found no open issue. The N4 branch is verified for publication without merging; the branch remains separate from `main`, data remain in its worktree, and no N5/N6 evaluation is performed.

## Limitations and next milestone

The data are not point-in-time; `available_at` is an assumption. Issuer records may be revised, and the seven corrections lack independent confirmation. GLD's evidence is weaker than an explicit assertion that distributions never occurred. DBC issuer coverage before 2007-12-17 is unproven. iShares expresses pre-split distributions in current units. Volume is unverified and unused; the universe is retrospective. D013's tolerance followed observation of rounding differences. Original Yahoo acquisition used uncommitted code, with its patch hash retained. Yahoo data rights are unestablished, and source snapshots are local rather than included in Git.

The N2 and N3 runs do not remove the data limitations above: they remain disclosed in the N2 and N3 reports. N2 results concern accounting mechanics under the interpretations in D021, not strategy behavior. N3 results describe benchmark rules on a historical simulation with modeled costs (10 bps per side) and a modeled Open price. H1/H2 have the status `computed_not_evaluated` (N4 branch, not merged): no H1/H2 return, risk or utility result is computed or published, and the reserved period remains closed.

Next step:

1. The N4 correction and registered replacement campaign are complete on the separate branch. Integration remains a separate decision; the next research stage is N5 (walk-forward selection and the section 11 metrics, computed by frozen code). N6 holds the section 12 scenarios. New data or corrections require fresh reconciliation, QA and a new readiness decision.

Deferred:

- (a) Resolved in N3 (`9b8a721`, D022 item 2).
- (b) N1, a separate branch: `pipeline.audit_snapshot` should verify `payable.json` against its snapshot manifest, also without `--corrections` (an external review comment), with a test using a substituted file. N2 and N3 are not affected, because their loader pins the vintage hash.
- (c) N0: four broken local `aapl-finalization` links in docs/n0/AAPL_REUSE_AUDIT.md, line 15. The English edition from `main` replaced them with GitHub links to the AAPL release; whether those external links resolve was not checked here.
- (d) The cp1252 test prints an ASCII path and does not exercise the `backslashreplace` branch.
- (e) Other minor findings of the final N2 review that are not yet fixed: the small items in the list above (style, additional tests, diagnostics for rejections before a Run exists). The exit code on `invariants_failed` was changed to 3 by D022 (item 1). Fixed in `c18e904`: references and wording in DECISIONS.md, EXECUTION_MODEL.md and N2_REPORT.md.
