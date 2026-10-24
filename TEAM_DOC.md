# Team doc: how we built the Cobalt Bank simulation

Cobalt Bank lives through ten weeks (Nov 2 – Jan 10) with 24 LLM personas. Each week every persona
reads what happened to it and what it heard; the model then decides what it does, its status and what
happens to its money. We make two decisions on the bank's behalf and compare the outcome with business
as usual. Code: `code/sim/` (engine), `code/personas/` (personas), `code/config/` (world, decisions,
announcements), `code/scripts/` (runs, sweeps, viewer, live interview).

## Personas and why those attributes

Full spec: [`code/personas/spec.md`](code/personas/spec.md); one-paragraph briefs:
[`code/personas/personas-brief.md`](code/personas/personas-brief.md). `generate.py` writes
`personas.jsonl` deterministically; the same file is used in all five runs.

**Groups (4 of 5, six personas each):** paycheck customers (P1–P6), savers with large balances
(S1–S6), small business owners with a Cobalt card reader (B1–B6), everyday customers (E1–E6).
Students are left out: small balances, no lever on goal 2, and behavior close to the young everyday
personas. They are the first group we would add.

**Attributes used, and in which form**
- *Fixed fields that couple to the crisis* (dossier sector list): pay into Cobalt and payday (4 of 6
  paycheck personas are paid Fri Dec 11), balance band, above/knows the FDIC limit, number of banks,
  Cobalt as main or second bank, moves money for rate, checks the app daily, uses P2P, past fraud
  victim, financial literacy, reaction to a bank SMS.
- *Temperament* (catalog C, E, G): values, risk attitude, trust in institutions, price consciousness,
  loyalty, need for control, anxiety, anger speed, patience, forgiveness, embarrassed to complain,
  debt, living paycheck to paycheck.
- *Information* (catalog F): news sources, circle size, leader/follower/independent, sways easily,
  checks rumors, who they ask before deciding. These feed the network (`network.json`).
- *Narrative lines* (catalog A, B, I): a life (age, place, job, household), why they chose Cobalt, one
  scar, a recent life event, this quarter's fear, two or three lifestyle details. They fight sameness
  and make the live Q&A credible.
- *A concrete commitment for the migration weekend* (`migration_weekend`): rent autopay, Sunday
  payouts, weekend card tickets above $100, one big purchase, a settlement delay. The world turns it
  into plain facts ("5 of your weekend tickets were above $100: about $1,400 you could not charge").
- *Changing state*: status, money, memory, rating and complaint come only from the model's weekly
  answer and carry over to the next week.

**Left out:** race/ethnicity, religion, health, politics, immigration (not needed for the client's
question, and a stereotype risk); catalog items with no mechanism linking them to a migration or a
rate (zodiac, military service, first in family to college); more than three lifestyle details.

**Grounding:** group sizes and deposits come from the dossier (310k paycheck, 42k card readers, 105k
savers = the top 5% holding half of $6.0B, 1.643M everyday). Age and balance skews follow the general
ACS / Survey of Consumer Finances pattern (older households hold larger balances); stated as an
assumption, not fitted to microdata.

**Weights:** each persona carries `weight_customers` (2.1M in total) and `weight_deposits_usd`
(≈ $6.0B in total), uneven within a group so deposits stay heavy-tailed (S1 Victor: 1,000 customers
at $350k; S6 Chloe: 41,500 at $13k). A persona does not move its whole audience: only a share
f = 0.05–0.5 makes the same move (higher for second-bank and rate-sensitive personas, lower when pay
lands at Cobalt). Formulas: [`code/sim/metrics.py`](code/sim/metrics.py) and `assumptions` in every
`metrics.json`.

## The world

**What personas see each week** (prompt built in `code/sim/prompt.py`):
- the calendar (Thanksgiving, migration weekend, Christmas, New Year) and business-as-usual notices
  (migration email in week 5, holding statements on social media);
- dashboard announcements, word for word, from their week on, reaching a persona by a seeded draw
  (90% if it checks the app daily, 60% if it follows social media, 35% otherwise);
- our decision message, word for word, only if the persona is in the target and only from its week;
- what happened to *it* this week: pay landed, the app was read-only, a ticket above the offline
  limit was declined, an autopay ran late with a fee, support took N minutes;
- a rival's rate offer in week 5 (certain for rate-chasers and people with three or more banks);
- messages from other personas: posts, group chats, direct messages.

**What they can do:** check the app, try a transfer, call support, complain in the app, post, tell
friends, review the app, complain to the CFPB/BBB, dispute a charge, move some or most money, move
direct deposit, open a rival account, use Cobalt less, recommend Cobalt, wait and see. The model
picks; the engine only validates the answer against a JSON schema and retries invalid answers.

**How a week runs (two rounds):** every persona is called once in parallel; their messages are routed
over the network (5% stranger post, 35% followed account, 65% close friend, 80% group chat, 100%
direct), at most two peer messages per persona per week; only recipients get a second call. A
persona's quote of the bank's message is never forwarded, so the decision text cannot leak outside its
target. Status, money and memory carry over to the next week.

**Speed:** about 50–65 s for a full ten-week run of 24 personas; the five official runs run in
parallel.

## How we read each crisis

Details and the verbatim texts: [`docs/crisis-log.md`](docs/crisis-log.md).
- **C0, the known migration (week 6).** The freeze itself is mild; harm comes from money that must
  move that weekend and from any gap between what we promised and what happened. Modelled through each
  persona's own weekend commitment, longer support waits (25 min in week 6, 12 in week 7) and a rival
  rate offer that targets the date.
- **C1, small unrecognized charges (week 3).** Little money, big trust hit, three weeks before the
  freeze. The text reaches people by the reach draw; our reading of what really happened sits in the
  announcement's `effects`: the business-as-usual holding statement, support waits of 9 and 7 minutes
  in weeks 3–4, and three personas (P5, E4, B5) who find charges themselves. With surprises off, text
  and effects vanish together.
- _Later announcements: add here as they arrive._

## Experiments

Every row: [`docs/experiments.md`](docs/experiments.md). Candidates and budget math:
[`docs/decisions-log.md`](docs/decisions-log.md). Tool: `code/scripts/sweep.py` (variants × seeds,
with the no-decision baseline).

| Plan | Idea | Cost | First result (2 seeds, before C1) |
|---|---|---|---|
| A: inform, cheap | early honest notice, $250 offline, security pack; instant dispute credit after | $0.8M | Everyone stays active; deposits 96.4%, below baseline |
| B: protect paycheck | early pay + $250 offline + 150 staff; new-money rate boost after | $2.1M | Best deposits (97.9% in both seeds) |
| C: defend deposits | +0.5 pt rate boost; goodwill + dispute credit after | $3.0M | Same deposits as B for $0.9M more |
| D: fraud first | answer C1 in week 4 (security pack + instant dispute credit); migration notice + 50 staff in week 5 | $1.05M | _to run with C1 on_ |
| none | business as usual | $0 | Deposits 97.0%; only goal 2 at risk |

What we learned so far:
1. With an on-time migration and an honest notice, reactions are mild; a plan's value shows when
   something goes wrong (overrun, fraud scare).
2. A reassuring message that reality contradicts can make things worse: in one overrun run a persona
   escalated to the CFPB because "no surprises" was followed by a late fee.
3. Goal 2 moves through two savers; differences between plans are one persona's choice, so we read
   them as direction, never as size, and require two seeds before any claim.

## Problems we hit and how we solved them

- **Inert simulation.** First runs: plan and no-decision identical, nobody posted, nobody reacted to
  the migration. Cause: the network was not loaded and the world never told a persona what happened
  to it, so the model invented "it went fine". Fix: load the network, add per-persona weekend
  commitments and deterministic consequences ([`docs/engine-review.md`](docs/engine-review.md)).
- **One persona = a whole audience** made results jump by tens of points. Fix: the follow share f.
- **Quiet users counted as lost.** Personas that stay but only "wait and see" were counted inactive.
  Fix: only a persona that used the app before and then stopped counts as lost.
- **Model arithmetic drifted balances.** Fix: the engine derives balance and 30-day activity from the
  model's reported money move and actions; the model never edits numbers.
- **Decision text leaking** through personas quoting it to friends outside the target. Fix: the
  router blocks quotes of the bank message.
- **Two engines in parallel.** We merged the two-round engine with our personas, metrics and tools;
  earlier experiment rows are kept but marked as not comparable.

## Our own ideas

- **Commitments, not moods:** each persona has a concrete thing that must happen on the migration
  weekend, so the crisis bites in dollars and the model reacts to facts, not to an adjective.
- **Words versus reality:** an announcement's text and what actually happened are separate inputs, so
  the same message can be tested against an on-time and an overrun weekend.
- **Follow share:** a persona's move counts for only part of its audience, set by its traits.
- **Live interview:** `code/scripts/interview.py` lets the board question any persona about its own
  ten weeks, built only from that persona's logged record.

## What we would do with more time

- More seeds per plan (five or more) and intervals instead of min–max.
- Add students; more personas per group so one saver does not decide goal 2.
- Calibrate f and the rating/complaint conversion against real churn and CFPB data.
- Test message wording variants, not only actions.
- Model rivals as agents instead of one fixed offer.
