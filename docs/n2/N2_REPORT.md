# N2 report: account and execution engine

Date: 7 October 2026, Europe/Moscow. Branch `claude/n2-execution`.

## Purpose

N2 checks the account and execution mechanics on real data: the order of events in a session, orders constrained by cash, costs, splits and payouts. N2 contains no strategies, no section 5 weights from the protocol and no section 11 metrics; those belong to N3. The model is described in [EXECUTION_MODEL.md](../../EXECUTION_MODEL.md); the manual calculations against which the engine tests are checked are in [manual_reconciliation.md](manual_reconciliation.md). The run uses the test weight provider `invariant_rotation`, which exists only so that orders, splits and payouts occur and is not a strategy. NAV, returns and any other performance measures are not published in this report, as the protocol prohibits.

## Vintage and command

Vintage: `data/derived/20261006T172442-80ef993493` (corrected, with `corrections.json`; verdict D019, approved by D020). Window 2007-05-31 to 2022-12-30.

```bash
PYTHONPATH=src .venv/Scripts/python -m alpha_lab simulate data/derived/20261006T172442-80ef993493 --provider invariant_rotation --start 2007-05-31 --end 2022-12-30 --root .
```

Test suite: 261 passed on `4b7a618`.

## Registered runs

| | Run 1 | Run 2 |
|---|---|---|
| id | 20261007T140216-1814c4deb7 | 20261007T140236-ff53aee6df |
| git_sha | 4b7a618 | 9a20161 |
| parent | none | 20261007T140216-1814c4deb7 |
| dirty_tree | false | false |
| status | completed | completed |
| journal lines committed | 9a20161 | 24810ff |

The journal lines were committed between the runs, so the second run has a different git_sha while the tree is clean in both. `manifest.json` lists 7 files; their hashes are identical in runs 1 and 2. The `data/runs` directory is not in Git, and the result files were not committed.

## CLI defect (fixed)

Run 1 completed and was journaled, but the command then failed with `UnicodeEncodeError` when printing the absolute run path, which contained Cyrillic characters, on a cp1252 console. Run 2 was executed with `PYTHONIOENCODING=utf-8`: the path was printed and the exit code was 0. The defect was fixed in `ad5debd`: `simulate` prints the path relative to the project (`data/runs/<run_id>`), and `main()` escapes characters the console encoding cannot represent, so the `PYTHONIOENCODING` workaround is no longer needed. The registered runs were not repeated: the fix changes neither the results nor the journal.

## Invariants (invariants.json, passed true)

| Invariant | Result |
|---|---|
| cash_non_negative | minimum cash balance 571.4822833714497 |
| nav_identity | maximum gap 5.820766091346741e-11 |
| cash_flow | maximum gap 2.546585164964199e-11 |
| split_quantity_only | 2 splits, no violations |
| receivable_conservation | accrued 54213.98078999996, paid 54133.83578999995, remaining 80.145 |
| execution_timing | 1870 orders, 1870 trades, no violations |
| costs | gap 0.0 on notional 18558427.134355545 |

Splits in the window: EEM 2008-07-24 and BIL 2017-11-30. There is exactly one proxy payout: BIL, ex-date 2008-03-03, payment 2008-03-13.

## Counts

- Decisions: 187.
- Orders: 1870. Filled completely: 1869; partially filled: 1 (the remainder was cancelled with reason `fractional_quantity`, see D021, item 10); cancelled entirely: 0.
- Trades: 1870.
- Cancellations by reason: `fractional_quantity` 1 (a fractional purchase remainder after a split); no other reasons.
- Payouts: 965, of which 964 paid and 1 `receivable`.

## Receivable check

The only `receivable` row in `payouts.csv` is SPY, ex-date 2022-12-16, payment date 2023-01-31 (actual), 45 shares, 1.781 per share, 80.145. The payment session is later than the end of the window, 2022-12-30, as expected; there is no receivable that can never be paid. This check is not part of the `receivable_conservation` invariant, which distinguishes only accrued, paid and remaining amounts, so it was performed separately.

## Limitations

- The data are not point-in-time, and `available_at` is a modeling assumption. The seven Yahoo corrections were accepted by the user's decision that the issuer is authoritative and have no independent confirmation (D016). The `confirmed_no_distributions` basis for GLD is weaker than a statement that distributions never occurred (D018). The completeness of DBC before 2007-12-17 is not proven by the issuer document (D017). The data readiness conditions and their disclosure: D019, D020.
- The payable-date contract check starts at 2007-05-30 (D021, item 13).
- The result concerns mechanics. The `invariant_rotation` provider is not a strategy; neither H1/H2 nor B0-B3 were calculated.
- Open: the deferred review findings listed in [STATUS.md](../../STATUS.md) (in particular, three of the seven invariants have no negative tests, and there is no test of a split and a dividend in the same session). They were passed to the final branch review.
