# Decisions log

Candidate decisions, their cost, and what we locked on the dashboard. Budget for both decisions
together, paid messages included: **$4.0M**. Costs are the CFO's estimates from
[`brief/10-cobalt-bank.md`](../brief/10-cobalt-bank.md); use them as given.

Locking rules: a decision takes effect at the start of its week and must be locked before that week
starts; nothing can be locked after 17:30. It can be replaced until its week starts.

**Week-3 surprise C1 (unrecognized charges):** the earliest answer was week 4 (lock before 14:30);
we did not lock then. The week-4 update (14:30) gave the causes and the scale (about 9,000 customers,
Cobalt not breached), so any answer now goes in **week 5 → lock before 15:00** and must use those
facts: "we do not know the cause yet" would now be a misleading statement.

**Deadlines that matter:** a decision that answers the week-6 migration must start in week 5 at the
latest → lock it **before 15:00**. A decision for week 6 itself → before 15:30. The last moment for
anything is **17:30** (week 10).

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

| Item | Decision | Cost |
|---|---|---|
| | | |
| **Total** | | **≤ $4.0M** |

## Locked on the dashboard

Copy the exact text locked on the dashboard into `code/config/decisions/plan.json`.
`plan.json` holds decision 1 as locked. Decision 2 is not locked: until it is, `plan.json` carries
D2 (migration notice, week 5) as a PLACEHOLDER so plan runs have two decisions; its `why` starts with
"PLACEHOLDER". Replace it word for word when decision 2 is locked.

| Decision | Week | Actions | Cost | Locked at (clock time) | Replaced? |
|---|---|---|---|---|---|
| 1 | 5 | Security pack (on) + Instant dispute credit (on) + Extra support staff (+50), everyone, push/email/in-app | $0.95M | locked 15:00 (last saved 14:57:44, confirmed on the dashboard) | yes: added +50 support staff (weeks 5–8, covers the migration week) |
| 2 | | not locked; options in `docs/decision-1-lock.md` | ≤ $3.05M | | |

Decision 1 in `plan.json` is the dashboard export's `run_decisions` entry, unchanged (`dashboard-export.json`, 14:58). Reasons and
simulation evidence: `docs/decision-1-lock.md` (sweep `c1_plans`).
