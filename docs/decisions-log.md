# Decisions log

Candidate decisions, their cost, and what we locked on the dashboard. Budget for both decisions
together, paid messages included: **$4.0M**. Costs are the CFO's estimates from
[`brief/10-cobalt-bank.md`](../brief/10-cobalt-bank.md); use them as given.

Locking rules: a decision takes effect at the start of its week and must be locked before that week
starts; nothing can be locked after 17:30. It can be replaced until its week starts.

**Week-3 surprise C1 (unrecognized charges):** the earliest answer was week 4 (lock before 14:30);
we did not lock then. The week-4 update (14:30) gave the causes and the scale (about 9,000 customers,
Cobalt not breached), so any answer now goes in **week 5 → lock before 15:00** and must use those
facts: "we do not know the cause yet" would now be a misleading statement. Done: decision 1 answers
it in week 5 with those facts, locked at 15:00.

**Deadlines that matter:** a decision that answers the week-6 migration must start in week 5 at the
latest → lock it **before 15:00**. A decision for week 6 itself → before 15:30. The last moment for
anything is **17:30** (week 10). Status at 15:40: weeks 5 and 6 are closed; decision 2 is planned for
week 8 (lock before 16:30), after the 16:00 week-7 announcement (`docs/decision-2-timing.md`).

## Candidates

Files: `code/config/decisions/candidates/*.json` (exact messages, channels and "why" inside).
Each file holds two decisions, because a plan run needs both; decision 2 can be replaced later by an
answer to a surprise.

| ID | Week | Target | Actions (level) | Channels | Cost | Idea |
|---|---|---|---|---|---|---|
| A1 | 5 | everyone | Security pack (on) + Higher offline card limit (on) | push, email, in-app | $0.4M | Say early and plainly what the weekend means; $250 offline; guard against phishing |
| A2 | 7 | everyone | Instant dispute credit (on) | push, in-app | $0.4M | Cut the complaints most likely to reach the CFPB after the switch |
| B1 | 5 | paycheck customers | Early pay (on) + Higher offline card limit (on) + Extra support staff (+150) | push, email, in-app | $1.3M | Paid Fri Dec 11, frozen Sat: early pay moves payday to Wed Dec 9, permanently |
| B2 | 7 | savers with large balances | Savings rate boost, new money only (+0.5 points) | push, email, in-app | $0.8M | Keep rate-chasing savers after the weekend at half the cost |
| C1 | 5 | savers with large balances | Savings rate boost (+0.5 points) | push, email, in-app | $1.6M | Close the 0.5-point rate gap for the 4 weeks around the switch |
| C2 | 7 | paycheck customers | Goodwill credit ($10 each) + Instant dispute credit (on) | push, in-app | $1.4M | Concrete sorry to those hit hardest, plus instant dispute credit |
| D1 | 5 | everyone | Security pack (on) + Instant dispute credit (on) | push, email, in-app | $0.7M | Answer C1 with the week-4 facts (processor double charges, fraud test charges on cards stolen elsewhere, not breached, ~9,000 customers), instant credit, alerts, free card; nothing promised about refunds |
| D2 | 5 | everyone | Higher offline card limit (on) + Extra support staff (+50) | push, email, in-app | $0.35M | Migration notice with $250 offline and more support |

| Plan | Decisions | Total |
|---|---|---|
| A: inform, cheap | A1 + A2 | $0.8M |
| B: protect paycheck customers | B1 + B2 | $2.1M |
| C: defend deposits | C1 + C2 | $3.0M |
| D: fraud first (after C1 and its week-4 update) | D1 + D2, both week 5 | $1.05M |

## How we test them (real model; each run is one engine run of 24 personas × 10 weeks)

Run from the repo root. `sweep.py` starts one `python3 -m sim` subprocess per variant and seed
(`--parallel 4` at a time) with the same inputs as `code/scripts/run_all.sh`, writes to
`experiments/sweeps/<name>/<variant>_s<seed>/`, and appends one row per variant to
[`experiments.md`](experiments.md).

```bash
# check first, no model calls: validates every variant and prints the commands
python3 code/scripts/sweep.py --name plans --seeds 1,2 --baseline --dry-run \
  --decisions code/config/decisions/candidates/a_inform_cheap.json \
              code/config/decisions/candidates/b_protect_paycheck.json \
              code/config/decisions/candidates/c_defend_deposits.json
# the three plans side by side, two seeds, with the no-decision baseline (drop --dry-run;
# add --fake for an offline run, --weeks-run 3 for a quick test):
python3 code/scripts/sweep.py --name plans --seeds 1,2 --baseline --parallel 8 \
  --decisions code/config/decisions/candidates/a_inform_cheap.json \
              code/config/decisions/candidates/b_protect_paycheck.json \
              code/config/decisions/candidates/c_defend_deposits.json \
              code/config/decisions/candidates/d_fraud_first.json
# timing: the winner's decision 1 in weeks 4, 5, 6 (7 = after the switch):
python3 code/scripts/sweep.py --name timing --seeds 1,2 --vary 1 --weeks 4,5,6,7 \
  --decisions code/config/decisions/candidates/<winner>.json
```

## Budget check

The engine reads the dashboard wording directly and prints cost, reach and resolved targets:

```bash
cd code && PYTHONPATH=. python3 -m sim --personas personas/personas.jsonl \
  --decisions config/decisions/plan.json --show-plan
```

Engine-checked totals (`--show-plan`): A $0.80M, B $2.10M, C $3.00M, D $1.05M. In C2 the $10 goodwill credit
reaches 32% of the paycheck group (100k-customer cap), i.e. one of the six paycheck personas.

`--show-plan` on `plan.json` with `targets.json` (16:28) prints decision 1 at $300,000 + $400,000 +
$250,000 = $950,000 and decision 2 at $400,000, total $1,350,000 of $4,000,000, matching the CFO menu
and the dashboard's own `total_cost_usd`.

| Item | Decision | Cost |
|---|---|---|
| Security pack (on): free new card on request + alert on every card payment | 1 (week 5, everyone) | $0.30M |
| Instant dispute credit (on): up to $100 per customer, 8 weeks | 1 | $0.40M |
| Extra support staff (+50), 4 weeks | 1 | $0.25M |
| Messages: push, email, in-app (no SMS, no CEO video) | 1 | $0 |
| **Decision 1 subtotal** | 1 | **$0.95M** |
| Zero-interest advance up to $500, up to 20,000 customers (on) | 2 (week 8, federal and contractor paycheck customers) | $0.40M |
| Messages: push, email, in-app (no SMS, no CEO video) | 2 | $0 |
| **Total** | 1 + 2 | **$1.35M of $4.0M ($2.65M unspent)** |

## Locked on the dashboard

Copy the exact text locked on the dashboard into `code/config/decisions/plan.json`.
`plan.json` is the dashboard export's `run_decisions`, unchanged (`dashboard-export.json`, exported
16:26:47). Decision 2's target is a description, not a persona group, so `targets.json` maps it to P2
(the one persona the shutdown hits) and gives the real group's size, 12,000 customers, so the
20,000-customer cap reaches him in every seed. `run_all.sh` reads `targets.json` by default.

| Decision | Week | Actions | Cost | Locked at (clock time) | Replaced? |
|---|---|---|---|---|---|
| 1 | 5 | Security pack (on) + Instant dispute credit (on) + Extra support staff (+50), everyone, push/email/in-app | $0.95M | locked 15:00 (last saved 14:57:44, confirmed on the dashboard) | yes: added +50 support staff (weeks 5–8, covers the migration week) |
| 2 | 8 | Zero-interest advance up to $500 (on), paycheck customers who work for the federal government or its contractors, push/email/in-app | $0.40M | saved 16:26:42 for week 8, locks at 16:30 (export at 16:26:47 still shows `locked: false`) | no (revision 1) |

Decision 1 in `plan.json` is the dashboard export's `run_decisions` entry, unchanged (`dashboard-export.json`, exported 15:36, shows it locked at 15:00). Reasons and
simulation evidence: `docs/decision-1-lock.md` (sweep `c1_plans`). Decision 2: sweep `d2_week8`
(16:06) had the advance and a new-money rate boost tie on every board goal; the advance answers the
week-7 shutdown directly for half the cost, and the rate boost does not reach S1, whose reason to move
is the FDIC limit.
