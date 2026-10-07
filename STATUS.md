# Project status

As of 7 October 2026, N0 assessment and N1 data preparation are complete. D020 approves D019's corrected vintage for N2 under its stated conditions. D015's earlier rejection remains part of the record. H1/H2 are `registered_not_tested`; reserved strategy performance has not been opened. The `main` branch contains the data pipeline only; N2 portfolio and execution functionality is not implemented here.

This is the [English editorial edition](docs/DOCUMENTATION_EDITION.md). Historical receipts and test results refer to their original versions. Commit identifiers retained below and in the journal may predate publication history rewriting; consult the [commit mapping](docs/HISTORY_REWRITE.md). Test counts below are historical records, not a new execution of the current suite.

## Documentation update: 7 October 2026

English edition 1.0-en.1 replaces the public documentation at baseline `4516269` with an investor-facing overview and separate reproduction instructions. Workspace-specific instructions and execution checklists are excluded from version control. Review checked the protocol's economic rules and identifiers, the N0 hash lineage, all 51 historical commit mappings, and local documentation links. The 16 public Markdown documents contain no Cyrillic text. Source code, tests, runtime configuration, historical receipts and the experiment journal are unchanged; application tests and research runs were not repeated for this editorial update.

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

## Limitations and next milestone

The data are not point-in-time; `available_at` is an assumption. Issuer records may be revised, and the seven corrections lack independent confirmation. GLD's evidence is weaker than an explicit assertion that distributions never occurred. DBC issuer coverage before 2007-12-17 is unproven. iShares expresses pre-split distributions in current units. Volume is unverified and unused; the universe is retrospective. D013's tolerance followed observation of rounding differences. Original Yahoo acquisition used uncommitted code, with its patch hash retained. Yahoo data rights are unestablished, and source snapshots are local rather than included in Git.

The next milestone is N2 portfolio accounting and execution under the [research protocol](RESEARCH_PROTOCOL.md): financial invariants, a trade ledger, and manual reconciliation on `data/derived/20261006T172442-80ef993493`. H1/H2 returns must wait for that accounting foundation. New data or corrections require fresh reconciliation, QA, and a new readiness decision.
