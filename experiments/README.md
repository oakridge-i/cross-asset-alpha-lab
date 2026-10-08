# Experiment journal

[EXPERIMENT_LOG.jsonl](EXPERIMENT_LOG.jsonl) records N1 data runs, N2 execution runs, N3 benchmark runs, the N4 hypothesis runs, reports and repeats (8 October 2026), and subsequent strategy calculations. At N0 it contained zero rows; availability and metadata probes were recorded separately in `docs/n0`. No strategy return or risk result has been computed for publication; the N2 runs use a test weight provider and publish no returns. The journal holds the N3 benchmark runs of B0, B1, B2, B3 and REF_SPY, the benchmark report and their repeats (7 October 2026); their results are in the [N3 report](../docs/n3/N3_REPORT.md). The journal holds the six N4 runs of the H1/H2 configurations, the N4 report, and their repeats (8 October 2026), with the run ids listed in the N4 section below; the status of the six configurations is `computed_not_evaluated`. The journal holds no H1/H2 return, risk or utility result: the runs freeze no `metrics.json`, and the diagnostics permitted by D023, item 6 are published in the [N4 report](../docs/n4/N4_REPORT.md).

## Events and provenance

The journal is append-only JSONL in UTF-8, with one record per event. A run begins with `started`. The current implementation emits one of three terminal statuses: `completed`; `quality_failed`, for an N1 audit that completes but fails technical QA (output files are frozen and the failed checks are recorded); or `failed`, for an execution error. A `simulate` run (N2 or N3) emits a fourth, `invariants_failed`, when the run completes but one or more of its seven financial invariants fail: the result is frozen for inspection and the names of the failed checks are listed in `quality_warnings`. Code that selects unsuccessful runs must handle `failed`, `quality_failed` and `invariants_failed`, not only `failed`. The commands signal these two check statuses by exit code: `simulate` exits with code 3 on `invariants_failed` and `audit` with code 3 on `quality_failed`, after printing the output directory; `completed` exits with 0, an exception with 1 and an argument error with 2 (D022, item 1). `report` has no check status: it completes or fails. A completed acquisition or reconciliation does not by itself certify research readiness; inspect quality warnings and the separate readiness decision. A repeated N2 run is started with `--parent` and records the earlier run in `parent_attempt_id`; the two registered N2 runs and their results are described in the [N2 report](../docs/n2/N2_REPORT.md).

A crash may leave an unmatched `started` record. Preserve it and document any interruption or recovery explicitly; the current code does not emit automatic `interrupted` or `recovered` events. A retry receives a new `run_id` and a reference to its predecessor. Errors are retained. An identical replay is not an independent experiment.

Required fields are `schema_version`, `event`, `run_id`, `attempt_id`, `parent_attempt_id` (which may be null), `created_at_utc`, `protocol_version`, `git_sha`, `dirty_tree`, `dirty_patch_sha256` (null for a clean tree), `config_sha256`, `data_sha256`, `environment_manifest_sha256`, `seed`, `purpose`, `candidate_ids`, `universe`, `splits`, `status`, `output_paths`, and `quality_warnings`.

Before acquisition, `data_sha256` is null with the reason `data_not_acquired`. A terminal record contains the snapshot hash or explains why no valid snapshot exists. Inapplicable or unavailable values use explicit nulls and recorded reasons. The initial event stores the configuration and environment manifest. Provenance must not imply that an unavailable environment or input was verified.

## N3 benchmark runs and report

A `simulate` run of a benchmark provider (`B0`, `B1`, `B2`, `B3`, `REF_SPY`) has the purpose `N3 benchmark run` and `candidate_ids` equal to the one provider name, in both the `started` and the terminal record. Runs of the test provider keep the purpose `N2 execution run` and an empty list. The registered sequence is five benchmark runs, then `report` over their five directories, then a repeat of each of the six runs with `--parent` set to its first run. The report run has the purpose `N3 benchmark report` and `candidate_ids` B0, B1, B2, B3, REF_SPY. It accepts only `completed` benchmark runs with `dirty_tree` false and a non-null `git_sha`, so each run starts on a clean tree and its journal lines are committed before the next run. A `failed` or `invariants_failed` run stays in the journal; its repeat records it in `parent_attempt_id`. Commands are in [REPRODUCIBILITY.md](../docs/REPRODUCIBILITY.md); the rules are in D022.

## N4 hypothesis runs and report

This section registers the procedure of D023, which was written before any H1/H2 run and executed on 8 October 2026 (the journal holds 28 records with these purposes). A `simulate` run of a hypothesis provider (`H1_252_3`, `H1_252_4`, `H1_126_3`, `H1_126_4`, `H2_4of6`, `H2_5of6`) has the purpose `N4 hypothesis run` and `candidate_ids` equal to the one provider name, in both the `started` and the terminal record. The journaled configuration of such a run also holds `provider.parameters`. The run freezes nine files: the seven N2 files, `weights.csv` and `signals.csv`; it freezes no `metrics.json`, so the return and risk metrics of H1/H2 are first computed in N5, and the requirement below that terminal portfolio records retain metrics is deferred to that stage for these runs. The report run has the purpose `N4 hypothesis report` and `candidate_ids` H1_252_3, H1_252_4, H1_126_3, H1_126_4, H2_4of6, H2_5of6; it accepts only `completed` hypothesis runs with `dirty_tree` false and a non-null `git_sha` (D023, item 7).

The registered sequence, each step on a clean tree with its journal lines committed before the next step, is: `simulate` for the six configurations (window 2008-12-31 to 2022-12-30, main scenario); `hypothesis-report` over the six run directories; a repeat of each of the six runs with `--parent` set to its first run, then a repeat of the report over the six repeat directories with `--parent` set to the first report; and a comparison of the manifest `files` dictionaries for all seven pairs. Commands are in [REPRODUCIBILITY.md](../docs/REPRODUCIBILITY.md). A `failed` or `invariants_failed` run and a failed report stay in the journal. Changes to `src` after the first registered run are bug fixes only, never motivated by the permitted diagnostics. Each such change requires rerunning all six configurations on the new tree, each with `--parent` set to its previous run, followed by a new report; a fix that changes the output of a provider increments its version, and a change in H1_252_3 also increments the versions of H2_4of6 and H2_5of6 (D023, item 8).

Status. `computed_not_evaluated` means that the configuration has a completed registered run on the approved vintage, the first completed N4 report over the final set of six runs has accepted it, the repeat comparison has found all seven pairs equal, and no decision under protocol section 13 exists. The journal records no status event. The current status of the six configurations is `computed_not_evaluated`; the three conditions were met on 8 October 2026 by the records below (D023, item 9). Hypothesis run directories are storage read only by code; only the diagnostics permitted by D023, item 6 may be published or shown.

Registered N4 records, all `completed` (the journal commit of each step is in the [N4 report](../docs/n4/N4_REPORT.md)):

| Configuration | First run | Repeat (parent: first run) |
|---|---|---|
| H1_252_3 | 20261008T174218-4053e6ea58 | 20261008T174340-dfb6a1c558 |
| H1_252_4 | 20261008T174253-cbb9ce2219 | 20261008T174343-bda6d756d5 |
| H1_126_3 | 20261008T174300-8531bbf3ae | 20261008T174347-8fc8ed2441 |
| H1_126_4 | 20261008T174303-337a7c2114 | 20261008T174355-8d6580f98d |
| H2_4of6 | 20261008T174309-3f0ab95aeb | 20261008T174358-e5b5bd731e |
| H2_5of6 | 20261008T174315-44f030c165 | 20261008T174405-a2006cbd61 |
| N4 hypothesis report | 20261008T174328-e5860d5cf2 | 20261008T174417-e6157ee9c6 |

Attempt accounting before N5 (spec section 12; D023, item 9). The accounting consists of the following lines, which are not added together as independent experiments:

- Registered configurations: six, one registered run each (the first-run ids above): H1_252_3, H1_252_4, H1_126_3, H1_126_4, H2_4of6 and H2_5of6.
- Reruns after bug fixes: zero. No change to `src` was made after the first registered run; every run and report started from the same `src` tree.
- Repeats made with `--parent`: six, one for each configuration (the repeat ids above, each with its first run as parent). Each is counted as a repeat, not as a new candidate and not as an independent experiment.
- Report runs: two, the first report (`20261008T174328-e5860d5cf2`) and its repeat (`20261008T174417-e6157ee9c6`, parent: the first report). Neither is a strategy attempt.
- Strategy attempts outside the journal in this project: none. The journal of the earlier AAPL project is excluded.
- Not attempts and not journaled: the independent recomputation of N4 evaluates the target weights of the providers at all 168 decisions and computes no H1/H2 account or return; the N3 regression reruns the B0-B3 and REF_SPY accounts in memory and compares the 45 benchmark file hashes, including `metrics.json`. Both print only counts and maximum differences. The real-vintage tests of the test suite are therefore not attempts.

## Requirements for later research stages

The following are registered requirements, rather than portfolio functionality implemented on `main`:

- Candidate identifiers: `B0`, `B1`, `B2`, `B3`, `REF_SPY`; `H1_252_3`, `H1_252_4`, `H1_126_3`, `H1_126_4`; `H2_4of6`, `H2_5of6`; and the separate policy `P_A1`.
- Scenarios carry `scenario_id` and `parent_run_id`. Time splits record exact boundaries and roles, rather than only train/test labels.
- Terminal portfolio records retain signals, orders, trades, holdings, distributions, NAV, and metrics whenever applicable.
- Fixed configurations, the adaptive policy, and additional hypotheses have separate `attempt_id` values. Diagnostic scenarios are listed completely. A strategy changed in response to a diagnostic is a new attempt linked to its parent.
- Opening reserved performance is recorded as `test_opened`, with its reason and frozen Git, protocol, configuration, and data hashes. N0 source QA is not a performance opening.

Before N5, reconstruct the number of all known manual and programmatic attempts. The six registered configurations are not a complete measure of multiple testing if selection methods, periods, or data were also changed. Do not include an incomplete historical AAPL journal as a statistical trial count for this project; disclose prior market familiarity separately.

Historical hashes and receipts retain their original scope. See the [English documentation edition](../docs/DOCUMENTATION_EDITION.md) and [commit mapping](../docs/HISTORY_REWRITE.md).
