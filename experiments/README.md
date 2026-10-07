# Experiment journal

[EXPERIMENT_LOG.jsonl](EXPERIMENT_LOG.jsonl) records N1 data runs and, when implemented, subsequent portfolio and strategy calculations. At N0 it contained zero rows; availability and metadata probes were recorded separately in `docs/n0`. No strategy results have been produced on `main`.

## Events and provenance

The journal is append-only JSONL in UTF-8, with one record per event. A run begins with `started`. The current N1 implementation emits the terminal events `completed`, `quality_failed` for an audit that completes but fails technical QA, or `failed` for an execution error. A completed acquisition or reconciliation does not by itself certify research readiness; inspect quality warnings and the separate readiness decision.

A crash may leave an unmatched `started` record. Preserve it and document any interruption or recovery explicitly; the current code does not emit automatic `interrupted` or `recovered` events. A retry receives a new `run_id` and a reference to its predecessor. Errors are retained. An identical replay is not an independent experiment.

Required fields are `schema_version`, `event`, `run_id`, `attempt_id`, `parent_attempt_id` (which may be null), `created_at_utc`, `protocol_version`, `git_sha`, `dirty_tree`, `dirty_patch_sha256` (null for a clean tree), `config_sha256`, `data_sha256`, `environment_manifest_sha256`, `seed`, `purpose`, `candidate_ids`, `universe`, `splits`, `status`, `output_paths`, and `quality_warnings`.

Before acquisition, `data_sha256` is null with the reason `data_not_acquired`. A terminal record contains the snapshot hash or explains why no valid snapshot exists. Inapplicable or unavailable values use explicit nulls and recorded reasons. The initial event stores the configuration and environment manifest. Provenance must not imply that an unavailable environment or input was verified.

## Requirements for later research stages

The following are registered requirements, rather than portfolio functionality implemented on `main`:

- Candidate identifiers: `B0`, `B1`, `B2`, `B3`, `REF_SPY`; `H1_252_3`, `H1_252_4`, `H1_126_3`, `H1_126_4`; `H2_4of6`, `H2_5of6`; and the separate policy `P_A1`.
- Scenarios carry `scenario_id` and `parent_run_id`. Time splits record exact boundaries and roles, rather than only train/test labels.
- Terminal portfolio records retain signals, orders, trades, holdings, distributions, NAV, and metrics whenever applicable.
- Fixed configurations, the adaptive policy, and additional hypotheses have separate `attempt_id` values. Diagnostic scenarios are listed completely. A strategy changed in response to a diagnostic is a new attempt linked to its parent.
- Opening reserved performance is recorded as `test_opened`, with its reason and frozen Git, protocol, configuration, and data hashes. N0 source QA is not a performance opening.

Before N5, reconstruct the number of all known manual and programmatic attempts. The six registered configurations are not a complete measure of multiple testing if selection methods, periods, or data were also changed. Do not include an incomplete historical AAPL journal as a statistical trial count for this project; disclose prior market familiarity separately.

Historical hashes and receipts retain their original scope. See the [English documentation edition](../docs/DOCUMENTATION_EDITION.md) and [commit mapping](../docs/HISTORY_REWRITE.md).
