# Experiments log

Every comparison run we make: which decisions, in which weeks, how many seeds, and what came out.
Scratch outputs live in `experiments/` (git-ignored); the numbers we keep go here. This feeds the
"experiments" section of `TEAM_DOC.md` and "how we compared approaches" in the presentation.

| ID | Decisions (week: actions) | Surprises | Seeds | Model | goal_1 | goal_2 | goal_3 | goal_3b | Cost | Takeaway |
|---|---|---|---|---|---|---|---|---|---|---|
| v2-w7-nodec | none (7 weeks only) | test fraud wave wk3 + update wk4 | 1 | 3.5-flash-lite | 101.9 | 92.0 | 4.60 | 120 | $0 | Baseline. Deposits at 92% because Elaine (S2, $375M) moved for the rate in week 1 and Victor (S1) moved some; two savers = 8 points of goal 2. |
| v2-w7-plan | wk5 everyone: offline $250 + support +150 + security pack + CEO msg; wk7 paycheck: instant dispute credit + free transfers 2w | same | 1 | 3.5-flash-lite | 101.9 | 92.0 | 4.60 | 120 | $1.6M | **No delta vs baseline when the migration completes on time.** Pre-announced, honest BAU email + on-time finish = mild reactions; the plan buys nothing visible. |
| ovr8b-w8-nodec | none, **8-hour overrun** (`world_overrun8.json`), 8 weeks | same | 1 | 3.5-flash-lite | 103.4 | 94.4 | 4.59 | 120 | $0 | Overrun produces angry posts (Jamal, Dana), 2 low ratings, 1 complaint to the bank; statuses and money unchanged. Survivable, as the organizers say. |
| ovr8b-w8-plan | plan as above, 8-hour overrun | same | 1 | 3.5-flash-lite | 101.9 | 94.4 | 4.60 | 120 | $1.6M | One fewer low rating, no complaint; goal_3 +0.01. The plan's value shows only when things go wrong, and even then it is small with 24 personas. |

| v3-ontime-nodec | none, 8 weeks, **per-persona weekend commitments on** | fraud wave | 1 | 3.5-flash-lite | 102.8 | 94.4 | 4.58 | 120 | $0 | One 1-star (Jamal: $1,400 of weekend tickets above the $100 limit). |
| v3-ontime-plan | test plan (wk5 limit $250 + support +150 + security; wk7 dispute credit + free transfers) | fraud wave | 1 | 3.5-flash-lite | 102.8 | 92.0 | 4.59 | 120 | $1.6M | Jamal loses $700 instead of $1,400; one more saver moved some money (seed noise). |
| v3-overrun-nodec | none, **8-hour overrun via surprise effects** | fraud wave + overrun | 1 | 3.5-flash-lite | 102.9 | 94.4 | 4.52 | 120 | $0 | 5 low ratings, 4 complaints to the bank (Jamal, Rosa, Robert, Dana). Rosa's rent autopay ran late, $50 fee. |
| v3-overrun-plan | test plan, 8-hour overrun | same | 1 | 3.5-flash-lite | 102.8 | 94.4 | 4.47 | 133.7 | $1.6M | 5 low ratings; **Rosa escalates to the CFPB**: the CEO promised "no surprises", then a late fee she did not cause. A reassuring message that reality contradicts can make it worse. Single seed. |

Notes (Oct 24, 14:10): with weekend commitments the crisis has teeth (ratings and complaints move, reasons name the dollar amounts) and the delta between plan and no-decision is now persona-specific and readable, but on one seed its sign is not stable. Two seeds minimum before any claim.

Notes (Oct 24, 13:45): all four runs on the same seed, so differences are decision effects only. Run time ≈ 20 s per 8-week run. Metrics formulas and assumptions: `code/sim/metrics.py`. Next: second seed, message-wording variants, a rate-boost candidate for goal 2 (the only goal currently off target), and sharper per-persona consequences (lost sales for card-reader personas, autopay bounce for paycheck-to-paycheck personas) so the delta has something to bite on.

### Earlier rows from Tarık's engine (not directly comparable)

The four rows below came from Tarık's earlier engine (`tarik/main`, Oct 24 13:37): different
personas, weights and metric formulas, so compare them with each other, not with the rows above.
Real model, seeds 1 and 2, ten weeks.

| ID | Decisions (week: actions) | Surprises | Seeds | Model | goal_1 | goal_2 | goal_3 | goal_3b | Cost | Takeaway |
|---|---|---|---|---|---|---|---|---|---|---|
| plans/a_inform_cheap (13:37) | w5: Security pack (on) + Higher offline card limit during the migration (on); w7: Instant dispute credit (on) | on | 1,2 | gemini-3.5-flash-lite | 100.00 (100.00-100.00) | 97.09 (96.54-97.65) | 4.60 (4.60-4.60) | 120.00 (120.00-120.00) | $0.80M | Cheapest and best: nobody left, 3-4 movers; first moves still in week 5 |
| plans/b_protect_paycheck (13:37) | w5: Early pay (on) + Higher offline card limit during the migration (on) + Extra support staff (+150); w7: Savings rate boost, new money only (+0.5 points) | on | 1,2 | gemini-3.5-flash-lite | 98.91 (97.83-100.00) | 96.08 (94.97-97.18) | 4.60 (4.60-4.60) | 147.15 (145.30-149.00) | $2.10M | Paycheck group calm, but savers moved in week 5 before the week-7 rate boost |
| plans/c_defend_deposits (13:37) | w5: Savings rate boost (+0.5 points); w7: Goodwill credit ($10 each) + Instant dispute credit (on) | on | 1,2 | gemini-3.5-flash-lite | 96.06 (95.17-96.96) | 96.91 (96.67-97.14) | 4.60 (4.60-4.60) | 134.45 (123.60-145.30) | $3.00M | Savers protected (p01 kept most), but untargeted everyday/small-business customers left |
| plans/nodecision (13:37) | none | on | 1,2 | gemini-3.5-flash-lite | 92.55 (91.31-93.78) | 92.32 (90.10-94.55) | 4.60 (4.60-4.60) | 134.45 (123.60-145.30) | $0.00M | Baseline: 4 left per seed, 7-13 movers; seeds differ by ~4.5 pts on deposits (noise) |

### Sweeps in this engine

Rows appended by `code/scripts/sweep.py` (same columns; mean over seeds, min-max in brackets).

| ID | Decisions (week: actions) | Surprises | Seeds | Model | goal_1 | goal_2 | goal_3 | goal_3b | Cost | Takeaway |
|---|---|---|---|---|---|---|---|---|---|---|
| merge_plans/a_inform_cheap (14:07) | w5: Security pack (on) + Higher offline card limit during the migration (on); w7: Instant dispute credit (on) | on | 1,2 | gemini-3.5-flash-lite | 100.00 (100.00-100.00) | 96.43 (95.87-96.98) | 4.60 (4.60-4.60) | 120.00 (120.00-120.00) | $0.80M | Everyone stays active, but S1 moved some/most money: deposits at or below no-decision. No rate lever for savers. |
| merge_plans/b_protect_paycheck (14:07) | w5: Early pay (on) + Higher offline card limit during the migration (on) + Extra support staff (+150); w7: Savings rate boost, new money only (+0.5 points) | on | 1,2 | gemini-3.5-flash-lite | 99.98 (99.95-100.00) | 97.86 (97.86-97.86) | 4.60 (4.60-4.60) | 120.00 (120.00-120.00) | $2.10M | Best on deposits (S1 keeps money in both seeds), above the 97 target in both seeds; S2 still leaves for yield. |
| merge_plans/c_defend_deposits (14:07) | w5: Savings rate boost (+0.5 points); w7: Goodwill credit ($10 each) + Instant dispute credit (on) | on | 1,2 | gemini-3.5-flash-lite | 99.95 (99.95-99.95) | 97.86 (97.86-97.86) | 4.60 (4.60-4.60) | 120.00 (120.00-120.00) | $3.00M | Same deposits as B for $0.9M more; S2 moved most anyway, so the week-5 rate boost did not hold the top saver. |
| merge_plans/nodecision (14:07) | none | on | 1,2 | gemini-3.5-flash-lite | 99.98 (99.95-100.00) | 96.98 (96.98-96.98) | 4.60 (4.60-4.60) | 120.00 (120.00-120.00) | $0.00M | Baseline: on-time migration is mild (no CFPB, rating 4.60); S2 moves most, S1 some, in both seeds. Only goal_2 is at risk. |

Notes (Oct 24, 14:15, merged engine, metrics recomputed after the quiet-user fix): first real comparison on the merged branch, no dashboard surprises yet (on-time migration only). Each run ~50-65 s, 8 runs in parallel in 65 s, 2,107 calls, 4 invalid (retried). The only goal that moves is goal_2, and it moves through two savers (S1 Victor, S2 Elaine; f = 0.38 each). Plan differences are one persona's choice, so read them as direction, not size.
| c1_plans/d_fraud_first (14:45) | w5: Security pack (on) + Instant dispute credit (on); w5: Higher offline card limit during the migration (on) + Extra support staff (+50) | on | 1,2 | engine default | 99.97 (99.95-100.00) | 96.98 (96.98-96.98) | 4.60 (4.60-4.60) | 120.00 (120.00-120.00) | $1.05M | |
| c1_plans/e_fraud_first_plus_rate (14:45) | w5: Security pack (on) + Instant dispute credit (on); w5: Higher offline card limit during the migration (on) + Extra support staff (+50) + Savings rate boost, new money only (+0.5 points) | on | 1,2 | engine default | 97.34 (94.67-100.00) | 97.42 (96.98-97.86) | 4.60 (4.60-4.60) | 120.00 (120.00-120.00) | $1.85M | |
| c1_plans/b_protect_paycheck (14:45) | w5: Early pay (on) + Higher offline card limit during the migration (on) + Extra support staff (+150); w7: Savings rate boost, new money only (+0.5 points) | on | 1,2 | engine default | 99.97 (99.95-100.00) | 96.98 (96.98-96.98) | 4.60 (4.60-4.60) | 120.00 (120.00-120.00) | $2.10M | |
| c1_plans/nodecision (14:45) | none | on | 1,2 | engine default | 99.95 (99.95-99.95) | 96.98 (96.98-96.98) | 4.60 (4.60-4.60) | 120.00 (120.00-120.00) | $0.00M | |
