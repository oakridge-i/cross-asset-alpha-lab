# Experiment journal

[EXPERIMENT_LOG.jsonl](EXPERIMENT_LOG.jsonl) records N1 data runs, N2 execution runs, N3 benchmark runs, the N4 hypothesis runs, reports and repeats (8 October 2026), and subsequent strategy calculations. At N0 it contained zero rows; availability and metadata probes were recorded separately in `docs/n0`. No strategy return or risk result has been computed for publication; the N2 runs use a test weight provider and publish no returns. The journal holds the N3 benchmark runs of B0, B1, B2, B3 and REF_SPY, the benchmark report and their repeats (7 October 2026); their results are in the [N3 report](../docs/n3/N3_REPORT.md). The journal holds the six N4 runs of the H1/H2 configurations, the N4 report, and their repeats (8 October 2026), with the run ids listed in the N4 section below; the status of the six configurations is `computed_not_evaluated`. The journal holds no H1/H2 return, risk or utility result: the runs freeze no `metrics.json`, and the diagnostics permitted by D023, item 6 are published in the [N4 report](../docs/n4/N4_REPORT.md). The procedure for the N5 walk-forward evaluation (D025) is registered in the section "N5 runs, evaluation report and campaign" below; the journal contains no N5 record yet.

## Events and provenance

The journal is append-only JSONL in UTF-8, with one record per event. A run begins with `started`. The current implementation emits one of three terminal statuses: `completed`; `quality_failed`, for an N1 audit that completes but fails technical QA (output files are frozen and the failed checks are recorded); or `failed`, for an execution error. A `simulate` run (N2 or N3) emits a fourth, `invariants_failed`, when the run completes but one or more of its seven financial invariants fail: the result is frozen for inspection and the names of the failed checks are listed in `quality_warnings`. Code that selects unsuccessful runs must handle `failed`, `quality_failed` and `invariants_failed`, not only `failed`. The commands signal these two check statuses by exit code: `simulate` exits with code 3 on `invariants_failed` and `audit` with code 3 on `quality_failed`, after printing the output directory; `completed` exits with 0, an exception with 1 and an argument error with 2 (D022, item 1). `report` has no check status: it completes or fails. A completed acquisition or reconciliation does not by itself certify research readiness; inspect quality warnings and the separate readiness decision. A repeated N2 run is started with `--parent` and records the earlier run in `parent_attempt_id`; the two registered N2 runs and their results are described in the [N2 report](../docs/n2/N2_REPORT.md).

A crash may leave an unmatched `started` record. Preserve it and document any interruption or recovery explicitly; the current code does not emit automatic `interrupted` or `recovered` events. A retry receives a new `run_id` and a reference to its predecessor. Errors are retained. An identical replay is not an independent experiment.

Required fields are `schema_version`, `event`, `run_id`, `attempt_id`, `parent_attempt_id` (which may be null), `created_at_utc`, `protocol_version`, `git_sha`, `dirty_tree`, `dirty_patch_sha256` (null for a clean tree), `config_sha256`, `data_sha256`, `environment_manifest_sha256`, `seed`, `purpose`, `candidate_ids`, `universe`, `splits`, `status`, `output_paths`, and `quality_warnings`.

Before acquisition, `data_sha256` is null with the reason `data_not_acquired`. A terminal record contains the snapshot hash or explains why no valid snapshot exists. Inapplicable or unavailable values use explicit nulls and recorded reasons. The initial event stores the configuration and environment manifest. Provenance must not imply that an unavailable environment or input was verified.

## N3 benchmark runs and report

A `simulate` run of a benchmark provider (`B0`, `B1`, `B2`, `B3`, `REF_SPY`) has the purpose `N3 benchmark run` and `candidate_ids` equal to the one provider name, in both the `started` and the terminal record. Runs of the test provider keep the purpose `N2 execution run` and an empty list. The registered sequence is five benchmark runs, then `report` over their five directories, then a repeat of each of the six runs with `--parent` set to its first run. The report run has the purpose `N3 benchmark report` and `candidate_ids` B0, B1, B2, B3, REF_SPY. It accepts only `completed` benchmark runs with `dirty_tree` false and a non-null `git_sha`, so each run starts on a clean tree and its journal lines are committed before the next run. A `failed` or `invariants_failed` run stays in the journal; its repeat records it in `parent_attempt_id`. Commands are in [REPRODUCIBILITY.md](../docs/REPRODUCIBILITY.md); the rules are in D022.

## N4 hypothesis runs and report

This section registers the procedure of D023, which was written before any H1/H2 run and executed on 8 October 2026 (the original campaign contributed 28 records; the D024 campaign and its failed launch add 30, for 58 N4 records). A `simulate` run of a hypothesis provider (`H1_252_3`, `H1_252_4`, `H1_126_3`, `H1_126_4`, `H2_4of6`, `H2_5of6`) has the purpose `N4 hypothesis run` and `candidate_ids` equal to the one provider name, in both the `started` and the terminal record. The journaled configuration of such a run also holds `provider.parameters`. The run freezes nine files: the seven N2 files, `weights.csv` and `signals.csv`; it freezes no `metrics.json`, so the return and risk metrics of H1/H2 are first computed in N5, and the requirement below that terminal portfolio records retain metrics is deferred to that stage for these runs. The report run has the purpose `N4 hypothesis report` and `candidate_ids` H1_252_3, H1_252_4, H1_126_3, H1_126_4, H2_4of6, H2_5of6; it accepts only `completed` hypothesis runs with `dirty_tree` false and a non-null `git_sha` (D023, item 7).

The registered sequence, each step on a clean tree with its journal lines committed before the next step, is: `simulate` for the six configurations (window 2008-12-31 to 2022-12-30, main scenario); `hypothesis-report` over the six run directories; a repeat of each of the six runs with `--parent` set to its first run, then a repeat of the report over the six repeat directories with `--parent` set to the first report; and a comparison of the manifest `files` dictionaries for all seven pairs. Commands are in [REPRODUCIBILITY.md](../docs/REPRODUCIBILITY.md). A `failed` or `invariants_failed` run and a failed report stay in the journal. Changes to `src` after the first registered run are bug fixes only, never motivated by the permitted diagnostics. Each such change requires rerunning all six configurations on the new tree, each with `--parent` set to its previous run, followed by a new report; a fix that changes the output of a provider increments its version, and a change in H1_252_3 also increments the versions of H2_4of6 and H2_5of6 (D023, item 8).

Status. `computed_not_evaluated` means that the configuration has a completed registered run on the approved vintage, the first completed N4 report over the final set of six runs has accepted it, the repeat comparison has found all seven pairs equal, and no decision under protocol section 13 exists. The journal records no status event. The current status of the six configurations is `computed_not_evaluated`; the three conditions were met on 8 October 2026 by the records below (D023, item 9). Hypothesis run directories are storage read only by code; only the diagnostics permitted by D023, item 6 may be published or shown.

The records below are the original N4 campaign. D024 records the post-run numerical validation correction, committed as `bd71fc0`. Its replacement campaign and repeats are complete and disclosed below. Historical records and the status they establish are retained.

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
- Reruns after bug fixes: zero in the original campaign. No change to `src` was made between the first registered run and the repeat report of that campaign; every run and report in it started from the same `src` tree. The later D024 correction (`bd71fc0`) did change `src`, and the replacement campaign that followed is a bug-driven rerun of all six configurations; it is accounted for in the section "D024 replacement campaign and attempt accounting" below.
- Repeat of H1_252_3: run `20261008T174340-dfb6a1c558`, parent `20261008T174218-4053e6ea58`; a repeat with `--parent`, not a new candidate and not an independent experiment.
- Repeat of H1_252_4: run `20261008T174343-bda6d756d5`, parent `20261008T174253-cbb9ce2219`; a repeat with `--parent`, not a new candidate and not an independent experiment.
- Repeat of H1_126_3: run `20261008T174347-8fc8ed2441`, parent `20261008T174300-8531bbf3ae`; a repeat with `--parent`, not a new candidate and not an independent experiment.
- Repeat of H1_126_4: run `20261008T174355-8d6580f98d`, parent `20261008T174303-337a7c2114`; a repeat with `--parent`, not a new candidate and not an independent experiment.
- Repeat of H2_4of6: run `20261008T174358-e5b5bd731e`, parent `20261008T174309-3f0ab95aeb`; a repeat with `--parent`, not a new candidate and not an independent experiment.
- Repeat of H2_5of6: run `20261008T174405-a2006cbd61`, parent `20261008T174315-44f030c165`; a repeat with `--parent`, not a new candidate and not an independent experiment.
- Repeat of the N4 report: run `20261008T174417-e6157ee9c6`, parent `20261008T174328-e5860d5cf2`; a repeat with `--parent`, not a new candidate and not an independent experiment.
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

## D024 replacement campaign and attempt accounting

The correction changed report validation only. The six replacement runs, their report, six repeats and repeat report completed on source tree `16ffaf71b09c540cdc094121d040deacdeb3dab9`, with clean source provenance and journal commits between steps. All seven new pairs and the seven comparisons with the original repeat set have identical `manifest.files`. Provider versions and the six registered configurations are unchanged.

| Configuration / report | Role | Run ID | Parent | Source commit | Journal commit |
|---|---|---|---|---|---|
| H1_252_3 | Replacement | `20261008T192727-e5e184b7db` | `20261008T192545-3e84621fc4` | `ad9ec2f` | `65d53f5` |
| H1_252_4 | Replacement | `20261008T192731-0f8d083cb0` | `20261008T174343-bda6d756d5` | `65d53f5` | `b720eba` |
| H1_126_3 | Replacement | `20261008T192734-866ab4b3d7` | `20261008T174347-8fc8ed2441` | `b720eba` | `1ec5a69` |
| H1_126_4 | Replacement | `20261008T192737-45e578bd7c` | `20261008T174355-8d6580f98d` | `1ec5a69` | `71d53cc` |
| H2_4of6 | Replacement | `20261008T192740-f8be1b1ad3` | `20261008T174358-e5b5bd731e` | `71d53cc` | `26bf028` |
| H2_5of6 | Replacement | `20261008T192745-708215766a` | `20261008T174405-a2006cbd61` | `26bf028` | `1348f06` |
| Report | Replacement | `20261008T192750-922eb4e4b7` | `20261008T174417-e6157ee9c6` | `1348f06` | `22b6e31` |
| H1_252_3 | Repeat | `20261008T192753-ecbedef345` | `20261008T192727-e5e184b7db` | `22b6e31` | `0859cfd` |
| H1_252_4 | Repeat | `20261008T192757-ecb65a91e3` | `20261008T192731-0f8d083cb0` | `0859cfd` | `af1bd4d` |
| H1_126_3 | Repeat | `20261008T192801-cd2cf8da52` | `20261008T192734-866ab4b3d7` | `af1bd4d` | `5181bcc` |
| H1_126_4 | Repeat | `20261008T192804-5d7dda6b7e` | `20261008T192737-45e578bd7c` | `5181bcc` | `791c3a0` |
| H2_4of6 | Repeat | `20261008T192808-88c4261f87` | `20261008T192740-f8be1b1ad3` | `791c3a0` | `44f42ce` |
| H2_5of6 | Repeat | `20261008T192812-bf50777423` | `20261008T192745-708215766a` | `44f42ce` | `5d1fc57` |
| Report | Repeat | `20261008T192817-09e39bfc79` | `20261008T192750-922eb4e4b7` | `5d1fc57` | `f927314` |

Failure retained: `20261008T192545-3e84621fc4` (H1_252_3, parent `20261008T174340-dfb6a1c558`, source commit `bd71fc0`, journal commit `ad9ec2f`) failed before loading the vintage because its relative root resolved to an unexpected nested directory. No output artifact was frozen. Its original two records were transferred unchanged to the canonical journal. The first successful replacement above retries it using an absolute root.

Additional accounting: six successful bug-driven replacement calculations; six deterministic repeats (each listed separately above); one replacement report and one report repeat; one failed launch. These are fifteen additional attempts, thirty additional events, zero new candidates and zero independent replications. The journal contains 124 events overall, of which 58 are N4 events: twenty-eight completed N4 attempts and one failed N4 attempt. The original attempts remain in the journal; the failed attempt is not added to the six-configuration candidate count. No excluded H1/H2 performance quantity was shown.

## N5 runs, evaluation report and campaign

This section registers the procedure of D025 (specification: [N5 design](../docs/superpowers/specs/2026-10-09-n5-evaluation-design.md), sections 4, 5, 7, 9 and 11). It was written before any registered N5 run. As of 10 October 2026 the journal contains no N5 record, no N5 run or report has been executed, and no H1/H2 return, risk or utility figure has been computed or shown. The mechanics are described in [EXECUTION_MODEL.md](../EXECUTION_MODEL.md), section 9, and the commands in [REPRODUCIBILITY.md](../docs/REPRODUCIBILITY.md).

Purposes and files. `simulate ... --stage 5` records one of three new purposes, so that the N3 and N4 reports accept and reject exactly what they accepted and rejected before (D025, item 12). `candidate_ids` is the one provider name in the `started` and the terminal record, as in N3 and N4.

| Purpose | Providers | Window | Files |
|---|---|---|---|
| `N5 benchmark run` | B0, B1, B2, B3, REF_SPY | 2008-12-31 to 2022-12-30 | nine: the files of an N3 run |
| `N5 hypothesis run` | H1_252_3, H1_252_4, H1_126_3, H1_126_4, H2_4of6, H2_5of6 | 2008-12-31 to 2022-12-30 | ten: the nine files of an N4 run plus `metrics.json` |
| `N5 hypothesis run` | H1_252_3, the P_A1 comparator | 2013-12-31 to 2022-12-30 | ten, with the walk-forward period list |
| `N5 policy run` | P_A1 | 2013-12-31 to 2022-12-30 | eleven: the ten files plus `selection.json` |
| `N5 evaluation report` | the thirteen runs | walk-forward period 2014-2022 | `evaluation.json` and `evaluation.md` |

The N5 runs freeze `metrics.json` for the hypothesis and policy kinds; the deferral of metrics to N5 in the N4 section above therefore ends with them. All runs use the approved vintage and the main scenario (cost 0.001, lag 1, reserve 0.01, proxy 10 calendar days, initial cash 100000).

Seeds. The `started` and the terminal record of the P_A1 run hold the seed 20261007 (the selection stability bootstrap), and those of the evaluation report hold the seed 20261006 (the paired utility bootstrap). The benchmark and hypothesis runs keep `seed` null with the existing reason, because they use no random numbers.

Registered campaign (D025, item 17; specification section 9). Each step is on a clean tree, with the new journal lines committed before the next step, and every command uses an absolute `--root`:

1. thirteen `simulate --stage 5` runs: the five benchmarks, the six configurations, P_A1 and the P_A1 comparator;
2. `evaluate` over the thirteen run directories;
3. a repeat of each of the thirteen runs with `--parent` set to its first run, then a repeat of the report over the thirteen repeat directories with `--parent` set to the first report;
4. a comparison of the manifest `files` dictionaries for all fourteen pairs, and of the shared files against the N3 and N4 references (the 45 hashes of the first N3 benchmark runs and the shared files of the six N4 replacement runs `20261008T192727-e5e184b7db`, `20261008T192731-0f8d083cb0`, `20261008T192734-866ab4b3d7`, `20261008T192737-45e578bd7c`, `20261008T192740-f8be1b1ad3` and `20261008T192745-708215766a`).

If every attempt succeeds, the campaign consists of thirteen runs, the report, thirteen repeats and the repeat report: 28 attempts. Each successful attempt writes a `started` and a terminal record, so the campaign adds 56 journal events. A failed or `invariants_failed` run or report is additional and stays in the journal. A mismatch in a file that N3 or N4 already froze, or an unequal `files` dictionary, stops the campaign (D023, item 10). Failure messages of hypothesis and policy runs and the errors of the evaluation report stay value-free (D025, item 16). Changes to `src` after the first registered N5 run are bug fixes only, never motivated by a figure; each requires rerunning all thirteen runs on the new tree with `--parent` set to the previous run, followed by a new report, and every such attempt is disclosed (D025, item 16; D023, item 8). A change of rule, candidate, window or period after the figures are shown is a new attempt with its own decision record.

Attempt accounting for N5 (D025, item 18; specification section 11). The following lines are separate and are not summed as independent experiments:

- Candidates: seven, the six configurations of N4 and the policy P_A1.
- Registered N5 runs: thirteen, with thirteen repeats and two evaluation reports (the first report and its repeat); 28 attempts and 56 events if all succeed. None has been executed.
- Reruns after bug fixes: zero at the time of writing. Any rerun that occurs is added here with its run ids.
- The P_A1 comparator run (H1_252_3 from 2013-12-31): one of the thirteen runs; it is not a candidate.
- The in-memory validation simulations of P_A1: four candidates for each of the nine selection years; they are part of the policy and are not journaled attempts.
- The real-vintage tests: not attempts. They print only counts, flags and maximum differences until the freeze.
- Attempts outside the journal: the owner's statement of 9 October 2026, as given, is that the owner has become familiar with the hypotheses and has reviewed the work a small number of times, and declines to count views and reviews individually. Prior exposure to H1/H2 is therefore non-zero and unquantified (this supersedes, for the purposes of N5, the statement of 6 October 2026 without editing it). No manual parameter or period change is reported. The reconstruction of the number of attempts that the section "Requirements for later research stages" asks for is therefore not a count; DSR and PBO are not implemented, and every N5 document describes the multiple-testing caveat as unresolved in size and the inferential figures as exploratory on familiar history. The statement is in [docs/n5/ATTEMPT_ACCOUNTING.md](../docs/n5/ATTEMPT_ACCOUNTING.md).
- Consequence for the Holm family: the Holm adjustment of the six-member family does not restore independence on this history (protocol line 163), so the adjusted p values and the intervals are exploratory figures on familiar history. The owner approved the specification, including this statement, on 9 October 2026.

Status. `evaluated_walk_forward` replaces `computed_not_evaluated` for a configuration, and applies to P_A1, when the completion conditions of specification section 1 items 1 to 5 hold (the benchmarks and the six configurations rerun on the frozen N5 code with every shared file unchanged; a frozen `metrics.json` for the six configurations and P_A1; a complete selection log for P_A1; one registered evaluation report; and a repeat of every run and of the report that reproduces the manifest `files` dictionaries) and no decision under protocol section 13 exists. The status says that walk-forward figures exist; it does not say that a configuration is useful or rejected. The journal gets no new event type; the evidence is the existing records (D025, item 19). The current status of the six configurations is `computed_not_evaluated`, and P_A1 has no status because it has not been run. The scenarios of protocol section 12, the reserved period 2023-2025, the selection of P_A1 for 2023 and the section 13 decisions belong to N6 (D025, item 20).
