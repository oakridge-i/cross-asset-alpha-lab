# Reproducibility

The repository implements N1 data preparation, the N2 account and execution engine, the N3 benchmark providers, metrics and report, the N4 providers and report for the six H1/H2 configurations, and the N5 code (the adaptive policy P_A1, the metrics of hypothesis and policy runs, the inference functions and the evaluation report). Reproduction requires the locked Python environment and, for offline data replay and for the N2 run, the corresponding local source, evidence, correction, and derived snapshots. Those data are excluded from Git; cloning the repository alone does not provide them. Benchmark reproduction is available: the registered N3 runs of B0-B3 and REF_SPY and their report are listed below and in the [N3 report](n3/N3_REPORT.md). The six registered N4 runs of H1/H2, their repeats and their reports were executed on 8 October 2026 on the branch `claude/n4-hypotheses` and are listed in the N4 section below and in the [N4 report](n4/N4_REPORT.md). They publish no returns; the N2 run uses a test weight provider and publishes no returns either. The thirteen N5 runs, the evaluation report and their repeats were executed on 10 October 2026 on the branch `claude/n5-evaluation`; the commands, run ids and comparison are in the section "N5 evaluation runs: executed receipt" at the end of this document, and the figures are in the [N5 report](n5/N5_REPORT.md).

The [English documentation edition](DOCUMENTATION_EDITION.md) registers current document hashes separately. N0 receipts and the original experiment records are historical evidence; they do not certify the bytes of the rewritten documentation. See [HISTORY_REWRITE.md](HISTORY_REWRITE.md) for old-to-published commit mappings.

## Environment and verification

Run from the repository root. The recorded environment was Python 3.14.0. `requirements.lock` pins all packages, including pip. The project requires Python 3.14; the package is used from `src` rather than installed. Pytest obtains that path from `pyproject.toml`; the CLI requires `PYTHONPATH=src`.

PowerShell adaptation of the recorded Git Bash setup and checks below. This shell adaptation was not executed as part of the documentation update:

```powershell
py -3.14 -m venv .venv
.venv/Scripts/python -m pip install -r requirements.lock
.venv/Scripts/python -m pip check
.venv/Scripts/python -m pytest -q -p no:cacheprovider --basetemp="$env:TEMP/alpha-lab-pytest"
$env:PYTHONPATH = 'src'
.venv/Scripts/python -m alpha_lab --help
git status --short --branch
git log -1 --oneline
```

Use a fresh temporary directory for `--basetemp`: pytest may remove an existing directory supplied there. These commands describe the supported setup; historical pass counts below are not a fresh run on this documentation edition.

A clean temporary environment outside the repository was tested on 6 October 2026 in Git Bash. After installation, `pip freeze --all` matched `requirements.lock`, `pip check` passed, and 66 tests passed at that checkpoint. `PYTHONPATH=src python -m alpha_lab --help` worked; omitting that path produced `No module named alpha_lab`. Later recorded checkpoints reached 122, 130, 145, and 149 tests on the data pipeline, and 265 tests with the N2 engine; [STATUS.md](../STATUS.md) identifies their commits and reviews.

Equivalent original Git Bash commands:

```bash
py -3.14 -m venv .venv
.venv/Scripts/python -m pip install -r requirements.lock
.venv/Scripts/python -m pip check
.venv/Scripts/python -m pytest -q -p no:cacheprovider --basetemp=$TEMP/n1pt
PYTHONPATH=src .venv/Scripts/python -m alpha_lab --help
```

The original working environment included `openpyxl 3.1.5` and `et_xmlfile 2.0.0`, installed for an early uncommitted script. Committed code does not import them and the lock excludes them. They were removed on 6 October 2026 using `pip uninstall -y openpyxl et_xmlfile`; afterward `pip freeze --all` matched the lock. N1 runs beginning with `20261006T103809-a4a22ec667` before that removal retain those packages in their environment hashes.

## Approved-vintage replay

D020 approves only `data/derived/20261006T172442-80ef993493` with its `corrections.json`. The original Yahoo acquisition is `20261006T103809-a4a22ec667`, through 2026-10-05. It was not reacquired during blocker resolution.

With the local artifacts present, this command performs offline replay:

```powershell
$env:PYTHONPATH = 'src'
.venv/Scripts/python -m alpha_lab replay data/derived/20261006T172442-80ef993493 --root . --parent 20261006T172442-80ef993493
```

Replay verifies and reconstructs inputs without network access. It creates a new run and appends journal events; it is not a read-only inspection command. Preserve the resulting run ID and journal changes. Repeating the same inputs is not an independent economic experiment. The historical records include replay equality and direct offline reconstruction of all 13 files by SHA-256, as detailed in STATUS.md and the review reports.

## N2 execution run

The `simulate` command applies the N2 engine to the approved vintage. It was verified by the registered runs of 7 October 2026 on `data/derived/20261006T172442-80ef993493`, window 2007-05-31 to 2022-12-30; results and invariants are in the [N2 report](n2/N2_REPORT.md), and the model is in [EXECUTION_MODEL.md](../EXECUTION_MODEL.md).

```bash
PYTHONPATH=src .venv/Scripts/python -m alpha_lab simulate data/derived/20261006T172442-80ef993493 --provider invariant_rotation --start 2007-05-31 --end 2022-12-30 --root .
```

The run needs the local approved vintage and a clean working tree. It appends journal events and writes its result to `data/runs/<run_id>`, which is excluded from Git. For a repeat, add `--parent <run id of the previous run>` after committing the previous run's journal lines, so that the repeat starts on a clean tree. The provider `invariant_rotation` is a mechanics test, not a strategy. An `invariants_failed` run prints its directory and exits with code 3 (D022, item 1); `audit` exits with code 3 on `quality_failed` in the same way. A caller should still read `passed` in `invariants.json` or the journal status. The command is not part of the N1 replay and the `data/runs` outputs are not committed.

## N3 benchmark runs

The N3 runs use the approved vintage, the locked environment of `requirements.lock` and a clean working tree. The interpreter is `.venv/Scripts/python` in a checkout that has its own environment; the registered N3 runs share one environment manifest, which the report checks. All twelve registered N3 runs journal the same environment manifest SHA-256 `5226dc9b0f21363873eb9a8420891733bbad1bc6c536262a3341eead520ce773` (created from `requirements.lock`), so a reproduction can compare its own environment hash with it. All five runs and the report must come from the same environment and from commits with the same `src` tree (D022, item 16). Before the first run, `provenance.verify` on `data/derived/20261006T172442-80ef993493` and its manifest SHA-256 `f89346107cf7da6ca052693d188b8a576a08d42024c86865b0a42a63b1d294f2` must match. The window is 2008-12-31 to 2022-12-30 in the main scenario (cost 0.001, lag 1, reserve 0.01, proxy 10, initial cash 100000); the first decision is the close of 2008-12-31 (D022, item 6).

```bash
PYTHONPATH=src .venv/Scripts/python -m alpha_lab simulate data/derived/20261006T172442-80ef993493 --provider B0 --start 2008-12-31 --end 2022-12-30 --root .
git add experiments/EXPERIMENT_LOG.jsonl
git commit -m "journal: B0 benchmark run"
PYTHONPATH=src .venv/Scripts/python -m alpha_lab simulate data/derived/20261006T172442-80ef993493 --provider B1 --start 2008-12-31 --end 2022-12-30 --root .
git add experiments/EXPERIMENT_LOG.jsonl
git commit -m "journal: B1 benchmark run"
PYTHONPATH=src .venv/Scripts/python -m alpha_lab simulate data/derived/20261006T172442-80ef993493 --provider B2 --start 2008-12-31 --end 2022-12-30 --root .
git add experiments/EXPERIMENT_LOG.jsonl
git commit -m "journal: B2 benchmark run"
PYTHONPATH=src .venv/Scripts/python -m alpha_lab simulate data/derived/20261006T172442-80ef993493 --provider B3 --start 2008-12-31 --end 2022-12-30 --root .
git add experiments/EXPERIMENT_LOG.jsonl
git commit -m "journal: B3 benchmark run"
PYTHONPATH=src .venv/Scripts/python -m alpha_lab simulate data/derived/20261006T172442-80ef993493 --provider REF_SPY --start 2008-12-31 --end 2022-12-30 --root .
git add experiments/EXPERIMENT_LOG.jsonl
git commit -m "journal: REF_SPY benchmark run"
PYTHONPATH=src .venv/Scripts/python -m alpha_lab report --runs data/runs/<B0 dir> data/runs/<B1 dir> data/runs/<B2 dir> data/runs/<B3 dir> data/runs/<REF_SPY dir> --root .
git add experiments/EXPERIMENT_LOG.jsonl
git commit -m "journal: benchmark report"
```

Each `simulate` prints `data/runs/<run_id>`; substitute the five printed directories in `report`. The commands are shown as a sequence, not an unattended batch: each run must start on a clean tree and the journal lines of the previous run are committed first, because the report rejects a run whose records have `dirty_tree` true or no `git_sha`. A run started on a dirty tree is rejected by the report and remains in the append-only journal. A command that exits with code 3 has frozen its result and journaled `invariants_failed`; it stays in the journal and its cause is fixed before a repeat with `--parent`.

A repeat uses `--parent <run id of the first run>` for each of the five runs and for the report. A repeated benchmark run and a repeated report are compared by the `files` dictionaries of their `manifest.json` (per-file SHA-256), not by the manifest bytes, which contain run identifiers. The report files `benchmarks.json` and `benchmarks.md` in `data/reports/<run_id>/` contain no run id. The `--expected-sha256` option of `simulate` and `report` exists for tests on synthetic vintages; registered runs use the default, the approved hash. The registered runs and their results are listed below.

The registered N3 runs of 7 October 2026 (results, invariants and counts are in the [N3 report](n3/N3_REPORT.md)):

| | First run | Repeat (parent: first run) |
|---|---|---|
| B0 | 20261007T180004-12aae80084 | 20261007T200819-ff620c4546 |
| B1 | 20261007T180018-b6c98bd0aa | 20261007T200822-68dc462b5f |
| B2 | 20261007T180026-dffe07154c | 20261007T200827-b8f9da8b3f |
| B3 | 20261007T180033-bba99392df | 20261007T200831-bcab64c3eb |
| REF_SPY | 20261007T180039-be7dd8f43a | 20261007T200835-3df74a38e0 |
| report | 20261007T200805-c75aa41980 | 20261007T200847-cf60a2b2d9 |

For all five benchmark pairs the `files` dictionaries of the manifests are identical, and so are those of the two reports. The result directories `data/runs` and `data/reports` are not in Git.

## N4 hypothesis runs

The registered procedure of D023, item 8 was executed on 8 October 2026 from the root of the branch's working copy (the branch `claude/n4-hypotheses`, a Git worktree of the project) with `../../.venv/Scripts/python`. The commands in the blocks below show that form. They were verified by these runs: the `simulate` command for the six providers, the `hypothesis-report` command over the six run directories, the repeats with `--parent` and the repeat of the report. The project-root form (`.venv/Scripts/python`, after the branch is merged) has not been executed. The run ids, journal commits, git SHAs and manifest hashes are in the [N4 report](n4/N4_REPORT.md); the first-run ids are:

| | First run | Repeat (parent: first run) | Journal commits (first, repeat) |
|---|---|---|---|
| H1_252_3 | 20261008T174218-4053e6ea58 | 20261008T174340-dfb6a1c558 | ae629c4, 6244b39 |
| H1_252_4 | 20261008T174253-cbb9ce2219 | 20261008T174343-bda6d756d5 | 23a157c, 85cf34a |
| H1_126_3 | 20261008T174300-8531bbf3ae | 20261008T174347-8fc8ed2441 | 2d9f24a, 3d17051 |
| H1_126_4 | 20261008T174303-337a7c2114 | 20261008T174355-8d6580f98d | 73501bc, 52d5daf |
| H2_4of6 | 20261008T174309-3f0ab95aeb | 20261008T174358-e5b5bd731e | f857975, 9504121 |
| H2_5of6 | 20261008T174315-44f030c165 | 20261008T174405-a2006cbd61 | b938f40, d0de40d |
| report | 20261008T174328-e5860d5cf2 | 20261008T174417-e6157ee9c6 | 6498f44, f921b41 |

All fourteen records are `completed`. The `files` dictionaries of the manifests are identical for all seven pairs (the six configurations and the reports). The `data/runs` and `data/reports` directories are not in Git, and the diagnostics permitted by D023, item 6 are published in the N4 report. The `simulate` and `hypothesis-report` commands are also exercised by tests on synthetic vintages. The real-vintage tests were executed on the N4 branch before the runs: the independent recomputation of the H1/H2 target weights evaluates the providers at 168 decisions and computes no H1/H2 account or return, and the N3 regression reruns the benchmarks in memory and compares the 45 benchmark file hashes. Neither is journaled or an attempt (D023, item 10).

Conditions, as for N3: the approved vintage `data/derived/20261006T172442-80ef993493` passes `provenance.verify` and has manifest SHA-256 `f89346107cf7da6ca052693d188b8a576a08d42024c86865b0a42a63b1d294f2`; the environment manifest SHA-256 is `5226dc9b0f21363873eb9a8420891733bbad1bc6c536262a3341eead520ce773`, the value journaled by the N3 runs and by the N4 records; the full test suite passes (602 passed, 0 skipped, on `bbf7640` before the first run); and the working tree is clean before each step. The vintage was copied into `data/derived` of the working copy. The window is 2008-12-31 to 2022-12-30 in the main scenario (cost 0.001, lag 1, reserve 0.01, proxy 10, initial cash 100000), the defaults of the command. The parameters of the six configurations are fixed in the registry (D023, item 5). The `--expected-sha256` option of `simulate` and `hypothesis-report` exists for tests on synthetic vintages; registered runs and reports use the default, the approved hash. The results of the runs are stored in `data/runs/<run_id>`, which is read only by code (D023, item 6), and the commands print only that path.

```bash
PYTHONPATH=src ../../.venv/Scripts/python -m alpha_lab simulate data/derived/20261006T172442-80ef993493 --provider H1_252_3 --start 2008-12-31 --end 2022-12-30 --root .
git add experiments/EXPERIMENT_LOG.jsonl
git commit -m "chore: log N4 H1_252_3 run <run id>"
```

The same pair of commands (with its own provider name and run id) was executed for `H1_252_4`, `H1_126_3`, `H1_126_4`, `H2_4of6` and `H2_5of6`. Then:

```bash
PYTHONPATH=src ../../.venv/Scripts/python -m alpha_lab hypothesis-report --runs <six run dirs> --root .
git add experiments/EXPERIMENT_LOG.jsonl
git commit -m "chore: log N4 hypothesis report run <run id>"
```

Here `<six run dirs>` stands for the six directories `data/runs/<run id>` of the first runs. The commit subjects shown are the form used; the subjects of the repeat commits use the word "rerun" for the repeats with `--parent`.

Repeats. Each of the six runs is repeated with `--parent <run id of its first run>`, with the journal lines committed after each run, and the report is repeated over the six repeat directories with `--parent <run id of the first report>`:

```bash
PYTHONPATH=src ../../.venv/Scripts/python -m alpha_lab simulate data/derived/20261006T172442-80ef993493 --provider H1_252_3 --start 2008-12-31 --end 2022-12-30 --root . --parent <first run id of H1_252_3>
PYTHONPATH=src ../../.venv/Scripts/python -m alpha_lab hypothesis-report --runs <six repeat dirs> --root . --parent <first report run id>
```

Comparison. Each repeat is compared with its first run, and the repeated report with the first report, by the `files` dictionaries of their `manifest.json` (per-file SHA-256), not by manifest bytes, which contain run identifiers. All seven pairs must be equal. The registered check prints one boolean and opens no result file:

```bash
python -c "import json,sys; a,b=(json.load(open(p+'/manifest.json'))['files'] for p in sys.argv[1:3]); print(a==b)" data/runs/<first dir> data/runs/<repeat dir>
```

The comparison command was run once on the first and repeated B0 runs of N3, with the result `True`. The seven N4 pairs were compared with the following script, executed from the root of the branch's working copy as `PYTHONPATH=src ../../.venv/Scripts/python - <<'EOF' ... EOF`. It differs from the registered one-boolean form above in that it verifies both manifests with `provenance.verify` and prints the number of files. It printed `equal` for all seven names, with 9 files for each pair of runs and 2 files for the pair of reports:

```python
from pathlib import Path
from alpha_lab.provenance import verify
pairs = [('runs','20261008T174218-4053e6ea58','20261008T174340-dfb6a1c558','H1_252_3'),
         ('runs','20261008T174253-cbb9ce2219','20261008T174343-bda6d756d5','H1_252_4'),
         ('runs','20261008T174300-8531bbf3ae','20261008T174347-8fc8ed2441','H1_126_3'),
         ('runs','20261008T174303-337a7c2114','20261008T174355-8d6580f98d','H1_126_4'),
         ('runs','20261008T174309-3f0ab95aeb','20261008T174358-e5b5bd731e','H2_4of6'),
         ('runs','20261008T174315-44f030c165','20261008T174405-a2006cbd61','H2_5of6'),
         ('reports','20261008T174328-e5860d5cf2','20261008T174417-e6157ee9c6','report')]
for kind, a, b, name in pairs:
    ma, mb = (verify(Path('data')/kind/x) for x in (a, b))
    print(name, 'equal' if ma['files'] == mb['files'] else 'differs', len(ma['files']), 'files')
```

The report files `hypotheses.json` and `hypotheses.md` in `data/reports/<run_id>/` contain no run id.

A run that exits with code 3 has frozen its result and journaled `invariants_failed`; a failed run or report stays in the journal. Changes to `src` after the first registered run are bug fixes only. Each requires a rerun of all six configurations on the new tree, each with `--parent` set to its previous run, and a new report, because the report requires one `src` tree for all runs; a fix that changes the output of a provider increments its version (D023, item 8). A failed hypothesis run prints an error whose message is withheld (`RuntimeError: ... message withheld under the N4 viewing restriction`); the cause is diagnosed by reproduction on synthetic data. During the original campaign, no run or report failed and no change to `src` was made between its first registered run and its publication, so the failure and rerun rule was not applied then. The subsequent report-validation correction (D024) requires a replacement campaign under D023, item 8. That campaign and its repeats are complete on committed clean source; the commands and comparisons above remain the original campaign recipe, while the D024 receipts and absolute-root command form below describe the corrected-source campaign. The conditions of D023, item 9 are met and the status of the six configurations is `computed_not_evaluated`. PR #1 merged the branch into `main` on 8 October 2026. The immutable N4 directories `data/runs` and `data/reports` remain in the original N4 worktree; artifact transfer to the primary checkout has not been performed. Reproduction from that checkout requires access to those same frozen directories. The existing worktree remains available for reproduction.

## Historical blocker-resolution sequence

The commands below preserve the 6 October 2026 acquisition and derivation recipe. They are historical commands with fixed parent and input IDs, rather than a script to paste as an unattended batch. New runs create new IDs; replace downstream paths with those actual outputs. The sequence is dependency-ordered. Journal changes were committed between the recorded steps so the next step started on a clean tree.

The local DBC file `data/manual/dbc-invesco-distribution.json` must be present. Its expected SHA-256 is recorded in `configs/n1_evidence.json` and D017. Capturing or distributing that issuer file is not covered by the repository's MIT license.

```bash
PYTHONPATH=src .venv/Scripts/python -m alpha_lab evidence --root . --parent 20261006T122017-3048321309
PYTHONPATH=src .venv/Scripts/python -m alpha_lab reconcile data/snapshots/20261006T103809-a4a22ec667 data/evidence/20261006T172354-1c0a8ca2d8 --root . --parent 20261006T122119-c6bfb5c69b
PYTHONPATH=src .venv/Scripts/python -m alpha_lab corrections data/reconciliation/20261006T172415-ce65adb53e --root . --parent 20261006T172415-ce65adb53e
PYTHONPATH=src .venv/Scripts/python -m alpha_lab audit data/snapshots/20261006T103809-a4a22ec667 --payable data/corrections/20261006T172434-fbb5c9f554/payable.json --corrections data/corrections/20261006T172434-fbb5c9f554/corrections.json --root . --parent 20261006T122144-73228a71eb
PYTHONPATH=src .venv/Scripts/python -m alpha_lab reconcile data/snapshots/20261006T103809-a4a22ec667 data/evidence/20261006T172354-1c0a8ca2d8 --corrections data/corrections/20261006T172434-fbb5c9f554/corrections.json --root . --parent 20261006T172415-ce65adb53e
PYTHONPATH=src .venv/Scripts/python -m alpha_lab replay data/derived/20261006T172442-80ef993493 --root . --parent 20261006T172442-80ef993493
```

`acquire` and network-backed `evidence` acquisition create a new vintage: suppliers may revise content and response hashes. A new vintage is not automatically approved by D020; reconciliation, QA, and a new decision are required. The `invesco_json` source reads the declared local file without network access.

## Earlier N1 sequence and schema limitation

These commands record the pre-resolution runs exactly as performed:

```bash
PYTHONPATH=src .venv/Scripts/python -m alpha_lab evidence --root . --parent 20261006T103625-5202b05cbc
PYTHONPATH=src .venv/Scripts/python -m alpha_lab reconcile data/snapshots/20261006T103809-a4a22ec667 data/evidence/20261006T122017-3048321309 --root . --parent 20261006T104437-36dd8f9b4a
PYTHONPATH=src .venv/Scripts/python -m alpha_lab audit data/snapshots/20261006T103809-a4a22ec667 --payable data/reconciliation/20261006T122119-c6bfb5c69b/payable.json --root . --parent 20261006T104336-dff9099c6b
PYTHONPATH=src .venv/Scripts/python -m alpha_lab replay data/derived/20261006T122144-73228a71eb --root . --parent 20261006T122144-73228a71eb
```

Current code does not reproduce the older derived snapshot `20261006T122144-73228a71eb`: the normalized schema gained `dividend_basis` and `dividend_correction_source`, and derived snapshots gained `corrections.json`. Exact replay of the old snapshot is recorded as `20261006T131812-09887a01da` on historical commit `977eaf6`. Use the mapped historical version and its environment when investigating that record. This snapshot is not approved for N2.

N1 runs begin with `started` and terminate with `completed`, `quality_failed`, or `failed`, according to the operation's outcome. A successfully written reconciliation can still contain unresolved events. See the [journal rules](../experiments/README.md).

## N0 diagnostics and historical receipt

The standard-library N0 probe retrieves fresh source responses and prints JSON:

```powershell
python -X utf8 docs/n0/probe_sources.py
```

Supplier responses and their hashes may change. `--output` accepts a new path for a new receipt; do not overwrite the existing receipt. This is a source diagnostic, not reproduction of the approved N1 vintage.

The original no-write verifier command was:

```powershell
python -X utf8 docs/n0/verify_n0.py --no-write
```

It checks links, exact original copies, manifest restrictions, an empty N0 journal, the local AAPL state, and illustrative formula arithmetic. It does not test a portfolio engine. Its 35/35 receipt applies to the original N0 commit and document bytes. The current journal is no longer empty, editorial files have changed, and expected original/sibling files may be absent. In a worktree the script previously looked for `quant-research-plan` beside the worktree root and raised `FileNotFoundError`. It is therefore retained as a historical verifier, not a passing verification command for the current repository. Moving the project to another machine also requires access to the original local source directories to reproduce its AAPL checks.

## Interpretation and rights

The corrected vintage passed the defined N1 readiness rule: both split bases confirmed, all ten ETFs confirmed or confirmed_no_distributions, technical QA passed, and replay equal. It does not certify all prices or contemporaneous availability. Actual payable dates exist only for issuer-matched events. D013-D019 disclose source precision, corrections, revised history, GLD documentary qualifications, and the DBC coverage gap.

Raw data, local issuer captures, and environments are excluded from Git. The [MIT license](../LICENSE) covers code and documentation only. Library terms do not establish market-data rights; external distribution or paid-source procurement requires separate authorization.

## D024 corrected-source campaign: executed receipt

Correction commit `bd71fc0`; source tree `16ffaf71b09c540cdc094121d040deacdeb3dab9`; last journal commit `f927314`. Run IDs, parents, source commits and journal commits are listed in the [N4 report](n4/N4_REPORT.md). The initial failed relative-root launch and its retained records are disclosed there. The fourteen successful commands used an absolute worktree root and absolute report-input directories, avoiding that resolution failure. The local root is represented below by `$n4Root`; run from the N4 worktree. Each line is historical evidence; a journal-only commit was made between adjacent command lines. These are not an unattended batch.

```powershell
$env:PYTHONPATH='src'
$env:PYTHONIOENCODING='utf-8'
$n4Root=(Get-Location).Path
& ../../.venv/Scripts/python.exe -m alpha_lab simulate data/derived/20261006T172442-80ef993493 --provider H1_252_3 --start 2008-12-31 --end 2022-12-30 --root $n4Root --parent 20261008T192545-3e84621fc4
& ../../.venv/Scripts/python.exe -m alpha_lab simulate data/derived/20261006T172442-80ef993493 --provider H1_252_4 --start 2008-12-31 --end 2022-12-30 --root $n4Root --parent 20261008T174343-bda6d756d5
& ../../.venv/Scripts/python.exe -m alpha_lab simulate data/derived/20261006T172442-80ef993493 --provider H1_126_3 --start 2008-12-31 --end 2022-12-30 --root $n4Root --parent 20261008T174347-8fc8ed2441
& ../../.venv/Scripts/python.exe -m alpha_lab simulate data/derived/20261006T172442-80ef993493 --provider H1_126_4 --start 2008-12-31 --end 2022-12-30 --root $n4Root --parent 20261008T174355-8d6580f98d
& ../../.venv/Scripts/python.exe -m alpha_lab simulate data/derived/20261006T172442-80ef993493 --provider H2_4of6 --start 2008-12-31 --end 2022-12-30 --root $n4Root --parent 20261008T174358-e5b5bd731e
& ../../.venv/Scripts/python.exe -m alpha_lab simulate data/derived/20261006T172442-80ef993493 --provider H2_5of6 --start 2008-12-31 --end 2022-12-30 --root $n4Root --parent 20261008T174405-a2006cbd61
& ../../.venv/Scripts/python.exe -m alpha_lab hypothesis-report --runs "$n4Root/data/runs/20261008T192727-e5e184b7db" "$n4Root/data/runs/20261008T192731-0f8d083cb0" "$n4Root/data/runs/20261008T192734-866ab4b3d7" "$n4Root/data/runs/20261008T192737-45e578bd7c" "$n4Root/data/runs/20261008T192740-f8be1b1ad3" "$n4Root/data/runs/20261008T192745-708215766a" --root $n4Root --parent 20261008T174417-e6157ee9c6
& ../../.venv/Scripts/python.exe -m alpha_lab simulate data/derived/20261006T172442-80ef993493 --provider H1_252_3 --start 2008-12-31 --end 2022-12-30 --root $n4Root --parent 20261008T192727-e5e184b7db
& ../../.venv/Scripts/python.exe -m alpha_lab simulate data/derived/20261006T172442-80ef993493 --provider H1_252_4 --start 2008-12-31 --end 2022-12-30 --root $n4Root --parent 20261008T192731-0f8d083cb0
& ../../.venv/Scripts/python.exe -m alpha_lab simulate data/derived/20261006T172442-80ef993493 --provider H1_126_3 --start 2008-12-31 --end 2022-12-30 --root $n4Root --parent 20261008T192734-866ab4b3d7
& ../../.venv/Scripts/python.exe -m alpha_lab simulate data/derived/20261006T172442-80ef993493 --provider H1_126_4 --start 2008-12-31 --end 2022-12-30 --root $n4Root --parent 20261008T192737-45e578bd7c
& ../../.venv/Scripts/python.exe -m alpha_lab simulate data/derived/20261006T172442-80ef993493 --provider H2_4of6 --start 2008-12-31 --end 2022-12-30 --root $n4Root --parent 20261008T192740-f8be1b1ad3
& ../../.venv/Scripts/python.exe -m alpha_lab simulate data/derived/20261006T172442-80ef993493 --provider H2_5of6 --start 2008-12-31 --end 2022-12-30 --root $n4Root --parent 20261008T192745-708215766a
& ../../.venv/Scripts/python.exe -m alpha_lab hypothesis-report --runs "$n4Root/data/runs/20261008T192753-ecbedef345" "$n4Root/data/runs/20261008T192757-ecb65a91e3" "$n4Root/data/runs/20261008T192801-cd2cf8da52" "$n4Root/data/runs/20261008T192804-5d7dda6b7e" "$n4Root/data/runs/20261008T192808-88c4261f87" "$n4Root/data/runs/20261008T192812-bf50777423" --root $n4Root --parent 20261008T192750-922eb4e4b7
```

Verification used `alpha_lab.provenance.verify` for every new frozen directory, compared the seven replacement/repeat `files` dictionaries, and compared all seven replacement outputs to the original repeat set. All matched. The original 94-row journal byte prefix was preserved; the total is 124 rows after retaining one failed launch and fourteen successful attempts. The source and environment stayed fixed, all financial invariant flags passed, and no H1/H2 performance metric was opened. Repetition remains deterministic reproduction, not an independent experiment.

## N5 evaluation runs: executed receipt

Status as of 10 October 2026: the registered N5 campaign of D025, item 17 and of the [N5 design](superpowers/specs/2026-10-09-n5-evaluation-design.md), section 9 was executed on 10 October 2026 from the root of the branch's working copy (branch `claude/n5-evaluation`, a Git worktree of the project, which reaches the project's environment through the relative path `../../.venv`). All 28 attempts (thirteen runs, the evaluation report, thirteen repeats and the repeat report) completed with exit code 0 and wrote a `started` and a `completed` journal record each (56 records); no attempt failed, and no `src` change was made during the campaign. The git SHAs, journal commits and manifest hashes of every attempt, the reproducibility result and the figures of the first report are in the [N5 report](n5/N5_REPORT.md). The project-root form of the commands (`.venv/Scripts/python`, after the branch is merged) has not been executed. The directories `data/runs` and `data/reports` are not in Git.

Conditions, as met before the first run: the freeze of D025, item 16 (commit `a2453b8`, `src` tree `058c72a492f78aa30f8defecbfab397eee37be96`, full test suite 766 passed and 0 skipped on a clean tree, whole-branch review without a critical or important finding) was recorded in [STATUS.md](../STATUS.md) and D025 by commit `db43fb4`, the commit from which the first run started. The approved vintage `data/derived/20261006T172442-80ef993493` has manifest SHA-256 `f89346107cf7da6ca052693d188b8a576a08d42024c86865b0a42a63b1d294f2`; the environment manifest SHA-256 journaled by every N5 record is `5226dc9b0f21363873eb9a8420891733bbad1bc6c536262a3341eead520ce773`. The five first N3 benchmark runs and the six N4 replacement runs that the report compares with were present in `data/runs` of the working copy and pass `provenance.verify`; they were read by code only. Each step started on a clean tree. The window of the benchmark and configuration runs is 2008-12-31 to 2022-12-30 and the window of P_A1 and its comparator is 2013-12-31 to 2022-12-30, in the main scenario (cost 0.001, lag 1, reserve 0.01, proxy 10, initial cash 100000), the defaults of the command; the journaled configuration of each run records its provider, window, vintage hash, scenario and initial cash.

Commands as executed. Every attempt was run from the root of the working copy in the form `PYTHONIOENCODING=utf-8 PYTHONPATH=src ../../.venv/Scripts/python -m alpha_lab <command> --root <ROOT>`, where `<ROOT>` stands for the absolute path of the working copy (`PYTHONIOENCODING=utf-8` because that path contains non-ASCII characters). Before each attempt the working tree was checked to be clean and the Git author e-mail was checked; after each attempt the new journal lines were committed with the subject `research: register N5 campaign step <k> of 28 (<label>)`, so that the next attempt started on a clean tree. The attempts were not an unattended batch. The 28 commands, in the order executed (the provider, window, parent and report inputs of each agree with the configuration journaled in its `started` record; the journal records the report inputs as `data/runs/<run id>`):

```bash
# step 1 (B0)
PYTHONIOENCODING=utf-8 PYTHONPATH=src ../../.venv/Scripts/python -m alpha_lab simulate data/derived/20261006T172442-80ef993493 --provider B0 --start 2008-12-31 --end 2022-12-30 --stage 5 --root <ROOT>
# step 2 (B1)
PYTHONIOENCODING=utf-8 PYTHONPATH=src ../../.venv/Scripts/python -m alpha_lab simulate data/derived/20261006T172442-80ef993493 --provider B1 --start 2008-12-31 --end 2022-12-30 --stage 5 --root <ROOT>
# step 3 (B2)
PYTHONIOENCODING=utf-8 PYTHONPATH=src ../../.venv/Scripts/python -m alpha_lab simulate data/derived/20261006T172442-80ef993493 --provider B2 --start 2008-12-31 --end 2022-12-30 --stage 5 --root <ROOT>
# step 4 (B3)
PYTHONIOENCODING=utf-8 PYTHONPATH=src ../../.venv/Scripts/python -m alpha_lab simulate data/derived/20261006T172442-80ef993493 --provider B3 --start 2008-12-31 --end 2022-12-30 --stage 5 --root <ROOT>
# step 5 (REF_SPY)
PYTHONIOENCODING=utf-8 PYTHONPATH=src ../../.venv/Scripts/python -m alpha_lab simulate data/derived/20261006T172442-80ef993493 --provider REF_SPY --start 2008-12-31 --end 2022-12-30 --stage 5 --root <ROOT>
# step 6 (H1_252_3)
PYTHONIOENCODING=utf-8 PYTHONPATH=src ../../.venv/Scripts/python -m alpha_lab simulate data/derived/20261006T172442-80ef993493 --provider H1_252_3 --start 2008-12-31 --end 2022-12-30 --stage 5 --root <ROOT>
# step 7 (H1_252_4)
PYTHONIOENCODING=utf-8 PYTHONPATH=src ../../.venv/Scripts/python -m alpha_lab simulate data/derived/20261006T172442-80ef993493 --provider H1_252_4 --start 2008-12-31 --end 2022-12-30 --stage 5 --root <ROOT>
# step 8 (H1_126_3)
PYTHONIOENCODING=utf-8 PYTHONPATH=src ../../.venv/Scripts/python -m alpha_lab simulate data/derived/20261006T172442-80ef993493 --provider H1_126_3 --start 2008-12-31 --end 2022-12-30 --stage 5 --root <ROOT>
# step 9 (H1_126_4)
PYTHONIOENCODING=utf-8 PYTHONPATH=src ../../.venv/Scripts/python -m alpha_lab simulate data/derived/20261006T172442-80ef993493 --provider H1_126_4 --start 2008-12-31 --end 2022-12-30 --stage 5 --root <ROOT>
# step 10 (H2_4of6)
PYTHONIOENCODING=utf-8 PYTHONPATH=src ../../.venv/Scripts/python -m alpha_lab simulate data/derived/20261006T172442-80ef993493 --provider H2_4of6 --start 2008-12-31 --end 2022-12-30 --stage 5 --root <ROOT>
# step 11 (H2_5of6)
PYTHONIOENCODING=utf-8 PYTHONPATH=src ../../.venv/Scripts/python -m alpha_lab simulate data/derived/20261006T172442-80ef993493 --provider H2_5of6 --start 2008-12-31 --end 2022-12-30 --stage 5 --root <ROOT>
# step 12 (P_A1)
PYTHONIOENCODING=utf-8 PYTHONPATH=src ../../.venv/Scripts/python -m alpha_lab simulate data/derived/20261006T172442-80ef993493 --provider P_A1 --start 2013-12-31 --end 2022-12-30 --stage 5 --root <ROOT>
# step 13 (H1_252_3_WF)
PYTHONIOENCODING=utf-8 PYTHONPATH=src ../../.venv/Scripts/python -m alpha_lab simulate data/derived/20261006T172442-80ef993493 --provider H1_252_3 --start 2013-12-31 --end 2022-12-30 --stage 5 --root <ROOT>
# step 14 (evaluation)
PYTHONIOENCODING=utf-8 PYTHONPATH=src ../../.venv/Scripts/python -m alpha_lab evaluate --runs data/runs/20261010T090706-d2f7f13f1c data/runs/20261010T090711-a0a3b5a215 data/runs/20261010T090717-13ebf67877 data/runs/20261010T090724-a39e6c5baa data/runs/20261010T090732-dbf52ab9f8 data/runs/20261010T090737-2d652c2127 data/runs/20261010T090745-899d5a7136 data/runs/20261010T090752-9bd003f35b data/runs/20261010T090800-f78d0ee07b data/runs/20261010T090807-af398ad6af data/runs/20261010T090820-2da0674722 data/runs/20261010T090831-aeca348964 data/runs/20261010T090913-3da4aae83e --root <ROOT>
# step 15 (B0 repeat)
PYTHONIOENCODING=utf-8 PYTHONPATH=src ../../.venv/Scripts/python -m alpha_lab simulate data/derived/20261006T172442-80ef993493 --provider B0 --start 2008-12-31 --end 2022-12-30 --stage 5 --parent 20261010T090706-d2f7f13f1c --root <ROOT>
# step 16 (B1 repeat)
PYTHONIOENCODING=utf-8 PYTHONPATH=src ../../.venv/Scripts/python -m alpha_lab simulate data/derived/20261006T172442-80ef993493 --provider B1 --start 2008-12-31 --end 2022-12-30 --stage 5 --parent 20261010T090711-a0a3b5a215 --root <ROOT>
# step 17 (B2 repeat)
PYTHONIOENCODING=utf-8 PYTHONPATH=src ../../.venv/Scripts/python -m alpha_lab simulate data/derived/20261006T172442-80ef993493 --provider B2 --start 2008-12-31 --end 2022-12-30 --stage 5 --parent 20261010T090717-13ebf67877 --root <ROOT>
# step 18 (B3 repeat)
PYTHONIOENCODING=utf-8 PYTHONPATH=src ../../.venv/Scripts/python -m alpha_lab simulate data/derived/20261006T172442-80ef993493 --provider B3 --start 2008-12-31 --end 2022-12-30 --stage 5 --parent 20261010T090724-a39e6c5baa --root <ROOT>
# step 19 (REF_SPY repeat)
PYTHONIOENCODING=utf-8 PYTHONPATH=src ../../.venv/Scripts/python -m alpha_lab simulate data/derived/20261006T172442-80ef993493 --provider REF_SPY --start 2008-12-31 --end 2022-12-30 --stage 5 --parent 20261010T090732-dbf52ab9f8 --root <ROOT>
# step 20 (H1_252_3 repeat)
PYTHONIOENCODING=utf-8 PYTHONPATH=src ../../.venv/Scripts/python -m alpha_lab simulate data/derived/20261006T172442-80ef993493 --provider H1_252_3 --start 2008-12-31 --end 2022-12-30 --stage 5 --parent 20261010T090737-2d652c2127 --root <ROOT>
# step 21 (H1_252_4 repeat)
PYTHONIOENCODING=utf-8 PYTHONPATH=src ../../.venv/Scripts/python -m alpha_lab simulate data/derived/20261006T172442-80ef993493 --provider H1_252_4 --start 2008-12-31 --end 2022-12-30 --stage 5 --parent 20261010T090745-899d5a7136 --root <ROOT>
# step 22 (H1_126_3 repeat)
PYTHONIOENCODING=utf-8 PYTHONPATH=src ../../.venv/Scripts/python -m alpha_lab simulate data/derived/20261006T172442-80ef993493 --provider H1_126_3 --start 2008-12-31 --end 2022-12-30 --stage 5 --parent 20261010T090752-9bd003f35b --root <ROOT>
# step 23 (H1_126_4 repeat)
PYTHONIOENCODING=utf-8 PYTHONPATH=src ../../.venv/Scripts/python -m alpha_lab simulate data/derived/20261006T172442-80ef993493 --provider H1_126_4 --start 2008-12-31 --end 2022-12-30 --stage 5 --parent 20261010T090800-f78d0ee07b --root <ROOT>
# step 24 (H2_4of6 repeat)
PYTHONIOENCODING=utf-8 PYTHONPATH=src ../../.venv/Scripts/python -m alpha_lab simulate data/derived/20261006T172442-80ef993493 --provider H2_4of6 --start 2008-12-31 --end 2022-12-30 --stage 5 --parent 20261010T090807-af398ad6af --root <ROOT>
# step 25 (H2_5of6 repeat)
PYTHONIOENCODING=utf-8 PYTHONPATH=src ../../.venv/Scripts/python -m alpha_lab simulate data/derived/20261006T172442-80ef993493 --provider H2_5of6 --start 2008-12-31 --end 2022-12-30 --stage 5 --parent 20261010T090820-2da0674722 --root <ROOT>
# step 26 (P_A1 repeat)
PYTHONIOENCODING=utf-8 PYTHONPATH=src ../../.venv/Scripts/python -m alpha_lab simulate data/derived/20261006T172442-80ef993493 --provider P_A1 --start 2013-12-31 --end 2022-12-30 --stage 5 --parent 20261010T090831-aeca348964 --root <ROOT>
# step 27 (H1_252_3_WF repeat)
PYTHONIOENCODING=utf-8 PYTHONPATH=src ../../.venv/Scripts/python -m alpha_lab simulate data/derived/20261006T172442-80ef993493 --provider H1_252_3 --start 2013-12-31 --end 2022-12-30 --stage 5 --parent 20261010T090913-3da4aae83e --root <ROOT>
# step 28 (evaluation repeat)
PYTHONIOENCODING=utf-8 PYTHONPATH=src ../../.venv/Scripts/python -m alpha_lab evaluate --runs data/runs/20261010T091043-854900b5a7 data/runs/20261010T091046-24f1f2afc7 data/runs/20261010T091048-b223f5975e data/runs/20261010T091051-e79c88c3a0 data/runs/20261010T091054-53e8829580 data/runs/20261010T091056-79e7a8ffe3 data/runs/20261010T091059-b17280952a data/runs/20261010T091102-c4fae89b36 data/runs/20261010T091105-5dbd95499e data/runs/20261010T091108-629ba2c4f0 data/runs/20261010T091112-378ce2d464 data/runs/20261010T091116-4835a4063a data/runs/20261010T091131-75eab3df7b --parent 20261010T091002-0c84d411ed --root <ROOT>
```

Each step was followed by:

```bash
git add experiments/EXPERIMENT_LOG.jsonl
git commit -m "research: register N5 campaign step <k> of 28 (<label>)"
```

Steps 12 and 13 are the policy and its comparator, which start in cash on 2013-12-31. The `P_A1` run journals the seed 20261007 and computes the validation accounts of its nine selection years in memory; it recorded no fallback and no quality warning. Step 13 is the P_A1 comparator (labeled `H1_252_3_WF` in the report), a supplementary run of the provider H1_252_3 and not a new candidate (D025, item 2). Step 14 printed `data/reports/20261010T091002-0c84d411ed`, wrote `evaluation.json` and `evaluation.md` there and journaled the seed 20261006; it is the first moment at which an H1/H2 or P_A1 figure was shown (D025, item 16). Steps 15 to 27 repeat steps 1 to 13 with `--parent <run id of the first run>`, and step 28 repeats the report over the thirteen repeat directories with `--parent 20261010T091002-0c84d411ed`; it printed `data/reports/20261010T091133-9f91bb3c9c`. The last journal commit of the campaign is `7f6dac8`.

Run and report ids:

| | First run | Repeat (parent: first run) |
|---|---|---|
| B0 | 20261010T090706-d2f7f13f1c | 20261010T091043-854900b5a7 |
| B1 | 20261010T090711-a0a3b5a215 | 20261010T091046-24f1f2afc7 |
| B2 | 20261010T090717-13ebf67877 | 20261010T091048-b223f5975e |
| B3 | 20261010T090724-a39e6c5baa | 20261010T091051-e79c88c3a0 |
| REF_SPY | 20261010T090732-dbf52ab9f8 | 20261010T091054-53e8829580 |
| H1_252_3 | 20261010T090737-2d652c2127 | 20261010T091056-79e7a8ffe3 |
| H1_252_4 | 20261010T090745-899d5a7136 | 20261010T091059-b17280952a |
| H1_126_3 | 20261010T090752-9bd003f35b | 20261010T091102-c4fae89b36 |
| H1_126_4 | 20261010T090800-f78d0ee07b | 20261010T091105-5dbd95499e |
| H2_4of6 | 20261010T090807-af398ad6af | 20261010T091108-629ba2c4f0 |
| H2_5of6 | 20261010T090820-2da0674722 | 20261010T091112-378ce2d464 |
| P_A1 | 20261010T090831-aeca348964 | 20261010T091116-4835a4063a |
| H1_252_3_WF (P_A1 comparator) | 20261010T090913-3da4aae83e | 20261010T091131-75eab3df7b |
| evaluation report | 20261010T091002-0c84d411ed | 20261010T091133-9f91bb3c9c |

Comparison (step 4 of the campaign). After the repeat report, the following script was executed with the project's environment and the arguments `<ROOT> data/reports/20261010T091002-0c84d411ed data/reports/20261010T091133-9f91bb3c9c` (the report directories relative to `<ROOT>`). It verifies every directory with `provenance.verify`, compares the `files` dictionaries of the fourteen pairs, compares the shared files of the first N5 runs with the N3 and N4 reference runs named in `alpha_lab.evaluation.REFERENCES`, ties each reference manifest to its terminal journal record, and checks the N5 journal records. It prints only booleans and counts. The script as executed read the two run lists from a local file not under version control; in the version below the lists are written inline, and nothing else differs:

```python
"""N5 campaign step 4: manifest pairs, shared files against N3/N4 references, reference journal ties, journal checks.
Prints hashes-derived booleans and counts only."""
import json
import sys
from pathlib import Path

ROOT = Path(sys.argv[1])
sys.path.insert(0, str(ROOT / 'src'))
from alpha_lab.provenance import verify, sha256  # noqa: E402
from alpha_lab.evaluation import REFERENCES  # noqa: E402

LABELS = ['B0', 'B1', 'B2', 'B3', 'REF_SPY', 'H1_252_3', 'H1_252_4', 'H1_126_3', 'H1_126_4', 'H2_4of6', 'H2_5of6',
          'P_A1', 'H1_252_3_WF']
FIRST = ['20261010T090706-d2f7f13f1c', '20261010T090711-a0a3b5a215', '20261010T090717-13ebf67877',
         '20261010T090724-a39e6c5baa', '20261010T090732-dbf52ab9f8', '20261010T090737-2d652c2127',
         '20261010T090745-899d5a7136', '20261010T090752-9bd003f35b', '20261010T090800-f78d0ee07b',
         '20261010T090807-af398ad6af', '20261010T090820-2da0674722', '20261010T090831-aeca348964',
         '20261010T090913-3da4aae83e']
REPEAT = ['20261010T091043-854900b5a7', '20261010T091046-24f1f2afc7', '20261010T091048-b223f5975e',
          '20261010T091051-e79c88c3a0', '20261010T091054-53e8829580', '20261010T091056-79e7a8ffe3',
          '20261010T091059-b17280952a', '20261010T091102-c4fae89b36', '20261010T091105-5dbd95499e',
          '20261010T091108-629ba2c4f0', '20261010T091112-378ce2d464', '20261010T091116-4835a4063a',
          '20261010T091131-75eab3df7b']
first = [ROOT / 'data/runs' / run_id for run_id in FIRST]
repeat = [ROOT / 'data/runs' / run_id for run_id in REPEAT]
first_report, repeat_report = ROOT / sys.argv[2], ROOT / sys.argv[3]
rows = [json.loads(line) for line in (ROOT / 'experiments/EXPERIMENT_LOG.jsonl').read_text(encoding='utf-8').splitlines()]

pairs = 0
for label, a, b in zip(LABELS, first, repeat):
    fa, fb = verify(a)['files'], verify(b)['files']
    ok = fa == fb
    pairs += ok
    print(f'pair {label}: files equal {ok} ({len(fa)} files)')
ra, rb = verify(first_report)['files'], verify(repeat_report)['files']
pairs += ra == rb
print(f'pair report: files equal {ra == rb} ({len(ra)} files)')
print(f'equal pairs: {pairs} of 14')

shared_ok = shared_total = 0
for label, a in zip(LABELS, first):
    ref = REFERENCES.get(label)
    if ref is None:
        continue
    ref_dir = ROOT / 'data/runs' / ref
    ref_files = verify(ref_dir)['files']
    mine = verify(a)['files']
    for name, digest in ref_files.items():
        shared_total += 1
        shared_ok += mine.get(name) == digest
    terminal = [r for r in rows if r.get('run_id') == ref and r['event'] != 'started']
    tie = (len(terminal) == 1 and terminal[0]['status'] == 'completed'
           and terminal[0]['data_sha256'] == sha256((ref_dir / 'manifest.json').read_bytes())
           and terminal[0]['purpose'] in ('N3 benchmark run', 'N4 hypothesis run')
           and terminal[0]['candidate_ids'] == [label])
    print(f'reference {label}: journal tie {tie}')
print(f'shared files equal: {shared_ok} of {shared_total}')

ids = {p.name for p in first + repeat} | {first_report.name, repeat_report.name}
n5 = [r for r in rows if r.get('run_id') in ids]
print(f'N5 journal records: {len(n5)}; attempts: {len({r["run_id"] for r in n5})}')
print(f'statuses: {sorted({r["status"] for r in n5 if r["event"] != "started"})}')
print(f'dirty_tree true: {sum(1 for r in n5 if r["dirty_tree"] is not False)}')
print(f'environments: {len({r["environment_manifest_sha256"] for r in n5})}')
print(f'git shas: {len({r["git_sha"] for r in n5})} (src trees checked separately)')
print(f'all N5-purpose records in journal: {sum(1 for r in rows if str(r.get("purpose", "")).startswith("N5"))}')
print(f'parents of repeats correct: {all(next(r for r in rows if r.get("run_id") == b.name)["parent_attempt_id"] == a.name for a, b in zip(first, repeat))}')
print(f'repeat report parent correct: {next(r for r in rows if r.get("run_id") == repeat_report.name)["parent_attempt_id"] == first_report.name}')
print(f'seeds: {sorted({(r["purpose"], r["seed"]) for r in n5 if r["event"] == "started"}, key=str)}')
```

Output:

```text
pair B0: files equal True (9 files)
pair B1: files equal True (9 files)
pair B2: files equal True (9 files)
pair B3: files equal True (9 files)
pair REF_SPY: files equal True (9 files)
pair H1_252_3: files equal True (10 files)
pair H1_252_4: files equal True (10 files)
pair H1_126_3: files equal True (10 files)
pair H1_126_4: files equal True (10 files)
pair H2_4of6: files equal True (10 files)
pair H2_5of6: files equal True (10 files)
pair P_A1: files equal True (11 files)
pair H1_252_3_WF: files equal True (10 files)
pair report: files equal True (2 files)
equal pairs: 14 of 14
reference B0: journal tie True
reference B1: journal tie True
reference B2: journal tie True
reference B3: journal tie True
reference REF_SPY: journal tie True
reference H1_252_3: journal tie True
reference H1_252_4: journal tie True
reference H1_126_3: journal tie True
reference H1_126_4: journal tie True
reference H2_4of6: journal tie True
reference H2_5of6: journal tie True
shared files equal: 99 of 99
N5 journal records: 56; attempts: 28
statuses: ['completed']
dirty_tree true: 0
environments: 1
git shas: 28 (src trees checked separately)
all N5-purpose records in journal: 56
parents of repeats correct: True
repeat report parent correct: True
seeds: [('N5 benchmark run', None), ('N5 evaluation report', 20261006), ('N5 hypothesis run', None), ('N5 policy run', 20261007)]
```

All fourteen pairs are equal, all 99 shared files (the 45 benchmark files of N3 and the 54 shared files of the six N4 replacement runs) have the reference SHA-256, and all eleven reference manifests are tied to their completed N3 or N4 journal records. Two further checks were made separately: `git rev-parse <sha>:src` for the 28 distinct starting commits returns the single tree `058c72a492f78aa30f8defecbfab397eee37be96`, and the SHA-256 of the first 124 rows of the 180-row journal is `2d0b5bf461088f48a6e63cd898a70d40a2e1dca406a26a5bbbdc92842e60995d`, the hash of the whole journal at the freeze; no N5 record has a quality warning. The version of the script above was run again on 10 October 2026 in the same working copy and printed the same output.

The evaluation report also applies the shared-file comparison to its own input directories before it computes anything, so the repeat report applied it to the repeat directories as well. The one-boolean pair check of the N4 section remains valid for a single pair:

```bash
python -c "import json,sys; a,b=(json.load(open(p+'/manifest.json'))['files'] for p in sys.argv[1:3]); print(a==b)" data/runs/<first dir> data/runs/<repeat dir>
```

A change to `src` after the first registered N5 run is a bug fix only. Each fix requires rerunning all thirteen runs on the new tree, each with `--parent` set to its previous run, followed by a new report, and every attempt is disclosed (D025, item 16; D023, item 8). No such change was made in this campaign. A change of rule, candidate, window or period after the figures are shown is a new attempt with its own decision record.
