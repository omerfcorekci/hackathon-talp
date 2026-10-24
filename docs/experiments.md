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
