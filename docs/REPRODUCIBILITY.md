# Reproducibility

The repository implements N1 data preparation, the N2 account and execution engine and the N3 benchmark providers, metrics and report. Reproduction requires the locked Python environment and, for offline data replay and for the N2 run, the corresponding local source, evidence, correction, and derived snapshots. Those data are excluded from Git; cloning the repository alone does not provide them. No strategy performance reproduction is available: the N2 run uses a test weight provider and publishes no returns, and the registered N3 benchmark runs described below have not been executed at the time of writing.

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

The N3 runs use the approved vintage, the locked environment and a clean working tree. Before the first run, `provenance.verify` on `data/derived/20261006T172442-80ef993493` and its manifest SHA-256 `f89346107cf7da6ca052693d188b8a576a08d42024c86865b0a42a63b1d294f2` must match. The window is 2008-12-31 to 2022-12-30 in the main scenario (cost 0.001, lag 1, reserve 0.01, proxy 10, initial cash 100000); the first decision is the close of 2008-12-31 (D022, item 6).

```bash
for p in B0 B1 B2 B3 REF_SPY; do
  PYTHONPATH=src .venv/Scripts/python -m alpha_lab simulate data/derived/20261006T172442-80ef993493 --provider $p --start 2008-12-31 --end 2022-12-30 --root .
  # commit the new EXPERIMENT_LOG.jsonl lines before the next command
done
PYTHONPATH=src .venv/Scripts/python -m alpha_lab report --runs data/runs/<B0 dir> data/runs/<B1 dir> data/runs/<B2 dir> data/runs/<B3 dir> data/runs/<REF_SPY dir> --root .
```

Each `simulate` prints `data/runs/<run_id>`; substitute the five printed directories in `report`. The commands are shown as a sequence, not an unattended batch: each run must start on a clean tree and the journal lines of the previous run are committed first, because the report rejects a run whose records have `dirty_tree` true or no `git_sha`. A command that exits with code 3 has frozen its result and journaled `invariants_failed`; it stays in the journal and its cause is fixed before a repeat with `--parent`.

A repeat uses `--parent <run id of the first run>` for each of the five runs and for the report. A repeated benchmark run and a repeated report are compared by the `files` dictionaries of their `manifest.json` (per-file SHA-256), not by the manifest bytes, which contain run identifiers. The report files `benchmarks.json` and `benchmarks.md` in `data/reports/<run_id>/` contain no run id. The `--expected-sha256` option of `simulate` and `report` exists for tests on synthetic vintages; registered runs use the default, the approved hash. Run identifiers and results are added to the repository after the runs; none is recorded here.

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
