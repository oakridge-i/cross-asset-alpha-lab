# N3 report: benchmarks B0-B3 and REF_SPY

Date: 7 October 2026, Europe/Moscow. Branch `claude/n3-benchmarks`.

## Purpose

N3 computes the benchmarks of the [research protocol](../../RESEARCH_PROTOCOL.md) on the approved vintage: B0 (BIL only), B1 (equal weights with caps), B2 (inverse volatility with caps and the volatility target), B3 (absolute 12-month trend with the common risk controls) and the reference REF_SPY (a single SPY purchase). It publishes the section 11 metrics of these five portfolios for 2009-2022. The weight rules, metrics and report are specified in [the N3 specification](../superpowers/specs/2026-10-07-n3-benchmarks-design.md); the interpretations that the protocol leaves open are recorded in [D022](../../DECISIONS.md), and the account mechanics are described in [EXECUTION_MODEL.md](../../EXECUTION_MODEL.md). The benchmarks are baselines for later comparison. This report contains no strategy results and no comparison of candidates, and it does not say which benchmark is better.

## Vintage and commands

Vintage: `data/derived/20261006T172442-80ef993493` (corrected, with `corrections.json`; D019, approved by D020), manifest SHA-256 `f89346107cf7da6ca052693d188b8a576a08d42024c86865b0a42a63b1d294f2`. Window 2008-12-31 to 2022-12-30; the first decision is at the close of 2008-12-31 and is executed at the open of 2009-01-02. Main scenario: cost 0.001 per side, lag 1, reserve 0.01, proxy payment lag 10 sessions; initial cash 100000.

```bash
PYTHONPATH=src .venv/Scripts/python -m alpha_lab simulate data/derived/20261006T172442-80ef993493 --provider B0 --start 2008-12-31 --end 2022-12-30 --root .
PYTHONPATH=src .venv/Scripts/python -m alpha_lab simulate data/derived/20261006T172442-80ef993493 --provider B1 --start 2008-12-31 --end 2022-12-30 --root .
PYTHONPATH=src .venv/Scripts/python -m alpha_lab simulate data/derived/20261006T172442-80ef993493 --provider B2 --start 2008-12-31 --end 2022-12-30 --root .
PYTHONPATH=src .venv/Scripts/python -m alpha_lab simulate data/derived/20261006T172442-80ef993493 --provider B3 --start 2008-12-31 --end 2022-12-30 --root .
PYTHONPATH=src .venv/Scripts/python -m alpha_lab simulate data/derived/20261006T172442-80ef993493 --provider REF_SPY --start 2008-12-31 --end 2022-12-30 --root .
PYTHONPATH=src .venv/Scripts/python -m alpha_lab report --runs data/runs/20261007T180004-12aae80084 data/runs/20261007T180018-b6c98bd0aa data/runs/20261007T180026-dffe07154c data/runs/20261007T180033-bba99392df data/runs/20261007T180039-be7dd8f43a --root .
```

The full sequence, including the commits of the journal lines between the runs and the repeats with `--parent`, is in [docs/REPRODUCIBILITY.md](../REPRODUCIBILITY.md). Test suite: 378 passed on `dfebc42`; the `src` tree did not change afterwards (later commits are journal lines and documents).

## Registered runs

First runs (all `completed`, `dirty_tree` false, no parent):

| benchmark | run id | git_sha | journal lines committed |
|---|---|---|---|
| B0 | 20261007T180004-12aae80084 | dfebc42 | a94a77e |
| B1 | 20261007T180018-b6c98bd0aa | a94a77e | 50d4f33 |
| B2 | 20261007T180026-dffe07154c | 50d4f33 | 1623de9 |
| B3 | 20261007T180033-bba99392df | 1623de9 | 8c6c220 |
| REF_SPY | 20261007T180039-be7dd8f43a | 8c6c220 | 5b5fea4 |

Report run `20261007T200805-c75aa41980` (git `a72313d`, journal lines `bd42479`, `completed`). Its journaled `expected_sha256` is the approved hash given above.

Repeats (each with the first run of the same benchmark as parent; all `completed`, `dirty_tree` false):

| benchmark | run id | git_sha | journal lines committed |
|---|---|---|---|
| B0 | 20261007T200819-ff620c4546 | bd42479 | 93544be |
| B1 | 20261007T200822-68dc462b5f | 93544be | c1c63ca |
| B2 | 20261007T200827-b8f9da8b3f | c1c63ca | 6daf373 |
| B3 | 20261007T200831-bcab64c3eb | 6daf373 | f198b69 |
| REF_SPY | 20261007T200835-3df74a38e0 | f198b69 | 132900c |

Repeat report `20261007T200847-cf60a2b2d9` (parent `20261007T200805-c75aa41980`, git `132900c`, journal lines `5dce670`, `completed`). The `data/runs` and `data/reports` directories are not in Git.

## Reproducibility

For all five benchmark pairs the `files` dictionaries of `manifest.json` (9 files each) are identical, so every result file has the same SHA-256 in the first run and in the repeat. The `files` of the two reports (`benchmarks.json`, `benchmarks.md`) are identical. The manifest bytes differ only by run identifiers in the metadata (and, for the report manifests, the referenced run ids and run manifest hashes), as expected (D022, item 16).

## Invariants and counts

All seven financial invariants passed in every run. Counts per first run (the repeats are identical):

| benchmark | decisions | orders (all filled) | trades | payouts paid / receivable | split events | minimum cash (USD) |
|---|---|---|---|---|---|---|
| B0 | 168 | 44 | 44 | 63 / 0 | BIL 2017-11-30 | 773.18 |
| B1 | 168 | 1427 | 1427 | 810 / 1 | none | 1013.78 |
| B2 | 168 | 1534 | 1534 | 814 / 1 | none | 1007.17 |
| B3 | 168 | 1184 | 1184 | 620 / 0 | BIL 2017-11-30 | 685.05 |
| REF_SPY | 1 | 1 | 1 | 55 / 1 | none | 688.10 |

There are no cancellations of any kind. There are no proxy payouts in the window: the only proxy row, BIL 2008-03-03, precedes it. The only `receivable` row is SPY, ex-date 2022-12-16, payment 2023-01-31 (actual), later than the window end, as in the [N2 report](../n2/N2_REPORT.md); there is no receivable that can never be paid.

## Weight construction

An independent recomputation of the weights over all 168 decision dates matched the providers to within 6e-15. Number of decisions (of 168) at which a rule was binding:

| rule | B1 | B2 | B3 |
|---|---|---|---|
| ETF cap (25%) | 0 | 44 | 23 |
| group cap (50%) | 0 | 0 | 0 |
| volatility target | 41 | 20 | 1 |

No target weight exceeded 25% per ETF or 50% per group.

## Results

The tables below are reproduced from the frozen `benchmarks.md` of report `20261007T200805-c75aa41980`, numbers unchanged; the repeat report has identical files.

Definitions (the full ones are in [D022](../../DECISIONS.md) and in section 11 of the [protocol](../../RESEARCH_PROTOCOL.md)):

- `cost_ratio`: the sum over the period's decisions of costs in USD divided by NAV at the decision close (a sum of relative costs, not the exact loss of compound return; D022, item 13).
- `turnover_annual`: one-way turnover, the sum of absolute trade notional divided by pretrade NAV, expressed as a multiple of NAV per year (`x`); it is not divided by 2 (D022, item 11).
- `mean_cash_plus_bil`, `mean_receivables`, `mean_risky`: mean shares of NAV held in USD cash plus BIL, in receivables, and in the risky ETFs (all tickers except BIL).
- `mean_target_risky`: the mean total target weight of the risky ETFs over the period's decisions; `n/a` where the period has no decision.
- `sharpe_bil`, `mean_excess` and `utility` use excess returns over the theoretical total-return index of BIL, not over B0 (D022, item 10).
- Decisions, turnover, costs and cost_ratio are attributed to the period of the execution session (D022, item 12).

Window 2008-12-31 to 2022-12-30, initial cash 100000.00, scenario {"cost": 0.001, "lag": 1, "proxy_pay_days": 10, "reserve": 0.01}.

### full

| benchmark | total_return | cagr | volatility | mean_excess | sharpe_bil | utility | max_drawdown | decisions | turnover_annual | costs_usd | cost_ratio | mean_cash_plus_bil | mean_receivables | mean_risky | mean_target_risky |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B0 | 5.92% | 0.41% | 0.30% | -0.02% | -0.358 | -0.000 | -0.44% | 168 | 0.07x | 104.89 | 0.10% | 99.99% | 0.01% | 0.00% | 0.00% |
| B1 | 79.31% | 4.26% | 7.88% | 4.05% | 0.513 | 0.031 | -17.83% | 168 | 0.66x | 1316.57 | 0.93% | 7.89% | 0.06% | 92.06% | 93.39% |
| B2 | 75.63% | 4.11% | 6.38% | 3.80% | 0.594 | 0.032 | -18.80% | 168 | 1.17x | 2434.75 | 1.63% | 4.80% | 0.06% | 95.15% | 96.58% |
| B3 | 45.39% | 2.71% | 4.36% | 2.34% | 0.536 | 0.021 | -9.59% | 168 | 2.93x | 5153.11 | 4.09% | 36.41% | 0.05% | 63.54% | 64.51% |
| REF_SPY | 385.27% | 11.96% | 16.84% | 12.28% | 0.729 | 0.080 | -29.95% | 1 | 0.07x | 99.21 | 0.10% | 8.11% | 0.20% | 91.69% | 100.00% |

### development

| benchmark | total_return | cagr | volatility | mean_excess | sharpe_bil | utility | max_drawdown | decisions | turnover_annual | costs_usd | cost_ratio | mean_cash_plus_bil | mean_receivables | mean_risky | mean_target_risky |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B0 | -0.17% | -0.03% | 0.39% | -0.05% | -0.448 | -0.000 | -0.24% | 60 | 0.20x | 99.45 | 0.10% | 100.00% | 0.00% | 0.00% | 0.00% |
| B1 | 40.76% | 7.09% | 8.08% | 7.16% | 0.883 | 0.062 | -8.51% | 60 | 0.93x | 539.02 | 0.46% | 13.05% | 0.06% | 86.89% | 88.10% |
| B2 | 43.29% | 7.47% | 6.21% | 7.39% | 1.183 | 0.068 | -7.57% | 60 | 1.31x | 784.11 | 0.66% | 6.45% | 0.07% | 93.49% | 94.91% |
| B3 | 24.63% | 4.51% | 4.88% | 4.52% | 0.923 | 0.042 | -5.33% | 60 | 2.87x | 1589.26 | 1.43% | 29.10% | 0.05% | 70.85% | 71.91% |
| REF_SPY | 118.07% | 16.90% | 18.53% | 17.33% | 0.933 | 0.122 | -26.95% | 1 | 0.20x | 99.21 | 0.10% | 4.17% | 0.22% | 95.61% | 100.00% |

### walk_forward

| benchmark | total_return | cagr | volatility | mean_excess | sharpe_bil | utility | max_drawdown | decisions | turnover_annual | costs_usd | cost_ratio | mean_cash_plus_bil | mean_receivables | mean_risky | mean_target_risky |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B0 | 6.10% | 0.66% | 0.24% | -0.01% | -3.266 | -0.000 | -0.24% | 108 | 0.01x | 5.44 | 0.01% | 99.99% | 0.01% | 0.00% | 0.00% |
| B1 | 27.39% | 2.73% | 7.77% | 2.33% | 0.299 | 0.014 | -17.83% | 108 | 0.51x | 777.54 | 0.46% | 5.02% | 0.05% | 94.93% | 96.33% |
| B2 | 22.57% | 2.29% | 6.47% | 1.80% | 0.279 | 0.012 | -18.80% | 108 | 1.08x | 1650.64 | 0.97% | 3.88% | 0.05% | 96.07% | 97.51% |
| B3 | 16.65% | 1.73% | 4.03% | 1.13% | 0.279 | 0.009 | -9.59% | 108 | 2.96x | 3563.85 | 2.66% | 40.47% | 0.04% | 59.48% | 60.40% |
| REF_SPY | 122.53% | 9.30% | 15.82% | 9.48% | 0.600 | 0.057 | -29.95% | 0 | 0.00x | 0.00 | 0.00% | 10.30% | 0.19% | 89.51% | n/a |

### 2014-2016

| benchmark | total_return | cagr | volatility | mean_excess | sharpe_bil | utility | max_drawdown | decisions | turnover_annual | costs_usd | cost_ratio | mean_cash_plus_bil | mean_receivables | mean_risky | mean_target_risky |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B0 | -0.09% | -0.03% | 0.27% | 0.00% | 0.108 | 0.000 | -0.24% | 36 | 0.00x | 0.00 | 0.00% | 100.00% | 0.00% | 0.00% | 0.00% |
| B1 | 2.82% | 0.93% | 6.63% | 1.17% | 0.177 | 0.005 | -14.81% | 36 | 0.27x | 115.89 | 0.08% | 1.39% | 0.06% | 98.56% | 100.00% |
| B2 | 4.64% | 1.52% | 5.02% | 1.67% | 0.332 | 0.013 | -10.44% | 36 | 0.85x | 378.77 | 0.26% | 1.64% | 0.06% | 98.31% | 99.78% |
| B3 | 0.91% | 0.30% | 3.31% | 0.38% | 0.116 | 0.002 | -4.94% | 36 | 3.18x | 1211.15 | 0.95% | 40.62% | 0.04% | 59.34% | 60.13% |
| REF_SPY | 25.87% | 7.97% | 12.13% | 8.43% | 0.694 | 0.062 | -11.82% | 0 | 0.00x | 0.00 | 0.00% | 8.58% | 0.21% | 91.21% | n/a |

### 2017-2019

| benchmark | total_return | cagr | volatility | mean_excess | sharpe_bil | utility | max_drawdown | decisions | turnover_annual | costs_usd | cost_ratio | mean_cash_plus_bil | mean_receivables | mean_risky | mean_target_risky |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B0 | 4.46% | 1.47% | 0.23% | -0.02% | -6.971 | -0.000 | -0.04% | 36 | 0.01x | 4.16 | 0.00% | 99.98% | 0.02% | 0.00% | 0.00% |
| B1 | 25.67% | 7.94% | 5.54% | 6.31% | 1.139 | 0.059 | -10.06% | 36 | 0.22x | 104.75 | 0.06% | 1.39% | 0.06% | 98.56% | 100.00% |
| B2 | 23.75% | 7.38% | 4.10% | 5.73% | 1.399 | 0.055 | -5.80% | 36 | 1.06x | 526.74 | 0.32% | 1.73% | 0.06% | 98.21% | 99.70% |
| B3 | 12.70% | 4.08% | 3.49% | 2.58% | 0.738 | 0.024 | -6.19% | 36 | 3.25x | 1299.25 | 0.97% | 36.16% | 0.06% | 63.79% | 64.77% |
| REF_SPY | 45.50% | 13.35% | 11.35% | 11.70% | 1.031 | 0.098 | -17.25% | 0 | 0.00x | 0.00 | 0.00% | 10.84% | 0.20% | 88.97% | n/a |

### 2020-2022

| benchmark | total_return | cagr | volatility | mean_excess | sharpe_bil | utility | max_drawdown | decisions | turnover_annual | costs_usd | cost_ratio | mean_cash_plus_bil | mean_receivables | mean_risky | mean_target_risky |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B0 | 1.66% | 0.55% | 0.20% | -0.01% | -3.136 | -0.000 | -0.21% | 36 | 0.00x | 1.28 | 0.00% | 99.99% | 0.01% | 0.00% | 0.00% |
| B1 | -1.41% | -0.47% | 10.32% | -0.50% | -0.048 | -0.021 | -17.83% | 36 | 1.05x | 556.90 | 0.31% | 12.28% | 0.04% | 87.68% | 88.99% |
| B2 | -5.35% | -1.82% | 9.13% | -1.97% | -0.216 | -0.032 | -18.80% | 36 | 1.34x | 745.13 | 0.40% | 8.26% | 0.04% | 91.69% | 93.06% |
| B3 | 2.58% | 0.85% | 5.06% | 0.42% | 0.083 | 0.000 | -9.59% | 36 | 2.45x | 1053.45 | 0.73% | 44.63% | 0.03% | 55.33% | 56.30% |
| REF_SPY | 21.51% | 6.71% | 21.78% | 8.32% | 0.382 | 0.012 | -29.95% | 0 | 0.00x | 0.00 | 0.00% | 11.48% | 0.16% | 88.36% | n/a |

### Annual total_return

| year | B0 | B1 | B2 | B3 | REF_SPY |
|---|---|---|---|---|---|
| 2009 | 0.04% | 10.35% | 8.87% | 0.22% | 25.33% |
| 2010 | -0.04% | 13.26% | 13.43% | 9.78% | 14.51% |
| 2011 | -0.04% | 4.60% | 7.90% | 5.32% | 1.78% |
| 2012 | -0.04% | 8.89% | 8.46% | 5.09% | 15.03% |
| 2013 | -0.09% | -1.12% | -0.85% | 2.34% | 29.79% |
| 2014 | -0.06% | 1.44% | 2.63% | 1.71% | 12.42% |
| 2015 | -0.13% | -6.49% | -4.75% | -0.73% | 1.13% |
| 2016 | 0.11% | 8.40% | 7.05% | -0.05% | 10.71% |
| 2017 | 0.68% | 13.53% | 10.65% | 8.71% | 19.24% |
| 2018 | 1.72% | -5.66% | -2.62% | -3.72% | -3.97% |
| 2019 | 2.00% | 17.34% | 14.85% | 7.68% | 27.07% |
| 2020 | 0.39% | 4.69% | 5.18% | 1.96% | 15.85% |
| 2021 | -0.10% | 6.91% | 4.00% | 2.58% | 25.32% |
| 2022 | 1.36% | -11.92% | -13.47% | -1.92% | -16.31% |

### Annual volatility

| year | B0 | B1 | B2 | B3 | REF_SPY |
|---|---|---|---|---|---|
| 2009 | 0.70% | 6.92% | 6.87% | 4.27% | 26.27% |
| 2010 | 0.29% | 9.34% | 6.36% | 6.71% | 17.38% |
| 2011 | 0.26% | 9.70% | 6.78% | 5.86% | 21.86% |
| 2012 | 0.23% | 6.48% | 4.66% | 2.58% | 11.97% |
| 2013 | 0.25% | 7.45% | 6.12% | 3.88% | 10.32% |
| 2014 | 0.24% | 5.04% | 3.91% | 2.80% | 10.40% |
| 2015 | 0.26% | 7.22% | 5.61% | 3.44% | 14.05% |
| 2016 | 0.29% | 7.36% | 5.38% | 3.65% | 11.71% |
| 2017 | 0.30% | 4.34% | 3.63% | 3.10% | 6.04% |
| 2018 | 0.18% | 6.78% | 4.51% | 4.41% | 15.12% |
| 2019 | 0.19% | 5.13% | 4.04% | 2.70% | 11.01% |
| 2020 | 0.18% | 12.43% | 10.66% | 6.34% | 28.90% |
| 2021 | 0.14% | 6.87% | 5.21% | 4.61% | 11.60% |
| 2022 | 0.24% | 10.85% | 10.43% | 3.93% | 21.28% |

### Annual mean_excess

| year | B0 | B1 | B2 | B3 | REF_SPY |
|---|---|---|---|---|---|
| 2009 | -0.23% | 9.82% | 8.46% | 0.04% | 25.75% |
| 2010 | 0.00% | 12.93% | 12.85% | 9.60% | 15.10% |
| 2011 | 0.00% | 5.01% | 7.87% | 5.39% | 4.19% |
| 2012 | 0.00% | 8.84% | 8.34% | 5.08% | 14.88% |
| 2013 | 0.00% | -0.76% | -0.58% | 2.48% | 26.71% |
| 2014 | 0.00% | 1.62% | 2.73% | 1.80% | 12.31% |
| 2015 | 0.00% | -6.32% | -4.58% | -0.55% | 2.24% |
| 2016 | -0.00% | 8.23% | 6.85% | -0.10% | 10.75% |
| 2017 | -0.01% | 12.14% | 9.54% | 7.74% | 17.16% |
| 2018 | -0.02% | -7.35% | -4.30% | -5.44% | -4.65% |
| 2019 | -0.03% | 14.11% | 11.92% | 5.42% | 22.56% |
| 2020 | -0.00% | 4.95% | 5.21% | 1.74% | 18.46% |
| 2021 | 0.00% | 7.02% | 4.16% | 2.75% | 23.35% |
| 2022 | -0.02% | -13.53% | -15.36% | -3.25% | -16.99% |

### Annual sharpe_bil

| year | B0 | B1 | B2 | B3 | REF_SPY |
|---|---|---|---|---|---|
| 2009 | -1.010 | 1.407 | 1.218 | 0.009 | 0.978 |
| 2010 | 0.137 | 1.378 | 2.005 | 1.423 | 0.867 |
| 2011 | 0.147 | 0.515 | 1.158 | 0.920 | 0.192 |
| 2012 | 0.191 | 1.355 | 1.772 | 1.950 | 1.239 |
| 2013 | 0.345 | -0.102 | -0.094 | 0.640 | 2.592 |
| 2014 | 0.263 | 0.321 | 0.699 | 0.644 | 1.183 |
| 2015 | 0.497 | -0.876 | -0.817 | -0.159 | 0.160 |
| 2016 | -0.369 | 1.120 | 1.277 | -0.027 | 0.917 |
| 2017 | -2.426 | 2.793 | 2.614 | 2.493 | 2.847 |
| 2018 | -9.841 | -1.082 | -0.954 | -1.230 | -0.308 |
| 2019 | -11.434 | 2.753 | 2.956 | 2.020 | 2.052 |
| 2020 | -2.402 | 0.398 | 0.488 | 0.273 | 0.639 |
| 2021 | 0.707 | 1.022 | 0.798 | 0.597 | 2.014 |
| 2022 | -5.920 | -1.248 | -1.475 | -0.832 | -0.798 |

### Annual max_drawdown

| year | B0 | B1 | B2 | B3 | REF_SPY |
|---|---|---|---|---|---|
| 2009 | -0.24% | -4.87% | -6.35% | -4.57% | -26.95% |
| 2010 | -0.06% | -5.78% | -3.76% | -4.76% | -15.25% |
| 2011 | -0.09% | -6.23% | -4.23% | -4.15% | -17.77% |
| 2012 | -0.04% | -5.58% | -3.82% | -1.69% | -9.15% |
| 2013 | -0.11% | -8.51% | -7.57% | -5.33% | -5.19% |
| 2014 | -0.11% | -6.27% | -4.26% | -1.95% | -6.71% |
| 2015 | -0.15% | -10.79% | -8.86% | -3.21% | -10.89% |
| 2016 | -0.09% | -5.81% | -5.15% | -4.94% | -9.30% |
| 2017 | -0.04% | -2.27% | -2.05% | -1.60% | -2.34% |
| 2018 | -0.02% | -10.06% | -5.80% | -6.19% | -17.25% |
| 2019 | -0.02% | -2.07% | -1.36% | -1.52% | -5.86% |
| 2020 | -0.09% | -17.83% | -16.35% | -9.59% | -29.95% |
| 2021 | -0.11% | -3.62% | -3.28% | -3.04% | -4.59% |
| 2022 | -0.03% | -16.83% | -18.32% | -3.56% | -21.95% |

### Groups (full)

| benchmark | mean Credit | mean Equity | mean Real | mean Treasury | max Credit | max Equity | max Real | max Treasury | max weight |
|---|---|---|---|---|---|---|---|---|---|
| B0 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| B1 | 20.38% | 30.79% | 20.51% | 20.37% | 22.56% | 35.25% | 24.77% | 26.40% | 13.45% |
| B2 | 35.53% | 19.55% | 14.20% | 25.86% | 44.91% | 29.12% | 21.18% | 33.29% | 25.37% |
| B3 | 26.99% | 13.74% | 7.39% | 15.42% | 43.86% | 29.79% | 28.01% | 32.70% | 25.20% |
| REF_SPY | 0.00% | 91.69% | 0.00% | 0.00% | 0.00% | 99.33% | 0.00% | 0.00% | 99.33% |

## Disclosures and limitations

- Realized volatility and cash shares differ across benchmarks. The 2009-2022 mean share of cash and BIL is 36.41% for B3, 7.89% for B1 and 4.80% for B2. Identical caps do not imply equal risk (protocol line 87).
- Drift. Actual ETF weights between decisions can exceed the target caps (protocol line 73): the maximum actual weight of an ETF is 25.37% for B2 and 25.20% for B3, above the 25% target cap, while no target weight exceeded it. Group maxima stay below 50%.
- REF_SPY has no risk controls. It holds 8.11% in cash and BIL on average because distributions are not reinvested after the single purchase (D022, item 7).
- B0 differs from the theoretical BIL index by costs, the 1% reserve, USD cash, whole-share rounding and the timing of reinvestment at monthly decisions (D022, item 10), so the standard deviation of its excess return is very small and its Sharpe ratios (for example -6.971 in 2017-2019 and -11.434 in 2019) are not economically meaningful.
- B3 turnover of about 2.9 times NAV a year arises mainly from instruments entering and leaving the trend selection, with the offsetting trades in BIL (in B3, 35.2% of traded notional opens or closes a risky position and 39.3% is BIL, against 2.5% position openings and closings in B1 and B2, essentially the initial entry); the absence of a trade threshold (D021 item 4) adds small re-sizing orders in every benchmark.
- Nothing after 2022-12-30 is computed or published. The report contains no comparison of candidates: no differences in utility, bootstrap, Holm adjustment or regressions, no H1/H2 values and no statement about which benchmark is better. H1/H2 remain `registered_not_tested`, and the reserved period remains closed.
- This is a historical simulation on data that are not point-in-time; `available_at` is a modeling assumption. The seven Yahoo corrections were accepted by the user's decision that the issuer is authoritative and have no independent confirmation (D016). The `confirmed_no_distributions` basis for GLD is weaker than a statement that distributions never occurred (D018). The completeness of DBC before 2007-12-17 is not proven by the issuer document (D017). The universe is retrospective. The data readiness conditions and their disclosure: D019, D020.
- Costs are modeled at 10 bps per side, not measured, and Open is a modeled price; the results do not reflect settlement, auction fills, liquidity or brokerage constraints. The payable-date contract check starts at 2007-05-30 (D021, item 13).
- The results describe the behavior of the benchmark rules on this history. They do not establish an investable track record or an alpha.
