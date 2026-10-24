# Decision 2: when to lock it

**Recommendation: do not lock for week 6. Wait for the week-7 announcement (16:00), then lock decision
2 for week 8 before 16:30.** Hard fallback: week 9 before 17:00. Never later than 17:30.

## The calendar

| Week | Starts / lock before | What happens | Decision 2 here can… |
|---|---|---|---|
| 6 | 15:30 | Migration Sat Dec 12 – Sun Dec 13 | prepare the weekend (offline limit); cannot answer what went wrong |
| 7 | 16:00 | Aftermath; an overrun or new surprise is likely announced at 16:00 | not answer it: a decision locked before 16:00 cannot see that announcement |
| **8** | **16:30** | Christmas | **answer the week-7 announcement** (the earliest week that can, per the brief) |
| 9 | 17:00 | New Year: "many people compare savings rates" | still answer it; a rate offer lands while people shop for rates |
| 10 | 17:30 (last) | Board goals measured Jan 10 | one week of effect only; leaves no time to test before the 17:30 runs |

## What the simulation says (real model, 2 seeds, C1 and its update on, decision 1 locked)

Sweep `d2_timing` (viewer: Karar önerisi → d2_timing), baseline from `c1_plans`.

| Decision 2 | Active ≥98 | Deposits ≥97 | Rating | CFPB | Total cost |
|---|---|---|---|---|---|
| Offline limit $250, week 6 | 99.97 | 96.98 (96.98–96.98) | 4.60 | 120 | $1.05M |
| New-money rate +0.5, week 6 | 97.31* | 97.42 (96.98–97.86) | 4.60 | 120 | $1.75M |
| New-money rate +0.5, week 8 | 97.34* | 97.42 (96.98–97.86) | 4.60 | 120 | $1.75M |
| New-money rate +0.5, week 9 | 99.97 | 97.42 (96.98–97.86) | 4.60 | 120 | $1.75M |
| No decisions (baseline) | 99.95 | 96.98 | 4.60 | 120 | $0 |

\* E2 artifact: he says everything is fine but logs no app action in weeks 9–10 and is counted as lost.

**Why it comes out this way**
- **Deposits are decided by one saver, S1, and his reason is the FDIC limit, not the rate.** In seed 2
  he moves $100k in week 4, before any decision 2 can start. In seed 1 he moves in week 6–8 in the runs
  without a rate offer and stays in the runs with one, but his own words never mention the rate; in the
  week-9 run he had not moved by week 8 although no offer existed yet. That is timing noise, not a
  rate effect.
- **S1 keeps saying he will move "after the holidays"**, i.e. around or after the Jan 10 measurement.
  The real deposit risk sits just past the board's date, and no menu item answers an FDIC worry.
- **S2 left in week 2** for a 0.5-point rival rate on $150k; a boost capped at $50k balances is too
  small to bring her back (no persona reported new money in any run).
- **The offline limit changes no board goal** and raises fraud exposure in a week when stolen card
  numbers are in the news.
- **Ratings and complaints move only in the migration week** and stay inside the targets everywhere.

So on today's evidence no decision-2 option, in any week, reliably changes a board goal. That makes the
choice about **option value**: the decision is worth most as an answer to something we cannot see yet.

## What to do

1. **15:30:** lock nothing for week 6.
2. **16:00:** read the week-7 announcement; add it to `code/config/surprises/` (verbatim + our reading).
3. **16:00–16:25:** sweep 2–3 answers to it (each with decision 1 fixed), pick by the viewer's rule,
   lock for **week 8 before 16:30**.
   - Overrun or failure hitting paycheck customers: zero-interest advance ($0.4M) or goodwill credit to
     the hit group ($0.5M / $1M) + free instant transfers.
   - Quiet week 7: new-money rate boost from week 8 or 9 for deposits ($0.8M), with honest framing.
4. If something blocks 16:30: lock for week 9 before 17:00. 17:30 is the hard last moment, and the five
   official runs start then.

## What the board should hear

"Our second decision was held back on purpose: the simulation showed no pre-migration step that moves
a board goal, so we kept it to answer what the migration actually did. The deposit risk we can see is
large savers above the FDIC limit, and it lands just after January 10."
