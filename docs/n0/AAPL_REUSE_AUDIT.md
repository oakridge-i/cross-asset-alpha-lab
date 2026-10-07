# AAPL release audit for selective reuse

Read-only audit dated 6 October 2026. Original repository: `C:\Quantitive\model 1 aapl`; release checkout: `<workspace>\aapl-finalization`.

| Check | Observed state |
|---|---|
| Primary checkout | main, HEAD ed4fd39518f1f58ad4065512bec8223443186bf3, clean |
| Local origin/main | ed4fd39518f1f58ad4065512bec8223443186bf3 |
| Local v0.6.0, peeled | 4d69932382af4a7bcaddfb4621f0973ea2d820c2 |
| Release checkout | codex/aapl-final-release, HEAD 4d69932382af4a7bcaddfb4621f0973ea2d820c2, clean |
| Direct remote ref check | main ed4fd39518f1f58ad4065512bec8223443186bf3; annotated tag 0300c8182c64a9c0b40fae1b4cb258340ae62c45, peeled 4d69932382af4a7bcaddfb4621f0973ea2d820c2 |

Reading the original repository used a one-time `-c safe.directory` setting, without a global configuration change. The first HTTPS git ls-remote failed with Windows schannel; the retry with `-c http.sslBackend=openssl` succeeded. TLS verification remained enabled. No fetch, pull, checkout or mutation of the original project was performed. Remote main was checked directly; the PR merge state was not queried separately through the GitHub API.

The audit read the release [research report](https://github.com/oakridge-i/aapl-sma-backtest/blob/4d69932382af4a7bcaddfb4621f0973ea2d820c2/docs/final/research_report.md), [reproduction instructions](https://github.com/oakridge-i/aapl-sma-backtest/blob/4d69932382af4a7bcaddfb4621f0973ea2d820c2/docs/final/reproduction.md), [review](https://github.com/oakridge-i/aapl-sma-backtest/blob/4d69932382af4a7bcaddfb4621f0973ea2d820c2/docs/final/review.md), [execution record](https://github.com/oakridge-i/aapl-sma-backtest/blob/4d69932382af4a7bcaddfb4621f0973ea2d820c2/docs/final/execution_record.md), release_manifest and final_tests.log. These links are pinned to the audited release commit; their repository and paths were verified against the local release checkout when preparing this English edition.

The recorded AAPL test result was 149 passed in 96.44 s, read from the saved log; it was not rerun during this audit. The saved documents record two frozen searches, offline repeats, 72 cost/lag scenarios per snapshot and 202320 daily rows. Over the common period of the updated data, nested-ensemble CAGR was 4.74%, versus 11.43% for 50% AAPL. A convincing advantage or alpha was not established. These figures were not used to select the new protocol on the basis of H1/H2 results.

release_manifest describes the local release before its subsequent publication. Its remote_mutations=false field does not imply that the PR or main remained unpublished. Direct ref comparison confirmed the later state recorded in the source brief. The previous preview belongs to 91e769e and is not treated as a new result.

## Candidates for selective reuse

| Release source | Potential use | Required validation against the new contract |
|---|---|---|
| src/quant_backtest/research_config.py | YAML/config validation pattern | New schema, universe, available_at and next-open parameters. Do not copy the previous defaults. |
| src/quant_backtest/data_quality.py and closeout.py | Snapshot, manifest, hash and effective-period patterns | OHLC/actions, split basis, preservation of raw data and vintages, and quality for each ETF beyond adjusted close. |
| src/quant_backtest/metrics.py | Drawdown, aligned excess returns and metric formulas | Consistent sample ddof=1 and sessions-based CAGR. The legacy calendar-based CAGR function must not be mixed with the report formula. |
| tests/test_a1_accounting.py, test_a2_financial_invariants.py | Manual financial invariants | Multiple assets, actual BIL, receivables/cash, Open and order quantities rather than allocations at close. |
| tests/test_closeout.py | Replay and effective-snapshot regression patterns | New multi-asset NAV, trade and position receipts; retain original and effective hashes. |
| tests/test_methodology_v05.py, test_m1_foundation.py | Causality test material | Future prices, actions and source vintages must not change past decisions; use an exchange calendar rather than artificial freq=B. |
| src/quant_backtest/reports.py, reporting scripts | Tables backed by source evidence | New field contract and explicit exploratory, reserved and prospective status. |

Module and test names were inspected, and metrics.py and research_data.py were read. The table identifies candidates for further audit; it does not certify every listed module. Their full source must be read before reuse. Raw snapshots were not copied into the new repository.

engine.py, costs.py, continuous.py and research orchestration require a separate assessment before any reuse. AAPL assumes next-close execution, synthetic BIL cash returns and different sizing/settlement; these assumptions do not meet the new RESEARCH_PROTOCOL. No AAPL production code was transferred during N0.

Any future reuse must record the original repository, tag, SHA, path, actual diff, license and new validation. Formula applicability takes priority over preserving the previous interface.
