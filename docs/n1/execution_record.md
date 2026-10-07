# N1 execution record

Source: experiments/EXPERIMENT_LOG.jsonl. At 6 October 2026 it contained 36 lines, one started and one completed/failed event for each of 18 runs. During those runs, journal lines were neither changed nor deleted. The later, authorized path redaction is documented in [HISTORY_REWRITE.md](../HISTORY_REWRITE.md); the English editorial edition is documented in [DOCUMENTATION_EDITION.md](../DOCUMENTATION_EDITION.md). Result directories are local under data/ and excluded from Git. Listed data_sha256 values are hashes of directory manifests.

| run_id | Purpose | Status | Parent | git SHA | dirty | Error or result |
|---|---|---|---|---|---|---|
| 20261006T103539-85096ec568 | N1 acquisition | failed | — | 1643651 | true | OperationalError: unable to open database file (yfinance cache) |
| 20261006T103621-754f18207b | N1 acquisition | failed | 20261006T103539-85096ec568 | 1643651 | true | SSLError curl (77): CA-file path contained Cyrillic characters; partial snapshot data/snapshots/20261006T103621-754f18207b, a22999ba… |
| 20261006T103625-5202b05cbc | N1 issuer evidence acquisition | completed | — | 1643651 | true | data/evidence/20261006T103625-5202b05cbc, 4156d547…; uncommitted code, superseded by 20261006T122017-3048321309 |
| 20261006T103702-af69d7e5e6 | N1 acquisition | failed | 20261006T103621-754f18207b | 1643651 | true | NotImplementedError: Option unsupported: 40309 (curl CAINFO_BLOB); partial snapshot 54f97843… |
| 20261006T103809-a4a22ec667 | N1 acquisition | completed | 20261006T103702-af69d7e5e6 | 1643651 | true | data/snapshots/20261006T103809-a4a22ec667, 09edd925…; Yahoo snapshot used as input |
| 20261006T104336-dff9099c6b | N1 offline QA | completed | — | 80f75c9 | true | data/derived/20261006T104336-dff9099c6b, d4cde5cf…; no actual payable dates; superseded by 20261006T122144-73228a71eb |
| 20261006T104437-36dd8f9b4a | N1 issuer distribution reconciliation | completed | — | 80f75c9 | true | data/reconciliation/20261006T104437-36dd8f9b4a, b87b4209…; uncommitted code, superseded by 20261006T122119-c6bfb5c69b |
| 20261006T122017-3048321309 | N1 issuer evidence acquisition | completed | 20261006T103625-5202b05cbc | 590281e | false | data/evidence/20261006T122017-3048321309, 0a9bcea6…; 9 sources, all ok; superseded by 20261006T172354-1c0a8ca2d8 |
| 20261006T122119-c6bfb5c69b | N1 issuer distribution reconciliation | completed | 20261006T104437-36dd8f9b4a | c78a319 | false | data/reconciliation/20261006T122119-c6bfb5c69b, cb69e4fc…; warnings: unresolved SPY, TLT, LQD, HYG, BIL; no GLD/DBC source; superseded by 20261006T172415-ce65adb53e |
| 20261006T122144-73228a71eb | N1 offline QA | completed | 20261006T104336-dff9099c6b | 8e677d1 | false | data/derived/20261006T122144-73228a71eb, f9602513…; technical_pass true, data_ready_for_n2 false; code predates 72d862e, not reproducible with current code (see below); superseded by 20261006T172442-80ef993493 |
| 20261006T122200-a9fd9ddbda | N1 offline replay | completed | 20261006T122144-73228a71eb | cdaaf85 | false | replay_equal true (data_sha256 equals the audited QA snapshot hash by construction) |
| 20261006T131812-09887a01da | N1 offline replay | completed | 20261006T122200-a9fd9ddbda | 977eaf6 | false | Repeat after final-review fixes; replay_equal true, source_manifest_sha256 09edd925… |
| 20261006T172354-1c0a8ca2d8 | N1 issuer evidence acquisition | completed | 20261006T122017-3048321309 | e4d1669 | false | data/evidence/20261006T172354-1c0a8ca2d8, e7bea822…; 12 sources, all completed; added local DBC capture (sha256 7337eeb7…, checked during copying) and two GLD documents |
| 20261006T172415-ce65adb53e | N1 issuer distribution reconciliation | completed | 20261006T122119-c6bfb5c69b | 13bc576 | false | data/reconciliation/20261006T172415-ce65adb53e, f329ac0a…; DBC confirmed, GLD confirmed_no_distributions, EFA/EEM/IEF confirmed; unresolved SPY, TLT, LQD, HYG, BIL with the same seven events |
| 20261006T172434-fbb5c9f554 | N1 issuer corrections | completed | 20261006T172415-ce65adb53e | 8f9e0b4 | false | data/corrections/20261006T172434-fbb5c9f554, da623293…; 7 corrections: 3 add, 3 replace, 1 remove; corrections.json b8f2ef25… |
| 20261006T172442-80ef993493 | N1 offline QA (corrected vintage) | completed | 20261006T122144-73228a71eb | 86b0715 | false | data/derived/20261006T172442-80ef993493, f8934610…; technical_pass true, 4869/4869 sessions, adjustment_breaks 0, actual payable dates for every event except BIL 2008-03-03 |
| 20261006T172453-4d72af092f | N1 issuer distribution reconciliation (corrected vintage) | completed | 20261006T172415-ce65adb53e | 5416938 | false | data/reconciliation/20261006T172453-4d72af092f, cded7286…; all ten tickers confirmed or confirmed_no_distributions, no warnings |
| 20261006T172504-6b932ef79b | N1 offline replay (corrected vintage) | completed | 20261006T172442-80ef993493 | 56fdf27 | false | replay_equal true, source_manifest_sha256 09edd925…; data_sha256 equals the audited derived snapshot hash by construction |

The initially committed configs/n1.json lacked `"http_backend": "requests_verified_TLS"`, present in the configuration for run 20261006T103809-a4a22ec667 (config_sha256 285a4643…, versus the file's 0cbb6d67…). The key was added; the file's canonical hash then matched 285a4643….

The first seven runs used code that was uncommitted at execution time (dirty_tree true; patch hash in the log). Yahoo snapshot 20261006T103809-a4a22ec667 remains the input. Its bytes are verified against the manifest on every audit/reconcile; no reacquisition was performed. Evidence, reconciliation and QA were rerun with committed code.

Commits c78a319, 8e677d1, cdaaf85, fa8fe34, 13bc576, 8f9e0b4, 86b0715, 5416938, 56fdf27 and c41e57e contain only new journal lines. They were created between runs so that each following run started on a clean tree. Hashes identify the original history; rewritten equivalents are listed in HISTORY_REWRITE.md.

## Commands for the committed-code reruns

Executed from the checkout root in Git Bash, using Python 3.14.0 in .venv. The package was not installed into the environment, so PYTHONPATH supplied src.

```bash
PYTHONPATH=src .venv/Scripts/python -m alpha_lab evidence --root . --parent 20261006T103625-5202b05cbc
PYTHONPATH=src .venv/Scripts/python -m alpha_lab reconcile data/snapshots/20261006T103809-a4a22ec667 data/evidence/20261006T122017-3048321309 --root . --parent 20261006T104437-36dd8f9b4a
PYTHONPATH=src .venv/Scripts/python -m alpha_lab audit data/snapshots/20261006T103809-a4a22ec667 --payable data/reconciliation/20261006T122119-c6bfb5c69b/payable.json --root . --parent 20261006T104336-dff9099c6b
PYTHONPATH=src .venv/Scripts/python -m alpha_lab replay data/derived/20261006T122144-73228a71eb --root . --parent 20261006T122144-73228a71eb
PYTHONPATH=src .venv/Scripts/python -m alpha_lab replay data/derived/20261006T122144-73228a71eb --root . --parent 20261006T122200-a9fd9ddbda
```

The first evidence invocation without PYTHONPATH failed with `No module named alpha_lab` before entering project code. No run started and no journal entry was created.

Replay output: `{"replay_equal": true}`.

## Closure commands and sequence

Executed on 6 October 2026 on branch claude/n1-closure, with a clean tree for each run. Each run's journal entries were committed separately (`chore: log N1 <purpose> run <run_id>`) before the next run. Yahoo input remained 20261006T103809-a4a22ec667 and was not reacquired. The local DBC capture is data/manual/dbc-invesco-distribution.json; its sha256 is recorded in configs/n1_evidence.json. Acquisition provenance is described in docs/n1/N1_REPORT.md and data/manual/dbc-invesco-distribution.capture.json.

```bash
PYTHONPATH=src .venv/Scripts/python -m alpha_lab evidence --root . --parent 20261006T122017-3048321309
PYTHONPATH=src .venv/Scripts/python -m alpha_lab reconcile data/snapshots/20261006T103809-a4a22ec667 data/evidence/20261006T172354-1c0a8ca2d8 --root . --parent 20261006T122119-c6bfb5c69b
PYTHONPATH=src .venv/Scripts/python -m alpha_lab corrections data/reconciliation/20261006T172415-ce65adb53e --root . --parent 20261006T172415-ce65adb53e
PYTHONPATH=src .venv/Scripts/python -m alpha_lab audit data/snapshots/20261006T103809-a4a22ec667 --payable data/corrections/20261006T172434-fbb5c9f554/payable.json --corrections data/corrections/20261006T172434-fbb5c9f554/corrections.json --root . --parent 20261006T122144-73228a71eb
PYTHONPATH=src .venv/Scripts/python -m alpha_lab reconcile data/snapshots/20261006T103809-a4a22ec667 data/evidence/20261006T172354-1c0a8ca2d8 --corrections data/corrections/20261006T172434-fbb5c9f554/corrections.json --root . --parent 20261006T172415-ce65adb53e
PYTHONPATH=src .venv/Scripts/python -m alpha_lab replay data/derived/20261006T172442-80ef993493 --root . --parent 20261006T172442-80ef993493
```

Replay output: `{"replay_equal": true}`. Each command completed on its first attempt; there were no retries or failed runs in this series.

## Replay after review fixes (7 October 2026)

After R1–R4, RR1–RR2 and minor review fixes, the final vintage was replayed on commit 591352a with a clean tree. Run 20261007T064823-b7b806e0ce, parent 20261006T172504-6b932ef79b (the previous replay of the same vintage), returned `{"replay_equal": true}`; data_sha256 was f89346107cf7da6ca052693d188b8a576a08d42024c86865b0a42a63b1d294f2.

```bash
PYTHONPATH=src .venv/Scripts/python -m alpha_lab replay data/derived/20261006T172442-80ef993493 --root . --parent 20261006T172504-6b932ef79b
```

## Reproducibility of the previous derived snapshot

Snapshot 20261006T122144-73228a71eb cannot be reproduced with current code: normalized tables gained dividend_basis and dividend_correction_source, and corrections.json became part of the derived snapshot. Byte comparison therefore cannot match the former format. Exact reproduction was recorded before that change in run 20261006T131812-09887a01da on commit 977eaf6 (replay_equal true). It was not replayed again after the format change and is not an N2 input. N2 uses corrected vintage 20261006T172442-80ef993493.
