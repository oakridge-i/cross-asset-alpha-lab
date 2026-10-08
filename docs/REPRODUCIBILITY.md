# Reproducibility

The repository implements N1 data preparation, the N2 account and execution engine, the N3 benchmark providers, metrics and report, and the N4 providers and report for the six H1/H2 configurations. Reproduction requires the locked Python environment and, for offline data replay and for the N2 run, the corresponding local source, evidence, correction, and derived snapshots. Those data are excluded from Git; cloning the repository alone does not provide them. Benchmark reproduction is available: the registered N3 runs of B0-B3 and REF_SPY and their report are listed below and in the [N3 report](n3/N3_REPORT.md). The six registered N4 runs of H1/H2, their repeats and their reports were executed on 8 October 2026 on the branch `claude/n4-hypotheses` and are listed in the N4 section below and in the [N4 report](n4/N4_REPORT.md). They publish no returns; the N2 run uses a test weight provider and publishes no returns either.

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
