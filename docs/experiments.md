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

Notes (Oct 24, 13:45): all four runs on the same seed, so differences are decision effects only. Run time ≈ 20 s per 8-week run. Metrics formulas and assumptions: `code/sim/metrics.py`. Next: second seed, message-wording variants, a rate-boost candidate for goal 2 (the only goal currently off target), and sharper per-persona consequences (lost sales for card-reader personas, autopay bounce for paycheck-to-paycheck personas) so the delta has something to bite on.
