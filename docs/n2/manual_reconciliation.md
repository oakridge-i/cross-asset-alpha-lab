# N2: manual reconciliations of the execution mechanics

Basis: the specification `docs/superpowers/specs/2026-10-07-n2-execution-design.md`, sections 5, 6, 8 and 9; RESEARCH_PROTOCOL.md section 8 (lines 118-126). Each case was calculated by hand before the engine was run; the test in `tests/test_engine.py` compares the engine's values with these numbers through `pytest.approx(value, abs=1e-9)`, while integer quantities and string fields are compared exactly.

## General conditions

- Calendar: XNYS sessions 2017-11-27 to 2017-12-08 (ten sessions: 11-27, 11-28, 11-29, 11-30, 12-01, 12-04, 12-05, 12-06, 12-07, 12-08). The data are synthetic (`tests/n2_fixtures.py`), with `payable_basis = actual` unless stated otherwise.
- Base scenario: cost c = 0.001, lag = 1, reserve r = 0.01, proxy_pay_days = 10. Initial cash 100000.0, no positions.
- start_session equals the first decision date, end_session = 2017-12-08. Decision dates are given explicitly.
- Order size: Q = floor((1 - r) × w × NAV / close), with the multiplier (1 - r) = 0.99.
- Sale: proceeds = qty × open × (1 - c). Purchase: spending = qty × open × (1 + c). Cost = c × qty × open.
- Purchases: R = Σ q × open × (1 + c), fill = min(1, cash / R), floor(fill × q) is bought.
- The weight provider returns a weight for every market ticker; a ticker not named in a case gets weight 0.

## Case 1. Before and after the open

Input: ticker AAA, close 100 in all sessions, open 100 in all sessions except 2017-11-29 (open 100.5). Decision 2017-11-28, weight of AAA = 1.

Calculation:

1. Q = floor(0.99 × 1 × 100000 / 100) = floor(990.00) = 990; order +990 for 2017-11-29.
2. Purchase on 2017-11-29: 990 × 100.5 = 99495.0; cost 99495.0 × 0.001 = 99.495; spending 99495.0 + 99.495 = 99594.495.
3. Cash: 100000 - 99594.495 = 405.505.
4. NAV at the close of 2017-11-29: 405.505 + 990 × 100 = 99405.505.

Expected values: target_qty 990, order qty 990, order close 100; trade on 2017-11-29, buy 990 at 100.5, cost 99.495; cash 405.505; NAV 99405.505.

Variation. Close and open for sessions 2017-11-30 to 2017-12-08 are replaced (250 and 17). The order from the 2017-11-28 decision uses only the close of 2017-11-28 and the open of 2017-11-29, so target_qty (990) and close (100) match the original run.

## Case 2. Split 1:2 (ratio 0.5) with a position and a pending order

Input: ticker BBB, close and open 91 through 2017-12-04 inclusive, split_ratio 0.5 on 2017-12-05, close and open 182 from 2017-12-05. Decisions: 2017-11-28 (weight 1), 2017-12-04 (weight 0.5), 2017-12-06 (weight 0).

Calculation:

1. Decision 2017-11-28: Q = floor(0.99 × 100000 / 91) = floor(1087.91) = 1087; order +1087 for 2017-11-29.
2. Purchase on 2017-11-29: 1087 × 91 = 98917.0; cost 98917.0 × 0.001 = 98.917; cash 100000 - 98917.0 - 98.917 = 984.083.
3. NAV at the close of 2017-12-04: 984.083 + 1087 × 91 = 984.083 + 98917.0 = 99901.083.
4. Decision 2017-12-04: Q = floor(0.99 × 0.5 × 99901.083 / 91) = floor(49451.036 / 91) = floor(543.42) = 543. Order 543 - 1087 = -544 for 2017-12-05.
5. Session 2017-12-05, step 1 (split, ratio 0.5): position 1087 × 0.5 = 543.5; order -544 × 0.5 = -272. Cash is unchanged.
6. Sale on 2017-12-05: 272 at 182; 272 × 182 = 49504.0; proceeds 49504.0 × (1 - 0.001) = 49454.496; cash 984.083 + 49454.496 = 50438.579; position 543.5 - 272 = 271.5.
7. NAV at the close of 2017-12-06: 50438.579 + 271.5 × 182 = 50438.579 + 49413.0 = 99851.579. Decision 2017-12-06 (weight 0): Q = 0, order 0 - 271.5 = -271.5 for 2017-12-07.
8. Sale on 2017-12-07: 271.5 at 182; 271.5 × 182 = 49413.0; proceeds 49413.0 × 0.999 = 49363.587; cash 50438.579 + 49363.587 = 99802.166; position 0.

Expected values: purchase 1087 at 91, cash 984.083; NAV of the 2017-12-04 decision = 99901.083, target_qty 543, order_qty after the split -272, filled_qty 272; sale 272 at 182, proceeds 49454.496, cash 50438.579, position 271.5; last order held_qty 271.5, order_qty -271.5, sale 271.5 at 182, proceeds 49363.587, cash 99802.166, position 0; `split_events == [['BBB', '2017-12-05']]`.

## Case 2b. Split 3:1 (ratio 3.0) with a position and a pending order

Input: ticker CCC, close and open 61 through 2017-12-04 inclusive, split_ratio 3.0 on 2017-12-05, close and open 20 from 2017-12-05. Decisions: 2017-11-28 (weight 0.5), 2017-12-04 (weight 1).

Calculation:

1. Decision 2017-11-28: Q = floor(0.99 × 0.5 × 100000 / 61) = floor(49500 / 61) = floor(811.48) = 811; order +811 for 2017-11-29.
2. Purchase on 2017-11-29: 811 × 61 = 49471.0; cost 49471.0 × 0.001 = 49.471; spending 49471.0 + 49.471 = 49520.471; cash 100000 - 49520.471 = 50479.529.
3. NAV at the close of 2017-12-04: 50479.529 + 811 × 61 = 50479.529 + 49471.0 = 99950.529.
4. Decision 2017-12-04: Q = floor(0.99 × 1 × 99950.529 / 61) = floor(98951.024 / 61) = floor(1622.15) = 1622. Order 1622 - 811 = +811 for 2017-12-05.
5. Session 2017-12-05, step 1 (split, ratio 3.0): position 811 × 3 = 2433; order +811 × 3 = +2433. Cash is unchanged: 50479.529.
6. Purchase on 2017-12-05: 2433 × 20 = 48660.0; R = 48660.0 × 1.001 = 48708.66; fill = min(1, 50479.529 / 48708.66) = 1; 2433 bought at 20. Cost 48.66; cash 50479.529 - 48708.66 = 1770.869; position 2433 + 2433 = 4866.
7. NAV at the close of 2017-12-05: 1770.869 + 4866 × 20 = 1770.869 + 97320.0 = 99090.869.

Expected values: purchase 811 at 61, cash 50479.529; NAV of the 2017-12-04 decision = 99950.529, target_qty 1622, held_qty 811, order_qty after the split 2433, filled_qty 2433, status filled; purchase 2433 at 20 with spending 48708.66, buy_fill 1.0; cash 1770.869, position 4866, NAV 99090.869; `split_events == [['CCC', '2017-12-05']]`.

## Case 3. Ex-date and payment date

Input: tickers DDD and EEE, close and open 49 in all sessions; both have dividend 1.0 on ex-date 2017-11-30, payable_date 2017-12-05, basis actual. Decisions: 2017-11-28 (DDD 1), 2017-11-29 (DDD 0, EEE 1), 2017-12-04 (EEE 1).

Calculation:

1. Decision 2017-11-28: Q(DDD) = floor(0.99 × 100000 / 49) = floor(2020.41) = 2020. Purchase on 2017-11-29: 2020 × 49 = 98980.0; cost 98.98; cash 100000 - 98980.0 - 98.98 = 921.02.
2. NAV at the close of 2017-11-29: 921.02 + 2020 × 49 = 99901.02. Decision 2017-11-29: DDD 0, Q(EEE) = floor(0.99 × 99901.02 / 49) = floor(2018.41) = 2018. Orders: DDD -2020, EEE +2018 for 2017-11-30.
3. Session 2017-11-30 (ex-date), step 2: DDD has a position of 2020 and a receivable of 2020 × 1.0 = 2020.0 due 2017-12-05; EEE has no position, so no receivable is created.
4. Sale of DDD 2020 at 49: 2020 × 49 = 98980.0; proceeds 98980.0 × 0.999 = 98881.02; cash 921.02 + 98881.02 = 99802.04.
5. Purchase of EEE 2018 at 49: 2018 × 49 = 98882.0; spending 98882.0 × 1.001 = 98980.882; cash 99802.04 - 98980.882 = 821.158.
6. NAV at the close of 2017-11-30: 821.158 + 2018 × 49 + 2020.0 = 821.158 + 98882.0 + 2020.0 = 101723.158.
7. Decision 2017-12-04: Q(EEE) = floor(0.99 × 101723.158 / 49) = floor(100705.926 / 49) = floor(2055.22) = 2055. Order 2055 - 2018 = +37 for 2017-12-05.
8. Session 2017-12-05, step 3: credit of 2020.0, cash 821.158 + 2020.0 = 2841.158. Step 5: purchase of 37 at 49; 37 × 49 = 1813.0; spending 1813.0 × 1.001 = 1814.813; cash 2841.158 - 1814.813 = 1026.345.
9. NAV at the close of 2017-12-05: 1026.345 + 2055 × 49 = 1026.345 + 100695.0 = 101721.345.

Expected values: cash on 2017-11-29 = 921.02; DDD receivable on 2017-11-30 = 2020.0, no EEE receivable (payouts has one row, status paid); sale of DDD 2020 with proceeds 98881.02, purchase of EEE 2018 with spending 98980.882, cash 821.158, NAV 101723.158; order on 2017-12-04 +37; 2017-12-05: purchase of 37 for 1814.813, cash 1026.345, receivable 0, NAV 101721.345.

## Case 3b. Scenario proxy_pay_days = 0

Input: ticker FFF, close and open 41, dividend 0.25 on ex-date 2017-11-30, payable_date 2017-12-11, payable_basis `proxy_ex_plus_10_calendar_days` (2017-11-30 + 10 calendar days = 2017-12-10, a Sunday; the first session no earlier than this date is 2017-12-11). Decision 2017-11-28, weight of FFF = 1.

Calculation:

1. Q = floor(0.99 × 100000 / 41) = floor(2414.63) = 2414. Purchase on 2017-11-29: 2414 × 41 = 98974.0; spending 98974.0 × 1.001 = 99072.974.
2. Ex-date 2017-11-30: receivable 2414 × 0.25 = 603.5.
3. Base scenario (k = 10): the due date 2017-12-11 is later than end_session 2017-12-08; the receivable stays with status receivable and is included in NAV; basis `proxy_ex_plus_10_calendar_days`; `proxy_payouts == [['FFF', '2017-11-30', '2017-12-11']]`.
4. Scenario proxy_pay_days = 0: the due date is the first session no earlier than 2017-11-30 + 0 days = 2017-11-30; crediting occurs in step 3 of the same session and cash increases by 603.5; basis `proxy_ex_plus_0_calendar_days`; `proxy_payouts == [['FFF', '2017-11-30', '2017-11-30']]`.

Expected values: quantity 2414; base: status receivable, pay_session 2017-12-11, amount 603.5, receivable 603.5 in daily on 2017-12-08; k = 0: status paid, pay_session 2017-11-30, amount 603.5, receivable at the close of 2017-11-30 equal to 0. The invariants pass in both scenarios.

## Case 4. Gap and fill coefficient

Input: ticker GGG, close 97 in all sessions, open 97 in all sessions except 2017-11-29 (open 99). Decision 2017-11-28, weight 1.

Calculation:

1. Q = floor(0.99 × 100000 / 97) = floor(1020.62) = 1020; order +1020 for 2017-11-29.
2. R = 1020 × 99 × 1.001 = 100980.0 × 1.001 = 101080.98.
3. fill = min(1, 100000 / 101080.98) = 0.989306.
4. Bought floor(0.989306 × 1020) = floor(1009.09) = 1009. The remainder of the order is cancelled with reason `insufficient_cash`; status partial.
5. Spending: 1009 × 99 = 99891.0; × 1.001 = 99990.891; cash 100000 - 99990.891 = 9.109.

Expected values: target_qty 1020, bought 1009 at 99, buy_fill = 100000 / 101080.98, cash 9.109, status partial, cancel_reason `insufficient_cash`.

## Case 5. ETF switch

Input: ticker HHH, close and open 80; ticker III, close and open 40. Decisions: 2017-11-28 (HHH 1), 2017-11-29 (HHH 0, III 1).

Calculation:

1. Decision 2017-11-28: Q(HHH) = floor(0.99 × 100000 / 80) = floor(1237.5) = 1237. Purchase on 2017-11-29: 1237 × 80 = 98960.0; cost 98.96; cash 100000 - 98960.0 - 98.96 = 941.04.
2. NAV at the close of 2017-11-29: 941.04 + 1237 × 80 = 99901.04. Decision 2017-11-29: HHH 0, Q(III) = floor(0.99 × 99901.04 / 40) = floor(2472.55) = 2472. Orders: HHH -1237, III +2472.
3. Session 2017-11-30. Sale of HHH 1237 at 80: 98960.0; proceeds 98960.0 × 0.999 = 98861.04; cost 98.96.
4. Purchase of III 2472 at 40: 98880.0; spending 98880.0 × 1.001 = 98978.88; cost 98.88. The sale proceeds are available for the purchase in the same session (R = 98978.88 with cash 941.04 + 98861.04 = 99802.08; fill = 1).
5. Cash: 941.04 + 98861.04 - 98978.88 = 823.20.
6. Costs of the 2017-11-29 decision: 98.96 + 98.88 = 197.84. Turnover: (98960.0 + 98880.0) / 99901.04 = 197840 / 99901.04.

Expected values: purchase of HHH 1237, cash 941.04, NAV 99901.04; on 2017-11-30 sale of HHH 1237 (proceeds 98861.04), purchase of III 2472 (spending 98978.88), cash 823.20; costs_usd of the 2017-11-29 decision = 197.84, turnover = 197840 / 99901.04, buy_fill 1.0.

## Case 6. Delay lag = 2

Input: ticker JJJ, close 97 in all sessions; open 97, except 2017-11-29 (open 50) and 2017-11-30 (open 98). Scenario lag = 2. Decision 2017-11-28, weight 1.

Calculation:

1. Q = floor(0.99 × 100000 / 97) = floor(1020.62) = 1020; execution on the second session after the decision: 2017-11-30. There are no trades on 2017-11-29; cash is 100000.0.
2. R = 1020 × 98 × 1.001 = 99960.0 × 1.001 = 100059.96; fill = 100000 / 100059.96 = 0.999401.
3. Bought floor(0.999401 × 1020) = floor(1019.39) = 1019 at 98.
4. Spending: 1019 × 98 = 99862.0; × 1.001 = 99961.862; cash 100000 - 99961.862 = 38.138.

Expected values: no trades on 2017-11-29; execution_session 2017-11-30; purchase of 1019 at 98; cash 38.138.

## Case 6b. Order without a valid Open

Input: ticker KKK, close 97 in all sessions; open 97, except 2017-11-29 (open not set, NaN). Decision 2017-11-28, weight 1.

Calculation: Q = floor(0.99 × 100000 / 97) = 1020; on 2017-11-29 the Open is not a finite number greater than 0, so the order is cancelled before R is computed. There are no trades, cash is 100000.0, buy_fill = 1.0 (there are no purchases to compute).

Expected values: status cancelled, cancel_reason `no_valid_open`, filled_qty 0.0, no trades.
