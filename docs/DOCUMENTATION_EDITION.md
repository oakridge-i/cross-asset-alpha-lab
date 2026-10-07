# English documentation edition

Edition: **1.0-en.1**, dated 7 October 2026.

This edition translates and reorganizes the documentation from `main` at commit `4516269fcccdba0c670e9ecb31d3cce337810c38`. The research protocol remains version **1.0**. Its formulas, universe, parameter values, comparison rules, execution assumptions and statistical criteria are unchanged. The edition identifier distinguishes the translated document from the original registered bytes; it is not a new research campaign or a new performance result.

The public README now presents the research question, available evidence, limitations and milestones. Detailed environment and replay instructions are in [REPRODUCIBILITY.md](REPRODUCIBILITY.md). Workspace-specific setup and execution checklists are no longer part of the public tree. Historical reports retain their original findings, identifiers and qualifications, with later resolutions identified separately. The [history mapping](HISTORY_REWRITE.md) preserves the original and published commit hashes.

## Protocol provenance

| Document | SHA-256 |
|---|---|
| Original research protocol 1.0 at the baseline commit | `71a230d738bddd6dff1f31f0fa8013ebac538c67e7f97570fa28e3d4a02ce849` |
| English protocol edition 1.0-en.1 | `b3ed75c8cb4c5e99eb4b9485c04e1b55acb570dde8c7495159b2f2f7688957d2` |
| Original N0 protocol manifest, retained unchanged | `89f5d563618a06044f4b08d3ca7198ba32f8efcb7919b1a273d1100e75ccabcc` |
| Original N0 verification receipt, retained unchanged | `bb204e27c9a8714e3da1e50ab667226faa35925a9cf0978412572e12a3fa8919` |

The original protocol remains recoverable from Git at the baseline commit. The [N0 verification receipt](n0/verification.json) records checks of the original documents, including files subsequently removed from the public tree. It has not been regenerated or edited to certify the English edition. The [N0 protocol manifest](n0/protocol_manifest.json) likewise retains its historical stage flags and version. Its original `data_ready_for_n2` value is not a statement of the later D020 decision.

This separation follows D011's requirement to preserve byte-level provenance when a document receives a new edition. Future substantive research changes require their own decision and research-version treatment; an editorial label does not authorize changes to the registered methodology.

## Scope of the update

Source code, tests, runtime configuration, dependency locks, stored data summaries, historical receipts and experiment records are unchanged. In particular, the existing experiment log retains SHA-256 `60510f25add4733268d2a1990004b3ace1ebbde83f7f0c0065205ccdf58e6cdb` at this edition's baseline. Later authorized runs will append records and change that hash.

The English edition is documentation for the N1 implementation on `main`. It does not incorporate the separate N2 implementation branch, claim new test results, or certify strategy performance. The original N0 verification script remains a historical procedure with external-directory and original-file dependencies; it is not an acceptance test for this reorganized documentation.

Editorial verification covers English-language consistency, local documentation links, preservation of research parameters and identifiers, historical-hash separation, and a diff check that excludes code and evidence changes. Application tests and research runs are not repeated for this edition. The current implementation status and the dates of recorded technical checks are in [STATUS.md](../STATUS.md).
