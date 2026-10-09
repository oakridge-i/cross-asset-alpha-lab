# N5 attempt accounting: precondition G0

Date: 9 October 2026. This document records the attempt statement that RESEARCH_PROTOCOL.md section 14 and experiments/README.md require before N5, as decided in [D025](../../DECISIONS.md), item 18. It states no research result.

## Registered attempts (from the experiment journal)

The journal at `main` commit `7a8ba1d` holds 124 rows. The H1/H2 attempts in it are the six registered configurations (H1_252_3, H1_252_4, H1_126_3, H1_126_4, H2_4of6, H2_5of6) with one registered run each, their seven report and repeat records, and the D024 replacement campaign: six bug-driven replacement runs, a replacement report, six repeats, a repeat report and one retained failed launch. No candidate was added by the replacement campaign. The line-by-line accounting is in [experiments/README.md](../../experiments/README.md) and the [N4 report](../n4/N4_REPORT.md).

## Statement of the project owner (9 October 2026)

The owner has become familiar with the hypotheses and has reviewed the work a small number of times. The owner declines to count views and reviews individually and approved the N5 specification.

## Consequences recorded in D025

- Prior exposure to H1/H2 is non-zero and unquantified. For the purposes of N5 this supersedes, without editing it, the statement of 6 October 2026 ("Not sure / do not remember", protocol line 130).
- No manual parameter or period change is reported.
- The multiple-testing caveat is stated in every N5 document as unresolved in size. All inferential figures are exploratory on familiar history, and the adjustment does not restore independence (protocol line 163).
- DSR and PBO are not implemented in N5, because they need an explicit trial set (D025 item 11).
- The attempts outside the journal are not counted in this document; the journal of the earlier AAPL project is excluded (experiments/README.md).

## Preconditions checked on 9 October 2026

- Branch `claude/n5-evaluation` was created from `main` at `7a8ba1d`.
- The five first N3 benchmark runs and the six N4 replacement-campaign runs of D025 item 17 were copied (not moved) to the primary `data/runs` and to this worktree; the approved vintage `20261006T172442-80ef993493` was copied to this worktree. Each copy passed `provenance.verify`, each run manifest hash equals the `data_sha256` of its terminal journal record, and the vintage manifest hash is `f89346107cf7da6ca052693d188b8a576a08d42024c86865b0a42a63b1d294f2`. No file inside an N4 run directory was opened.
- Baseline of the unchanged suite in this worktree: 610 passed, no skipped, in 256.70 seconds (a check in the current checkout; the earlier figure of 610 in STATUS.md is historical).
