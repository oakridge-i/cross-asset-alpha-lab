# Mathematics of Cross-Asset Alpha Lab: formulas, proofs and verification of the implementation

Date of the review: 10 October 2026. Source version examined: `7a8ba1d56938e2576b537fff670ba0363e6e618c`. Project: Cross-Asset Alpha Lab.

## Organization of this review

This document gives a detailed account of the mathematical chain of the project, from the raw price to the planned conclusion about the effect of a strategy. For each substantive formula it states the meaning, purpose, derivation, assumptions and limits of applicability. The review covers the current N1-N4, the implemented descriptive metrics and the registered mathematics of the future N5/N6. At this version N5 exists as an approved specification and not as a working statistical module.

The accounting identities, the feature computation rules and the weight construction have clear mathematical foundations. Profitability, new alpha, optimality of the parameters or reliability of forecasts do not follow from them. Some of the stated properties require clarification: the 10% level refers to a risk estimate relative to BIL; H2 preserves the concentration limits but not necessarily a risk limit; the seven invariants are useful checks but not a complete proof that all position movements are self-financing.

The review did not modify the source code, tests, configurations, protocol, decisions or the experiment journal. The actual closed H1/H2 return figures, their NAV and the results for reserved periods were not opened, and no new historical research runs were performed. Counterexamples and additional checks use synthetic data.

### Five meanings of "prove"

| Type of statement | What can be established | Example in the project |
|---|---|---|
| Algebraic identity | Derived exactly from the definitions and the accounting assumptions | NAV = USD + value of positions + receivable |
| Property of an algorithm | Proved for all admissible inputs in exact arithmetic | The sum of the inverse-volatility weights is $m/K$ |
| Statistical theorem | Proved conditionally on assumptions about distribution and dependence | FWER control by the Holm method for valid individual p-values |
| Model convention | Consequences can be explained; universal truth cannot be proved | 10 bps, 252 sessions, gamma=3, reserve of 1% |
| Empirical hypothesis | Tested on data with account of uncertainty | Momentum adds value after costs |

A numerical check confirms a specific example; it does not replace a theorem. A passing test confirms the expected behavior on the given inputs; it is not a formal verification of the whole Python code, NumPy, pandas, the data provider or the market. All analytical proofs below refer to the stated assumptions; machine arithmetic is treated separately.

### Impossibility of proving future profit from a single history

Let a deterministic rule $f$ observe the history $H_t$ and choose weights $w_t=f(H_t)$. Consider two worlds with exactly the same history up to $t$. In the first, the subsequent returns of the selected assets are favorable; in the second, they are unfavorable. The rule must produce the same $w_t$ in both worlds, because its input is the same. If the next portfolio return differs between the worlds, the past observations and the algebra of the rule do not determine the sign of the future result.

To compare two idealized portfolios with different risky weights $w$ and $b$, take $d=w-b\ne0$ and future returns $r^+=\varepsilon d$, $r^-=-\varepsilon d$, with $\varepsilon>0$ small enough that simple returns exceed $-1$. The difference of returns is then $+\varepsilon\|d\|^2$ and $-\varepsilon\|d\|^2$ respectively. Both continuations are compatible with the same past history. This proves that a past signal gives no unconditional guarantee of outperformance; costs and execution add constraints but do not remove this non-identifiability. A positive conditional expected return requires additional empirical assumptions about the market process.

## Reading guide

1. Part I (data): share units, the future split factor, total return, the Adj Close check, reconciliation of dividends, tolerances, corrections and data provenance.
2. Part II (signals and portfolio): sample volatility, covariance, momentum, H1/H2, inverse volatility, limits, risk relative to BIL, baseline strategies, causality and diagnostic aggregates.
3. Part III (accounting and execution): NAV, receivable, splits, orders, rounding, fill coefficient, cash constraint, costs, the exact decomposition of profit and the financial invariants.
4. Part IV (evaluation and conclusions): returns, CAGR, volatility, Sharpe ratio, utility, walk-forward, P_A1, bootstrap, Holm, OLS/HAC, alpha, scenarios and joint decision criteria.
5. Closing appendices: the implementation map, verified limitations, results of the current checks and references to primary methodological sources.

The document is a single connected text. Notation is introduced locally: for example, $q_i$ in Part II denotes the initial weight, whereas the number of shares in Part III is usually denoted by a separate letter. $E$ in the H2 filter is the ratio of monthly growth factors minus one; $e$ in the utility is the arithmetic difference of daily returns. They must not be substituted for one another.

## Overall computation chain

$$\text{source and corporate actions}
\longrightarrow \text{as-traded prices and distributions}
\longrightarrow T_{i,d}
\longrightarrow (M,\sigma,\Sigma,E)
\longrightarrow \text{selection and target weights}
\longrightarrow \text{orders at the available close}
\longrightarrow \text{execution at the future open}
\longrightarrow \text{positions, USD, receivable}
\longrightarrow NAV_d
\longrightarrow \text{descriptive and statistical estimates}.$$

The first branch, $T$, is the theoretical reinvestment used for features and reference series. The second branch, NAV, is the actual model of share ownership, costs, cash receipts and constraints. Replacing the NAV accounting by the TR index while also adding dividends as cash would produce double counting. For this reason the project keeps the two branches strictly separate.

## Map of mathematical objects

| Object | Unit | Purpose |
|---|---|---|
| Price $C,O$ | USD per current share | Valuation of a position and the actual number of shares |
| Split $s$ | new shares / old shares | Reconciliation of quantity and price |
| Distribution $D$ | USD per new share on the ex-date | Return from holding, entitlement to payment |
| TR index $T$ | Dimensionless normalized capital | Comparable features that include distributions |
| Simple return $r$ | Fraction per session/month | Change in capital |
| Momentum $M$ | Relative cumulative return | Historical outperformance relative to BIL |
| Volatility $\sigma$ | Annual scale of return | Normalization of the score and inverse-volatility sizing |
| Covariance $\Sigma$ | Square of the annual scale of return | Joint risk relative to BIL |
| Weight $q,v,w$ | Fraction of capital | Successive stages of allocation |
| Number of shares | Shares in consistent units | Self-financing accounting |
| Cash/receivable/NAV | USD | Available money, claim, wealth |
| Turnover | Fraction of decision-NAV per decision | Volume of trades executed |
| Utility $U$ | Annual mean-variance measure | Fixed criterion of risk-adjusted value |
| $\Delta U$ | Difference of annual utilities | Increment relative to a given comparator |
| Bootstrap CI/p | Interval/probability estimate under assumptions | Uncertainty of the effect |
| Alpha | Intercept relative to specific regressors | Residual mean return of the model |

The absence of leverage is a property of the weights and of the cash constraint, not a promise of the absence of losses. The absence of short positions means non-negative position quantities; individual factor exposures or covariances may nevertheless have a negative sign.

---

## Part I. Data, corporate actions and data provenance

Code examined: `7a8ba1d56938e2576b537fff670ba0363e6e618c`, verification date 10 October 2026. This part is a review of source code and contracts, not a new research run. The actual data directories, hypothesis results and the reserved period were not read. Sources, tests, configurations and the experiment journal were not modified. Every mathematical proof below is conditional: it establishes properties of a formula under the listed assumptions, but it does not establish the truth of the input economic data.

Main sources: `DATA_CONTRACT.md`, `src/alpha_lab/normalize.py`, `src/alpha_lab/quality.py`, `src/alpha_lab/reconcile.py`, `src/alpha_lab/corrections.py`, `src/alpha_lab/provenance.py`. The linking layer `src/alpha_lab/pipeline.py` is needed to check that the source JSON matches the adapter, to check the provenance of corrections and to verify exact replay. From `features.py` only the theoretical total return index and the daily return are examined here; signals and risk estimation belong to other parts of the document.

### 1. Notation and domain

For a single ETF let $t=0,1,\ldots,n$ be consecutive regular XNYS sessions. The sequence contains actual sessions, not every calendar day. Let:

| Notation | Meaning | Unit |
|---|---|---|
| $p_t$ | raw Yahoo Close, expressed by the provider on the later share-count basis | USD per raw provider unit |
| $a_t$ | raw Yahoo Adj Close | USD per adjusted unit |
| $d_t^{src}$ | raw Dividends + Capital Gains | USD per raw unit |
| $s_t$ | number of new shares per old share in session $t$; $s_t=1$ without an event | dimensionless |
| $F_t$ | product of the strictly later split factors | dimensionless |
| $C_t$ | Close in the historical units actually traded at $t$ | USD per historical share |
| $D_t$ | total distribution per historical share on the ex-date | USD per historical share |
| $T_t$ | theoretical reinvested wealth index, $T_0=1$ | dimensionless |

In the raw `Stock Splits` column zero denotes the absence of an event. This is an encoding of absence, not a mathematical share ratio: before any computation zero is replaced by one. Negative factors are rejected; a positive fractional factor is allowed and corresponds to a reverse split. Implementation: `src/alpha_lab/normalize.py:111`.

Under exact arithmetic the proofs assume $p_t,C_t,a_t>0$, $D_t,d_t^{src}\ge0$, $s_t>0$. The normalizer checks finiteness and signs of the raw numbers, chronological order and the OHLC conditions:

$$
L_t\le\min(O_t,C_t),\qquad H_t\ge\max(O_t,C_t).
$$

Consequently $L_t\le O_t\le H_t$ and $L_t\le C_t\le H_t$. For positive $F_t$, multiplying all four prices by $F_t$ preserves these inequalities. The raw volume must be finite and non-negative. Checks: `src/alpha_lab/normalize.py:66`.

For Yahoo, simultaneous positive Dividends and Capital Gains are rejected, because it has not been confirmed whether the source includes one in the other. The row `source_dividend = Dividends + Capital Gains` therefore does not permit mechanically adding two positive quantities on an unknown basis. By contrast, for the SSGA issuer table the basis of the sum is stated explicitly, and the parser adds the dividend, the short-term and long-term capital gain distributions. If all three cells are empty, no distribution amount is proven and an error is raised; at least one explicitly stated zero cell can prove a zero amount. Implementation: `src/alpha_lab/evidence.py:75`.

The purpose of these restrictions is to define the admissible domain in which the financial formulas are meaningful. They cannot establish that a positive price or amount is actually correct.

### 2. Restoring historical units: the factor of later splits

#### 2.1. Formula and proof

The code uses

$$
F_t=\prod_{u=t+1}^{n}s_u,
\qquad C_t=p_tF_t,
\qquad D_t^{Y}=d_t^{src}F_t.
$$

The vectorized implementation first obtains the product that includes the current factor, going from right to left, and then divides by $s_t$:

$$
\frac{\prod_{u=t}^{n}s_u}{s_t}
=\prod_{u=t+1}^{n}s_u.
$$

The empty product in the last row equals 1. For this reason the split of the current session is not part of $F_t$: for that session the prices and the distribution already refer to the new shares. If another split follows the current one, $F_t$ still includes the later event; excluding the session's own factor does not mean that $F_t$ must equal 1 on every split date. Code and output columns: `src/alpha_lab/normalize.py:111`.

The economic assumption is that the provider has already divided the old prices by every later split factor. For a future 3:1 event, a historical price of 30 becomes a raw price of 10, and restoration multiplies 10 by 3. For a reverse 1:2 split, a historical price of 45 is represented as 90, and restoration multiplies 90 by 0.5.

Example from a verified test: raw Close `[90,90,90,91]` with factors `[1,1,0.5,1]` becomes the historical traded prices `[45,45,90,91]`. On the day of the reverse split the number of shares is halved and the price doubles; the value of the position does not change. Test: `tests/test_normalize.py:21`.

Counterexample to unconditional applicability. If the input `[30,30,10]` is already expressed in historical traded units and the current split factor is 3, repeated multiplication gives `[90,90,10]`. The return on the event day becomes $3\cdot10/90-1=-2/3$, although the actual split created no loss. External confirmation is therefore required that the Yahoo prices are in fact adjusted for splits. The mere presence of a correct 3:1 event does not confirm the basis of distributions.

#### 2.2. Invariance of past inputs under later splits

Consider a new version of the source after a future split with factor $b>0$ that occurs later than all past sessions under examination. If the provider changes its basis correctly:

$$
p'_t=p_t/b,
\qquad d_t^{src\prime}=d_t^{src}/b,
\qquad F'_t=bF_t.
$$

Then

$$
C'_t=p'_tF'_t=(p_t/b)(bF_t)=C_t,
\qquad D_t^{Y\prime}=(d_t^{src}/b)(bF_t)=D_t^Y.
$$

The past $s_t$ are also unchanged. Consequently, any algorithm that uses only past restored prices, distributions and split factors receives the same past input. For several new splits, their product is taken in place of $b$. This is an exact algebraic invariance with respect to a consistent change of units.

A verified synthetic test compares the history of Close `[30,29]` and distributions `[0,1]` with the extended history of Close `[10,29/3,10,11]`, distributions `[0,1/3,0,0]` and a late 3:1 split; the past Close, distributions and $T$ agree to the tolerance of the test. Source: `tests/test_normalize.py:36`.

The assumptions are essential:

1. The provider recomputes both prices and distribution amounts consistently.
2. All splits relevant to the basis applied by the provider are represented within the horizon used.
3. An issuer correction in historical traded units is stored as a historical amount and is not rescaled again by the new $F_t$.
4. Only changes of units are allowed. Correcting a wrong old price or distribution is a different transformation and can change past features.

The factor of later splits is therefore not an independent predictive signal. This fact, however, does not establish the historical availability of the whole data set: late published corrections and revised history remain a separate problem. In floating-point arithmetic the proven identity can be violated by a rounding amount; an identical mathematical history does not guarantee identical bytes across versions of numerical libraries.

#### 2.3. Rationale for not rescaling volume

The basis of the raw Volume does not follow from $C_t=p_tF_t$. If the raw volume were guaranteed to be expressed in current equivalent shares, the possible inverse formula would be $V_t^{trade}=V_t^{src}/F_t$. The contract, however, contains no confirmation of this assumption. The code therefore stores `source_volume` and marks it `source_unconfirmed_not_used`. The contract prohibits using it for execution, liquidity limits or determining quantities. This is a correct limit of what can be proven, not a missing necessary formula. See `src/alpha_lab/normalize.py:120` and `DATA_CONTRACT.md:25`.

### 3. Theoretical total return: derivation from share counts and distributions

#### 3.1. A single transition between sessions

Suppose that before the event an investor holds $q_{t-1}$ old shares worth $q_{t-1}C_{t-1}$. The split creates $q_{t-1}s_t$ new shares. If $D_t$ is paid per new share, the total entitlement to the distribution equals $q_{t-1}s_tD_t$. The economic wealth on the ex-date, taking this entitlement into account, is:

$$
W_t=q_{t-1}s_tC_t+q_{t-1}s_tD_t
=q_{t-1}s_t(C_t+D_t).
$$

The gross return factor is therefore:

$$
G_t=\frac{W_t}{q_{t-1}C_{t-1}}
=s_t\frac{C_t+D_t}{C_{t-1}},
\qquad r_t=G_t-1.
$$

The quantity $q_{t-1}$ cancels. This proves that the formula does not depend on the arbitrary scale of the initial position. For a split without a distribution and without movement of economic value, $C_t=C_{t-1}/s_t$, so $G_t=1$. For an ordinary distribution without other movement, $C_t=C_{t-1}-D_t$, so $G_t=1$ as well: the price decline is offset by the entitlement to the cash distribution.

If a 3:1 split and $D_t=1$ occur simultaneously, the old Close 30 and the new Close 9 give $G_t=3(9+1)/30=1$. On that session the distribution is already stated per new share; multiplying the distribution again by the current factor 3 inside $F_t$ would produce the erroneous $G_t=3(9+3)/30=1.2$. Verified example: `tests/test_normalize.py:28`.

#### 3.2. The multi-period index and reinvestment

If distributions are theoretically reinvested immediately at the Close $C_t$, the new quantity is:

$$
q_t=q_{t-1}s_t+\frac{q_{t-1}s_tD_t}{C_t}
=q_{t-1}s_t\left(1+\frac{D_t}{C_t}\right).
$$

Consequently $q_tC_t=W_t$. At the next step this wealth is again multiplied by the corresponding $G_{t+1}$. By induction:

$$
T_0=1,
\qquad T_t=T_{t-1}G_t
=\prod_{u=1}^{t}G_u.
$$

This is a theoretical index with immediate reinvestment of the entitlement to the distribution, fractional shares and no costs. In an actual simulated account, a distribution is a receivable until the pay date and cash afterwards; it must not be counted both as reinvested return of the position and again as a cash credit. The index is suitable for comparing the economic movement of an instrument and for computing features; it does not automatically equal the NAV of a purchasable ETF or an achievable portfolio return. See `src/alpha_lab/normalize.py:138` and `src/alpha_lab/features.py:19`.

The first row is forced to have $G_0=1$. There is no $C_{-1}$, so an initial distribution or split does not create an invented return before the start of observation. This is a choice of starting point, not a denial of the event itself. To evaluate the return of an event on the first session of interest, a preceding Close is required.

`features.daily_returns` computes $T_t/T_{t-1}-1$ and drops the first row. The equality with $G_t-1$ follows directly from the recursion. `features.total_return_index` independently repeats the same formula and additionally rejects a non-finite or non-positive final index; the normalizer does not check this postcondition. Sources: `src/alpha_lab/features.py:19`, `src/alpha_lab/features.py:31`.

#### 3.3. Algebraic cancellation of the factor and its limits

For consecutive sessions $F_{t-1}=s_tF_t$. Before correction with issuer data:

$$
G_t=s_t\frac{F_t(p_t+d_t^{src})}{F_{t-1}p_{t-1}}
=\frac{p_t+d_t^{src}}{p_{t-1}}.
$$

For a consistent split-adjusted source the same theoretical $G_t$ can therefore be obtained without a separate restoration of historical prices. Restoration is still needed for historical execution: share quantities, price levels and cash amounts must have real units. With the issuer-based correction $D_t^I$ in place of $F_td_t^{src}$, the cancellation of the distribution in this form no longer applies.

Agreement between the implementations in `normalize` and `features` is not independent proof that the basis is correct: both can process mistaken units in the same way. The manual derivation above and the tests with a simultaneous split and distribution check the stronger economic basis.

### 4. Reconciliation of distributions with issuer records

#### 4.1. Bases of amounts

For an issuer event on date $d$ the code recomputes $F(d)$ as the product of all split factors strictly after $d$, including for a date that is not a session of the table. If the issuer declares `current_units`, the following applies:

$$
D_d^I=D_d^{I,raw}F(d).
$$

For `as_traded` the amount is unchanged: $D_d^I=D_d^{I,raw}$. The Yahoo amount in historical units and the issuer amount are then rounded to 10 decimal places; the difference is also rounded to 10 places. Date comparison uses the ISO format, whose lexicographic order coincides with calendar order. Implementation: `src/alpha_lab/reconcile.py:58`.

Sources of one ticker are not merged automatically: several distribution sources cause a refusal, so that one distribution is not added twice. The issuer parsers reject repeated ex-dates, NaN/Inf and negative total amounts. For iShares, several embedded tables must coincide; otherwise the parser refuses to choose one. See `src/alpha_lab/reconcile.py:13`, `src/alpha_lab/evidence.py:26`, `src/alpha_lab/evidence.py:120`.

#### 4.2. Derivation of the tolerance 0.0005

If Yahoo rounds the amount to the nearest multiple of the step $h=0.001$ USD, the rounding error is bounded by $h/2=0.0005$. Two rounding bases are possible:

$$
|\varepsilon_{trade}|\le0.0005,
\qquad |\varepsilon_{src}F|\le0.0005F.
$$

A single upper bound for either of these two cases is:

$$
\tau(F)=\max(0.0005,0.0005F)
=0.0005\max(1,F).
$$

This is an absolute monetary tolerance in historical traded units; it is not a relative percentage, a standard error or a statistical significance level. For $F=3$ the tolerance is 0.0015; for $F=0.5$ it remains 0.0005. The issuer may apply its own rounding; its error does not follow automatically from this formula. The formula rests on the contractual choice of known Yahoo bases and not on a universal error bound for arbitrary providers.

The `matched` criterion:

$$
|\operatorname{round}(D_d^Y-D_d^I,10)|\le\tau(F(d))+10^{-12}.
$$

The addition of $10^{-12}$ is intended for borderline binary rounding. Quantization to 10 decimal places can change the difference by up to about $5\cdot10^{-11}$; the criterion therefore applies to the rounded quantities and is not a strict test of equality of unrounded values. Relative to the ordinary tolerance $5\cdot10^{-4}$ this term is small. A shared tolerance function and an identical rule for `replace` exclude the situation in which the reconciliation classifies an event as `matched` but a correction nevertheless changes it. Code: `src/alpha_lab/normalize.py:23`, `src/alpha_lab/normalize.py:62`, `src/alpha_lab/reconcile.py:81`.

Verified test: an issuer amount of 0.648931 in current units and $F=3$ give 1.946793 in historical traded units; Yahoo 1.947 differs by 0.000207 and is classified as `matched`. A difference of 0.0012 is also `matched`; 0.0016 is already `amount_mismatch`. Source: `tests/test_reconcile.py:186`.

#### 4.3. Discrepancy classes as a partition of the set of events

Let $Y$ be the dates of positive Yahoo distributions in the window, $I$ the dates of positive issuer distributions, and $[a,b]$ the first and last ex-date in the whole issuer table, including explicitly zero rows. The loop runs over the union of $Y$ and $I$, so an isolated zero issuer row without a Yahoo event does not turn into a distribution.

For each $d\in Y\cup I$ the classes are applied in the following order:

| Condition | Class | What is actually established |
|---|---|---|
| issuer event absent and $d$ outside $[a,b]$ | `outside_issuer_coverage` | no issuer table covers this Yahoo date |
| Yahoo event absent, issuer states a positive amount | `issuer_only` | the Yahoo source contains no positive event |
| Yahoo states a positive amount, no positive issuer amount inside the coverage | `yahoo_only` | discrepancy; the absence of a row does not prove a zero distribution |
| both amounts present, difference within tolerance | `matched` | amounts agree on this date on this basis |
| both amounts present, difference outside tolerance | `amount_mismatch` | amounts disagree |

Under these conditions the classes are mutually exclusive and cover the loop. `confirmed` means that no class other than `matched` occurs. This is a statement about agreement of the presented events, not proof that the history is complete. If both sources omit an event, it is not in $Y\cup I$ and the loop does not see it. If both sources have the same erroneous amount, they are also `matched`.

A verified additional counterexample: the requested window is 2017-11-28 to 2017-11-29, there are no Yahoo events, and the issuer has a single zero row on 2010-01-04. The result is `confirmed`, the number of all events inside the window is zero, and the coverage is 2010-01-04 to 2010-01-04. Full coverage of the requested window is not checked by a separate condition. `confirmed` therefore cannot be converted into the statement "the issuer has confirmed the complete history in the window". The contract requires a separate completeness check. See `src/alpha_lab/reconcile.py:61` and `DATA_CONTRACT.md:47`.

The GLD status `confirmed_no_distributions` is built differently: it requires a source document with a corresponding statement and zero Yahoo events in the window. Before classification, the document must be in a verified manifest with the correct hash. The code does not prove the semantic truth of the PDF text: it uses the registered `no_distributions` and `basis` as an external expert assumption. If a Yahoo distribution is found, the result is `unresolved`. Without an issuer source, the absence of Yahoo events gives `unverified_no_issuer_source`, not a confirmation. Sources: `src/alpha_lab/reconcile.py:13`, `src/alpha_lab/reconcile.py:122`.

#### 4.4. Materiality in basis points: interpretation and limits

In `compare` the following is computed:

$$
M=10^4\sum_{d\in\mathcal C}\frac{|D_d^Y-D_d^I|}{C_{d^-}},
$$

Here $d^-$ is the last observed session strictly before the ex-date, a missing amount on one side is replaced by 0, and the set of compared events excludes `outside_issuer_coverage`. The sum includes the differences of `matched` events as well. The factor $10^4$ converts the dimensionless fraction into basis points: 1 bps = 0.0001.

For $s_d=1$ the difference between two one-period theoretical returns at the same price is indeed

$$
r_d^Y-r_d^I=\frac{D_d^Y-D_d^I}{C_{d^-}}.
$$

$M$ is therefore the sum of absolute monetary discrepancies normalized by prices, without offsetting between positive and negative differences. In a verified test the sum $0.0004+0.0011+0.25+0.3=0.5515$ USD at a previous Close of 100 gives $M=55.15$ bps. Source: `tests/test_reconcile.py:164`.

On a split day, however, the exact difference is:

$$
r_d^Y-r_d^I=s_d\frac{D_d^Y-D_d^I}{C_{d^-}}.
$$

The code's $M$ does not contain the factor $s_d$. An additional verified example: old Close 30, 3:1 split, Yahoo distribution 1 and issuer distribution 2 per new share. `materiality_bps` equals $333.3333\ldots$, while the one-period economic discrepancy equals $1000$ bps. This limits the economic interpretation of this diagnostic measure. The code formula matches its own description but is not an exact measure of return error when a split and a distribution coincide.

Moreover, $M$ does not equal the difference of cumulative returns. For two variants of distributions:

$$
\frac{T_n^Y}{T_n^I}
=\prod_{d=1}^{n}\frac{C_d+D_d^Y}{C_d+D_d^I},
$$

If prices and splits are identical, the exact terminal difference requires a product, not a sum. For small differences the first-order term uses $(D_d^Y-D_d^I)/(C_d+D_d^I)$; in general this also differs from the denominator of the previous Close used in $M$. Materiality serves as a diagnostic of the scale of discrepancies; it cannot be presented as an established loss of a specific portfolio.

### 5. Corrections: admissible operations and preservation of the past

#### 5.1. How a correction is constructed

`derive` creates only three types:

$$
\text{issuer\_only}\mapsto\text{add},\qquad
\text{amount\_mismatch}\mapsto\text{replace},\qquad
\text{yahoo\_only}\land\text{explicit issuer zero}\mapsto\text{remove}.
$$

No `matched` row is corrected. The absence of an issuer row is not replaced by zero: `remove` is allowed only with a registered explicit zero row on the exact ex-date. This is the distinction between absence of evidence and evidence of absence. `corrections_run` refuses to create the next frozen version of corrections from a reconciliation that was already computed with corrections: otherwise discrepancies that have disappeared could erase corrections and change provenance. Sources: `src/alpha_lab/corrections.py:18`, `src/alpha_lab/corrections.py:49`.

`check_correction` additionally requires a finite non-negative issuer amount and a non-empty source reference. `add` and `replace` must have a positive issuer amount; `remove` requires exactly 0. For `add` the original amount must be zero with threshold $10^{-9}$. For `replace`/`remove` the original event must be non-zero, and the declared `yahoo_amount` must coincide with it within the absolute tolerance $10^{-9}$. A `replace` within the `matched` tolerance is prohibited. The date of the corrected event must be a session of the table. Code: `src/alpha_lab/normalize.py:38`, `src/alpha_lab/normalize.py:130`.

The threshold $10^{-9}$ is a technical check that the correction corresponds to the original event, whereas the tolerance $0.0005\max(1,F)$ is the economically defined tolerance for agreement between Yahoo and the issuer. These are different checks. In particular, the reconciliation may regard a positive original distribution not exceeding $10^{-9}$ as an event, while the admissibility check of a correction regards it as absent. For real dollar amounts of ordinary scale the boundary is small; without a lower bound on admissible distributions, the components share no universal criterion for when an event exists.

The check for a non-empty source reference in the low-level normalizer does not examine the text of the reference and does not prove that the issuer amount was extracted from a document. The pipeline of frozen snapshots adds a chain of hashes; a manual dictionary is accepted and does not automatically acquire such provenance evidence.

#### 5.2. Mathematics of the corrected index

Suppose that only the distribution in session $k\ge1$ changes, $D_k\to\widetilde D_k$, while prices and splits remain as before. Then

$$
\widetilde G_k/G_k
=\frac{C_k+\widetilde D_k}{C_k+D_k},
$$

and all other $G_t$ are unchanged. Consequently,

$$
\widetilde T_t=T_t\quad(t<k),
\qquad
\frac{\widetilde T_t}{T_t}
=\frac{C_k+\widetilde D_k}{C_k+D_k}\quad(t\ge k).
$$

For the set of corrected dates $K$:

$$
\frac{\widetilde T_t}{T_t}
=\prod_{k\in K,\;1\le k\le t}
\frac{C_k+\widetilde D_k}{C_k+D_k}.
$$

This proves that the prefix before the first correction is unchanged and that a single correction has a constant multiplicative effect on subsequent index levels. Later daily returns outside the corrected dates are preserved, although later levels are shifted. In the first row, $k=0$, a correction does not change $T$, because $G_0$ is forced to 1.

The code first records the corrected $D_t$, retains `source_dividend`, the basis and the source reference, and then builds $T$. Prices and splits are not corrected. The tests cover `replace`, `add`, `remove`, the absence of a pay date for `remove`, an exactly unchanged prefix, corrections on a split day and the preservation of unaffected events. Sources: `src/alpha_lab/normalize.py:130`, `tests/test_normalize.py:101`.

Causality of the formula is not the same as historical availability of the correction. If an error was discovered in 2026, the processed old 2012 distribution can influence a simulated 2012 signal. This is a historical reconstruction with corrected knowledge, not proof that the corrected amount was published before the 2012 decision.

#### 5.3. Linking a correction to the source data vintage

For a path inside a frozen snapshot, `check_vintage_lineage` requires that the hash of the source manifest match through the reconciliation; for a copy in a derived snapshot it requires that the hash of the source snapshot and the bytes of the correction match the indicated frozen version of corrections. Pay dates from a different frozen catalog are rejected. One transition through a derived snapshot is allowed; beyond that the reference must lead to a version of corrections, which prevents arbitrary recursion through derived snapshots.

If a correction is supplied as a dictionary or a file without a manifest, there is no complete chain: the low-level checks of amount and source remain, but provenance back to issuer evidence is not derived. This is an intended branch and is not equivalent to provenance through a frozen chain of issuer documents. See `src/alpha_lab/pipeline.py:103`.

### 6. Calendar and availability of cash

#### 6.1. Session completeness as equality of sequences

Within normalization, the ordered observed index is checked for equality with the regular XNYS sessions from the first to the last observed row. Duplicates and violations of sorting are excluded beforehand. This is stronger than intersecting the calendars of the assets: a date missing identically for all assets must not vanish from the expected calendar.

The separate `assess` builds the set $E$ of sessions of the requested common window and, for each ETF, the set $O_i$ of observed dates:

$$
\text{missing}_i=E\setminus O_i,
\qquad \text{unexpected}_i=O_i\setminus E.
$$

These differences detect gaps at the boundary: an internally complete table with a late start may be insufficient for the common window. Exceptional closures and weekends are not in $E$; the absence of such a row is not a missing price. The tests cover the Sandy closures of 2012-10-29/30, the early close after Thanksgiving and the omission of a boundary session. See `src/alpha_lab/normalize.py:108`, `src/alpha_lab/quality.py:48`, `tests/test_quality.py:45`.

#### 6.2. The pay date as rounding up in the session calendar

For an ex-date $e$, a declared pay date $p\ge e$ and the set of regular sessions:

$$
\pi(p)=\min\{s\in\mathcal S:s\ge p\}.
$$

The actual issuer date takes priority. Without it, the conditional date $p=e+\delta$ counts calendar days; in the main scenario $\delta=10$. Other permitted delays are used as separate assumptions. `normalize` writes into `payable_date` the session on which the cash is credited, which can differ from the calendar date of the issuer. For example, a declared Saturday date is moved to Monday. The column must not be interpreted as always being the literal date declared by the issuer.

Conditions for an actual date: a source reference exists, the date is valid, and the payment is not earlier than the ex-date. At the reconciliation stage the pay date is taken only from `matched` events; `add`/`replace` corrections may carry a separate issuer date, and a conflict between two actual dates leads to a refusal. For `remove` the pay date is not filled in. The calendar is extended beyond the last price date so that admissible future payments have a crediting session, but no future prices are added. Sources: `src/alpha_lab/reconcile.py:142`, `src/alpha_lab/normalize.py:90`, `src/alpha_lab/normalize.py:145`.

Recording a future pay date does not mean that a future price or market return entered a signal. A public historical table may, however, contain information that became known late; the actual historical availability of the relevant fields requires separate evidence of the time of publication and receipt.

#### 6.3. Temporal availability

`available_at` is modeled as 18:00 America/New_York on the given session, including on early-close days; the offset from UTC varies with daylight-saving rules. `retrieved_at` is the actual date on which the history was retrieved. These timestamps denote different facts:

$$
\text{modeled usable time}\ne\text{proved original publication time}.
$$

In the normalizer, `availability_basis` states explicitly `historical_model_assumption`. A historical `available_at` does not establish that the modern version of a Yahoo row or of a correction was known at that old close. A causal algorithm on a frozen data version means that it does not access the subsequent rows of that model; a data set with actual historical availability also requires excluding late revisions. See `src/alpha_lab/normalize.py:141`, `DATA_CONTRACT.md:33`.

### 7. Adj Close check: derivation of the residual and the difference from economic total return

#### 7.1. Model of retrospective adjustment

Denote $B_t=a_t/p_t$. In the model of retrospective adjustment for Yahoo distributions under examination, the old prices are multiplied by

$$
f_t=1-\frac{d_t^{src}}{p_{t-1}}.
$$

If $B_t$ contains the product of strictly future distribution adjustment factors, then

$$
B_{t-1}=f_tB_t,
\qquad\frac{B_t}{B_{t-1}}=\frac{1}{f_t}.
$$

Hence the residual:

$$
\varepsilon_t
=\frac{B_t}{B_{t-1}}
\left(1-\frac{d_t^{src}}{p_{t-1}}\right)-1.
$$

When the data are consistent with this model, the residual equals zero. The code uses exactly this formula in `src/alpha_lab/quality.py:55`, checking whether the absolute residual exceeds 0.00005 by default, that is, 0.5 bps. This is a relative residual of the adjustment multiplier; it is not a dollar error of the distribution and not the same quantity as `materiality_bps`.

It is expected that $d_t^{src}<p_{t-1}$, so that $f_t>0$. The normalizer itself does not restrict this ratio. A non-zero adjustment is not independent confirmation, because both Adj Close and the events come from Yahoo. It can detect a missing event when the adjustment is retained, but two consistently wrong columns will pass the check.

#### 7.2. Difference between the Adj Close return and $T$

Without a split, or in consistent split-adjusted units:

$$
G_t^{adj}=\frac{a_t}{a_{t-1}}
=\frac{p_t}{p_{t-1}-d_t^{src}},
\qquad
G_t^{econ}=\frac{p_t+d_t^{src}}{p_{t-1}}.
$$

Subtracting:

$$
G_t^{adj}-G_t^{econ}
=\frac{d_t^{src}(p_t-p_{t-1}+d_t^{src})}
{p_{t-1}(p_{t-1}-d_t^{src})}.
$$

Equality holds for a zero distribution or for $p_t=p_{t-1}-d_t^{src}$, that is, a pure price decline equal to the distribution with no other movement. In general, retrospective scaling and buying additional shares at the ex-date Close are different reinvestment rules.

Verified example: $p_{t-1}=100$, $p_t=100$, distribution 1, Adj Close `[99,100]`. The residual of the check is exactly 0; $G^{econ}=1.01$, but the factor from Adj Close equals $100/99$. The difference is about 1.0101 bps for one transition. Using daily Adj Close returns in place of an explicitly chosen economic total return index therefore replaces the formula of the model, even when the check passes.

`assess` uses `source_dividend`, not the corrected distribution, and the raw prices. Issuer-based corrections change the economic series but do not rewrite the history of the diagnostic Yahoo factor. One cannot expect a correction to reduce this residual of the raw source automatically. The function does not publish a separate diagnostic series $G^{adj}-G^{econ}$; a comparison that is not present cannot be recovered from the residual alone. The existence of such a separate comparison in manual or other checks cannot be asserted on the basis of `assess`.

#### 7.3. Meaning of `technical_pass`

For each input table `assess` counts missing and unexpected sessions and tolerance exceedances. Formally:

$$
\text{technical\_pass}
=\mathbf1\{\text{frames nonempty}\}
\land\bigwedge_i
\{\text{missing}_i=\varnothing,
\text{unexpected}_i=\varnothing,
\nexists t:|\varepsilon_{i,t}|>\eta\}.
$$

`data_ready_for_n2` remains fixed at false. The number of rows, the number of events by year, the number of actual payments and the largest residuals are descriptive diagnostic indicators. None of them proves the size of all historical distributions, the right to use the data or their past availability. This is the correct distinction between a technical result and research admission. Code: `src/alpha_lab/quality.py:48`.

### 8. Gaps in numerical checks confirmed by synthetic examples

For the ordinary range of ETF prices and splits, the proofs above are consistent with the verified tests. A finite input, however, does not imply a finite result: a product of finite positive numbers can overflow, and a ratio can round to 0.

N1-NUM-1: no postcondition of finiteness for the normalized quantities. Synthetic raw Close `[1,1,1]` and split factors `[0,1e308,1e308]` are finite and pass the input check. The reverse cumulative product overflows. The resulting Close, factors and TR are not all finite, and $T$ is output as `[1.0, NaN, 0.0]`. `quality.assess` with identical raw Close and Adj Close returns `technical_pass=true`, because its residual refers to the raw columns and not to the normalized outputs. The cause is localized in `src/alpha_lab/normalize.py:113`, `src/alpha_lab/normalize.py:138` and in the absence of a finiteness check of the output values before the result is returned. `features.total_return_index` later has its own check, but this does not make the N1 `technical_pass` evidence of finiteness of the output table.

N1-NUM-2: a NaN residual is not counted as exceeding the tolerance. Raw Close `[1e308,1e308]` and Adj Close `[1e-308,1e-308]` are positive and finite. $a_t/p_t$ rounds to 0, and $B_t/B_{t-1}=0/0$ gives NaN. The comparison `NaN > tolerance` gives false; the verified result is `technical_pass=true`, `max_adjustment_residual=null`. The cause is `src/alpha_lab/quality.py:55`: there is no separate rejection of a non-finite residual where the transition must be defined. The first row is NaN by construction because no previous value exists; it must be distinguished from NaN on subsequent transitions.

These examples reveal an insufficient numerical domain of definition for the checks; they do not identify a defect in an admitted actual data version, since actual data were not read and their presence or absence in such a range was not established. No code fixes or new tests are proposed in this review. A useful exact postcondition for a future fix is finite positive factors/OHLC/TR and a finite residual on all checked transitions, with separate treatment of the first row.

N1-INT-1: materiality measure and splits. The omitted $s_d$ in the diagnostic `bps` is confirmed by the example 333.3333... against 1000 bps above. Keeping the current formula is acceptable as the definition of an aggregate, provided it is not called an exact economic return error; such an interpretation requires a different formula or name.

N1-LIMIT-1: `confirmed` does not prove issuer coverage. The counterexample with a single zero issuer row outside the requested window shows why an external completeness check is mandatory. Equality of the presented events in the code cannot logically establish that no events are missing.

### 9. Hashes, manifests and replay: integrity without proof of truth

#### 9.1. Deterministic serialization

`canonical_bytes` serializes JSON with sorted keys, fixed separators, UTF-8, a trailing newline and rejection of NaN/Inf. For an identical structure and an identical representation of values in one environment the same byte sequence $C(x)$ results. Reordering the keys of a dictionary does not change the result. This is a project-specific canonical encoding, not a claim about universal canonicalization of all semantically equivalent JSON: for example, `1` and `1.0` may denote a similar economic quantity but have different bytes and hashes. Source: `src/alpha_lab/provenance.py:13`.

#### 9.2. Two-level manifest

For each file $b_j$:

$$
h_j=\operatorname{SHA256}(b_j).
$$

The manifest $M$ contains a mapping of file names to their hashes $h_j$ and metadata. A separate file contains

$$
h_M=\operatorname{SHA256}(C(M)).
$$

Verification first requires the manifest hash, then an exact match of the set of files and of the content hashes. A change, deletion or addition of a single file without a consistent change of the control values is therefore detected. Unsafe names, paths leaving the directory and symbolic links in the content are rejected. `freeze` creates a new directory with `exist_ok=False` and does not allow overwriting through this API. Sources: `src/alpha_lab/provenance.py:26`, `src/alpha_lab/provenance.py:53`.

The proof relies conditionally on the collision resistance of SHA-256. If a trusted $h_M$ is fixed and the manifest is changed, the new manifest can be accepted only if the new hash matches; likewise for content under an unchanged file hash. But if an adversary or a faulty process has replaced the content, the manifest, `manifest.sha256` and all external records simultaneously, local consistency is preserved. There is no cryptographic signature or externally pinned trust anchor here. A hash proves agreement of bytes with a control value; it does not prove the correctness of a number, the authorship of the issuer, the time of publication or the absence of a consistent forgery.

The term "immutable" denotes a write discipline through the API and detection of changes at verification. It is not a file lock against an external editor. The integrity of the bytes of the GLD document likewise does not prove that its interpretation as `no_distributions` is correct.

#### 9.3. Reconciling the source response and the adapter

Before normalization the pipeline requires that the indices and the necessary schema of the source chart and the adapter match. For each column:

$$
|x^{chart}_t-x^{adapter}_t|\le10^{-12},
$$

with `rtol=0`, that is, the tolerance is absolute and does not grow with price. `equal_nan=True` allows identical missing values at the stage of reconciling the required columns, but `normalize` then rejects non-finite inputs. This sequence means "the adapter preserved the source", not "a missing source price is allowed". Capital Gains are checked separately. For a raw corporate event on a missing session, a duplicate event or an incorrect split factor, parsing refuses. Sources: `src/alpha_lab/pipeline.py:13`, `src/alpha_lab/quality.py:8`.

Two records from the same provider are a check that the source transformation was preserved, not independent financial observations. If the source JSON is wrong, a matching adapter will confirm the error as agreement of bytes and values.

#### 9.4. Replay as an identity of the transformation function

Denote the construction function above by $\mathcal F(S,P,K;\theta)$: it uses the snapshot of raw data $S$, the pay dates $P$, the corrections $K$, and the configuration and environment $\theta$. Replay verifies the hash of the raw data manifest, rebuilds the files and compares the mapping of files to hashes:

$$
\{j:\operatorname{SHA256}(\mathcal F_j(S,P,K;\theta))\}
=\{j:h_j^{frozen}\}.
$$

Equality of the dictionaries requires the same set of files and the same hashes of every output file. The entire set is checked, including the normalized CSV, quality JSON, payable JSON and corrections JSON. Code: `src/alpha_lab/pipeline.py:216`.

This is strong evidence of reproducibility of a specific version of the transformation on frozen inputs under the given control values. But an incorrect formula can be reproduced deterministically, and erroneous inputs reproduce an erroneous result. "Replay equal" must therefore not be turned into "the historical returns are correct"; the code itself prints the warning `Exact replay does not certify data quality`.

#### 9.5. Provenance of runs and limits of the append-only journal

`Run` records the hashes of the configuration and the environment, the Git HEAD, the diff of the uncommitted state and the files outside Git, the hash of the data manifest, the parent attempt, the purpose, the time and the result. The hash of the uncommitted state is formed from the bytes of the binary diff and a canonical table mapping the names of files outside Git to their hashes. `started` is written before the result is computed; `finish` writes the final state, and an exit without `finish` or an exception is recorded as `failed`. Appending to the end of the file with flush/fsync improves the durability of states. Sources: `src/alpha_lab/provenance.py:82`, `src/alpha_lab/provenance.py:99`.

With identical verified inputs and hashes of output files, a registered repeat is a reproducibility check and not an independent experiment. `seed=None` with the reason `deterministic_data_pipeline` means that N1 contains no random algorithm; it does not mean the absence of all sources of external variability: the network, versions and provider revisions are still captured by the data version and the description of the environment.

The journal assumes a single writing process and is not a cryptographic hash chain. The code does not prove that old rows were never deleted, that a timestamp serves as a trusted time or that external files were not replaced consistently. These limits do not negate the usefulness of tracing; they define its exact level of evidence.

### 10. Checks actually performed for this part

A limited set of tests on synthetic examples was run: `tests/test_normalize.py`, `tests/test_quality.py`, `tests/test_reconcile.py`, `tests/test_corrections.py`, `tests/test_provenance.py` and two TR tests from `tests/test_features.py`. Result: 130 passed in 39.82s. Python was run from the existing `.venv`, with `PYTHONDONTWRITEBYTECODE=1`, the pytest cache disabled and temporary synthetic directories outside the repository. The first attempts using the default sandbox temporary directory gave 84 passed, 46 setup errors because the pytest temporary directory could not be created; a repeat with a separate permitted `--basetemp` completed successfully. Environment setup errors are not presented as errors of the financial tests.

In addition, five conditions were checked in memory without reading actual data: the difference between Adj Close and the economic total return index at a zero residual; overflow of the factor and TR; rounding of the adjustment factor to zero; an empty reconciliation inside the window with non-matching issuer coverage; and the materiality of a discrepancy on a split date. The numbers above refer only to the specially constructed synthetic inputs.

The coverage includes all mathematical operations of the N1 modules under review: sign and domain restrictions, OHLC inequalities, addition of distributed gains, products of split factors, unit conversions, accumulation of total return, rounding and tolerances, classification of sets of events, normalization of materiality, correction rules and prefix invariance, differences of calendar sets and the transfer of a distribution to a session, availability assumptions, the residual of retrospective adjustment, canonical bytes and hashes, and equality of replay. These proofs do not establish the actual return of H1/H2, results for the reserved period or the investment value of the project.

Exact reproductions of the five additional examples are stored in a separate verification script that is not part of the repository; its verified JSON output contains only synthetic numbers. The script imports the project source code, creates tables in memory and does not read actual data sets or run results.

## Part II. Features, ETF selection and portfolio construction

This part was checked against `src/alpha_lab/features.py`, `portfolio.py`, `benchmarks.py`, `hypotheses.py` and `hypothesis_report.py` at version `7a8ba1d56938e2576b537fff670ba0363e6e618c`. All examples below are artificial; historical strategy results are not used here.

### II.1. Notation and the object being modeled

The risky part consists of nine ETFs: SPY, EFA, EEM, IEF, TLT, LQD, HYG, GLD, DBC. A tenth ETF, BIL, serves as the cash instrument. BIL is a traded fund with a price, distributions and costs. The USD balance is a separate asset with zero return in the model.

The index $d$ denotes the ordinal number of a trading session, not a calendar day. Hence $t-21$ is twenty-one trading sessions before $t$. The letter $t$ in a signal denotes the close of the last regular session of the month. $T_{i,d}>0$ is the theoretical total return index of ETF $i$, which accounts for splits and distributions with notional immediate reinvestment. The actual account need not follow this index: distributions first become receivables, then cash, and new purchases take place separately.

Daily simple return:

$$r_{i,d}=\frac{T_{i,d}}{T_{i,d-1}}-1.$$

This is the change in capital relative to its initial size: if capital was $T_{d-1}$ and became $T_d$, its gain is $T_d-T_{d-1}$, and the relative gain is this difference divided by $T_{d-1}$. The formula follows from this definition and is not an additional hypothesis.

Invariance of signals under the normalization $T_0=1$. For any $b_i>0$, replacing $T_{i,d}$ by $b_iT_{i,d}$ leaves the ratio of two levels of the same ETF unchanged. Daily returns, momentum, monthly relative returns, risk estimates and weights therefore do not depend on the initial scale of the index. The levels $T_i$ of different funds cannot be compared directly; the code compares ratios of levels.

Source: `src/alpha_lab/features.py:19`, `src/alpha_lab/features.py:31`.

### II.2. Rationale for requiring 253 closes

One return requires two levels. $n$ consecutive returns require $n+1$ levels. Long momentum uses the levels at $t$ and $t-252$, so the total requirement is 253 closes. The same common warm-up is kept for short momentum so that comparisons do not start on different dates.

Volatility uses the last 63 returns, covariance uses 126, and H2 uses seven completed monthly levels for six monthly returns. These requirements differ: the availability of 253 rows does not in itself prove the absence of calendar gaps or the presence of correctly completed months.

`require_warmup` checks the number of rows. The calendar check belongs to the earlier loading and QA layers, and H2 separately checks that months are completed. This is a conditional guarantee of correctness of the whole chain, not a self-contained proof of data completeness by a single function.

Source: `src/alpha_lab/features.py:36`, `src/alpha_lab/features.py:112`.

### II.3. Sample volatility and the division by $n-1$

For the last $n=63$ daily returns of an ETF:

$$\bar r_i=\frac1n\sum_{d=1}^{n}r_{i,d},\qquad
s_i^2=\frac1{n-1}\sum_{d=1}^{n}(r_{i,d}-\bar r_i)^2,\qquad
\sigma_{i,t}=\sqrt{252}\,s_i.$$

The squared deviation measures the size of fluctuations irrespective of sign. Averaging the squares gives the variance; the square root restores the units of return. Thus $\sigma=0.20$ is read as 20% annual volatility under the adopted annualization convention.

Proof of the Bessel correction for independent identically distributed observations. Let $E[r_d]=\mu$ and $\operatorname{Var}(r_d)=v$. The decomposition is

$$\sum(r_d-\bar r)^2=\sum(r_d-\mu)^2-n(\bar r-\mu)^2.$$

Taking expectations and using $\operatorname{Var}(\bar r)=v/n$ gives $nv-v=(n-1)v$. Hence $E[s^2]=v$. In general, however, $E[s]\ne\sqrt v$, because the square root is nonlinear. Moreover, under serial dependence $\operatorname{Var}(\bar r)$ contains autocovariances, and the unbiasedness shown above is no longer guaranteed. `ddof=1` is the standard sample estimator, not a proof that the market is independent.

Rationale for $\sqrt{252}$. For a sum of 252 independent daily changes with the same variance $v$, the variance equals $252v$ and the standard deviation equals $\sqrt{252}\sqrt v$. Under dependence:

$$\operatorname{Var}\left(\sum_{d=1}^{N}r_d\right)
=Nv+2\sum_{h=1}^{N-1}(N-h)\gamma_h,$$

where $\gamma_h=\operatorname{Cov}(r_d,r_{d-h})$. The factor $\sqrt{252}$ in the project is therefore a single convention, adopted under the approximation of weak serial dependence; it does not automatically equal the true volatility of the compounded annual return $\prod(1+r_d)-1$. The choice of 63 and 252 is not derived from a theorem as optimal: these are registered parameters.

Zero or non-numeric volatility is prohibited because $1/\sigma$ and $M/\sigma$ are used later. This prevents division by zero; it does not mean that any practically small positive $\sigma$ is statistically reliable.

Source: `src/alpha_lab/features.py:49`. The semantics of `ddof` are confirmed by the [NumPy documentation](https://numpy.org/doc/stable/reference/generated/numpy.std.html); the proof above is given independently.

### II.4. Covariance: what co-moves, and why the matrix is PSD

For each risky ETF, the arithmetic excess over BIL is defined:

$$x_{i,d}=r_{i,d}-r_{B,d}.$$

Over the last $n=126$ sessions:

$$\bar x_i=\frac1n\sum_d x_{i,d},\qquad
\Sigma_{ij,t}=\frac{252}{n-1}\sum_d(x_{i,d}-\bar x_i)(x_{j,d}-\bar x_j).$$

A positive covariance indicates a tendency to move in the same direction relative to BIL; a negative covariance indicates offsetting deviations. In contrast to volatility taken separately, covariance accounts for the interaction between assets.

Let $X_c$ be the matrix of centered observations of size $126\times9$. Then:

$$\Sigma=\frac{252}{125}X_c^{\mathsf T}X_c.$$

Proof of symmetry: $(X_c^{\mathsf T}X_c)^{\mathsf T}=X_c^{\mathsf T}X_c$.

Proof of positive semidefiniteness (PSD): for any $z\in\mathbb R^9$,

$$z^{\mathsf T}\Sigma z=\frac{252}{125}\|X_cz\|_2^2\ge0.$$

The quadratic form is therefore not an arbitrary risk formula: it is the annualized sample variance of a linear combination of excess returns. Zero variance is possible for the zero vector or for a combination lying in the kernel of the covariance matrix. The presence of 126 observations does not guarantee positive definiteness: linearly dependent columns can make the matrix singular.

The code checks finiteness, symmetry with tolerance $10^{-12}$, and a minimum eigenvalue not below $-10^{-12}$. Separately, in the portfolio calculation, a variance in $[-10^{-12},0)$ is set to zero, and a value below $-10^{-12}$ raises an error. This protects against rounding; it does not repair an economically incorrect matrix. The PSD theorem refers to exact arithmetic; its machine implementation uses tolerances.

Source: `src/alpha_lab/features.py:61`, `src/alpha_lab/features.py:71`. The estimator format was checked against [NumPy `cov`](https://numpy.org/doc/stable/reference/generated/numpy.cov.html).

### II.5. Substantive meaning of the 10% target: risk relative to BIL

In an idealized fully invested portfolio with one-period constant weights $w_i$, $w_B=1-\sum_iw_i$:

$$r_P=\sum_iw_ir_i+w_Br_B=r_B+\sum_iw_i(r_i-r_B).$$

Consequently:

$$\operatorname{Var}(r_P-r_B)=w^{\mathsf T}\operatorname{Cov}(x)w.$$

This is the variance of the deviation from BIL, often called tracking error. The total variance is:

$$\operatorname{Var}(r_P)=\operatorname{Var}(r_B)
+2\operatorname{Cov}(r_B,w^{\mathsf T}x)+\operatorname{Var}(w^{\mathsf T}x).$$

Implication: bounding the last term does not bound the whole sum by the same number. For example, if the annual scale of BIL fluctuations is 4%, and the deviation of the portfolio has a volatility of 10% and is perfectly positively correlated with BIL, the total volatility will be 14%, although the calculation relative to BIL gives 10%. This is an artificial illustration, not an estimate of the risk of the actual BIL.

With a share $u$ of idle USD and no other complications:

$$r_P-r_B=\sum_iw_i(r_i-r_B)-u r_B.$$

With receivables, distributions and intraday trades, the actual dynamics are more complicated still. Therefore $\sqrt{w^{\mathsf T}\Sigma w}\le0.10$ is a property of the estimated target portfolio relative to BIL on the window data. It is not a guarantee of the realized volatility of the account, of the exact risk of execution, or of future risk. This follows directly from the choice of source series in the code and is not an error of annualization.

### II.6. H1: relative momentum with the last month skipped

For $L\in\{126,252\}$ and a fixed skip $b=21$:

$$G_i=\frac{T_{i,t-21}}{T_{i,t-L}},\quad
G_B=\frac{T_{B,t-21}}{T_{B,t-L}},\quad
M_{i,t}(L)=\frac{G_i}{G_B}-1.$$

The window contains exactly $L-21$ returns: the product runs over sessions $t-L+1,\ldots,t-21$. This is 231 returns for $L=252$ and 105 for $L=126$, not 252 and 126 returns. In Python the end levels are at `iloc[-22]` and `iloc[-(L+1)]`.

Proof by the telescoping product:

$$\frac{T_{i,t-21}}{T_{i,t-L}}
=\prod_{d=t-L+1}^{t-21}(1+r_{i,d}).$$

In the product, adjacent denominators and numerators cancel. Momentum therefore reflects compound accumulation, not a sum of daily percentages.

If $R_i=G_i-1$ and $R_B=G_B-1$, then:

$$M_i=\frac{R_i-R_B}{1+R_B}.$$

For example, 10% for an ETF and 2% for BIL give $(1.10/1.02)-1=7.843137\%$, not 8%. The sign coincides with the sign of $R_i-R_B$ because $1+R_B>0$. This permits interpreting positive momentum as outperformance of BIL over the given past window, but not as a guarantee of future outperformance.

In logarithms:

$$\log(1+M_i)=\sum_d[\log(1+r_{i,d})-\log(1+r_{B,d})].$$

Here relative accumulation becomes a sum of logarithmic excesses. For small returns $\log(1+r)\approx r-r^2/2$, but the code computes exact ratios of levels, not this approximation.

Purpose of the skip of 21. The skip separates medium-term movement from recent movement and short-term effects. How convincing this motivation is remains an empirical question. The skip does not prove the existence of a momentum premium and does not eliminate all data errors. Nor does it mean that the signal as a whole stopped using the last 21 sessions: $\sigma$ is measured over the history up to and including $t$.

Source: `src/alpha_lab/features.py:80`.

### II.7. The score $S=M/\sigma$, eligibility and ranking

$$S_{i,t}(L)=\frac{M_{i,t}(L)}{\sigma_{i,t}},\qquad
\mathcal E_t=\{i:S_{i,t}>0\}.$$

Since $\sigma_i>0$, the conditions $S_i>0$ and $M_i>0$ are equivalent. The ordering of ETFs, however, depends on $\sigma$. Example: $M_A=0.12$ and $\sigma_A=0.24$ give $S_A=0.5$; $M_B=0.09$ and $\sigma_B=0.10$ give $S_B=0.9$. B is chosen despite its smaller momentum.

This is a ranking measure of the strength of past relative movement per unit of the individual volatility. It is not a Sharpe ratio: the numerator is the accumulated relative return over a window with a skip; the denominator is annual volatility over a different window; and no mean of future return is estimated from the numerator. The measure is also not a z-statistic and does not automatically have a normal distribution.

Sorting by the pair $(-S_i,\text{ticker}_i)$ selects the maximum $S$; an exact machine tie is resolved by the ASCII order of tickers. Close but unequal numbers are not treated as a tie. The selected set $\mathcal S_t$ consists of the first $m\le K$ ranked elements, $K\in\{3,4\}$. Zero and negative scores do not fill vacant places. The number $m=|\mathcal S_t|$ may be zero.

For a fixed $L$, the top-3 selection is a subset of the top-4 selection, because the ranking is the same. It does not follow that the weights of common ETFs at $K=4$ will be larger or smaller in any fixed proportion after all the limits: $m/K$, the normalizing sum, the group limits and the risk scaling all change.

Source: `src/alpha_lab/hypotheses.py:25`.

### II.8. Inverse volatility: slot budget and proven properties

For $m>0$:

$$q_i=\frac mK\frac{1/\sigma_i}{\sum_{j\in\mathcal S}1/\sigma_j},\ i\in\mathcal S;
\qquad q_i=0,\ i\notin\mathcal S.$$

For $m=0$ all $q_i=0$; this is a separate branch that excludes $0/0$.

Proof of normalization: the fractions sum to one, hence $\sum_iq_i=m/K\le1$. Unused slots leave $1-m/K$ in BIL before the limits are applied.

Proof of equal individual risk scale: for the selected ETFs,

$$q_i\sigma_i=\frac{m/K}{\sum_j1/\sigma_j},$$

that is, the product of weight and individual volatility is the same. If all $\sigma$ are equal, $q_i=1/K$ regardless of $m$. If all volatilities are multiplied by a common positive number, the initial $q$ do not change. The subsequent risk scaling may nevertheless change.

Example: $\sigma_{SPY}=0.10$, $\sigma_{TLT}=0.20$, $m=2$, $K=3$. The sum of inverse volatilities is then 15, $q_{SPY}=4/9$ and $q_{TLT}=2/9$. The sum is $2/3$ and the remainder is $1/3$. SPY is then capped at $1/4$; the excess does not pass to TLT.

Limits of the risk-parity interpretation. For a covariance matrix $\Omega$, the portfolio variance is $V^2=q^{\mathsf T}\Omega q$. The derivative is $\partial V/\partial q_i=(\Omega q)_i/V$. The contribution of an ETF to volatility is $RC_i=q_i(\Omega q)_i/V$. Inverse volatility equalizes $q_i\sigma_i$ but in general does not equalize $RC_i$, because correlations differ. With diagonal $\Omega$ and consistent $\sigma_i=\sqrt{\Omega_{ii}}$ one obtains equal $q_i^2\sigma_i^2$, and risk parity holds in this special case. Here $\sigma$ is built on 63 ordinary returns and $\Sigma$ on 126 returns relative to BIL; even the diagonal special case does not automatically yield the required equality between two different estimates.

The algorithm does not solve the Markowitz problem $\min_w w^{\mathsf T}\Sigma w$ and does not maximize the Sharpe ratio. It is a transparent fixed allocation rule.

Source: `src/alpha_lab/portfolio.py:15`.

### II.9. ETF and group caps: a sequential algorithm, not an optimizer

First:

$$u_i=\min(q_i,0.25).$$

Then, for each disjoint group $g$:

$$B_g=\sum_{i\in g}u_i,\qquad
b_g=\begin{cases}1,&B_g\le0.50,\\0.50/B_g,&B_g>0.50,\end{cases}
\qquad v_i=b_gu_i.$$

The groups are Equity={SPY,EFA,EEM}, Treasury={IEF,TLT}, Credit={LQD,HYG}, Real={GLD,DBC}. Each ETF belongs to exactly one group.

Proof of the limits: $0\le b_g\le1$, hence $0\le v_i\le u_i\le0.25$. The group sum equals $b_gB_g=\min(B_g,0.50)$. The total does not increase: $\sum_iv_i\le\sum_iq_i\le1$. Because the groups are disjoint, processing one group does not violate the others. The sum of removed weights remains for BIL.

Treasury, Credit and Real have two ETFs each; after the 25% cap their sum already does not exceed 50%. The additional group limit can therefore actually bind only for the Equity group of three funds. This is a logical consequence of the current composition and not a reason to remove the registered checks.

Example: $q=(0.40,0.20,0.10)$ for SPY/EFA/EEM. After the ETF cap the weights are $(0.25,0.20,0.10)$, with sum 0.55. The group scale is $0.50/0.55=10/11$, so $v=(0.2272727,0.1818182,0.0909091)$, with sum 0.50.

Limitation of the proof. Reducing each positive weight does not guarantee a reduction of $v^{\mathsf T}\Sigma v$ when covariances are negative. The limits control concentration. The risk is recomputed after them; without this recomputation there is no guarantee of the target risk.

Source: `src/alpha_lab/portfolio.py:27`.

### II.10. Risk scaling: proof of the bound

On the already capped vector $v$:

$$V=\sqrt{v^{\mathsf T}\Sigma_tv},\qquad
a=\begin{cases}1,&V=0,\\\min(1,0.10/V),&V>0,\end{cases}
\qquad w_i=av_i,\quad w_B=1-\sum_iw_i.$$

Proof: the covariance form is homogeneous of degree two:

$$\sqrt{w^{\mathsf T}\Sigma w}
=\sqrt{a^2v^{\mathsf T}\Sigma v}=aV=\min(V,0.10).$$

Consequently, in exact arithmetic the computed risk of the final target vector does not exceed 10%. Since $0\le a\le1$, the ETF limits, the group limits and the absence of leverage are preserved. The sum of weights including BIL equals one. If $V<0.10$, the scale remains one: the algorithm does not increase exposure to reach 10%. If $V=0$, there is no division by zero.

Example: the single $v_{TLT}=0.25$, $\Sigma_{TLT,TLT}=0.64$. Then $V=0.25\times0.8=0.20$, $a=0.5$, the final $w_{TLT}=0.125$ and $w_B=0.875$.

A strong structural bound for H1 top-3. At most three ETFs are selected, and each final weight is at most 25%. Hence $\sum_iw_i\le0.75$ and $w_B\ge0.25$. For top-4 the corresponding general lower bound on BIL is zero, although the individual caps, the group caps, an insufficient number of selected ETFs and risk scaling often leave a positive BIL remainder. For any $m$:

$$\sum_iw_i\le\min(m/K,0.25m),\qquad
w_B\ge1-\min(m/K,0.25m).$$

For example, a single selected ETF in top-3 receives at most 25%, not 33.3%: the ETF cap binds before the slot budget.

What cannot be proved from this: that an ETF will not fall by more than 25%; that the account loss is bounded by 10%; that the future covariance equals the estimated one; that the actual daily shares remain within the limits. A weight is a share of capital, volatility is a standard deviation, and a possible loss is a different quantity.

Source: `src/alpha_lab/portfolio.py:38`.

### II.11. H2: six completed calendar months

For consecutive month ends $j-1,j$:

$$E_{i,j}=\frac{T_{i,end(j)}/T_{i,end(j-1)}}{T_{B,end(j)}/T_{B,end(j-1)}}-1.$$

This is the relative accumulated monthly return, analogous to $M$. It is not equal to $R_{i,j}-R_{B,j}$, although it has the same sign. The regression monthly excess returns used later employ the difference; the shared word "excess" in function names does not make the numerical definitions identical.

From the last six returns:

$$N_i=\sum_{j=1}^{6}\mathbf1[E_{i,j}>0],\qquad
F_i(h)=\mathbf1[N_i\ge h],\quad h\in\{4,5\}.$$

The filter ignores the size of the positive excess. Five months of +0.1% and one month of -20% pass the 5/6 threshold, although the cumulative result may be negative. Three large positive months and three small negative months may fail 4/6, although the cumulative result is positive. The filter indicates sign regularity; it is neither a replacement for momentum nor a statistical test.

Computing six returns requires seven monthly levels. The last actual XNYS sessions of each month are used; the months must be consecutive. The current month is included because the decision is made after it ends. The skip of the last 21-day segment belongs to H1 momentum, not to the H2 filter.

Source: `src/alpha_lab/features.py:112`, `src/alpha_lab/features.py:135`.

### II.12. H2 inherits the computed parent weights: what is preserved and what is not

The parent is always H1_252_3, with no selection of a best parent:

$$w_i^{H2}=F_i(h)w_i^{H1},\qquad
w_B^{H2}=w_B^{H1}+\sum_i(1-F_i(h))w_i^{H1}.$$

Proved: $0\le w_i^{H2}\le w_i^{H1}$; the set of nonzero risky weights is a subset of the parent's; the group and ETF limits are preserved; the risky budget does not increase; BIL does not decrease; the weights sum to one. There is no new ranking, no replacement of an excluded fund, and no subsequent re-increase of risk.

For the same data, $F_i(5)\le F_i(4)$, so the risky weights of H2_5of6 are not higher than those of H2_4of6 componentwise. This does not prove an ordering of their returns, turnover, total volatility or utility: the actual accounts evolve separately and incur different trades and costs.

The 10% risk bound is not preserved automatically. Let $D=\operatorname{diag}(F_i)$ and $w'=Dw$. Then:

$$V_{H2}^2=w^{\mathsf T}D\Sigma Dw.$$

The PSD property of $\Sigma$ does not imply $D\Sigma D\preceq\Sigma$. Decompose the parent vector into the retained part $u$ and the removed part $z$:

$$V_{parent}^2=V_u^2+V_z^2+2u^{\mathsf T}\Sigma z.$$

If the last term is sufficiently negative, removing $z$ increases the variance.

An exact numerical counterexample compatible with the weight limits. Two ETFs of different groups have the annual excess covariance

$$\Sigma=\begin{pmatrix}0.25&-0.2375\\-0.2375&0.25\end{pmatrix}.$$

Its eigenvalues $0.0125$ and $0.4875$ are positive, and the correlation is $-0.95$. The parent weights $(0.25,0.25)$ give

$$V_{parent}^2=2(0.25)^2(0.25-0.2375)=0.0015625,
\qquad V_{parent}=3.952847\%.$$

The risk scale is $a=1$, and the parent meets the 10% bound. H2 removes the second ETF and keeps the first weight at 25%:

$$V_{H2}=\sqrt{(0.25)^2\cdot0.25}=12.5\%.$$

The filter can thus violate the 10% target for excess risk even at the moment of the decision. This is a limitation of the registered rule, not a demonstration of such a violation on real data. The actual frequency was not computed in this check. Re-scaling would change H2 and would require a separate research decision; here the code is left unchanged.

A sufficient additional condition for monotone reduction is that all elements of $\Sigma$ are nonnegative: removing nonnegative terms of the quadratic form then cannot increase it. Market covariance need not satisfy this condition.

Source: `src/alpha_lab/hypotheses.py:45`. In `signals.csv`, the H2 field `scale` remains the parent's; it is not a new risk calculation for the filtered portfolio.

Illustration without market interpretation: if the six signs were independent and each had probability $1/2$ of being positive, then $P(N\ge4)=(15+6+1)/64=34.375\%$ and $P(N\ge5)=7/64=10.9375\%$. This is binomial arithmetic; the ETFs selected by H1 give no grounds for treating the signs as independent or as a fair coin. These numbers are not H2 p-values.

### II.13. Baseline strategies: purpose and formula of each

| Rule | Initial risky vector | Common constraints | What it isolates |
|---|---|---|---|
| B0 | $q_i=0$, BIL=1 | Execution and accounting only | The traded cash ETF as the baseline account |
| B1 | $q_i=1/9$ | ETF, group, excess-risk | Simple diversification without signal-based selection |
| B2 | Inverse volatility of all nine, $m=K=9$ | The same | Risk allocation without momentum selection |
| B3 | Positive relative trend over 252 sessions, then inverse-vol with $K=9$ | The same | The main comparator of H1, trend without top-K/skip-21 |
| REF_SPY | SPY=1, others=0 | ETF/group cap and vol-target are not applied | A separate equity market reference |

For B1 the initial group sums are $3/9,2/9,2/9,2/9$ and the individual weights are $1/9$. The caps therefore do not bind; only the common scale $a$ remains. The final nine risky weights are equal at $a/9$, with BIL=$1-a$. The weights are equal within the risky part, but the portfolio does not necessarily hold all capital in it.

For B3 the criterion is:

$$A_i=\frac{T_{i,t}/T_{i,t-252}}{T_{B,t}/T_{B,t-252}}-1>0.$$

There is no skip of 21 and no top-3/top-4 here: all eligible ETFs are admitted, $m\le9$, and the initial budget is $m/9$. The name "absolute trend" does not mean merely a nominal price rise above zero: what is implemented is growth of the total return relative to BIL. An ETF can have a positive USD return and still fail B3 if BIL grew more.

H1 versus B3 changes simultaneously the horizon, the skip of the last sessions, the normalization of the rank by $\sigma$, the top-K and the slot budget. A positive difference H1-B3 therefore does not by itself isolate the causal effect of any single detail. The registered N6 ablations separately remove the division of the score by sigma and separately replace inverse-vol by equal weights within the selected set.

B0 directs free funds into BIL every month. REF_SPY has a single initial decision; distributions remain in USD and are not reinvested. REF_SPY therefore does not equal the theoretical SPY total return and is not a competitor comparable in risk with the capped strategies. Accounts are not reset at year boundaries.

Source: `src/alpha_lab/benchmarks.py:17`, `src/alpha_lab/engine.py:253` (the `PROVIDERS` registry sets the decision frequency).

### II.14. Target weights differ from actual weights: proof of drift

Without trades and distributions over one interval, for a fully invested idealized portfolio:

$$\widetilde w_i'=
\frac{w_i(1+r_i)}{\sum_jw_j(1+r_j)}.$$

This is the ratio of the new value of the position to the new total value. If an ETF with an initial weight of 25% doubled and the other 75% of capital did not change, its new share is $0.50/(0.50+0.75)=40\%$. The initial cap was not violated when the target was created, but the actual share has become higher than 25%.

In the actual simulated account, quantities, as-traded prices, USD and receivables are tracked instead of notional weights; rounding, the order reserve, the overnight gap and costs further separate actual shares from the target. The presence of a 10% risk target in the signal does not make the realized volatilities of all strategies equal. Both the results and the actual risky shares, BIL, USD, receivables and realized risk must be compared.

### II.15. Causality: the formal guarantee and its premises

Let $\mathcal F_t$ be the information available under the adopted rules at the decision time. All levels $T_d$ with $d\le t$, past events and the calendar must be $\mathcal F_t$-measurable. The history is passed through `Market.history(t)`, which cuts off observations after $t$.

Sums, ratios, variances, a finite ranking and the capping operations over this history then remain $\mathcal F_t$-measurable. Consequently $w_t=f(\mathcal F_t)$ does not use future prices. The proof rests on the closure of measurable functions under composition and finite arithmetic operations; the sign and the sorting are also deterministic, and ties are resolved in a fixed way.

An equivalent engineering check: for any two markets $A,B$ that coincide up to $t$, $w_t(A)=w_t(B)$ must hold. Synthetic tests alter all future prices and compare H1 and H2. This is a necessary and useful check; a separate finite set of tests does not prove all possible inputs.

The causality of the code is conditional on the reliability of the availability metadata. Using a historical price corrected today does not make it actually available in the past. The historical `available_at=18:00 America/New_York` is a modeling assumption. The test that the future does not change the past does not reconstruct the provider's actual publication history.

Future splits under the inverse transformation of source units are a separate technical question; its invariance is proved in detail in Part I. A previously known exchange calendar is not equivalent to future information about returns.

### II.16. Mathematics of the N4 control report

The report checks internal identities and does not evaluate the closed returns. For one date it requires: $S_i\approx M_i/\sigma_i$, $\sigma_i>0$, eligibility=$\mathbf1[S_i>0]$, contiguous ranks $1,\ldots,|\mathcal E|$, selection by $rank\le K$, zero $q,v,w$ for unselected ETFs, sum $q=m/K$, equality of $q_i\sigma_i$ among the selected, recomputation of the caps, $w_i\approx av_i$, the BIL remainder, and consistency of signals and weights. H2 is additionally checked against the fixed parent and the monthly signs.

Relative closeness is defined exactly as:

$$|x-y|\le10^{-8}\max(|x|,|y|).$$

For $x=y=0$ exact equality is required. Absolute checks of weights use $10^{-9}$. The CSV stores 10 significant digits (`%.10g`), so a small difference is expected between a stored value and a computation on unrounded data. Textual equality of some columns is stronger than the numerical tolerance but refers only to the serialized values.

The equalities $\sum q=m/K$ and $q_i\sigma_i=c$ characterize inverse-vol for positive $\sigma$: the second implies $q_i=c/\sigma_i$, and the first gives $c=(m/K)/\sum 1/\sigma_i$. This is an independent check of the construction that does not call the same generating function.

Limit of the check. Internal consistency does not prove the correctness of the source $T$, of the volatility or of the momentum. The N4 report does not recompute prices or covariance and does not prove that the recorded `scale` corresponds exactly to $\min(1,0.10/V)$. These properties are checked by the original computation and by separate tests. The report also does not prove returns and does not establish the probability of success of a strategy.

Some relations are checked on rounded numbers: for example, an exact machine tie of the original scores and the coincidence of the displayed scores are not identical. The check of rank order permits a non-increasing score but does not by itself reconstruct the ASCII rule for an exact tie of the original values; this is covered by provider tests.

Non-numeric values and infinities are rejected; an overflow of `fsum` is treated as a failure of the check and not as a confirmation. Correction D024 specifically closed the corresponding validator defect without changing the strategy formulas.

Source: `src/alpha_lab/hypothesis_report.py:72`, `src/alpha_lab/hypothesis_report.py:305`.

### II.17. All published N4 diagnostic aggregates

Let $D$ be the number of decisions in the selected period; $m_d$ the number of selected ETFs; $e_d$ here the number of eligible ETFs (not a daily excess return); $b_d=\sum_iw_{i,d}$ the target risky share; $a_d$ the parent scale; $\tau_d$ the turnover; and $f_d$ the overall buy fill coefficient. Then:

- `mean_eligible`=$D^{-1}\sum e_d$, `mean_selected`=$D^{-1}\sum m_d$.
- `selected_distribution[k]`=$\sum_d\mathbf1[m_d=k]$; the sum of these counts equals $D$.
- `empty_selections` is the number of $m_d=0$.
- `mean_risky`=$D^{-1}\sum b_d$; `max_risky`=$\max b_d$; `mean_bil`=$D^{-1}\sum w_{B,d}$.
- `max_etf`=$\max_{d,i}w_{i,d}$, `max_group`=$\max_{d,g}\sum_{i\in g}w_{i,d}$.
- `scale_binding`=$\sum_d\mathbf1[a_d<1]$, share=$scale\_binding/D$; `mean_scale` is the mean of $a_d$. For H2 this is the parent's scale, not the risk of the final H2 portfolio.
- `turnover_sum`=$\sum_d\tau_d$, `turnover_mean`=$\sum_d\tau_d/D$, `cost_ratio`=$c\sum_d\tau_d$; `min_buy_fill`=$\min f_d$, `partial_fills`=$\sum_d\mathbf1[f_d<1]$.
- `ticker_selection[i]` is the number of decisions that select $i$, divided by $D$. For H2 this is the parent's selection.
- H2 `pass_share` is the number of parent ticker-decision pairs that passed the filter, divided by the number of all pairs selected by the parent. This weights by the number of pairs, not by capital.
- H2 `ticker_pass[i]` is the number of the parent's selections of the given ETF that passed, divided by the number of its parent selections.
- H2 `removal_decisions` is the number of decisions in which at least one ETF selected by the parent is removed.
- H2 `mean_removed_share` is the mean of $(b_d^{parent}-b_d^{H2})/b_d^{parent}$ over the decisions with $b_d^{parent}>0$ only. This is a mean of individual shares, not a ratio of sums.
- Order, trade and distribution counters are sums of indicators of the corresponding categories. A distribution is assigned to the year of its ex-date and has the status at the end of the whole run; this is not the sum of money paid in the stated year.

For an empty set, the mean, share, minimum and maximum return `None`, displayed as `n/a`; the turnover sum without decisions equals zero. An empty denominator must not be turned into a zero probability. A decision is assigned to the year of execution, not to the year of creation; a December decision executed in January is counted in the January year.

All these aggregates describe the behavior of the algorithm and are not evidence of effectiveness. A low share of selected ETFs does not imply high forecasting accuracy; the H2 pass share is not a frequency of winning trades.

Source: `src/alpha_lab/hypothesis_report.py:530` and the functions `_selection`, `_targets`, `_trading`, `_h2_filter`, `_per_ticker` of the same file.

## Part III. Capital Accounting and Order Execution

Audited version: `7a8ba1d56938e2576b537fff670ba0363e6e618c`, 10 October 2026. This part is an audit of the ledger mathematics and is not a change to the research protocol. Sources, tests, settings and repository documents were not modified. Actual hypothesis results, research run directories and reserved-period results were not opened.

Three kinds of statements are distinguished below.

1. Algebraic identity: follows from the recorded state transitions under exact arithmetic.
2. Software check: a specific condition that the code actually verifies, sometimes with a tolerance.
3. Economic assumption: a modeling choice that cannot be proved by an accounting equality. For example, the possibility of trading the whole quantity at the historical Open is an execution assumption, not a consequence of a correct NAV.

All line references refer to the audited version. The primary sources are `src/alpha_lab/market.py:1`, `src/alpha_lab/ledger.py:1`, `src/alpha_lab/engine.py:1`, `EXECUTION_MODEL.md:1` and the manual reconciliations (`docs/n2/manual_reconciliation.md:1`).

### 1. Notation, units and account state

Let $t$ be the index of a common trading session and $i$ an ETF. Indexing follows the common calendar, not calendar days.

| Symbol | Meaning | Dimension |
|---|---|---|
| $C_{i,t}$ | Close in the units actually traded in that session | USD / share |
| $O_{i,t}$ | Open, if it is admissible for execution | USD / share |
| $S_{i,t}>0$ | new shares / old shares in a split, otherwise 1 | dimensionless |
| $d_{i,t}\ge0$ | distribution per share on the ex-date, in the units of that session | USD / share |
| $H_{i,t}\ge0$ | number of shares after execution, at the close | shares |
| $K_t$ | cash balance | USD |
| $A_t$ | sum of outstanding distribution receivables | USD |
| $V_t$ | NAV at the close | USD |
| $w_{i,t}$ | target weight returned by the decision provider | dimensionless |
| $r$ | parameter reducing the size of the target portfolio (order reserve) | dimensionless |
| $c$ | transaction cost per side | USD / USD of traded notional |

The `Account` state stores cash, positions, receivables and pending orders. Initially $K=100000$, all $H_i=0$, and there are no receivables or orders. The parameter `initial_cash` may be set in the code to any other finite positive number; this does not mean that the protocol permits changing the research initial capital. See `src/alpha_lab/ledger.py:50` and `src/alpha_lab/engine.py:39`.

Dimensional check: $H_iC_i$ and $H_id_i$ are in USD; $w_iV/C_i$ is in shares; $c\times\text{notional}$ is in USD. A quantity of shares cannot be added to a monetary value, and an old quantity cannot be used with a new price after a split without a change of units.

### 2. Guarantees of the Market layer

Let $D_i$ be the set of dates present in the table of ETF $i$. The common sessions are

$$
\mathcal T=\operatorname{sort}\left(\bigcap_i D_i\right),
$$

after truncation from below by the parameter start. Duplicate dates within one ETF are forbidden. A positive finite Close is required; Open may be a positive finite number or NaN; a distribution is finite and non-negative; a split coefficient is finite and positive. See `src/alpha_lab/market.py:97`.

Rationale for the intersection. Every recorded NAV values all ETFs on a single date; one instrument cannot be executed at today's price and another silently at a past price. However, the presence of a row and a finite price does not by itself establish freshness, tradability, membership of the date in the exchange calendar, or absence of a provider error. Completeness of the XNYS calendar and the quality of the real vintage are separate QA questions. In particular, `market_from_frames` does not require the intersection to contain every expected session: the synthetic test `test_common_calendar_is_intersection` (`tests/test_market.py:18`) deliberately removes one session of one ETF.

A corporate action on an excluded date must not be lost silently. Within the range in use, a row outside the common calendar with a finite positive distribution or a finite $S\neq1$ causes rejection. A pay date inside the common range must also lie in the common calendar. This is a stronger condition than a simple intersection of tables. It does not turn rows before the specified start, or invalid events on excluded dates, into fully validated data. See `src/alpha_lab/market.py:80`, `src/alpha_lab/market.py:88` and `tests/test_market.py:136`.

Loading verifies the manifest and the file hashes through provenance.verify and the expected SHA-256 of the manifest. This shows that the bytes correspond to the approved vintage, provided the hashing procedure is correct; it does not show the economic truth of prices and distributions. The account computation receives as-traded Open/Close, not Adj Close. This separation is necessary so that a distribution does not appear both in an adjusted price and as a separate receivable. See `src/alpha_lab/market.py:129` and `EXECUTION_MODEL.md:13`.

### 3. NAV: proof and economic meaning

The implemented definition is

$$
\boxed{V_t=K_t+\sum_i H_{i,t}C_{i,t}+A_t.}
$$

See `src/alpha_lab/ledger.py:163`.

This is the sum of three mutually distinct assets: cash, the market value of the shares owned, and accrued but not yet received claims to distributions. An order is not an asset and is not added to NAV: it only defines a possible future transition between cash and shares. Since there is no borrowing or shorting, separate liabilities for debt and short positions are not needed here.

Proof of the correctness of the form. Under the stated assumptions the account owns exactly the three listed kinds of assets. One share is valued at $C_i$, so the linear value of $H_i$ shares is $H_i C_i$. Each receivable is valued at face value, and the sum of the face values is $A$. Cash is already expressed in USD. Summing disjoint ownership claims gives the formula.

Valuing a receivable at face value is an assumption, not a market theorem. The model contains no discounting, default risk, tax or withholding. If such factors were present, the economic NAV could differ from this formula. An unreceived distribution raises NAV but does not raise the cash available for purchases. NAV and the purchasing power of the account are therefore different quantities.

A simple example from `test_nav_counts_cash_positions_and_receivables` (`tests/test_ledger.py:194`): cash 100, two shares at 10, and a receivable $2\times0.25=0.5$; NAV is $100+20+0.5=120.5$.

### 4. Order of operations

In every session the following steps are executed.

1. Splits of positions and of pending orders.
2. Accrual of the distribution on the post-split quantity, before trades.
3. Transfer of receivables due today into cash.
4. Sales at today's admissible Open.
5. Purchases at today's admissible Open.
6. NAV valuation at Close; after it, if a decision is scheduled, computation of new orders.

See `src/alpha_lab/engine.py:157` and `EXECUTION_MODEL.md:63`.

The transitions do not commute. If one buys on the ex-date first and accrues afterwards, the buyer wrongly obtains the right to a distribution that has already detached. If one sells first and then accrues, the seller wrongly loses it. If one accrues on the old quantity and then applies the split, the amount for a new share is wrong when a split and a distribution occur simultaneously. If purchases precede sales, the available liquidity is smaller. The order of operations is therefore a defining part of the model, not a technical permutation of rows.

A session can be both the execution of an old decision and the close of a new one. The check admits equality of the index of the new decision with the index of the previous execution: old orders disappear at the Open and new ones arise at the Close. With lag=2 the intermediate close does not recompute the pending order. See `src/alpha_lab/engine.py:97`.

### 5. Splits and conversion of units

For a split $S$:

$$
H_i^+=S_iH_i^-,\qquad q_i^+=S_iq_i^-,\qquad K^+=K^-,\qquad A^+=A^-.
$$

Here $q$ is the signed quantity of a pending order: a purchase is positive and a sale is negative. See `src/alpha_lab/ledger.py:62`.

Rationale for converting the order as well. A decision in old units intended to change the holding from $H$ to $Q$; its order is $Q-H$. After the change of units the same economic holding has the quantity $SH$ and the same target is $SQ$. The difference must therefore equal $SQ-SH=S(Q-H)$. Changing only the position would amount to executing a different economic order.

With several splits between the decision and the execution:

$$
q_e=\left(\prod_{s=t+1}^{e}S_{i,s}\right)(Q_{i,t}-H_{i,t}).
$$

The fields `target_qty`, `held_qty` and close keep their values in the units of the decision moment. Only qty changes units. After a split the equality `order_qty=target_qty-held_qty` is therefore generally false; the product of the coefficients must be used. This follows directly from the absence of assignment to the old fields in `apply_splits` and is reflected in `src/alpha_lab/engine.py:309`.

Condition for value preservation. If in a pure split the price of a new share is $C^+=C^-/S$, then:

$$
H^+C^+=(SH^-)(C^-/S)=H^-C^-.
$$

The quantity conversion does not by itself guarantee that the observed price satisfies this equality: a market return is possible between the close and the next open. The invariant `split_quantity_only` checks the quantity conversion and the absence of cash movement, not the equality of NAV before and after market revaluation.

Reverse split 1:2. 1087 old shares become 543.5 new shares; under a pure change of units the price 91 becomes 182. The value before and after is 98917. The order $-544$ becomes $-272$, and the sale leaves 271.5 shares. The model keeps this fraction and later permits selling it in full. There is no cash in lieu at the split. All the numbers are verified in `tests/test_engine.py:117` and in case 2 of the manual reconciliation (`docs/n2/manual_reconciliation.md:30`).

An old distribution receivable is not converted: it already expresses a fixed claim to USD that arose on its own ex-date. Increasing its amount at a split would create additional money. The quantity and the amount per share stored in an old `Receivable` remain historical attributes whose product is already fixed.

### 6. Accrual on the ex-date and receipt on the pay date

Before the trades of session $t$, the position in current units is

$$
h_{i,t}=S_{i,t}H_{i,t-1}.
$$

If $d_{i,t}>0$ and $h_{i,t}>0$, a separate receivable is created:

$$
R_{i,t}=h_{i,t}d_{i,t}.
$$

The quantity is fixed at that moment, not at the future payment. `Receivable`.amount equals qty times amount_per_share; subsequent sales do not reduce this right. See `src/alpha_lab/ledger.py:8` and `src/alpha_lab/ledger.py:79`.

Let $P_t$ be the sum of all receivables whose due date is $t$, including today's accrual if the pay date coincides with the ex-date. Then:

$$
A_t=A_{t-1}+\sum_i h_{i,t}d_{i,t}-P_t.
$$

The pure payment transition is

$$
K^+=K^-+P_t,\qquad A^+=A^--P_t,
$$

and therefore $K^++A^+=K^-+A^-$. With positions and prices unchanged, receiving a previously accrued distribution does not change NAV. This is a transfer of the form of the asset, not a new return. See `src/alpha_lab/ledger.py:91`.

Prevention of double counting. For a single share without a split, when Close falls from 100 to 99 and the distribution is 1, the change in $HC+A$ equals $-1+1=0$. Receiving this unit later again does not increase NAV. If, instead of the raw price 99, one used a series in which the distribution is already reflected in the return, and also added the `Receivable` 1, an artificial additional return would result. A total return series is therefore useful for signals and for a theoretical reference, but it must not replace as-traded prices in this ledger together with cash distributions.

In case 3 (`docs/n2/manual_reconciliation.md:63`), DDD is sold on the ex-date and EEE is bought on the same date. The receivable of 2020 USD arises only for DDD. The purchase of EEE does not receive the distribution, although its synthetic table also contains dividend=1. The constant synthetic price 49 does not imitate a mechanical ex-date drop: the NAV increase of 2020 USD here is intentionally due to the specified inputs, not to a ledger error.

Relevance of the pay date despite unchanged NAV at receipt. Until it is paid, a receivable enters $V$ and hence the size of the target orders, but not the cash available to pay for them. An earlier payment can increase purchases, and the new positions then earn a different market return. A change of the pay date can therefore alter the future NAV trajectory through liquidity, although the payment itself is arithmetically neutral.

### 7. Actual and proxy pay date

For an actual distribution the pay date from the vintage is kept. For a proxy:

$$
\operatorname{pay}(x,k)=\min\{s\in\operatorname{XNYS}:s\ge x+k\text{ calendar days}\}.
$$

See `src/alpha_lab/market.py:48` and `src/alpha_lab/engine.py:103`.

In the source data the bases actual and `proxy_ex_plus_10_calendar_days` are admissible. For a proxy, the loader requires the recorded date to agree exactly with the +10 rule. A scenario can change only the proxy, to $k\in\{0,10,30\}$, and preserves the actual dates. The difference matters: $k$ counts calendar days, whereas lag counts indices of common sessions. For the ex-date 2017-11-30 the proxy +10 gives 2017-12-11, because 10 December is a Sunday; +30 gives 2018-01-02. See `tests/test_market.py:73`.

With k=0, accrual and receipt occur in the same session because of the order accrue, then credit. The condition $\text{pay}\ge\text{ex}$ forbids receipt before the right arises. If the due date is later than the end of the simulation, the receivable remains in NAV; there is no forced receipt or liquidation on the last date. See `tests/test_engine.py:191`.

`credit_payouts` looks for exact equality of the date, not $\text{pay}\le\text{today}$. For a direct manual call on an incorrectly skipped calendar, an old receivable would therefore not be settled automatically. The normal loader/`pay_map` path forbids payments inside the common range on missing common dates. The `receivable_conservation` check by itself does not establish that a remaining receivable has a due date later than the end of the window: for that, the due dates of the individual receivables must be compared with `end_session`.

### 8. Target weights and the order quantity at the close

The provider must return weights for all existing ETFs and only for them; each weight is finite, real and non-negative. The permitted condition is:

$$
\sum_i w_i\le1+10^{-12}.
$$

`math.fsum` is used to check the sum. Values of type bool and `np.bool_` are forbidden by the predicate `finite_number`. The cash weight as an output quantity, `usd=1-fsum(w_i)`, may be slightly negative within the tolerance; this is not negative actual cash. See `src/alpha_lab/engine.py:112` and `src/alpha_lab/engine.py:300`.

At the decision close:

$$
Q_{i,t}=\left\lfloor\frac{(1-r)w_{i,t}V_t}{C_{i,t}}\right\rfloor,
\qquad q_{i,t}=Q_{i,t}-H_{i,t}.
$$

See `src/alpha_lab/ledger.py:101`.

This is a target quantity, not a purchase of the amount $(1-r)w_iV$: the existing position is subtracted. If the position is above the target, the result is a sale. For $q=0$ no order is created; every other nonzero size creates one, with no minimum threshold. The target is an integer; `held_qty` and the difference itself can be fractional because of a split.

Rationale for floor. For $x_i=(1-r)w_iV/C_i\ge0$:

$$
0\le x_i-\lfloor x_i\rfloor<1.
$$

Consequently the monetary underinvestment relative to the continuous target, for each ETF, is

$$
0\le (1-r)w_iV-Q_iC_i<C_i.
$$

The total underinvestment is strictly less than the sum of the prices of the assets with a positive continuous target; for weight 0 the difference is 0. Floor gives a value not above the target and an integer size, but it does not solve the problem of the optimal discrete portfolio and does not distribute the remainder among ETFs.

When $\sum_i w_i\le1$ holds exactly:

$$
\sum_iQ_iC_i\le(1-r)V\sum_iw_i\le(1-r)V.
$$

This implies only that the target stock portfolio at decision prices occupies at most the fraction $(1-r)$ of NAV. The tolerance on the sum of weights adds to the right-hand side a possible error $(1-r)V\times10^{-12}$. Actual weights after execution, and later during drift, can differ because of a gap, costs, whole shares, receivables and unfilled orders.

The size uses only the decision close and the NAV at that time; the future Open does not participate. The quantity should not be recomputed at the Open, even if the new price would be more convenient. That would change the rule and the information structure of the model.

### 9. Meaning and limits of the order reserve

The parameter $r$ reduces every target position. It is not a continuously maintained cash share. Even if the targets are achieved ideally and without costs, $V-\sum_iQ_iC_i\ge rV$ implies only $K+A\ge rV$, not $K\ge rV$: part of the remainder can be a receivable that is unavailable for payment.

For a first entry from an account held entirely in cash, with no gap, no receivable and no rounding, the full target purchase requires:

$$
(1+c)(1-r)V\le V
\iff r\ge\frac{c}{1+c}.
$$

This is a sufficient condition when floor is taken into account, since floor only reduces spending. It does not guarantee execution at an arbitrary future Open. For example, in manual case 4, r=0.01, but an open at 99 instead of a close at 97 leads to a partial fill.

For a general portfolio rebuild with $A=0$, $O_i=C_i$, no split and exact arithmetic, let $B$ be the full monetary volume of purchases before costs and $L$ the monetary volume of sales. Then the cash on full achievement of the targets is:

$$
K'=V-\sum_iQ_iC_i-c(B+L).
$$

Since $B\le\text{(value of the target portfolio)}\le(1-r)V$ and $L\le\text{(value of the old portfolio)}\le V$, a sufficient but not necessary condition is:

$$
K'\ge[r-c(2-r)]V\ge0
\quad\Leftarrow\quad r\ge\frac{2c}{1+c}.
$$

This illustrates the two sides of costs when switching between ETFs. The implemented model guarantees the absence of overspending through the fill, not through a theorem that $r$ is sufficient for any price path.

A zero weight does not mean that the ETF disappears immediately: the sale is executed only at the assigned Open and can be cancelled for lack of an admissible price. A weight cap is a rule for forming the target, not a continuous constraint on actual holdings.

### 10. Sales, cash flows and the absence of short positions

After orders without an admissible Open are excluded, a sale $q_i<0$ is executed in the amount

$$
L_i=\min(-q_i,\max(h_i,0)).
$$

After it, $H_i'=h_i-L_i\ge0$, and cash increases by

$$
L_i O_i(1-c)=L_iO_i-cL_iO_i.
$$

See `src/alpha_lab/ledger.py:133`.

Proof by induction that the portfolio is long-only. Initially all quantities are 0. A split with positive $S$ preserves non-negativity. A sale subtracts at most the current non-negative quantity. A purchase adds a non-negative quantity. Accrual and receipt of distributions do not change quantities. Hence, under ordinary operations, all positions remain non-negative. This is a property of the implementation, although among the seven final checks there is no separate position invariant.

With correct sizing, $-q=H-Q\le H$, because $Q\ge0$. After a split both parts change proportionally, so the order also does not exceed the position. The `exceeds_position` branch is a defensive reaction to an inconsistent external state, not a normal mechanism for limiting signals. For an input position that is already negative because of an outside change, the proof does not apply.

A sale permits a fractional quantity in order to close the remainder after a split. The purchase of whole shares does not mean that all sales are whole as well. The direct use of sale proceeds for purchases of the same session is an accepted simplification of settlement, not a model of a settlement account.

### 11. Fill coefficient for purchases: proof that cash is not overspent

Let $J$ be the set of positive pending orders with an admissible Open today. After distributions and all sales, denote the available cash by $K*$. The required spending is computed on the full quantity of the order, including the fraction:

$$
R=\sum_{i\in J}q_iO_i(1+c).
$$

The fill coefficient is

$$
f=\begin{cases}
1,&R=0,\\
\min(1,\max(K*,0)/R),&R>0.
\end{cases}
$$

Each purchase is

$$
B_i=\lfloor fq_i\rfloor,
\qquad K_{final}=K*-\sum_{i\in J}B_iO_i(1+c).
$$

See `src/alpha_lab/ledger.py:148`.

Proof for $K*\ge0$ and finite positive prices. $0\le f\le1$ and $0\le\lfloor fq_i\rfloor\le fq_i$. Multiplying by the positive $O_i(1+c)$ and summing:

$$
\sum_i B_iO_i(1+c)\le fR\le K*.
$$

Hence $K_{final}\ge0$. The intermediate cash after any single purchase is also non-negative: a partial sum of non-negative outlays does not exceed the total. Sales and distributions before the purchases do not reduce cash, because $d\ge0$ and $0\le c\le0.005<1$. Together with the positive initial cash this proves self-financing of the cash budget at every step in exact arithmetic.

The code check allows cash down to `-1e-8` because of rounding; below this bound `execute_orders` raises ValueError. If cash is already negative beforehand, the guard $max(K*,0)$ forbids new purchases but does not itself correct the earlier violation of the budget.

Equal common coefficient and unequal realized fill shares. For every positive $q$:

$$
f-\frac1{q_i}<\frac{B_i}{q_i}\le f.
$$

The floor error is less than one share, but in relative terms it is material for small $q$. After floor, different ETFs can have different $B_i/q_i$ despite the same $f$. This is not an optimization of the minimum deviation of weights and does not guarantee the same tracking error.

Remainder after floor. Introduce $\varepsilon_i=fq_i-B_i\in[0,1)$. Then:

$$
K_{final}=(K*-fR)+\sum_i\varepsilon_iO_i(1+c).
$$

When cash is insufficient and $0<K*<R$, the first term equals 0, so the remainder is strictly less than $\sum_i O_i(1+c)$ for nonempty $J$. When f=1, the original surplus $K*-R$ is added to the rounding. The remainder is not redistributed and could allow the purchase of one more share; the algorithm deliberately does not do this.

In `test_fill_ratio_applies_equally_to_several_buys` (`tests/test_ledger.py:85`), the orders 10, 7, 9 at prices 50, 30, 20 require $890\times1.001=890.89$, with cash=500. The common $f$ equals $500/890.89$, the purchases are 5, 3, 5, the notional is 440, the costs are 0.44 and cash=59.56. The order of tickers does not give the first one all the liquidity: the coefficient is computed once, before the purchases. However, the order of summation in floating point affects the last bits of the arithmetic.

### 12. Fractional orders: three distinct effects

A fractional quantity can arise not only from the conversion of an order by a split but also from subtracting a fractional current position from an integer $Q$. A sale can be executed fractionally; a purchase only as $\lfloor fq\rfloor$.

With f=1 and a non-integer $q>0$, $\lfloor q\rfloor$ is bought and the remainder of less than one share is cancelled. If $q<1$, there is no trade at all. The reason `fractional_quantity` applies when the executed quantity is not less than $\lfloor q\rfloor$. If less than $\lfloor q\rfloor$ is bought, the reason is `insufficient_cash`. See `src/alpha_lab/ledger.py:156` and `tests/test_ledger.py:110`.

The reason is not an exact statement about f=1 or f<1. For example, with q=2.2 and f=0.95, 2 shares are bought although f<1; $\lfloor q\rfloor$ was bought, so the reason is `fractional_quantity`. A shortage of cash for the full fractional order existed but did not reduce its integer part.

A fraction enters $R$ and can therefore reduce the purchase of another ETF. A verified synthetic counterexample: cash=200, c=0, both prices 100, orders AAA=0.5 and BBB=2. Then R=250, f=0.8, the purchases are AAA=0 and BBB=1, and cash=100. If $R$ were computed only over the whole parts being bought, 2 shares of BBB could be bought. This is a difference in the economic rule, not a violation of the budget; the implemented rule corresponds unambiguously to the full $q$ in $R$. `EXECUTION_MODEL.md:93` acknowledges this effect separately.

Statuses are determined by the size of the executed quantity: filled when `filled_qty=abs(q)`, partial for a positive incomplete execution, cancelled at 0. Therefore f=1 does not always mean filled. All orders assigned to the Open are removed from pending after this single open; the remainder does not stay for the next session. See `src/alpha_lab/ledger.py:120` and `src/alpha_lab/ledger.py:135`.

### 13. Costs, notional and turnover

For a trade $j$ of positive quantity $u_j$ at an admissible Open $p_j$:

$$
N_j=u_jp_j,\qquad F_j=cN_j.
$$

A purchase spends $N_j+F_j$ and a sale receives $N_j-F_j$. The `Trade` data record notional, cost and cash_after. See `src/alpha_lab/ledger.py:126`.

The cost is not added to the execution price again: `trade.price` remains the Open, and the cost is separated as a cash flow. A double deterioration of the price together with a separate identical fee would overstate the costs. For c=0.001 the cost per side equals 10 bps of notional. Entry and BIL are paid for under the same rule; distributions and splits are free. The modeled Open does not ensure the necessary auction volume and the model contains no separate spread, market impact, taxes, currency exchange or brokerage settlement: these are either aggregated in $c$ or excluded.

For decision $t$ with execution $e$:

$$
T_t=\frac{\sum_{j:\operatorname{session}(j)=e}N_j}{V_t},
\qquad \operatorname{costs\_usd}_t=\sum_{j:\operatorname{session}(j)=e}F_j.
$$

The denominator is the NAV at the decision close, not the NAV at execution and not the average capital. The numerator is the actually executed sales plus purchases; there is no division by 2. The time restriction on decisions excludes an overlap of pending packages, so today's trades belong to one package. Even a decision without orders receives a row with turnover=0, `costs_usd`=0 and `buy_fill`=1. See `src/alpha_lab/engine.py:178` and `EXECUTION_MODEL.md:128`.

With a single $c$ and positive $V$, the following holds identically:

$$
\boxed{\operatorname{costs\_usd}_t=cV_tT_t,\qquad
\operatorname{costs\_usd}_t/V_t=cT_t.}
$$

This is a monetary cost normalized by the capital at the decision. It does not automatically equal the loss of daily execution return if the capital changed between the decision and the execution. If $c$ varied across instruments, a formula with a single $c$ would be wrong; the code uses a single parameter.

In a full switch from ETF A to B with approximately unchanged capital, the turnover is close to 2 and the cost is close to $2cV$. In manual case 5 the notionals are 98960 and 98880 and the decision capital is 99901.04:

$$
T=197840/99901.04,\qquad F=0.001\times197840=197.84.
$$

The initial purchase of HHH at the previous Open had a separate cost of 98.96 and is not included in this decision. See `tests/test_engine.py:219`.

Turnover is not bounded by 1, and in general even the bound 2 cannot be guaranteed: the denominator lags the execution and prices can change substantially. The measure reflects the trading outlay relative to the historical capital at the decision, not the distance between two vectors of target weights.

### 14. Exact self-financing P&L decomposition

This section gives an independent derivation concerning the financial ledger. It does not compute hypothesis returns and applies to any synthetic or admissible inputs.

Let $H_i=H_{i,t-1}$ and $h_i=S_{i,t}H_i$. Denote by $b_i\ge0$ the shares actually bought, by $l_i\ge0$ the shares actually sold, and let $\Delta_i=b_i-l_i$. After execution $H_{i,t}=h_i+\Delta_i$. Let $F_t=\sum_j \text{cost}_j$ be the costs of all of today's trades, $D_t=\sum_i h_id_{i,t}$ the accruals, and $P_t$ the settled receivables. The transitions are then:

$$
K_t=K_{t-1}+P_t-\sum_i\Delta_iO_{i,t}-F_t,
$$

$$
A_t=A_{t-1}+D_t-P_t.
$$

If there are no trades in $i$ and Open is absent, the term $\Delta_iO_i$ is defined as zero, without multiplying NaN by zero; it is safer to write the sum only over the trades actually executed.

Substituting into NAV:

$$
\begin{aligned}
V_t-V_{t-1}
&=(K_t-K_{t-1})+(A_t-A_{t-1})
 +\sum_i[(h_i+\Delta_i)C_{i,t}-H_iC_{i,t-1}]\\
&=P_t-\sum_i\Delta_iO_{i,t}-F_t+D_t-P_t
 +\sum_i[h_iC_{i,t}-H_iC_{i,t-1}+\Delta_iC_{i,t}]\\
&=\boxed{\sum_iH_i(S_{i,t}C_{i,t}-C_{i,t-1})
 +\sum_iS_{i,t}H_id_{i,t}
 +\sum_i\Delta_i(C_{i,t}-O_{i,t})-F_t.}
\end{aligned}
$$

The four terms are assigned as follows.

1. Revaluation of the shares carried over, with the correct change of units for a split.
2. The new economic right to a distribution.
3. The change in intraday exposure caused by today's trades.
4. The reduction of wealth by costs.

$P_t$ cancels: a previously accrued distribution by itself does not create today's profit. For a sale, $\Delta<0$, and the third term subtracts the intraday return of the shares sold at the Open: after the sale the account no longer owns them. For a purchase, $\Delta>0$, and the third term adds the intraday return of the new shares: they must not be credited with the movement from the previous Close to the Open.

An equivalent form, if an admissible Open exists for all the assets involved:

$$
\boxed{V_t-V_{t-1}=
\sum_i h_i\left(O_{i,t}-\frac{C_{i,t-1}}{S_{i,t}}+d_{i,t}\right)
 +\sum_iH_{i,t}(C_{i,t}-O_{i,t})-F_t.}
$$

The first term is the transition from the previous close to today's open together with the detachment of the distribution for the old owner; the second is the transition from open to close for the new composition of the portfolio. Proof of equivalence: distribute $h$ in the first term and $H_t=h+\Delta$ in the second; $hO$ cancels, and $hC_{prev}/S=H_{prev}C_{prev}$.

If all positions and cash are correct and the initial NAV is positive, then for admissible positive Close values and non-negative receivables NAV remains positive: either positive cash still exists, or positive assets were bought with it, or the value of the receivables is preserved. The daily return can then be obtained by division:

$$
R_t=(V_t-V_{t-1})/V_{t-1}.
$$

Each term of the decomposition divided by the previous NAV gives a contribution to this return. Without additional conditions the contribution of costs equals $F_t/V_{t-1}$, not $c\times\text{turnover}_t$, because turnover uses the NAV of the decision date.

Summing the decomposition over time gives the telescoping equality $V_T-V_0=\sum_t\mathrm{P\&L}_t$. This is additive profit in USD. The sum of daily percentage returns does not equal the total percentage return; the latter uses the product $\prod_t(1+R_t)=V_T/V_0$.

#### Checks of the decomposition on the manual examples

First entry of case 1: on the previous date there were no shares; 990 were bought at Open 100.5, Close 100, with costs 99.495. Therefore:

$$
\Delta V=990(100-100.5)-99.495=-594.495.
$$

NAV is $100000-594.495=99405.505$. The losing Open-to-Close movement of 495 USD and the costs of 99.495 have different sources.

Forward split of case 2b: before the session there were 811 shares at 61, S=3, Close=Open=20, a further 2433 were bought, and the costs were 48.66. Then:

$$
\Delta V=811(3\times20-61)+2433(20-20)-48.66
=-811-48.66=-859.66.
$$

NAV changes from $99950.529$ to $99090.869$. The fall of 811 is a price change: a pure split would correspond to the price $61/3$, not 20. The invariant `split_quantity_only` passes, as it should: a correct replacement of the quantity is compatible with a negative market return.

On the ex-date of case 3 the prices of both ETFs are constant, so the revaluation and intraday terms are zero. The accrual of 2020 USD minus the costs $98.98+98.882=197.862$ gives 1822.138, that is, $101723.158-99901.02$. On the pay date only the cost of the additional purchase of 37 shares remains: $1813\times0.001=1.813$; NAV goes from 101723.158 to 101721.345. The 2020 USD received are not added to P&L a second time.

### 15. Temporal causality: what the interface establishes

Execution is assigned by the indices of the common table:

$$
\operatorname{index}(e)=\operatorname{index}(t)+lag,\quad lag\in\{1,2\}.
$$

The existence of the sessions and the position of the execution inside the window are checked. Decision sessions strictly increase; an earlier decision cannot leave a pending package after the next decision. A window end later than 2022-12-30 is rejected. See `src/alpha_lab/engine.py:75`.

The provider receives `Market.history(t)`, in which open, close, dividend and `split_ratio` are truncated at $t$ inclusive, and payable contains only rows with ex-date $\le t$. See `src/alpha_lab/market.py:39` and `tests/test_engine.py:442`.

Conditional causality theorem. Suppose the provider is a deterministic function only of the permitted historical observations, does not access future data through external state, and these observations are identical up to $t$. Then its weights up to $t$ are identical. Order sizing uses identical weights, cash, positions, receivables and decision Close, so the orders are identical. By induction, identical events and executions up to $t$ give an identical state. A change of prices after $t$ cannot change a previously created quantity.

In case 1 the prices after the execution are replaced with Close=250 and Open=17; the decision target and the decision price are preserved. See `tests/test_engine.py:102`.

The premises of the theorem are essential. history retains the future `pay_session` of an ex-date that has already arisen, and `manifest_sha256` characterizes the complete vintage. The interface does not prove when the final pay date was historically known, does not restrict an arbitrary external file inside the provider function, and does not turn a retroactively corrected vintage into a point-in-time source. The restriction of rows is therefore a protection against direct access to future price bars through the passed object, not a full certificate of the absence of look-ahead.

The invariant `execution_timing` attests the binding of an order and a price to dates and the repetition of the sizing. It does not investigate where the provider obtained the signal. A provider that returned weights computed in advance from the future can pass it completely. When common sessions are missing, lag=1 means the next element of the intersection, not necessarily the next expected XNYS session; for the approved full vintage these coincide, according to a separate QA.

### 16. The seven invariants: exact conditions and the limit of the proof

During the loop, `Tally` records the total accruals $G$, the settlements $P$, the maximum NAV and cash-flow errors, split events and conversion errors. The final checks are implemented in `src/alpha_lab/engine.py:205`. The overall `passed` flag is the conjunction of seven flags, not a separate eighth financial test.

#### 16.1. `cash_non_negative`

The following is checked:

$$
\min(\{K_t\}_{daily}\cup\{cash\_after_j\}_{trades})\ge-10^{-8}.
$$

Purpose: the absence of debt-financed trades and of negative cash at the close. The intermediate states after individual trades are also taken into account, which is stronger than checking only the daily balance. There are no separate intermediate records after a split, accrual or payment, but these ordinary operations do not reduce cash. The check does not prove the absence of an outside change of positions or the correctness of the whole economic model.

#### 16.2. `nav_identity`

In every session:

$$
\left|V_t-\left(K_t+\sum_iH_{i,t}C_{i,t}+G_t-P_t^{cum}\right)\right|\le10^{-6}.
$$

The maximum error is stored. The initial $A=0$; with correct accrual and settlement, $A=G-P^{cum}$. The equality independently compares the current list of receivables with the accumulated accounting trail. However, the valuation of shares uses the same $H$ and $C$ as nav, so it does not attest to the correctness of the change of $H$ itself in a trade or to the truth of $C$. The addition of one USD to nav is detected in `tests/test_engine.py:264`.

#### 16.3. `cash_flow`

For each session:

$$
\left|K_t-K_{before,t}-\left(P_t+\sum_{sales}(N_j-F_j)-\sum_{buys}(N_j+F_j)\right)\right|\le10^{-6}.
$$

Purpose: the movement of cash is explained by distributions and recorded trades, and there are no unexplained cash inflows. This equality holds per session, not only over the whole period, so errors on different days cannot offset one another. However, it uses the notional and cost already recorded; `run_invariants` has no independent check of each notional against qty times price. It also does not check the complete position balance.

#### 16.4. `split_quantity_only`

Immediately after `apply_splits`, the exact equality $H_{new}=H_{old}\times S$ is checked for each ETF and $q_{new}=q_{old}\times S$ for pending orders; cash and the total receivables are unchanged. There is no tolerance here. Both the implementation and the check compute the same product in machine arithmetic, so exact equality is not a claim about the accuracy of real numbers with infinitely many digits.

The check does not cover the market ratio of the new price to the old one, the bitwise invariance of each individual receivable, or the self-financing of trades after the split. An artificial cash inflow at a split is detected in `tests/test_engine.py:321`.

#### 16.5. `receivable_conservation`

Both conditions are checked through the maximum of the errors:

$$
G_{end}=P_{end}^{cum}+A_{end},
\qquad\sum_{r:status=paid}r.amount=P_{end}^{cum},
$$

with the tolerance $10^{-6}$ USD. The second condition links the status of the historical payout records with the actual settlement. See `tests/test_engine.py:306`: if money is received without a change of status, this invariant fails although `nav_identity` passes.

Aggregate sums are controlled here. Wrong amounts of two receivables could offset each other. The correct owner, the exact ex-date session, the basis and the settlement of each receivable on its own due date are not proved. Checking the sums is necessary, but the economic semantics of the individual events is confirmed by the source data and by independent scenario tests.

#### 16.6. `execution_timing`

For each order the following are checked: the exact lag in indices, the exact agreement of the recorded decision-close with the market Close of that date, and the recomputed `target_qty=floor((1-r)wV/close)`. For a trade, the check is the existence of at least one order for its ticker and session, together with the exact equality `trade.price`=Open.

The following are not checked: the sign and the actual size of the trade relative to the order, the correctness of the position change, the optimality of the fill, the origin of the signals, or the real executability of the volume. Repeating the same sizing is also not an independent check of the accuracy of the formula in machine arithmetic. A change of `trade.price` is detected in `tests/test_engine.py:288`.

#### 16.7. `costs`

The maximum of

$$
\left|\sum_jF_j-c\sum_jN_j\right|,
\qquad\left|\sum_tcosts\_usd_t-c\sum_jN_j\right|
$$

is checked, and the value is required to be at most $10^{-6}$ USD. This confirms the aggregate costs and their link to the decisions. It does not check each trade independently; distortions of different trades could offset one another. A doubling of the recorded costs with unchanged cash causes `costs` and `cash_flow` to fail in `tests/test_engine.py:272`.

#### 16.8. Seven passing flags and the full P&L decomposition

The following counterexample was checked exclusively on a synthetic market and only by a temporary in-memory substitution of a function. After a normal purchase of 990 shares at 100, a wrapper adds one more share to `account.positions`, without changing `Trade`, cash or receivables. The recorded trade has qty=990; the daily position is 991. All seven invariants remain true.

The reason: `cash_flow` corresponds to the purchase actually paid for; `costs` and `execution_timing` correspond to its record; `nav_identity` revalues the positions that have already been changed; on the following days `split_quantity_only` compares yesterday's erroneous quantity with today's. There is no independent check of:

$$
H_{i,t}=S_{i,t}H_{i,t-1}+\sum_{buy(i,t)}qty-\sum_{sell(i,t)}qty.
$$

This position equality, together with the cash flow, is what the full self-financing decomposition of section 14 requires. The counterexample does not mean that the current ledger creates free shares: the ordinary code updates positions correctly. It shows the limited diagnostic power of the existing set of invariants and why they cannot be declared a universal proof of correctness of any modified engine.

Separate conditions on `Trade` records would also be useful: $\mathrm{qty}>0$, notional equal to qty times price, cost equal to $c$ times notional, and the link of each trade to a signed order and to filled_qty. Part of this semantics is guaranteed by the current implementation and by the scenario tests, but not by the seven invariants individually. No additional tests were added to the repository.

### 17. Numerical arithmetic: limits of the proofs for floating-point computation

Table prices are converted to float; cash and quantities are usually stored in machine arithmetic without rounding to cents. The model does not keep an integer ledger in cents. The ordinary sum is used for cash flows and NAV, so small residual errors are possible because of the order of operations; the absolute tolerances $10^{-8}$ and $10^{-6}$ USD are engineering decisions, not a relative guarantee for capital of arbitrary scale.

Floor is especially sensitive near an integer. Even a very small error in the quotient can change $Q$ by one share. An exact comparison in `execution_timing` does not detect this if the check repeats the same operations on the same type.

Confirmed discrepancy between the documentation and the common interface. In `EXECUTION_MODEL.md:46`, `np.float32` is described as widened to float64. However, `src/alpha_lab/engine.py:118` stores `raw[t]` without `float()`, and `src/alpha_lab/ledger.py:107` multiplies by it directly. In the current environment the intermediate arithmetic with such a weight remains `np.float32`.

A reproducible synthetic input:

```python
w = np.float32(0.5)  # 0.5 is represented exactly in both float32 and float64
nav = 100000.0
reserve = 0.01
close = 99.000001
math.floor((1-reserve) * w * nav / close)         # 500
math.floor((1-reserve) * float(w) * nav / close)  # 499
```

With float64 the quotient is approximately `499.99999494949503`; float32 gives `500.0`. This is not an error in the representation of w=0.5 itself but a reduced precision of the intermediate computations. `size_orders` does create `target_qty`=500 for the first variant. The existing test `test_provider_numpy_weights_are_accepted` (`tests/test_engine.py:399`) checks the acceptance of the type but not the agreement of such a discrete boundary with widened arithmetic.

The consequence is limited: the common API admits a type whose behavior diverges from the documented widening. This example does not establish that the registered built-in providers return `np.float32` or that their results are affected. No change of code and no repeated research run were performed.

CSV serialization uses `%.10g`, that is, ten significant digits, not ten decimal places. For magnitudes of about 100000 USD, the last stored decimal place is of the order of $10^{-4}$ USD. A repeated NAV reconciliation from the saved CSV files therefore need not fall within the internal $10^{-6}$, although the internal validation uses unrounded values. For a different scale of amounts the decimal error is also different; "about 1e-4" is not a universal bound. See `src/alpha_lab/engine.py:294` and `EXECUTION_MODEL.md:138`.

### 18. Relation of the manual scenarios to individual statements

| Scenario | What the synthetic reconciliation establishes | What it does not establish |
|---|---|---|
| Case 1 | Sizing at the decision close, execution at the next Open, cash and NAV; insensitivity of the order to later prices | Real executability at the Open, or all forms of provider causality |
| Case 2, 1:2 | Conversion of the position and of the sales, preservation of the fractional remainder, subsequent full closing | The market value of cash in lieu at a real broker |
| Case 2b, 3:1 | Conversion of a positive pending order and of the position | Zero return on the split: the entry from 61 to 20 contains a price movement |
| Case 3 | The seller's right on the ex-date, the absence of such a right for the new buyer, the use of cash after the pay date | The true historical ex-date dynamics under a constant synthetic price |
| Case 3b | An outstanding receivable with a due date after the window; settlement on the same day with proxy +0 | The empirical effect of all pay date variants |
| Case 4 | The common budget-constraint coefficient under a gap, floor and cancellation of the remainder | Optimality of the purchase, or maintenance of a fixed cash reserve |
| Case 5 | Sales before purchases, both sides of costs, the turnover formula | Equality of turnover to the distance between target weights |
| Case 6 | Fixing of the quantity at lag=2 and use of the Open of the second element of the common calendar | Preferability of such a lag |
| Case 6b | Cancellation of an order with a NaN Open, exclusion from $R$, absence of a trade | Freshness of any other finite Open |

The numbers and conditions are in `docs/n2/manual_reconciliation.md:15`; the implementations and expected values are in `tests/test_engine.py:50`. The reconciliations of monetary numbers use `pytest.approx(value, abs=1e-9)`. In the installed version an explicit abs without rel indeed gives an absolute tolerance of 1e-9; this was checked separately on the approx object. Integer targets, statuses and dates are compared exactly. Passing a finite set of scenarios is not a proof for all possible prices, weights and capital scales; the universal properties above were derived separately.

### 19. Verification performed

In the current working copy only a limited synthetic check was run:

```powershell
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider `
    tests/test_market.py tests/test_ledger.py tests/test_engine.py `
    -k 'not real_vintage' `
    --basetemp '<temporary directory outside the repository>' -q
```

Result: 109 passed, 1 deselected, 4.06 seconds according to the pytest output. `test_real_vintage_loads` is excluded; real data were not loaded. The flag -B prevents the creation of pyc files, `-p no:cacheprovider` excludes the pytest cache, and the temporary synthetic files are placed outside the repository. This is a current check, not a repetition of a historical research run. The environment prints a warning about locating the actual Python executable, but the test process finished with exit code 0.

Independently, without saving research results and without calling `run_simulation`, the P&L decomposition of section 14 was checked on two synthetic ETFs with a simultaneous split and accrual, a subsequent payment day, market movements and a rebuild of the portfolio. For c=0, 0.001 and 0.005 the maximum close-to-close errors of the decomposition were 0, `1.6484591469634324e-11` and `7.673861546209082e-12` USD, respectively. All seven ordinary invariants passed. This is a check of individual artificial trajectories, not a study of a strategy and not an estimate of alpha.

In addition, three targeted synthetic counterexamples were run: the influence of a fraction in $R$ on the neighboring purchase; the passing of the seven invariants after a free share is introduced in memory only; and the difference in `target_qty` between `np.float32` and float64 for the same exactly representable weight 0.5. Their results are described in sections 12, 16.8 and 17. None of these checks changed the sources, tests, execution settings, experiment journal or data of the repository. The synthetic script that reproduces them is stored outside the repository; its rerun completed successfully and reported NumPy 2.5.3.

### 20. Established result and open boundaries

Under finite admissible inputs, a correct initial state, exact arithmetic and ordinary transitions, the ledger mathematically ensures non-negative positions, the absence of overspending of cash, single recognition of a distribution, a correct conversion of quantity at a split, and an exact self-financing decomposition of wealth. The machine implementation was checked on the stated synthetic set with the monetary tolerances taken into account.

The return or utility of a strategy, the freshness of real prices, the available auction volume, the historical knowability of corrected distributions, the optimality of discrete execution and the universality of the seven diagnostic flags cannot be inferred from this. Two items require separate attention: the absence of an independent position balance in the final invariants, and the specific discrepancy between the common `np.float32` interface and the documentation concerning float64. These boundaries were established without opening hypothesis results and without changing the economic rules.

## Part IV. Metrics, adaptive selection and statistical inference

Verified snapshot: `7a8ba1d56938e2576b537fff670ba0363e6e618c`, 10 October 2026. This part concerns the project `cross-asset-alpha-lab`. It explains the mathematical definitions and provable properties of the methods, not the economic results of the hypotheses. The actual H1/H2 NAV series, research results and the reserved period were not opened. Sources, tests, configuration and the journal were not modified; the STATUS entry is described in the introduction.

### 1. What is implemented and what is only registered

`src/alpha_lab/metrics.py` implements daily returns, total return, CAGR, sample volatility, mean excess return, the Sharpe ratio relative to BIL, utility, maximum drawdown, turnover, costs and exposure statistics. This is the existing computation path for benchmark metrics. The existence of a function that can process a `Result` object does not mean that the economic results of H1/H2 have already been computed: stage N4 deliberately preserved them without these estimates.

The adaptive policy P_A1, the `inference.py` module, the bootstrap, Holm adjustment, regressions and the evaluation report are not implemented at the verified HEAD. This is stated directly in the N5 specification, `docs/superpowers/specs/2026-10-09-n5-evaluation-design.md:3`, and the list of files in `src/alpha_lab` confirms it. Accordingly, below the word "computes" refers to the existing `metrics.py`, and the word "provided for" refers to the approved future N5/N6. `DECISIONS.md:223` (D025) records the decisions made before any N5 code or results.

| Object | Status at HEAD | Primary source |
|---|---|---|
| Metrics of individual accounts | Implemented | `metrics.py:36-99` |
| Theoretical BIL total return index | Implemented | `features.py:19-28` |
| H2 as removal of some parent weights | Implemented | `hypotheses.py:45-63` |
| P_A1, annual selection and its stability | Approved N5 design | specification `78-109` |
| Paired circular bootstrap and basic CI | Approved N5 design | specification `123-125` |
| Holm adjustment for six comparisons | Approved N5 design | specification `127-129` |
| OLS, HAC and alpha intervals | Approved N5 design | specification `131-133` |
| Stress scenarios and final criteria | Assigned to N6 | protocol `169-188` |
| Downside deviation, Sortino | Absent from the implementation and from the N5 contract | full `metrics.py`, protocol section 11 |
| DSR, PBO, bootstrap of the whole adaptive procedure | Excluded from N5 | specification `135-137` |

### 2. Notation, observations and economic basis

Let $V_t>0$ be the NAV of the account at the close of session $t$, including the value of the ETFs, USD cash and accrued but not yet paid distributions. This is the economic value of the whole account. Therefore the conversion of a distribution receivable into cash creates no additional profit, and trading costs reduce NAV.

For a period, the indices $t_1,\ldots,t_n$ of the daily rows whose date lies in the given range are selected. In `metrics.py:38` the search starts at index 1: the first row of the whole simulation is the base and has no previous observation. The period base $V_0$ is the previous close within the given account, immediately before the first selected row (`metrics.py:42-44`). For the full account this is the initial NAV; for 2014 in a continuous account it is the end of 2013. Consequently the first daily return of the period includes the transition across its boundary, and the first entry from cash includes trading costs. The period boundary code is at `src/alpha_lab/metrics.py:38`.

Define

$$
r_t=\frac{V_t}{V_{t-1}}-1,\qquad
b_t=\frac{T^{BIL}_t}{T^{BIL}_{t-1}}-1,\qquad
e_t=r_t-b_t.
$$

$T^{BIL}$ is the theoretical total return index of BIL with immediate reinvestment of distributions, not the B0 account with delayed payments, a cash remainder and entry costs. `compute_metrics` obtains this index through `total_return_index`, then constructs $b_t$ and $e_t$ (`metrics.py:87-91`). Therefore the excess return relative to BIL and the advantage over the executable benchmark B0 are different comparisons. This is not a defect: the contract fixes exactly this basis.

For the index series of a single ETF the following applies:

$$
\frac{T_t}{T_{t-1}}
=s_t\frac{C_t+D_t}{C_{t-1}},
$$

where $s_t$ is the split ratio and $C_t,D_t$ are expressed in consistent as-traded units. The first value of $T$ is normalized to 1. See `src/alpha_lab/features.py:19`. This formula constructs the return of an instrument for a signal or comparison; it must not be added to the actual account, which already accrues distributions, because that would double count them.

The constant $A=252$ is the number of nominal trading sessions in a year (`features.py:11`). This is the established unit of annual scale; a particular calendar year may have 251 or 253 sessions. All computations must use the same dates, NAV base and BIL. Comparing a series of $n$ observations with another series of $n-1$ observations changes the mean, the variance and the initial entry, even if the difference is a single date.

### 3. Returns: exact identities and annual conventions

#### 3.1. Total return and the telescoping product

By definition $1+r_t=V_t/V_{t-1}$. Hence

$$
\prod_{t=1}^{n}(1+r_t)
=\frac{V_1}{V_0}\frac{V_2}{V_1}\cdots\frac{V_n}{V_{n-1}}
=\frac{V_n}{V_0}.
$$

All intermediate NAV values cancel. The total return

$$
R_{total}=\frac{V_n}{V_0}-1
$$

is the exact realized relative gain of the account in the simulation, provided that NAV is not distorted by external contributions or withdrawals. The code uses the ratio of the final NAV to the base (`metrics.py:45,61`) and does not sum daily percentages. For example, $+10\%$ followed by $-10\%$ gives $1.1\times0.9-1=-1\%$, although the sum is zero.

#### 3.2. CAGR

Let $g$ be the constant annual rate that gives the same accumulation over $n/A$ nominal years. Then

$$
(1+g)^{n/A}=\frac{V_n}{V_0}
\quad\Longrightarrow\quad
g=\left(\frac{V_n}{V_0}\right)^{A/n}-1.
$$

This is implemented literally (`metrics.py:61`). For positive NAV values one can write

$$
\log(1+g)=\frac{A}{n}\sum_t\log(1+r_t).
$$

Consequently CAGR is an annual geometric rate, whereas $A\bar r$ is an arithmetic rate. They coincide only approximately when variability is small. The expansion $\log(1+r)\approx r-r^2/2$ shows the effect of volatility on accumulation: the negative correction depends on the mean square of the return, not only on the mean.

On a short interval the exponent $A/n$ amplifies any random outcome. This is a consequence of the formula and not a forecast of the return for the next year. For this reason the protocol requires the total return of an incomplete year to be reported separately. CAGR uses trading time rather than actual calendar time; this is an explicit convention.

#### 3.3. Annual mean excess return

$$
\bar e=\frac1n\sum_t e_t,\qquad
\mu_{ann}=A\bar e.
$$

`mean_excess` (`metrics.py:63`) is the arithmetic mean expressed on an annual scale. It is not the excess CAGR and not the exact difference of compound annual returns. For a candidate $c$ and a comparison account $q$ with the same BIL:

$$
A(\bar e_c-\bar e_q)
=A\,\overline{r_c-r_q},
$$

because BIL is subtracted and cancels in every pair of dates. In the variance, by contrast, BIL does not cancel automatically.

### 4. Sample variance, volatility and the Sharpe ratio

#### 4.1. Rationale for `ddof=1`

For a series $x_1,\ldots,x_n$

$$
s_x^2=\frac{1}{n-1}\sum_t(x_t-\bar x)^2.
$$

For independent identically distributed observations with variance $\sigma^2$:

$$
\sum_t(x_t-\bar x)^2
=\sum_t(x_t-\mu)^2-n(\bar x-\mu)^2.
$$

The expectation of the first term is $n\sigma^2$, and that of the second is $n\operatorname{Var}(\bar x)=\sigma^2$. Hence the expected sum of squares equals $(n-1)\sigma^2$, and division by $n-1$ removes this bias. This gives `ddof=1` (`metrics.py:59-65`). Under temporal dependence $\operatorname{Var}(\bar x)$ contains covariances, so `ddof=1` no longer guarantees exact unbiasedness. It remains the registered sample convention.

For $n=1$ the denominator is zero, and the dispersion metrics are undefined. The code returns `None` for volatility, Sharpe and utility, while retaining total return, CAGR and mean excess return (`metrics.py:59-65`). A period without any daily return is omitted altogether (`38-40`).

#### 4.2. NAV volatility

$$
\widehat\sigma_{r,ann}=\sqrt{A}\,s_r.
$$

This is the standard deviation of the ordinary return of the account (`metrics.py:62`). The factor $\sqrt A$ follows from

$$
\operatorname{Var}\!\left(\sum_{t=1}^{A}r_t\right)
=A\sigma_r^2
$$

under equal variances and no correlation between days. In the general stationary case

$$
\operatorname{Var}\!\left(\sum_{t=1}^{A}r_t\right)
=A\gamma_0+2\sum_{h=1}^{A-1}(A-h)\gamma_h,
$$

where $\gamma_h=\operatorname{Cov}(r_t,r_{t-h})$. Consequently the realized annual volatility is a coherent convention but not an exact estimate of annual risk under autocorrelation, and not the standard deviation of the compound annual return. The bootstrap partly accounts for local dependence in the uncertainty of an effect; it does not change the definition of the reported volatility.

#### 4.3. Sharpe ratio relative to BIL

$$
\widehat S_{BIL}=\sqrt A\frac{\bar e}{s_e}.
$$

For additive annual excess return with uncorrelated daily excess returns, the numerator scales with $A$ and the denominator with $\sqrt A$, which gives the factor $\sqrt A$. See `src/alpha_lab/metrics.py:64`.

The denominator is $s_e$ and not $s_r$:

$$
\operatorname{Var}(r-b)
=\operatorname{Var}(r)+\operatorname{Var}(b)-2\operatorname{Cov}(r,b).
$$

BIL has its own varying returns. The relative quality by Sharpe ratio and the total volatility of the account may produce different rankings. For $s_e=0$ the ratio is undefined: the Sharpe ratio is returned as `None`, even if the excess return is positive. A conventional "infinite Sharpe ratio" is not reported. Zero volatility of the ordinary return $r$, by contrast, is a valid number, 0.

#### 4.4. Downside deviation and Sortino: an explanation of a missing method only

Neither `downside_deviation` nor Sortino exists in `metrics.py`. They must not be listed among the results or among the approved N5 metrics. The drawdown below is a separate risk measure and not a downside deviation.

To understand the difference, one commonly introduces the lower partial moment relative to a daily threshold $\tau$:

$$
DD_{\tau,ann}=\sqrt{\frac A n\sum_t\min(x_t-\tau,0)^2}.
$$

In it, positive deviations contribute zero and are not penalized symmetrically. Division by all $n$ differs from division only by the number of unfavorable days: these are different definitions. A Sortino ratio would require a separate fixing of $x$, the threshold, the denominator and the annual scale. The notion of "downside-only risk" does not follow from the already existing variance criterion U. Adding such a metric now would require a decision on the method; this part does not add it.

### 5. Utility and the primary difference in effect

#### 5.1. Formula and the meaning of the coefficient

$$
U(x)=A\bar x-\frac\gamma2 A s_x^2,
\qquad \gamma=3,
$$

where $x=e$. In the code `UTILITY_PENALTY=1.5` (`metrics.py:13,65`); $\gamma/2=1.5$ explains the relation to the coefficient 3 in the protocol. This is a chosen compromise between the mean result and variability. The coefficient is not estimated from data and not optimized. It is not a demonstrated individual risk aversion of an investor.

The relation to the mean-variance certainty equivalent can be derived for a normally distributed additive return $X\sim N(\mu,\sigma^2)$ and exponential utility: $\mathbb E\exp(-\gamma X)=\exp(-\gamma\mu+\gamma^2\sigma^2/2)$. The certainty equivalent $CE$, satisfying $\exp(-\gamma CE)=\mathbb E\exp(-\gamma X)$, equals $\mu-\gamma\sigma^2/2$. For independent days the annual $\mu,\sigma^2$ scale additively with $A$, and the registered form is obtained. Under non-normality this is a second-order interpretation; for actual compound wealth, tails, drawdown and changing weights it is not exact. In the project the formula remains the definition of a statistic; the interpretation above only motivates it.

Units: the mean is a decimal return, the variance is a squared return, and $\gamma$ reconciles their scales. Returns must not be changed from decimal values to percentages without changing the coefficient: the mean would increase 100 times and the variance 10000 times, and the criterion would become a different one. A value of $+0.01$ means one percentage unit of annual utility, not necessarily $+1\%$ CAGR.

#### 5.2. Rationale for the difference of two utilities rather than the utility of the difference

For a candidate $c$ and a comparison account $q$:

$$
\widehat\Delta U
=A(\bar e_c-\bar e_q)-\frac\gamma2 A(s_c^2-s_q^2).
$$

But

$$
U(e_c-e_q)
=A(\bar e_c-\bar e_q)-\frac\gamma2 A\{s_c^2+s_q^2-2s_{cq}\}.
$$

The first expression answers the question of how much the quality of two whole accounts differs under a single criterion. The second penalizes the tracking error of the difference and answers a different question. Substituting one for the other changes the research hypothesis. The bootstrap must compute both utilities separately each time and then subtract.

With a common BIL basis

$$
s_{e_c}^2-s_{e_q}^2
=s_{r_c}^2-s_{r_q}^2-2\{s_{r_c,b}-s_{r_q,b}\}.
$$

The variance of BIL cancels, but the covariances with BIL may differ. Therefore the whole excess risk cannot be replaced by the ordinary volatility.

#### 5.3. Economic threshold

The protocol, `RESEARCH_PROTOCOL.md:159`, requires $\Delta U\ge0.01$ and $A(\bar e_c-\bar e_q)>0$. The second condition prevents an improvement obtained solely through lower variability with a smaller mean result from being accepted as useful. The threshold is a price of additional complexity chosen in advance and not the result of statistical optimization.

For H1 the primary comparison account is B3, and for H2 it is the fixed H1_252_3. H2 vs B3/B2 are mandatory as supplementary comparisons. Even a good supplementary result does not replace a failed comparison of H2 with its parent. P_A1 has a separate comparison account with the same start in cash.

### 6. Drawdown: the NAV path and the initial maximum

Let

$$
H_t=\max(V_0,V_1,\ldots,V_t),\qquad
D_t=\frac{V_t}{H_t}-1\le0,
\qquad MDD=\min_{0\le t\le n}D_t.
$$

This is implemented with `path=[base,*navs]`, `maximum.accumulate(path)` and a minimum (`metrics.py:46,66`). The initial base is mandatory: a fall from 100 to 90 on the first day gives $MDD=-10\%$, although the first published NAV of 90 would by itself be a false new maximum. When NAV reaches a new high, $D_t=0$. The negative value of MDD in the JSON is a signed drawdown; if the text states "a drawdown of 10%", then $-MDD$ is used.

The maximum drawdown depends on the order of returns and not only on the mean and variance. Therefore equal utilities do not imply equal drawdowns. The existing code computes a separate drawdown within each period, with the previous close as the initial high. It does not inherit the 2009-2013 maximum when computing the 2014-2022 period. Consequently its walk-forward MDD is the local drawdown of the selected window and not the maximum drawdown of the full account that entered the window from an earlier peak. This corresponds to the chosen period-base convention; the difference must be taken into account when reading the tables.

### 7. Turnover, costs and exposures

#### 7.1. Turnover and its denominator

At the execution of decision $d$:

$$
TO_d=\frac{\sum_{j\in trades(d)}|N_j|}{V_{decision(d)}},
\qquad TO_{period}=\sum_{d\in period}TO_d,
\qquad TO_{ann}=\frac A n TO_{period}.
$$

Executed notionals are positive on both sides of a trade, so `engine.py:182` sums them without an explicit `abs`. Selling 20% of the account and buying another position for 20% gives a turnover of about 40%, not 20%. There is no division by two.

The term `pretrade_NAV` in the protocol is clarified by `DECISIONS.md:169` (D022): the denominator is the NAV at the close of the decision date, used for order sizing. It is not the NAV before trading at the next open. `engine.py:197` stores the `value` of the decision date, and `182` uses it later. The difference due to the overnight move is provided for by the decision, so no discrepancy with the current contract was found here.

#### 7.2. Costs

$$
Costs_{USD}=\sum_d C_d,\qquad
CostRatio=\sum_d\frac{C_d}{V_{decision(d)}}.
$$

With a single proportional cost $c$ per side, $C_d=c\sum_j|N_j|$, hence $CostRatio=c\,TO_{period}$, up to numerical summation accuracy. This is a useful consistency check. See `metrics.py:48-49,67-68` and `engine.py:207-209`.

CostRatio is a sum of relative charges with a changing denominator. It is not equal to $\sum C/\overline V$, is not an exact loss of compound return and is not equal to the difference between net and gross CAGR. An exact cost drag requires a separate account without costs: costs change the size of future positions, the available cash and subsequent returns. `DECISIONS.md:173` (D022) fixes this interpretation explicitly. Net NAV already contains the costs; they must not be subtracted additionally from the computed $r$.

Decisions, turnover, costs and `mean_target_risky` belong to the period of execution and not to the period in which the decision was formed (`metrics.py:47-50`). Therefore a December decision executed in January falls into the new year. The count `decisions` counts all decision records, including those without trades; it is not the number of trades and not necessarily the number of successful purchases.

#### 7.3. Held and target exposure

At the close:

$$
w_{i,t}^{held}=\frac{q_{i,t}C_{i,t}}{V_t},\quad
w_{cash,t}=\frac{Cash_t}{V_t},\quad
w_{rec,t}=\frac{Receivables_t}{V_t},\quad
w_{risky,t}=\sum_{i\in risky}w_{i,t}^{held}.
$$

The group weight is the sum of the weights of the group members. `shares` (`metrics.py:22-33`) constructs these shares, and `period_metrics` takes the daily arithmetic mean and the maximum over the closes. Under a correct accounting identity and a complete set of instruments, cash + BIL + receivables + risky equals 1. Receivables are not part of `mean_cash_plus_bil`, because they are not yet available for trading.

`mean_target_risky` is the mean of the sum of the target risky weights over the decisions of the period, and `mean_risky` is the mean over days of the realized weights at the close. Differences between them are possible because of weight drift, order reserves, execution costs and delays. The daily maximum of a group or instrument may exceed the cap imposed on the target weights: a price rise after the decision does not prove a violation of the limit applied in order sizing. Close-based metrics also do not measure intraday maxima.

### 8. P_A1: the complete causal mechanism of the future selection

#### 8.1. Object of selection

One of four H1 configurations is selected: H1_252_3, H1_252_4, H1_126_3, H1_126_4. H2 does not participate, and the parent H1_252_3 participates first. This is a separate adaptive policy and not a seventh fixed signal configuration. The order, the utility criterion U with its coefficient, the windows and the tolerance are fixed; however, the selection of a configuration by historical U is itself an adaptation to the data. The expression "no estimated parameters" means the absence of additional numerical model parameters and not the absence of selection uncertainty.

For a year $Y\ge2014$ exactly five preceding calendar years $Y-5,\ldots,Y-1$ are available. The first three serve as history for the deterministic signals and not as an optimization sample. The last two provide the estimate for the internal validation. Each of the four candidates has its own continuous internal-validation account, starting in cash on the last session of December $Y-3$ and ending on the last session of December $Y-1$. This yields 24 decisions with execution inside the segment; the December decision of $Y-1$ is not executed in this segment. See the specification, `docs/superpowers/specs/2026-10-09-n5-evaluation-design.md:86`.

For 2014 the context is 2009-2011, the internal-validation returns are 2012-2013, and the initial base is the last close of 2011. In computing U there is no separate annual reset of the account between 2012 and 2013. All candidates are evaluated on common dates and execution rules. The first three years do not enter U; they provide the pre-history for all signals.

#### 8.2. Mathematics of the close set

$$
U_{best}=\max_i U_i,\qquad
\mathcal C=\{i:U_i\ge U_{best}-0.001\}.
$$

If all $U_i$ are finite, the set is nonempty: the maximum itself belongs to it. The first element of $\mathcal C$ in the fixed order is selected. Therefore the selected $i$ may have a utility below the maximum, but the difference is at most 0.001. Exact equality with the boundary is included. This is neither a rounding of U nor a sorting by U alone; it is a tolerance and a preference established in advance.

For example, $U=(0.1000,0.1009,0.0900,0.0700)$ gives a close set of the first two and the selection of H1_252_3, although the maximum belongs to H1_252_4. With a maximum of 0.1020 the first candidate at 0.1000 no longer qualifies. The test is applied to floating-point numbers literally; an arbitrary epsilon must not change the rule.

If at least one U is not finite while the data are fully valid and the financial checks have succeeded, a fixed fallback selection of H1_252_3 with a warning is provided for. A missing date, a warm-up shortfall, a provider exception or a violated invariant halt the computation. A faulty candidate must not be silently dropped with the selection made among the rest: that would be an unregistered selection rule. See `DECISIONS.md:237` (D025).

#### 8.3. Causality and the state of the actual account

The selection is fixed at the close $s_Y$, the last session of December $Y-1$, before the first open of year $Y$. The history of the nested simulations must be truncated at $s_Y$, even if the computation is first requested later. Otherwise the current date of the call would silently add future data to a selection that is already in the past. The cache is limited to a single provider instance and the key $Y$, the data vintage hash and $s_Y$, so that no foreign history can change the selection.

The decision uses the selection of the execution year, so a decision in December $Y-1$ already uses the selection for $Y$. The actual P_A1 account starts in cash on 2013-12-31 and then carries positions, cash and receivables across years without a reset. The selection determines the rule for target weights; switching produces ordinary causal orders and costs. Each new monthly decision uses the current signals of the selected H1 and not the frozen weights of the internal-validation account.

The fixed H1/H2 accounts and the benchmarks for the walk-forward evaluation, by contrast, are slices of accounts that began on 2008-12-31. Therefore P_A1 cannot be compared cleanly with the continuous H1_252_3: they begin 2014 in different states. P2 provides a separate H1_252_3 account starting in cash on 2013-12-31. This controls the entry cost and the first overnight exposure; it does not make P_A1 an independent experiment. See `DECISIONS.md:227` (D025).

The selection for 2023 is not computed in N5, although its input dates precede 2023: this already belongs to the decisions of the reserved-period campaign N6. Such a barrier is procedural and not a mathematical lack of data.

### 9. Paired circular block bootstrap

#### 9.1. Index construction

For $n$ matched dates and a block length $L\in\{21,63,126\}$, set $M=\lceil n/L\rceil$. For replicate $b$, the block starts $S_{b,j}$ are drawn independently and uniformly from $\{0,\ldots,n-1\}$, $j=1,\ldots,M$. A block is

$$
I_{b,j,a}=(S_{b,j}+a)\bmod n,\qquad a=0,\ldots,L-1.
$$

After the $M$ blocks are concatenated, the first $n$ indices are kept. The same indices are applied to the whole row $(r_c,r_q,b)$. For example, with $n=5,L=3$ and starts $4,2$, the sequence $4,0,1,2,3,4$ is truncated to $4,0,1,2,3$. The local order is preserved inside a block, and a block may wrap around the end of the series. The starts of new blocks break long-range dependence.

With a uniform start and a fixed offset $a$, the index $(S+a)\bmod n$ is also uniform. Every position of a full or truncated block therefore has a uniform marginal probability over the original dates, and the ends of the original series do not have a lower chance of selection. This is an advantage of the circular construction, but the artificial junction of the end of the history with its beginning is not a real market sequence.

Pairing is used because, for the means,

$$
\operatorname{Var}(\bar e_c-\bar e_q)
=\operatorname{Var}(\bar e_c)+\operatorname{Var}(\bar e_q)
-2\operatorname{Cov}(\bar e_c,\bar e_q).
$$

Resampling the candidate and the comparison account independently would destroy the last term. It would usually lose the benefit of comparing on the same market dates and would estimate a different experiment. Joint blocks preserve both the contemporaneous cross-series movements and the dependence within a block. BIL must fall in the same replicate.

#### 9.2. Replicates, seed and estimate

For each replicate, $e_c^*=r_c^*-b^*$ and $e_q^*=r_q^*-b^*$ are formed, and then

$$
\Delta U_b^*=U(e_c^*)-U(e_q^*).
$$

The registered values are $B=10000$, seed 20261006 and primary $L=63$. The generator `Generator(PCG64(seed))` is created anew for each pair $(n,L)$; the starts have shape $(B,\lceil n/L\rceil)$. Shared $(n,L)$ give shared random indices regardless of the order of comparisons. Chunking must preserve the same sequence of random numbers and the same replicates; this is a reproducibility constraint that a future implementation still has to verify. See the specification, `docs/superpowers/specs/2026-10-09-n5-evaluation-design.md:125`.

All three lengths are shown, rather than the most favorable one. A larger L preserves longer dependence but yields fewer nearly independent blocks; a smaller L increases their number but may understate persistence. With $n=2266$ and $L=63$, a replicate consists of approximately 36 blocks, not 2266 independent days. This is not an exact effective number of independent observations, but it explains why thousands of daily rows do not provide thousands of independent pieces of evidence.

#### 9.3. Basic 95% CI: derivation by quantile reflection

Let $\theta=\Delta U$, let $\hat\theta$ be the observed estimate, and let $E=\hat\theta-\theta$ be the estimation error. The bootstrap approximates the distribution of $E$ by the distribution of $E^*=\theta^*-\hat\theta$.

If $q_{.025}\le E\le q_{.975}$, then

$$
\hat\theta-q_{.975}\le\theta\le\hat\theta-q_{.025}.
$$

The bootstrap error quantiles are $q_p=Q_p(\theta^*)-\hat\theta$. Substitution gives

$$
CI_{basic}=
\left[2\hat\theta-Q_{.975}(\theta^*),\;
2\hat\theta-Q_{.025}(\theta^*)\right].
$$

The quantiles exchange places because of the subtraction. This is the basic interval, which reflects the bootstrap distribution around $\hat\theta$; it is not the percentile interval $[Q_{.025},Q_{.975}]$, a studentized interval or a BCa interval. The nominal 95% denotes approximate coverage under repeated sampling and suitable assumptions. It is not a 95% probability that the fixed true parameter lies in the particular published interval.

The specification fixes `numpy.quantile(method='linear')`. If the ordered $B$ replicates are indexed from zero, with $h=(B-1)p$, $j=\lfloor h\rfloor$ and $g=h-j$, then $Q_p=(1-g)\theta^*_{(j)}+g\theta^*_{(j+1)}$. This interpolation is confirmed by the [official NumPy documentation](https://numpy.org/doc/stable/reference/generated/numpy.quantile.html). The environment version is fixed separately; the current web page does not replace the project lock file.

#### 9.4. One-sided centered p: exact direction of the inequality

The test is of $H_0:\theta\le0$ against $H_1:\theta>0$. At the boundary null $\theta=0$, the observed positive statistic equals the error $\hat\theta$. The bootstrap therefore estimates the right tail of the centered error:

$$
p=\frac{1+\sum_{b=1}^{B}
\mathbf1\{\theta_b^*-\hat\theta\ge\hat\theta\}}{B+1}
=\frac{1+\sum_b\mathbf1\{\theta_b^*\ge2\hat\theta\}}{B+1}.
$$

The threshold $2\hat\theta$ follows from the centering. Replacing it with 0, using the left tail, counting $\theta_b^*\le0$ or subtracting the estimate twice would implement a different test. Equality is included by the sign `>=`. This is fixed by the protocol, `RESEARCH_PROTOCOL.md:161`.

The $+1$ correction prevents a zero Monte Carlo p: the minimum is $1/10001$ and the maximum is 1. It does not turn the centered bootstrap into an exact permutation or randomization test. For a composite null it is assumed that the boundary distribution at 0 is suitable for the required right tail; a bootstrap with imprecise centering, changing regimes and a variance component has no proven exact finite-sample level here.

For identical series, all $\theta_b^*=\hat\theta=0$. Every replicate satisfies $0\ge0$, so $p=1$ and the CI equals $[0,0]$. This is a suitable future regression test. For a negative estimate, p is usually large, but without symmetry the universal rule "necessarily at least 0.5" cannot be asserted.

As an illustration, not as research, take $\hat\theta=.02$ and five artificial replicates $-.01,0,.01,.04,.06$. The linear quantiles are $Q_{.025}=-.009$ and $Q_{.975}=.058$; the basic CI is $[-.018,.049]$. The right tail $\theta^*\ge.04$ contains two replicates, so $p=(1+2)/6=.5$. This checks the algebra, not the quality of a real bootstrap.

With $B=10000$, the rough conditional Monte Carlo SE for a probability near .05 is $\sqrt{.05\times.95/10000}\approx.00218$. A shared seed provides reproducibility but does not remove this approximation. A CI with a lower endpoint $>0$ uses the two-sided 95% right quantile .975, whereas the one-sided p of .05 uses a 5% right tail. The CI and the raw p therefore need not lead to the same decision. The protocol requirement of both checks is a joint, stricter criterion and not a mathematical contradiction.

#### 9.5. Conditions of applicability

The resampled object is the return series of a completed account. Trades, queues, receivables, covariance estimates and signals are not recomputed after the permutation. The resulting replicate is not a new executable simulation of the strategy on an artificial market. It estimates the uncertainty of a statistic of the fixed observed return process, conditional on the model and rule already chosen.

Theoretical consistency of the block bootstrap requires suitable stationarity or an approximation by local stationarity, weakening of temporal dependence and sufficiently many finite moments. For the variance part of the utility, tails and higher-order moments are especially important. The standard asymptotic regime assumes that the block length grows as $n\to\infty$ with $L/n\to0$; the three fixed lengths of the project are a finite-sample sensitivity check and not a proof of this regime. Structural breaks, the retrospective composition of instruments, the concentration of crises and selection on a familiar history can violate the interpretation. Circular blocks do not create new independent crises.

The historical primary source of the construction is Politis and Romano, "A circular block-resampling procedure for stationary data", 1992; the bibliographic entry appears in the [author's official publication list](https://profiles.stanford.edu/joseph-romano?tab=publications). The construction and algebra of this part are presented independently; the project's basic CI and p have their own registered contract.

### 10. Holm: algorithm, adjusted p and proof of FWER control

#### 10.1. Family and ordering

There are six p-values at the single primary length 63: four H1 against B3 and two H2 against H1_252_3. The additional comparisons of H2 against B3 and B2, and P_A1, are outside the family. The first are not additional protected confirmatory results, and no p is defined for P_A1 at all. The three bootstrap lengths must not be turned into 18 opportunities to choose the best p without a new multiple-testing adjustment.

Order the values as $p_{(1)}\le\cdots\le p_{(m)}$ with $m=6$. The step-down Holm procedure at $\alpha=.05$ rejects successively as long as

$$
p_{(i)}\le\frac{\alpha}{m-i+1}.
$$

After the first failure, no further hypotheses are rejected. The prescribed adjusted p is

$$
\tilde p_{(i)}=
\max_{j\le i}\min\{1,(m-j+1)p_{(j)}\}.
$$

The cumulative maximum is needed because the hypothesis at position $i$ passes only after all preceding ones have passed. It makes the adjusted p-values non-decreasing. They are then mapped back to the original candidate identifiers. Equal raw p-values receive the same adjusted p: the earlier of the equal values is multiplied by a larger factor and enters the maximum of the later ones, so the order of ties gives no advantage.

The example $p=(.005,.010,.012,.030,.200,.800)$ gives $\tilde p=(.030,.050,.050,.090,.400,.800)$. With the standard `<=.05`, the first three are rejected. However, the final economic criterion of the project literally requires Holm p `<0.05`, and values of exactly .05 do not satisfy it. The step-down FWER statement is usually written with `<=`; the strict project boundary is more conservative and must be retained in the implementation rather than replaced out of habit.

#### 10.2. Full proof of strong FWER control

Let $I_0$ be the set of indices of the true null hypotheses, with $m_0=|I_0|$. For each true null, assume that p is valid, that is, $P(p_i\le u)\le u$ for every $u\in[0,1]$. Independence of the p-values from each other is not required.

Suppose the Holm procedure rejects at least one true null hypothesis. Consider the first true null in the sorted order, at position $j$. All $m_0$ true nulls lie at positions $j$ onward, so $m-j+1\ge m_0$. For it to be rejected, it must hold that

$$
p_{(j)}\le\frac\alpha{m-j+1}\le\frac\alpha{m_0}.
$$

This $p_{(j)}$ is the minimum p among the true nulls. The event of at least one wrongful rejection is therefore contained in

$$
\bigcup_{i\in I_0}\{p_i\le\alpha/m_0\}.
$$

By the union bound,

$$
FWER\le\sum_{i\in I_0}P(p_i\le\alpha/m_0)
\le m_0\frac\alpha{m_0}=\alpha.
$$

For $m_0=0$ an error is impossible. The proof works for any number of false nulls, so the control is strong, and for any dependence structure, so shared market dates and a shared bootstrap do not break it. The primary source of the method is [Holm, 1979](https://www.jstor.org/stable/4615733).

The proof, however, begins from valid individual p-values. Here the centered bootstrap is approximate. In addition, the familiarity of the history and the unmeasured awareness of past data are not included in the complete family of all research decisions. The formal Holm formula is therefore correct, but an exact 5% global research false-discovery guarantee for this project is not proved. The adjustment accounts for the six registered comparisons, not for all possible manual inspections, the chosen universe, the idea, the history and the parameters. D025 explicitly retains the exploratory label. Holm controls the probability of at least one false rejection in the family; it does not control the probability that a selected strategy is useful, and it is not a posterior probability of a hypothesis.

### 11. Monthly compounding and asset-class proxies

The future N5 uses 108 complete months from January 2014 to December 2022 and 2266 daily returns on the same XNYS sessions. For an account,

$$
R_m=\frac{V_{end(m)}}{V_{end(m-1)}}-1
=\prod_{t\in m}(1+r_t)-1.
$$

This follows from the same telescoping product. January 2014 necessarily uses the December 2013 base; otherwise the first daily return is lost. A month is complete only if both the required end and the required start are present; the latest available intermediate close does not turn an unfinished month into a complete one. Similarly, $B_m=T^{BIL}_{end(m)}/T^{BIL}_{end(m-1)}-1$.

The monthly excess $R_m-B_m$ is not equal to $\prod_{t\in m}(1+e_t)-1$. For example, if the daily portfolio and BIL returns vary jointly, daily subtraction and compound accumulation do not commute. Each whole series is compounded first, and the monthly BIL is subtracted afterwards. See `DECISIONS.md:243` (D025).

For a group $g$ with $K_g$ ETFs,

$$
F_{g,m}=\frac1{K_g}\sum_{i\in g}(R_{i,m}-B_m)
=\frac1{K_g}\sum_{i\in g}R_{i,m}-B_m.
$$

The composition is fixed: Equity is SPY/EFA/EEM; Treasury is IEF/TLT; Credit is LQD/HYG; Real is GLD/DBC. The monthly total return of each instrument is computed first and then averaged. This is not the same as rebalancing an equal-weight group account daily and compounding its daily returns. The proxy contains neither the execution, nor the costs, nor the delays of distribution payments of the strategy; it is a regression control for exposure, not an investable benchmark and not a canonical academic factor. There are no weights fitted to improve alpha.

### 12. OLS, Newey-West HAC and alpha

#### 12.1. Two distinct models

For month $m$, $y_m=R_{candidate,m}-B_m$.

Model A:

$$
y_m=\alpha_A+\beta_q(R_{q,m}-B_m)+u_m.
$$

The comparator is B3 for H1, the parent for H2, and a separate comparison account with an identical initial state for P_A1. Model B:

$$
y_m=\alpha_B+\sum_{g=1}^{4}\beta_gF_{g,m}+u_m.
$$

B3 is not added to Model B: the protocol assigns two separate models with different sets of regressors. An additional B3 would create a different contract. The proximity of its exposures to the class proxies could also raise multicollinearity; this is a possible explanation and not a proven property of the real series. Each model is estimated separately. Alpha is the intercept relative to the particular model chosen, and not direct proof of universal investment skill.

#### 12.2. Derivation of OLS

Let $X$ be an $n\times k$ matrix whose first column consists of ones, with $k=2$ in A and $k=5$ in B. Minimize

$$
S(\beta)=(y-X\beta)'(y-X\beta).
$$

The gradient is $-2X'(y-X\beta)$; setting it to zero gives the normal equations $X'X\hat\beta=X'y$. Under full column rank,

$$
\hat\beta=(X'X)^{-1}X'y,\qquad
\hat u=y-X\hat\beta,\qquad X'\hat u=0.
$$

For computation, least squares via QR or SVD is preferable to explicit inversion of $X'X$: the condition number of $X'X$ is approximately the square of the condition number of $X$. The formula is a mathematical definition and not a requirement for an unstable algorithm.

With an intercept, the mean residual is zero: $\bar y=\hat\alpha+\sum_g\hat\beta_g\bar F_g$. This explains alpha as the part of the mean excess return not explained by the chosen mean exposures. If the regressors have nonzero covariance with omitted factors, a causal interpretation does not follow.

#### 12.3. Insufficiency of the ordinary SE

From the model $y=X\beta+u$,

$$
\hat\beta-\beta=(X'X)^{-1}X'u.
$$

The conditional covariance equals

$$
\operatorname{Var}(\hat\beta\mid X)
=(X'X)^{-1}X'\Omega X(X'X)^{-1}.
$$

The ordinary formula $\sigma_u^2(X'X)^{-1}$ assumes $\Omega=\sigma_u^2I$. With changing variance and serial correlation, this is incorrect. HAC changes the covariance estimate, not the OLS coefficients themselves and not the definition of alpha.

#### 12.4. The prescribed Newey-West covariance

Denote by $g_m=x_m\hat u_m$ the score vector of size $k$. With $q=3$ months and Bartlett weights $a_h=1-h/(q+1)$,

$$
S_0=\sum_{m=1}^{n}g_mg_m',\qquad
S_h=\sum_{m=h+1}^{n}g_mg_{m-h}',
$$

$$
\widehat S=S_0+\sum_{h=1}^{3}a_h(S_h+S_h'),
\quad (a_1,a_2,a_3)=(.75,.50,.25),
$$

$$
\widehat{\operatorname{Cov}}_{HAC}(\hat\beta)
=\frac n{n-k}(X'X)^{-1}\widehat S(X'X)^{-1}.
$$

Here `k` includes the intercept; with $n=108$ the correction is $108/106$ for A and $108/103$ for B. The SE of a coefficient is the square root of the corresponding diagonal element. The formula is sometimes written in terms of $Q=X'X/n$ and $\widehat S/n$, after which an outer factor $1/n$ appears. These variants are equivalent only under consistent normalizations; an additional division by n in the sum form above is an error.

At lag 0 the $S_h$ vanish, leaving $\sum x_mx_m'\hat u_m^2$, and the correction $n/(n-k)$ gives the HC1 heteroskedasticity-robust covariance. This is exactly what is prescribed as an independent synthetic test (`spec:204`). Lag 3 uses cross-products up to three months, not three daily sessions and not three years. See the specification, `docs/superpowers/specs/2026-10-09-n5-evaluation-design.md:133`.

#### 12.5. Non-negativity of the Bartlett covariance estimate

For any vector $v$, set $z_m=v'g_m$, extending the series by zeros outside $1,\ldots,n$. Then

$$
v'\widehat S v
=\sum_m z_m^2+2\sum_{h=1}^{q}\left(1-\frac h{q+1}\right)\sum_m z_mz_{m-h}.
$$

But the same quantity equals

$$
\frac1{q+1}\sum_{a\in\mathbb Z}
\left(\sum_{j=0}^{q}z_{a-j}\right)^2\ge0.
$$

Each square $z_m^2$ occurs $q+1$ times, and each pair $z_mz_{m-h}$ occurs $q+1-h$ times, which yields the Bartlett coefficients. Hence $\widehat S$ is positive semidefinite. Multiplication on the left and right by $(X'X)^{-1}$ preserves this property, and so does the factor $n/(n-k)>0$. A small negative diagonal element arising from floating-point arithmetic may be a numerical error, whereas a substantially negative diagonal element indicates an erroneous implementation. This proof is self-contained; the primary method is published by [Newey and West, 1987](https://doi.org/10.2307/1913610).

#### 12.6. Alpha, scale and interval

$$
\alpha_{ann}=12\hat\alpha_{month},\qquad
SE_{ann}=12\sqrt{\widehat{\operatorname{Cov}}_{00}},
$$

$$
CI_{ann}=12\left[\hat\alpha_{month}-1.96SE_{month},\;
\hat\alpha_{month}+1.96SE_{month}\right].
$$

This is a linear transformation of the estimator: $\operatorname{Var}(12\hat\alpha)=144\operatorname{Var}(\hat\alpha)$, so the SE is multiplied by 12 and not by $\sqrt{12}$. The square root of 12 would be the scale for a sum of independent monthly returns, whereas here a single estimated coefficient is rescaled. By contract, the annual alpha is arithmetic; $(1+\hat\alpha)^{12}-1$ is a different, nonlinear number and is not used.

The value 1.96 is the asymptotic normal quantile, not an exact t-quantile with $n-k$ degrees of freedom. The correction $n/(n-k)$ increases the covariance but does not by itself make the coverage exact. With 36 months and non-Gaussian dependent returns, the asymptotic approximation may be weak. The full 36 months are a minimum gate and not a promise of sufficient power.

#### 12.7. Numerical constraints and statistical limits

Alpha and its interval are not produced when $n<36$, when $X$ has deficient rank or when $\kappa(X)>10^8$. Under rank deficiency, different coefficient vectors give the same prediction $X\beta$, so alpha and the exposure coefficients are not uniquely determined. A large condition number means that a small change in the input can cause a large change in the coefficients. The threshold depends on the scale of the regressor columns. A future implementation must use one unambiguous matrix and norm for the condition number, and must not compare $\kappa(X'X)$ with the threshold intended for X.

HAC requires the orthogonality condition $E[x_m u_m]=0$, finite moments and sufficiently weak temporal dependence for a statistical interpretation. It does not correct omitted factors, measurement errors, retrospective selection or an incorrect economic model. The fixed lag of 3 does not account for arbitrary dependence beyond the third month. For general asymptotic consistency of HAC with an infinite correlation tail, a window length growing with n is usually needed; the fixed q=3 is a registered practical approximation. This is a limitation and not an error in the formula. The intervals are supplementary and descriptive; there is no new uncorrected confirmatory p. A positive alpha does not prove a confirmed investment history.

### 13. Robustness bootstrap for P_A1

For each selection year, the plan is to resample separately the matched vector of the four internal-validation excess-return series by circular blocks with $L=63$, $B=1000$ and seed 20261007. On each replicate the four U values are computed anew, and the same close set, the same preference order and the same fallback selection are applied. For candidate $i$,

$$
f_{i,Y}=\frac1{1000}\sum_{b=1}^{1000}\mathbf1\{selected_{b,Y}=i\}.
$$

Since each replicate selects exactly one candidate, $\sum_i f_{i,Y}=1$. A fallback replicate enters the frequency of H1_252_3 but is also counted in a separate counter of fallback applications; this distinguishes an ordinary preference for the original candidate from a numerical failure. Joint blocks preserve the dependence among the four alternative strategies on the same dates. See the specification, `docs/superpowers/specs/2026-10-09-n5-evaluation-design.md:105`.

At $f=.5$ the maximum conditional Monte Carlo SE of the frequency is approximately $\sqrt{.5\times.5/1000}=.0158$; at $f=.9$ it is about .00949. This is the random precision of 1000 replicates and not the full statistical uncertainty of the historical selection.

A high frequency shows that the given selection is robust to this particular way of perturbing the sample of internal-validation returns. It does not equal the probability that the configuration will be the best in the following year, and it is not a Bayesian posterior probability. The closeness of U, the asymmetry of preferences and the tolerance of .001 can produce a high frequency for the initial candidate even without a convincing advantage.

The internal validation contains about two years, approximately eight blocks of 63 sessions. This is little for independent reproduction of different market regimes. The windows of adjacent selection years overlap, so the nine journal rows are not nine independent selection experiments. The bootstrap does not recompute the entire training, the market features and the execution on the permuted market; it re-evaluates the selection on the already realized internal-validation returns.

A separate bootstrap of the realized P_A1 NAV is intended only for a conditional confidence interval of its $\Delta U$ relative to the comparison account with an identical initial state. The NAV path itself already includes the nine observed selections. A full interval for the adaptive process would require simulating repeated selection and execution, which is not implemented in N5. For P_A1, p is not published and is not included in Holm; the absence of p here is a deliberate boundary of the claim.

### 14. H2: lower exposure does not guarantee lower risk

The implemented H2 has $w_i^{H2}=w_i^{parent}F_i$ with $F_i\in\{0,1\}$ and moves the released weight into BIL (`hypotheses.py:52-58`). For each instrument the weight does not increase, the total risky exposure does not increase, and the ticker and group caps do not become weaker. These are strict component-wise properties.

However, for the annual covariance of excess returns over BIL, $\Sigma\succeq0$, the risk $\sqrt{w'\Sigma w}$ is not component-wise monotone when covariances are negative. If $u$ is the retained part and $v$ is the removed part, then

$$
Var(parent)-Var(H2)
=(u+v)'\Sigma(u+v)-u'\Sigma u
=v'\Sigma v+2u'\Sigma v.
$$

The first term is non-negative; the second can be sufficiently negative that the difference becomes negative. The removed position could have hedged the remaining ones.

A synthetic, checkable counterexample:

$$
\Sigma=\begin{pmatrix}.16&-.152\\-.152&.16\end{pmatrix},
\quad w_{parent}=(.25,.25),\quad w_{H2}=(.25,0).
$$

The eigenvalues $.008,.312$ are positive, so the covariance is admissible. The parent variance is $.25^2(.16+.16-2\cdot.152)=.001$, with risk $3.1623\%$; the H2 variance is $.25^2\cdot.16=.01$, with risk $10\%$. The risky exposure falls from 50% to 25%, while the covariance risk rises. With nonnegative covariance entries alone and nonnegative weights, a component-wise reduction would indeed not increase the quadratic form, but no such restriction exists.

This is a counterexample for the excess-risk model and not a calculation of the actual total volatility of H2. The realized NAV volatility also involves weight drift, costs, cash and changing distribution payments. The statement that H2 reduces risk must therefore be tested and not derived from weight deletion. Even the parent's ex-ante risk cap is not automatically inherited by the post-filter H2: a particular example can be strengthened until the cap itself is exceeded. This conclusion uses no hypothesis returns.

### 15. Exposure-matched parent and the purpose of robustness

The protocol, `RESEARCH_PROTOCOL.md:176`, assigns a causal exposure-matched parent to the future N6. On the decision date let

$$
a_P=\sum_iw_i^P,\qquad a_H=\sum_iw_i^{H2},\quad0\le a_H\le a_P.
$$

If $a_P>0$, the natural proportional implementation of reducing the parent's budget is

$$
\lambda=\frac{a_H}{a_P},\qquad
w_i^{match}=\lambda w_i^P,\qquad
w_{BIL}^{match}=1-a_H.
$$

For $a_P=0$, H2 also has $a_H=0$; the matched portfolio is entirely BIL, with no $0/0$ division. The formula preserves the relative composition of the parent and equalizes the target total risky weight of H2. It isolates the value of the choice of the removed ETFs beyond a simple reduction of market exposure. The formula is a direct formalization of the phrase "reduce the parent's risky weights to the sum of H2 risky weights at the current decision"; the concrete implementation of the scenario belongs to N6.

It does not equalize risk, group composition, realized holdings or drawdown. The matched parent risk is $\lambda\sqrt{w_P'\Sigma w_P}$ for a single current $\Sigma$, whereas the H2 risk depends on the filter-selected composition. Both accounts must be executed separately, with order sizing computed from the current state and with costs. Matching on future realized volatility would make the comparison non-causal; this is explicitly prohibited.

The other registered scenarios address parallel questions:

- The full grid of $cost\in\{0,10,20,50\}$ bps crossed with next-open and one-extra-session execution measures sensitivity to costs and delay. A cost of 10 bps is .001 on each side; the zero-cost result explains the drag and does not replace the main result.
- The proxy pay date (0, 10 or 30 calendar days) replaces only missing dates; actual payable dates are not changed. The order reserve of 0, 1 or 2% changes the causal buying power. Each such item is varied separately at the main cost and lag.
- H1 without division of the score by sigma separates the choice of scaling; equal weights within the same set of selected instruments separate the order sizing. Mixing these two modifications loses the identification of their contributions.
- Leave-one-class-out removes the whole group without relaxing K or the caps. For B1, B2 and B3, the slots are counted relative to the original nine instruments; automatic full reallocation would increase the budgets and would investigate a different strategy.
- A separate exclusion of DBC is a pre-named instrument diagnostic and not a search for a convenient exclusion after viewing a chart.
- P_A1 retains the main annual selections in all stress scenarios: reselection under stress would mix a change in execution with a new adaptive policy.

The purpose of these scenarios is to test fragility and attribution, not to select a winner and re-optimize parameters. The cost and delay effect can be non-monotone because the execution itself changes the subsequent account state; the zero-cost and high-cost paths cannot be obtained by simply subtracting aggregate cost from a single NAV.

### 16. Annual contributions and concentration: arithmetic is not wealth

For the matched dates of year $y$,

$$
A_y=\sum_{t\in y}(r_{c,t}-r_{q,t}),\qquad
D_y=252\,\overline{e_c-e_q}
=\frac{252}{n_y}A_y.
$$

Since $252/n_y>0$, a positive difference of the mean annual excess returns is equivalent to $A_y>0$. The count of positive years can therefore be obtained from the sign of the sum of daily differences. The values $D_y$ and $A_y$ nevertheless differ slightly because $n_y=251,252,253$.

For the positive walk-forward years, define

$$
S_+=\sum_{y:A_y>0}A_y,\qquad
C_{max}=\frac{\max_{y:A_y>0}A_y}{S_+}.
$$

The protocol requires $C_{max}\le.50$. The denominator includes only positive contributions; a negative year does not increase the share of the best positive year by reducing the net sum. When there are no positive years, the ratio is undefined; this is not "zero concentration" but a failure of other requirements. A single positive year would give a ratio of 1. Five positive years do not guarantee the criterion: one of them may account for 90% of all positive contributions.

This measure does not equal the share of a year in the cumulative monetary advantage. Even when $\sum_t(r_c-r_q)=0$, the final NAVs may differ: a candidate with $+10\%,-10\%$ and a comparison account with $0,0$ give an arithmetic difference of 0, but the candidate's wealth is 1% lower. A difference of CAGR also does not telescope from daily differences. T3 is therefore a descriptive table of concentration of arithmetic contributions, with the registered denominator, and not an attribution of compound wealth.

### 17. Full joint criteria of future decisions

N5 provides descriptive indicators and statistics, but not a conclusion of "supported" or "rejected": the final assessment requires N6 and the reserved period. The protocol, lines 184-186, sets the following joint conditions for the main fixed configuration:

1. There are no causality or accounting errors and no material unresolved data defects; otherwise economic conclusions are suspended.
2. $\Delta U\ge.01$ and a positive difference of the mean annual excess returns, both in walk-forward and in the reserved period.
3. The lower bound of the main basic interval is $>0$ and the main p after Holm is $<.05$ in the scheduled historical checks.
4. $\Delta U>0$ at 20 bps plus one extra session. Section 13 of the protocol also treats the disappearance of the effect at 20 bps or with an additional delay as lack of support. The full scenario grid is required: a favorable scenario that varies only one condition must not be presented on its own.
5. At least 3 of 4 asset-class exclusions give $\Delta U>0$.
6. A positive difference of the mean annual excess returns occurs in at least 5 of the 9 walk-forward years and 2 of the 3 reserved years.
7. Among the positive walk-forward arithmetic contributions, the share of the largest year is at most 50%.

The result is labeled only as "a candidate for further research". Satisfying the joint criteria is not proof of independent universal alpha or of sufficient statistical power. The main H1_252_3 and H2_4of6 are evaluated on their own: the success of the neighboring H1_126_4 or H2_5of6 is not transferred to them.

If $\Delta U\le0$ or the effect disappears in a designated stress scenario, the hypothesis is not supported within the limits of this study. If $0<\Delta U<.01$, the criterion of economic value is not established. If the point estimate is sufficient but the CI includes 0, the evidence is insufficient. A reduction in risk without convincing added value is called risk management. Instability is disclosed as concentration or fragility of the effect; it does not give the right to change the comparison account, the dates or the parameters. Statistical insignificance means a lack of grounds to reject the null hypothesis and not a demonstrated absence of an effect.

Some formulations in section 13 of the protocol refer to "scheduled historical checks", but N5 details the statistical family only for walk-forward, and N6 is not yet implemented. It therefore cannot be asserted that the future reserved Holm is already defined in program code. Its application must follow the frozen N6 contract, with the same transparent accounting of attempts. A change of the family after the results would destroy the preregistration.

### 18. Rounding, numerical correctness and verified tests

The benchmark metrics use unrounded in-memory numbers; the future statistics module will read `daily.csv` with 10 significant digits. The specification, lines 121 and 149, therefore assigns a tolerance of $10^{-7}$ for checking the consistency of U and total return, and $10^{-12}$ for comparing the module itself with an independent loop on the same numbers. These are two different kinds of error: rounding of the stored data and the arithmetic of the implementation. Literal equality of U from the CSV and the unrounded U is not expected. The size of the rounding depends on the NAV magnitude, the number of rows and the subtraction of close numbers; the order-of-magnitude estimate of $10^{-9}$ given in the specification is an estimate and not a universal theorem for arbitrary inputs.

The function `number` (`metrics.py:16-19`) converts a non-finite float to `None` so that canonical JSON contains no NaN or Infinity. This is a representation convention and not a proof of correct inputs. Positive finite NAV values, matched sorted sessions and a complete BIL return series must be ensured before the metrics are called: `compute_metrics` itself does not check all of these conditions. A null must not be read as a zero effect, and Holm must not be run on automatically substituted zero p-values.

In the existing `tests/test_metrics.py` (line 57), the following independent synthetic cases were examined:

- `57-76`: first return, geometric total, CAGR, sample volatility, Sharpe and U; the standard deviation of two returns equals $|r_2-r_1|/\sqrt2$ by hand.
- `79-92`: a constant excess return gives an undefined Sharpe at a nonzero mean; a single return gives a null dispersion.
- `95-110`: previous-close base, first drawdown of the year, no loss of the boundary return.
- `113-137`: execution-date attribution, annual turnover, target-risky mean, sum of relative costs instead of division by the mean NAV.
- `140-159`: no decisions and no shares at the close or at the group maxima.
- `162-180`: omission of empty periods, order and schema, JSON finiteness, guard after 2022-12-30.

These tests were read and not run for this document; a historical successful test run must not be presented as a new run. The formulas were checked separately with the Python standard library on artificial numbers, without imports from the project, its data or its research runs. The results obtained: total .008990000000000054; annual vol .12347469376354007; U 1.0737473473521868 for two synthetic returns from the test scenario; Holm $[.03,.05,.05,.09,.4,.8]$; basic CI $[-.018,.049]$ and p .5 for five artificial replicates; H2 excess-risk counterexample .0316227766 against .10; compounding $1.1\cdot.9-1=-.01$.

This verifies arithmetic illustrations. It does not verify the absent N5 code, the coverage of the bootstrap, the future numerical regression gates or the quality of real data. No new hypothesis-performance figures were computed.

### 19. Verifiable remarks and limits of interpretation

1. Real provable limitation of H2: component-wise weight removal guarantees that risky capital does not increase and that caps are preserved, but not the covariance risk. Under negative correlation, removing a hedge can raise the ex-ante risk and exceed the parent cap. If a public description promises guaranteed risk reduction, such a promise is mathematically incorrect; see section 14 and `hypotheses.py:45-63`. The actual effect must be evaluated separately.
2. Downside deviation and Sortino are absent. The symmetric variance-based criterion U must not be called a downside-risk measure, and it must not be claimed that a Sortino ratio is implemented.
3. Holm is correct, the guarantee is conditional. An exact FWER proof requires super-uniform individual p-values; the centered block-bootstrap p is approximate, and unknown prior trials are not part of the family of six. "Holm 5%" must not be turned into an exact guarantee for the whole historical research campaign.
4. HAC lag 3 is limited. It accounts for heteroskedasticity and autocovariance terms up to three months with Bartlett shrinkage. The finite-sample correction and the normal interval do not prove valid coverage under arbitrary long dependence; the exogeneity and weak-dependence conditions are essential.
5. Utility, volatility and alpha answer different questions. Utility and Sharpe use the variation of excess returns over BIL; the published volatility is that of the full NAV return; alpha is the conditional intercept of a model. None of them logically replaces the others.
6. P_A1 uncertainty is conditional. The validation bootstrap reselects on completed account returns, and the realized-policy CI is conditional on the observed selections. This is not coverage of the whole training and execution procedure and not a new independent trial.
7. Arithmetic concentration is not wealth attribution. T3 sums the daily candidate-minus-comparison-account returns; the size of compound cumulative outperformance cannot be inferred from it.
8. The existing guards are narrow by design. `metrics.py` blocks sessions after 2022-12-30 but is not a self-contained check of all financial invariants and data quality. Technical passage of the functions does not replace a check of research quality.
9. Other differences found are provided for by decisions: decision-close turnover denominator, execution-date attribution, sum-of-relative cost ratio, separate matched-start P_A1 comparison account. They are not errors, because they are explicitly fixed in D022 and D025.

Historical familiarity of the data, the retrospective ETF universe, point-in-time limitations, the exclusion of most of the 2008 crisis, corrections of distributions and the execution model affect the economic interpretation even when the arithmetic is error-free. The 2014-2022 data do not become independent after Holm, a new version of the document or a byte-identical rerun. The reserved period has a separate freeze procedure; repeatability of the numbers means reproducibility of the computation and not demonstrated predictive power.

### 20. Source map for re-verification

All paths below refer to the verified HEAD. Each entry gives the first line of the relevant fragment, followed by its range.

| Topic | Source and lines |
|---|---|
| All implemented metrics | `src/alpha_lab/metrics.py:36`, 36-99 |
| Daily account shares | `src/alpha_lab/metrics.py:22`, 22-33 |
| BIL and index basis | `src/alpha_lab/features.py:19`, 19-33 |
| Turnover and cost numerator, stored decision NAV | `src/alpha_lab/engine.py:178`, 178-198 |
| Interpretations of denominator, base and cost ratio | `DECISIONS.md:169`, 169-173 |
| Registered adaptive policy | `RESEARCH_PROTOCOL.md:145`, 145-153 |
| Metrics, effect, uncertainty | `RESEARCH_PROTOCOL.md:155`, 155-167 |
| Stress and joint decision criteria | `RESEARCH_PROTOCOL.md:169`, 169-188 |
| Detailed design of P_A1 | N5 specification (`docs/superpowers/specs/2026-10-09-n5-evaluation-design.md:78`), 78-109 |
| Detailed design of inference | N5 specification (`docs/superpowers/specs/2026-10-09-n5-evaluation-design.md:111`), 111-137 |
| Future independent tests | N5 specification (`docs/superpowers/specs/2026-10-09-n5-evaluation-design.md:200`), 200-209 |
| D025 P1-P14 and freeze/scope | `DECISIONS.md:221`, 221-263 |

The mathematical identities, counterexamples and proofs in this part do not depend on unknown economic results. They allow one to check which question each metric asks, under which conditions its statistical interpretation follows, and which claims cannot be proved by formulas alone.

## Appendices: scope, verification findings and reproducibility

### A. Map from formula to implementation to purpose

| Mathematical part | Code or registered contract | Purpose |
|---|---|---|
| Checks of value ranges, OHLC, events and calendar | `quality.py`, `normalize.py`, `market.py` | Avoid computing the portfolio on invalid bars |
| Product of later splits | `normalize.py:111` | Restore historical price and distribution units |
| TR: $s(C+D)/C_{prev}$ | `normalize.py:138`, `features.py:19` | Features and the theoretical BIL reference |
| Dividend tolerances, event categories, materiality | `reconcile.py:58`, `normalize.py:23` | Check that stored events agree with the sources |
| Event corrections and the causal change in TR | `corrections.py`, `normalize.py:130` | A separate corrected vintage without rewriting the original |
| SHA-256, canonical bytes, inventory, replay | `provenance.py`, `pipeline.py` | Trace the data and detect file changes |
| 63-day sigma, 126-day covariance | `features.py:49`, `features.py:71` | Normalize the score and estimate joint excess risk |
| Momentum, monthly relative returns | `features.py:80`, `features.py:135` | H1 ranking and H2 sign regularity |
| Inverse volatility, ETF/group caps, risk scaling | `portfolio.py:15`, `portfolio.py:38` | Transparent sequential construction of target weights |
| B0-B3, REF_SPY, H1/H2 | `benchmarks.py`, `hypotheses.py`, `engine.py:253` | Control comparisons and the six fixed hypotheses |
| NAV, shares, receivables, cash, fill, costs | `ledger.py`, `engine.py:146` | An executable model account in place of an idealized mixture of returns |
| Seven financial checks | `engine.py:205` | Detect specified violations of the accounting trail |
| Returns, CAGR, Sharpe, U, drawdown, proportions | `metrics.py` | Describe the account on identical dates and definitions |
| Consistency and diagnostics of reports | `report.py`, `hypothesis_report.py` | Admit only comparable and internally consistent records |
| P_A1, bootstrap, Holm, OLS/HAC | N5 specification, sections 5-6; not yet code | Selection from the available past and estimation of uncertainty |
| Scenarios and criteria of the research decision | Protocol, sections 12-13; future N6 | Test robustness before concluding on usefulness |

`acquire.py`, `evidence.py` and `__main__.py` mainly organize the acquisition of sources, the parsing of documents and the launch of commands. Their financial computations reduce to the unit transformations, the summation of distributions and the matching of dates and events described above; network transport and CLI construction do not create a separate alpha model. The project contains no neural network, no predictor training, no hidden Markowitz optimizer, no manual execution of DBC futures and no formula for a guaranteed future return. Index mechanisms inside the ETFs themselves are already reflected in the observed fund prices; they are not trading algorithms implemented here.

### B. Verified limitations and discrepancies

This section states properties of the formulas and reproduced examples. They do not support the conclusion that the closed real results contain such errors: those results were not examined.

| No. | Finding | Type and practical meaning |
|---|---|---|
| 1 | The covariance is built from $r_i-r_{BIL}$ | The 10% level is an estimated risk relative to BIL, not a guarantee of total or future volatility |
| 2 | Removing H2 weight can increase covariance risk | Counterexample: 3.952847% for the parent, 12.5% after the filter; the caps are preserved, the risk target may not be |
| 3 | The seven invariants do not contain an independent daily position balance | Artificially adding one free share passes all seven; ordinary code does not create such a share |
| 4 | The project documentation describes widening to `np.float32`, but the common interface preserves the type | At the floor boundary, 500 versus 499 shares were obtained; the built-in registered providers are not found to be affected by this example |
| 5 | After a correct finite-input check, normalization can overflow | On artificial splits of $10^{308}$ the output contains Inf/NaN while the `technical_pass` QA remains true; the overall `data_ready_for_n2` is nevertheless still false |
| 6 | A NaN adjustment residual is not counted as a large deviation | In an artificial underflow, two positive finite series give zero ratios and a missing residual; the early QA does not certify the numerical correctness of all transformations |
| 7 | A `confirmed` reconciliation does not guarantee documentary coverage of the whole window | An empty set of events inside the window yields confirmed even with a single issuer record outside the window; an external completeness gate is necessary |
| 8 | `materiality_bps` does not include the current split ratio | In a split-plus-distribution example, the diagnostic indicator is 333.3333 bps against 1000 bps of exact one-day TR error; these are different definitions |
| 9 | The N4 report checks the consistency of recorded features, not the underlying market | It cannot be regarded as independent evidence of the correctness of $T$, of all covariance estimates or of the parent `scale` |
| 10 | The N5 mathematics is registered, but its implementation is absent | A correct statement of the formulas does not confirm the existence of a working bootstrap, Holm adjustment, HAC or P_A1 |

Items 1-2 follow from the formulas. Item 3 is a limitation of diagnostic power. Item 4 is a reproduced discrepancy between the common API and the documentation. Items 5-6 are defects of numerical protection on extreme admissible inputs, not an established defect of the approved market data set. Items 7-9 define the scope of evidence of the QA and of the report. Item 10 is the actual boundary of the current stage.

The verification does not change the registered rules. In particular, repeated risk limiting after H2 would be new strategy behavior. A correction of the validator, a correction of the type description and the addition of an independent position invariant are possible subsequent technical tasks; they are only described here. For any change that affects stored research outputs, the project's versioning and rerun-disclosure rules apply.

### C. Rationale for the parameters and what is not established for them

| Parameter | Role | What does not follow from the value |
|---|---|---|
| 252 sessions | A single annual scale and the long window | That every year has exactly 252 days; that returns are independent |
| 126 sessions | Short momentum and the covariance window | Minimal error of the risk forecast |
| 63 sessions | Sigma window and primary bootstrap block | Optimal length for all regimes |
| 21 sessions | Skipping the most recent part of momentum; short bootstrap sensitivity | Elimination of all reversals and look-ahead |
| K=3/4 | Number of permitted H1 slots | Optimal number of ETFs |
| 4/6 and 5/6 | Strength of the H2 sign filter | Statistically significant evidence of persistence |
| 25% ETF and 50% group | Limit on target concentration | A limit on actual drift or losses |
| 10% | Maximum estimated excess risk of H1 and of the common risk algorithm | Total volatility, maximum drawdown or guaranteed risk of H2 |
| 1% reserve | Margin when target quantities are created | That the account always retains at least 1% in cash |
| 10 bps per side | Main model cost | Observed spread or slippage at the actual open |
| Proxy +10 days | Approximation of the unknown pay date | That the cash historically arrived on this date |
| Gamma=3 | Fixed variance penalty in U | Optimal risk aversion or the utility of all investors |
| Close-set 0.001 | Utility tolerance when selecting P_A1 | Absence of selection bias or optimal smoothing |
| Minimum $\Delta U=0.01$ | Threshold of economic value of complexity | A threshold of statistical significance or a guarantee of a future effect |
| 10,000/1,000 replications | Monte Carlo precision and reproducibility | Exact finite-sample coverage or independence of the history |
| HAC lag=3, minimum 36 months, condition at most $10^8$ | Registered conditions for interpreting the regression | Sufficient power, correctness of the factor model and absence of long-range dependence |

The protocol fixes these numbers in advance so that favorable values are not chosen after the results are viewed. Fixing the values in advance improves the interpretability of the study; it does not prove the economic optimality of the constants.

### D. Checks performed on 10 October 2026

The existing project environment was used: Python 3.14.0, NumPy 2.5.3, pandas 3.0.6, pytest 9.1.1. The environment check printed an interpreter-launcher warning about the location of the Python executable, but the subsequent selected commands completed successfully. This does not replace the historical environment manifest of the registered campaigns.

1. Features, weight construction, benchmark providers, H1/H2, metrics, ledger and engine: 168 passed in 33.22s.
2. N1 normalization, QA, reconciliation, corrections, provenance and two TR scenarios: 130 passed in 39.82s after moving the pytest basetemp to a permitted working folder. The first attempt gave 84 passed and 46 setup errors caused by permissions on the temporary directory; these environment errors are recorded in the description in Part I.
3. The N4 validator and report diagnostics: 150 passed in 86.66s.
4. A separate check of accounting, loader and engine: 109 passed, with one real-vintage check excluded. This partly overlaps with the first set; the figures are not summed into a number of unique tests.
5. An additional signal script: seven groups of synthetic assertions, including 1,000 PSD covariance examples of risk limiting, the H2 counterexample, the inverse-volatility budget, caps and a calendar of 2,266 sessions and 108 months.
6. An additional data script: five synthetic counterexamples and identities from the table above; the primary data check and an independent repetition reproduced the results.
7. An additional ledger script: exact P&L decomposition at three cost rates, fractional fill, an artificial position mutation and the float32 floor; an independent repetition completed successfully.
8. An additional check of statistical examples: linear quantiles and basic CI, centered p, six Holm-adjusted p-values, the difference between $U(c)-U(q)$ and $U(c-q)$, and Bartlett HAC and HC1 in an artificial constant-only regression. All assertions passed; this is a check of the algebra of the examples, not a check of the absent N5 implementation.

The full project suite was not run in this work. The historical 610 passed recorded in STATUS is not presented as a current run. The repeated synthetic checks are not new financial research attempts, and the experiment journal was not extended.

In the additional signal script, the first attempt passed the mathematical assertions but ended with an error when printing a Cyrillic path in cp1252; the output was made ASCII-compatible and the script was rerun with exit code 0. This error concerns printing, not the formulas.

#### Verification scripts for the artificial examples

The artificial examples were reproduced with separate verification scripts that are not part of the repository. Each script uses only the project's source modules and artificial inputs; none loads `data/runs` or opens the closed strategy metrics. The commands were verified in the current working environment, and the numerical outputs are tied to its types and versions.

### E. Primary sources of the methods and project definitions

The main source of the specific formulas is the verified code and the project's conventions: the research protocol (`RESEARCH_PROTOCOL.md`), the execution model (`EXECUTION_MODEL.md`), the data contract (`DATA_CONTRACT.md`), the decision history (`DECISIONS.md`) and the approved N5 specification (`docs/superpowers/specs/2026-10-09-n5-evaluation-design.md`).

Library definitions and independent methodological foundations were checked against primary sources:

- NumPy: [covariance and ddof](https://numpy.org/doc/stable/reference/generated/numpy.cov.html), [standard deviation](https://numpy.org/doc/stable/reference/generated/numpy.std.html), [linear quantile](https://numpy.org/doc/stable/reference/generated/numpy.quantile.html). They clarify the API and do not prove an investment effect.
- [Politis and Romano: circular block resampling, original Stanford technical report](https://statistics.stanford.edu/technical-reports/circular-block-resampling-procedure-stationary-data). The assumptions on the dependent series are essential for a meaningful application of the method.
- [Holm, 1979: original article](https://www.jstor.org/stable/4615733). The proof of FWER control is given in Part IV; for the project it is conditional on valid individual p-values and a specified family.
- [statsmodels: source code of the sandwich covariance](https://www.statsmodels.org/stable/_modules/statsmodels/stats/sandwich_covariance.html). The Bartlett form and the $n/(n-k)$ correction were checked; statsmodels is not a new dependency of the project and is not yet used in N5.
- [Newey and West: original work on the positive semidefinite HAC estimator, NBER](https://www.nber.org/papers/t0055). The algebraic proof that the Bartlett estimator is PSD is given in Part IV; the applicability of asymptotic intervals requires additional conditions.
- [NIST: Secure Hash Standard](https://www.nist.gov/publications/secure-hash-standard). SHA-256 provides a means of byte-integrity control given trusted anchors; it does not imply a signature or proof of financial truth.

The algebraic derivations, examples and counterexamples in this document are formulated independently. The dates of the web documentation do not change the recorded versions of the research environment.

### F. What is now justified

From the data formulas follow the consistency of quantity and price under a split and the model TR return under the stated reinvestment. From the weight rules follow the budget $m/K$, non-negativity, the concentration limits and the bound on estimated excess risk before the H2 filter. From the operations of the standard ledger follows the self-financing decomposition of NAV given correct data and records. From the metric definitions follow the exact cumulative returns and the conditional annualized indicators. From the statistical procedures follow algorithms for estimating uncertainty and conditional theorems, not a proof of alpha.

The research question itself remains open: whether H1 and H2 add value after costs, risk, exposures and constraints when evaluated on a history that has already been inspected. Its resolution requires the not yet implemented N5 and N6, and an independent observation of the future, that is, an actual freeze of the model and prospective data. Mathematical transparency allows the question to be posed and tested correctly; it does not predetermine a positive answer.
